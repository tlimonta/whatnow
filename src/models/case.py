"""Shared case and task state for backend integrations."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from uuid import uuid4

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, JsonValue


def require_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("Must contain non-whitespace characters")
    return value


NonBlankString = Annotated[str, Field(min_length=1), AfterValidator(require_non_blank)]


class CaseType(str, Enum):
    STOLEN_PHONE = "stolen_phone"
    LOST_PHONE = "lost_phone"
    UNCERTAIN_PHONE_LOSS = "uncertain_phone_loss"
    UNSUPPORTED = "unsupported"


class CaseStatus(str, Enum):
    INTAKE = "intake"
    ACTIVE = "active"
    RESOLVED = "resolved"


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: NonBlankString = Field(default_factory=lambda: str(uuid4()))
    title: NonBlankString
    status: TaskStatus = TaskStatus.PENDING
    description: NonBlankString | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    priority: NonBlankString | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    workflow_id: NonBlankString | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    source_id: NonBlankString | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: NonBlankString = Field(default_factory=lambda: str(uuid4()))
    case_type: CaseType | None = None
    status: CaseStatus = CaseStatus.INTAKE
    risk_level: RiskLevel | None = None
    initial_message: NonBlankString
    facts: dict[str, JsonValue] = Field(default_factory=dict)
    missing_fields: list[NonBlankString] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
