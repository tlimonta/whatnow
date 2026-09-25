"""Run from the repository root: python -m uvicorn src.backend.main:app."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.backend.schemas import CreateCaseRequest, UpdateTaskRequest
from src.backend.service import CaseNotFoundError, CaseService, TaskNotFoundError
from src.backend.storage import InMemoryCaseStore
from src.models.case import Case


def get_case_service(request: Request) -> CaseService:
    return request.app.state.case_service


ServiceDependency = Annotated[CaseService, Depends(get_case_service)]


def create_app() -> FastAPI:
    app = FastAPI(title="WhatNow", version="0.1.0")
    app.state.case_service = CaseService(InMemoryCaseStore())

    @app.exception_handler(CaseNotFoundError)
    async def case_not_found(request: Request, exc: CaseNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Case not found"})

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found(request: Request, exc: TaskNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Task not found"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/cases", response_model=Case, status_code=status.HTTP_201_CREATED)
    def create_case(body: CreateCaseRequest, service: ServiceDependency) -> Case:
        return service.create_case(body.message)

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
