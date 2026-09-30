"""Run from the repository root: python -m uvicorn src.backend.main:app."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.ai.client import AnthropicClient
from src.ai.errors import IntakeOutputError, LLMConfigurationError, LLMProviderError
from src.ai.parser import IntakeParser
from src.backend.schemas import CreateCaseRequest, UpdateTaskRequest
from src.backend.service import CaseNotFoundError, CaseService, TaskNotFoundError
from src.backend.storage import InMemoryCaseStore
from src.backend.workflow_engine import WorkflowDataError, WorkflowEvaluationError
from src.models.case import Case


def get_case_service(request: Request) -> CaseService:
    return request.app.state.case_service


ServiceDependency = Annotated[CaseService, Depends(get_case_service)]


def create_intake_parser() -> IntakeParser:
    """Construct the provider only for a valid POST request."""
    try:
        return IntakeParser(AnthropicClient())
    except ModuleNotFoundError as exc:
        provider_module = exc.name == "anthropic" or (exc.name or "").startswith(
            "anthropic."
        )
        if not provider_module:
            raise
        raise LLMConfigurationError("Anthropic SDK is unavailable") from exc


def create_app(
    intake_parser_factory: Callable[[], IntakeParser] = create_intake_parser,
) -> FastAPI:
    app = FastAPI(title="WhatNow", version="0.1.0")
    app.state.case_service = CaseService(InMemoryCaseStore())

    @app.exception_handler(CaseNotFoundError)
    async def case_not_found(request: Request, exc: CaseNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Case not found"})

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found(request: Request, exc: TaskNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Task not found"})

    @app.exception_handler(LLMConfigurationError)
    async def intake_configuration_error(
        request: Request, exc: LLMConfigurationError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "AI intake is not configured"})

    @app.exception_handler(LLMProviderError)
    async def intake_provider_error(
        request: Request, exc: LLMProviderError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "AI provider request failed"})

    @app.exception_handler(IntakeOutputError)
    async def intake_output_error(
        request: Request, exc: IntakeOutputError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "AI intake response was invalid"})

    @app.exception_handler(WorkflowDataError)
    @app.exception_handler(WorkflowEvaluationError)
    async def workflow_error(
        request: Request, exc: WorkflowDataError | WorkflowEvaluationError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Verified workflow unavailable"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/cases", response_model=Case, status_code=status.HTTP_201_CREATED)
    def create_case(body: CreateCaseRequest, service: ServiceDependency) -> Case:
        intake = intake_parser_factory().parse(body.message)
        return service.create_case_from_intake(body.message, intake.result)

    @app.get("/api/cases/{case_id}", response_model=Case)
    def get_case(case_id: str, service: ServiceDependency) -> Case:
        return service.get_case(case_id)

    @app.patch("/api/cases/{case_id}/tasks/{task_id}", response_model=Case)
    def update_task(
        case_id: str, task_id: str, body: UpdateTaskRequest, service: ServiceDependency
    ) -> Case:
        return service.update_task_status(case_id, task_id, body.status)

    return app


app = create_app()
