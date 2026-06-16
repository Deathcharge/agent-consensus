# Consensus Algorithms Guide

## Overview

This guide explains the different consensus algorithms available in the Agent Consensus Engine and when to use each one.

## Algorithm Comparison

| Algorithm | Requirement | Fault Tolerance | Use Case |
|-----------|-------------|-----------------|----------|
| Simple Majority | > 50% | None | General voting |
| Supermajority | ≥ 2/3 | Low | Important decisions |
| Unanimous | 100% | None | Critical decisions |
| BFT | ≥ 2/3 | High | Untrusted agents |

## Simple Majority

**Requirement:** More than 50% agreement

**Formula:** votes_for > (votes_for + votes_against) / 2

**Example:**
```python
votes = {"for": 3, "against": 2}
result = engine.simple_majority(votes)  # Result: agreed
```

**When to use:**
- General voting
- Quick decisions
- Low-stakes proposals

## Supermajority

**Requirement:** At least 2/3 majority

**Formula:** votes_for ≥ (votes_for + votes_against) * 2/3

**Example:**
```python
votes = {"for": 4, "against": 1}
result = engine.supermajority(votes)  # Result: agreed
```

**When to use:**
- Important decisions
- Policy changes
- Resource allocation

## Unanimous

**Requirement:** 100% agreement

**Formula:** votes_against == 0 AND votes_for > 0

**Example:**
```python
votes = {"for": 5, "against": 0}
result = engine.unanimous(votes)  # Result: agreed
```

**When to use:**
- Critical decisions
- Security policies
- System changes

## Byzantine Fault Tolerant (BFT)

**Requirement:** At least 2/3 agreement despite faulty agents

**Formula:** votes_for ≥ (total_agents - faulty_agents) * 2/3

**Example:**
```python
votes = {"for": 5, "against": 0}
faulty = ["agent_3"]
result = engine.bft(votes, faulty_agents=faulty)  # Result: agreed
```

**When to use:**
- Untrusted agents
- Distributed systems
- High-reliability requirements

## Selection Guide

### Decision Tree

1. **Do you need to handle faulty agents?**
   - Yes → Use **BFT**
   - No → Continue to 2

2. **How critical is the decision?**
   - Very critical → Use **Unanimous**
   - Important → Use **Supermajority**
   - General → Use **Simple Majority**

3. **What's your agreement threshold?**
   - 100% → Use **Unanimous**
   - 66%+ → Use **Supermajority** or **BFT**
   - 50%+ → Use **Simple Majority**

## Implementation Details

### Simple Majority Implementation

```python
def simple_majority(votes):
    for_count = sum(1 for v in votes.values() if v == "for")
    against_count = sum(1 for v in votes.values() if v == "against")
    total = for_count + against_count
    return for_count > total / 2
```

### Supermajority Implementation

```python
def supermajority(votes):
    for_count = sum(1 for v in votes.values() if v == "for")
    against_count = sum(1 for v in votes.values() if v == "against")
    total = for_count + against_count
    required = total * 2 / 3
    return for_count >= required
```

### Unanimous Implementation

```python
def unanimous(votes):
    against_count = sum(1 for v in votes.values() if v == "against")
    return against_count == 0 and len(votes) > 0
```

### BFT Implementation

```python
def bft(votes, faulty_agents):
    for_count = sum(1 for v in votes.values() if v == "for")
    total_agents = len(votes)
    faulty_count = len(faulty_agents)
    required = (total_agents - faulty_count) * 2 / 3
    return for_count >= required
```

## Performance Tuning

### Timeout Configuration

```python
engine = ConsensusEngine(timeout=30)  # 30 seconds
```

### Batch Processing

```python
# Process multiple proposals efficiently
for proposal in proposals:
    result = engine.reach_consensus(agents, proposal)
```

### Caching Results

```python
# Cache consensus results for identical proposals
cache = {}
if proposal_id in cache:
    result = cache[proposal_id]
else:
    result = engine.reach_consensus(agents, proposal)
    cache[proposal_id] = result
```

## Troubleshooting

### Consensus Failures

**Problem:** Consensus fails frequently

**Solution:** Use a more lenient algorithm
```python
# Change from Unanimous to Supermajority
result = engine.supermajority(votes)
```

### Timeout Issues

**Problem:** Consensus takes too long

**Solution:** Increase timeout or use faster algorithm
```python
engine = ConsensusEngine(timeout=60)
```

### Faulty Agent Handling

**Problem:** Faulty agents block consensus

**Solution:** Use BFT algorithm
```python
result = engine.bft(votes, faulty_agents=faulty_list)
```
