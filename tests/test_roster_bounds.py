"""The async engine bounds roster collection, not just downstream execution."""

import pytest

from agent_consensus import (
    ConfigurationError,
    ConsensusConfig,
    ConsensusEngine,
    Participant,
    ParticipantResponse,
)


async def approve(prompt: str, *, max_tokens: int) -> ParticipantResponse:
    return ParticipantResponse("approve", tokens_used=0)


@pytest.mark.parametrize("cap", [1, 3, 32])
def test_oversized_generator_stops_at_the_first_excess_participant(cap):
    consumed = []

    def roster():
        for index in range(cap + 1):
            consumed.append(index)
            yield Participant(str(index), approve)
        raise AssertionError("The engine consumed beyond the first excess participant")

    with pytest.raises(ConfigurationError, match="max_participants"):
        ConsensusEngine(roster(), config=ConsensusConfig(max_participants=cap, min_successful=1))
    assert consumed == list(range(cap + 1))


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [1, 3, 32])
async def test_valid_generator_is_snapshotted_in_order_and_can_run_again(size):
    source = [Participant(str(index), approve) for index in range(size)]
    expected = tuple(source)
    engine = ConsensusEngine(
        (participant for participant in source),
        config=ConsensusConfig(max_participants=size, min_successful=1),
    )
    source.reverse()
    source.append(Participant("later", approve))
    assert engine.participants == expected
    for _ in range(2):
        result = await engine.run("Review release")
        assert result.agreed
        assert [outcome.participant for outcome in result.outcomes] == [str(i) for i in range(size)]


def test_rejection_does_not_drain_or_close_the_caller_owned_iterator():
    roster = (Participant(str(index), approve) for index in range(8))
    with pytest.raises(ConfigurationError, match="max_participants"):
        ConsensusEngine(roster, config=ConsensusConfig(max_participants=3))
    assert next(roster).name == "4"


def test_large_positive_integer_cap_remains_supported_for_finite_rosters():
    participants = (Participant(str(index), approve) for index in range(2))
    engine = ConsensusEngine(participants, config=ConsensusConfig(max_participants=10**400))
    assert len(engine.participants) == 2


def test_roster_errors_before_the_cap_are_not_swallowed():
    def roster():
        yield Participant("a", approve)
        raise RuntimeError("Registry unavailable")

    with pytest.raises(RuntimeError, match="Registry unavailable"):
        ConsensusEngine(roster())


def test_roster_length_hints_are_not_used_to_allocate_unbounded_storage():
    class Roster:
        def __init__(self):
            self.remaining = iter([Participant("a", approve), Participant("b", approve)])

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.remaining)

        def __length_hint__(self):
            raise AssertionError("Do not preallocate from an untrusted length hint")

    assert len(ConsensusEngine(Roster()).participants) == 2
