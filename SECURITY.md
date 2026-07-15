# Security policy

## Supported versions

Security fixes are provided for the latest released minor version. Before v1.0, maintainers may ship a new minor or patch release depending on compatibility impact.

## Report a vulnerability

Use GitHub's private vulnerability reporting flow on the repository Security tab. Do not open a public issue for credential exposure, command execution, secret exfiltration, unsafe Claude permissions, artifact-permission failures, marketplace supply-chain risk, or a bypass of the sensitive-input controls.

Include affected version, operating system, reproduction steps using synthetic data, impact, and any proposed mitigation. Do not include real credentials or private repository content. Maintainers will acknowledge a valid report as soon as practical and coordinate remediation and disclosure.

## Security boundaries

Second Opinion by AmanERP is local advisory software. It sends operator-selected content directly to Anthropic through the operator's Claude Code authentication. AmanERP does not receive that content. The plugin does not provide a network service, share authentication, post to GitHub, execute model tools, or guarantee that model output is correct.

The runner selects models through fixed quality profiles, verifies the initialized and answering model family from Claude Code's verbose stream, and rejects auxiliary model usage. This verifies model routing, not reasoning correctness. It never retries with a lower-quality model automatically. Non-zero exits retain only a bounded, redacted event summary rather than the raw failed stream.

The runner gives child processes an explicit environment allowlist. Version 0.2 supports stored Anthropic subscription OAuth and documented first-party credential variables, but intentionally drops custom Anthropic endpoints, third-party cloud-provider modes, and unknown Claude configuration variables. Standard certificate and HTTP proxy variables remain available; organizations should review their workstation proxy and trust-store policy separately.

Update discovery is off by default. `doctor --check-update` is an explicit,
read-only request through the authenticated GitHub CLI to the fixed public
AmanERP repository's latest stable release endpoint. It sends no review content
or usage telemetry, validates canonical release metadata, and cannot install,
remove, pin, or upgrade a plugin. Marketplace changes always remain a separate
operator action.

The secret scanner is a fail-closed guard for common high-confidence patterns, not a complete data-loss-prevention system. Operators remain responsible for approving context and complying with their organization's data policy.
