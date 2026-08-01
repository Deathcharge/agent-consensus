"""Gather release reviews and enforce a fail-closed operational policy."""

import asyncio

from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    DecisionPolicy,
    Participant,
    ParticipantResponse,
    Responder,
    evaluate_decision,
)


def reviewer(choice: str, rationale: str) -> Responder:
    """Create a deterministic offline participant for this runnable example."""

    async def respond(prompt: str, *, max_tokens: int) -> ParticipantResponse:
        del prompt, max_tokens
        return ParticipantResponse(choice=choice, content=rationale, tokens_used=0)

    return respond


async def main() -> None:
    """Run the complete evidence-collection and decision-gate journey."""
    engine = ConsensusEngine(
        [
            Participant("security", reviewer("approve", "No blocker found."), weight=2),
            Participant("reliability", reviewer("APPROVE", "Rollback tested.")),
            Participant("product", reviewer("hold", "Launch window is optional.")),
        ],
        config=ConsensusConfig(
            threshold=0.5,
            min_successful=3,
            timeout_seconds=2,
            max_concurrency=3,
            max_output_tokens_per_participant=50,
            max_total_output_tokens=150,
        ),
    )
    consensus = await engine.run("Should release 1.4 proceed?")
    policy = DecisionPolicy(
        pass_choices={"approve"},
        veto_choices={"reject"},
        allowed_choices={"approve", "hold", "reject"},
        required_participants={"security", "reliability"},
        min_successful_weight=4,
    )
    verdict = evaluate_decision(consensus, policy)

    print(f"consensus={consensus.status.value} choice={consensus.choice}")
    print(f"gate={verdict.status.value}")
    print(f"reasons={[reason.value for reason in verdict.reasons]}")


if __name__ == "__main__":
    asyncio.run(main())
