# Getting Started with Agent Consensus Engine

## Installation

### Via pip

```bash
pip install agent-consensus
```

### From source

```bash
git clone https://github.com/Deathcharge/agent-consensus.git
cd agent-consensus
pip install -e .
```

### Development

```bash
git clone https://github.com/Deathcharge/agent-consensus.git
cd agent-consensus
pip install -r requirements-test.txt
pytest tests/
```

## 5-Minute Quick Start

### 1. Import the engine

```python
from agent_consensus import ConsensusEngine, AgentCoordinator
```

### 2. Create agents

```python
agents = [
    {"id": "agent_1", "name": "Alice"},
    {"id": "agent_2", "name": "Bob"},
    {"id": "agent_3", "name": "Charlie"}
]
```

### 3. Create a proposal

```python
proposal = {
    "id": "proposal_1",
    "content": "Increase budget by 10%",
    "proposer": "agent_1"
}
```

### 4. Reach consensus

```python
engine = ConsensusEngine()
result = engine.reach_consensus(agents, proposal)
print(f"Status: {result['status']}")
print(f"Agreement: {result['agreement_level']}")
```

## Common Patterns

### Pattern 1: Simple Majority Voting

```python
votes = {
    "agent_1": "for",
    "agent_2": "for",
    "agent_3": "against"
}
result = engine.simple_majority(votes)
```

### Pattern 2: Multi-Agent Coordination

```python
coordinator = AgentCoordinator()
for agent in agents:
    coordinator.register_agent(agent)
state = coordinator.coordinate_agents(agents)
```

### Pattern 3: Conflict Resolution

```python
conflict = {
    "type": "voting_conflict",
    "agents": ["agent_1", "agent_2"]
}
resolved = coordinator.resolve_conflict(conflict)
```

### Pattern 4: Byzantine Fault Tolerance

```python
faulty_agents = ["agent_3"]
result = engine.bft(votes, faulty_agents)
```

### Pattern 5: Monitoring and Metrics

```python
metrics = engine.get_metrics()
print(f"Total proposals: {metrics['total_proposals']}")
print(f"Agreement rate: {metrics['agreement_rate']}")
```

## Troubleshooting

### Consensus Timeout

**Problem:** Consensus takes too long to reach

**Solution:**
```python
engine = ConsensusEngine(timeout=30)  # Set timeout in seconds
```

### Deadlock

**Problem:** Agents cannot reach agreement

**Solution:**
```python
# Use supermajority instead of unanimous
result = engine.supermajority(votes)
```

### Agent Failure

**Problem:** Agent becomes unavailable

**Solution:**
```python
# Use BFT to handle faulty agents
result = engine.bft(votes, faulty_agents=["agent_3"])
```

## Next Steps

- Read the [API Reference](API_REFERENCE.md)
- Explore [Consensus Algorithms](CONSENSUS_ALGORITHMS.md)
- Check out [Examples](../examples/)
- Review [Contributing Guide](../CONTRIBUTING.md)
