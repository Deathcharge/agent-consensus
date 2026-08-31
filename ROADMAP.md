# agent-consensus roadmap

This roadmap separates implementation, release, publication, and adoption. Passing one gate does
not imply the next.

## Product boundary

Portfolio role: **standalone reusable library/SDK**. The package owns bounded collection of explicit
choices, deterministic consensus evaluation, and fail-closed operational policy verdicts. It does
not own provider clients, agent conversations, persistence, deployment execution, or authenticated
authorization. Other Samsarix repositories may consume its public API, but none is a runtime
dependency.

Current disposition: the original productization work and decision-gate capability (PR #12),
numeric hardening and artifact checks (PR #14), and optional installed producer/consumer integration
(PR #15) are merged to `main`. Main-push CI now retains checksum-bound candidate artifacts for
owner review. Publication and production adoption remain owner-controlled decisions.

## Release-candidate priorities

- Keep Python 3.10–3.14, Windows, lint, strict typing, coverage, artifact, installed-wheel, and
  offline-example checks green.
- Keep the optional installed policy-engine consumer and versioned contract fixture green; obtain
  a real application's consumer-owned enforcement evidence before claiming production adoption.
- Confirm package-index ownership, license, release version, provenance workflow, and rollback before
  publication.
- Verify a downloaded candidate against the successful CI run's commit and separately recorded
  receipt digest before installing or publishing it; unsigned checksums are not signed provenance.
- Preserve immutable CI/action references and keep dependency upgrades isolated in reviewable PRs.

## Highest-value product work

1. Adopt the verified policy-panel contract in a real application's own CI and actual enforcement
   point. The separately packaged reference consumer now verifies the pinned producer through
   installed wheels, including deny precedence, drift and error handling.
2. Define a small versioned JSON Schema for persisted consensus/verdict audit records if a real
   consumer needs interchange.
3. Add an optional OpenTelemetry integration recipe only after adopters identify required fields
   and redaction boundaries.

Bounded exhaustive invariants now cover policy precedence, normalization, input ordering, policy
strengthening and decimal successful-weight boundaries. Expand their finite input spaces when real
consumers supply additional edge cases. Core installed-wheel checks include a dependency-free release
simulation, and the optional policy-engine integration verifies a real installed producer. Neither
replaces evidence from an externally adopted application's actual action boundary.

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
