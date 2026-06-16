"""Example 5: Multi-Proposal Workflow"""

from agent_consensus import ConsensusEngine

engine = ConsensusEngine()

# Multiple proposals
proposals = [
    {"id": "p1", "content": "Budget increase"},
    {"id": "p2", "content": "Policy change"},
    {"id": "p3", "content": "Resource allocation"}
]

# Votes for each proposal
votes_set = [
    {"for": 4, "against": 1},
    {"for": 3, "against": 2},
    {"for": 5, "against": 0}
]

print("=== Multi-Proposal Consensus ===")
for i, (proposal, votes) in enumerate(zip(proposals, votes_set)):
    result = engine.simple_majority(votes)
    status = "AGREED" if result else "REJECTED"
    print(f"{proposal['id']}: {proposal['content']} - {status}")
