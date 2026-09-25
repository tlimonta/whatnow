"""Process-local storage; callers receive copies, never live stored objects."""

from src.models.case import Case


class InMemoryCaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, Case] = {}

    def save(self, case: Case) -> None:
        self._cases[case.id] = case.model_copy(deep=True)

    def get(self, case_id: str) -> Case | None:
        case = self._cases.get(case_id)
        return case.model_copy(deep=True) if case is not None else None
