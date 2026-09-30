"""Deterministic evaluation of the verified stolen-phone workflow."""

import json
from collections.abc import Callable
from datetime import date
from enum import Enum
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Self

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from src.models.case import Case, CaseType, NonBlankString, Task, TaskStatus


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKFLOW_PATH = (
    REPOSITORY_ROOT / "data" / "workflows" / "stolen_phone_es.json"
)
DEFAULT_SOURCES_PATH = REPOSITORY_ROOT / "data" / "sources" / "stolen_phone_es.json"


class WorkflowDataError(ValueError):
    """The verified workflow or source data is malformed or unsupported."""


class WorkflowEvaluationError(ValueError):
    """Structured case facts cannot be evaluated safely."""


class ConditionResult(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class WorkflowStepData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonBlankString
    title: NonBlankString
    description: NonBlankString
    priority: NonBlankString
    condition: NonBlankString | None
    source_id: NonBlankString


class WorkflowData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: NonBlankString
    locale: NonBlankString
    title: NonBlankString
    description: NonBlankString
    steps: list[WorkflowStepData] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_step_ids(self) -> Self:
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Workflow step IDs must be unique")
        return self


class SourceData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonBlankString
    name: NonBlankString
    url: AnyHttpUrl
    description: NonBlankString
    type: NonBlankString
    last_verified: date


class SourceCatalogData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: NonBlankString
    sources: list[SourceData] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_source_ids(self) -> Self:
        source_ids = [source.id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Source IDs must be unique")
        return self


ConditionEvaluator = Callable[[Case], ConditionResult]


def _not_represented_in_current_facts(_case: Case) -> ConditionResult:
    """Keep unsupported condition inputs unknown rather than guessing."""

    return ConditionResult.UNKNOWN


def _banking_access_condition(case: Case) -> ConditionResult:
    value = case.facts.get("banking_apps_present")
    if value is None:
        return ConditionResult.UNKNOWN
    if not isinstance(value, bool):
        raise WorkflowEvaluationError(
            "Fact 'banking_apps_present' must be true, false, or null"
        )
    return ConditionResult.TRUE if value else ConditionResult.FALSE


# The data currently stores conditions as prose. Pairing the exact text with an
# evaluator makes that limitation explicit: changed or new rules fail at load
# time until deterministic handling is deliberately added.
_CONDITION_RULES: dict[str, tuple[str, ConditionEvaluator]] = {
    "stolen_phone_es_02_movistar": (
        "The stolen SIM/line is provided by Movistar.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_03_vodafone": (
        "The stolen SIM/line is provided by Vodafone.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_04_orange": (
        "The stolen SIM/line is provided by Orange.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_05_yoigo": (
        "The stolen SIM/line is provided by Yoigo.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_06_apple": (
        "The stolen device is an iPhone or iPad and Buscar was enabled before the theft.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_07_android": (
        "The stolen device is Android and the documented Localizador prerequisites are satisfied.",
        _not_represented_in_current_facts,
    ),
    "stolen_phone_es_08_bank": (
        "Banking apps or payment instruments were installed on or accessible from the stolen device.",
        _banking_access_condition,
    ),
    "stolen_phone_es_09_manufacturer": (
        "The device has manufacturer support, a theft-and-loss plan, or another coverage issue that requires manufacturer action; the exact route depends on the device and plan.",
        _not_represented_in_current_facts,
    ),
}


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except OSError as exc:
        raise WorkflowDataError(
            f"Could not read workflow data file {path}: {exc}"
        ) from exc
    except JSONDecodeError as exc:
        raise WorkflowDataError(
            f"Invalid JSON in workflow data file {path}: {exc}"
        ) from exc


class WorkflowEngine:
    """Load, validate, evaluate, and idempotently apply one verified workflow."""

    def __init__(self, workflow: WorkflowData, sources: SourceCatalogData) -> None:
        self._workflow = workflow
        self._sources = {source.id: source for source in sources.sources}

    @classmethod
    def from_files(
        cls,
        workflow_path: str | Path = DEFAULT_WORKFLOW_PATH,
        sources_path: str | Path = DEFAULT_SOURCES_PATH,
    ) -> Self:
        workflow_file = Path(workflow_path)
        sources_file = Path(sources_path)
        try:
            workflow = WorkflowData.model_validate(_read_json(workflow_file))
        except ValidationError as exc:
            raise WorkflowDataError(
                f"Invalid workflow structure in {workflow_file}: {exc}"
            ) from exc
        try:
            sources = SourceCatalogData.model_validate(_read_json(sources_file))
        except ValidationError as exc:
            raise WorkflowDataError(
                f"Invalid source structure in {sources_file}: {exc}"
            ) from exc

        cls._validate_contract(workflow, sources)
        return cls(workflow, sources)

    @staticmethod
    def _validate_contract(workflow: WorkflowData, sources: SourceCatalogData) -> None:
        if workflow.workflow_id != sources.workflow_id:
            raise WorkflowDataError(
                "Workflow and source catalog workflow_id values do not match"
            )

        source_ids = {source.id for source in sources.sources}
        missing_sources = sorted(
            {step.source_id for step in workflow.steps} - source_ids
        )
        if missing_sources:
            raise WorkflowDataError(
                "Workflow references unknown source IDs: " + ", ".join(missing_sources)
            )

        for step in workflow.steps:
            if step.condition is None:
                continue
            rule = _CONDITION_RULES.get(step.id)
            if rule is None:
                raise WorkflowDataError(
                    f"Conditional workflow step {step.id!r} has no deterministic evaluator"
                )
            expected_condition, _ = rule
            if step.condition != expected_condition:
                raise WorkflowDataError(
                    f"Condition for workflow step {step.id!r} changed and is not supported"
                )

    @property
    def workflow_id(self) -> str:
        return self._workflow.workflow_id

    @property
    def step_ids(self) -> frozenset[str]:
        return frozenset(step.id for step in self._workflow.steps)

    @property
    def source_ids(self) -> frozenset[str]:
        return frozenset(self._sources)

    def evaluate(self, case: Case) -> list[Task]:
        """Return tasks whose workflow conditions are definitively true."""

        if case.case_type != CaseType.STOLEN_PHONE:
            return []

        tasks: list[Task] = []
        for step in self._workflow.steps:
            result = self._evaluate_step(step, case)
            if result != ConditionResult.TRUE:
                continue
            tasks.append(
                Task(
                    id=step.id,
                    title=step.title,
                    description=step.description,
                    priority=step.priority,
                    workflow_id=self._workflow.workflow_id,
                    source_id=step.source_id,
                )
            )
        return tasks

    def apply_to_case(self, case: Case) -> Case:
        """Reconcile active tasks without losing completed or skipped history."""

        updated = case.model_copy(deep=True)
        seen_task_ids: set[str] = set()
        for task in updated.tasks:
            if task.id in seen_task_ids:
                raise WorkflowEvaluationError(
                    f"Case contains duplicate task ID {task.id!r}"
                )
            seen_task_ids.add(task.id)

        generated_tasks = self.evaluate(case)
        active_task_ids = {task.id for task in generated_tasks}
        updated.tasks = [
            task
            for task in updated.tasks
            if not (
                task.workflow_id == self._workflow.workflow_id
                and task.id not in active_task_ids
                and task.status == TaskStatus.PENDING
            )
        ]
        task_positions = {task.id: index for index, task in enumerate(updated.tasks)}

        for generated in generated_tasks:
            position = task_positions.get(generated.id)
            if position is None:
                task_positions[generated.id] = len(updated.tasks)
                updated.tasks.append(generated)
                continue

            existing = updated.tasks[position]
            if existing.workflow_id != generated.workflow_id:
                raise WorkflowEvaluationError(
                    f"Task ID {generated.id!r} conflicts with an existing non-workflow task"
                )
            generated.status = existing.status
            updated.tasks[position] = generated

        return updated

    @staticmethod
    def _evaluate_step(step: WorkflowStepData, case: Case) -> ConditionResult:
        if step.condition is None:
            return ConditionResult.TRUE
        _, evaluator = _CONDITION_RULES[step.id]
        return evaluator(case)
