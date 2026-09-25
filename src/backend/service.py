"""Application logic independent of HTTP and future AI providers."""

from threading import RLock

from src.backend.storage import InMemoryCaseStore
from src.models.case import Case, TaskStatus


class CaseNotFoundError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class CaseService:
    def __init__(self, store: InMemoryCaseStore) -> None:
        self._store = store
        # One service per app serializes read-modify-write operations across requests.
        self._lock = RLock()

    def create_case(self, message: str) -> Case:
        case = Case(initial_message=message)
        with self._lock:
            self._store.save(case)
        return case

    def get_case(self, case_id: str) -> Case:
        with self._lock:
            case = self._store.get(case_id)
        if case is None:
            raise CaseNotFoundError(case_id)
        return case

    def update_task_status(
        self, case_id: str, task_id: str, status: TaskStatus
    ) -> Case:
        validated_status = TaskStatus(status)
        with self._lock:
            case = self.get_case(case_id)
            for task in case.tasks:
                if task.id == task_id:
                    task.status = validated_status
                    self._store.save(case)
                    return case
        raise TaskNotFoundError(task_id)
