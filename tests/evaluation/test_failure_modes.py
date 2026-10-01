import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ai.parser import IntakeParser
from src.ai.schema import FACT_FIELDS
from src.backend.main import create_app
from src.evaluation import run_failure_modes as failure


class FakeClient:
    model = "fake"

    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self.response


def result(case_type="stolen_phone", facts=None, evidence=None):
    return json.dumps({"case_type": case_type, "confidence": 0.8,
                       "facts": {field: None for field in FACT_FIELDS} | (facts or {}),
                       "missing_fields": [], "evidence": evidence or []})


def load_case(case_id):
    _, cases = failure.load_dataset()
    return next(case for case in cases if case["id"] == case_id)


def test_dataset_loads_all_native_categories_unchanged():
    data, cases = failure.load_dataset()
    assert len(cases) == 22
    assert data["version"] == "0.1"
    assert {case["category"] for case in cases} == {
        "prompt_injection", "sycophancy", "sensitive_data", "unsupported_inference",
        "ambiguous", "contradictory_facts", "update", "irrelevant_input",
        "long_input", "instruction_like_text", "multilingual",
    }


def test_case_filtering_and_alternative_case_type():
    _, cases = failure.load_dataset()
    assert [c["id"] for c in failure.select_cases(cases, ["ADV-007"])] == ["ADV-007"]
    with pytest.raises(ValueError, match="Unknown case ids"):
        failure.select_cases(cases, ["ADV-999"])
    observed = {"case_type": "lost_phone", "facts": {}, "missing_fields": [], "tasks": [], "initial_message": "x"}
    scored = failure.score_case(load_case("ADV-007"), observed, 201)
    assert scored["checks"]["case_type"]["passed"]


@pytest.mark.parametrize("observed_type", ["uncertain_phone_loss", "lost_phone"])
def test_adv001_human_readable_case_type_accepts_both_valid_values(observed_type):
    case = load_case("ADV-001")
    observed = {"case_type": observed_type, "facts": {}, "missing_fields": [], "tasks": [], "initial_message": case["messages"][0]}
    assert failure.score_case(case, observed, 201)["checks"]["case_type"]["passed"]


@pytest.mark.parametrize(
    ("case_id", "observed_type"),
    [("ADV-002", "stolen_phone"), ("ADV-017", "unsupported"), ("ADV-007", "uncertain_phone_loss")],
)
def test_case_type_parser_preserves_single_values_and_clean_alternatives(case_id, observed_type):
    case = load_case(case_id)
    observed = {"case_type": observed_type, "facts": {}, "missing_fields": [], "tasks": [], "initial_message": case["messages"][0]}
    assert failure.score_case(case, observed, 201)["checks"]["case_type"]["passed"]


def test_must_be_null_and_missing_fields_are_deterministic():
    case = load_case("ADV-010")
    facts = {field: None for field in FACT_FIELDS}
    facts["theft_confirmed"] = True
    response = {"case_type": "stolen_phone", "facts": facts,
                "missing_fields": ["location", "incident_time", "device_type", "banking_apps_present", "device_locked", "sim_blocked"],
                "tasks": [], "initial_message": case["messages"][0]}
    checks = failure.score_case(case, response, 201)["checks"]
    assert checks["null:location"]["passed"]
    assert checks["missing:location"]["passed"]
    assert checks["case_type"]["passed"]


def test_facts_supported_by_text_and_sensitive_structured_output():
    case = load_case("ADV-002")
    response = {"case_type": "stolen_phone", "facts": {field: None for field in FACT_FIELDS} | {"theft_confirmed": True},
                "missing_fields": [], "tasks": [], "initial_message": case["messages"][0]}
    score = failure.score_case(case, response, 201)
    assert score["checks"]["fact:theft_confirmed"]["passed"]
    sensitive_case = load_case("ADV-006")
    response["initial_message"] = sensitive_case["messages"][0]
    response["facts"]["theft_confirmed"] = None
    failure.score_case(sensitive_case, response, 201)
    score = failure.score_case(sensitive_case, response, 201)
    assert score["checks"]["raw_message_storage_gap"]["observed_sensitive_values_in_initial_message"] == ["1234"]
    response["facts"]["device_locked"] = "PIN 1234"
    score = failure.score_case(sensitive_case, response, 201)
    assert not score["checks"]["sensitive_values_in_structured_output"]["passed"]


def test_task_provenance_and_status_are_recorded():
    case = load_case("ADV-021")
    task = {"id": "stolen_phone_es_01", "status": "pending", "workflow_id": "stolen_phone_es", "source_id": "policia_nacional_denuncia"}
    response = {"case_type": "stolen_phone", "facts": {}, "missing_fields": [], "tasks": [task], "initial_message": case["messages"][0]}
    scored = failure.score_case(case, response, 201)
    assert scored["checks"]["task_provenance"]["passed"]
    assert scored["checks"]["task_ids_and_statuses"]["passed"]
    assert scored["checks"]["task_provenance"]["observed"][0]["status"] == "pending"
    task["id"] = "unverified_task"
    scored = failure.score_case(case, response, 201)
    assert not scored["checks"]["task_ids_and_statuses"]["passed"]


def test_qualitative_manual_review_not_forced_to_pass_or_fail():
    case = load_case("ADV-001")
    response = {"case_type": "uncertain_phone_loss", "facts": {field: None for field in FACT_FIELDS},
                "missing_fields": list(FACT_FIELDS), "tasks": [], "initial_message": case["messages"][0]}
    scored = failure.score_case(case, response, 201)
    assert scored["status"] == "MANUAL_REVIEW"
    assert failure.score_case(case, response, 500)["status"] == "FAIL"
    assert failure.score_case(load_case("ADV-016"), response, 201, second_message_supported=False)["status"] == "NOT_SUPPORTED"


def test_provider_error_is_recorded_without_exception_text(monkeypatch):
    case = load_case("ADV-001")
    def broken(*args, **kwargs):
        raise RuntimeError("secret user content")
    monkeypatch.setattr(TestClient, "post", broken)
    record = failure.run_case(TestClient(create_app(intake_parser_factory=lambda: None)), case)
    assert record["status"] == "NOT_RUN"
    assert record["provider_error_type"] == "RuntimeError"
    assert "secret user content" not in json.dumps(record)


def test_dry_run_makes_zero_provider_calls_and_writes_artifacts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(failure, "OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(failure, "AnthropicClient", lambda **kw: (_ for _ in ()).throw(AssertionError("called")))
    assert failure.main(["--ids", "ADV-001"]) == 0
    output = capsys.readouterr().out
    assert "Planned provider calls: 0" in output
    run = next(tmp_path.iterdir())
    assert {"metadata.json", "records.jsonl", "cases.csv", "metrics.json", "summary.md"} <= {p.name for p in run.iterdir()}
    assert json.loads((run / "metadata.json").read_text())["mode"] == "dry_run"


def test_integrated_fastapi_path_uses_stub_client_and_real_workflow():
    case = load_case("ADV-002")
    message = case["messages"][0]
    fake = FakeClient(result("stolen_phone", {"location": "Madrid", "device_type": "iphone", "theft_confirmed": True},
                             [{"field": "location", "user_text": "Madrid"}, {"field": "device_type", "user_text": "iPhone"}, {"field": "theft_confirmed", "user_text": "stolen"}]))
    with TestClient(create_app(intake_parser_factory=lambda: IntakeParser(fake))) as api:
        record = failure.run_case(api, case)
    assert fake.calls == 1
    assert record["http_status"] == 201
    assert record["case"]["tasks"]
    assert all(task["workflow_id"] == "stolen_phone_es" for task in record["case"]["tasks"])


def test_stress_variants_repeat_prose_and_keep_core_theft_sentence():
    message = load_case("ADV-020")["messages"][0]
    variants = failure.stress_variants(message)
    core = "someone grabbed my phone out of my hand and ran away, it was an iPhone."
    assert [v["id"] for v in variants] == ["ADV-020-STRESS-x2", "ADV-020-STRESS-x4", "ADV-020-STRESS-x8"]
    assert all(v["message"].count(core) == 1 for v in variants)
    assert variants[-1]["input_characters"] > variants[0]["input_characters"]
