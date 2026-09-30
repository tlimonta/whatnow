import json
import sys

import pytest
from fastapi.testclient import TestClient

from src.ai.errors import LLMProviderError
from src.ai.parser import IntakeParser
from src.ai.schema import FACT_FIELDS
from src.backend.main import create_app, get_case_service
from src.backend.service import CaseService
from src.backend.storage import InMemoryCaseStore
from src.backend.workflow_engine import (
    DEFAULT_WORKFLOW_PATH,
    WorkflowDataError,
    WorkflowEngine,
    WorkflowEvaluationError,
)


def model_output(
    case_type: str | None,
    facts: dict[str, object] | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps(
        {
            "case_type": case_type,
            "confidence": 0.91,
            "facts": {field: None for field in FACT_FIELDS} | (facts or {}),
            "missing_fields": [],
            "evidence": evidence or [],
        }
    )


STOLEN_MESSAGE = "My iPhone was stolen in Madrid and I have banking apps on it."
STOLEN_FACTS = {
    "location": "Madrid",
    "device_type": "iphone",
    "theft_confirmed": True,
    "banking_apps_present": True,
}
STOLEN_EVIDENCE = [
    {"field": "location", "user_text": "in Madrid"},
    {"field": "device_type", "user_text": "iPhone"},
    {"field": "theft_confirmed", "user_text": "was stolen"},
    {"field": "banking_apps_present", "user_text": "I have banking apps on it"},
]


def test_stolen_intake_is_mapped_workflow_backed_and_retrievable(
    client: TestClient, fake_client, service: CaseService
) -> None:
    fake_client.response = model_output(
        "stolen_phone", STOLEN_FACTS, STOLEN_EVIDENCE
    )

    response = client.post("/api/cases", json={"message": STOLEN_MESSAGE})

    assert response.status_code == 201
    case = response.json()
    assert case["case_type"] == "stolen_phone"
    assert case["initial_message"] == STOLEN_MESSAGE
    assert case["status"] == "intake"
    assert case["risk_level"] is None
    assert case["facts"] == {field: STOLEN_FACTS.get(field) for field in FACT_FIELDS}
    assert case["missing_fields"] == [
        "incident_time", "device_locked", "sim_blocked"
    ]
    assert "confidence" not in case
    assert "evidence" not in case
    assert "warnings" not in case
    assert "raw_output" not in case
    assert len(fake_client.prompts) == 1

    verified_steps = {
        step["id"]: step
        for step in json.loads(DEFAULT_WORKFLOW_PATH.read_text(encoding="utf-8"))["steps"]
    }
    assert [task["id"] for task in case["tasks"]] == [
        "stolen_phone_es_01", "stolen_phone_es_08_bank"
    ]
    for task in case["tasks"]:
        step = verified_steps[task["id"]]
        assert task["title"] == step["title"]
        assert task["description"] == step["description"]
        assert task["priority"] == step["priority"]
        assert task["workflow_id"] == "stolen_phone_es"
        assert task["source_id"] == step["source_id"]
        assert task["status"] == "pending"

    assert client.get(f"/api/cases/{case['id']}").json() == case

    completed = client.patch(
        f"/api/cases/{case['id']}/tasks/stolen_phone_es_08_bank",
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["tasks"][1]["status"] == "completed"
    assert client.get(f"/api/cases/{case['id']}").json() == completed.json()

    recalculated = WorkflowEngine.from_files().apply_to_case(
        service.get_case(case["id"])
    )
    assert recalculated == service.get_case(case["id"])


@pytest.mark.parametrize(
    "banking_value,banking_evidence,expected_bank_task",
    [
        (True, [{"field": "banking_apps_present", "user_text": "banking apps"}], True),
        (False, [{"field": "banking_apps_present", "user_text": "no banking apps"}], False),
        (None, [], False),
    ],
)
def test_banking_condition_requires_definite_true(
    client: TestClient,
    fake_client,
    banking_value: bool | None,
    banking_evidence: list[dict[str, str]],
    expected_bank_task: bool,
) -> None:
    if banking_value is True:
        message = "My phone was stolen. I have banking apps."
    elif banking_value is False:
        message = "My phone was stolen. I have no banking apps."
    else:
        message = "My phone was stolen."
    fake_client.response = model_output(
        "stolen_phone",
        {"theft_confirmed": True, "banking_apps_present": banking_value},
        [{"field": "theft_confirmed", "user_text": "was stolen"}]
        + banking_evidence,
    )

    response = client.post("/api/cases", json={"message": message})

    assert response.status_code == 201
    case = response.json()
    assert case["facts"]["banking_apps_present"] is banking_value
    assert ("stolen_phone_es_08_bank" in {task["id"] for task in case["tasks"]}) is expected_bank_task
    assert "stolen_phone_es_01" in {task["id"] for task in case["tasks"]}


@pytest.mark.parametrize(
    "case_type", ["unsupported", "lost_phone", "uncertain_phone_loss"]
)
def test_other_case_types_do_not_get_stolen_phone_tasks(
    client: TestClient, fake_client, case_type: str
) -> None:
    fake_client.response = model_output(case_type)

    response = client.post("/api/cases", json={"message": "My phone is missing."})

    assert response.status_code == 201
    case = response.json()
    assert case["case_type"] == case_type
    assert case["tasks"] == []
    assert case["risk_level"] is None
    assert case["missing_fields"] == ([] if case_type == "unsupported" else list(FACT_FIELDS))


@pytest.mark.parametrize(
    "raw_output",
    [
        "not json",
        model_output(None),
        model_output("stolen_phone", {"banking_apps_present": "yes"}),
    ],
)
def test_invalid_model_output_fails_without_saving(
    client: TestClient, fake_client, store: InMemoryCaseStore, raw_output: str
) -> None:
    fake_client.response = raw_output

    response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 502
    assert response.json() == {"detail": "AI intake response was invalid"}
    assert store._cases == {}


def test_provider_failure_is_safe_and_does_not_save(
    client: TestClient, fake_client, store: InMemoryCaseStore
) -> None:
    fake_client.response = LLMProviderError("secret-provider-token")

    response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 502
    assert response.json() == {"detail": "AI provider request failed"}
    assert "secret-provider-token" not in response.text
    assert store._cases == {}


def test_missing_configuration_is_safe_and_only_checked_on_valid_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/api/cases", json={}).status_code == 422
        response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 503
    assert response.json() == {"detail": "AI intake is not configured"}
    assert "ANTHROPIC_API_KEY" not in response.text


def test_missing_provider_package_is_a_safe_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-key")
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with TestClient(create_app()) as client:
        response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 503
    assert response.json() == {"detail": "AI intake is not configured"}
    assert "test-only-key" not in response.text


def test_missing_provider_submodule_is_a_safe_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_client() -> None:
        raise ModuleNotFoundError(
            "provider import failed", name="anthropic.types.beta.missing_module"
        )

    monkeypatch.setattr("src.backend.main.AnthropicClient", broken_client)
    with TestClient(create_app()) as client:
        response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 503
    assert response.json() == {"detail": "AI intake is not configured"}


@pytest.mark.parametrize("error", [WorkflowDataError("secret"), WorkflowEvaluationError("secret")])
def test_workflow_failure_is_safe_and_does_not_save(
    fake_client, store: InMemoryCaseStore, error: Exception
) -> None:
    fake_client.response = model_output(
        "stolen_phone",
        {"theft_confirmed": True},
        [{"field": "theft_confirmed", "user_text": "was stolen"}],
    )

    def broken_workflow() -> WorkflowEngine:
        raise error

    service = CaseService(store, workflow_factory=broken_workflow)
    app = create_app(intake_parser_factory=lambda: IntakeParser(fake_client))
    app.dependency_overrides[get_case_service] = lambda: service
    with TestClient(app) as client:
        response = client.post("/api/cases", json={"message": "My phone was stolen."})

    assert response.status_code == 503
    assert response.json() == {"detail": "Verified workflow unavailable"}
    assert "secret" not in response.text
    assert store._cases == {}
