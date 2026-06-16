# Agent Consensus Engine - API Reference

## Overview

The Agent Consensus Engine provides a comprehensive framework for multi-agent coordination and consensus protocols. This document details all public APIs and their usage.

## Core Classes

### ConsensusEngine

The main consensus engine for reaching agreement among agents.

```python
from agent_consensus import ConsensusEngine

engine = ConsensusEngine()
result = engine.reach_consensus(agents, proposal)
```

**Methods:**
- `reach_consensus(agents, proposal)` - Reach consensus on a proposal
- `calculate_agreement(votes)` - Calculate agreement level
- `get_consensus_state()` - Get current consensus state

### AgentCoordinator

Coordinates multiple agents and manages their interactions.

```python
from agent_consensus import AgentCoordinator

coordinator = AgentCoordinator()
coordinator.register_agent(agent)
coordinator.coordinate_agents(agents)
```

**Methods:**
- `register_agent(agent)` - Register an agent
- `get_agent_state(agent_id)` - Get agent state
- `coordinate_agents(agents)` - Coordinate multiple agents
- `resolve_conflict(conflict)` - Resolve agent conflicts

## Consensus Algorithms

### Simple Majority

Requires more than 50% agreement.

```python
result = engine.simple_majority(votes)
```

### Supermajority

Requires 2/3 majority.

```python
result = engine.supermajority(votes)
```

### Unanimous

Requires 100% agreement.

```python
result = engine.unanimous(votes)
```

### Byzantine Fault Tolerant (BFT)

Handles faulty agents.

```python
result = engine.bft(votes, faulty_agents)
```

## Data Structures

### Proposal

```python
{
    "id": "proposal_1",
    "content": "Proposal content",
    "proposer": "agent_1",
    "timestamp": "2026-04-12T12:00:00",
    "status": "pending",
    "votes": {}
}
```

### ConsensusResult

```python
{
    "proposal_id": "proposal_1",
    "status": "agreed",
    "agreement_level": 0.8,
    "votes_for": 4,
    "votes_against": 1,
    "abstentions": 0,
    "timestamp": "2026-04-12T12:00:00"
}
```

### AgentState

```python
{
    "id": "agent_1",
    "name": "Agent1",
    "state": "active",
    "last_update": "2026-04-12T12:00:00",
    "metrics": {
        "consensus_reached": 10,
        "votes_cast": 15,
        "conflicts_resolved": 2
    }
}
```

## Error Handling

### ConsensusTimeoutError

Raised when consensus cannot be reached within timeout.

```python
try:
    result = engine.reach_consensus(agents, proposal)
except ConsensusTimeoutError:
    print("Consensus timeout")
```

### ConflictError

Raised when unresolvable conflicts occur.

```python
try:
    engine.resolve_conflict(conflict)
except ConflictError:
    print("Conflict resolution failed")
```

## Examples

### Basic Consensus

```python
from agent_consensus import ConsensusEngine

engine = ConsensusEngine()
agents = [agent1, agent2, agent3]
proposal = {"id": "p1", "content": "Test"}
result = engine.reach_consensus(agents, proposal)
print(f"Agreement: {result['agreement_level']}")
```

### Multi-Agent Coordination

```python
from agent_consensus import AgentCoordinator

coordinator = AgentCoordinator()
for agent in agents:
    coordinator.register_agent(agent)
    
state = coordinator.coordinate_agents(agents)
print(f"Coordination status: {state['status']}")
```

### Conflict Resolution

```python
conflict = {
    "type": "voting_conflict",
    "agents": ["agent_1", "agent_2"],
    "votes": {"agent_1": "for", "agent_2": "against"}
}
result = coordinator.resolve_conflict(conflict)
print(f"Resolved: {result['resolved']}")
```

## Best Practices

1. **Always handle timeouts** - Set appropriate timeout values
2. **Monitor metrics** - Track consensus performance
3. **Use appropriate algorithms** - Choose based on your requirements
4. **Handle conflicts gracefully** - Implement recovery strategies
5. **Log all operations** - Enable comprehensive logging

## Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Simple Majority | O(n) | O(n) |
| Supermajority | O(n) | O(n) |
| Unanimous | O(n) | O(n) |
| BFT | O(n²) | O(n²) |

Where n is the number of agents.
