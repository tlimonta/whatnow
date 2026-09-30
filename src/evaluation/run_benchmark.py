"""Run the labelled intake cases against prompt versions and compute section 4 metrics.

From the repository root:
    python -m src.evaluation.run_benchmark                 # dry run: plan and cost estimate only
    python -m src.evaluation.run_benchmark --mock          # fake client, no cost, pipeline check
    python -m src.evaluation.run_benchmark --run --limit 3 # real calls (costs money)
"""

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from src.ai.client import DEFAULT_MODEL, MAX_TOKENS, AnthropicClient, LLMClient
from src.ai.errors import IntakeError, LLMConfigurationError
from src.ai.parser import IntakeParser
from src.ai.prompts import PROMPT_FILES, load_prompt_template, neutralize_delimiters, render_prompt
from src.ai.schema import FACT_FIELDS, IntakeResult
from src.backend.service import CaseService
from src.backend.storage import InMemoryCaseStore
from src.evaluation.metrics import aggregate, score_case, validate_raw

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "evaluations" / "intake_cases.json"
OUTPUT_ROOT = REPO_ROOT / "outputs" / "evaluations"
LAYERS = ("raw", "post_parser")

# USD per million tokens, for the dry-run estimate only. Check current prices before a big run.
PRICES = {"claude-haiku-4-5": (1.0, 5.0), "claude-sonnet-5-5": (2.0, 10.0)}
ASSUMED_OUTPUT_TOKENS = 400


class MockClient:
    """Always answers 'uncertain, nothing known'. Checks the pipeline; its scores mean nothing."""

    model = "mock"

    def complete(self, prompt: str) -> str:
        return json.dumps({
            "case_type": "uncertain_phone_loss",
            "confidence": 0.5,
            "facts": {field: None for field in FACT_FIELDS},
            "missing_fields": list(FACT_FIELDS),
            "evidence": [],
        })


def load_cases(path: Path, limit: int | None = None, ids: list[str] | None = None) -> tuple[dict, list[dict]]:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    if ids:
        unknown = set(ids) - {c["id"] for c in cases}
        if unknown:
            raise SystemExit(f"Unknown case ids: {sorted(unknown)}")
        cases = [c for c in cases if c["id"] in ids]
    if limit is not None:
        cases = cases[:limit]
    return dataset, cases


def build_prompts(versions: list[str], cases: list[dict], neutralize: bool) -> list[dict]:
    calls = []
    for version in versions:
        template = load_prompt_template(version)
        for case in cases:
            sent = neutralize_delimiters(case["input"]) if neutralize else case["input"]
            calls.append({"version": version, "case": case, "sent": sent, "prompt": render_prompt(template, sent)})
    return calls


def estimate(calls: list[dict], model: str) -> str:
    # About 4 characters per token: a rough guide, not a measurement.
    input_tokens = sum(len(c["prompt"]) for c in calls) // 4
    lines = [f"{len(calls)} calls, about {input_tokens:,} input tokens"]
    if model in PRICES:
        price_in, price_out = PRICES[model]
        cost = input_tokens * price_in / 1e6 + len(calls) * ASSUMED_OUTPUT_TOKENS * price_out / 1e6
        lines.append(f"rough cost on {model}: about ${cost:.2f} (assumes {ASSUMED_OUTPUT_TOKENS} output tokens per call)")
    else:
        lines.append(f"no price on file for {model}; check the provider's pricing page")
    return "\n".join(lines)


def workflow_outcome(service: CaseService, message: str, parser_result: dict) -> list[str]:
    """Task ids the merged integration would give this parser result (local, no API call)."""
    case = service.create_case_from_intake(message, IntakeResult.model_validate(parser_result))
    return [task.id for task in case.tasks]


def call_model(client: LLMClient, calls: list[dict], records_path: Path) -> list[dict]:
    """One paid call per (version, case). Records are written as they arrive."""
    parsers = {v: IntakeParser(client, v) for v in {c["version"] for c in calls}}
    # Same path as POST /api/cases after parsing, with a throwaway in-memory store.
    service = CaseService(InMemoryCaseStore())
    records = []
    with records_path.open("w", encoding="utf-8") as out:
        for i, call in enumerate(calls, 1):
            record = {"prompt_version": call["version"], "case_id": call["case"]["id"],
                      "raw_output": None, "provider_error": None,
                      "parser_result": None, "parser_error": None, "parser_warnings": [],
                      "workflow_task_ids": None, "workflow_error": None}
            try:
                record["raw_output"] = client.complete(call["prompt"])
            except LLMConfigurationError:
                raise
            except IntakeError as exc:
                record["provider_error"] = f"{type(exc).__name__}: {exc}"
            if record["raw_output"] is not None:
                try:
                    parsed = parsers[call["version"]].parse_output(record["raw_output"], call["sent"])
                    record["parser_result"] = parsed.result.model_dump(mode="json")
                    record["parser_warnings"] = parsed.warnings
                except IntakeError as exc:
                    record["parser_error"] = type(exc).__name__
            if record["parser_result"] is not None:
                try:
                    record["workflow_task_ids"] = workflow_outcome(
                        service, call["case"]["input"], record["parser_result"]
                    )
                except ValueError as exc:  # WorkflowDataError / WorkflowEvaluationError
                    record["workflow_error"] = type(exc).__name__
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            records.append(record)
            status = "provider error" if record["provider_error"] else "ok"
            print(f"[{i}/{len(calls)}] {call['version']} {call['case']['id']}: {status}", flush=True)
    return records


def score(records: list[dict], cases: list[dict]) -> tuple[dict, list[dict]]:
    by_id = {c["id"]: c for c in cases}
    metrics, rows = {}, []
    for version in sorted({r["prompt_version"] for r in records}):
        metrics[version] = {}
        for layer in LAYERS:
            scores = []
            for r in (r for r in records if r["prompt_version"] == version):
                case = by_id[r["case_id"]]
                if layer == "raw":
                    output, reason = validate_raw(r["raw_output"])
                else:
                    output = r["parser_result"]
                    reason = "provider_error" if r["provider_error"] else f"parser:{r['parser_error']}"
                s = score_case(case, output, r["raw_output"], reason)
                scores.append(s)
                tasks = r["workflow_task_ids"] if layer == "post_parser" else None
                rows.append({"prompt_version": version, "layer": layer, **_row(s),
                             "workflow_tasks": "" if tasks is None else len(tasks)})
            metrics[version][layer] = aggregate(scores)
        metrics[version]["integration"] = integration_summary(
            [r for r in records if r["prompt_version"] == version], by_id
        )
    return metrics, rows


def integration_summary(records: list[dict], by_id: dict[str, dict]) -> dict:
    """What the merged integration does with each parser result, plus parser warnings."""
    stolen = [r for r in records if by_id[r["case_id"]]["expected_case_type"] == "stolen_phone"]
    # No case at all (the API would answer 502) vs a case that was saved without tasks.
    intake_failed = [r["case_id"] for r in stolen if r["parser_result"] is None]
    without_tasks = [r["case_id"] for r in stolen if r["parser_result"] is not None and not r["workflow_task_ids"]]
    warnings: Counter = Counter()
    for r in records:
        # Group by rule, not by field: "set sim_blocked to null: ..." -> "set <field> to null: ..."
        for w in r["parser_warnings"]:
            for field in FACT_FIELDS:
                w = w.replace(field, "<field>")
            warnings[w] += 1
    return {
        "stolen_cases_without_tasks": {"count": len(without_tasks), "total": len(stolen),
                                       "rate": round(len(without_tasks) / len(stolen), 4) if stolen else None},
        "stolen_cases_without_tasks_ids": without_tasks,
        "stolen_cases_intake_failed": {"count": len(intake_failed), "total": len(stolen),
                                       "rate": round(len(intake_failed) / len(stolen), 4) if stolen else None},
        "stolen_cases_intake_failed_ids": intake_failed,
        "workflow_errors": sum(r["workflow_error"] is not None for r in records),
        "parser_warning_counts": dict(warnings.most_common()),
        "out_of_spain": [
            {
                "case_id": r["case_id"],
                "input": by_id[r["case_id"]]["input"],
                "case_type": (r["parser_result"] or {}).get("case_type"),
                "location": ((r["parser_result"] or {}).get("facts") or {}).get("location"),
                "workflow_task_ids": r["workflow_task_ids"],
            }
            for r in records
            if "location_outside_spain" in by_id[r["case_id"]]["tags"]
        ],
    }


def _row(s: dict) -> dict:
    return {
        "case_id": s["case_id"], "language": s["language"], "valid": s["valid"], "invalid_reason": s["invalid_reason"] or "",
        "expected_case_type": s["expected_case_type"], "predicted_case_type": s["predicted_case_type"],
        "class_correct": s["class_correct"], "confidence": s["confidence"],
        "fields_wrong": " ".join(f for f, ok in s["fields_correct"].items() if not ok),
        "missing_fields_correct": s["missing_fields_correct"],
        "filled_nulls": " ".join(s["filled_nulls"]), "bad_evidence": " ".join(s["bad_evidence"]),
        "unquoted_facts": " ".join(s["unquoted_facts"]),
        "unsupported_inference": s["unsupported_inference"],
        "injection_resisted": s.get("injection_resisted", ""),
    }


def run_metadata(client: LLMClient, args: argparse.Namespace, dataset: dict, cases: list[dict]) -> dict:
    def git(*cmd: str) -> str:
        try:
            return subprocess.run(["git", *cmd], cwd=REPO_ROOT, capture_output=True, text=True).stdout.rstrip("\n")
        except OSError:
            return "unknown"

    try:
        sdk = metadata.version("anthropic")
    except metadata.PackageNotFoundError:
        sdk = None
    return {
        "mock": client.model == "mock",
        "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "mock" if client.model == "mock" else "anthropic",
        "model": client.model,
        "sampling": "provider default (anthropic SDK 1.x accepts no temperature)",
        "max_tokens": MAX_TOKENS,
        "anthropic_sdk": sdk,
        "prompt_versions": args.versions,
        "delimiter_neutralization": not args.raw_delimiters,
        "dataset": {"file": "evaluations/intake_cases.json", "version": dataset["version"],
                    "cases_run": len(cases), "cases_total": len(dataset["cases"])},
        "git_commit": git("rev-parse", "--short", "HEAD"),
        # Paths only, so a reader can see whether the code itself was uncommitted.
        # outputs/ is where results land, so it is not counted.
        "git_dirty_files": [
            line[3:] for line in git("status", "--porcelain").splitlines() if not line[3:].startswith("outputs/")
        ],
    }


SUMMARY_ROWS = [
    ("Valid output", "valid_output"),
    ("Classification accuracy", "classification_accuracy"),
    ("Classification (excl. label_debatable)", "classification_accuracy_excluding_debatable"),
    ("Field extraction accuracy", "field_extraction_accuracy"),
    ("missing_fields exactly right", "missing_fields_accuracy"),
    ("Stolen cases classified lost/uncertain (lower is better)", "stolen_classified_lost_or_uncertain"),
    ("Unsupported inference (case rate, lower is better)", "unsupported_inference_case_rate"),
    ("Unsupported inference (field rate, lower is better)", "unsupported_inference_field_rate"),
    ("Ambiguous handling (lenient)", "ambiguous_lenient"),
    ("Ambiguous handling (strict)", "ambiguous_strict"),
    ("Uncertain on non-uncertain cases (lower is better)", "uncertain_on_non_uncertain_cases"),
    ("Parser-level injection resistance", "parser_level_injection_resistance"),
]


def summary_markdown(meta: dict, metrics: dict) -> str:
    def cell(m: dict) -> str:
        return "n/a" if not m["total"] else f"{m['count']}/{m['total']} ({m['rate']:.0%})"

    lines = [f"# Benchmark run {meta['date_utc']}", ""]
    if meta["mock"]:
        lines += ["**MOCK RUN: fake client, not a real model. These numbers mean nothing.**", ""]
    lines += [f"Model `{meta['model']}`, sampling {meta['sampling']}, dataset "
              f"{meta['dataset']['version']} ({meta['dataset']['cases_run']} of {meta['dataset']['cases_total']} cases), "
              f"commit {meta['git_commit']}"
              f"{' (uncommitted: ' + ', '.join(meta['git_dirty_files']) + ')' if meta['git_dirty_files'] else ''}, "
              f"delimiter neutralization {'on' if meta['delimiter_neutralization'] else 'off'}.", ""]
    for version, layers in metrics.items():
        lines += [f"## {version}", "", "| Metric | Raw model output | After parser |", "|---|---|---|"]
        for label, key in SUMMARY_ROWS:
            lines.append(f"| {label} | {cell(layers['raw'][key])} | {cell(layers['post_parser'][key])} |")
        raw, post, integ = layers["raw"], layers["post_parser"], layers["integration"]
        lines += ["", f"Invalid reasons (raw): {raw['invalid_reasons'] or 'none'}. "
                  f"Confident-wrong ambiguous cases (raw): {raw['ambiguous_confident_wrong']}. "
                  f"Unsupported-inference instances (raw): {raw['unsupported_inference_count']}. "
                  f"Unsupported-inference cases that count only because the output is invalid (raw / after parser): "
                  f"{raw['unsupported_inference_cases_invalid']} / {post['unsupported_inference_cases_invalid']}.", ""]
        lines += ["### By language (after parser)", "",
                  "| Language | Cases | Valid | Classification | Field extraction |", "|---|---|---|---|---|"]
        for lang, m in post["by_language"].items():
            lines.append(f"| {lang} | {m['cases']} | {cell(m['valid_output'])} | "
                         f"{cell(m['classification_accuracy'])} | {cell(m['field_extraction_accuracy'])} |")
        lines += ["", "### Integration outcome (merged CaseService + workflow engine, run locally)", "",
                  f"- Stolen-labelled cases saved **without tasks**: "
                  f"{cell(integ['stolen_cases_without_tasks'])} "
                  f"{integ['stolen_cases_without_tasks_ids'] or ''}",
                  f"- Stolen-labelled cases where intake failed (no case, API 502): "
                  f"{cell(integ['stolen_cases_intake_failed'])} "
                  f"{integ['stolen_cases_intake_failed_ids'] or ''}",
                  f"- Stolen cases classified lost/uncertain: {post['stolen_classified_lost_or_uncertain_ids'] or 'none'}",
                  f"- Workflow errors: {integ['workflow_errors']}"]
        for r in integ["out_of_spain"]:
            lines.append(f"- Out of Spain, {r['case_id']} \"{r['input']}\": case_type `{r['case_type']}`, "
                         f"location `{r['location']}`, tasks {r['workflow_task_ids']}")
        lines += ["", "### Parser warnings", ""]
        lines += [f"- {count} × {w}" for w, count in integ["parser_warning_counts"].items()] or ["- none"]
        lines += ["", "### Misclassified cases (after parser)", ""]
        lines += [f"- {m['case_id']}: expected `{m['expected']}`, got `{m['predicted']}` (confidence {m['confidence']})"
                  for m in post["misclassified"]] or ["- none"]
        lines.append("")
    lines += ["Injection resistance checks `must_not` only for URLs and a copied 1.0 confidence; "
              "the other `must_not` items need a manual read of `records.jsonl`.", ""]
    return "\n".join(lines)


def write_results(out_dir: Path, meta: dict, metrics: dict, rows: list[dict]) -> None:
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (out_dir / "cases.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out_dir / "summary.md").write_text(summary_markdown(meta, metrics), encoding="utf-8")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="make real, paid API calls")
    mode.add_argument("--mock", action="store_true", help="use a fake client (no cost, meaningless scores)")
    mode.add_argument("--rescore", type=Path, metavar="RUN_DIR",
                      help="recompute metrics and summary from a saved run's records.jsonl (no API calls)")
    p.add_argument("--versions", nargs="+", default=sorted(PROMPT_FILES), choices=sorted(PROMPT_FILES))
    p.add_argument("--model", default=None, help=f"default: WHATNOW_LLM_MODEL or {DEFAULT_MODEL}")
    p.add_argument("--limit", type=int, default=None, help="only the first N cases")
    p.add_argument("--ids", default=None, help="comma-separated case ids, e.g. IC-001,IC-028")
    p.add_argument("--raw-delimiters", action="store_true",
                   help="do not neutralize <user_message> tags (tests the prompt alone, as IC-028 intends)")
    p.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    return p.parse_args(argv)


def rescore(run_dir: Path) -> int:
    """Score saved raw outputs again, e.g. after a metric fix. The model is not called."""
    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (run_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    dataset, all_cases = load_cases(DATASET)
    if dataset["version"] != meta["dataset"]["version"]:
        print(f"Dataset is now {dataset['version']}, the run used {meta['dataset']['version']}.", file=sys.stderr)
        return 2
    run_ids = {r["case_id"] for r in records}
    if "git_dirty" in meta:  # runs recorded before the file list existed
        meta["git_dirty_files"] = ["(not recorded)"] if meta.pop("git_dirty") else []
    meta["rescored_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metrics, rows = score(records, [c for c in all_cases if c["id"] in run_ids])
    write_results(run_dir, meta, metrics, rows)
    print(f"Rescored {len(records)} records in {run_dir}")
    return 0


def main(argv: list[str] | None = None, client: LLMClient | None = None) -> int:
    args = parse_args(argv)
    if args.rescore:
        return rescore(args.rescore)
    dataset, cases = load_cases(DATASET, args.limit, args.ids.split(",") if args.ids else None)
    calls = build_prompts(args.versions, cases, neutralize=not args.raw_delimiters)
    model = args.model or DEFAULT_MODEL

    if not (args.run or args.mock) and client is None:
        print("DRY RUN: no API calls made.")
        print(estimate(calls, model))
        print("Add --mock for a free pipeline check, or --run to make the real calls.")
        return 0

    if client is None:
        try:
            client = MockClient() if args.mock else AnthropicClient(model=args.model)
        except LLMConfigurationError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 2
    if client.model != "mock":
        print(estimate(calls, client.model))

    # Read git state before the output folder exists, or every run would look "dirty".
    meta = run_metadata(client, args, dataset, cases)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.output_dir / f"{stamp}_{client.model}"
    out_dir.mkdir(parents=True)
    try:
        records = call_model(client, calls, out_dir / "records.jsonl")
    except LLMConfigurationError as exc:
        print(f"Stopped: {exc}. Partial records are in {out_dir}", file=sys.stderr)
        return 2
    metrics, rows = score(records, cases)
    write_results(out_dir, meta, metrics, rows)
    print(f"Results written to {out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
