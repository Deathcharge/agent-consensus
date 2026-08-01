# API reference

All supported public names are exported from `agent_consensus`. Type hints ship with a `py.typed`
marker.

## ConsensusEngine

```python
ConsensusEngine(
    participants: Iterable[Participant],
    *,
    config: ConsensusConfig | None = None,
    normalizer: Callable[[str], str] = normalize_choice,
)
```

Construction rejects an empty participant list, duplicate names, impossible quorum, participant
counts above the configured cap, and a total token budget too small to allocate one token per
participant.

### `await run(prompt: str) -> ConsensusResult`

Queries participants with bounded concurrency and a timeout for each active call. Queue time is
included in outcome duration but not in the individual call timeout. Worst-case run time is roughly
`ceil(participants / max_concurrency) × timeout_seconds`, plus cancellation cleanup and local work.

Cancellation of `run()` cancels all outstanding participant tasks and waits for their cleanup before
propagating `CancelledError`.

## ConsensusConfig

Immutable settings with safe finite defaults:

| Field | Default | Meaning |
| --- | ---: | --- |
| `threshold` | `2 / 3` | Required leading weight divided by all configured weight |
| `min_successful` | `2` | Successful responses required for quorum |
| `timeout_seconds` | `30.0` | Timeout for one active participant call |
| `max_concurrency` | `4` | Simultaneous participant calls |
| `max_participants` | `32` | Fan-out cap |
| `max_prompt_characters` | `100_000` | Prompt size cap before calls start |
| `max_response_characters` | `100_000` | Supporting-content cap per response |
| `max_output_tokens_per_participant` | `1_000` | Requested per-call output cap |
| `max_total_output_tokens` | `4_000` | Requested output cap split across all participants |

The effective `max_tokens` passed to each participant is:

```text
min(max_output_tokens_per_participant, floor(max_total_output_tokens / participant_count))
```

## Participant

```python
Participant(name: str, responder: Responder, weight: float = 1.0)
```

Names must be unique and at most 128 characters. Weight must be finite and positive.

## Responder protocol

```python
async def __call__(prompt: str, *, max_tokens: int) -> ParticipantResponse: ...
```

Any async function or callable object with this shape is accepted. Returning another type produces
an error outcome rather than crashing sibling calls.

## ParticipantResponse

```python
ParticipantResponse(
    choice: str,
    content: str = "",
    confidence: float | None = None,
    tokens_used: int | None = None,
    metadata: Mapping[str, Any] = {},
)
```

Only `choice` affects consensus. It must be non-empty and at most 256 characters. Confidence, when
present, must be between 0 and 1. Reported tokens cannot be negative or exceed the allocation passed
to the adapter. Metadata is returned unchanged and is never logged by the library.

## `evaluate_votes`

```python
evaluate_votes(
    votes: Iterable[Vote],
    *,
    threshold: float = 2 / 3,
    min_votes: int = 1,
    normalizer: Callable[[str], str] = normalize_choice,
) -> ConsensusResult
```

Synchronously evaluates already collected votes. Duplicate voter names are rejected. Because every
input is a collected vote, this helper has no error or timeout outcomes.

## DecisionPolicy

```python
DecisionPolicy(
    pass_choices: Collection[str] = {"approve"},
    veto_choices: Collection[str] = {},
    allowed_choices: Collection[str] | None = None,
    required_participants: Collection[str] = {},
    min_successful_weight: float = 0.0,
)
```

Immutable operational rules applied after consensus evaluation. Choice configuration matches
`ChoiceTally.normalized_choice` exactly. `pass_choices` cannot be empty; pass and veto choices
cannot overlap; and an allowed vocabulary, when supplied, must include all pass and veto choices.

## `evaluate_decision`

```python
evaluate_decision(
    consensus: ConsensusResult,
    policy: DecisionPolicy,
) -> DecisionVerdict
```

Returns `passed` only for an agreed pass choice when all configured evidence rules are satisfied.
An explicit veto or agreed non-pass choice returns `blocked`. Missing required participants,
insufficient successful weight, an unexpected choice, quorum failure, or no consensus returns
`indeterminate` unless blocking evidence is also present.

`DecisionVerdict` exposes stable reason codes, the normalized winning choice, sorted veto and
unavailable-participant lists, unexpected choices, the configured weight requirement, the complete
applied policy snapshot, the complete underlying `ConsensusResult`, a `passed` convenience
property, and `to_dict()`.

## Vote

```python
Vote(participant: str, choice: str, weight: float = 1.0)
```

Participant and choice must be non-empty. Weight must be finite and positive.

## ConsensusResult

Important fields:

- `status`: `ConsensusStatus.AGREED`, `NO_CONSENSUS`, or `QUORUM_FAILED`
- `choice`: leading original choice only when agreed; otherwise `None`
- `agreement`: leading weight divided by all configured weight
- `quorum_reached`: whether the successful response count met the minimum
- `successful_count`, `total_count`, `successful_weight`, `total_weight`
- `reported_tokens_used`: sum of non-null successful token reports
- `token_usage_complete`: true only when every successful response reported usage
- `tallies`: ordered weighted support by normalized choice
- `outcomes`: participant-order execution details
- `duration_ms`: total local run duration
- `agreed`: convenience boolean
- `to_dict()`: full dictionary representation

## Enums

`ConsensusStatus` values: `agreed`, `no_consensus`, `quorum_failed`.

`ResponseStatus` values: `success`, `error`, `timeout`.

`DecisionStatus` values: `passed`, `blocked`, `indeterminate`.

`DecisionReason` values: `policy_satisfied`, `veto_cast`, `winning_choice_not_permitted`,
`required_participant_unavailable`, `successful_weight_below_minimum`, `unexpected_choice`,
`quorum_failed`, and `no_consensus`.

## Exceptions

- `ConsensusError`: base package exception
- `ConfigurationError`: invalid bounds, thresholds, participants, or budgets
- `DuplicateParticipantError`: repeated participant identity
- `ResponseValidationError`: invalid prompts, votes, responses, or normalizer output

Participant exceptions are isolated into sanitized outcomes. Configuration and caller-input errors
are raised directly.

## Compatibility import path

`agent_consensus.multi_ai_consensus` re-exports the standalone types and aliases
`MultiAIConsensus` to `ConsensusEngine` and `ConsensusResponse` to `ConsensusResult`. Provider-specific
clients from the extracted source were not preserved because they depended on a private
`helix-unified` service and were never present in the built 0.1 wheel.
