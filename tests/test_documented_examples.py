"""Execute explicitly marked, trusted repository examples as a reader would copy them.

This is test-only execution of maintained source, never a loader for external Markdown.
"""

import contextlib
import io
import re
from pathlib import Path

import pytest

from agent_consensus import Vote, evaluate_votes

ROOT = Path(__file__).resolve().parents[1]
GUIDES = [
    (
        "README.md",
        ("collected-votes", "async-consensus", "decision-gate"),
        {"security", "reliability"},
    ),
    (
        "docs/GETTING_STARTED.md",
        (
            "collected-votes",
            "local-adapter",
            "async-consensus",
            "decision-gate",
            "result-states",
        ),
        {"policy-a", "policy-b"},
    ),
]


def snippets(document):
    text = (ROOT / document).read_text(encoding="utf-8")
    matches = re.findall(
        r"<!-- runnable: ([a-z-]+) -->\n```python\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    assert len(matches) == len(dict(matches)), "Duplicate runnable example identifiers"
    assert len(matches) == text.count("```python\n"), "Every Python example needs a runnable marker"
    return dict(matches)


def execute(source, namespace):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source, "<documented-example>", "exec"), namespace)
    return output.getvalue()


@pytest.mark.parametrize("document,identifiers,reviewers", GUIDES)
def test_documented_journey_uses_the_async_evidence(document, identifiers, reviewers):
    examples = snippets(document)
    assert tuple(examples) == identifiers, "Keep the explicit runnable-example contract current"
    namespace = {}
    execute(examples["collected-votes"], namespace)
    collected = namespace["result"]
    output = ""
    for identifier in identifiers[1:]:
        output += execute(examples[identifier], namespace)
    result = namespace["result"]
    assert result is not collected, "The policy must not reuse the earlier static vote example"
    assert {outcome.participant for outcome in result.outcomes} == reviewers
    assert namespace["verdict"].consensus is result
    assert namespace["verdict"].passed
    assert "action=permitted" in output


@pytest.mark.parametrize("document,identifiers,reviewers", GUIDES)
@pytest.mark.parametrize(
    "scenario,status,action",
    [
        ("approved", "passed", "permitted"),
        ("veto", "blocked", "blocked"),
        ("missing-reviewer", "indeterminate", "withheld"),
        ("unknown-choice", "indeterminate", "withheld"),
    ],
)
def test_documented_gate_branches_fail_closed(
    document, identifiers, reviewers, scenario, status, action
):
    examples = snippets(document)
    names = sorted(reviewers)
    votes = [Vote(name, "approve") for name in names]
    namespace = {"result": evaluate_votes(votes)}
    execute(examples["decision-gate"], namespace)
    policy = namespace["policy"]
    if scenario == "veto":
        votes[0] = Vote(names[0], next(iter(policy.veto_choices)))
    elif scenario == "missing-reviewer":
        votes.pop()
    elif scenario == "unknown-choice":
        votes[0] = Vote(names[0], "unexpected-choice")
    namespace["result"] = evaluate_votes(votes)
    output = execute(examples["decision-gate"], namespace)
    verdict = namespace["verdict"]
    assert verdict.consensus is namespace["result"]
    assert verdict.status.value == status
    assert output.startswith(f"action={action}")
    assert ("action=permitted" in output) is (status == "passed")
