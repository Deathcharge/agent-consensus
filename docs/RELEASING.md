# Release procedure

Releases are owner-gated. Building and validating artifacts is safe locally; creating a GitHub
release, registering a package index publisher, or uploading artifacts changes external state and
requires an authorized Samsarix release owner.

## 1. Decide the release identity

- Confirm `agent-consensus` is the intended PyPI distribution name and the owner controls it.
- Make the explicit license choice recorded in [LICENSING.md](LICENSING.md).
- Choose a version using semantic versioning.
- Keep that version synchronized in `pyproject.toml`, `agent_consensus/__init__.py`,
  `CITATION.cff`, and `CHANGELOG.md`.
- Confirm current-facing author, maintainer, support, repository, and project URLs.

## 2. Verify the candidate

From a clean checkout with the pinned contributor toolchain installed:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy agent_consensus
python -m pytest
python -m build
python -m twine check dist/*
```

Inspect the wheel and sdist, then install the exact wheel into a new virtual environment with
`--no-deps`. Using **that environment's Python**, run:

```bash
python -m pip check
python -I scripts/check_installed.py
python -I examples/01_basic_consensus.py
# Repeat for each of the seven examples listed in README.md.
```

`-I` excludes checkout paths and `PYTHONPATH` from imports. The check asserts that the installed
package comes from the selected environment, checks version, licenses, typing marker and absence
of runtime dependencies, and exercises a local release consumer's pass, veto, unknown-choice and
unavailable-reviewer paths. It also checks strict successful-weight boundaries. This consumer
simulation is not evidence of external production adoption. The CI matrix must also be green on
every supported Python version before publication.

## 3. Configure publication without stored tokens

Use a PyPI Trusted Publisher tied to this GitHub repository, a narrowly scoped release workflow,
and a protected `pypi` GitHub environment. PyPI's
[Trusted Publisher documentation](https://docs.pypi.org/trusted-publishers/) explains the OIDC flow;
it mints short-lived credentials instead of storing a long-lived API token in repository secrets.

The publishing job should declare job-level permissions containing only `id-token: write`, consume
artifacts built by an unprivileged job, and use
`pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33` (`release/v1`). Add an
artifact read permission only if the final workflow's artifact topology requires it; the publishing
job does not need repository contents. Re-review pinned action SHAs when updating their release.

Do not configure publication until the distribution name, license, version, repository environment,
and required reviewer are confirmed. This repository intentionally does not contain a live publish
workflow before those owner decisions.

## 4. Stage and publish

1. Publish the candidate through a separately configured TestPyPI trusted publisher.
2. Install from TestPyPI into a clean environment and repeat the import and example smoke tests.
3. Review the rendered project metadata and README.
4. Tag the exact verified commit (for example, `v0.2.0`) and create immutable release notes from the
   changelog.
5. Approve the protected PyPI environment to publish the already-verified artifacts.
6. Install from public PyPI by name and verify the version and SHA-256 hashes.

Never rebuild between verification and production upload: publish the same wheel and sdist bytes.

## 5. Recovery

PyPI releases cannot be replaced with different files at the same version. If metadata or artifacts
are wrong, stop, document the issue, increment the version, rebuild, and repeat verification. Yank a
bad release only when necessary and explain the reason in the release notes; yanking does not remove
copies already downloaded.
