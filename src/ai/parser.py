"""Turn a user message into validated intake data. No workflow or procedure logic here."""

import json
import re

from pydantic import ValidationError

from src.ai.client import LLMClient
from src.ai.errors import IntakeOutputError
from src.ai.prompts import (
    DEFAULT_PROMPT_VERSION,
    load_prompt_template,
    neutralize_delimiters,
    render_prompt,
)
from src.ai.schema import FACT_FIELDS, IntakeFacts, IntakeResult, ParsedIntake
from src.models.case import CaseType

_CODE_FENCE = re.compile(r"^```(?:json)?\s*\n(.*)\n```$", re.DOTALL)


class IntakeParser:
    def __init__(self, client: LLMClient, prompt_version: str = DEFAULT_PROMPT_VERSION) -> None:
        self._client = client
        self._prompt_version = prompt_version
        self._template = load_prompt_template(prompt_version)

    def parse(self, user_message: str) -> ParsedIntake:
        """Raise LLMProviderError / IntakeOutputError on failure; never guess a result."""
        sent_message = neutralize_delimiters(user_message)
        raw_output = self._client.complete(render_prompt(self._template, sent_message))

        warnings: list[str] = []
        if sent_message != user_message:
            warnings.append("neutralized <user_message> tags found in the user text")
        result = _validate(raw_output, warnings)
        result = _enforce_rules(result, sent_message, warnings)
        return ParsedIntake(
            result=result,
            prompt_version=self._prompt_version,
            model=self._client.model,
            warnings=warnings,
            raw_output=raw_output,
        )


def _validate(raw_output: str, warnings: list[str]) -> IntakeResult:
    text = raw_output.strip()
    fenced = _CODE_FENCE.match(text)
    if fenced:
        text = fenced.group(1)
        warnings.append("removed a Markdown code fence around the JSON")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IntakeOutputError(f"Model output is not valid JSON: {exc.msg}", raw_output) from exc
    try:
        return IntakeResult.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(map(str, err['loc'])) or 'output'}: {err['msg']}" for err in exc.errors()
        )
        raise IntakeOutputError(f"Model output does not match the intake schema: {problems}", raw_output) from exc


def _enforce_rules(result: IntakeResult, sent_message: str, warnings: list[str]) -> IntakeResult:
    """Apply the prompt's rules deterministically instead of trusting the model to follow them."""
    facts = result.facts.model_dump()

    if result.case_type == CaseType.UNSUPPORTED:
        if any(value is not None for value in facts.values()) or result.evidence:
            warnings.append("unsupported case: cleared facts and evidence")
        return result.model_copy(
            update={"facts": IntakeFacts(), "missing_fields": [], "evidence": []}
        )

    # Evidence must be an exact quote of what the model was given, for a non-null fact.
    evidence = []
    seen = set()
    for item in result.evidence:
        if facts[item.field] is None:
            warnings.append(f"dropped evidence for null fact {item.field}")
        elif item.user_text not in sent_message:
            warnings.append(f"dropped evidence for {item.field}: text not found in the user message")
        elif item.field in seen:
            warnings.append(f"dropped duplicate evidence for {item.field}")
        else:
            evidence.append(item)
            seen.add(item.field)

    # A fact without a supporting quote is an unsupported inference: make it unknown.
    for field in FACT_FIELDS:
        if facts[field] is not None and field not in seen:
            warnings.append(f"set {field} to null: no supporting evidence")
            facts[field] = None

    missing_fields = [field for field in FACT_FIELDS if facts[field] is None]
    if missing_fields != result.missing_fields:
        warnings.append("recomputed missing_fields from the facts")

    return result.model_copy(
        update={
            "facts": IntakeFacts(**facts),
            "missing_fields": missing_fields,
            "evidence": evidence,
        }
    )
