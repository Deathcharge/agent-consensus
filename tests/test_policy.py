"""Tests for fail-closed operational decision policies."""

import json
from collections.abc import Callable
from dataclasses import replace

import pytest

from agent_consensus import (
    ConfigurationError,
    ConsensusResult,
    ConsensusStatus,
    DecisionInputError,
    DecisionPolicy,
    DecisionReason,
    DecisionStatus,
    Vote,
    evaluate_decision,
    evaluate_votes,
)


def test_approved_consensus_passes_complete_policy() -> None:
    consensus = evaluate_votes(
        [Vote("security", "APPROVE", 2), Vote("reliability", " approve ")],
        min_votes=2,
    )
    policy = DecisionPolicy(
        policy_id="release/production-v1",
        pass_choices={"approve"},
        veto_choices={"reject"},
        allowed_choices={"approve", "reject"},
        required_participants={"security", "reliability"},
        min_successful_weight=3,
    )

    verdict = evaluate_decision(consensus, policy)

    assert verdict.passed
    assert verdict.status is DecisionStatus.PASSED
    assert verdict.reasons == (DecisionReason.POLICY_SATISFIED,)
    assert verdict.normalized_choice == "approve"
    assert len(verdict.policy.digest) == 64


def test_minority_veto_blocks_an_otherwise_agreed_choice() -> None:
    consensus = evaluate_votes(
        [Vote("release", "approve", 3), Vote("security", "reject")],
        threshold=0.75,
        min_votes=2,
    )

    verdict = evaluate_decision(
        consensus,
        DecisionPolicy(pass_choices={"approve"}, veto_choices={"reject"}),
    )

    assert consensus.agreed
    assert verdict.status is DecisionStatus.BLOCKED
    assert verdict.reasons == (DecisionReason.VETO_CAST,)
    assert verdict.veto_participants == ("security",)


def test_blocking_evidence_precedes_incomplete_evidence() -> None:
    consensus = evaluate_votes([Vote("security", "reject")], min_votes=2)
    policy = DecisionPolicy(
        pass_choices={"approve"},
        veto_choices={"reject"},
        required_participants={"security", "reliability"},
        min_successful_weight=2,
    )

    verdict = evaluate_decision(consensus, policy)

    assert verdict.status is DecisionStatus.BLOCKED
    assert verdict.reasons == (
        DecisionReason.VETO_CAST,
        DecisionReason.REQUIRED_PARTICIPANT_UNAVAILABLE,
        DecisionReason.SUCCESSFUL_WEIGHT_BELOW_MINIMUM,
        DecisionReason.QUORUM_FAILED,
    )


def test_agreed_non_pass_choice_blocks_without_a_veto_rule() -> None:
    consensus = evaluate_votes([Vote("a", "hold"), Vote("b", "hold")], min_votes=2)

    verdict = evaluate_decision(consensus, DecisionPolicy(pass_choices={"approve"}))

    assert verdict.status is DecisionStatus.BLOCKED
    assert verdict.reasons == (DecisionReason.WINNING_CHOICE_NOT_PERMITTED,)


def test_missing_required_participant_is_indeterminate() -> None:
    consensus = evaluate_votes([Vote("release", "approve")])

    verdict = evaluate_decision(
        consensus,
        DecisionPolicy(required_participants={" release ", "security"}),
    )

    assert verdict.status is DecisionStatus.INDETERMINATE
    assert verdict.unavailable_required_participants == ("security",)
    assert verdict.reasons == (DecisionReason.REQUIRED_PARTICIPANT_UNAVAILABLE,)


def test_insufficient_successful_weight_is_indeterminate() -> None:
    consensus = evaluate_votes([Vote("release", "approve", 2)])

    verdict = evaluate_decision(consensus, DecisionPolicy(min_successful_weight=3))

    assert verdict.status is DecisionStatus.INDETERMINATE
    assert verdict.reasons == (DecisionReason.SUCCESSFUL_WEIGHT_BELOW_MINIMUM,)


def test_successful_weight_boundary_tolerates_floating_point_roundoff() -> None:
    consensus = evaluate_votes(
        [Vote("authorization", "approve", 0.1), Vote("ethics", "approve", 0.7)],
        min_votes=2,
    )

    verdict = evaluate_decision(consensus, DecisionPolicy(min_successful_weight=0.8))

    assert consensus.successful_weight < 0.8
    assert verdict.status is DecisionStatus.PASSED


def test_unexpected_choice_fails_closed_even_with_approved_consensus() -> None:
    consensus = evaluate_votes(
        [Vote("release", "approve", 3), Vote("observer", "abstain")],
        threshold=0.75,
        min_votes=2,
    )

    verdict = evaluate_decision(
        consensus,
        DecisionPolicy(allowed_choices={"approve", "reject"}, veto_choices={"reject"}),
    )

    assert verdict.status is DecisionStatus.INDETERMINATE
    assert verdict.reasons == (DecisionReason.UNEXPECTED_CHOICE,)
    assert verdict.unexpected_choices == ("abstain",)


@pytest.mark.parametrize(
    ("votes", "min_votes", "reason"),
    [
        ([Vote("a", "approve"), Vote("b", "reject")], 2, DecisionReason.NO_CONSENSUS),
        ([Vote("a", "approve")], 2, DecisionReason.QUORUM_FAILED),
    ],
)
def test_incomplete_consensus_is_indeterminate(
    votes: list[Vote], min_votes: int, reason: DecisionReason
) -> None:
    consensus = evaluate_votes(votes, threshold=0.5, min_votes=min_votes)

    verdict = evaluate_decision(consensus, DecisionPolicy())

    assert verdict.status is DecisionStatus.INDETERMINATE
    assert verdict.reasons == (reason,)


def test_verdict_is_deterministic_and_json_serializable() -> None:
    consensus = evaluate_votes(
        [Vote("z", "reject"), Vote("a", "reject")],
        min_votes=2,
    )
    verdict = evaluate_decision(
        consensus,
        DecisionPolicy(pass_choices={"approve"}, veto_choices={"reject"}),
    )

    payload = verdict.to_dict()

    assert payload["veto_participants"] == ["a", "z"]
    assert payload["successful_weight"] == 2
    assert payload["policy"] == {
        "schema_version": 1,
        "policy_id": None,
        "pass_choices": ["approve"],
        "veto_choices": ["reject"],
        "allowed_choices": None,
        "required_participants": [],
        "min_successful_weight": 0.0,
        "digest": verdict.policy.digest,
    }
    assert payload["schema_version"] == 1
    assert json.loads(json.dumps(payload))["consensus"]["status"] == "agreed"


def test_policy_defensively_copies_configured_collections() -> None:
    pass_choices = {"approve"}
    required = {"security"}
    policy = DecisionPolicy(pass_choices=pass_choices, required_participants=required)
    pass_choices.add("ship")
    required.add("reliability")

    assert policy.to_dict()["pass_choices"] == ["approve"]
    assert policy.to_dict()["required_participants"] == ["security"]


def test_policy_digest_is_order_independent_and_content_sensitive() -> None:
    first = DecisionPolicy(
        policy_id="action-authorization/v1",
        pass_choices={"approve", "allow"},
        allowed_choices={"allow", "approve", "reject"},
        required_participants={"ethics", "authorization"},
        min_successful_weight=2,
    )
    reordered = DecisionPolicy(
        policy_id="action-authorization/v1",
        pass_choices={"allow", "approve"},
        allowed_choices={"reject", "approve", "allow"},
        required_participants={"authorization", "ethics"},
        min_successful_weight=2.0,
    )
    changed = DecisionPolicy(
        policy_id="action-authorization/v2",
        pass_choices={"allow", "approve"},
        allowed_choices={"reject", "approve", "allow"},
        required_participants={"authorization", "ethics"},
        min_successful_weight=2,
    )

    assert first.digest == reordered.digest
    assert first.digest != changed.digest
    assert first.to_dict()["digest"] == first.digest


def test_policy_digest_has_a_stable_schema_v1_contract() -> None:
    """Protect schema v1; a mismatch requires migration, not replacing this vector."""
    assert (
        DecisionPolicy(policy_id="contract/v1").digest
        == "3db772495f47ab90df60b74b8d2842d3976eaa37b2bca55445121868c27fa71c"
    )


@pytest.mark.parametrize(
    "build_policy",
    [
        lambda: DecisionPolicy(pass_choices=set()),
        lambda: DecisionPolicy(pass_choices="approve"),
        lambda: DecisionPolicy(pass_choices={""}),
        lambda: DecisionPolicy(pass_choices={"x" * 257}),
        lambda: DecisionPolicy(pass_choices={"approve"}, veto_choices={"approve"}),
        lambda: DecisionPolicy(pass_choices={"approve"}, allowed_choices={"reject"}),
        lambda: DecisionPolicy(min_successful_weight=-1),
        lambda: DecisionPolicy(min_successful_weight=float("inf")),
        lambda: DecisionPolicy(min_successful_weight=True),
        lambda: DecisionPolicy(required_participants={1}),
        lambda: DecisionPolicy(policy_id=" contains spaces "),
        lambda: DecisionPolicy(policy_id="x" * 129),
        lambda: DecisionPolicy(policy_id=1),
    ],
)
def test_invalid_policy_is_rejected(build_policy: Callable[[], DecisionPolicy]) -> None:
    with pytest.raises(ConfigurationError):
        build_policy()


def test_evaluate_decision_rejects_wrong_input_types() -> None:
    consensus = evaluate_votes([Vote("a", "approve")])

    with pytest.raises(DecisionInputError, match="consensus"):
        evaluate_decision(None, DecisionPolicy())  # type: ignore[arg-type]
    with pytest.raises(DecisionInputError, match="policy"):
        evaluate_decision(consensus, None)  # type: ignore[arg-type]


def test_evaluate_decision_rejects_inconsistent_agreed_evidence() -> None:
    forged = ConsensusResult(
        status=ConsensusStatus.AGREED,
        choice=None,
        agreement=1.0,
        quorum_reached=False,
        successful_count=0,
        total_count=0,
        successful_weight=0.0,
        total_weight=0.0,
        threshold=2 / 3,
        min_successful=1,
        reported_tokens_used=0,
        token_usage_complete=False,
        duration_ms=0.0,
        tallies=(),
        outcomes=(),
    )

    with pytest.raises(DecisionInputError, match="internally inconsistent"):
        evaluate_decision(forged, DecisionPolicy())


def test_evaluate_decision_rejects_individually_corrupted_builder_fields() -> None:
    valid = evaluate_votes([Vote("security", "approve"), Vote("release", "approve")])
    corrupted = (
        replace(valid, choice=None),
        replace(valid, agreement=0.0),
        replace(valid, quorum_reached=False),
        replace(valid, successful_count=0),
        replace(valid, total_count=0),
        replace(valid, successful_weight=0.0),
        replace(valid, total_weight=0.0),
        replace(valid, tallies=()),
        replace(valid, outcomes=()),
    )

    for candidate in corrupted:
        with pytest.raises(DecisionInputError, match="internally inconsistent"):
            evaluate_decision(candidate, DecisionPolicy())
