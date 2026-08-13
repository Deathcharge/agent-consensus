"""Aggregate structured authorization, ethics, and readiness decisions."""

import asyncio
from dataclasses import dataclass

from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    DecisionPolicy,
    Participant,
    ParticipantResponse,
    Responder,
    evaluate_decision,
    normalize_choice,
)

CHOICE_ALIASES = {
    "allow": "approve",
    "deny": "reject",
    "review": "hold",
    "ready": "approve",
}


@dataclass(frozen=True)
class StructuredDecision:
    """Small provider-neutral view of an external decision contract."""

    outcome: str
    policy_id: str
    reference: str


def panel_normalizer(choice: str) -> str:
    """Map explicit external vocabularies into one reviewed gate vocabulary."""
    normalized = normalize_choice(choice)
    return CHOICE_ALIASES.get(normalized, normalized)


def participant_for(decision: StructuredDecision) -> Responder:
    """Adapt one already-computed structured decision without importing its package."""

    async def respond(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        return ParticipantResponse(
            choice=decision.outcome,
            tokens_used=0,
            metadata={
                "policy_id": decision.policy_id,
                "reference": decision.reference,
            },
        )

    return respond


async def main() -> None:
    """Require independent authorization, ethics, and operational readiness."""
    decisions = {
        "authorization": StructuredDecision(
            outcome="allow",
            policy_id="agent-actions/v1",
            reference="request:deploy-184",
        ),
        "ethics": StructuredDecision(
            outcome="allow",
            policy_id="safe-agent-actions/2026-08",
            reference="decision:ethics-771",
        ),
        "operations": StructuredDecision(
            outcome="ready",
            policy_id="launch-readiness/v3",
            reference="release:1.4.0",
        ),
    }
    engine = ConsensusEngine(
        [
            Participant(name, participant_for(decision), weight=2 if name != "operations" else 1)
            for name, decision in decisions.items()
        ],
        config=ConsensusConfig(
            threshold=1.0,
            min_successful=3,
            timeout_seconds=2,
            max_concurrency=3,
            max_output_tokens_per_participant=10,
            max_total_output_tokens=30,
        ),
        normalizer=panel_normalizer,
    )
    consensus = await engine.run("May agent deploy release 1.4.0?")
    policy = DecisionPolicy(
        policy_id="agent-deployment/production-v1",
        pass_choices={"approve"},
        veto_choices={"reject"},
        allowed_choices={"approve", "hold", "reject"},
        required_participants=set(decisions),
        min_successful_weight=5,
    )
    verdict = evaluate_decision(consensus, policy)

    print(f"gate={verdict.status.value} policy_digest={policy.digest[:12]}")
    for outcome in consensus.outcomes:
        assert outcome.response is not None
        print(f"{outcome.participant}: {outcome.response.metadata['reference']}")


if __name__ == "__main__":
    asyncio.run(main())
