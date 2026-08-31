"""Maintain optional contract pins without importing or installing the producer."""

import json
import re
from pathlib import Path

import agent_consensus

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "integrations" / "policy_engine"
CONTRACT = json.loads(
    (CONSUMER / "consensus_policy_consumer" / "contract-v1.json").read_text(encoding="utf-8")
)


def test_consumer_contract_and_package_versions_stay_aligned() -> None:
    manifest = (CONSUMER / "pyproject.toml").read_text(encoding="utf-8")
    assert CONTRACT["contract_version"] == 1
    assert CONTRACT["consensus"]["version"] == agent_consensus.__version__
    for name in ("producer", "consensus"):
        spec = CONTRACT[name]
        assert f'"{spec["distribution"]}=={spec["version"]}"' in manifest
    assert '"Private :: Do Not Upload"' in manifest
    assert re.fullmatch(r"[0-9a-f]{32}", CONTRACT["expected_policy_digest"])


def test_consumer_ci_uses_the_reviewed_producer_revision() -> None:
    revision = CONTRACT["producer"]["revision"]
    assert re.fullmatch(r"[0-9a-f]{40}", revision)
    workflow = (ROOT / ".github" / "workflows" / "policy-engine-consumer.yml").read_text(
        encoding="utf-8"
    )
    assert f"ref: {revision}" in workflow
    assert "repository: Deathcharge/policy-engine" in workflow


def test_versioned_fixture_covers_all_enforcement_dispositions() -> None:
    assert {case["status"] for case in CONTRACT["cases"]} == {"passed", "blocked", "indeterminate"}
    for case in CONTRACT["cases"]:
        assert case["executed"] is (case["status"] == "passed")
