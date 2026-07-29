# Productization record

Last updated: 2026-07-28

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

A zero-runtime-dependency Python library that evaluates explicit weighted votes and can safely gather
those votes from async application-supplied participant adapters. It returns deterministic,
auditable results with quorum, threshold, failure, timeout, duration, and reported usage details.

### Target user and use case

The primary user is a Python developer who already has two or more independent agents, policy
checks, reviewers, or services. The primary use case is making one bounded release/policy/routing
decision from their explicit choices without adopting a full agent framework or coupling to one
model provider.

### Primary journey

1. Install the wheel or source checkout.
2. Wrap each evaluator in the small async responder protocol.
3. Configure quorum, threshold, concurrency, timeout, size, and token limits.
4. Run one prompt through `ConsensusEngine`.
5. Branch on `agreed`, `no_consensus`, or `quorum_failed` and inspect all outcomes.

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
  and [LangGraph multi-agent patterns](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)
  cover broader coordination. Their scope supports a narrow, composable decision primitive instead
  of a competing framework.
- Current official action repositories document `actions/checkout@v6` and
  `actions/setup-python@v6`; CI uses those major versions.
- The public [PyPI project URL](https://pypi.org/project/agent-consensus/) returned HTTP 404 on
  2026-07-28. This suggests no public project currently exists, but it does not reserve the name or
  prove that the repository owner can publish it.

Inference: a small provider-neutral package is more independently useful and supportable than
preserving the extracted private integration or implementing another general agent framework.

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
- [x] Current-facing ownership, support, conduct, citation, and attribution metadata used obsolete or
  fictional identities.
- [ ] Owner must verify distribution-name availability and ownership before publication.

### P2

- [ ] Add separately distributed provider adapter examples after users identify demanded providers.
- [ ] Add property-based tests for custom voting policies if the policy surface expands.
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
- [x] Make all five examples execute real library behavior offline.
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
- [ ] GitHub-hosted CI has run on the final commit (external gate).
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

## Final verification

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
| Tracked-file credential pattern scan | No matches |

Not run locally: Python 3.10, 3.12, and 3.14 full suites (interpreters unavailable); Linux tests;
GitHub-hosted CI; TestPyPI/PyPI publication; real paid provider calls. Python 3.11 ran the complete
suite and Python 3.13 ran a core smoke test. CI defines the remaining Python 3.10–3.14 and Windows
matrix, but its result is an external release gate rather than a local claim.

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
4. Run the repository's GitHub-hosted CI on the final change. Verification: all matrix and package
   jobs are green.
5. If publishing, configure a PyPI Trusted Publisher scoped to this repository and release workflow;
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
- No real CI run or public installation evidence exists until the owner exercises external gates.

## Distribution and sustainability

The simplest distribution is a pure-Python wheel and sdist on PyPI, with source installation as the
pre-publication path. A free open-source library maintained by Samsarix LLC is the honest initial
model. Apache-2.0 best balances adoption, patent clarity, attribution mechanics, and trademark
separation; MPL-2.0 is appropriate if the owner prioritizes reciprocity for distributed file changes.
If maintenance demand emerges, sustainability could come from funded support or separately
maintained adapters; a hosted subscription is not justified and would add credentials, privacy,
availability, and billing scope without strengthening the core product.
