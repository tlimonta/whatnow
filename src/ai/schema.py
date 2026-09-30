"""Structured intake output: the contract defined in prompts/v3_uncertainty_prompt.md."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.models.case import CaseType, NonBlankString

# Schema order; missing_fields is listed in this order.
FACT_FIELDS: tuple[str, ...] = (
    "location",
    "incident_time",
    "device_type",
    "theft_confirmed",
    "banking_apps_present",
    "device_locked",
    "sim_blocked",
)

FactField = Literal[
    "location",
    "incident_time",
    "device_type",
    "theft_confirmed",
    "banking_apps_present",
    "device_locked",
    "sim_blocked",
]


class IntakeFacts(BaseModel):
    # strict: "true" or 1 is not a boolean, and a number is not a location.
    model_config = ConfigDict(extra="forbid", strict=True)

    location: NonBlankString | None = None
    incident_time: NonBlankString | None = None
    device_type: NonBlankString | None = None
    theft_confirmed: bool | None = None
    banking_apps_present: bool | None = None
    device_locked: bool | None = None
    sim_blocked: bool | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    field: FactField
    user_text: NonBlankString


class IntakeResult(BaseModel):
    """What the parser returns to the backend.

    Extra keys are rejected, so a model that adds tasks, procedures or advice
    produces an invalid output instead of untrusted workflow data.
    """

    model_config = ConfigDict(extra="forbid")

    case_type: CaseType
    confidence: float = Field(ge=0.0, le=1.0)
    facts: IntakeFacts
    missing_fields: list[FactField]
    evidence: list[Evidence]


class ParsedIntake(BaseModel):
    """Validated result plus audit data; only `result` is meant for the Case."""

    model_config = ConfigDict(extra="forbid")

    result: IntakeResult
    prompt_version: str
    model: str
    # Changes the parser made to the model's output, for logging and benchmarking.
    warnings: list[str] = Field(default_factory=list)
    raw_output: str
