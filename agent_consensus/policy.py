"""Fail-closed operational policy evaluation for consensus results."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Any

from .errors import ConfigurationError, DecisionInputError
from .models import (
    MAX_CHOICE_CHARACTERS,
    MAX_NAME_CHARACTERS,
    ConsensusResult,
    ConsensusStatus,
    ResponseStatus,
)

POLICY_SCHEMA_VERSION = 1
VERDICT_SCHEMA_VERSION = 1
_POLICY_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")


class DecisionStatus(str, Enum):
    """Operational disposition after applying a policy to consensus evidence."""

    PASSED = "passed"
    BLOCKED = "blocked"
    INDETERMINATE = "indeterminate"


class DecisionReason(str, Enum):
    """Stable machine-readable explanation for a decision verdict."""

    POLICY_SATISFIED = "policy_satisfied"
    VETO_CAST = "veto_cast"
    WINNING_CHOICE_NOT_PERMITTED = "winning_choice_not_permitted"
    REQUIRED_PARTICIPANT_UNAVAILABLE = "required_participant_unavailable"
    SUCCESSFUL_WEIGHT_BELOW_MINIMUM = "successful_weight_below_minimum"
    UNEXPECTED_CHOICE = "unexpected_choice"
    QUORUM_FAILED = "quorum_failed"
    NO_CONSENSUS = "no_consensus"


_INCOMPLETE_REASONS = frozenset(
    {
        DecisionReason.REQUIRED_PARTICIPANT_UNAVAILABLE,
        DecisionReason.SUCCESSFUL_WEIGHT_BELOW_MINIMUM,
        DecisionReason.UNEXPECTED_CHOICE,
        DecisionReason.QUORUM_FAILED,
        DecisionReason.NO_CONSENSUS,
    }
)


def _freeze_strings(
    values: Collection[str],
    *,
    field_name: str,
    max_characters: int,
    strip: bool,
) -> frozenset[str]:
    """Validate and defensively freeze one configured set of identifiers."""
    if isinstance(values, (str, bytes)) or not isinstance(values, Collection):
        raise ConfigurationError(f"{field_name} must be a collection of strings")

    frozen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ConfigurationError(f"{field_name} must contain only strings")
        canonical = value.strip() if strip else value
        if not canonical:
            raise ConfigurationError(f"{field_name} cannot contain empty strings")
        if len(canonical) > max_characters:
            raise ConfigurationError(
                f"{field_name} values cannot exceed {max_characters} characters"
            )
        frozen.add(canonical)
    return frozenset(frozen)


@dataclass(frozen=True)
class DecisionPolicy:
    """Rules that turn consensus evidence into an operational gate verdict.

    Choice values match ``ChoiceTally.normalized_choice`` exactly. With the
    default consensus normalizer, configure lowercase, whitespace-collapsed
    values such as ``"approve"`` and ``"reject"``.
    """

    policy_id: str | None = None
    pass_choices: Collection[str] = field(default_factory=lambda: frozenset({"approve"}))
    veto_choices: Collection[str] = field(default_factory=frozenset)
    allowed_choices: Collection[str] | None = None
    required_participants: Collection[str] = field(default_factory=frozenset)
    min_successful_weight: float = 0.0

    def __post_init__(self) -> None:
        policy_id = self.policy_id
        if policy_id is not None and (
            not isinstance(policy_id, str) or not _POLICY_ID_PATTERN.fullmatch(policy_id)
        ):
            raise ConfigurationError(
                "policy_id must start with an ASCII alphanumeric character and contain at most "
                "128 ASCII alphanumeric, '.', '_', ':', '/', or '-' characters"
            )
        pass_choices = _freeze_strings(
            self.pass_choices,
            field_name="pass_choices",
            max_characters=MAX_CHOICE_CHARACTERS,
            strip=False,
        )
        if not pass_choices:
            raise ConfigurationError("pass_choices must contain at least one choice")
        veto_choices = _freeze_strings(
            self.veto_choices,
            field_name="veto_choices",
            max_characters=MAX_CHOICE_CHARACTERS,
            strip=False,
        )
        allowed_choices = (
            None
            if self.allowed_choices is None
            else _freeze_strings(
                self.allowed_choices,
                field_name="allowed_choices",
                max_characters=MAX_CHOICE_CHARACTERS,
                strip=False,
            )
        )
        required_participants = _freeze_strings(
            self.required_participants,
            field_name="required_participants",
            max_characters=MAX_NAME_CHARACTERS,
            strip=True,
        )

        if pass_choices & veto_choices:
            raise ConfigurationError("pass_choices and veto_choices must not overlap")
        if allowed_choices is not None and not (pass_choices | veto_choices) <= allowed_choices:
            raise ConfigurationError(
                "allowed_choices must include every configured pass and veto choice"
            )
        if (
            isinstance(self.min_successful_weight, bool)
            or not isinstance(self.min_successful_weight, (int, float))
            or self.min_successful_weight < 0
        ):
            raise ConfigurationError("min_successful_weight must be finite and non-negative")
        try:
            minimum = float(self.min_successful_weight)
        except OverflowError as error:
            raise ConfigurationError("min_successful_weight must be finite") from error
        if not math.isfinite(minimum):
            raise ConfigurationError("min_successful_weight must be finite and non-negative")
        if isinstance(self.min_successful_weight, int) and (
            Fraction(str(minimum)) != self.min_successful_weight
        ):
            raise ConfigurationError(
                "min_successful_weight cannot change decimal value during float normalization"
            )

        object.__setattr__(self, "pass_choices", pass_choices)
        object.__setattr__(self, "veto_choices", veto_choices)
        object.__setattr__(self, "allowed_choices", allowed_choices)
        object.__setattr__(self, "required_participants", required_participants)
        object.__setattr__(self, "min_successful_weight", minimum)

    def _content_dict(self) -> dict[str, Any]:
        """Return the canonical policy content covered by the digest."""
        return {
            "schema_version": POLICY_SCHEMA_VERSION,
            "policy_id": self.policy_id,
            "pass_choices": sorted(self.pass_choices),
            "veto_choices": sorted(self.veto_choices),
            "allowed_choices": (
                None if self.allowed_choices is None else sorted(self.allowed_choices)
            ),
            "required_participants": sorted(self.required_participants),
            "min_successful_weight": self.min_successful_weight,
        }

    @property
    def digest(self) -> str:
        """Return a deterministic SHA-256 digest of the complete policy content."""
        payload = json.dumps(
            self._content_dict(),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible policy snapshot."""
        return {**self._content_dict(), "digest": self.digest}


@dataclass(frozen=True)
class DecisionVerdict:
    """Auditable operational verdict and the consensus evidence behind it."""

    status: DecisionStatus
    reasons: tuple[DecisionReason, ...]
    policy: DecisionPolicy
    consensus: ConsensusResult
    normalized_choice: str | None
    veto_participants: tuple[str, ...]
    unavailable_required_participants: tuple[str, ...]
    unexpected_choices: tuple[str, ...]
    required_successful_weight: float

    @property
    def passed(self) -> bool:
        """Whether the caller may proceed under the configured policy."""
        return self.status is DecisionStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        """Return the verdict and its evidence as a JSON-compatible dictionary."""
        return {
            "schema_version": VERDICT_SCHEMA_VERSION,
            "status": self.status.value,
            "reasons": [reason.value for reason in self.reasons],
            "policy": self.policy.to_dict(),
            "normalized_choice": self.normalized_choice,
            "veto_participants": list(self.veto_participants),
            "unavailable_required_participants": list(self.unavailable_required_participants),
            "unexpected_choices": list(self.unexpected_choices),
            "successful_weight": self.consensus.successful_weight,
            "required_successful_weight": self.required_successful_weight,
            "consensus": self.consensus.to_dict(),
        }


def _is_consensus_evidence_consistent(consensus: ConsensusResult) -> bool:
    """Check the builder invariants relied on by an operational decision gate."""

    if (
        not isinstance(consensus.status, ConsensusStatus)
        or not isinstance(consensus.quorum_reached, bool)
        or isinstance(consensus.successful_count, bool)
        or not isinstance(consensus.successful_count, int)
        or consensus.successful_count < 0
        or isinstance(consensus.total_count, bool)
        or not isinstance(consensus.total_count, int)
        or consensus.total_count < 0
        or isinstance(consensus.min_successful, bool)
        or not isinstance(consensus.min_successful, int)
        or consensus.min_successful < 1
        or (
            consensus.choice is not None
            and (not isinstance(consensus.choice, str) or not consensus.choice.strip())
        )
    ):
        return False

    numeric_fields = (
        consensus.agreement,
        consensus.successful_weight,
        consensus.total_weight,
        consensus.threshold,
    )
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in numeric_fields
    ):
        return False
    if (
        not 0 <= consensus.agreement <= 1
        or consensus.successful_weight < 0
        or consensus.total_weight < 0
        or not 0 < consensus.threshold <= 1
    ):
        return False

    outcome_by_participant = {}
    successful_outcomes = []
    total_weight = 0.0
    for outcome in consensus.outcomes:
        if (
            not isinstance(outcome.participant, str)
            or not outcome.participant
            or outcome.participant in outcome_by_participant
            or not isinstance(outcome.status, ResponseStatus)
            or isinstance(outcome.weight, bool)
            or not isinstance(outcome.weight, (int, float))
            or not math.isfinite(outcome.weight)
            or outcome.weight <= 0
        ):
            return False
        is_successful = outcome.status is ResponseStatus.SUCCESS
        has_response = outcome.response is not None
        if is_successful is not has_response:
            return False
        outcome_by_participant[outcome.participant] = outcome
        total_weight += outcome.weight
        if is_successful:
            successful_outcomes.append(outcome)

    successful_weight = sum(outcome.weight for outcome in successful_outcomes)
    if (
        consensus.total_count != len(consensus.outcomes)
        or consensus.successful_count != len(successful_outcomes)
        or not math.isclose(consensus.total_weight, total_weight, rel_tol=1e-12, abs_tol=1e-12)
        or not math.isclose(
            consensus.successful_weight,
            successful_weight,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
    ):
        return False

    successful_participants = {outcome.participant for outcome in successful_outcomes}
    tallied_participants: list[str] = []
    normalized_choices: set[str] = set()
    for tally in consensus.tallies:
        if (
            not isinstance(tally.choice, str)
            or not tally.choice
            or not isinstance(tally.normalized_choice, str)
            or not tally.normalized_choice
            or tally.normalized_choice in normalized_choices
            or isinstance(tally.vote_count, bool)
            or not isinstance(tally.vote_count, int)
            or tally.vote_count != len(tally.participants)
            or not tally.participants
            or len(set(tally.participants)) != len(tally.participants)
            or isinstance(tally.weight, bool)
            or not isinstance(tally.weight, (int, float))
            or not math.isfinite(tally.weight)
            or tally.weight <= 0
        ):
            return False
        if any(participant not in successful_participants for participant in tally.participants):
            return False
        expected_weight = sum(
            outcome_by_participant[participant].weight for participant in tally.participants
        )
        first_response = outcome_by_participant[tally.participants[0]].response
        if (
            first_response is None
            or tally.choice != first_response.choice
            or not math.isclose(tally.weight, expected_weight, rel_tol=1e-12, abs_tol=1e-12)
        ):
            return False
        normalized_choices.add(tally.normalized_choice)
        tallied_participants.extend(tally.participants)

    if (
        len(set(tallied_participants)) != len(tallied_participants)
        or set(tallied_participants) != successful_participants
        or tuple(sorted(consensus.tallies, key=lambda item: (-item.weight, item.normalized_choice)))
        != consensus.tallies
        or not math.isclose(
            sum(tally.weight for tally in consensus.tallies),
            consensus.successful_weight,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
    ):
        return False

    quorum_reached = consensus.successful_count >= consensus.min_successful
    leading_weight = consensus.tallies[0].weight if consensus.tallies else 0.0
    agreement = leading_weight / consensus.total_weight if consensus.total_weight else 0.0
    tied = len(consensus.tallies) > 1 and math.isclose(
        consensus.tallies[0].weight,
        consensus.tallies[1].weight,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
    if consensus.quorum_reached is not quorum_reached or not math.isclose(
        consensus.agreement, agreement, rel_tol=1e-12, abs_tol=1e-12
    ):
        return False

    if not quorum_reached:
        expected_status = ConsensusStatus.QUORUM_FAILED
        expected_choice = None
    elif consensus.tallies and not tied and agreement >= consensus.threshold:
        expected_status = ConsensusStatus.AGREED
        expected_choice = consensus.tallies[0].choice
    else:
        expected_status = ConsensusStatus.NO_CONSENSUS
        expected_choice = None
    return consensus.status is expected_status and consensus.choice == expected_choice


def evaluate_decision(
    consensus: ConsensusResult,
    policy: DecisionPolicy,
) -> DecisionVerdict:
    """Apply an operational policy without altering consensus arithmetic.

    A veto or an agreed non-pass choice produces ``BLOCKED``. Missing or
    unrecognized evidence produces ``INDETERMINATE``. Only an agreed pass
    choice with every availability and vocabulary rule satisfied produces
    ``PASSED``.
    """
    if not isinstance(consensus, ConsensusResult):
        raise DecisionInputError("consensus must be a ConsensusResult")
    if not isinstance(policy, DecisionPolicy):
        raise DecisionInputError("policy must be a DecisionPolicy")
    if not _is_consensus_evidence_consistent(consensus):
        raise DecisionInputError("consensus evidence is internally inconsistent")

    choice_by_participant = {
        participant: tally.normalized_choice
        for tally in consensus.tallies
        for participant in tally.participants
    }
    successful_participants = {
        outcome.participant
        for outcome in consensus.outcomes
        if outcome.status is ResponseStatus.SUCCESS and outcome.response is not None
    }
    veto_participants = tuple(
        sorted(
            participant
            for participant, choice in choice_by_participant.items()
            if choice in policy.veto_choices
        )
    )
    unavailable_required = tuple(
        sorted(set(policy.required_participants) - successful_participants)
    )
    unexpected_choices = (
        ()
        if policy.allowed_choices is None
        else tuple(
            sorted(
                tally.normalized_choice
                for tally in consensus.tallies
                if tally.normalized_choice not in policy.allowed_choices
            )
        )
    )
    normalized_choice = (
        consensus.tallies[0].normalized_choice
        if consensus.status is ConsensusStatus.AGREED and consensus.tallies
        else None
    )

    reasons: list[DecisionReason] = []
    if veto_participants:
        reasons.append(DecisionReason.VETO_CAST)
    if normalized_choice is not None and normalized_choice not in policy.pass_choices:
        reasons.append(DecisionReason.WINNING_CHOICE_NOT_PERMITTED)
    if unavailable_required:
        reasons.append(DecisionReason.REQUIRED_PARTICIPANT_UNAVAILABLE)
    # Tolerances can forgive missing participants at large or tiny scales. Sum
    # decimal spellings exactly, using outcomes rather than the rounded summary.
    successful_weight = sum(
        (
            Fraction(str(outcome.weight))
            for outcome in consensus.outcomes
            if outcome.status is ResponseStatus.SUCCESS and outcome.response is not None
        ),
        Fraction(),
    )
    if successful_weight < Fraction(str(policy.min_successful_weight)):
        reasons.append(DecisionReason.SUCCESSFUL_WEIGHT_BELOW_MINIMUM)
    if unexpected_choices:
        reasons.append(DecisionReason.UNEXPECTED_CHOICE)
    if consensus.status is ConsensusStatus.QUORUM_FAILED:
        reasons.append(DecisionReason.QUORUM_FAILED)
    elif consensus.status is ConsensusStatus.NO_CONSENSUS:
        reasons.append(DecisionReason.NO_CONSENSUS)

    blocked = bool(veto_participants) or DecisionReason.WINNING_CHOICE_NOT_PERMITTED in reasons
    incomplete = bool(set(reasons) & _INCOMPLETE_REASONS)
    if blocked:
        status = DecisionStatus.BLOCKED
    elif incomplete:
        status = DecisionStatus.INDETERMINATE
    else:
        status = DecisionStatus.PASSED
        reasons.append(DecisionReason.POLICY_SATISFIED)

    return DecisionVerdict(
        status=status,
        reasons=tuple(reasons),
        policy=policy,
        consensus=consensus,
        normalized_choice=normalized_choice,
        veto_participants=veto_participants,
        unavailable_required_participants=unavailable_required,
        unexpected_choices=unexpected_choices,
        required_successful_weight=policy.min_successful_weight,
    )
