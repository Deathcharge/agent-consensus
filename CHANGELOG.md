# Changelog

This project follows semantic versioning. Dates use ISO 8601.

## Unreleased

### Added

- Fail-closed operational decision policies with pass, veto, vocabulary, required-participant, and
  successful-weight rules
- Stable decision statuses and reason codes with JSON-serializable audit verdicts
- Versioned policy snapshots with optional IDs and deterministic SHA-256 content digests
- A complete offline release-gate example and decision-gate integration guide
- A provider-neutral policy-panel example and optional integration cookbook
- A package-specific `DecisionInputError` that remains compatible with `TypeError`
- An isolated installed-wheel consumer check covering artifact identity, numeric boundaries,
  release enforcement and caller-owned audit redaction without extra test dependencies

### Changed

- Pinned CI actions to reviewed immutable commit SHAs
- Disabled persisted checkout credentials in every CI job
- Updated the contributor test runner to pytest 9.0.3, closing CVE-2025-71176 in the pinned
  development toolchain
- Consolidated threshold and quorum-setting validation across public entry points
- Made immutable participant responses safely hashable without hashing caller-owned metadata
- Corrected review-discovered documentation and metadata-serialization coverage gaps
- Enforce minimum successful weight using exact decimal-spelling sums from participant outcomes,
  preventing large- and tiny-scale tolerance bypasses while preserving `0.1 + 0.7` against `0.8`
- Reject integer policy minima that would silently change during float normalization
- Run installed-wheel checks and all examples in Python isolated mode to prevent checkout imports

## 0.2.0 - 2026-07-28

### Added

- Deterministic weighted vote evaluation with explicit quorum and tie behavior
- Provider-neutral async participant protocol
- Timeouts, cancellation cleanup, concurrency and size caps, and requested token budgets
- Immutable typed results with complete tallies and sanitized participant outcomes
- Zero-runtime-dependency package with a `py.typed` marker
- Real production-code tests, cross-version CI, wheel smoke testing, and offline examples
- Security guidance and a living productization record
- Samsarix LLC ownership, support contacts, citation metadata, attribution, and trademark guidance
- A repeatable owner-gated release procedure and an evidence-backed licensing decision record

### Changed

- Replaced private `helix-unified` imports with dependency injection
- Replaced fictional `ConsensusEngine`, `AgentCoordinator`, BFT, and production-readiness claims
- Consolidated packaging metadata in `pyproject.toml`
- Raised the supported Python floor to 3.10 because Python 3.9 is end-of-life
- Clarified the standalone boundary between this explicit-vote primitive and richer sibling tools

### Removed

- Unpublished `helix-hub-shared` and unused `pydantic` runtime dependencies
- Provider-specific wrappers that ignored their API key arguments
- Mock-only tests and fabricated monitoring examples

## 0.1.0 - unreleased extraction

Initial source extraction from `helix-unified`. Its wheel omitted the implementation package and its
runtime dependency could not be resolved from a public package index.
