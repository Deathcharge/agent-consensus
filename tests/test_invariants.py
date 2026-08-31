"""Bounded exhaustive invariants with independent policy and decimal oracles."""

import math
from collections import defaultdict
from decimal import Decimal, localcontext
from itertools import permutations, product

from agent_consensus import (
    DecisionPolicy,
    DecisionReason,
    DecisionStatus,
    Vote,
    evaluate_decision,
    evaluate_votes,
)


def test_policy_precedence_normalization_and_ordering_invariants() -> None:
    """Enumerate 64 panels x 12 policies/quorums x all six input orderings."""
    aliases = {"approve": " APPROVE ", "reject": "Reject", "hold": " HOLD ", "new": " NEW "}
    for choices in product(aliases, repeat=3):
        votes = [
            Vote(name, aliases[choice], weight)
            for name, choice, weight in zip(("a", "b", "c"), choices, (1, 2, 4), strict=True)
        ]
        totals: dict[str, int] = defaultdict(int)
        for choice, weight in zip(choices, (1, 2, 4), strict=True):
            totals[choice] += weight
        winner = max(totals, key=lambda choice: totals[choice])
        for minimum, missing_required, quorum in product((0, 7, 8), (False, True), (1, 4)):
            policy = DecisionPolicy(
                veto_choices={"reject"},
                allowed_choices={"approve", "reject", "hold"},
                required_participants={"absent"} if missing_required else (),
                min_successful_weight=minimum,
            )
            # Independent integer oracle: quorum, then a strict weighted majority.
            agreed = quorum <= 3 and totals[winner] * 2 > 7
            blocked = "reject" in choices or (agreed and winner != "approve")
            incomplete = missing_required or minimum > 7 or "new" in choices or not agreed
            expected = (
                DecisionStatus.BLOCKED
                if blocked
                else DecisionStatus.INDETERMINATE
                if incomplete
                else DecisionStatus.PASSED
            )
            reference = None
            for ordering in permutations(votes):
                verdict = evaluate_decision(
                    evaluate_votes(ordering, threshold=0.5, min_votes=quorum), policy
                )
                assert verdict.status is expected, (choices, minimum, missing_required, quorum)
                assert (DecisionReason.POLICY_SATISFIED in verdict.reasons) is verdict.passed
                semantic_result = (
                    verdict.status,
                    verdict.reasons,
                    verdict.normalized_choice,
                    verdict.veto_participants,
                    verdict.unavailable_required_participants,
                    verdict.unexpected_choices,
                )
                if reference is None:
                    reference = semantic_result
                assert semantic_result == reference


def test_successful_weight_matches_independent_decimal_oracle() -> None:
    """512 panels x four minima, using Decimal rather than the implementation's Fraction."""
    weights = (5e-324, 1e-15, 0.1, 0.2, 0.7, 0.7999999999999999, 1.0, 1e12)
    with localcontext() as context:
        context.prec = 1000  # Exact for this bounded exponent/coefficient space.
        for panel in product(weights, repeat=3):
            consensus = evaluate_votes(
                [Vote(str(index), "approve", weight) for index, weight in enumerate(panel)]
            )
            assert consensus.agreement == 1.0
            total = sum((Decimal(str(weight)) for weight in panel), Decimal(0))
            nearest = float(total)
            for minimum in (
                0.0,
                math.nextafter(nearest, 0.0),
                nearest,
                math.nextafter(nearest, math.inf),
            ):
                verdict = evaluate_decision(
                    consensus, DecisionPolicy(min_successful_weight=minimum)
                )
                assert verdict.passed is (total >= Decimal(str(minimum))), (panel, minimum)


def test_strengthening_policy_cannot_create_a_pass() -> None:
    """All 64 panels retain a fail-closed result when any availability rule tightens."""
    for choices in product(("approve", "reject", "hold", "new"), repeat=3):
        consensus = evaluate_votes(
            [Vote(str(index), choice) for index, choice in enumerate(choices)]
        )
        baseline = evaluate_decision(consensus, DecisionPolicy(veto_choices={"reject"}))
        for policy in (
            DecisionPolicy(veto_choices={"reject", "hold"}),
            DecisionPolicy(veto_choices={"reject"}, required_participants={"absent"}),
            DecisionPolicy(veto_choices={"reject"}, min_successful_weight=4),
            DecisionPolicy(veto_choices={"reject"}, allowed_choices={"approve", "reject"}),
        ):
            stricter = evaluate_decision(consensus, policy)
            assert not stricter.passed or baseline.passed
