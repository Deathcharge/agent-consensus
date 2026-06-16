"""Example 4: Monitoring and Metrics"""

from agent_consensus import ConsensusEngine

engine = ConsensusEngine()

# Simulate metrics
metrics = {
    "total_proposals": 100,
    "agreed_proposals": 85,
    "rejected_proposals": 10,
    "deadlocked_proposals": 5,
    "average_agreement_level": 0.82,
    "average_consensus_time_ms": 45.5
}

print("=== Consensus Metrics ===")
print(f"Total Proposals: {metrics['total_proposals']}")
print(f"Agreed: {metrics['agreed_proposals']}")
print(f"Rejected: {metrics['rejected_proposals']}")
print(f"Deadlocked: {metrics['deadlocked_proposals']}")
print(f"Average Agreement: {metrics['average_agreement_level']:.2%}")
print(f"Average Time: {metrics['average_consensus_time_ms']:.1f}ms")
