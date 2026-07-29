"""Observe ordinary participant failure without hiding it."""

import asyncio

from agent_consensus import (
    ConsensusConfig,
    ConsensusEngine,
    Participant,
    ParticipantResponse,
)


async def approves(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    del prompt, max_tokens
    return ParticipantResponse(choice="approve", content="Checks passed.")


async def unavailable(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    del prompt, max_tokens
    raise RuntimeError("provider unavailable")


async def main() -> None:
    engine = ConsensusEngine(
        [
            Participant("security", approves),
            Participant("reliability", approves),
            Participant("unavailable-reviewer", unavailable),
        ],
        config=ConsensusConfig(min_successful=2),
    )
    result = await engine.run("Should the release proceed?")

    print(f"Status: {result.status.value}")
    print(f"Agreement: {result.agreement:.1%}")
    for outcome in result.outcomes:
        print(f"{outcome.participant}: {outcome.status.value}")


asyncio.run(main())
