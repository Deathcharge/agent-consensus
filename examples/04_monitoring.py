"""Serialize an audit result for application-owned monitoring."""

import json

from agent_consensus import Vote, evaluate_votes

result = evaluate_votes([Vote("a", "approve"), Vote("b", "approve"), Vote("c", "hold")])

print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
