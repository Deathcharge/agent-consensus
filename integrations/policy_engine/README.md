# Installed policy-engine consumer

This optional, separately packaged reference consumer combines a **real** Samsarix Policy Engine
decision with operational readiness before a host-owned release action. It imports public APIs from
installed wheels, not sibling checkout paths. The example performs no deployment, networking,
credential access or paid calls. Its test operation only records invocation in memory.

The core `agent-consensus` wheel does not include or depend on this consumer or the producer.
The consumer package is marked `Private :: Do Not Upload`; do not publish it as a product.

## Contract and support boundary

- Python 3.11–3.14 (the producer's supported range; the core still supports Python 3.10).
- `agent-consensus` 0.2.0 with the numeric hardening in PR #14 or later.
- `samsarix-policy-engine` 0.1.0 at
  [`6e51f2585fa4412037f4f5458d313cb26ad3d59d`](https://github.com/Deathcharge/policy-engine/commit/6e51f2585fa4412037f4f5458d313cb26ad3d59d).
- Consumer contract v1 is stored in `consensus_policy_consumer/contract-v1.json` and included in its
  wheel. It records versions, producer revision, policy content/digest, requests and expected
  enforcement results. Producer `policy_version` means **schema version**, not a release counter.

Support level: maintained reference integration, verified against the pinned producer commit. It is
not evidence of deployed production adoption, a general compatibility promise, or authenticated
human approval. Version metadata alone does not prove artifact provenance: use the pinned source
revision and record the hashes of the wheels actually built and installed.

The producer has its own [BUSL-1.1 terms at that revision](https://github.com/Deathcharge/policy-engine/blob/6e51f2585fa4412037f4f5458d313cb26ad3d59d/LICENSE),
including production-use conditions. This non-production verification does not grant production
rights or change either project's license. No producer source is vendored or relicensed here.

## Build and verify

From the `agent-consensus` checkout, using a contributor environment installed from
`requirements-dev.txt`, clone the optional producer into a dedicated directory:

```bash
git clone https://github.com/Deathcharge/policy-engine.git .contract-producer
git -C .contract-producer checkout --detach 6e51f2585fa4412037f4f5458d313cb26ad3d59d
git -C .contract-producer rev-parse HEAD
python -m build --outdir .contract-artifacts/consensus
python -m build .contract-producer --outdir .contract-artifacts/producer
python -m build integrations/policy_engine --outdir .contract-artifacts/consumer
python -m venv .contract-venv
```

Confirm the printed revision exactly matches the pin. These builds may download build tooling;
evaluation itself is offline. Use fresh artifact directories, and never reuse stale wheels by name.
Activate `.contract-venv` using `.contract-venv/Scripts/Activate.ps1` on Windows PowerShell or
`source .contract-venv/bin/activate` on Linux/macOS. Then install only the three local wheels:

```bash
python -m pip install --no-index --no-deps .contract-artifacts/consensus/agent_consensus-0.2.0-py3-none-any.whl .contract-artifacts/producer/samsarix_policy_engine-0.1.0-py3-none-any.whl .contract-artifacts/consumer/agent_consensus_policy_consumer_example-0.0.0-py3-none-any.whl
python -m pip check
python -I integrations/policy_engine/verify.py
python -I scripts/check_installed.py
```

The verifier rejects checkout imports, checks installed versions and the golden source-policy
digest, and runs the versioned cases against the real producer. Separate fault-injection checks
exercise source errors, schema/identity/digest drift, immutable request binding and operation errors.
The dedicated CI workflow repeats this on Windows Python 3.11 and Linux Python 3.14. The core CI
remains independent of producer access.

## Enforcement example

```python
from consensus_policy_consumer import run_release_gate
from policy_engine import PolicyEngine

# policy_document, request and expected_digest are reviewed host configuration.
# operation receives the same immutable request that the policy evaluated.
run = await run_release_gate(
    PolicyEngine(policy_document),
    request,
    readiness="ready",
    operation=operation,
    expected_policy_digest=expected_digest,
)
print(run.audit)  # explicit allowlist; no original request/context or source reason
```

Authorization has weight 1 and readiness has weight 3. An explicit source deny still vetoes a
weighted readiness majority. Both participants are required. Invalid or drifted source evidence,
missing request identity, unknown readiness and producer failures prevent the operation. A valid
readiness `hold` also prevents it. Only `passed` reaches the operation.

The request is validated and frozen before asynchronous collection, and the operation receives that
same snapshot. Do not substitute mutable original attributes when implementing the real effect.
The host remains responsible for trustworthy request attributes, identity, policy provenance,
current readiness, action binding, idempotency, cancellation and bounded I/O. A policy digest is not
a signature. The local synchronous producer is bounded by its own input limits but is not preempted
by an asyncio timeout while executing; this is not an adapter for unbounded blocking services.

`GateRun.audit` deliberately excludes full source reasons, context and the original prompt.
Allowlisted request and policy identifiers can still be sensitive; the host chooses access and
retention. Nothing is persisted automatically. Operation exceptions propagate without retries or a
fabricated success receipt; external effect recovery belongs to the host.

## Updating or adopting the contract

1. Review producer source, license and compatibility before changing the revision/version pin.
2. Update the fixture and CI checkout ref together; do not overwrite a golden digest just to make a
   test pass. Review the policy change and expected deny behavior first.
3. Rebuild all three wheels, rerun source/consumer checks, and record commit IDs and artifact hashes.
4. In a real consuming application, bind its actual operation and add consumer-owned tests for
   authentication, resource identity, idempotency and rollback before deployment.
5. Roll back by pinning the previous verified artifacts and contract as a set. Do not reuse a verdict
   after changing request, policy, readiness, or evaluator version.

The adoption milestone proven here is installed-package contract compatibility and enforcement in
a local consumer. The next external milestone is a real application's own CI exercising its actual
enforcement point; no usage counts, deployment claims or user demand are inferred from this example.
