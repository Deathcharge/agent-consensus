# Security policy

## Supported version

Security fixes are currently applied to the latest 0.2.x release line. This repository has not yet
published a package release; source users should track the `main` branch and review changes.

## Reporting

Do not include credentials, proprietary prompts, model responses, or personal data in a public issue.
Use GitHub's private vulnerability reporting feature for the repository if it is enabled. Otherwise,
email [support@samsarix.com](mailto:support@samsarix.com) with the repository name, affected version,
impact, reproduction steps, and any suggested mitigation before disclosing details publicly.

No response SLA is promised because the repository does not document a staffed security team.
Do not send secrets or live customer data in the initial report.

## Trust model

- Participant adapters are application-supplied code and execute with the host process's authority.
- The library does not authenticate participant identity; uniqueness is a local name invariant.
- `choice`, `content`, and metadata are untrusted adapter output.
- Custom normalizers are decision policy and can merge choices incorrectly.
- Returned results may contain sensitive response content and metadata.
- Token allocation is a request to adapters, not enforcement by an external provider.

## Secure integration guidance

- Keep provider credentials in the host application's secret store or environment, never in source.
- Give adapters the least network and data access they need.
- Use a closed decision vocabulary and validate it in the adapter.
- Set quorum and threshold to fail closed for the impact of the decision.
- Use `DecisionPolicy.allowed_choices` at an operational boundary so an adapter cannot introduce an
  unreviewed choice, and treat only `DecisionStatus.PASSED` as permission to proceed.
- Configure required participants and vetoes deliberately, but do not confuse participant names
  with authenticated identity or independent human approval.
- Produce `ConsensusResult` through `evaluate_votes` or `ConsensusEngine`; do not reconstruct one
  from untrusted serialized fields and treat it as verified evidence.
- Redact results before logging or exporting them.
- Add bounded, idempotent retries only when the provider operation is safe to repeat.
- Use non-blocking provider clients; do not run blocking network or model calls on the event loop.
- Apply authorization and enforce the verdict in the host system before performing a protected
  action. The policy evaluator is not an authorization service.
- Do not treat this in-process tally as a Byzantine-fault-tolerant approval mechanism.

The core package makes no network calls, opens no files, launches no subprocesses, and has no runtime
dependencies.
