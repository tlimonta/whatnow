"""System-level adversarial evaluation. Dry-run by default; live calls require --run."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.ai.client import DEFAULT_MODEL, MAX_TOKENS, AnthropicClient
from src.ai.parser import IntakeParser
from src.backend.main import create_app
from src.models.case import CaseType

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "evaluations" / "adversarial_cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "failure_modes"
SENSITIVE_RE = re.compile(
    r"(?i)(?:\b\d{4}\b|FAKE-PASSWORD-example-123|4111\s+1111\s+1111\s+1111|\b000\b|\b000000\b|900\s+000\s+000)"
)


def load_dataset(path: Path = DATASET) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("cases"), list):
        raise ValueError("Dataset must contain a cases list")
    return data, data["cases"]


def select_cases(cases: list[dict], ids: list[str] | None = None, limit: int | None = None) -> list[dict]:
    if ids:
        unknown = set(ids) - {case["id"] for case in cases}
        if unknown:
            raise ValueError(f"Unknown case ids: {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case["id"] in ids]
    return cases[:limit] if limit is not None else cases


def expected_values(expected: Any) -> list[Any]:
    if isinstance(expected, str):
        valid_values = (case_type.value for case_type in CaseType)
        pattern = r"(?<![\w])(" + "|".join(re.escape(value) for value in valid_values) + r")(?![\w])"
        return re.findall(pattern, expected)
    return [expected]


def sensitive_strings(text: str) -> list[str]:
    return list(dict.fromkeys(match.group(0) for match in SENSITIVE_RE.finditer(text)))


def score_case(case: dict, response: dict | None, http_status: int | None,
               second_message_supported: bool = True) -> dict:
    """Score only API/data properties. Qualitative assertions remain manual review."""
    expected = case.get("expected", {})
    checks: dict[str, dict] = {}
    if http_status is not None:
        checks["http_success"] = {"passed": http_status == 201, "observed": http_status}
    elif response is not None:
        checks["http_success"] = {"passed": True, "observed": http_status}
    if response is not None:
        actual_type = response.get("case_type")
        target = expected.get("case_type")
        if target:
            options = expected_values(target)
            checks["case_type"] = {"passed": actual_type in options, "expected": options, "observed": actual_type}
        facts = response.get("facts") or {}
        for field, value in expected.get("facts_supported_by_text", {}).items():
            checks[f"fact:{field}"] = {"passed": facts.get(field) == value, "expected": value, "observed": facts.get(field)}
        for field in expected.get("must_be_null", []):
            checks[f"null:{field}"] = {"passed": facts.get(field) is None, "expected": None, "observed": facts.get(field)}
        for field in expected.get("must_list_in_missing_fields", []):
            checks[f"missing:{field}"] = {"passed": field in response.get("missing_fields", []), "observed": field in response.get("missing_fields", [])}
        tasks = response.get("tasks", [])
        if actual_type == "unsupported" or actual_type != "stolen_phone":
            checks["task_presence"] = {"passed": len(tasks) == 0, "expected": 0, "observed": len(tasks)}
        valid_source_ids = _verified_sources()
        valid_step_ids = _verified_steps()
        provenance_ok = all(task.get("workflow_id") == "stolen_phone_es" and task.get("source_id") in valid_source_ids for task in tasks)
        checks["task_provenance"] = {"passed": provenance_ok, "observed": [{"id": t.get("id"), "status": t.get("status"), "workflow_id": t.get("workflow_id"), "source_id": t.get("source_id")} for t in tasks]}
        task_integrity = all(task.get("id") in valid_step_ids and task.get("status") in {"pending", "completed", "skipped"} for task in tasks)
        checks["task_ids_and_statuses"] = {"passed": task_integrity, "observed": [{"id": t.get("id"), "status": t.get("status")} for t in tasks]}
        initial = response.get("initial_message", "")
        matches = sensitive_strings(initial)
        if case["category"] == "sensitive_data":
            checks["raw_message_storage_gap"] = {"passed": initial == case["messages"][0], "observed_sensitive_values_in_initial_message": matches}
        serialized_structured = json.dumps({"facts": facts, "tasks": tasks}, ensure_ascii=False)
        relevant = [v for v in sensitive_strings(case["messages"][0]) if v in serialized_structured]
        checks["sensitive_values_in_structured_output"] = {"passed": not relevant, "observed_values": relevant}
    qualitative = bool(expected.get("must_not") or expected.get("acceptable") or expected.get("must_be_true"))
    status = "FAIL" if any(not item["passed"] for item in checks.values()) else ("MANUAL_REVIEW" if qualitative else "PASS")
    unsupported = case["id"] == "ADV-016" and not second_message_supported
    if unsupported and status != "FAIL":
        status = "NOT_SUPPORTED"
    reasons = []
    failed = [name for name, item in checks.items() if not item["passed"]]
    if failed:
        reasons.append("Deterministic checks failed: " + ", ".join(failed))
    if qualitative and not failed:
        reasons.append("Qualitative must_not/acceptable behavior requires human review")
    if unsupported:
        reasons.append("No API endpoint accepts a second natural-language update for this case")
    return {"status": status, "checks": checks, "reason": "; ".join(reasons) or "All applicable deterministic checks passed"}


def _verified_sources() -> set[str]:
    data = json.loads((ROOT / "data" / "sources" / "stolen_phone_es.json").read_text(encoding="utf-8"))
    return {source["id"] for source in data["sources"]}


def _verified_steps() -> set[str]:
    data = json.loads((ROOT / "data" / "workflows" / "stolen_phone_es.json").read_text(encoding="utf-8"))
    return {step["id"] for step in data["steps"]}


def stress_variants(message: str) -> list[dict]:
    """Repeat existing neutral prose around the unchanged theft sentence; add no facts."""
    core = "someone grabbed my phone out of my hand and ran away, it was an iPhone."
    if core not in message:
        raise ValueError("ADV-020 core theft sentence not found")
    prefix, tail = message.split(core, 1)
    filler = (prefix + " ")
    variants = []
    for multiplier in (2, 4, 8):
        expanded = prefix + filler * (multiplier - 1) + core + tail
        variants.append({"id": f"ADV-020-STRESS-x{multiplier}", "category": "long_input_stress", "message": expanded,
                         "input_characters": len(expanded), "approx_input_tokens": (len(expanded) + 3) // 4})
    return variants


def run_case(client: TestClient, case: dict, message: str | None = None) -> dict:
    text = message if message is not None else case["messages"][0]
    try:
        response = client.post("/api/cases", json={"message": text})
        status = response.status_code
        body = response.json() if status == 201 else None
        score = score_case(case, body, status, second_message_supported=False)
        return {"case_id": case["id"], "native_category": case["category"], "http_status": status,
                "provider_outcome": "success" if status == 201 else "api_error", "case": body,
                "api_error_detail": None if status == 201 else response.json().get("detail"),
                "observed_case_type": (body or {}).get("case_type"),
                "observed_facts": (body or {}).get("facts"),
                "observed_missing_fields": (body or {}).get("missing_fields"),
                "observed_tasks": [{"id": task.get("id"), "status": task.get("status")} for task in (body or {}).get("tasks", [])],
                "workflow_source_provenance": [{"id": task.get("id"), "workflow_id": task.get("workflow_id"), "source_id": task.get("source_id")} for task in (body or {}).get("tasks", [])],
                "deterministic_checks": score["checks"], "status": score["status"], "reason": score["reason"],
                "input_characters": len(text), "approx_input_tokens": (len(text) + 3) // 4,
                "second_message_status": "NOT_SUPPORTED" if case["id"] == "ADV-016" else None,
                "warning": "Parser warnings are not exposed by the API response" if status == 201 else None}
    except Exception as exc:  # Provider/parser errors are retained without their potentially sensitive message.
        name = type(exc).__name__
        return {"case_id": case["id"], "native_category": case["category"], "http_status": None,
                "provider_outcome": "error", "provider_error_type": name, "case": None,
                "deterministic_checks": {}, "status": "NOT_RUN", "reason": f"Request/provider error ({name})",
                "input_characters": len(text), "approx_input_tokens": (len(text) + 3) // 4,
                "second_message_status": "NOT_SUPPORTED" if case["id"] == "ADV-016" else None,
                "warning": name}


def write_artifacts(directory: Path, metadata: dict, records: list[dict]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    with (directory / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    columns = ["case_id", "native_category", "provider_outcome", "http_status", "status", "reason", "input_characters", "approx_input_tokens", "second_message_status"]
    with (directory / "cases.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: r.get(key) for key in columns} for r in records)
    counts: dict[str, int] = {}
    categories: dict[str, dict[str, int]] = {}
    for record in records:
        counts[record["status"]] = counts.get(record["status"], 0) + 1
        group = categories.setdefault(record["native_category"], {})
        group[record["status"]] = group.get(record["status"], 0) + 1
    metrics = {"records": len(records), "statuses": counts, "by_native_category": categories}
    (directory / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    summary = ["# Failure-mode evaluation run", "", f"Model: {metadata['model']}",
               f"Dataset: {metadata['dataset']['file']} v{metadata['dataset']['version']}",
               f"Cases: {metadata['dataset']['cases_selected']}", "", "## Status counts", ""]
    summary += [f"- {key}: {value}" for key, value in sorted(counts.items())]
    summary += ["", "No qualitative expectation is treated as automatically verified; MANUAL_REVIEW cases require a human read.", ""]
    (directory / "summary.md").write_text("\n".join(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="make live Anthropic calls; costs money")
    parser.add_argument("--ids", help="comma-separated case IDs")
    parser.add_argument("--smoke", action="store_true", help="select ADV-001 and ADV-017 unless --ids is supplied")
    parser.add_argument("--model", default=None)
    parser.add_argument("--stress", action="store_true", help="add three progressively longer ADV-020 variants")
    args = parser.parse_args(argv)
    dataset, all_cases = load_dataset()
    ids = args.ids.split(",") if args.ids else (["ADV-001", "ADV-017"] if args.smoke else None)
    cases = select_cases(all_cases, ids)
    stress = stress_variants(next(c for c in all_cases if c["id"] == "ADV-020")["messages"][0]) if args.stress else []
    calls = len(cases) + len(stress)
    model = args.model or DEFAULT_MODEL
    print(f"Planned provider calls: {calls if args.run else 0} (selected cases: {len(cases)}; stress variants: {len(stress)})")
    print(f"Live-call budget if --run: {calls}. Model: {model}. No credentials or workspace identifiers are displayed.")
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUTPUT_ROOT / f"{stamp}_{model}"
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "unknown"
    meta = {"created_utc": now.isoformat(timespec="seconds"), "mode": "live" if args.run else "dry_run",
            "provider": "anthropic", "model": model, "max_tokens": MAX_TOKENS,
            "sampling": "Anthropic SDK defaults", "git_commit": commit,
            "dataset": {"file": "evaluations/adversarial_cases.json", "name": dataset["dataset"],
                        "version": dataset["version"], "cases_total": len(all_cases), "cases_selected": len(cases)},
            "expected_provider_calls": calls if args.run else 0, "stress_enabled": args.stress,
            "stress_variants": [{"id": x["id"], "input_characters": x["input_characters"], "approx_input_tokens": x["approx_input_tokens"]} for x in stress]}
    records = []
    if args.run:
        provider = AnthropicClient(model=model)
        app = create_app(intake_parser_factory=lambda: IntakeParser(provider))
        with TestClient(app) as api:
            for i, case in enumerate(cases, 1):
                rec = run_case(api, case)
                records.append(rec)
                print(f"[{i}/{calls}] {case['id']}: {rec['status']} ({rec['provider_outcome']})")
            adv020 = next((c for c in all_cases if c["id"] == "ADV-020"), None)
            for variant in stress:
                fake_case = {**adv020, "id": variant["id"], "category": "long_input", "messages": [variant["message"]]}
                rec = run_case(api, fake_case, variant["message"])
                rec["input_characters"] = variant["input_characters"]
                rec["approx_input_tokens"] = variant["approx_input_tokens"]
                records.append(rec)
                print(f"[stress] {variant['id']}: {rec['status']}")
    else:
        records = [{"case_id": c["id"], "native_category": c["category"], "provider_outcome": "not_run",
                    "http_status": None, "status": "NOT_RUN", "reason": "Dry run; no provider calls made",
                    "input_characters": len(c["messages"][0]), "approx_input_tokens": (len(c["messages"][0]) + 3) // 4}
                   for c in cases]
    write_artifacts(run_dir, meta, records)
    try:
        display_path = run_dir.relative_to(ROOT)
    except ValueError:
        display_path = run_dir
    print(f"Artifacts: {display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
