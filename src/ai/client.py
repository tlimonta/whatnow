"""Provider clients. The parser only depends on the LLMClient protocol."""

import os
from typing import Protocol

from src.ai.errors import LLMConfigurationError, LLMProviderError

API_KEY_ENV = "ANTHROPIC_API_KEY"
WORKSPACE_ID_ENV = "ANTHROPIC_WORKSPACE_ID"
WORKSPACE_ID_HEADER = "anthropic-workspace-id"
MODEL_ENV = "WHATNOW_LLM_MODEL"
# Cheapest current Claude model; enough for single-message classification/extraction.
# If the Phase 3 benchmark shows it is too weak, try claude-sonnet-5-5 via WHATNOW_LLM_MODEL.
DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 2048


class LLMClient(Protocol):
    """Anything that turns one prompt into the model's raw text answer."""

    model: str

    def complete(self, prompt: str) -> str: ...


class AnthropicClient:
    """Calls the Claude Messages API. Credentials come only from the environment."""

    def __init__(self, model: str | None = None, timeout_seconds: float = 60.0) -> None:
        if not os.environ.get(API_KEY_ENV):
            raise LLMConfigurationError(
                f"{API_KEY_ENV} is not set. Put it in your local .env or shell, never in Git."
            )
        # Imported here so the rest of src.ai (and its tests) work without the SDK.
        import anthropic

        self._anthropic = anthropic
        self.model = model or os.environ.get(MODEL_ENV) or DEFAULT_MODEL
        client_options: dict[str, object] = {
            "timeout": timeout_seconds,
            "max_retries": 2,
        }
        workspace_id = os.environ.get(WORKSPACE_ID_ENV)
        if workspace_id:
            client_options["default_headers"] = {
                WORKSPACE_ID_HEADER: workspace_id,
            }

        self._client = anthropic.Anthropic(**client_options)

    def complete(self, prompt: str) -> str:
        anthropic = self._anthropic
        try:
            # No thinking or effort settings: Haiku 4.5 rejects `effort`, and the
            # output is one short JSON object. No temperature either: anthropic SDK 1.x
            # does not accept sampling parameters, so the provider default is used.
            response = self._client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APITimeoutError as exc:
            raise LLMProviderError("The AI provider timed out") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMProviderError("Could not reach the AI provider") from exc
        except anthropic.AuthenticationError as exc:
            raise LLMConfigurationError(f"The AI provider rejected {API_KEY_ENV}") from exc
        except anthropic.RateLimitError as exc:
            raise LLMProviderError("The AI provider rate limit was reached") from exc
        except anthropic.APIStatusError as exc:
            raise LLMProviderError(f"The AI provider returned HTTP {exc.status_code}") from exc

        if response.stop_reason == "refusal":
            raise LLMProviderError("The AI provider declined the request")
        if response.stop_reason == "max_tokens":
            raise LLMProviderError("The AI response was cut off before it finished")
        return "".join(block.text for block in response.content if block.type == "text")
