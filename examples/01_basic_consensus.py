"""Example 1: Basic Consensus Workflow"""

from agent_consensus import ConsensusEngine

# Create engine
engine = ConsensusEngine()

# Create agents
agents = [
    {"id": "agent_1", "name": "Alice"},
    {"id": "agent_2", "name": "Bob"},
    {"id": "agent_3", "name": "Charlie"}
]

# Create proposal
proposal = {
    "id": "proposal_1",
    "content": "Increase budget by 10%",
    "proposer": "agent_1"
}

# Votes
votes = {
    "agent_1": "for",
    "agent_2": "for",
    "agent_3": "against"
}

# Reach consensus
result = engine.simple_majority(votes)
print(f"Consensus Result: {result}")
print(f"Proposal: {proposal['content']}")
