from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.backend.main import create_app, get_case_service
from src.backend.service import CaseService
from src.backend.storage import InMemoryCaseStore


@pytest.fixture
def store() -> InMemoryCaseStore:
    return InMemoryCaseStore()


@pytest.fixture
def service(store: InMemoryCaseStore) -> CaseService:
    return CaseService(store)


@pytest.fixture
def client(service: CaseService) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_case_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
