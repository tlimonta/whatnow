"""HTTP request bodies, separate from persisted case state."""

from pydantic import BaseModel, ConfigDict

from src.models.case import NonBlankString, TaskStatus


class CreateCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: NonBlankString


class UpdateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus
