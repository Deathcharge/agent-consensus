"""Consumer-owned release gate using the public APIs of two installed packages.

This optional example is not part of the agent_consensus runtime package.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from policy_engine import (
    Decision,
    Effect,
    PolicyEngine,
    Request,
    RequestValidationError,
    parse_request,
)

import agent_consensus
from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    DecisionPolicy,
    DecisionStatus,
    Participant,
    ParticipantResponse,
    evaluate_decision,
    normalize_choice,
)

CONTRACT_VERSION = 1


class SourceContractError(ValueError):
    """A source decision does not satisfy the consumer's reviewed contract."""


@dataclass(frozen=True)
class GateRun:
    """Allowlisted audit record; full requests, contexts and reasons are omitted."""

    executed: bool
    audit: dict[str, Any]


def panel_normalizer(choice: str) -> str:
    normalized = normalize_choice(choice)
    return {"allow": "approve", "deny": "reject", "ready": "approve"}.get(normalized, normalized)


def adapt_decision(
    decision: Decision, request: Request, *, policy_id: str, policy_digest: str
) -> ParticipantResponse:
    """Bind a live decision to the expected request, policy and schema before voting."""
    if (
        (decision.effect is not Effect.ALLOW and decision.effect is not Effect.DENY)
        or decision.allowed is not (decision.effect is Effect.ALLOW)
        or type(decision.policy_version) is not int
        or decision.policy_version != CONTRACT_VERSION
        or decision.policy_id != policy_id
        or decision.policy_digest != policy_digest
        or not request.request_id
        or decision.request_id != request.request_id
    ):
        raise SourceContractError("source decision does not match the reviewed contract")
    return ParticipantResponse(
        choice=decision.effect.value,
        metadata={
            "policy_id": decision.policy_id,
            "policy_version": decision.policy_version,
            "policy_digest": decision.policy_digest,
            "request_id": decision.request_id,
        },
    )


async def run_release_gate(
    engine: PolicyEngine,
    request: Mapping[str, Any],
    readiness: str,
    operation: Callable[[Request], None],
    *,
    expected_policy_digest: str,
) -> GateRun:
    """Evaluate a frozen request, then invoke the host operation only for PASSED.

    The operation receives the same validated immutable request that was evaluated.
    Operation exceptions propagate; no success receipt or automatic retry is fabricated.
    """
    try:
        parsed = parse_request(request)
    except RequestValidationError:
        parsed = None

    async def authorization(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        if parsed is None:
            raise SourceContractError("invalid source request")
        return adapt_decision(
            engine.evaluate(parsed),
            parsed,
            policy_id=engine.policy.id,
            policy_digest=expected_policy_digest,
        )

    async def operations(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        if readiness not in {"ready", "hold"}:
            raise SourceContractError("unrecognized readiness outcome")
        return ParticipantResponse(choice=readiness)

    policy = DecisionPolicy(
        policy_id="consumer/release-v1",
        pass_choices={"approve"},
        veto_choices={"reject"},
        allowed_choices={"approve", "reject", "hold"},
        required_participants={"authorization", "operations"},
        min_successful_weight=4,
    )
    consensus = await ConsensusEngine(
        [Participant("authorization", authorization), Participant("operations", operations, 3)],
        config=ConsensusConfig(min_successful=2, timeout_seconds=1, max_concurrency=2),
        normalizer=panel_normalizer,
    ).run("Evaluate the bound release request")
    verdict = evaluate_decision(consensus, policy)
    executed = False
    if verdict.status is DecisionStatus.PASSED:
        assert parsed is not None
        operation(parsed)
        executed = True

    source = next(
        outcome for outcome in consensus.outcomes if outcome.participant == "authorization"
    )
    return GateRun(
        executed=executed,
        audit={
            "contract_version": CONTRACT_VERSION,
            "library_version": agent_consensus.__version__,
            "request_id": parsed.request_id if parsed is not None else None,
            "policy_digest": policy.digest,
            "status": verdict.status.value,
            "reasons": [reason.value for reason in verdict.reasons],
            "executed": executed,
            "source_status": source.status.value,
            "source_error_type": source.error_type,
            "source": dict(source.response.metadata) if source.response is not None else None,
        },
    )
