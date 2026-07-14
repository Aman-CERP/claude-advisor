# Claude Advisor

Claude Advisor is an open-source Codex plugin for asking a locally authenticated Claude Code CLI for an independent engineering opinion or adversarial pull-request review.

It is deliberately narrow: invocation is explicit, Claude receives a bounded context bundle, Claude customizations and tools are disabled, no session is persisted, and every run produces a structured result plus a provenance receipt. The plugin never edits code or posts to GitHub.

## What it provides

- `$claude-advisory` — compare options and obtain a structured recommendation for a bounded decision.
- `$claude-pr-review` — review a GitHub PR or supplied diff with prioritized, evidence-oriented findings.
- A dependency-free Python runner with stable exit codes, bounded inputs and child-process streams, reported turn/cost breach detection, secret screening, an explicit child-environment allowlist, and owner-only artifacts.
- A public Codex marketplace that can be installed once per local Codex user and used from every workspace on that machine.

## Prerequisites

- macOS or Linux.
- Python 3.11 or newer.
- A Codex release with plugin marketplace support. V0.1.0 was developed with Codex CLI 0.144.1.
- Claude Code 2.1.209 or newer, authenticated locally. V0.1.0 behavior-tested the isolation controls on 2.1.209; newer versions produce a warning until their no-tools behavior is reverified.
- GitHub CLI 2.x, authenticated locally, only for GitHub PR mode.

Install and authenticate Claude Code using [Anthropic's setup guide](https://docs.anthropic.com/en/docs/claude-code/getting-started). Each user must use their own Claude account or organization-approved first-party Anthropic credential. V1 intentionally does not pass custom base URLs or Bedrock, Vertex, Foundry, or Mantle provider configuration to the child.

## Install in Codex

```bash
codex plugin marketplace add Aman-CERP/claude-advisor
codex plugin add claude-advisor@aman-cerp
```

Start a fresh Codex task after installation so the new skills are discovered. Verify:

```bash
codex plugin list --json
```

Installation is global for the current local Codex user. It therefore covers AmanERP checkouts A–L on the same workstation. Teammates on different machines run the two installation commands once and authenticate their own Claude CLI; the project does not share credentials or proxy requests.

## Use from Codex

Invoke a skill explicitly:

```text
Use $claude-advisory to ask Claude for an independent opinion on this architecture decision.
```

```text
Use $claude-pr-review to ask Claude to adversarially review PR 123 in owner/repository.
```

Neither skill can be invoked implicitly. Claude's output is advisory: Codex or the human reviewer must reproduce material findings against the original evidence.

## Use the runner directly

From a source checkout:

```bash
RUNNER="$(pwd)/plugins/claude-advisor/scripts/claude_advisor.py"
python3 "$RUNNER" doctor --require-gh
```

Decision advisory:

```bash
python3 "$RUNNER" advisory \
  --question-file /absolute/path/to/question.md \
  --context-file /absolute/path/to/approved-context.md
```

GitHub PR review:

```bash
python3 "$RUNNER" pr-review \
  --pr 123 \
  --repo owner/repository \
  --critical
```

Supplied diff:

```bash
python3 "$RUNNER" pr-review \
  --diff-file /absolute/path/to/change.diff \
  --source-label "staged diff at commit abc123"
```

The runner writes one JSON summary to stdout and diagnostics to stderr. Stable non-zero codes distinguish invalid input, missing dependencies, authentication, Claude failure, timeout, invalid structured output, GitHub read failure, and internal error.

## Run artifacts

By default, runs are stored under `.codex/claude-advisor/runs/` in the current workspace:

- `request.json` — sanitized configuration and source metadata;
- `input.sha256` — hash of the exact prompt plus untrusted input bundle;
- `claude-response.json` — Claude's JSON envelope;
- `result.json` — locally schema-validated result;
- `report.md` — deterministic human-readable rendering;
- `receipt.json` — versions, revisions, hashes, limits, controls, outcome, and safe usage metadata;
- `stderr.log` — redacted child-process diagnostics.

Run files use owner-only permissions where supported. Input hashes prove identity, not content; retain an approved source snapshot separately when content-level auditability is required.

## Security and data disclosure

Selected questions, diffs, metadata, and context files are sent to Anthropic through the local Claude Code authentication. The plugin itself sends no telemetry and stores no credentials.

The runner uses `--safe-mode`, an empty tool list, `--no-chrome`, and `--no-session-persistence`. It screens likely secret-bearing paths and high-confidence credential patterns, but this is not a complete DLP system. Review context before sending it. An explicit `--allow-sensitive-input` override is recorded in the receipt.

Each child receives a minimal purpose-specific environment: Claude receives only Anthropic credentials, while `gh` receives only GitHub credentials. Stored subscription OAuth, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, and `CLAUDE_CODE_OAUTH_TOKEN` are supported; endpoint overrides, cloud-provider modes, and unknown Claude configuration variables are removed. Standard certificate and HTTP proxy variables are retained for normal network compatibility. Failed or over-limit children are terminated as a POSIX process group so descendants cannot outlive the run.

Do not use personal Claude OAuth as a backend for other users. This project is a local tool: every operator authenticates their own CLI. A future hosted service would require a separate API-based architecture, terms review, threat model, and specification.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [the full specification](docs/specification.md) for trust boundaries and acceptance criteria.

## Update or remove

Refresh the marketplace snapshot, then reinstall using the current Codex marketplace commands:

```bash
codex plugin marketplace remove aman-cerp
codex plugin marketplace add Aman-CERP/claude-advisor
codex plugin remove claude-advisor@aman-cerp
codex plugin add claude-advisor@aman-cerp
```

To uninstall completely:

```bash
codex plugin remove claude-advisor@aman-cerp
codex plugin marketplace remove aman-cerp
```

Removing the plugin does not delete local run artifacts or alter Claude credentials.

## Develop and package

```bash
make check
make package
make package-repro-check
```

The runtime has no third-party Python dependency. Release archives use stored ZIP entries with normalized metadata for cross-toolchain reproducibility.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [the implementation plan](docs/implementation-plan.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).
