from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from src.backend.service import CaseNotFoundError, CaseService, TaskNotFoundError
from src.backend.storage import InMemoryCaseStore
from src.models.case import Case, Task, TaskStatus


def test_creation_has_unique_ids_and_is_saved(service: CaseService) -> None:
    first = service.create_case("Lost phone")
    second = service.create_case("Lost phone")
    assert first.id != second.id
    assert service.get_case(first.id) == first
    assert first.case_type is None
    assert first.risk_level is None
    assert first.tasks == []


def test_service_rejects_blank_message(service: CaseService) -> None:
    with pytest.raises(ValidationError):
        service.create_case(" \t")


def test_unknown_case_raises_domain_error(service: CaseService) -> None:
    with pytest.raises(CaseNotFoundError):
        service.get_case("missing")
    with pytest.raises(CaseNotFoundError):
        service.update_task_status("missing", "step", TaskStatus.COMPLETED)


def test_task_is_scoped_to_its_case(service: CaseService, store: InMemoryCaseStore) -> None:
    first = service.create_case("First case")
    second = Case(initial_message="Second case", tasks=[Task(id="step", title="Test task")])
    store.save(second)
    with pytest.raises(TaskNotFoundError):
        service.update_task_status(first.id, "step", TaskStatus.COMPLETED)
    assert service.get_case(second.id) == second


def test_invalid_status_does_not_mutate_storage(
    service: CaseService, store: InMemoryCaseStore
) -> None:
    case = Case(initial_message="Fixture", tasks=[Task(id="step", title="Test task")])
    store.save(case)
    with pytest.raises(ValueError):
        service.update_task_status(case.id, "step", "done")  # type: ignore[arg-type]
    assert service.get_case(case.id) == case


def test_concurrent_updates_preserve_other_tasks(
    service: CaseService, store: InMemoryCaseStore
) -> None:
    case = Case(initial_message="Fixture", tasks=[Task(title=f"Test {i}") for i in range(20)])
    store.save(case)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = [
            executor.submit(service.update_task_status, case.id, task.id, TaskStatus.COMPLETED)
            for task in case.tasks
        ]
        for result in results:
            result.result()
    saved = service.get_case(case.id)
    assert all(task.status == TaskStatus.COMPLETED for task in saved.tasks)
    assert saved.status == case.status
    assert saved.initial_message == case.initial_message
    assert saved.created_at == case.created_at


def test_storage_copies_nested_data_on_read_and_write(store: InMemoryCaseStore) -> None:
    case = Case(
        initial_message="Fixture",
        facts={"device": {"name": None}},
        tasks=[Task(title="Test task")],
    )
    store.save(case)
    case.facts["device"]["name"] = "changed"
    case.tasks[0].status = TaskStatus.COMPLETED
    fetched = store.get(case.id)
    assert fetched.facts["device"]["name"] is None
    assert fetched.tasks[0].status == TaskStatus.PENDING
    fetched.tasks.clear()
    fetched.facts.clear()
    assert len(store.get(case.id).tasks) == 1
    assert store.get(case.id).facts == {"device": {"name": None}}


def test_new_store_is_empty(store: InMemoryCaseStore) -> None:
    case = Case(initial_message="Fixture")
    store.save(case)
    assert InMemoryCaseStore().get(case.id) is None
