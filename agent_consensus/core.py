"""Deterministic vote evaluation and bounded asynchronous fan-out."""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Iterable
from dataclasses import dataclass

from .errors import (
    ConfigurationError,
    DuplicateParticipantError,
    ResponseValidationError,
)
from .models import (
    MAX_CHOICE_CHARACTERS,
    ChoiceNormalizer,
    ChoiceTally,
    ConsensusConfig,
    ConsensusResult,
    ConsensusStatus,
    Participant,
    ParticipantOutcome,
    ParticipantResponse,
    ResponseStatus,
    Vote,
    _validate_decision_settings,
)


def normalize_choice(choice: str) -> str:
    """Normalize casing and whitespace without guessing semantic equivalence."""
    normalized = " ".join(choice.split()).casefold()
    if not normalized:
        raise ResponseValidationError("normalized choice cannot be empty")
    return normalized


@dataclass
class _MutableTally:
    """Mutable accumulator used only while building an immutable result."""

    choice: str
    normalized_choice: str
    weights: list[float]
    participants: list[str]


def _validate_unique_names(names: Iterable[str]) -> None:
    """Reject ambiguous participant identities before evaluating votes."""
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise DuplicateParticipantError(f"duplicate participant name: {name!r}")
        seen.add(name)


def _sum_weights(weights: Iterable[float]) -> float:
    """Use the same accurate accumulation for totals and their positive subsets."""
    try:
        return math.fsum(weights)
    except OverflowError as error:
        raise ConfigurationError("total participant weight must be finite") from error


def _build_result(
    outcomes: tuple[ParticipantOutcome, ...],
    *,
    threshold: float,
    min_successful: int,
    normalizer: ChoiceNormalizer,
    duration_ms: float,
) -> ConsensusResult:
    """Build a deterministic immutable result from participant outcomes."""
    total_weight = _sum_weights(outcome.weight for outcome in outcomes)
    tallies_by_key: dict[str, _MutableTally] = {}
    successful = tuple(
        outcome
        for outcome in outcomes
        if outcome.status is ResponseStatus.SUCCESS and outcome.response is not None
    )

    for outcome in successful:
        response = outcome.response
        assert response is not None
        normalized = normalizer(response.choice)
        if not isinstance(normalized, str) or not normalized.strip():
            raise ResponseValidationError("choice normalizer must return a non-empty string")
        if len(normalized) > MAX_CHOICE_CHARACTERS:
            raise ResponseValidationError(
                f"choice normalizer output cannot exceed {MAX_CHOICE_CHARACTERS} characters"
            )
        tally = tallies_by_key.get(normalized)
        if tally is None:
            tally = _MutableTally(
                choice=response.choice,
                normalized_choice=normalized,
                weights=[],
                participants=[],
            )
            tallies_by_key[normalized] = tally
        tally.weights.append(outcome.weight)
        tally.participants.append(outcome.participant)

    tallies = tuple(
        sorted(
            (
                ChoiceTally(
                    choice=tally.choice,
                    normalized_choice=tally.normalized_choice,
                    weight=_sum_weights(tally.weights),
                    vote_count=len(tally.participants),
                    participants=tuple(tally.participants),
                )
                for tally in tallies_by_key.values()
            ),
            key=lambda item: (-item.weight, item.normalized_choice),
        )
    )

    successful_weight = _sum_weights(outcome.weight for outcome in successful)
    quorum_reached = len(successful) >= min_successful
    leading_weight = tallies[0].weight if tallies else 0.0
    agreement = leading_weight / total_weight if total_weight else 0.0
    tied = len(tallies) > 1 and math.isclose(
        tallies[0].weight,
        tallies[1].weight,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )

    if not quorum_reached:
        status = ConsensusStatus.QUORUM_FAILED
        choice = None
    elif not tied and tallies and agreement >= threshold:
        status = ConsensusStatus.AGREED
        choice = tallies[0].choice
    else:
        status = ConsensusStatus.NO_CONSENSUS
        choice = None

    token_reports = [
        outcome.response.tokens_used for outcome in successful if outcome.response is not None
    ]
    return ConsensusResult(
        status=status,
        choice=choice,
        agreement=agreement,
        quorum_reached=quorum_reached,
        successful_count=len(successful),
        total_count=len(outcomes),
        successful_weight=successful_weight,
        total_weight=total_weight,
        threshold=threshold,
        min_successful=min_successful,
        reported_tokens_used=sum(value for value in token_reports if value is not None),
        token_usage_complete=bool(successful) and all(value is not None for value in token_reports),
        duration_ms=duration_ms,
        tallies=tallies,
        outcomes=outcomes,
    )


def evaluate_votes(
    votes: Iterable[Vote],
    *,
    threshold: float = 2 / 3,
    min_votes: int = 1,
    normalizer: ChoiceNormalizer = normalize_choice,
) -> ConsensusResult:
    """Evaluate pre-collected votes with deterministic weighted tallying.

    Failed participants are not representable in this synchronous helper. Use
    :class:`ConsensusEngine` when participant execution and failures matter.
    """
    _validate_decision_settings(threshold, min_votes, quorum_field="min_votes")
    if not callable(normalizer):
        raise ConfigurationError("normalizer must be callable")
    collected = tuple(votes)
    _validate_unique_names(vote.participant for vote in collected)
    outcomes = tuple(
        ParticipantOutcome(
            participant=vote.participant,
            status=ResponseStatus.SUCCESS,
            weight=vote.weight,
            duration_ms=0.0,
            requested_max_tokens=0,
            response=ParticipantResponse(choice=vote.choice),
        )
        for vote in collected
    )
    return _build_result(
        outcomes,
        threshold=threshold,
        min_successful=min_votes,
        normalizer=normalizer,
        duration_ms=0.0,
    )


class ConsensusEngine:
    """Query independent participants concurrently and evaluate their choices.

    Participant failures count against the agreement denominator. This prevents
    a small surviving subset from appearing more representative than it is.
    ``min_successful`` independently controls quorum.
    """

    def __init__(
        self,
        participants: Iterable[Participant],
        *,
        config: ConsensusConfig | None = None,
        normalizer: ChoiceNormalizer = normalize_choice,
    ) -> None:
        self.participants = tuple(participants)
        self.config = config or ConsensusConfig()
        self.normalizer = normalizer

        if not callable(self.normalizer):
            raise ConfigurationError("normalizer must be callable")
        if not self.participants:
            raise ConfigurationError("at least one participant is required")
        if len(self.participants) > self.config.max_participants:
            raise ConfigurationError(
                f"participant count exceeds max_participants={self.config.max_participants}"
            )
        if self.config.min_successful > len(self.participants):
            raise ConfigurationError("min_successful cannot exceed the number of participants")
        _validate_unique_names(participant.name for participant in self.participants)
        _sum_weights(participant.weight for participant in self.participants)
        self._allocated_tokens = min(
            self.config.max_output_tokens_per_participant,
            self.config.max_total_output_tokens // len(self.participants),
        )
        if self._allocated_tokens < 1:
            raise ConfigurationError(
                "max_total_output_tokens must allocate at least one token per participant"
            )

    async def _query_participant(
        self,
        participant: Participant,
        prompt: str,
        semaphore: asyncio.Semaphore,
    ) -> ParticipantOutcome:
        """Isolate one bounded responder call and sanitize its outcome."""
        started = time.perf_counter()
        try:
            async with semaphore:
                response = await asyncio.wait_for(
                    participant.responder(
                        prompt,
                        max_tokens=self._allocated_tokens,
                    ),
                    timeout=self.config.timeout_seconds,
                )
            if not isinstance(response, ParticipantResponse):
                raise ResponseValidationError("responder must return ParticipantResponse")
            if len(response.content) > self.config.max_response_characters:
                raise ResponseValidationError("response content exceeds configured limit")
            if response.tokens_used is not None and response.tokens_used > self._allocated_tokens:
                raise ResponseValidationError(
                    "reported token use exceeds the participant allocation"
                )
            return ParticipantOutcome(
                participant=participant.name,
                status=ResponseStatus.SUCCESS,
                weight=participant.weight,
                duration_ms=(time.perf_counter() - started) * 1_000,
                requested_max_tokens=self._allocated_tokens,
                response=response,
            )
        except asyncio.CancelledError:
            raise
        except (TimeoutError, asyncio.TimeoutError):
            return ParticipantOutcome(
                participant=participant.name,
                status=ResponseStatus.TIMEOUT,
                weight=participant.weight,
                duration_ms=(time.perf_counter() - started) * 1_000,
                requested_max_tokens=self._allocated_tokens,
                error_type="TimeoutError",
            )
        except Exception as error:  # Participant isolation is intentional.
            return ParticipantOutcome(
                participant=participant.name,
                status=ResponseStatus.ERROR,
                weight=participant.weight,
                duration_ms=(time.perf_counter() - started) * 1_000,
                requested_max_tokens=self._allocated_tokens,
                error_type=type(error).__name__,
            )

    async def run(self, prompt: str) -> ConsensusResult:
        """Run one bounded fan-out and return a complete audit result."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ResponseValidationError("prompt must be a non-empty string")
        if len(prompt) > self.config.max_prompt_characters:
            raise ResponseValidationError("prompt exceeds configured limit")

        started = time.perf_counter()
        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        tasks = tuple(
            asyncio.create_task(self._query_participant(participant, prompt, semaphore))
            for participant in self.participants
        )
        try:
            outcomes = tuple(await asyncio.gather(*tasks))
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        return _build_result(
            outcomes,
            threshold=self.config.threshold,
            min_successful=self.config.min_successful,
            normalizer=self.normalizer,
            duration_ms=(time.perf_counter() - started) * 1_000,
        )
