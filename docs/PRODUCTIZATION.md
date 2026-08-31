# Productization record

Last updated: 2026-08-31

This is the living audit and release record for `Deathcharge/agent-consensus`.

Current product identity: `agent-consensus`, developed and maintained by Samsarix LLC. Public
contacts are `contact@samsarix.com` for general inquiries and `support@samsarix.com` for support,
security, and conduct reports. Historical Helix names below are retained only where needed to
describe the repository's provenance and the dependencies removed during productization.

## Repository assessment

### Original purpose

The first `main` commit extracted one `multi_ai_consensus.py` module from `helix-unified`. Its intent
was to fan a prompt out to four named AI providers, count outcomes, select a primary response, and
write usage to a Helix-specific state path. Two later documentation commits added a different,
unimplemented API for generic majority voting and agent coordination.

### What worked at baseline

- Git history, an MIT license, basic package metadata, examples, and 48 pytest cases existed.
- `python -m pytest` passed all 48 fixture-based cases.
- `python -m build` produced an sdist and wheel.
- Importing the source module worked only on this machine because a sibling `helix-unified` checkout
  was already discoverable on `sys.path`.

### What did not work

- The wheel contained `tests/` and no `agent_consensus` implementation.
- The import package was an empty namespace because it had no `__init__.py`.
- A dry-run install failed: public package indexes had no `helix-hub-shared>=0.1.0`.
- The only module imported `apps.backend.services.unified_llm` from a sibling private repository and
  wrote to `Helix/state/consensus_usage.jsonl`.
- The module treated the number of successful provider calls as agreement; it did not compare model
  decisions or responses.
- Documented `ConsensusEngine`, `AgentCoordinator`, majority, supermajority, unanimous, BFT,
  conflict-resolution, and monitoring APIs did not exist.
- Tests asserted fixtures and hand-written arithmetic without importing production code.
- Examples either failed to import or printed fabricated results and metrics.
- README installation paths, files, CI, coverage path, and “Production Ready” status were false.
- No workflow, changelog, security policy, package smoke test, lint configuration, or type-check
  configuration existed.

## Baseline command record

Commands were run from the clean `main` worktree at `26d722e` on Windows, Python 3.11.9.

| Command | Actual baseline result |
| --- | --- |
| `git status --short --branch` | Clean; `main...origin/main` |
| `python --version` | `Python 3.11.9` |
| `python -c "import agent_consensus; ..."` | Exit 0, namespace package, no public names |
| `python -c "import agent_consensus.multi_ai_consensus"` | Exit 0 only through sibling `helix-unified`; import took roughly 50 seconds |
| `python examples/01_basic_consensus.py` | Exit 1, `ModuleNotFoundError: No module named 'agent_consensus'` |
| `python -m pytest` | Exit 0, 48 passed in 1.31s; no production imports |
| `python -m build` | Exit 0 with setuptools warnings; built sdist and wheel |
| `python -m zipfile -l dist/agent_consensus-0.1.0-py3-none-any.whl` | Wheel contained only tests and metadata |
| `python -m pip install --dry-run --ignore-installed .` | Exit 1; no matching distribution for `helix-hub-shared>=0.1.0` |
| `python -m pip index versions helix-hub-shared` | Exit 1; no matching distribution found |
| `ruff --version` | `ruff 0.15.12` |
| `mypy --version` | Installed toolchain later identified as `mypy 1.19.1` |

The baseline build generated ignored `build/`, `dist/`, and `agent_consensus.egg-info/` artifacts. They
are not source changes and are removed/rebuilt during final verification.

## Chosen product

### Definition

A zero-runtime-dependency Python library that gathers and evaluates explicit weighted votes, then
applies fail-closed operational rules to the resulting evidence. It returns deterministic,
auditable consensus results and decision verdicts with quorum, threshold, veto, required-reviewer,
vocabulary, failure, timeout, duration, and reported usage details.

### Target user and use case

The primary user is a Python developer who already has two or more independent agents, policy
checks, reviewers, or services. The primary use case is enforcing a bounded release, output-safety,
or routing gate from their explicit choices without adopting a full agent framework or coupling to
one model provider.

### Primary journey

1. Install the wheel or source checkout.
2. Wrap each evaluator in the small async responder protocol.
3. Configure quorum, threshold, concurrency, timeout, size, and token limits.
4. Run one prompt through `ConsensusEngine`.
5. Apply a `DecisionPolicy` with pass, veto, vocabulary, required-participant, and successful-weight
   rules.
6. Permit the protected action only for `passed`; handle `blocked` and `indeterminate` explicitly.
7. Inspect or redact the complete verdict and underlying outcomes for audit.

### Independent reason to exist

AutoGen and LangGraph document broad conversation, routing, and workflow systems. This package is a
small deterministic join/evaluation primitive that can sit inside those systems or ordinary asyncio
applications. It has no dependency on Helix, an agent framework, or an AI provider.

### Portfolio boundary

`agent-consensus` owns explicit-choice collection and deterministic weighted evaluation. The sibling
`neural-mesh` repository addresses richer provider-facing comparison of free-form AI responses,
usage/cost reporting, persistence, and CLI workflows. These are complementary products, not a
runtime stack: neither repository depends on the other, and this package remains useful without any
other Samsarix source checkout.

### Deliberate non-goals

- Provider SDKs, provider credentials, model selection, or model-specific defaults
- Agent conversation, planning, routing, tools, memory, or UI
- Semantic similarity or LLM-based response clustering
- Durable distributed consensus, Byzantine fault tolerance, or authenticated approvals
- Automatic retries, synthesis, persistence, telemetry, billing, or hosted service

## Research and standards decisions

Bounded primary-source research informed the implementation:

- The [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
  supports one `pyproject.toml` source of project and tool metadata; duplicate `setup.py` metadata was
  removed.
- The [Python version status table](https://devguide.python.org/versions/) lists 3.9 as end-of-life
  and 3.10–3.14 as supported on the audit date, so CI covers 3.10–3.14.
- The [asyncio task documentation](https://docs.python.org/3.10/library/asyncio-task.html) documents
  timeout cancellation and gather cancellation behavior used by the engine.
- [AutoGen teams](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html)
  and [LangGraph's graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  cover broader coordination. Their scope supports a narrow, composable decision primitive instead
  of a competing framework.
- [OpenAI Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/) provide
  per-guardrail tripwires. A separate deterministic gate is useful when multiple independent
  guardrail or reviewer choices must satisfy quorum, weighting, required-party, or veto rules.
- [GitHub deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
  demonstrate a real operational need for required reviewers and deployment protection rules. This
  package supplies portable decision evidence; the host platform still owns identity and enforcement.
- [OPA decision logs](https://www.openpolicyagent.org/docs/management-decision-logs) reinforce the
  value of stable decision identifiers and auditable context while warning that logged inputs may
  contain secrets. Verdict serialization therefore remains explicit and caller-redacted.
- Direct public-package comparison found `consensus-weave` focused on quorum/weighted/veto proposal
  arithmetic, `consensys` focused on a provider-dependent code-review product, and
  `agent-consistency` focused on verifying workflow outcomes rather than multi-reviewer approval.
  The defensible wedge here is bounded async evidence collection plus framework-neutral,
  deterministic operational gates—not another agent conversation framework.
- Local read-only portfolio inspection found concrete optional producers: Samsarix Policy Engine
  exposes allow/deny plus policy ID/version/digest; Samsarix Ethics exposes allow/deny/review plus
  decision/policy identity; Samsarix Orchestration names approval/interrupt as a next milestone; and
  LaunchGuard maintains signed release/readiness evidence. The integration cookbook maps these
  public shapes without importing or modifying any sibling repository.
- CI references reviewed immutable commits for `actions/checkout` and `actions/setup-python`, with
  human-readable version comments retained for dependency automation.
- The public [PyPI project URL](https://pypi.org/project/agent-consensus/) returned HTTP 404 on
  2026-07-28. This suggests no public project currently exists, but it does not reserve the name or
  prove that the repository owner can publish it.

Inference: a small provider-neutral decision-gate package is more independently useful and
supportable than preserving the extracted private integration or implementing another general
agent framework.

## Architecture and product decisions

- Explicit `choice` is the sole decision input. Supporting prose is never interpreted as agreement.
- Default normalization changes only whitespace and casing. Domain aliases require an explicit
  caller-owned normalizer.
- Threshold denominator is all configured weight, including failed participants, so availability
  loss cannot inflate agreement.
- Quorum is a successful response count separate from weighted authority.
- Ties never agree, even at a 0.5 threshold.
- Participants are injected async callables; the core imports no provider SDK.
- No automatic retry exists. The host owns idempotency and retry cost.
- Error messages are discarded; only types appear in outcomes.
- Prompts/results are returned to the caller but never logged or persisted by the library.
- Consensus arithmetic and operational policy are separate. A veto or agreed non-pass result is
  `blocked`; incomplete evidence is `indeterminate`; only a fully satisfied policy is `passed`.
- Policy choices match normalized tally values exactly. Allowed vocabularies fail closed on unknown
  values, and required names are availability checks rather than identity authentication.
- Python package metadata lives only in `pyproject.toml`, and package discovery explicitly excludes
  tests.
- Pinned contributor tools live in `requirements-dev.txt`. Runtime has no dependencies, so there is
  no application dependency lock to maintain.
- Runtime dependency-license exposure is empty. Installed metadata for the pinned contributor tools
  reports MIT (`build`, `mypy`, `pytest`, `pytest-cov`, `ruff`) or Apache-2.0 (`pytest-asyncio`,
  `twine`); those tools are not included in runtime artifacts.

## Findings by priority

### P0

- [x] Built wheel omitted implementation.
- [x] Public install failed on an unpublished dependency.
- [x] Runtime relied on a sibling private repository.
- [x] Advertised API and every advertised example were nonfunctional.
- [x] “Production Ready” claim contradicted the repository.
- [x] No production-code tests protected the principal journey.

### P1

- [x] “Agreement” measured provider availability rather than decisions.
- [x] No input, participant identity, size, concurrency, timeout, cancellation, or cost bounds.
- [x] Exception/logging and automatic usage persistence could expose prompt details.
- [x] Duplicate and contradictory package metadata.
- [x] No CI despite README claims.
- [x] No installed-wheel or example verification.
- [x] No truthful security/trust-boundary documentation.
- [x] Consensus results lacked a composable, fail-closed operational policy layer for real release,
  routing, or output-safety gates.
- [x] Successful-weight policy tolerances could forgive a genuine shortfall at large or tiny
  scales. The gate now sums decimal outcome weights exactly, independent of rounded summaries;
  integer minimums that change decimal value during normalization are rejected.
- [x] Current-facing ownership, support, conduct, citation, and attribution metadata used obsolete or
  fictional identities.
- [x] Onboarding snippets kept the async result out of scope, reused earlier static evidence in the
  policy step, and called undefined host-action placeholders. The actual snippets now have source
  and isolated installed-wheel regressions.
- [ ] Owner must verify distribution-name availability and ownership before publication.

### P2

- [ ] Add separately distributed provider adapter examples after users identify demanded providers.
- [x] Add bounded generated invariants for policy precedence, normalization, weights, and ordering.
- [ ] Add signed provenance/SBOM in a publication workflow once release ownership is decided.
- [ ] Reassess dropping Python 3.10 after its scheduled October 2026 end of life.
- [ ] Owner must explicitly retain MIT or select Apache-2.0/MPL-2.0 after confirming the copyright
  chain; the current MIT license was not silently changed.

## Implementation checklist

- [x] Add an importable typed package and deliberate public API.
- [x] Implement weighted static voting with deterministic normalization and ties.
- [x] Implement bounded async fan-out, timeout isolation, and cancellation cleanup.
- [x] Add prompt, content, participant, concurrency, and requested token caps.
- [x] Return auditable typed tallies/outcomes without implicit persistence.
- [x] Replace mock-only tests with production unit and integration tests.
- [x] Make all seven examples execute real library behavior offline.
- [x] Add deterministic pass/veto/required-party/vocabulary/weight policy evaluation with auditable
  reason codes.
- [x] Consolidate build and quality configuration in `pyproject.toml`.
- [x] Add pinned contributor dependencies and cross-version/cross-platform CI.
- [x] Test the installed wheel shape and exclude tests from it.
- [x] Include maintained docs, examples, policies, and tests in the source distribution.
- [x] Rewrite README and API/decision/getting-started documentation.
- [x] Add security policy and changelog.
- [x] Add Samsarix ownership/support metadata, citation, attribution, and trademark guidance.
- [x] Document the standalone sibling-repository boundary and exact owner-gated release process.
- [x] Record an evidence-backed license recommendation without changing legal terms automatically.
- [x] Add repository ownership and monthly dependency-update configuration.
- [x] Record final local and isolated-environment command outcomes below.

## Release acceptance criteria

- [x] Product identity, target user, and non-goals are explicit.
- [x] No private Helix or provider dependency remains.
- [x] Installation has no runtime dependency resolution.
- [x] Static and async primary journeys are implemented and documented.
- [x] Empty, error, timeout, disagreement, quorum failure, and cancellation behavior is tested.
- [x] Configuration fails early for impossible or unsafe local states.
- [x] Errors do not retain exception messages.
- [x] README claims map to files and commands in the repository.
- [x] Format, lint, strict typing, tests/coverage, build, artifact check, isolated install, and examples
  pass in final local verification.
- [x] GitHub-hosted CI passed the supported-version, Windows, quality, package, installed-wheel, and
  example jobs on the pushed release-candidate branch.
- [ ] Release owner has confirmed name/version/tag and PyPI ownership (publication gate).

## Completed work

- Replaced the private four-provider module with provider-neutral models and execution.
- Preserved `agent_consensus.multi_ai_consensus` as an import-path shim without imaginary clients.
- Removed `helix-hub-shared` and unused Pydantic runtime requirements.
- Replaced the empty namespace and mock-only suite with the real package and behavior tests.
- Replaced fabricated examples, BFT claims, monitoring metrics, API, CI, and maturity claims.
- Added modern package discovery, type marker, quality configuration, CI, release notes, and security
  guidance.
- Replaced current-facing Helix/fictitious identities with Samsarix LLC and its working contact and
  support addresses while preserving historical provenance.
- Added `NOTICE`, `TRADEMARKS.md`, `CITATION.cff`, release instructions, and a licensing decision
  record recommending Apache-2.0 or MPL-2.0 according to the owner's protection goal.
- Defined a clean portfolio boundary with `neural-mesh`; both repositories remain standalone.
- Added a framework-neutral operational decision gate, complete release-gate example, stable reason
  codes, and explicit host-enforcement guidance.
- Added stable policy IDs/digests plus a provider-neutral policy-panel example and cookbook grounded
  in read-only inspection of real optional producer contracts.
- Added an optional, separately packaged policy-engine consumer verified against a pinned real
  producer wheel, with a versioned fixture, drift controls, immutable request binding, deny-veto
  enforcement and a separate compatibility workflow. No producer code enters the core wheel.
- Closed merged-review findings covering shared validation, immutable hashing, metadata tests,
  alias normalization, documentation accuracy, least-privilege release guidance, and immutable CI
  action references.
- Updated the pinned contributor test runner to pytest 9.0.3, the first patched release for
  CVE-2025-71176; the affected tool is development-only and not present in the runtime wheel.

## 0.2 productization verification (2026-07-28)

Commands below were run after implementation and documentation changes on Windows. The execution
environment blocked removal of ignored baseline artifact directories even after their absolute paths
were verified, so the release artifacts and isolated virtual environment were created under a new,
GUID-named system temporary directory. The wheel was built from that fresh sdist. The first branded
metadata build correctly failed because setuptools does not accept a `mailto:` project URL; the
maintainer email was retained and the project link was corrected to HTTPS before the successful run.

| Command | Final result |
| --- | --- |
| `git diff --check` | Exit 0, no whitespace errors |
| `python -m ruff format --check .` | Exit 0, 14 files already formatted |
| `python -m ruff check .` | Exit 0, all checks passed |
| `python -m mypy agent_consensus` | Exit 0, no issues in 5 source files |
| `python -m pytest` | Exit 0, 48 passed; 98.36% branch-aware coverage (95% required) |
| `py -3.13 -c "...evaluate_votes..."` | Exit 0, printed `agreed yes` |
| `python -m pip install --dry-run -r requirements-dev.txt` | Exit 0; pinned tools resolved and editable package would install |
| `python -m build --outdir <fresh-temp>/dist` | Exit 0; built `0.2.0` sdist and pure-Python wheel from the fresh sdist |
| `python -m twine check <fresh-temp>/dist/*` | Both artifacts passed |
| `python -m zipfile -l <fresh-temp>/dist/*.whl` | Wheel contains the six package/type-marker files, metadata, MIT license, NOTICE, and trademark guidance; no tests or private code |
| `tar -tf <fresh-temp>/dist/*.tar.gz` | Sdist contains package, citation, attribution, trademark guidance, docs, examples, policies, contributor requirements, and tests |
| `cffconvert --validate -i CITATION.cff` | Exit 0; citation metadata is valid against CFF schema 1.2.0 |
| `<fresh-temp>/venv/Scripts/python -m pip install --no-deps <wheel>` | Exit 0, installed `agent-consensus-0.2.0` |
| Isolated import outside the checkout | Exit 0; imported version `0.2.0`, vote smoke result `agreed yes` |
| `<fresh-temp>/venv/Scripts/python -m pip check` | Exit 0, no broken requirements |
| `<fresh-temp>/venv/Scripts/python examples/<each of five scripts>` | Every example exited 0 with real output |
| GitHub Actions CI | Passed quality; Linux Python 3.10–3.14; Windows Python 3.14; wheel/sdist, installed-wheel, and example jobs on the pushed branch |
| Tracked-file credential pattern scan | No matches |

Not run locally: Python 3.10, 3.12, and 3.14 full suites (interpreters unavailable); Linux tests;
TestPyPI/PyPI publication; real paid provider calls. Python 3.11 ran the complete local suite and
Python 3.13 ran a local core smoke test. GitHub-hosted CI supplied the remaining Linux Python
3.10–3.14 and Windows Python 3.14 evidence.

## Decision-gate iteration verification (2026-08-01)

The decision-gate branch was verified on Windows with Python 3.14.6 in a fresh system-temporary
virtual environment installed solely from `requirements-dev.txt`. A second environment installed
the built wheel with `--no-deps` and ran outside the checkout so source-tree imports could not mask
packaging defects.

| Command | Actual result |
| --- | --- |
| `python -m ruff format --check .` | Exit 0; 17 files already formatted |
| `python -m ruff check .` | Exit 0; all checks passed |
| `python -m mypy agent_consensus` | Exit 0; no issues in 6 source files |
| `python -m pytest` | Exit 0; 80 passed; 99.62% branch-aware coverage (95% required) |
| `python -m build --outdir <fresh-temp>/dist` | Exit 0; built the sdist, then built the pure-Python wheel from that sdist |
| `python -m twine check <fresh-temp>/dist/*` | Wheel and sdist passed |
| `<fresh-temp>/wheel-env/Scripts/python -m pip install --no-deps <wheel>` | Exit 0; installed `agent-consensus-0.2.0` with no dependencies |
| Installed API smoke outside checkout | Exit 0; serialized schema-v1 policy ID and the stable digest vector `3db772...fa71c` |
| `<fresh-temp>/wheel-env/Scripts/python -m pip check` | Exit 0; no broken requirements |
| Installed-wheel execution of `examples/*.py` | All seven examples exited 0; release and policy-panel gates passed with source references preserved |

Exact-head artifact digests belong in the external pull-request or release evidence rather than
inside the sdist itself: embedding a newly calculated sdist digest changes that artifact. The local
verification retained both artifacts in a GUID-named system temporary directory for inspection.

GitHub Actions on draft PR #12 passed quality, Linux Python 3.10–3.14, Windows Python 3.14, package
build/check, installed-wheel, and all-example jobs for implementation head
`4ff499b1260821f5b71f5c1247ff5d869eb442db`. TestPyPI/PyPI
publication, a real external consumer, and paid-provider calls remain intentionally outside local
verification.

## Successful-weight boundary verification (2026-08-31)

PR #12 was merged at `e7632fc`; this iteration started from clean `main` at `2cc7066` after the
contributor-tool updates in PR #13. That baseline passed 82 tests (96.96% coverage), but a minimum of
`1e12 + 0.5` incorrectly passed with only `1e12` successful weight. Tiny shortfalls, inflated summary
totals, and integer minimums rounded down to floats exposed equivalent routes. Fifteen new
regression cases failed against the original implementation before the patch.

The fix recomputes successful weight from successful outcomes using exact decimal rational
arithmetic, without changing consensus tally arithmetic. Policy construction rejects integer
minimums that cannot retain their decimal value in the existing schema-v1 float representation.
The numeric contract and computed-float limitations are documented in `DECISION_GATES.md`.
An independent read-only candidate review found no surviving concrete bypass or regression.

Verification used a fresh Windows Python 3.14.7 environment installed from `requirements-dev.txt`;
the complete suite also ran on Windows Python 3.11.9. A separate, dependency-free environment
installed the wheel and ran outside the checkout with Python isolated mode (`-I`).

| Command | Actual result |
| --- | --- |
| `git diff --check` | Exit 0; no whitespace errors |
| `python -m ruff format --check .` / `python -m ruff check .` | Exit 0; format and lint passed |
| `python -m mypy agent_consensus` | Exit 0; 6 source files passed strict typing |
| `python -m pytest tests/test_policy.py -q --no-cov` | Exit 0; 54 passed |
| `python -m pytest` / `py -3.11 -m pytest -q` | Exit 0; 106 passed on each interpreter; 97.18% coverage |
| `python -m build --outdir <fresh-temp>/dist` | Exit 0; wheel built from fresh sdist |
| `python -m twine check <fresh-temp>/dist/*` | Both artifacts passed |
| `<wheel-env>/python -m pip install --no-deps <wheel>` / `pip check` | Installed successfully; no broken requirements |
| `<wheel-env>/python -I -c '<import-path and boundary assertions>'` outside checkout | Imported from the new environment's site-packages; large shortfall rejected and `0.1 + 0.7` control accepted |
| `<wheel-env>/python -I <absolute-example-path>` | All seven examples passed |

The existing policy digest golden vector remains unchanged. Additional controls cover outcome
ordering, weight scaling, independence from the host decimal context, integer normalization, and
async error/timeout/invalid-response paths. Only complete successful evidence contributes weight.

The earlier formal diff-scan publication failed; its terminal status was rechecked and no completed
report is available. The targeted reproduction, independent review, and checks above are evidence
for this fix, not a claim of a completed repository-wide security audit. Exact-head hosted CI and
artifact hashes are recorded in the pull request. Package publication and external production
adoption are not part of this verification.

## Artifact and generated-invariant follow-up (2026-08-31)

The installed-wheel CI smoke previously ran an import from the checkout, which could resolve source
instead of the installed artifact. CI now runs `scripts/check_installed.py` and all seven examples
with `-I`, asserts package location and distribution metadata, and checks dependency consistency.
The source distribution includes this verification script and the roadmap. The script exercises a
consumer-owned release simulation with approved, vetoed, unknown-choice and unavailable-reviewer
outcomes and an explicit audit-field allowlist. It is not a claim of external adoption.

New bounded exhaustive tests enumerate 4,608 policy/order configurations, 2,048 exact-decimal
boundary comparisons and 256 policy-strengthening comparisons. The independent Decimal oracle
exposed a second defect: 24 of its 512 fractional panels generated agreement above 1.0 on Python
3.14, then failed evidence validation. Tally accumulation used repeated addition while totals used
Python's `sum`. Both now use the same [accurate floating-point summation](https://docs.python.org/3/library/math.html#math.fsum).
Aggregate overflow is a configuration error, checked before async adapter execution. The
floating-point threshold/tie semantics remain distinct from the exact policy minimum.

The final source suite passes **115 tests with 97.22% coverage** on Windows Python 3.14.7 and 3.11.9.
Formatting, lint and strict package typing pass. Four dependency-free installed-wheel checks and all
seven examples are required in addition to the source suite; the exact-head build/install/CI record
and artifact hashes are recorded in the pull request. The earlier independent security-fix review
covered the minimum-weight patch; the generated-invariant follow-up was reviewed locally with
separate static, async, overflow, decimal-oracle, and installed-wheel regressions.

## Installed producer/consumer verification (2026-08-31)

The documented policy-panel recipe now has a separately packaged reference consumer under
`integrations/policy_engine`. It uses actual `PolicyEngine.evaluate` outputs from
`samsarix-policy-engine` 0.1.0 at public commit
`6e51f2585fa4412037f4f5458d313cb26ad3d59d`; the producer checkout was inspected read-only and exported
to a temporary directory for building. The sibling worktree was not modified. Three separate wheels
(core, producer, consumer) were installed with `--no-index --no-deps`, then verified in Python
isolated mode from outside the checkout. This proves installed contract compatibility, not external
production adoption.

Consumer contract v1 includes policy content, the golden producer policy digest
`a56d4e100f024f143121969504f77d6d`, producer revision/version, request fixture and seven expected
outcomes. The source policy version is its schema version. A source deny vetoes the heavier readiness
majority; missing/invalid/drifted evidence fails closed. The host operation receives the same frozen
request evaluated by the source. The returned audit is allowlisted, and operation exceptions
propagate without retries or invented success. Eight installed-consumer tests cover those paths,
including a mutation during asynchronous collection and seven source-contract drift variants.

| Command | Local result |
| --- | --- |
| `python -m ruff format --check .` / `python -m ruff check .` | Passed |
| `python -m mypy agent_consensus` | Passed; 6 source files |
| `python -m mypy --strict --python-version 3.11 integrations/policy_engine/consensus_policy_consumer` | Passed; consumer source checked against the installed typed producer |
| `python -m pytest -q` | 118 passed; core coverage remains 97.22% |
| `python -m pytest -q` from the extracted fresh core sdist | 118 passed; import-path assertion confirmed the extracted package, not the checkout |
| `python -m build <producer-export> --outdir <temp>/producer-dist` | Built producer sdist and wheel from the pinned source export |
| `python -m build integrations/policy_engine --outdir <temp>/consumer-dist` | Built independent consumer sdist and wheel, including its contract |
| `<consumer-python> -m pip install --no-index --no-deps <three-wheels>` / `pip check` | Installed successfully; no broken requirements |
| `<consumer-python> -I integrations/policy_engine/verify.py` | 8 passed; all imports came from the isolated environment |
| `<consumer-python> -I scripts/check_installed.py` | 4 passed; core wheel excludes integration/producer modules |
| `python -m twine check <core/producer/consumer artifacts>` | All six wheel/sdist artifacts passed |

The dedicated workflow runs on Linux Python 3.14 and Windows Python 3.11, using a pinned public
producer checkout and read-only permissions. Core CI has no dependency on that checkout or workflow.
Exact-head artifact hashes, clean-sdist verification and hosted results belong in the integration PR.
The producer's BUSL terms remain separate from this project's MIT terms; non-production integration
testing is not a grant of production rights, and no producer source is vendored or relicensed.

A fresh primary-source check of [LangGraph workflow patterns](https://docs.langchain.com/oss/python/langgraph/workflows-agents),
[Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/), and
[OPA decision logs](https://www.openpolicyagent.org/docs/management-decision-logs) supports the
same product choice: compose with host workflow/guardrail systems and use explicit, redacted audit
context. The inference for this product is to prove a narrow enforcement integration, not add an
agent framework, hosted database or telemetry service. No comparative performance or market-demand
claim follows from that research.

## Release-candidate security review and handoff (2026-08-31)

A Standard static security scan completed successfully for revision
`4d87c0a8d6af49d4317d22adcf81b09586f9d7ab`, scan ID
`7fa48710-d8c6-45ae-aace-f20d70bdbe39`. An independent baseline, architecture review, two focused
control reviews and parent reconciliation covered all 55 tracked files. No confirmed vulnerabilities
were reported. The generated report, canonical manifest, coverage and findings artifacts were
validated and indexed by the scan service; this is distinct from the earlier failed diff scan.

The audit was read-only and offline: test code was inspected, not executed as part of the scan.
The runtime and installed-package results above are separate verification evidence. Producer
implementation, ignored build environments, live infrastructure and real consuming applications
were outside scope. A clean static scan is not a guarantee of security or production readiness.

Review confirmed the in-scope veto, required-participant, closed-vocabulary, exact minimum-weight,
request-binding and audit-allowlist controls. Documented limitations remain: floating-point
thresholds, host-authority adapters, cooperative/per-run limits, unauthenticated participant names,
shallow metadata freezing and host-owned authorization/retention. The README now distinguishes the
async quorum default of 2 from the collected-vote default of 1 and makes the different roster and
resource-limit contracts explicit. These follow-up edits change documentation only.

Release handoff status (updated after owner-authorized merges):

1. [PR #14](https://github.com/Deathcharge/agent-consensus/pull/14), containing numeric hardening and
   isolated artifact verification, merged as `f9ad5f1a3a2b87388d2e85fe4990cc9a22229ba2`.
2. [PR #15](https://github.com/Deathcharge/agent-consensus/pull/15) was retargeted to `main`, its
   resulting merge tree checked against the tested head, and merged as
   `036ea2ba2b0d5abe1509c01293d4f7864b41ecc1`. No open PRs remained. The owner authorized subsequent
   focused work directly on `main`; no history was rewritten or sibling repository changed.
3. Confirm license, package ownership and release identity, then follow `RELEASING.md` before any
   TestPyPI/PyPI upload. No publication, deployment, license change or sibling modification is
   included in this handoff.
4. Before claiming production adoption, obtain the actual consumer application's own enforcement,
   identity, privacy, idempotency and rollback tests. The reference consumer is not that evidence.

Exact commit checks, artifact hashes and the completed scan identifier belong in the pull-request
evidence. The scan covers the revision named above; later documentation edits do not imply a new
whole-repository audit or silently extend its scope.

## Exact-artifact candidate handoff (2026-08-31)

The merged baseline passed [core CI](https://github.com/Deathcharge/agent-consensus/actions/runs/33416693014)
and [installed-consumer CI](https://github.com/Deathcharge/agent-consensus/actions/runs/33416692887).
Its local suite passed 118 tests with 97.22% core coverage. An artifact API check found zero retained
artifacts for the core run: CI had verified distributions but discarded the files needed to follow
the release procedure's requirement to publish the same bytes. This was a P1 release-handoff gap,
not a runtime defect or a reason to publish prematurely.

The bounded correction adds `scripts/release_bundle.py`, a standard-library-only release tool outside
the runtime wheel/API. After existing package checks, main-push CI creates a deterministic receipt,
verifies it, and retains the exact wheel, sdist and receipt for seven days. Upload uses the reviewed
`actions/upload-artifact` v7.0.1 commit `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`, with no new
repository write or publishing permissions. Artifact names include the commit, run ID and attempt.
Pull-request CI does not retain candidates. Expiry limits retention within the existing Actions
allowance; no billing configuration was changed.

Creation requires exactly one core wheel and matching sdist, refuses an existing receipt, and never
overwrites it. Verification requires an independently supplied commit and manifest digest, validates
an exact schema and inventory, rejects duplicate JSON keys, symbolic links, unsafe filenames and size/hash
mismatches, and reads without extracting or executing artifacts. Receipts are limited to 64 KiB and
each distribution to 100 MiB. Negative tests cover mutation, malformed/untrusted input, missing and
extra files, invalid identity, repeat creation, isolated CLI behavior and nonzero failure exits.

Local source verification on Windows Python 3.14.7:

| Command | Result |
| --- | --- |
| `python -m ruff format --check .` / `python -m ruff check .` | Passed |
| `python -m mypy agent_consensus` / `python -m mypy --strict scripts/release_bundle.py` | Passed; 6 runtime files and 1 release-tool file |
| `python -m pytest -q` | 154 passed; core coverage unchanged at 97.22% |
| `python -m pytest -o addopts= tests/test_release_bundle.py --cov=scripts.release_bundle --cov-branch --cov-report=term-missing --cov-fail-under=95` | 36 passed; release-tool coverage 95.81% |
| `python -m build --outdir <fresh-temp>/dist` / `python -m twine check <fresh-temp>/dist/*` | Fresh wheel built from sdist; both metadata checks passed |
| `<wheel-python> -m pip install --no-index --no-deps <wheel>` / `pip check` | Installed in a new environment; no broken requirements |
| `<wheel-python> -I scripts/check_installed.py` / all seven examples with `-I` | 4 installed-wheel checks and all examples passed |
| `python -m pytest -q` from the extracted fresh sdist | 154 passed; 97.22% core coverage; import-path assertion confirmed extracted source |

CI repeats the new tests across the supported matrix and gates release-tool coverage separately
from core coverage. The release procedure now gives exact trusted-run selection, download,
verification, isolated installation and expiry-recovery steps. Exact-head hosted run and downloaded
artifact evidence must accompany the candidate's handoff; these source results alone are not that
evidence. The optional consumer's code and pinned producer contract were not changed by this slice.

This design follows [PyPA's build/publish separation](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
and [GitHub's artifact handoff model](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts).
The product inference is to preserve already-tested bytes, not add a publishing service. The receipt
is unsigned and only binds bytes to a stated commit; it is not authenticated source provenance, a
package-content validator, an SBOM, a license approval or evidence of production adoption. Trusted
CI/account access, an independent digest and stable local files remain assumptions. The previous
formal scan does not cover this new release tooling. Package publication and license choice remain
owner-gated; signed provenance and a real application's adoption evidence remain higher-value next
gates than additional speculative runtime features.

## Executable onboarding follow-up (2026-08-31)

A broader goal audit at `dac0dcffb99d751b686b84b4183e53ff87131673` confirmed a clean synchronized
`main`, successful exact-head CI, no open issues or PRs, and a verified downloadable candidate.
Those checks did not prove the documented developer journey. Executing the getting-started Python
snippets in their displayed order exposed a P1 onboarding defect: `main()` printed its async
result but returned nothing, leaving the global `result` bound to the earlier `a`/`b`/`c` votes.
The policy therefore produced `blocked`, then failed with `NameError: name 'stop' is not defined`,
even though the preceding async example had printed `agreed approve`. README had the same scope
trap and undefined host-operation placeholders.

Both guides now return the async `ConsensusResult` into the next step and print explicit local
action dispositions. They distinguish those prints from real deployment execution and explain that
only the passed branch may invoke a host operation. The getting-started interface signature is
plain reference text; all Python example blocks are runnable, explicitly marked and tested. Its
installation check now uses `-I` to avoid accidentally importing checkout source.

Ten tests execute the exact displayed snippets, verify that the policy receives the async evidence
rather than the earlier static votes, and exercise approved, veto, missing-reviewer and unknown-choice
branches for both guides. Missing, duplicate or unmarked example blocks fail the contract. The
existing standard-library installed-wheel checker also runs both walkthroughs, now totaling five
checks, so examples cannot pass solely because checkout imports work. These mechanisms execute
trusted repository documentation only; they are not general Markdown execution features.

Local checks on Windows Python 3.14.7:

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_documented_examples.py -q --no-cov` | 10 passed |
| `python -m pytest -q` | 164 passed; core coverage remains 97.22% |
| `python -m ruff format --check .` / `python -m ruff check .` / `python -m mypy agent_consensus` | Passed |
| `<isolated-wheel-python> -I scripts/check_installed.py` | 5 passed, including both updated guides against the previously downloaded `dac0dcf` CI wheel |

No runtime source/API, license, version, provider dependency or protected host action changed.
The exact-head CI build and readback evidence for this follow-up must accompany its commit; the
previous candidate's digest is not a digest of newly built files.

A same-day primary-source refresh of [LangGraph parallel workflows](https://docs.langchain.com/oss/python/langgraph/workflows-agents),
[Agents SDK blocking guardrails](https://openai.github.io/openai-agents-python/guardrails/), and
the [consensus-weave package description](https://pypi.org/project/consensus-weave/) still supports the
chosen composition boundary: deterministic evidence collection/evaluation complements broader
workflow systems and explicit weighted-vote libraries. This is a scope inference, not a measured
competitive ranking or demand claim. A reproducible first-use journey is actionable here; additional
frameworks, provider adapters or telemetry still need consumer evidence. Publication ownership,
license confirmation and actual application adoption remain separate gates.

## Numeric error-contract follow-up (2026-08-31)

The requirement audit at `3939dc227512b34b0b04840bda4c2585402831ad` found a caller-visible error
contract gap. Python integers such as `10**400` caused `math.isfinite` to raise `OverflowError`
before the public validators could raise their documented package errors. Six entry paths were
reproduced: configuration/static thresholds, timeouts, participant/vote weights and confidence.
The same primitive error escaped structural validation of numeric consensus evidence. This was an
invalid-input reliability defect, not a demonstrated authorization bypass.

A private shared finite-number predicate now rejects overflowing integers without converting
accepted values in place. Configuration errors remain `ConfigurationError`, vote/response errors
remain `ResponseValidationError`, and inconsistent numeric decision evidence raises
`DecisionInputError`. The existing policy minimum's exact-decimal semantics, policy digests,
threshold/tie arithmetic, accepted integer weights, and runtime dependency boundary are unchanged.

The first focused regression run failed 26 cases and passed 23 controls before the fix. The final
67-case suite also covers booleans/numeric strings, NaN/infinities, all affected numeric evidence
fields, async error isolation and finite-value preservation. Positive controls include `2**53 + 1`,
`10**308`, the largest finite float and the smallest positive float. The installed-wheel checker now
has six checks, including numeric error and integer-preservation controls.

| Command | Local Windows Python 3.14.7 result |
| --- | --- |
| `python -m pytest tests/test_numeric_validation.py -q --no-cov --tb=no` before the fix | 26 failed, 23 passed, confirming the regression |
| `python -m pytest -q` after the fix and expanded controls | 231 passed; 98.17% core coverage |
| `python -m ruff format --check .` / `python -m ruff check .` | Passed |
| `python -m mypy agent_consensus` | Passed; 6 source files |
| `git diff --check` | Passed |

The follow-up's exact-head CI, installed artifact and source-archive evidence belongs in its commit
verification record; an older wheel cannot prove this runtime fix. No new public API, dependency,
license term, version, publisher configuration or sibling-repository change is included.

## Bounded roster collection follow-up (2026-08-31)

Revalidation at `0f4c657f8985befa90a210268e1ac6bc845e43dd` confirmed green terminal CI, a clean
`main`, no open issues/PRs and unchanged owner publication gates. Before treating those gates as an
impasse, inspection of the `Iterable[Participant]` constructor found a locally actionable resource
gap: it converted the entire iterable to a tuple before checking `max_participants`. A bounded
reproduction configured a cap of 3 and observed all 100 entries consumed before rejection. An
unbounded or very large dynamic registry therefore could defeat the intended collection bound.

The constructor now accumulates only a permitted roster and rejects the first excess entry. It
consumes at most `max_participants + 1` entries, does not silently truncate or drain the input, and
preserves valid snapshot order, repeat runs and large positive integer caps. The caller continues to
own the iterator; the library neither closes it nor hides errors it raises before the cap. Work
inside a single iterator step remains synchronous and caller-owned, not preempted or sandboxed.
The explicitly uncapped synchronous `evaluate_votes` helper was not changed.

The focused suite failed four cases and passed six controls before the fix, then passed all ten.
It covers caps 1/3/32, valid snapshots/reuse, remaining iterator contents after rejection, registry
errors, very large caps and independence from length-hint preallocation. The installed-wheel checker
now has seven checks, including the same cap=3 consumption assertion.

| Command | Local Windows Python 3.14.7 result |
| --- | --- |
| `python -m pytest tests/test_roster_bounds.py -q --no-cov --tb=no` before the fix | 4 failed, 6 passed |
| `python -m pytest tests/test_roster_bounds.py -q --no-cov` after the fix | 10 passed |
| `python -m pytest -q` | 241 passed; 98.18% core coverage |
| `python -m ruff format --check .` / `python -m ruff check .` / `python -m mypy agent_consensus` | Passed |
| `git diff --check` | Passed |

The API guide documents both the new collection bound and its cooperative iterator limitation.
Exact-head hosted and downloaded-artifact checks belong in the follow-up commit record. No new API,
provider coupling, vote arithmetic, automatic iterator cleanup, publication or legal change is
included. This is concrete engineering progress; the still-unanswered license/publication/adoption
gates are not treated as permission to publish or expand into sibling repositories.

## Mission evidence map (2026-08-31)

This map ties the original numbered mission to concrete evidence rather than treating a green test
count as a blanket completion claim. Historical baselines and exact-head records above remain
separate from owner-controlled publication and real adoption.

| Mission requirement | Evidence and disposition |
| --- | --- |
| 1. Preserve existing work and repository scope | Incremental git history, owner-authorized PR merges and subsequent `main` commits; clean synchronized checkpoints. No force pushes or sibling modifications. |
| 2. Audit the real repository | Baseline wheel/import/install failures recorded above; current runtime, models, policy, packaging, docs, workflows and test assertions inspected. Recent executable-doc and numeric-error reproductions contradicted weaker prior evidence and were fixed. |
| 3. Define a defensible independent product | README/product definition and primary-source research: bounded explicit-choice collection plus deterministic operational rules, with no framework/provider coupling or fabricated demand claim. |
| 4. Maintain a productization record | This document records baseline, priorities, decisions, completed work, commands, risks, acceptance criteria and external gates. |
| 5. Complete the primary journey | Static and async builders, `evaluate_decision`, seven offline examples, exact guide-snippet regressions and installed callback-enforcement checks. No placeholder host action is represented as a deployed action. |
| 6. Apply package-specific quality | Deliberate typed exports, `py.typed`, version/changelog, zero-runtime-dependency metadata, wheel/sdist inspection and isolated public-API checks. UI/service/store requirements are inapplicable to this library. |
| 7. Verify engineering and release quality | Pinned contributor tools, format/lint/strict typing, source and generated invariants, six CI environments, installed wheel and downloaded-sdist test records; seven-day candidate receipts retain exact tested files. |
| 8. Address security, privacy and cost | The core has no provider/network/file persistence; tests cover bounded collection, cancellation, error redaction, budgets, vetoes and invalid input. SECURITY.md documents trusted adapters, cooperative limits and host-owned identity/retention. The dated formal scan does not cover later edits. |
| 9. Onboard an independent user | README and getting-started snippets execute in source tests and installed-wheel checks; API, decision, integration, contribution and release guides are maintained. |
| 10. Respect external/owner gates | No package publication or license switch is implied. Package ownership, legal confirmation, release identity/publisher configuration and actual consumer adoption remain unverified owner actions. |
| 11. Apply the definition of done | Technical source/artifact evidence supports a standalone release candidate; it does not prove package-index installation, production adoption, authenticated approval or market demand. Those claims remain explicitly absent. |
| 12. Provide an evidence-based handoff | Focused commits carry CI links, commands, results and artifact digests in their verification records. Release disposition remains qualified by the named external gates. |

## Deferred work and rationale

- Provider adapters: demand and maintenance burden are unknown; injection already supports them.
- Semantic clustering/synthesis: nondeterministic, costly, and contrary to the explicit-decision
  trust model.
- Persistence: result retention and privacy requirements belong to the host application.
- Publication automation: cannot be tested honestly without owner repository/package configuration.
- License change: existing MIT intent is clear and earlier grants cannot be revoked. Apache-2.0 is
  the permissive recommendation and MPL-2.0 is the reciprocity alternative, but copyright-chain and
  legal intent remain owner decisions. See `docs/LICENSING.md`.

## Owner/external blockers

1. Explicitly retain MIT or select Apache-2.0/MPL-2.0 after confirming copyright ownership and any
   contributor consent. Verification: `LICENSE`, `pyproject.toml`, `CITATION.cff`, README, and the
   release tag all identify the same terms; prior MIT versions remain available under MIT.
2. Confirm that `agent-consensus` is the desired public distribution name and claim it through the
   authorized release flow. The unauthenticated project URL returned 404 during this audit, but name
   availability can change. Verification: open the intended project page while authenticated and
   confirm owner access immediately before release.
3. Choose the first public version/tag (the repository currently declares `0.2.0`) and review this
   changelog. Verification: version, Git tag, and artifact metadata match.
4. If publishing, configure a PyPI Trusted Publisher scoped to this repository and release workflow;
   do not add an API token to repository files. Verification: publish to TestPyPI first and install
   the exact artifact in a clean environment.

## Known risks

- Participant identity and authority are configured in-process, not cryptographically verified.
- Custom normalizers can merge choices unsafely.
- Adapters can ignore token allocations or perform unbounded input-token work; the host must review
  adapters.
- A timeout waits for coroutine cancellation cleanup and can therefore exceed the configured value
  if an adapter suppresses cancellation.
- A participant that performs blocking synchronous work can stall the shared event loop; adapters
  must use non-blocking clients or explicitly move blocking work to a bounded thread executor.
- Result metadata can be non-JSON or sensitive because it is caller-owned.
- Public package-index installation evidence does not exist until the owner exercises the
  publication gates. Hosted CI evidence exists for the merged 0.2 release-candidate work and the
  decision-gate implementation on merged PR #12; each subsequent candidate needs its own CI record.

## Distribution and sustainability

The simplest distribution is a pure-Python wheel and sdist on PyPI, with source installation as the
pre-publication path. A free open-source library maintained by Samsarix LLC is the honest initial
model. Apache-2.0 best balances adoption, patent clarity, attribution mechanics, and trademark
separation; MPL-2.0 is appropriate if the owner prioritizes reciprocity for distributed file changes.
If maintenance demand emerges, sustainability could come from funded support or separately
maintained adapters; a hosted subscription is not justified and would add credentials, privacy,
availability, and billing scope without strengthening the core product.
