from types import SimpleNamespace

import pytest

from src.ai.client import (
    API_KEY_ENV,
    DEFAULT_MODEL,
    MODEL_ENV,
    WORKSPACE_ID_ENV,
    WORKSPACE_ID_HEADER,
    AnthropicClient,
)
from src.ai.errors import LLMConfigurationError, LLMProviderError

anthropic = pytest.importorskip("anthropic")
httpx2 = pytest.importorskip("httpx2")

FAKE_KEY = "test-key-not-real"
FAKE_WORKSPACE_ID = "workspace-test-not-real"


class FakeMessages:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def make_client(
    monkeypatch, result, workspace_id: str | None = None
) -> tuple[AnthropicClient, FakeMessages]:
    monkeypatch.setenv(API_KEY_ENV, FAKE_KEY)
    if workspace_id is None:
        monkeypatch.delenv(WORKSPACE_ID_ENV, raising=False)
    else:
        monkeypatch.setenv(WORKSPACE_ID_ENV, workspace_id)
    client = AnthropicClient()
    messages = FakeMessages(result)
    client._client = SimpleNamespace(messages=messages)
    return client, messages


def response(stop_reason="end_turn", text='{"ok": true}'):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)],
    )


REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def test_missing_api_key_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    with pytest.raises(LLMConfigurationError, match=API_KEY_ENV):
        AnthropicClient()


def test_model_comes_from_environment_or_default(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV, FAKE_KEY)
    monkeypatch.delenv(WORKSPACE_ID_ENV, raising=False)
    monkeypatch.delenv(MODEL_ENV, raising=False)
    assert AnthropicClient().model == DEFAULT_MODEL
    monkeypatch.setenv(MODEL_ENV, "claude-sonnet-5-5")
    assert AnthropicClient().model == "claude-sonnet-5-5"


def test_client_omits_workspace_header_when_workspace_id_is_not_set(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV, FAKE_KEY)
    monkeypatch.delenv(WORKSPACE_ID_ENV, raising=False)
    constructor_options = {}

    def fake_anthropic(**kwargs):
        constructor_options.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(anthropic, "Anthropic", fake_anthropic)

    AnthropicClient()

    assert "default_headers" not in constructor_options


def test_client_configures_workspace_header_when_workspace_id_is_set(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV, FAKE_KEY)
    monkeypatch.setenv(WORKSPACE_ID_ENV, FAKE_WORKSPACE_ID)
    constructor_options = {}

    def fake_anthropic(**kwargs):
        constructor_options.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(anthropic, "Anthropic", fake_anthropic)

    AnthropicClient()

    assert constructor_options["default_headers"] == {
        WORKSPACE_ID_HEADER: FAKE_WORKSPACE_ID,
    }


def test_returns_only_text_blocks_and_sends_the_prompt(monkeypatch):
    client, messages = make_client(monkeypatch, response())
    assert client.complete("PROMPT") == '{"ok": true}'
    assert messages.calls[0]["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert messages.calls[0]["model"] == client.model


@pytest.mark.parametrize(
    ("error", "expected", "match"),
    [
        (anthropic.APITimeoutError(request=REQUEST), LLMProviderError, "timed out"),
        (anthropic.APIConnectionError(request=REQUEST), LLMProviderError, "reach"),
        (
            anthropic.InternalServerError("boom", response=httpx2.Response(500, request=REQUEST), body=None),
            LLMProviderError,
            "HTTP 500",
        ),
        (
            anthropic.AuthenticationError("bad key", response=httpx2.Response(401, request=REQUEST), body=None),
            LLMConfigurationError,
            "rejected",
        ),
    ],
    ids=["timeout", "connection", "server_error", "bad_key"],
)
def test_sdk_errors_become_clear_intake_errors(monkeypatch, error, expected, match):
    client, _ = make_client(monkeypatch, error, workspace_id=FAKE_WORKSPACE_ID)
    with pytest.raises(expected, match=match) as excinfo:
        client.complete("PROMPT")
    assert FAKE_KEY not in str(excinfo.value)
    assert FAKE_WORKSPACE_ID not in str(excinfo.value)


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_incomplete_responses_are_provider_errors(monkeypatch, stop_reason):
    client, _ = make_client(monkeypatch, response(stop_reason=stop_reason))
    with pytest.raises(LLMProviderError):
        client.complete("PROMPT")
