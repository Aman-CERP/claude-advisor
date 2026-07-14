# Security policy

## Supported versions

Security fixes are provided for the latest released minor version. Before v1.0, maintainers may ship a new minor or patch release depending on compatibility impact.

## Report a vulnerability

Use GitHub's private vulnerability reporting flow on the repository Security tab. Do not open a public issue for credential exposure, command execution, secret exfiltration, unsafe Claude permissions, artifact-permission failures, marketplace supply-chain risk, or a bypass of the sensitive-input controls.

Include affected version, operating system, reproduction steps using synthetic data, impact, and any proposed mitigation. Do not include real credentials or private repository content. Maintainers will acknowledge a valid report as soon as practical and coordinate remediation and disclosure.

## Security boundaries

Claude Advisor is local advisory software. It sends operator-selected content to Anthropic through the operator's Claude Code authentication. It does not provide a network service, share authentication, post to GitHub, execute Claude tools, or guarantee that model output is correct.

The runner gives child processes an explicit environment allowlist. V1 supports stored Anthropic subscription OAuth and documented first-party credential variables, but intentionally drops custom Anthropic endpoints, third-party cloud-provider modes, and unknown Claude configuration variables. Standard certificate and HTTP proxy variables remain available; organizations should review their workstation proxy and trust-store policy separately.

The secret scanner is a fail-closed guard for common high-confidence patterns, not a complete data-loss-prevention system. Operators remain responsible for approving context and complying with their organization's data policy.
