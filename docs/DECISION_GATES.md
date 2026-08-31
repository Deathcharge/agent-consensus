# Operational decision gates

Consensus and authorization are different questions. `ConsensusResult` records what independent
participants agreed on. `DecisionPolicy` determines whether that evidence permits an application
action. Keeping them separate makes policy reviewable and prevents domain-specific release or
safety rules from changing the consensus arithmetic.

## Complete release-gate example

```python
from agent_consensus import DecisionPolicy, Vote, evaluate_decision, evaluate_votes

consensus = evaluate_votes(
    [
        Vote("security", "approve", weight=2),
        Vote("reliability", "approve"),
        Vote("product", "hold"),
    ],
    threshold=0.5,
    min_votes=3,
)
policy = DecisionPolicy(
    policy_id="release/production-v1",
    pass_choices={"approve"},
    veto_choices={"reject"},
    allowed_choices={"approve", "hold", "reject"},
    required_participants={"security", "reliability"},
    min_successful_weight=4,
)

verdict = evaluate_decision(consensus, policy)
assert verdict.passed
```

The same policy blocks if any successful participant casts `reject`, even when a weighted majority
agrees on `approve`. It becomes indeterminate if a required participant fails, the successful
weight is too low, a participant emits an unrecognized choice, or consensus itself is incomplete.

## Status precedence

The evaluator collects every applicable reason in a stable order and selects one status:

1. `blocked` when any configured veto is cast or the agreed winning choice is not a pass choice;
2. otherwise `indeterminate` when required evidence, vocabulary validation, quorum, or agreement is
   incomplete; and
3. otherwise `passed` with `policy_satisfied`.

Blocking evidence takes precedence over incomplete evidence. For example, a veto plus a missing
required reviewer remains blocked while both reason codes are retained for audit.

## Choice and identity contracts

### Minimum successful weight

The minimum-weight gate sums the decimal spellings (`str(weight)`) of successful participant
outcome weights exactly and compares that sum with `str(policy.min_successful_weight)`. It uses
standard-library rational arithmetic, with no absolute or relative tolerance. Thus `0.1` and `0.7`
together satisfy `0.8`, but a single `0.7999999999999999` does not. Neither `1e12` against
`1e12 + 0.5` nor `1e-15` against `2e-15` can pass. Errors and timeouts contribute no successful weight.

Consensus tallies, agreement, and the serialized `successful_weight` summary retain their existing
floating-point arithmetic. The gate recomputes its minimum check from outcomes; a rounded or
slightly inflated summary does not grant permission. The verdict's embedded outcomes and policy
snapshot are sufficient to reproduce this decimal calculation. This does not authenticate evidence.

Float inputs are interpreted as supplied, not as the expressions that produced them: a minimum
computed as `0.1 + 0.2` is `0.30000000000000004`, not `0.3`. Configure a reviewed decimal literal or
integer scale when that distinction matters. Minima remain serialized as floats under schema v1;
integer minima that would change decimal value during normalization (for example `2**53 + 1`)
raise `ConfigurationError` instead of silently changing the rule. Existing accepted policy snapshots
and their digests are unchanged. This rule tightens evaluation behavior, so record the library
version/commit alongside persisted verdicts; a policy digest alone does not identify the evaluator.

### Vocabulary and participant identity

Policy choices match `ChoiceTally.normalized_choice` exactly. Under the default normalizer, use
lowercase, whitespace-collapsed strings. When supplying a custom normalizer, configure and test the
policy against its exact output vocabulary.

Required participants match the canonical participant names in the result. The library verifies
that a named participant returned a successful, validated response; it does not authenticate the
person or service behind that name. Identity, authorization, and reviewer independence belong to
the host system.

`ConsensusResult` is an immutable public data model, not a signed receipt. Produce it with
`evaluate_votes` or `ConsensusEngine` inside the trusted process. Do not deserialize attacker-chosen
fields into a result and treat `evaluate_decision` as evidence verification. The decision evaluator
rechecks the result's builder invariants and rejects internally contradictory evidence, but that
structural check does not authenticate who produced a self-consistent result.

## Safe integration pattern

- Treat only `DecisionStatus.PASSED` as permission to proceed.
- Route `BLOCKED` and `INDETERMINATE` to different operational handling if useful, but fail closed
  for both.
- Enforce the verdict in the same trusted control plane that owns the protected action.
- Assign a versioned `policy_id` and retain its deterministic `digest` with deployment configuration.
- Persist or log `verdict.to_dict()` only after redacting response content and metadata. The payload
  includes schema versions, the applied policy snapshot, and its SHA-256 digest for audit. A digest
  detects content differences but is not a signature; authenticate policy distribution separately.
- Version policy configuration alongside the deployment or workflow that consumes it.
- Test custom normalizers and allowed vocabularies with casing, Unicode, whitespace, and unknown
  choices.

The evaluator has no network, persistence, retry, or side-effect behavior. It can sit after local
rules, provider-backed reviewers, OpenAI-style guardrails, or a broader agent framework, but it is
not itself an authorization service or deployment platform.
