# Changelog

This project follows semantic versioning. Dates use ISO 8601.

## 0.2.0 - 2026-07-28

### Added

- Deterministic weighted vote evaluation with explicit quorum and tie behavior
- Provider-neutral async participant protocol
- Timeouts, cancellation cleanup, concurrency and size caps, and requested token budgets
- Immutable typed results with complete tallies and sanitized participant outcomes
- Zero-runtime-dependency package with a `py.typed` marker
- Real production-code tests, cross-version CI, wheel smoke testing, and offline examples
- Security guidance and a living productization record

### Changed

- Replaced private `helix-unified` imports with dependency injection
- Replaced fictional `ConsensusEngine`, `AgentCoordinator`, BFT, and production-readiness claims
- Consolidated packaging metadata in `pyproject.toml`
- Raised the supported Python floor to 3.10 because Python 3.9 is end-of-life

### Removed

- Unpublished `helix-hub-shared` and unused `pydantic` runtime dependencies
- Provider-specific wrappers that ignored their API key arguments
- Mock-only tests and fabricated monitoring examples

## 0.1.0 - unreleased extraction

Initial source extraction from `helix-unified`. Its wheel omitted the implementation package and its
runtime dependency could not be resolved from a public package index.
