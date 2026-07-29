"""Typed public data models for deterministic consensus evaluation."""

from __future__ import annotations

import math
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Protocol

from .errors import ConfigurationError, ResponseValidationError

MAX_NAME_CHARACTERS = 128
MAX_CHOICE_CHARACTERS = 256


class ConsensusStatus(str, Enum):
    """Final state of a consensus evaluation."""

    AGREED = "agreed"
    NO_CONSENSUS = "no_consensus"
    QUORUM_FAILED = "quorum_failed"


class ResponseStatus(str, Enum):
    """Execution state for one participant."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ParticipantResponse:
    """A participant's explicit vote and optional supporting content.

    ``choice`` is the only field used to calculate consensus. The library does
    not pretend to infer semantic agreement from ``content``.
    """

    choice: str
    content: str = ""
    confidence: float | None = None
    tokens_used: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.choice, str) or not self.choice.strip():
            raise ResponseValidationError("choice must be a non-empty string")
        if len(self.choice) > MAX_CHOICE_CHARACTERS:
            raise ResponseValidationError(
                f"choice cannot exceed {MAX_CHOICE_CHARACTERS} characters"
            )
        if not isinstance(self.content, str):
            raise ResponseValidationError("content must be a string")
        if self.confidence is not None and (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not math.isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ResponseValidationError("confidence must be between 0 and 1")
        if self.tokens_used is not None and (
            isinstance(self.tokens_used, bool)
            or not isinstance(self.tokens_used, int)
            or self.tokens_used < 0
        ):
            raise ResponseValidationError("tokens_used must be a non-negative integer")
        if not isinstance(self.metadata, Mapping):
            raise ResponseValidationError("metadata must be a mapping")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible shape when metadata values are compatible."""
        return {
            "choice": self.choice,
            "content": self.content,
            "confidence": self.confidence,
            "tokens_used": self.tokens_used,
            "metadata": dict(self.metadata),
        }


class Responder(Protocol):
    """Callable contract implemented by an agent or provider adapter."""

    def __call__(self, prompt: str, *, max_tokens: int) -> Awaitable[ParticipantResponse]:
        """Return an awaitable participant response."""
        ...


@dataclass(frozen=True)
class Participant:
    """A named and optionally weighted consensus participant."""

    name: str
    responder: Responder
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ConfigurationError("participant name must be a non-empty string")
        normalized_name = self.name.strip()
        if len(normalized_name) > MAX_NAME_CHARACTERS:
            raise ConfigurationError(
                f"participant name cannot exceed {MAX_NAME_CHARACTERS} characters"
            )
        if not callable(self.responder):
            raise ConfigurationError("participant responder must be callable")
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, (int, float))
            or not math.isfinite(self.weight)
            or self.weight <= 0
        ):
            raise ConfigurationError("participant weight must be finite and positive")
        object.__setattr__(self, "name", normalized_name)


@dataclass(frozen=True)
class Vote:
    """A pre-collected vote for synchronous evaluation."""

    participant: str
    choice: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.participant, str) or not self.participant.strip():
            raise ResponseValidationError("vote participant must be a non-empty string")
        normalized_participant = self.participant.strip()
        if len(normalized_participant) > MAX_NAME_CHARACTERS:
            raise ResponseValidationError(
                f"vote participant cannot exceed {MAX_NAME_CHARACTERS} characters"
            )
        ParticipantResponse(choice=self.choice)
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, (int, float))
            or not math.isfinite(self.weight)
            or self.weight <= 0
        ):
            raise ResponseValidationError("vote weight must be finite and positive")
        object.__setattr__(self, "participant", normalized_participant)


@dataclass(frozen=True)
class ConsensusConfig:
    """Safety and decision settings for :class:`ConsensusEngine`."""

    threshold: float = 2 / 3
    min_successful: int = 2
    timeout_seconds: float = 30.0
    max_concurrency: int = 4
    max_participants: int = 32
    max_prompt_characters: int = 100_000
    max_response_characters: int = 100_000
    max_output_tokens_per_participant: int = 1_000
    max_total_output_tokens: int = 4_000

    def __post_init__(self) -> None:
        if (
            isinstance(self.threshold, bool)
            or not isinstance(self.threshold, (int, float))
            or not math.isfinite(self.threshold)
            or not 0 < self.threshold <= 1
        ):
            raise ConfigurationError("threshold must be greater than 0 and at most 1")
        if isinstance(self.min_successful, bool) or not isinstance(self.min_successful, int):
            raise ConfigurationError("min_successful must be an integer")
        if self.min_successful < 1:
            raise ConfigurationError("min_successful must be at least 1")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ConfigurationError("timeout_seconds must be finite and positive")
        for field_name in (
            "max_concurrency",
            "max_participants",
            "max_prompt_characters",
            "max_response_characters",
            "max_output_tokens_per_participant",
            "max_total_output_tokens",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfigurationError(f"{field_name} must be an integer")
            if value < 1:
                raise ConfigurationError(f"{field_name} must be at least 1")


@dataclass(frozen=True)
class ParticipantOutcome:
    """Sanitized result of querying one participant."""

    participant: str
    status: ResponseStatus
    weight: float
    duration_ms: float
    requested_max_tokens: int
    response: ParticipantResponse | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the outcome as a serializable dictionary."""
        return {
            "participant": self.participant,
            "status": self.status.value,
            "weight": self.weight,
            "duration_ms": round(self.duration_ms, 3),
            "requested_max_tokens": self.requested_max_tokens,
            "response": self.response.to_dict() if self.response else None,
            "error_type": self.error_type,
        }


@dataclass(frozen=True)
class ChoiceTally:
    """Weighted support accumulated for one normalized choice."""

    choice: str
    normalized_choice: str
    weight: float
    vote_count: int
    participants: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the tally as a serializable dictionary."""
        return {
            "choice": self.choice,
            "normalized_choice": self.normalized_choice,
            "weight": self.weight,
            "vote_count": self.vote_count,
            "participants": list(self.participants),
        }


@dataclass(frozen=True)
class ConsensusResult:
    """Auditable result for either collected or asynchronously gathered votes."""

    status: ConsensusStatus
    choice: str | None
    agreement: float
    quorum_reached: bool
    successful_count: int
    total_count: int
    successful_weight: float
    total_weight: float
    threshold: float
    min_successful: int
    reported_tokens_used: int
    token_usage_complete: bool
    duration_ms: float
    tallies: tuple[ChoiceTally, ...]
    outcomes: tuple[ParticipantOutcome, ...]

    @property
    def agreed(self) -> bool:
        """Whether the configured threshold and quorum were both satisfied."""
        return self.status is ConsensusStatus.AGREED

    def to_dict(self) -> dict[str, Any]:
        """Return the complete audit result as a serializable dictionary."""
        return {
            "status": self.status.value,
            "choice": self.choice,
            "agreement": round(self.agreement, 6),
            "quorum_reached": self.quorum_reached,
            "successful_count": self.successful_count,
            "total_count": self.total_count,
            "successful_weight": self.successful_weight,
            "total_weight": self.total_weight,
            "threshold": self.threshold,
            "min_successful": self.min_successful,
            "reported_tokens_used": self.reported_tokens_used,
            "token_usage_complete": self.token_usage_complete,
            "duration_ms": round(self.duration_ms, 3),
            "tallies": [tally.to_dict() for tally in self.tallies],
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
        }


ChoiceNormalizer = Callable[[str], str]
