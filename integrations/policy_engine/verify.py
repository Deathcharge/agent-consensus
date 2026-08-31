"""Run the pinned contract against three installed wheels, not checkout imports."""

from __future__ import annotations

import asyncio
import copy
import json
import sys
import unittest
from dataclasses import replace
from importlib import metadata, resources
from pathlib import Path
from unittest.mock import patch

import consensus_policy_consumer
import policy_engine
from consensus_policy_consumer import SourceContractError, adapt_decision, run_release_gate
from policy_engine import PolicyEngine, Request, parse_request

import agent_consensus

CONTRACT = json.loads(
    resources.files(consensus_policy_consumer)
    .joinpath("contract-v1.json")
    .read_text(encoding="utf-8")
)


class InstalledPolicyConsumerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = PolicyEngine(CONTRACT["policy"])
        self.request = copy.deepcopy(CONTRACT["request"])

    def test_installed_identity_and_golden_contract(self) -> None:
        self.assertTrue(sys.flags.isolated, "Run this verifier with Python -I")
        for module in (agent_consensus, policy_engine, consensus_policy_consumer):
            origin = Path(module.__file__).resolve()
            self.assertTrue(origin.is_relative_to(Path(sys.prefix).resolve()), origin)
        for dependency in ("producer", "consensus"):
            spec = CONTRACT[dependency]
            self.assertEqual(metadata.version(spec["distribution"]), spec["version"])
        self.assertEqual(CONTRACT["contract_version"], consensus_policy_consumer.CONTRACT_VERSION)
        self.assertEqual(self.engine.policy_digest, CONTRACT["expected_policy_digest"])
        self.assertEqual(self.engine.evaluate(self.request).policy_version, 1)

    async def test_versioned_real_producer_cases_enforce_before_action(self) -> None:
        for case in CONTRACT["cases"]:
            with self.subTest(case=case["name"]):
                request = copy.deepcopy(self.request)
                request["context"].update(case.get("context", {}))
                request.update(case.get("request", {}))
                calls: list[Request] = []
                if case["effect"] is not None:
                    self.assertEqual(self.engine.evaluate(request).effect.value, case["effect"])
                result = await run_release_gate(
                    self.engine,
                    request,
                    case["readiness"],
                    calls.append,
                    expected_policy_digest=CONTRACT["expected_policy_digest"],
                )
                self.assertEqual(result.audit["status"], case["status"])
                self.assertEqual(result.executed, case["executed"])
                self.assertEqual(len(calls), int(case["executed"]))
                if calls:
                    self.assertEqual(calls[0], parse_request(request))
                if case["effect"] == "deny":
                    self.assertIn("veto_cast", result.audit["reasons"])
                encoded = json.dumps(result.audit, allow_nan=False)
                for private in (
                    "DO_NOT_RETAIN_PRIVATE_CONTEXT",
                    "private_note",
                    "principal",
                    "context",
                ):
                    self.assertNotIn(private, encoded)
                self.assertEqual(json.loads(encoded)["contract_version"], 1)

    async def test_source_contract_drift_never_invokes_the_operation(self) -> None:
        original = self.engine.evaluate(self.request)
        changes = (
            {"allowed": False},
            {"policy_version": 2},
            {"policy_version": True},
            {"policy_id": "another-policy"},
            {"policy_digest": "0" * 32},
            {"request_id": "another-release"},
            {"effect": "future-value"},
        )
        for change in changes:
            with self.subTest(change=change):
                changed = replace(original, **change)
                with self.assertRaises(SourceContractError):
                    adapt_decision(
                        changed,
                        parse_request(self.request),
                        policy_id=self.engine.policy.id,
                        policy_digest=self.engine.policy_digest,
                    )
                calls: list[Request] = []
                with patch.object(self.engine, "evaluate", return_value=changed):
                    result = await run_release_gate(
                        self.engine,
                        self.request,
                        "ready",
                        calls.append,
                        expected_policy_digest=self.engine.policy_digest,
                    )
                self.assertFalse(result.executed)
                self.assertEqual(calls, [])
                self.assertEqual(result.audit["status"], "indeterminate")
                self.assertEqual(result.audit["source_error_type"], "SourceContractError")

    async def test_changed_live_policy_requires_an_explicit_contract_update(self) -> None:
        changed = copy.deepcopy(CONTRACT["policy"])
        changed["id"] = "new-release-policy"
        calls: list[Request] = []
        result = await run_release_gate(
            PolicyEngine(changed),
            self.request,
            "ready",
            calls.append,
            expected_policy_digest=CONTRACT["expected_policy_digest"],
        )
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])
        self.assertEqual(result.audit["status"], "indeterminate")

    async def test_producer_failure_is_sanitized_and_fails_closed(self) -> None:
        calls: list[Request] = []
        with patch.object(
            self.engine, "evaluate", side_effect=RuntimeError("PRIVATE_FAILURE_DETAIL")
        ):
            result = await run_release_gate(
                self.engine,
                self.request,
                "ready",
                calls.append,
                expected_policy_digest=self.engine.policy_digest,
            )
        self.assertEqual(calls, [])
        self.assertFalse(result.executed)
        self.assertEqual(result.audit["status"], "indeterminate")
        self.assertNotIn("PRIVATE_FAILURE_DETAIL", json.dumps(result.audit))
        self.assertEqual(result.audit["source_error_type"], "RuntimeError")

    async def test_operation_uses_validated_snapshot_not_mutable_original(self) -> None:
        calls: list[Request] = []

        def operation(request: Request) -> None:
            self.request["resource"] = "service:unapproved"
            self.request["context"]["approved"] = False
            self.assertEqual(request.resource, "service:catalog")
            self.assertTrue(request.context["approved"])
            with self.assertRaises(TypeError):
                request.context["approved"] = False  # type: ignore[index]
            calls.append(request)

        result = await run_release_gate(
            self.engine,
            self.request,
            "ready",
            operation,
            expected_policy_digest=self.engine.policy_digest,
        )
        self.assertTrue(result.executed)
        self.assertEqual(len(calls), 1)

    async def test_operation_error_propagates_without_retry(self) -> None:
        calls: list[Request] = []

        def operation(request: Request) -> None:
            calls.append(request)
            raise RuntimeError("operation failed")

        with self.assertRaisesRegex(RuntimeError, "operation failed"):
            await run_release_gate(
                self.engine,
                self.request,
                "ready",
                operation,
                expected_policy_digest=self.engine.policy_digest,
            )
        self.assertEqual(len(calls), 1)

    async def test_request_mutation_during_collection_cannot_rebind_the_action(self) -> None:
        calls: list[Request] = []
        gate = asyncio.create_task(
            run_release_gate(
                self.engine,
                self.request,
                "ready",
                calls.append,
                expected_policy_digest=self.engine.policy_digest,
            )
        )
        await asyncio.sleep(
            0
        )  # Let validation finish and the gate yield to participant collection.
        self.request["resource"] = "service:unapproved"
        self.request["context"]["approved"] = False
        result = await gate
        self.assertTrue(result.executed)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].resource, "service:catalog")
        self.assertTrue(calls[0].context["approved"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
