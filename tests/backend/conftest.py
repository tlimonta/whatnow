from collections.abc import Iterator
import json

import pytest
from fastapi.testclient import TestClient

from src.ai.parser import IntakeParser
from src.ai.schema import FACT_FIELDS
from src.backend.main import create_app, get_case_service
from src.backend.service import CaseService
from src.backend.storage import InMemoryCaseStore


@pytest.fixture
def store() -> InMemoryCaseStore:
    return InMemoryCaseStore()


@pytest.fixture
def service(store: InMemoryCaseStore) -> CaseService:
    return CaseService(store)


class FakeClient:
    model = "test-model"

    def __init__(self) -> None:
        self.response: str | Exception = json.dumps(
            {
                "case_type": "unsupported",
                "confidence": 0.9,
                "facts": {field: None for field in FACT_FIELDS},
                "missing_fields": [],
                "evidence": [],
            }
        )
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def client(service: CaseService, fake_client: FakeClient) -> Iterator[TestClient]:
    app = create_app(intake_parser_factory=lambda: IntakeParser(fake_client))
    app.dependency_overrides[get_case_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
