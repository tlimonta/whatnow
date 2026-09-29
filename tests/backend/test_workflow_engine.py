import json
from pathlib import Path

import pytest

from src.backend.workflow_engine import (
    DEFAULT_SOURCES_PATH,
    DEFAULT_WORKFLOW_PATH,
    WorkflowDataError,
    WorkflowEngine,
    WorkflowEvaluationError,
)
from src.models.case import Case, CaseType, Task, TaskStatus


@pytest.fixture
def engine() -> WorkflowEngine:
    return WorkflowEngine.from_files()


def stolen_case(**facts: object) -> Case:
    return Case(
        initial_message="Structured test fixture",
        case_type=CaseType.STOLEN_PHONE,
        facts=facts,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_loads_real_workflow(engine: WorkflowEngine) -> None:
    assert engine.workflow_id == "stolen_phone_es"
    assert len(engine.step_ids) == 9
    assert "stolen_phone_es_01" in engine.step_ids


def test_loads_and_validates_real_sources(engine: WorkflowEngine) -> None:
    assert len(engine.source_ids) == 9
    assert "policia_nacional_denuncia" in engine.source_ids
    assert "bde_uso_fraudulento_tarjeta" in engine.source_ids


def test_stolen_phone_gets_only_definitively_applicable_tasks(
    engine: WorkflowEngine,
) -> None:
    tasks = engine.evaluate(stolen_case())
    assert [task.id for task in tasks] == ["stolen_phone_es_01"]
    assert tasks[0].title == "File a police report (denuncia)"
    assert tasks[0].source_id == "policia_nacional_denuncia"


def test_true_condition_activates_verified_bank_action(engine: WorkflowEngine) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    tasks = case.tasks
    assert [task.id for task in tasks] == [
        "stolen_phone_es_01",
        "stolen_phone_es_08_bank",
    ]
    assert all(task.status == TaskStatus.PENDING for task in tasks)


def test_false_condition_does_not_activate_bank_action(engine: WorkflowEngine) -> None:
    task_ids = {
        task.id
        for task in engine.evaluate(stolen_case(banking_apps_present=False))
    }
    assert "stolen_phone_es_08_bank" not in task_ids


@pytest.mark.parametrize("facts", [{}, {"banking_apps_present": None}])
def test_unknown_condition_is_not_guessed(
    engine: WorkflowEngine, facts: dict[str, object]
) -> None:
    task_ids = {task.id for task in engine.evaluate(stolen_case(**facts))}
    assert "stolen_phone_es_08_bank" not in task_ids


@pytest.mark.parametrize(
    "case_type",
    [None, CaseType.LOST_PHONE, CaseType.UNCERTAIN_PHONE_LOSS, CaseType.UNSUPPORTED],
)
def test_non_applicable_case_type_produces_no_tasks(
    engine: WorkflowEngine, case_type: CaseType | None
) -> None:
    case = Case(
        initial_message="Structured test fixture",
        case_type=case_type,
        facts={"banking_apps_present": True},
    )
    assert engine.evaluate(case) == []


def test_repeated_application_does_not_duplicate_tasks(engine: WorkflowEngine) -> None:
    once = engine.apply_to_case(stolen_case(banking_apps_present=True))
    twice = engine.apply_to_case(once)
    assert twice == once
    assert len({task.id for task in twice.tasks}) == len(twice.tasks) == 2


@pytest.mark.parametrize("new_value", [False, None])
def test_pending_task_is_removed_when_condition_is_no_longer_true(
    engine: WorkflowEngine, new_value: bool | None
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    case.facts["banking_apps_present"] = new_value

    recalculated = engine.apply_to_case(case)

    assert [task.id for task in recalculated.tasks] == ["stolen_phone_es_01"]


@pytest.mark.parametrize("historical_status", [TaskStatus.COMPLETED, TaskStatus.SKIPPED])
def test_historical_task_remains_when_condition_becomes_false(
    engine: WorkflowEngine, historical_status: TaskStatus
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    bank_task = next(task for task in case.tasks if task.id == "stolen_phone_es_08_bank")
    bank_task.status = historical_status
    case.facts["banking_apps_present"] = False

    recalculated = engine.apply_to_case(case)

    preserved = next(
        task for task in recalculated.tasks if task.id == "stolen_phone_es_08_bank"
    )
    assert preserved.status == historical_status


@pytest.mark.parametrize("case_type", [None, CaseType.UNSUPPORTED])
def test_non_applicable_case_type_removes_pending_workflow_tasks(
    engine: WorkflowEngine, case_type: CaseType | None
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    case.case_type = case_type

    recalculated = engine.apply_to_case(case)

    assert recalculated.tasks == []


@pytest.mark.parametrize("case_type", [None, CaseType.UNSUPPORTED])
@pytest.mark.parametrize(
    "historical_status", [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
)
def test_non_applicable_case_type_preserves_historical_workflow_tasks(
    engine: WorkflowEngine,
    case_type: CaseType | None,
    historical_status: TaskStatus,
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    police_task = next(task for task in case.tasks if task.id == "stolen_phone_es_01")
    police_task.status = historical_status
    case.case_type = case_type

    recalculated = engine.apply_to_case(case)

    assert [(task.id, task.status) for task in recalculated.tasks] == [
        ("stolen_phone_es_01", historical_status)
    ]


def test_completed_and_skipped_states_survive_recalculation(
    engine: WorkflowEngine,
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    case.tasks[0].status = TaskStatus.COMPLETED
    case.tasks[1].status = TaskStatus.SKIPPED

    recalculated = engine.apply_to_case(case)

    assert [task.status for task in recalculated.tasks] == [
        TaskStatus.COMPLETED,
        TaskStatus.SKIPPED,
    ]


def test_generated_tasks_are_backed_by_real_workflow_and_sources(
    engine: WorkflowEngine,
) -> None:
    workflow = load_json(DEFAULT_WORKFLOW_PATH)
    steps = {step["id"]: step for step in workflow["steps"]}
    for task in engine.evaluate(stolen_case(banking_apps_present=True)):
        step = steps[task.id]
        assert task.workflow_id == workflow["workflow_id"]
        assert task.title == step["title"]
        assert task.description == step["description"]
        assert task.priority == step["priority"]
        assert task.source_id == step["source_id"]
        assert task.source_id in engine.source_ids


def test_unknown_source_reference_fails_clearly(tmp_path: Path) -> None:
    workflow = load_json(DEFAULT_WORKFLOW_PATH)
    workflow["steps"][0]["source_id"] = "missing_source"
    workflow_path = tmp_path / "workflow.json"
    write_json(workflow_path, workflow)

    with pytest.raises(WorkflowDataError, match="unknown source IDs: missing_source"):
        WorkflowEngine.from_files(workflow_path, DEFAULT_SOURCES_PATH)


def test_malformed_workflow_json_fails_clearly(tmp_path: Path) -> None:
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(WorkflowDataError, match="Invalid JSON"):
        WorkflowEngine.from_files(workflow_path, DEFAULT_SOURCES_PATH)


def test_invalid_source_record_fails_clearly(tmp_path: Path) -> None:
    sources = load_json(DEFAULT_SOURCES_PATH)
    sources["sources"][0]["url"] = "not-an-http-url"
    sources_path = tmp_path / "sources.json"
    write_json(sources_path, sources)

    with pytest.raises(WorkflowDataError, match="Invalid source structure"):
        WorkflowEngine.from_files(DEFAULT_WORKFLOW_PATH, sources_path)


def test_mismatched_source_catalog_fails_clearly(tmp_path: Path) -> None:
    sources = load_json(DEFAULT_SOURCES_PATH)
    sources["workflow_id"] = "different_workflow"
    sources_path = tmp_path / "sources.json"
    write_json(sources_path, sources)

    with pytest.raises(WorkflowDataError, match="workflow_id values do not match"):
        WorkflowEngine.from_files(DEFAULT_WORKFLOW_PATH, sources_path)


def test_changed_prose_condition_fails_instead_of_being_guessed(tmp_path: Path) -> None:
    workflow = load_json(DEFAULT_WORKFLOW_PATH)
    workflow["steps"][1]["condition"] = "A new condition with no evaluator."
    workflow_path = tmp_path / "workflow.json"
    write_json(workflow_path, workflow)

    with pytest.raises(WorkflowDataError, match="changed and is not supported"):
        WorkflowEngine.from_files(workflow_path, DEFAULT_SOURCES_PATH)


def test_invalid_condition_fact_type_fails_clearly(engine: WorkflowEngine) -> None:
    with pytest.raises(WorkflowEvaluationError, match="must be true, false, or null"):
        engine.evaluate(stolen_case(banking_apps_present="yes"))


def test_existing_non_workflow_task_is_preserved(engine: WorkflowEngine) -> None:
    manual_task = Task(id="manual", title="Existing task", status=TaskStatus.COMPLETED)
    case = stolen_case(banking_apps_present=False)
    case.tasks.append(manual_task)

    updated = engine.apply_to_case(case)

    assert updated.tasks[0] == manual_task
    assert updated.tasks[1].id == "stolen_phone_es_01"


def test_reconciliation_does_not_touch_unrelated_or_other_workflow_tasks(
    engine: WorkflowEngine,
) -> None:
    case = engine.apply_to_case(stolen_case(banking_apps_present=True))
    manual_task = Task(id="manual", title="Existing task", status=TaskStatus.COMPLETED)
    other_workflow_task = Task(
        id="other-step",
        title="Other workflow task",
        status=TaskStatus.PENDING,
        workflow_id="other_workflow",
        source_id="other_source",
    )
    case.tasks.extend([manual_task, other_workflow_task])
    case.facts["banking_apps_present"] = False

    recalculated = engine.apply_to_case(case)

    assert manual_task in recalculated.tasks
    assert other_workflow_task in recalculated.tasks
    assert "stolen_phone_es_08_bank" not in {
        task.id for task in recalculated.tasks
    }


def test_deterministic_id_collision_fails_clearly(engine: WorkflowEngine) -> None:
    case = stolen_case()
    case.tasks.append(Task(id="stolen_phone_es_01", title="Unrelated task"))

    with pytest.raises(WorkflowEvaluationError, match="conflicts"):
        engine.apply_to_case(case)
