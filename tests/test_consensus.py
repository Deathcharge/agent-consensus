"""Tests for deterministic vote evaluation and public models."""

import json
from itertools import permutations

import pytest

from agent_consensus import (
    ConfigurationError,
    ConsensusConfig,
    ConsensusStatus,
    DuplicateParticipantError,
    Participant,
    ParticipantResponse,
    ResponseValidationError,
    Vote,
    evaluate_votes,
    normalize_choice,
)


def test_evaluate_votes_reaches_normalized_supermajority() -> None:
    result = evaluate_votes(
        [
            Vote("reviewer-a", "APPROVE"),
            Vote("reviewer-b", " approve "),
            Vote("reviewer-c", "reject"),
        ]
    )

    assert result.status is ConsensusStatus.AGREED
    assert result.choice == "APPROVE"
    assert result.agreement == pytest.approx(2 / 3)
    assert result.tallies[0].normalized_choice == "approve"
    assert result.tallies[0].participants == ("reviewer-a", "reviewer-b")


def test_evaluate_votes_returns_no_consensus_for_tie() -> None:
    result = evaluate_votes(
        [Vote("a", "approve"), Vote("b", "reject")],
        threshold=0.5,
        min_votes=2,
    )

    assert result.status is ConsensusStatus.NO_CONSENSUS
    assert result.choice is None
    assert result.agreement == 0.5


def test_evaluate_votes_reports_quorum_failure() -> None:
    result = evaluate_votes([], min_votes=1)

    assert result.status is ConsensusStatus.QUORUM_FAILED
    assert result.total_count == 0
    assert result.tallies == ()


def test_evaluate_votes_respects_weights() -> None:
    result = evaluate_votes(
        [Vote("owner", "ship", weight=3), Vote("reviewer", "hold")],
        threshold=0.75,
        min_votes=2,
    )

    assert result.agreed
    assert result.choice == "ship"
    assert result.agreement == 0.75
    assert result.total_weight == 4


@pytest.mark.parametrize("weights", [(1e-15, 1.0, 0.1), (0.1, 0.2, 0.7999999999999999)])
def test_fractional_unanimity_is_exactly_one_in_every_order(weights: tuple[float, ...]) -> None:
    for ordering in permutations(weights):
        result = evaluate_votes(
            [Vote(str(index), "approve", weight) for index, weight in enumerate(ordering)],
            threshold=1.0,
        )
        assert result.agreed
        assert result.agreement == 1.0
        assert result.successful_weight == result.total_weight == result.tallies[0].weight


def test_aggregate_weight_overflow_is_a_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="total participant weight"):
        evaluate_votes([Vote("a", "approve", 1e308), Vote("b", "approve", 1e308)])


def test_evaluate_votes_supports_explicit_custom_normalization() -> None:
    result = evaluate_votes(
        [Vote("a", "yes: safe"), Vote("b", "yes: documented")],
        normalizer=lambda choice: choice.split(":", maxsplit=1)[0],
        min_votes=2,
    )

    assert result.agreed
    assert result.tallies[0].normalized_choice == "yes"


def test_duplicate_voter_names_are_rejected() -> None:
    with pytest.raises(DuplicateParticipantError, match="duplicate participant"):
        evaluate_votes([Vote("same", "yes"), Vote("same", "no")])


def test_static_normalizer_must_be_callable() -> None:
    with pytest.raises(ConfigurationError, match="normalizer"):
        evaluate_votes([Vote("a", "yes")], normalizer=None)  # type: ignore[arg-type]


@pytest.mark.parametrize("threshold", [0, -0.1, 1.1, float("inf")])
def test_invalid_threshold_is_rejected(threshold: float) -> None:
    with pytest.raises(ConfigurationError, match="threshold"):
        evaluate_votes([], threshold=threshold)


@pytest.mark.parametrize("choice", ["", "   "])
def test_empty_choice_is_rejected(choice: str) -> None:
    with pytest.raises(ResponseValidationError, match="choice"):
        ParticipantResponse(choice=choice)


def test_response_shape_limits_are_enforced() -> None:
    with pytest.raises(ResponseValidationError, match="choice cannot exceed"):
        ParticipantResponse(choice="x" * 257)
    with pytest.raises(ResponseValidationError, match="content"):
        ParticipantResponse(choice="yes", content=123)  # type: ignore[arg-type]
    with pytest.raises(ResponseValidationError, match="metadata"):
        ParticipantResponse(choice="yes", metadata=[])  # type: ignore[arg-type]


def test_response_usage_fields_are_validated() -> None:
    with pytest.raises(ResponseValidationError, match="confidence"):
        ParticipantResponse(choice="yes", confidence=1.1)
    with pytest.raises(ResponseValidationError, match="tokens_used"):
        ParticipantResponse(choice="yes", tokens_used=-1)
    with pytest.raises(ResponseValidationError, match="tokens_used"):
        ParticipantResponse(choice="yes", tokens_used=True)


def test_response_defensively_copies_metadata() -> None:
    metadata = {"source": "local"}
    response = ParticipantResponse(choice="yes", metadata=metadata)
    metadata["source"] = "changed"

    assert response.metadata["source"] == "local"


def test_response_hash_ignores_unhashable_metadata() -> None:
    first = ParticipantResponse(choice="yes", metadata={"trace": ["local"]})
    same_vote = ParticipantResponse(choice="yes", metadata={"trace": ["other"]})

    assert hash(first) == hash(same_vote)


def test_participant_configuration_is_validated() -> None:
    async def valid(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        return ParticipantResponse(choice="yes")

    with pytest.raises(ConfigurationError, match="name"):
        Participant("", valid)
    with pytest.raises(ConfigurationError, match="name cannot exceed"):
        Participant("x" * 129, valid)
    with pytest.raises(ConfigurationError, match="callable"):
        Participant("invalid", None)  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="weight"):
        Participant("invalid", valid, weight=0)


def test_vote_shape_is_validated() -> None:
    with pytest.raises(ResponseValidationError, match="participant"):
        Vote("", "yes")
    with pytest.raises(ResponseValidationError, match="participant cannot exceed"):
        Vote("x" * 129, "yes")
    with pytest.raises(ResponseValidationError, match="weight"):
        Vote("a", "yes", weight=0)
    assert Vote("  trimmed  ", "yes").participant == "trimmed"


def test_config_rejects_unbounded_or_impossible_values() -> None:
    with pytest.raises(ConfigurationError, match="timeout_seconds"):
        ConsensusConfig(timeout_seconds=0)
    with pytest.raises(ConfigurationError, match="max_concurrency"):
        ConsensusConfig(max_concurrency=0)
    with pytest.raises(ConfigurationError, match="min_successful"):
        ConsensusConfig(min_successful=0)
    with pytest.raises(ConfigurationError, match="integer"):
        ConsensusConfig(min_successful=True)


@pytest.mark.parametrize(
    "field_name",
    [
        "max_concurrency",
        "max_participants",
        "max_prompt_characters",
        "max_response_characters",
        "max_output_tokens_per_participant",
        "max_total_output_tokens",
    ],
)
def test_config_rejects_non_positive_limits(field_name: str) -> None:
    with pytest.raises(ConfigurationError, match=field_name):
        ConsensusConfig(**{field_name: 0})


def test_normalize_choice_only_changes_case_and_whitespace() -> None:
    assert normalize_choice("  Needs   Review ") == "needs review"
    assert normalize_choice("yes!") != normalize_choice("yes")
    with pytest.raises(ResponseValidationError, match="normalized choice"):
        normalize_choice("   ")


def test_result_is_json_serializable() -> None:
    result = evaluate_votes([Vote("a", "yes")])

    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"status": "agreed"' in encoded
    assert '"participant": "a"' in encoded


def test_response_is_json_serializable_with_json_metadata() -> None:
    response = ParticipantResponse(
        choice="yes",
        metadata={"trace_id": "local-1", "labels": ["safe"]},
    )

    encoded = json.dumps(response.to_dict(), sort_keys=True)
    assert '"trace_id": "local-1"' in encoded
    assert '"labels": ["safe"]' in encoded
