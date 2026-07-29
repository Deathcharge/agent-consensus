"""Make participant authority explicit with weighted voting."""

from agent_consensus import Vote, evaluate_votes

votes = [
    Vote("release-owner", "ship", weight=3),
    Vote("reviewer", "hold", weight=1),
]

result = evaluate_votes(votes, threshold=0.75, min_votes=2)
print(f"Status: {result.status.value}")
print(f"Choice: {result.choice}")
for tally in result.tallies:
    print(f"{tally.choice}: weight={tally.weight:g}")
