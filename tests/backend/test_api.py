from datetime import datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.ai.parser import IntakeParser
from src.backend.main import create_app
from src.backend.storage import InMemoryCaseStore
from src.models.case import Case, Task


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_retrieve_case(client: TestClient) -> None:
    message = "  A tax question.  "
    response = client.post("/api/cases", json={"message": message})
    assert response.status_code == 201
    case = response.json()
    assert UUID(case["id"]).version == 4
    assert datetime.fromisoformat(case["created_at"]).utcoffset().total_seconds() == 0
    assert case == {
        "id": case["id"],
        "case_type": "unsupported",
        "status": "intake",
        "risk_level": None,
        "initial_message": message,
        "facts": {
            "location": None,
            "incident_time": None,
            "device_type": None,
            "theft_confirmed": None,
            "banking_apps_present": None,
            "device_locked": None,
            "sim_blocked": None,
        },
        "missing_fields": [],
        "tasks": [],
        "created_at": case["created_at"],
    }
    fetched = client.get(f"/api/cases/{case['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == case


def test_fake_unsupported_intake_has_no_workflow_tasks(client: TestClient) -> None:
    case = client.post("/api/cases", json={"message": "A tax question"}).json()
    assert case["case_type"] == "unsupported"
    assert case["risk_level"] is None
    assert all(value is None for value in case["facts"].values())
    assert case["tasks"] == []


@pytest.mark.parametrize("body", [
    {},
    {"message": ""},
    {"message": " \n\t"},
    {"message": None},
    {"message": 123},
    {"message": []},
    {"message": "Hello", "case_type": "stolen_phone"},
])
def test_invalid_creation_body(client: TestClient, fake_client, body: dict) -> None:
    response = client.post("/api/cases", json=body)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert fake_client.prompts == []


def test_unknown_case(client: TestClient) -> None:
    response = client.get("/api/cases/unknown-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_update_unknown_case(client: TestClient) -> None:
    response = client.patch("/api/cases/unknown/tasks/task", json={"status": "completed"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_update_missing_task_on_empty_case(client: TestClient) -> None:
    case = client.post("/api/cases", json={"message": "Lost phone"}).json()
    response = client.patch(
        f"/api/cases/{case['id']}/tasks/unknown", json={"status": "completed"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
    assert client.get(f"/api/cases/{case['id']}").json() == case


def test_task_updates_are_persisted(client: TestClient, store: InMemoryCaseStore) -> None:
    case = Case(initial_message="Test fixture", tasks=[Task(id="step-1", title="Test task")])
    store.save(case)
    for task_status in ["completed", "completed", "skipped", "pending"]:
        response = client.patch(
            f"/api/cases/{case.id}/tasks/step-1", json={"status": task_status}
        )
        assert response.status_code == 200
        assert response.json()["tasks"][0]["status"] == task_status
        assert client.get(f"/api/cases/{case.id}").json() == response.json()
        assert response.json()["status"] == "intake"


@pytest.mark.parametrize("body", [
    {},
    {"status": "done"},
    {"status": None},
    {"status": "COMPLETED"},
    {"status": "completed", "title": "Changed"},
])
def test_invalid_task_update_does_not_mutate_case(
    client: TestClient, store: InMemoryCaseStore, body: dict
) -> None:
    case = Case(initial_message="Test fixture", tasks=[Task(id="step", title="Test task")])
    store.save(case)
    response = client.patch(f"/api/cases/{case.id}/tasks/step", json=body)
    assert response.status_code == 422
    assert store.get(case.id) == case


def test_app_instances_have_separate_storage(fake_client) -> None:
    parser_factory = lambda: IntakeParser(fake_client)
    with TestClient(create_app(parser_factory)) as first, TestClient(create_app(parser_factory)) as second:
        case = first.post("/api/cases", json={"message": "Lost phone"}).json()
        assert first.get(f"/api/cases/{case['id']}").status_code == 200
        assert second.get(f"/api/cases/{case['id']}").status_code == 404
