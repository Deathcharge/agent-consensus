"""Verify a wheel's public API with no checkout imports or third-party test tools.

Run with the wheel environment's Python: python -I scripts/check_installed.py.
This is a local consumer simulation, not evidence of external production adoption.
"""

from __future__ import annotations

import json
import sys
import unittest
from importlib.metadata import distribution
from pathlib import Path

import agent_consensus
from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    DecisionPolicy,
    DecisionStatus,
    Participant,
    ParticipantResponse,
    Vote,
    evaluate_decision,
    evaluate_votes,
)


class InstalledWheelTests(unittest.IsolatedAsyncioTestCase):
    def test_import_and_distribution_shape(self) -> None:
        self.assertTrue(sys.flags.isolated, "Invoke this check with Python -I")
        package_path = Path(agent_consensus.__file__).resolve()
        self.assertTrue(package_path.is_relative_to(Path(sys.prefix).resolve()), package_path)
        installed = distribution("agent-consensus")
        self.assertEqual(agent_consensus.__version__, installed.version)
        self.assertEqual(
            package_path, Path(installed.locate_file("agent_consensus/__init__.py")).resolve()
        )
        paths = {str(path).replace("\\", "/") for path in installed.files or ()}
        self.assertIn("agent_consensus/py.typed", paths)
        self.assertFalse(any(path.startswith("tests/") for path in paths))
        for filename in ("LICENSE", "NOTICE", "TRADEMARKS.md"):
            self.assertTrue(any(path.endswith(f".dist-info/licenses/{filename}") for path in paths))
        # Optional contributor requirements are allowed; runtime requirements are not.
        for requirement in installed.requires or ():
            self.assertEqual(requirement.partition(";")[2].strip(), 'extra == "dev"')

    def test_decimal_policy_boundary(self) -> None:
        for weight, minimum in ((1e12, 1e12 + 0.5), (1e-15, 2e-15)):
            with self.subTest(weight=weight):
                result = evaluate_votes([Vote("reviewer", "approve", weight)])
                self.assertFalse(
                    evaluate_decision(result, DecisionPolicy(min_successful_weight=minimum)).passed
                )
        result = evaluate_votes([Vote("a", "approve", 0.1), Vote("b", "approve", 0.7)])
        self.assertTrue(evaluate_decision(result, DecisionPolicy(min_successful_weight=0.8)).passed)

    async def test_release_consumer_enforces_every_verdict(self) -> None:
        # Consumer-owned contract v1: source decisions must be explicit and closed-vocabulary.
        cases = (
            ("approve", DecisionStatus.PASSED, True),
            ("reject", DecisionStatus.BLOCKED, False),
            ("unknown", DecisionStatus.INDETERMINATE, False),
            (None, DecisionStatus.INDETERMINATE, False),
        )
        policy = DecisionPolicy(
            policy_id="consumer/release-v1",
            allowed_choices={"approve", "reject"},
            veto_choices={"reject"},
            required_participants={"security", "reliability"},
            min_successful_weight=2,
        )
        for security_choice, expected, should_act in cases:
            with self.subTest(security_choice=security_choice):

                async def security(
                    prompt: str, *, max_tokens: int, choice: str | None = security_choice
                ) -> ParticipantResponse:
                    if choice is None:
                        raise RuntimeError("private source failure detail")
                    return ParticipantResponse(
                        choice=choice,
                        content="private review detail",
                        metadata={"request_id": "release-184", "private": "private source detail"},
                    )

                async def reliability(prompt: str, *, max_tokens: int) -> ParticipantResponse:
                    return ParticipantResponse(choice="approve")

                consensus = await ConsensusEngine(
                    [Participant("security", security), Participant("reliability", reliability)],
                    config=ConsensusConfig(min_successful=2, timeout_seconds=1),
                ).run("private release request")
                verdict = evaluate_decision(consensus, policy)
                self.assertEqual(verdict.status, expected)

                # The consumer owns both the enforcement point and audit allowlist.
                protected_actions: list[str] = []
                if verdict.status is DecisionStatus.PASSED:
                    protected_actions.append("release-184")
                self.assertEqual(bool(protected_actions), should_act)
                audit_record = {
                    "contract_version": 1,
                    "request_id": "release-184",
                    "library_version": agent_consensus.__version__,
                    "policy_digest": verdict.policy.digest,
                    "status": verdict.status.value,
                    "reasons": [reason.value for reason in verdict.reasons],
                }
                self.assertNotIn("private", json.dumps(audit_record))
                self.assertEqual(json.loads(json.dumps(audit_record))["status"], expected.value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
