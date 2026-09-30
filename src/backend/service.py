"""Application logic independent of HTTP and future AI providers."""

from collections.abc import Callable
from threading import RLock

from src.ai.schema import IntakeResult
from src.backend.storage import InMemoryCaseStore
from src.backend.workflow_engine import WorkflowEngine
from src.models.case import Case, CaseType, TaskStatus


class CaseNotFoundError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class CaseService:
    def __init__(
        self,
        store: InMemoryCaseStore,
        workflow_factory: Callable[[], WorkflowEngine] = WorkflowEngine.from_files,
    ) -> None:
        self._store = store
        self._workflow_factory = workflow_factory
        # One service per app serializes read-modify-write operations across requests.
        self._lock = RLock()

    def create_case(self, message: str) -> Case:
        """Keep the neutral Phase 1 creation method for non-intake callers."""
        case = Case(initial_message=message)
        with self._lock:
            self._store.save(case)
        return case

    def create_case_from_intake(self, message: str, intake: IntakeResult) -> Case:
        """Persist a case only after verified intake and workflow evaluation."""
        case = Case(
            initial_message=message,
            case_type=intake.case_type,
            facts=intake.facts.model_dump(mode="json"),
            missing_fields=list(intake.missing_fields),
        )
        if case.case_type == CaseType.STOLEN_PHONE:
            case = self._workflow_factory().apply_to_case(case)
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
