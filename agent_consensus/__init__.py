"""Deterministic consensus evaluation for Python agents and services."""

from .core import ConsensusEngine, evaluate_votes, normalize_choice
from .errors import (
    ConfigurationError,
    ConsensusError,
    DuplicateParticipantError,
    ResponseValidationError,
)
from .models import (
    ChoiceTally,
    ConsensusConfig,
    ConsensusResult,
    ConsensusStatus,
    Participant,
    ParticipantOutcome,
    ParticipantResponse,
    Responder,
    ResponseStatus,
    Vote,
)
from .policy import (
    DecisionPolicy,
    DecisionReason,
    DecisionStatus,
    DecisionVerdict,
    evaluate_decision,
)

__version__ = "0.2.0"

__all__ = [
    "ChoiceTally",
    "ConfigurationError",
    "ConsensusConfig",
    "ConsensusEngine",
    "ConsensusError",
    "ConsensusResult",
    "ConsensusStatus",
    "DecisionPolicy",
    "DecisionReason",
    "DecisionStatus",
    "DecisionVerdict",
    "DuplicateParticipantError",
    "Participant",
    "ParticipantOutcome",
    "ParticipantResponse",
    "Responder",
    "ResponseStatus",
    "ResponseValidationError",
    "Vote",
    "evaluate_decision",
    "evaluate_votes",
    "normalize_choice",
]
