# Integration cookbook

`agent-consensus` does not import policy engines, agent frameworks, deployment systems, or provider
SDKs. Integrations translate an independently computed structured outcome into
`ParticipantResponse`, retain non-sensitive source identity in metadata, and map reviewed outcome
vocabularies with an explicit normalizer.

The runnable [`07_policy_panel.py`](../examples/07_policy_panel.py) combines authorization, ethics,
and operational-readiness decisions without requiring any sibling package.

## Shared vocabulary

Use a deliberately closed gate vocabulary. The following adapter accepts explicit outputs used by
common policy systems while keeping their meanings visible:

```python
from agent_consensus import normalize_choice

ALIASES = {
    "allow": "approve",
    "deny": "reject",
    "review": "hold",
    "ready": "approve",
}


def panel_normalizer(choice: str) -> str:
    normalized = normalize_choice(choice)
    return ALIASES.get(normalized, normalized)
```

Configure `allowed_choices={"approve", "hold", "reject"}` so a new upstream outcome fails closed
until the mapping and policy are reviewed.

## Structured policy decisions

An action-policy engine can become one independent participant. Evaluate the policy before entering
the adapter; do not let consensus weaken an individual policy's deny semantics.

```python
async def authorization_review(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    del prompt, max_tokens
    decision = action_policy.evaluate(request)
    return ParticipantResponse(
        choice=decision.effect.value,  # allow or deny
        metadata={
            "policy_id": decision.policy_id,
            "policy_version": decision.policy_version,
            "policy_digest": decision.policy_digest,
            "request_id": decision.request_id,
        },
    )
```

Do not copy a policy decision's explanatory reason into metadata by default; it may disclose request
or rule details. Retain bounded identifiers and keep the source audit record in its owning system.

## Ethics or safety decisions

An ethics evaluator with `allow`, `deny`, and `review` outcomes can be adapted independently:

```python
async def ethics_review(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    del prompt, max_tokens
    decision = ethics_engine.evaluate(context)
    return ParticipantResponse(
        choice=decision.outcome.value,
        metadata={
            "decision_id": decision.decision_id,
            "policy_id": decision.policy_id,
            "policy_version": decision.policy_version,
        },
    )
```

Configure `deny` as a veto (`reject` after normalization). A unanimous or weighted majority must not
override a source policy that already denied the action.

## Workflow approval step

In an embedded workflow, evaluate the panel immediately before the protected effect. Persist the
host workflow checkpoint and redacted verdict separately, then perform the action only for
`DecisionStatus.PASSED`. Use the workflow's stable idempotency key at the external destination; a
consensus verdict does not provide exactly-once delivery.

Do not place a paid or destructive effect inside a participant adapter. Participant calls may fail,
time out, or be cancelled, and the engine intentionally performs them concurrently.

## Deployment and incident tooling

A release gate can combine evidence such as:

- security and policy decisions;
- signed health/checker evidence;
- rollback or maintenance readiness;
- required release-owner review; and
- an explicit incident or change-management veto.

The host must authenticate reviewers and evidence sources. Participant names and metadata references
are audit context, not signatures. Keep deployment credentials and the actual deploy operation
outside the consensus process.

## Portfolio compatibility evidence

The adapter fields above reflect the locally inspected public contracts on 2026-08-01:

| Optional producer | Explicit outcome | Useful bounded identity |
| --- | --- | --- |
| Samsarix Policy Engine | `allow` / `deny` | policy ID, version, digest, request ID |
| Samsarix Ethics | `allow` / `deny` / `review` | decision ID, policy ID, policy version |
| Samsarix Orchestration | application-owned approval step | run/step ID and idempotency key |
| LaunchGuard | application-owned readiness decision | release marker and signed-evidence reference |

These are integration recipes, not runtime dependencies or claims of cross-repository release
compatibility. Pin and test the producer version in the consuming application. This repository's CI
verifies only the provider-neutral example and `agent-consensus` public contract.
