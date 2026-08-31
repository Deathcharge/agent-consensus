"""Public numeric boundaries reject non-finite inputs with package-specific errors."""

import math
import sys
from dataclasses import replace

import pytest

from agent_consensus import (
    ConfigurationError,
    ConsensusConfig,
    ConsensusEngine,
    ConsensusStatus,
    DecisionInputError,
    DecisionPolicy,
    Participant,
    ParticipantResponse,
    ResponseStatus,
    ResponseValidationError,
    Vote,
    evaluate_decision,
    evaluate_votes,
)


async def approve(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    return ParticipantResponse("approve")


@pytest.mark.parametrize(
    "invalid",
    [10**400, -(10**400), math.nan, math.inf, -math.inf, True, False, "1"],
    ids=[
        "overflow-positive",
        "overflow-negative",
        "nan",
        "infinity",
        "negative-infinity",
        "true",
        "false",
        "numeric-string",
    ],
)
@pytest.mark.parametrize(
    "construct,error,field",
    [
        (lambda value: ConsensusConfig(threshold=value), ConfigurationError, "threshold"),
        (lambda value: ConsensusConfig(timeout_seconds=value), ConfigurationError, "timeout"),
        (lambda value: evaluate_votes([], threshold=value), ConfigurationError, "threshold"),
        (lambda value: Participant("a", approve, value), ConfigurationError, "weight"),
        (lambda value: Vote("a", "approve", value), ResponseValidationError, "weight"),
        (
            lambda value: ParticipantResponse("approve", confidence=value),
            ResponseValidationError,
            "confidence",
        ),
    ],
    ids=["config-threshold", "timeout", "static-threshold", "participant", "vote", "confidence"],
)
def test_invalid_numeric_inputs_raise_the_documented_error(invalid, construct, error, field):
    with pytest.raises(error, match=field):
        construct(invalid)


@pytest.mark.parametrize("invalid", [10**400, -(10**400)], ids=["huge-positive", "huge-negative"])
@pytest.mark.parametrize(
    "field", ["agreement", "successful_weight", "total_weight", "threshold", "outcome", "tally"]
)
def test_unrepresentable_evidence_raises_decision_input_error(invalid, field):
    result = evaluate_votes([Vote("a", "approve")])
    if field == "outcome":
        result = replace(result, outcomes=(replace(result.outcomes[0], weight=invalid),))
    elif field == "tally":
        result = replace(result, tallies=(replace(result.tallies[0], weight=invalid),))
    else:
        result = replace(result, **{field: invalid})
    with pytest.raises(DecisionInputError, match="internally inconsistent"):
        evaluate_decision(result, DecisionPolicy())


@pytest.mark.parametrize(
    "weight",
    [1, 2**53 + 1, 10**308, sys.float_info.max, math.ulp(0.0)],
    ids=["integer", "inexact-float-integer", "large-integer", "largest-float", "smallest-float"],
)
def test_finite_weight_values_are_preserved_not_coerced(weight):
    participant = Participant("a", approve, weight)
    vote = Vote("a", "approve", weight)
    assert participant.weight is weight
    assert vote.weight is weight
    result = evaluate_votes([vote])
    assert result.outcomes[0].weight is weight
    assert result.agreement == 1
    assert evaluate_decision(result, DecisionPolicy()).passed


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [10**400, -(10**400)], ids=["huge-positive", "huge-negative"])
async def test_oversized_adapter_confidence_is_isolated_as_response_validation(invalid):
    async def invalid_confidence(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        return ParticipantResponse("approve", confidence=invalid)

    result = await ConsensusEngine(
        [Participant("healthy", approve), Participant("invalid", invalid_confidence)]
    ).run("Review release")
    assert result.status is ConsensusStatus.QUORUM_FAILED
    assert result.outcomes[0].status is ResponseStatus.SUCCESS
    assert result.outcomes[1].status is ResponseStatus.ERROR
    assert result.outcomes[1].error_type == "ResponseValidationError"
    assert result.outcomes[1].response is None
    assert not evaluate_decision(result, DecisionPolicy()).passed
