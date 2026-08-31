# Release procedure

Releases are owner-gated. CI retains temporary candidate artifacts for review; it does not publish
packages. Creating a GitHub release, registering a package index publisher, or uploading to
TestPyPI/PyPI requires an authorized Samsarix release owner.

## 1. Decide the release identity

- Confirm `agent-consensus` is the intended PyPI distribution name and the owner controls it.
- Make the explicit license choice recorded in [LICENSING.md](LICENSING.md).
- Choose a version using semantic versioning.
- Keep that version synchronized in `pyproject.toml`, `agent_consensus/__init__.py`,
  `CITATION.cff`, and `CHANGELOG.md`.
- Confirm current-facing author, maintainer, support, repository, and project URLs.

## 2. Verify the candidate

From a clean, committed checkout with the pinned contributor toolchain installed and a fresh,
empty `dist` directory (do not mix old candidates):

To review an existing CI candidate, skip rebuilding and use the download subsection below instead.

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy agent_consensus
python -m mypy --strict scripts/release_bundle.py
python -m pytest
python -m pytest -o addopts= tests/test_release_bundle.py --cov=scripts.release_bundle --cov-branch --cov-report=term-missing --cov-fail-under=95
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

### Review the exact CI candidate without rebuilding

After all quality, matrix and installed-package checks pass, `main` push CI creates a receipt and
retains one GitHub Actions artifact named `candidate-COMMIT-RUN_ID-RUN_ATTEMPT` for seven days.
It contains exactly the wheel, sdist and `release-manifest.json`. Pull-request runs do not upload
candidates. The workflow uses read-only repository permissions and a commit-pinned upload action;
it has no publisher credentials or OIDC publishing permission.

1. Select a successful **CI** push run for the intended full `main` commit in this repository.
   Check its event, branch, head, attempt, conclusion, job results and logs, not just an artifact name.
2. Copy the full commit SHA, artifact name and the `Manifest SHA-256: ...` value from that run's
   **Create and verify candidate receipt** log. The receipt digest is different from GitHub's ZIP
   artifact digest. Obtain it from the trusted run, not by hashing the downloaded receipt.
3. Download to a new, empty directory, then verify with this script from a trusted checkout. The
   following commands work in Bash and PowerShell when placeholders are replaced with those values:

```bash
gh run view RUN_ID --repo Deathcharge/agent-consensus --json workflowName,event,headBranch,headSha,attempt,conclusion,url,jobs
gh run view RUN_ID --repo Deathcharge/agent-consensus --attempt RUN_ATTEMPT --log
gh run download RUN_ID --repo Deathcharge/agent-consensus --name candidate-COMMIT-RUN_ID-RUN_ATTEMPT --dir candidate-download
python -I scripts/release_bundle.py verify --dist candidate-download --source-commit COMMIT --manifest-sha256 TRUSTED_MANIFEST_SHA256
```

Require exit code 0 and the expected `Verified agent-consensus VERSION at COMMIT` output before
installing anything. Any mismatch, missing/extra file, malformed receipt, symbolic link or oversized file
fails with a nonzero exit code. The tool requires a 40-character lowercase Git commit SHA and
64-character lowercase receipt SHA-256. Each distribution is limited to 100 MiB; the receipt is
limited to 64 KiB. It reads files without extracting or executing package contents. It intentionally
supports this project's pure-Python wheel/sdist filenames, not arbitrary package bundles.

Then install that exact wheel in a new environment and repeat the isolated checks and examples
above, using trusted scripts from the selected revision. Keep the candidate directory unchanged
between verification, installation and any later upload. Upload **only the wheel and sdist** to a
package index, never `release-manifest.json` or a wildcard that also selects it.

Receipts bind bytes to a **stated** commit; they do not prove the build came from that commit, certify
package contents or license rights, or replace signatures, attestations, an SBOM or CI review. Anyone
able to replace both files and your trusted digest can forge a receipt. Verification assumes trusted
local tools, CI/account access and no concurrent modification of the selected directory.

For a locally built candidate, run the following only after the preceding checks, from a clean,
committed checkout. Record the printed digest separately and use it in the verification command:

```bash
git rev-parse HEAD
python -I scripts/release_bundle.py create --dist dist --source-commit COMMIT
python -I scripts/release_bundle.py verify --dist dist --source-commit COMMIT --manifest-sha256 TRUSTED_MANIFEST_SHA256
```

Creation refuses existing receipts and extra files; it never overwrites a candidate's receipt.
It does not run tests or inspect Git state for you. If the seven-day artifact has expired,
prepare and verify a new candidate instead of claiming newly built bytes are the original files.
An owner can retain an approved copy before expiry under their own retention policy. GitHub artifact
storage uses the repository's existing Actions allowance; this workflow does not change billing.

This follows [PyPA's separation of build artifacts from publication](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
See [GitHub artifact retention and download behavior](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)
for access and expiry rules. GitHub's archive-integrity check is separate from the fail-closed receipt
verification above.

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
