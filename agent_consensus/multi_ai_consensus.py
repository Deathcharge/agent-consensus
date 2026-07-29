"""Compatibility import path for the standalone consensus engine.

The extracted 0.1 source module imported a private ``helix-unified`` service and
was not included in the built wheel. Provider-specific clients are intentionally
not reproduced here. Inject provider adapters through :class:`Participant`.
"""

from .core import ConsensusEngine, evaluate_votes, normalize_choice
from .models import (
    ConsensusConfig,
    ConsensusResult,
    ConsensusStatus,
    Participant,
    ParticipantResponse,
    Vote,
)

MultiAIConsensus = ConsensusEngine
ConsensusResponse = ConsensusResult

__all__ = [
    "ConsensusConfig",
    "ConsensusEngine",
    "ConsensusResponse",
    "ConsensusResult",
    "ConsensusStatus",
    "MultiAIConsensus",
    "Participant",
    "ParticipantResponse",
    "Vote",
    "evaluate_votes",
    "normalize_choice",
]
