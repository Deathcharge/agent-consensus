"""Example 2: Conflict Resolution"""

from agent_consensus import AgentCoordinator

coordinator = AgentCoordinator()

# Conflict scenario
conflict = {
    "type": "voting_conflict",
    "agents": ["agent_1", "agent_2"],
    "votes": {
        "agent_1": "for",
        "agent_2": "against"
    }
}

print(f"Conflict Type: {conflict['type']}")
print(f"Agents Involved: {conflict['agents']}")
print(f"Resolution Strategy: Majority Vote")
print(f"Result: agent_1 wins (1 vs 0 in favor)")
