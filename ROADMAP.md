# agent-consensus roadmap

This roadmap separates implementation, release, publication, and adoption. Passing one gate does
not imply the next.

## Product boundary

Portfolio role: **standalone reusable library/SDK**. The package owns bounded collection of explicit
choices, deterministic consensus evaluation, and fail-closed operational policy verdicts. It does
not own provider clients, agent conversations, persistence, deployment execution, or authenticated
authorization. Other Samsarix repositories may consume its public API, but none is a runtime
dependency.

Current disposition: the original productization work and decision-gate capability are merged
(PR #12). Successful-weight boundary hardening, consistent fractional tallying, generated invariant
tests, and isolated artifact checks are the current release-candidate patch. Publication and
production adoption remain owner-controlled decisions.

## Release-candidate priorities

- Keep Python 3.10–3.14, Windows, lint, strict typing, coverage, artifact, installed-wheel, and
  offline-example checks green.
- Exercise one real consumer workflow using `DecisionPolicy` and record a versioned contract fixture.
- Confirm package-index ownership, license, release version, provenance workflow, and rollback before
  publication.
- Preserve immutable CI/action references and keep dependency upgrades isolated in reviewable PRs.

## Highest-value product work

1. Prove the documented policy-panel recipe in a separate package consumer with a pinned producer
   version and a versioned contract fixture.
2. Define a small versioned JSON Schema for persisted consensus/verdict audit records if a real
   consumer needs interchange.
3. Add an optional OpenTelemetry integration recipe only after adopters identify required fields
   and redaction boundaries.

Bounded exhaustive invariants now cover policy precedence, normalization, input ordering, policy
strengthening and decimal successful-weight boundaries. Expand their finite input spaces when real
consumers supply additional edge cases. Installed-wheel checks include a consumer-owned release
simulation, but that does not replace the separate real-consumer milestone above.

## Deliberate deferrals

- Provider SDKs and automatic retries remain caller-owned to avoid credential, cost, and lifecycle
  coupling.
- Authenticated human approval, durable storage, and deployment execution require a host control
  plane and are not claims of this in-process library.
- A hosted service, UI, billing, or subscription is unjustified without adoption evidence.
- Compatibility aliases do not recreate the extracted provider-specific API; any legacy consumer
  still requires an explicit migration check.

## Samsarix adoption

- Consume only released public APIs or artifacts—never sibling-source imports.
- Add a consumer-owned contract fixture covering identity, privacy, limits, errors, version
  compatibility, and the exact enforcement point.
- Make one implementation canonical only after parity, rollback, and ownership are proven.
- Record a support level, compatibility window, and measurable adoption signal.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, consumer
or deployment evidence, and rollback path are recorded in a pull request or release record. README
claims must not exceed that evidence.
