# Security policy

## Supported version

Security fixes are currently applied to the latest 0.2.x release line. This repository has not yet
published a package release; source users should track the `main` branch and review changes.

## Reporting

Do not include credentials, proprietary prompts, model responses, or personal data in a public issue.
Use GitHub's private vulnerability reporting feature for the repository if it is enabled. Otherwise,
contact the repository owner through a private channel listed on the owner's GitHub profile before
disclosing details publicly.

No response SLA is promised because the repository does not document a staffed security team.

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
- Redact results before logging or exporting them.
- Add bounded, idempotent retries only when the provider operation is safe to repeat.
- Use non-blocking provider clients; do not run blocking network or model calls on the event loop.
- Apply authorization in the host system before acting on a consensus result.
- Do not treat this in-process tally as a Byzantine-fault-tolerant approval mechanism.

The core package makes no network calls, opens no files, launches no subprocesses, and has no runtime
dependencies.
