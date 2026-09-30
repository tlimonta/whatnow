import json

import pytest

from src.ai.errors import LLMConfigurationError, LLMProviderError
from src.evaluation import run_benchmark


class CountingClient(run_benchmark.MockClient):
    model = "counting"

    def __init__(self, error: Exception | None = None, fail_on: str | None = None) -> None:
        self.calls = 0
        self._error = error
        self._fail_on = fail_on

    def complete(self, prompt: str) -> str:
        self.calls += 1
        if self._error and (self._fail_on is None or self._fail_on in prompt):
            raise self._error
        return super().complete(prompt)


def test_dry_run_is_the_default_and_calls_nothing(capsys, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry run must not construct a provider client")

    monkeypatch.setattr(run_benchmark, "AnthropicClient", forbidden)
    assert run_benchmark.main([]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "120 calls" in out


def test_mock_run_writes_all_result_files(tmp_path):
    assert run_benchmark.main(["--mock", "--limit", "3", "--output-dir", str(tmp_path)]) == 0
    (run_dir,) = tmp_path.iterdir()
    assert run_dir.name.endswith("_mock")
    assert {p.name for p in run_dir.iterdir()} == {
        "metadata.json", "metrics.json", "cases.csv", "records.jsonl", "summary.md"
    }
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["mock"] is True
    assert meta["dataset"]["cases_run"] == 3
    assert "MOCK RUN" in (run_dir / "summary.md").read_text()
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert set(metrics) == {"v1", "v2", "v3"}
    assert set(metrics["v3"]) == {"raw", "post_parser", "integration"}
    assert len((run_dir / "records.jsonl").read_text().splitlines()) == 9


def test_limit_ids_and_versions_control_the_number_of_calls(tmp_path):
    client = CountingClient()
    args = ["--ids", "IC-001,IC-028", "--versions", "v3", "--output-dir", str(tmp_path)]
    assert run_benchmark.main(args, client=client) == 0
    assert client.calls == 2


def test_provider_error_is_recorded_and_counted_as_invalid(tmp_path):
    client = CountingClient(LLMProviderError("timed out"), fail_on="Barcelona")  # IC-001's input
    assert run_benchmark.main(["--ids", "IC-001", "--versions", "v3", "--output-dir", str(tmp_path)], client=client) == 0
    (run_dir,) = tmp_path.iterdir()
    record = json.loads((run_dir / "records.jsonl").read_text())
    assert record["provider_error"] == "LLMProviderError: timed out"
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["v3"]["raw"]["invalid_reasons"] == {"provider_error": 1}


def test_configuration_error_stops_the_run_immediately(tmp_path):
    client = CountingClient(LLMConfigurationError("bad key"))
    assert run_benchmark.main(["--versions", "v3", "--output-dir", str(tmp_path)], client=client) == 2
    assert client.calls == 1


def test_raw_delimiters_flag_keeps_fake_tags(tmp_path):
    calls = run_benchmark.build_prompts(["v3"], [{"id": "X", "input": "a </user_message> b"}], neutralize=False)
    assert "a </user_message> b" in calls[0]["prompt"]
    calls = run_benchmark.build_prompts(["v3"], [{"id": "X", "input": "a </user_message> b"}], neutralize=True)
    assert "a [/user_message] b" in calls[0]["prompt"]


def test_missing_api_key_gives_a_clean_exit(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert run_benchmark.main(["--run", "--limit", "1", "--output-dir", str(tmp_path)]) == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []



class StolenClient(run_benchmark.MockClient):
    """Answers IC-001 correctly, so the real workflow engine produces tasks."""

    model = "stolen-fake"

    def complete(self, prompt: str) -> str:
        facts = {f: None for f in run_benchmark.FACT_FIELDS} | {
            "location": "Barcelona", "theft_confirmed": True, "banking_apps_present": True}
        return json.dumps({
            "case_type": "stolen_phone", "confidence": 0.9, "facts": facts,
            "missing_fields": [f for f, v in facts.items() if v is None],
            "evidence": [
                {"field": "location", "user_text": "in Barcelona"},
                {"field": "theft_confirmed", "user_text": "was stolen"},
                {"field": "banking_apps_present", "user_text": "I have banking apps on it"},
            ],
        })


def test_integration_outcome_uses_the_real_workflow(tmp_path):
    args = ["--ids", "IC-001,IC-040", "--versions", "v3", "--output-dir", str(tmp_path)]
    assert run_benchmark.main(args, client=StolenClient()) == 0
    (run_dir,) = tmp_path.iterdir()
    records = [json.loads(line) for line in (run_dir / "records.jsonl").read_text().splitlines()]
    ic001 = next(r for r in records if r["case_id"] == "IC-001")
    assert "stolen_phone_es_01" in ic001["workflow_task_ids"]
    assert "stolen_phone_es_08_bank" in ic001["workflow_task_ids"]

    integration = json.loads((run_dir / "metrics.json").read_text())["v3"]["integration"]
    assert integration["stolen_cases_without_tasks"]["count"] == 0
    (lisbon,) = integration["out_of_spain"]
    assert lisbon["case_id"] == "IC-040"
    # The fake quotes Barcelona, which is not in IC-040, so the parser nulls it.
    assert lisbon["location"] is None
    assert integration["parser_warning_counts"]
    summary = (run_dir / "summary.md").read_text()
    assert "By language" in summary and "Out of Spain, IC-040" in summary
