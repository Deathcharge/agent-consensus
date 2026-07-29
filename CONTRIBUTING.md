# Contributing

Contributions that keep `agent-consensus` small, deterministic, provider-neutral, and auditable are
welcome.

## Set up

```bash
git clone https://github.com/Deathcharge/agent-consensus.git
cd agent-consensus
python -m venv .venv
```

Activate the environment with your shell's normal command, then install the pinned contributor
toolchain:

```bash
python -m pip install -r requirements-dev.txt
```

## Verify a change

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy agent_consensus
python -m pytest
python -m build
python -m twine check dist/*
```

Tests enforce at least 95% branch-aware coverage of the package. Add behavior tests for error,
timeout, cancellation, and budget paths when changing orchestration.

## Design expectations

- Keep explicit decisions separate from supporting prose.
- Preserve deterministic outcomes and participant order.
- Bound new network, memory, retry, concurrency, persistence, and cost behavior.
- Do not add provider credentials or private Helix dependencies.
- Do not log prompts, response content, metadata, or exception messages.
- Document public API and semantics in the same change.
- Avoid adding a runtime dependency when the standard library is sufficient.

Provider integrations should normally live in consuming applications or separately versioned adapter
packages. A core integration proposal should include demand evidence, maintenance ownership, safe
credential handling, deterministic tests, and cost/cancellation behavior.

## Pull requests

Keep changes focused. Explain the user problem, behavioral contract, tests run, compatibility impact,
and any security/privacy/cost tradeoff. CI must pass on every supported Python version.

## Security issues

Follow [SECURITY.md](SECURITY.md). Do not put secrets or private model content in an issue or test
fixture.

By contributing, you agree that your contribution is provided under the existing MIT license.
