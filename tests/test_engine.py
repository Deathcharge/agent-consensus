"""Tests for bounded asynchronous participant orchestration."""

import asyncio
import json
from collections.abc import Awaitable, Callable

import pytest

from agent_consensus import (
    ConfigurationError,
    ConsensusConfig,
    ConsensusEngine,
    ConsensusStatus,
    DecisionPolicy,
    DuplicateParticipantError,
    Participant,
    ParticipantResponse,
    ResponseStatus,
    ResponseValidationError,
    evaluate_decision,
)

ResponseCallable = Callable[..., Awaitable[ParticipantResponse]]


def responder(
    choice: str,
    *,
    delay: float = 0,
    tokens_used: int | None = 1,
    content: str = "",
) -> ResponseCallable:
    async def respond(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        assert prompt
        assert max_tokens > 0
        if delay:
            await asyncio.sleep(delay)
        return ParticipantResponse(
            choice=choice,
            content=content,
            tokens_used=tokens_used,
        )

    return respond


def failing_responder(message: str = "failure") -> ResponseCallable:
    async def respond(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        raise RuntimeError(message)

    return respond


@pytest.mark.asyncio
async def test_engine_completes_the_primary_consensus_journey() -> None:
    engine = ConsensusEngine(
        [
            Participant("security", responder("approve", content="No blocker.")),
            Participant("reliability", responder("APPROVE")),
            Participant("product", responder("hold")),
        ]
    )

    result = await engine.run("Should this release proceed?")

    assert result.status is ConsensusStatus.AGREED
    assert result.choice == "approve"
    assert result.successful_count == 3
    assert result.reported_tokens_used == 3
    assert result.token_usage_complete
    assert [outcome.participant for outcome in result.outcomes] == [
        "security",
        "reliability",
        "product",
    ]


@pytest.mark.asyncio
async def test_fractional_unanimity_passes_the_policy_gate() -> None:
    engine = ConsensusEngine(
        [
            Participant(str(index), responder("approve"), weight)
            for index, weight in enumerate((1e-15, 1.0, 0.1))
        ],
        config=ConsensusConfig(threshold=1.0),
    )
    result = await engine.run("fractional release gate")
    assert result.agreement == 1.0
    assert evaluate_decision(result, DecisionPolicy()).passed


def test_aggregate_weight_overflow_fails_before_any_adapter_call() -> None:
    calls: list[str] = []

    async def unexpected(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        calls.append(prompt)
        return ParticipantResponse(choice="approve")

    with pytest.raises(ConfigurationError, match="total participant weight"):
        ConsensusEngine([Participant("a", unexpected, 1e308), Participant("b", unexpected, 1e308)])
    assert calls == []


@pytest.mark.asyncio
async def test_failures_are_sanitized_and_count_against_agreement() -> None:
    engine = ConsensusEngine(
        [
            Participant("healthy", responder("approve")),
            Participant("broken", failing_responder("sk-secret-value")),
        ],
        config=ConsensusConfig(threshold=0.5, min_successful=1),
    )

    result = await engine.run("review")
    encoded = json.dumps(result.to_dict())

    assert result.status is ConsensusStatus.AGREED
    assert result.agreement == 0.5
    assert result.successful_weight == 1
    assert result.total_weight == 2
    assert result.outcomes[1].status is ResponseStatus.ERROR
    assert result.outcomes[1].error_type == "RuntimeError"
    assert "sk-secret-value" not in encoded


@pytest.mark.asyncio
async def test_timeout_is_visible_and_can_fail_quorum() -> None:
    engine = ConsensusEngine(
        [
            Participant("fast", responder("approve")),
            Participant("slow", responder("approve", delay=0.1)),
        ],
        config=ConsensusConfig(timeout_seconds=0.01, min_successful=2),
    )

    result = await engine.run("review")

    assert result.status is ConsensusStatus.QUORUM_FAILED
    assert result.outcomes[1].status is ResponseStatus.TIMEOUT
    assert result.outcomes[1].error_type == "TimeoutError"


@pytest.mark.asyncio
async def test_concurrency_limit_is_enforced() -> None:
    active = 0
    peak = 0

    async def tracked(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        nonlocal active, peak
        del prompt, max_tokens
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.001)
        active -= 1
        return ParticipantResponse(choice="yes")

    engine = ConsensusEngine(
        [Participant(str(index), tracked) for index in range(4)],
        config=ConsensusConfig(max_concurrency=1),
    )

    result = await engine.run("review")

    assert result.agreed
    assert peak == 1


@pytest.mark.asyncio
async def test_total_output_budget_is_split_before_calls() -> None:
    allocations: list[int] = []

    async def captures_budget(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt
        allocations.append(max_tokens)
        return ParticipantResponse(choice="yes", tokens_used=max_tokens)

    engine = ConsensusEngine(
        [Participant(str(index), captures_budget) for index in range(3)],
        config=ConsensusConfig(
            max_output_tokens_per_participant=10,
            max_total_output_tokens=8,
        ),
    )

    result = await engine.run("review")

    assert allocations == [2, 2, 2]
    assert result.reported_tokens_used == 6


@pytest.mark.asyncio
async def test_reported_token_overage_invalidates_response() -> None:
    engine = ConsensusEngine(
        [
            Participant("over", responder("yes", tokens_used=3)),
            Participant("within", responder("yes", tokens_used=2)),
        ],
        config=ConsensusConfig(
            threshold=0.5,
            min_successful=1,
            max_output_tokens_per_participant=2,
            max_total_output_tokens=4,
        ),
    )

    result = await engine.run("review")

    assert result.outcomes[0].status is ResponseStatus.ERROR
    assert result.outcomes[0].error_type == "ResponseValidationError"
    assert result.successful_count == 1


@pytest.mark.asyncio
async def test_oversized_content_invalidates_response() -> None:
    engine = ConsensusEngine(
        [Participant("large", responder("yes", content="12345"))],
        config=ConsensusConfig(
            threshold=1,
            min_successful=1,
            max_response_characters=4,
        ),
    )

    result = await engine.run("review")

    assert result.status is ConsensusStatus.QUORUM_FAILED
    assert result.outcomes[0].error_type == "ResponseValidationError"


@pytest.mark.asyncio
async def test_invalid_responder_return_isolated_as_error() -> None:
    async def invalid(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        return "yes"  # type: ignore[return-value]

    engine = ConsensusEngine(
        [Participant("invalid", invalid)],
        config=ConsensusConfig(min_successful=1),
    )

    result = await engine.run("review")

    assert result.status is ConsensusStatus.QUORUM_FAILED
    assert result.outcomes[0].error_type == "ResponseValidationError"


@pytest.mark.asyncio
async def test_cancelling_run_cancels_participants() -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def waits_forever(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
        return ParticipantResponse(choice="unreachable")

    engine = ConsensusEngine(
        [Participant("slow", waits_forever)],
        config=ConsensusConfig(min_successful=1),
    )
    task = asyncio.create_task(engine.run("review"))
    await started.wait()

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert cancelled.is_set()


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt", ["", "   "])
async def test_empty_prompt_is_rejected(prompt: str) -> None:
    engine = ConsensusEngine(
        [Participant("one", responder("yes"))],
        config=ConsensusConfig(min_successful=1),
    )

    with pytest.raises(ResponseValidationError, match="prompt"):
        await engine.run(prompt)


@pytest.mark.asyncio
async def test_oversized_prompt_is_rejected_before_calls() -> None:
    engine = ConsensusEngine(
        [Participant("one", responder("yes"))],
        config=ConsensusConfig(min_successful=1, max_prompt_characters=3),
    )

    with pytest.raises(ResponseValidationError, match="prompt"):
        await engine.run("four")


def test_duplicate_participants_are_rejected() -> None:
    with pytest.raises(DuplicateParticipantError, match="duplicate participant"):
        ConsensusEngine(
            [Participant("same", responder("yes")), Participant("same", responder("no"))]
        )


def test_engine_requires_participants_and_respects_participant_cap() -> None:
    with pytest.raises(ConfigurationError, match="at least one"):
        ConsensusEngine([])
    with pytest.raises(ConfigurationError, match="max_participants"):
        ConsensusEngine(
            [Participant("one", responder("yes")), Participant("two", responder("yes"))],
            config=ConsensusConfig(max_participants=1),
        )


def test_engine_normalizer_must_be_callable() -> None:
    with pytest.raises(ConfigurationError, match="normalizer"):
        ConsensusEngine(
            [Participant("one", responder("yes"))],
            config=ConsensusConfig(min_successful=1),
            normalizer=None,  # type: ignore[arg-type]
        )


def test_impossible_quorum_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="min_successful"):
        ConsensusEngine(
            [Participant("one", responder("yes"))],
            config=ConsensusConfig(min_successful=2),
        )


def test_budget_must_allocate_at_least_one_token_each() -> None:
    with pytest.raises(ConfigurationError, match="allocate at least one token"):
        ConsensusEngine(
            [Participant("one", responder("yes")), Participant("two", responder("yes"))],
            config=ConsensusConfig(max_total_output_tokens=1),
        )


def test_static_minimum_vote_count_is_validated() -> None:
    from agent_consensus import evaluate_votes

    with pytest.raises(ConfigurationError, match="min_votes must be at least 1"):
        evaluate_votes([], min_votes=0)


@pytest.mark.asyncio
@pytest.mark.parametrize("normalized", ["", "   "])
async def test_normalizer_contract_is_validated(normalized: str) -> None:
    engine = ConsensusEngine(
        [Participant("one", responder("yes"))],
        config=ConsensusConfig(min_successful=1),
        normalizer=lambda choice: normalized,
    )

    with pytest.raises(ResponseValidationError, match="normalizer"):
        await engine.run("review")


@pytest.mark.asyncio
async def test_normalizer_output_size_is_bounded() -> None:
    engine = ConsensusEngine(
        [Participant("one", responder("yes"))],
        config=ConsensusConfig(min_successful=1),
        normalizer=lambda choice: "x" * 257,
    )

    with pytest.raises(ResponseValidationError, match="normalizer output"):
        await engine.run("review")
