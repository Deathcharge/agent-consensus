"""
Comprehensive pytest configuration and fixtures for agent-consensus.

This module provides reusable fixtures for testing consensus mechanisms,
agent coordination, and multi-agent workflows.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import asyncio


# ============================================================================
# MOCK AGENTS AND AGENT STATES
# ============================================================================

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = Mock()
    agent.id = "agent_1"
    agent.name = "TestAgent"
    agent.state = "active"
    agent.vote = None
    return agent


@pytest.fixture
def mock_agents():
    """Create multiple mock agents for testing."""
    agents = []
    for i in range(5):
        agent = Mock()
        agent.id = f"agent_{i}"
        agent.name = f"Agent{i}"
        agent.state = "active"
        agent.vote = None
        agents.append(agent)
    return agents


@pytest.fixture
def mock_agent_state():
    """Create a mock agent state."""
    return {
        "id": "agent_1",
        "name": "TestAgent",
        "state": "active",
        "last_update": datetime.now().isoformat(),
        "metrics": {
            "consensus_reached": 0,
            "votes_cast": 0,
            "conflicts_resolved": 0
        }
    }


# ============================================================================
# MOCK PROPOSALS AND CONSENSUS DATA
# ============================================================================

@pytest.fixture
def mock_proposal():
    """Create a mock proposal for consensus."""
    return {
        "id": "proposal_1",
        "content": "Test proposal for consensus",
        "proposer": "agent_1",
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "votes": {}
    }


@pytest.fixture
def mock_proposals():
    """Create multiple mock proposals."""
    proposals = []
    for i in range(3):
        proposal = {
            "id": f"proposal_{i}",
            "content": f"Test proposal {i}",
            "proposer": f"agent_{i % 5}",
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "votes": {}
        }
        proposals.append(proposal)
    return proposals


@pytest.fixture
def mock_consensus_result():
    """Create a mock consensus result."""
    return {
        "proposal_id": "proposal_1",
        "status": "agreed",
        "agreement_level": 0.8,
        "votes_for": 4,
        "votes_against": 1,
        "abstentions": 0,
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def mock_votes():
    """Create mock votes for testing."""
    return {
        "agent_1": "for",
        "agent_2": "for",
        "agent_3": "against",
        "agent_4": "for",
        "agent_5": "abstain"
    }


# ============================================================================
# CONSENSUS SCENARIOS
# ============================================================================

@pytest.fixture
def simple_majority_scenario():
    """Create a simple majority consensus scenario."""
    return {
        "algorithm": "simple_majority",
        "agents": 5,
        "votes_for": 3,
        "votes_against": 2,
        "expected_result": "agreed"
    }


@pytest.fixture
def supermajority_scenario():
    """Create a supermajority consensus scenario."""
    return {
        "algorithm": "supermajority",
        "agents": 5,
        "votes_for": 4,
        "votes_against": 1,
        "expected_result": "agreed"
    }


@pytest.fixture
def unanimous_scenario():
    """Create a unanimous consensus scenario."""
    return {
        "algorithm": "unanimous",
        "agents": 5,
        "votes_for": 5,
        "votes_against": 0,
        "expected_result": "agreed"
    }


@pytest.fixture
def bft_scenario():
    """Create a Byzantine fault tolerant scenario."""
    return {
        "algorithm": "bft",
        "agents": 7,
        "faulty_agents": 2,
        "votes_for": 5,
        "votes_against": 0,
        "expected_result": "agreed"
    }


@pytest.fixture
def deadlock_scenario():
    """Create a deadlock consensus scenario."""
    return {
        "algorithm": "simple_majority",
        "agents": 4,
        "votes_for": 2,
        "votes_against": 2,
        "expected_result": "deadlock"
    }


# ============================================================================
# CONFLICT SCENARIOS
# ============================================================================

@pytest.fixture
def conflict_scenario():
    """Create a conflict scenario for testing."""
    return {
        "type": "voting_conflict",
        "agents_involved": ["agent_1", "agent_2", "agent_3"],
        "conflict_votes": {
            "agent_1": "for",
            "agent_2": "against",
            "agent_3": "for"
        },
        "resolution_strategy": "majority"
    }


@pytest.fixture
def deadlock_conflict():
    """Create a deadlock conflict scenario."""
    return {
        "type": "deadlock",
        "agents_involved": ["agent_1", "agent_2"],
        "conflict_votes": {
            "agent_1": "for",
            "agent_2": "against"
        },
        "resolution_strategy": "re_vote"
    }


# ============================================================================
# METRICS AND MONITORING
# ============================================================================

@pytest.fixture
def consensus_metrics():
    """Create mock consensus metrics."""
    return {
        "total_proposals": 100,
        "agreed_proposals": 85,
        "rejected_proposals": 10,
        "deadlocked_proposals": 5,
        "average_agreement_level": 0.82,
        "average_consensus_time_ms": 45.5
    }


@pytest.fixture
def coordination_metrics():
    """Create mock coordination metrics."""
    return {
        "total_agents": 10,
        "active_agents": 9,
        "inactive_agents": 1,
        "average_harmony": 0.88,
        "conflicts_resolved": 5,
        "conflicts_pending": 0
    }


# ============================================================================
# TIME SERIES DATA
# ============================================================================

@pytest.fixture
def time_series_data():
    """Create mock time series data for monitoring."""
    data = []
    base_time = datetime.now()
    for i in range(60):
        data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "agreement_level": 0.75 + (i % 20) * 0.01,
            "consensus_time_ms": 40 + (i % 30),
            "active_agents": 8 + (i % 3)
        })
    return data


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "consensus: mark test as consensus mechanism test"
    )
    config.addinivalue_line(
        "markers", "coordination: mark test as agent coordination test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
