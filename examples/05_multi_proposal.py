"""Evaluate several independent proposals without shared hidden state."""

from agent_consensus import Vote, evaluate_votes

proposals = {
    "release-1": [Vote("a", "ship"), Vote("b", "ship"), Vote("c", "hold")],
    "release-2": [Vote("a", "ship"), Vote("b", "hold"), Vote("c", "hold")],
    "release-3": [Vote("a", "ship"), Vote("b", "hold")],
}

for proposal_id, votes in proposals.items():
    result = evaluate_votes(votes)
    print(f"{proposal_id}: {result.status.value} ({result.choice})")
