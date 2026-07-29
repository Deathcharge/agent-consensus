# agent-consensus

`agent-consensus` is a small Python library for deterministic vote evaluation and bounded
asynchronous fan-out across independent agents, reviewers, or service adapters.

It is for developers who already have participants capable of returning an explicit decision such
as `approve`, `reject`, or `needs_review` and need one auditable answer. It does not call model
providers, manage agent conversations, or guess whether arbitrary prose is semantically equivalent.

Current maturity: **0.2 beta / release candidate**. The core API, tests, wheel, and examples are
ready for independent evaluation. Package publication remains an owner action.

## Why this exists

Full agent frameworks solve routing, conversation, tools, and state. This package has a narrower
job:

1. ask independent participants concurrently, within explicit limits;
2. collect an explicit `choice` from each successful participant;
3. normalize only casing and whitespace by default;
4. apply weighted threshold and quorum rules; and
5. return every tally, failure, timeout, duration, and reported token count.

Participant failures remain in the agreement denominator. A surviving minority cannot look like a
strong consensus merely because other participants failed.

## Requirements

- Python 3.10 or newer
- No runtime dependencies
- Provider credentials only if your own adapter needs them

Python 3.9 is not supported because it reached end of life in October 2025.

## Install

Until an owner publishes the distribution, install from a checkout:

```bash
git clone https://github.com/Deathcharge/agent-consensus.git
cd agent-consensus
python -m pip install .
```

For development, use the pinned contributor toolchain:

```bash
python -m pip install -r requirements-dev.txt
```

## Quick start: collected votes

```python
from agent_consensus import Vote, evaluate_votes

result = evaluate_votes(
    [
        Vote("security", "approve"),
        Vote("reliability", "APPROVE"),
        Vote("product", "hold"),
    ]
)

print(result.status.value)  # agreed
print(result.choice)        # approve
print(result.agreement)     # 0.666...
```

## Primary journey: query independent participants

Each adapter is an async callable that accepts a prompt and the engine's output-token allocation.
It must return `ParticipantResponse` with an explicit choice.

```python
import asyncio

from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    Participant,
    ParticipantResponse,
)


async def security_review(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    # Call your provider or local evaluator here. Honor max_tokens.
    return ParticipantResponse(
        choice="approve",
        content="No release blocker found.",
        tokens_used=42,
    )


async def reliability_review(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    return ParticipantResponse(choice="approve", tokens_used=31)


async def main() -> None:
    engine = ConsensusEngine(
        [
            Participant("security", security_review),
            Participant("reliability", reliability_review),
        ],
        config=ConsensusConfig(
            threshold=2 / 3,
            min_successful=2,
            timeout_seconds=10,
            max_concurrency=2,
            max_output_tokens_per_participant=500,
            max_total_output_tokens=1_000,
        ),
    )
    result = await engine.run("Should release 1.4 proceed?")
    print(result.to_dict())


asyncio.run(main())
```

The engine does not retry. This keeps external side effects and API spending predictable; adapters
that add retries should make them bounded and idempotent.

## Decision semantics

- The default threshold is two thirds of **all configured participant weight**.
- Quorum is a separate minimum count of successful responses (default: 2).
- Timeouts and errors do not vote and still count in the total configured weight.
- Equal leading weights are always `no_consensus`, even if a threshold of 0.5 is configured.
- The default normalizer only strips repeated whitespace and applies Unicode case folding.
- Supporting `content`, confidence, and metadata never change the vote.
- A custom normalizer is allowed, but it must return a non-empty string and becomes part of your
  application's trust boundary.

This is application-level deterministic voting. It is not a distributed-systems consensus protocol
and does not provide Byzantine fault tolerance, durable replication, or leader election.

## Safety, privacy, and cost controls

`ConsensusConfig` bounds participant count, concurrency, per-participant timeout, prompt length,
response length, per-participant requested output tokens, and total requested output tokens. The
engine cancels participant tasks when its own task is cancelled.

The package never logs or persists prompts, responses, metadata, or credentials. Error results retain
only the exception type, not the exception message. The returned result still contains participant
content and metadata, so the calling application controls redaction, retention, and access.

Token controls are contractual: the engine passes `max_tokens` to each adapter and rejects reported
usage above the allocation, but only the provider adapter can guarantee that an external API honors
the request. Cost is therefore approximately:

```text
sum(input_tokens × provider_input_rate + output_tokens × provider_output_rate)
```

The library itself has no hosted operating cost or telemetry.

See [SECURITY.md](SECURITY.md) for the trust model and reporting guidance.

## Development and verification

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy agent_consensus
python -m pytest
python -m build
python -m twine check dist/*
```

Run the offline examples after installing the package:

```bash
python examples/01_basic_consensus.py
python examples/02_conflict_resolution.py
python examples/03_fault_tolerance.py
python examples/04_monitoring.py
python examples/05_multi_proposal.py
```

CI is configured to run formatting, linting, strict type checking, coverage, Python 3.10–3.14 tests,
a Windows smoke test, artifact checks, isolated wheel installation, and every example. It does not
publish artifacts.

## Package and release

Build artifacts locally with `python -m build`. A release owner should then verify the package name,
version/tag, changelog, and PyPI ownership before configuring a Trusted Publisher. No publication
credentials belong in this repository.

The package uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Architecture

- `agent_consensus/models.py`: immutable public configuration, input, outcome, and result types
- `agent_consensus/core.py`: normalization, weighted tallying, async execution, and cancellation
- `agent_consensus/errors.py`: stable package-specific exceptions
- `agent_consensus/multi_ai_consensus.py`: compatibility import path without private Helix dependencies

Provider integrations belong in the consuming application. This keeps the library independently
usable and prevents credentials, model churn, provider SDKs, and retry policy from leaking into its
core API.

## Limitations

- No semantic clustering of free-form answers
- No provider SDK adapters, retries, persistent history, or telemetry
- No Byzantine-fault-tolerant protocol guarantees
- No automatic result synthesis; the winning `choice` is returned with all supporting content
- In-process `asyncio` execution only; no distributed scheduler

## Documentation

- [Getting started](docs/GETTING_STARTED.md)
- [API reference](docs/API_REFERENCE.md)
- [Decision model](docs/CONSENSUS_ALGORITHMS.md)
- [Productization record](docs/PRODUCTIZATION.md)
- [Contributing](CONTRIBUTING.md)

## License

MIT. See [LICENSE](LICENSE). No license change was made during productization.
