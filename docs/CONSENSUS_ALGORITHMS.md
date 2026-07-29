# Decision model

This package implements deterministic application-level vote aggregation. It deliberately does not
claim distributed-system consensus or Byzantine fault tolerance.

## Normalization

The default normalizer applies Unicode `casefold()`, trims leading and trailing whitespace, and
collapses internal whitespace. Thus `" APPROVE "` and `"approve"` share a tally. `"approve!"` and
`"approve"` do not.

Semantic clustering is outside scope because it introduces another model, cost, nondeterminism, and
a new failure mode into the decision boundary. Applications with domain aliases can supply an
explicit normalizer:

```python
aliases = {"approved": "approve", "yes": "approve"}
normalizer = lambda choice: aliases.get(choice.casefold(), choice.casefold())
```

Treat custom normalization as security-sensitive policy and test it with adversarial inputs.

## Weighted threshold

For every normalized choice, support is the sum of its successful participant weights.

```text
agreement = leading_choice_weight / total_configured_participant_weight
```

The result is `agreed` only when:

1. successful response count meets quorum;
2. there is one unique leading choice; and
3. agreement is greater than or equal to the configured threshold.

Failures remain in the denominator. With three equal participants, two `approve` responses and one
timeout produce `2 / 3`, not `1.0`.

## Quorum

Quorum is a count of successful, validated participant responses. It is separate from weighted
agreement so a single heavily weighted participant cannot satisfy a multi-party availability rule.

If quorum is missed, status is `quorum_failed` and choice is `None`, even when the available votes
all match. Callers should normally fail closed or request human review.

## Ties

Equal leading weights always produce `no_consensus`. This rule holds at a 0.5 threshold and prevents
participant order from deciding the outcome.

Tallies are returned in deterministic order: descending weight, then normalized choice.

## Confidence

A participant may report confidence for auditing, but it does not modify vote weight. Allowing
self-reported confidence to silently change authority makes decisions difficult to reason about.
Assign deliberate participant weights instead.

## Failure semantics

- A timeout produces a `timeout` outcome.
- Any other participant or response-contract exception produces an `error` outcome.
- Only exception type is returned; exception messages are discarded.
- Sibling calls continue after ordinary participant failure.
- Cancelling the engine cancels all participant tasks and propagates cancellation.
- No automatic retries occur.

## What this does not guarantee

The engine runs in one Python process. It provides no durable log, replicated state machine,
authenticated identity, network membership, leader election, equivocation detection, or tolerance
proof. Do not use it as a substitute for Raft, Paxos, PBFT, database transactions, or a safety-critical
human approval system.
