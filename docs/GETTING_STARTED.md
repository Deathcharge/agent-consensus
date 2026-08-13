# Getting started

This guide takes a new user from installation to an auditable async consensus result without any
network credentials.

## Install from source

```bash
git clone https://github.com/Deathcharge/agent-consensus.git
cd agent-consensus
python -m pip install .
```

Confirm the installed public API:

```bash
python -c "import agent_consensus; print(agent_consensus.__version__)"
```

Expected version for this checkout: `0.2.0`.

## Evaluate existing votes

```python
from agent_consensus import Vote, evaluate_votes

result = evaluate_votes(
    [Vote("a", "yes"), Vote("b", "YES"), Vote("c", "no")],
    threshold=2 / 3,
    min_votes=2,
)

assert result.agreed
assert result.choice == "yes"
```

Use this path when another system has already collected the votes. Voter names must be unique and
weights must be finite positive numbers.

## Adapt an async participant

A participant adapter has one method contract:

```python
async def adapter(prompt: str, *, max_tokens: int) -> ParticipantResponse: ...
```

The adapter owns provider configuration, credentials, input-token limits, and any retry behavior.
It should map provider output to a deliberately small decision vocabulary rather than put arbitrary
prose in `choice`.

```python
from agent_consensus import ParticipantResponse


async def policy_reviewer(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    decision = "approve" if "documented" in prompt.casefold() else "needs_review"
    return ParticipantResponse(
        choice=decision,
        content="Local deterministic example.",
        tokens_used=0,
        metadata={"source": "local-policy-v1"},
    )
```

## Run the engine

```python
import asyncio

from agent_consensus import ConsensusConfig, ConsensusEngine, Participant


async def main() -> None:
    engine = ConsensusEngine(
        [
            Participant("policy-a", policy_reviewer),
            Participant("policy-b", policy_reviewer),
        ],
        config=ConsensusConfig(
            threshold=1.0,
            min_successful=2,
            timeout_seconds=5,
            max_concurrency=2,
            max_output_tokens_per_participant=100,
            max_total_output_tokens=200,
        ),
    )
    result = await engine.run("The rollout is documented.")
    print(result.status.value, result.choice)


asyncio.run(main())
```

## Apply an operational policy

Use a decision policy when consensus protects an action rather than merely reporting a result:

```python
from agent_consensus import DecisionPolicy, DecisionStatus, evaluate_decision

policy = DecisionPolicy(
    pass_choices={"approve"},
    veto_choices={"needs_review"},
    allowed_choices={"approve", "needs_review"},
    required_participants={"policy-a", "policy-b"},
    min_successful_weight=2,
)
verdict = evaluate_decision(result, policy)

if verdict.status is DecisionStatus.PASSED:
    proceed()
elif verdict.status is DecisionStatus.BLOCKED:
    stop(verdict.reasons)
else:
    request_human_review(verdict.reasons)
```

Policy choice strings match normalized tally values exactly. With the default normalizer, use
lowercase, whitespace-collapsed values. Only `passed` should authorize the protected action.

## Handle every result state

```python
from agent_consensus import ConsensusStatus

if result.status is ConsensusStatus.AGREED:
    use(result.choice)
elif result.status is ConsensusStatus.NO_CONSENSUS:
    request_human_review(result.tallies)
else:  # quorum_failed
    retry_later_or_fail_closed(result.outcomes)
```

The library never retries automatically. A retry may repeat an external side effect or amplify cost,
so retry policy belongs with the adapter or caller that understands idempotency.

## Inspect failures safely

Each `ParticipantOutcome` contains `success`, `error`, or `timeout`, duration, weight, allocation, and
an exception type for failures. Exception messages are omitted because provider exceptions commonly
contain request details or credentials.

`result.to_dict()` is suitable for application-owned serialization when your metadata values are
JSON-compatible. It includes response content. Redact or omit fields before sending the result to a
log or third-party monitor.

## Next steps

- Read the exact [API reference](API_REFERENCE.md).
- Understand threshold and failure behavior in the [decision model](CONSENSUS_ALGORITHMS.md).
- Configure fail-closed application rules with [decision gates](DECISION_GATES.md).
- Adapt structured policy, ethics, workflow, and release evidence with the
  [integration cookbook](INTEGRATIONS.md).
- Run every script in [`examples/`](../examples/).
