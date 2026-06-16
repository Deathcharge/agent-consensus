"""Example 3: Byzantine Fault Tolerance"""

from agent_consensus import ConsensusEngine

engine = ConsensusEngine()

# Votes with one faulty agent
votes = {
    "agent_1": "for",
    "agent_2": "for",
    "agent_3": "for",
    "agent_4": "for",
    "agent_5": "against",
    "agent_6": "against",
    "agent_7": "against"
}

faulty_agents = ["agent_7"]  # Agent 7 is faulty

# Use BFT
result = engine.bft(votes, faulty_agents)
print(f"BFT Result: {result}")
print(f"Faulty Agents: {faulty_agents}")
print(f"Consensus: Despite faulty agent, agreement reached")
