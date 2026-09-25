import pytest
from pydantic import ValidationError

from src.models.case import Case, CaseStatus, CaseType, RiskLevel, Task, TaskStatus


@pytest.mark.parametrize("field,enum_type", [
    ("case_type", CaseType), ("status", CaseStatus), ("risk_level", RiskLevel)
])
def test_all_supported_case_values(field: str, enum_type: type) -> None:
    for value in enum_type:
        case = Case(initial_message="Fixture", **{field: value.value})
        assert getattr(case, field) == value


@pytest.mark.parametrize("field,value", [
    ("case_type", "phone"), ("status", "done"), ("status", None),
    ("risk_level", "urgent"), ("initial_message", " \n"), ("id", ""),
    ("created_at", "2026-09-23T12:00:00"), ("missing_fields", [""])
])
def test_invalid_case_values(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Case.model_validate({"initial_message": "Fixture", field: value})


@pytest.mark.parametrize("status", list(TaskStatus))
def test_supported_task_statuses(status: TaskStatus) -> None:
    assert Task(title="Test task", status=status.value).status == status


@pytest.mark.parametrize("fields", [
    {"status": "done"},
    {"status": None},
    {"title": " "},
    {"id": ""},
    {"unexpected": True},
])
def test_invalid_task_values(fields: dict) -> None:
    with pytest.raises(ValidationError):
        Task.model_validate({"title": "Test task", **fields})


def test_unknown_values_remain_null() -> None:
    case = Case(initial_message="Fixture", facts={"country": None, "has_backup": None})
    serialized = case.model_dump(mode="json")
    assert serialized["case_type"] is None
    assert serialized["risk_level"] is None
    assert serialized["facts"] == {"country": None, "has_backup": None}


def test_mutable_defaults_are_not_shared() -> None:
    first = Case(initial_message="First")
    second = Case(initial_message="Second")
    first.facts["country"] = None
    first.missing_fields.append("country")
    first.tasks.append(Task(title="Test task"))
    assert second.facts == {}
    assert second.missing_fields == []
    assert second.tasks == []


def test_assignment_is_validated() -> None:
    task = Task(title="Test task")
    with pytest.raises(ValidationError):
        task.status = "done"
    case = Case(initial_message="Fixture")
    with pytest.raises(ValidationError):
        case.risk_level = "urgent"
