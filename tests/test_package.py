"""Tests for the installed/imported public package shape."""

import agent_consensus
from agent_consensus import (
    ConsensusEngine,
    ConsensusError,
    ConsensusResult,
    DecisionInputError,
    DecisionPolicy,
    DecisionVerdict,
)
from agent_consensus.multi_ai_consensus import (
    ConsensusResponse,
    MultiAIConsensus,
)


def test_public_package_exports_version_and_core_types() -> None:
    assert agent_consensus.__version__ == "0.2.0"
    assert "ConsensusEngine" in agent_consensus.__all__
    assert "DecisionPolicy" in agent_consensus.__all__
    assert "DecisionInputError" in agent_consensus.__all__
    assert "evaluate_decision" in agent_consensus.__all__
    assert issubclass(DecisionInputError, ConsensusError)
    assert issubclass(DecisionInputError, TypeError)
    assert "ParticipantResponse" in agent_consensus.__all__
    assert DecisionPolicy.__module__ == "agent_consensus.policy"
    assert DecisionVerdict.__module__ == "agent_consensus.policy"


def test_legacy_module_path_points_to_standalone_types() -> None:
    assert MultiAIConsensus is ConsensusEngine
    assert ConsensusResponse is ConsensusResult
