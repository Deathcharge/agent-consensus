"""Evaluate votes that have already been collected."""

from agent_consensus import Vote, evaluate_votes

votes = [
    Vote("security", "approve"),
    Vote("reliability", "APPROVE"),
    Vote("product", "hold"),
]

result = evaluate_votes(votes)
print(f"Status: {result.status.value}")
print(f"Choice: {result.choice}")
print(f"Agreement: {result.agreement:.1%}")
