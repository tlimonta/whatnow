"""Errors raised by the AI intake layer. Messages never contain credentials."""


class IntakeError(Exception):
    """Base class: the backend can catch this one type for any intake failure."""


class LLMConfigurationError(IntakeError):
    """Required local configuration (e.g. the API key variable) is missing."""


class LLMProviderError(IntakeError):
    """The provider call failed: timeout, network, API error or refusal."""


class IntakeOutputError(IntakeError):
    """The model answered, but not with valid structured intake data."""

    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output
