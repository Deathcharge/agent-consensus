"""Tests for the installed/imported public package shape."""

import agent_consensus
from agent_consensus import ConsensusEngine, ConsensusResult
from agent_consensus.multi_ai_consensus import (
    ConsensusResponse,
    MultiAIConsensus,
)


def test_public_package_exports_version_and_core_types() -> None:
    assert agent_consensus.__version__ == "0.2.0"
    assert "ConsensusEngine" in agent_consensus.__all__
    assert "ParticipantResponse" in agent_consensus.__all__


def test_legacy_module_path_points_to_standalone_types() -> None:
    assert MultiAIConsensus is ConsensusEngine
    assert ConsensusResponse is ConsensusResult
