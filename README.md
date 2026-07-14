# Second Opinion by AmanERP

Second Opinion by AmanERP is an open-source Codex plugin for obtaining a bounded independent engineering opinion or adversarial pull-request review through a user's own locally authenticated Claude Code CLI.

The plugin is deliberately narrow. Invocation is explicit, selected content is disclosed before transmission, model tools and session persistence are disabled, child processes are resource-bounded, and every completed run creates a structured result and provenance receipt. It never edits code, posts to GitHub, or makes the final decision for the user.

Second Opinion by AmanERP is an independent project. AmanERP is not affiliated with or endorsed by Anthropic. Claude and Claude Code are trademarks of Anthropic PBC.

## What it provides

- `$independent-advisory` compares options and returns a structured recommendation for a bounded decision.
- `$independent-pr-review` reviews a GitHub pull request or supplied diff with prioritized, evidence-oriented findings.
- A dependency-free Python runner enforces bounded inputs and child streams, stable exit codes, sensitive-input screening, a minimal child environment, local schema validation, and owner-only artifacts.
- A portable Codex marketplace entry can be installed once per local Codex user and used from every workspace on that machine.

## Prerequisites

- macOS or Linux.
- Python 3.11 or newer.
- A Codex release with plugin marketplace support.
- Claude Code 2.1.209 or newer, separately installed and authenticated by the user. Version 2.1.209 is the currently behavior-tested isolation baseline; later versions produce a warning until their no-tools behavior is reverified.
- GitHub CLI 2.x, authenticated locally, only for GitHub pull-request mode.

Install and authenticate Claude Code using [Anthropic's setup guide](https://docs.anthropic.com/en/docs/claude-code/getting-started). Every user must use their own Claude account or an organization-approved first-party Anthropic credential. The plugin does not share credentials, proxy requests, or support custom model gateways and cloud-provider modes.

## Install in Codex

```bash
codex plugin marketplace add Aman-CERP/amanerp-second-opinion
codex plugin add amanerp-second-opinion@amanerp
```

Start a fresh Codex task after installation so the skills are discovered, then verify:

```bash
codex plugin list --json
```

Installation is global for the current local Codex user. It therefore covers AmanERP checkouts A–L on the same workstation. Teammates on another machine run the two installation commands once and authenticate their own Claude CLI.

## Use from Codex

Invoke one skill explicitly:

```text
Use $independent-advisory to obtain a second opinion on this architecture decision.
```

```text
Use $independent-pr-review to adversarially review PR 123 in owner/repository.
```

Neither skill can be invoked implicitly. Before execution, Codex tells the user which selected content will be sent to Anthropic. The result is advisory: Codex or a human reviewer must reproduce every material finding against the original evidence.

## Use the runner directly

From a source checkout:

```bash
RUNNER="$(pwd)/plugins/amanerp-second-opinion/scripts/second_opinion.py"
python3 "$RUNNER" doctor --require-gh
```

Decision advisory:

```bash
python3 "$RUNNER" advisory \
  --question-file /absolute/path/to/question.md \
  --context-file /absolute/path/to/approved-context.md
```

GitHub pull-request review:

```bash
python3 "$RUNNER" pr-review \
  --pr 123 \
  --repo owner/repository \
  --critical
```

Supplied-diff review:

```bash
python3 "$RUNNER" pr-review \
  --diff-file /absolute/path/to/change.diff \
  --source-label "staged diff at commit abc123"
```

The runner writes one compact JSON summary to stdout and diagnostics to stderr. Stable non-zero exit codes distinguish invalid input, missing dependencies, authentication failure, model failure, timeout, invalid structured output, GitHub read failure, and internal error.

## Data flow and artifacts

```text
Codex -> local runner -> local Claude Code -> Anthropic
                    \-> local result + provenance receipt
```

User-selected questions, diffs, pull-request metadata, and context files are sent directly from the user's workstation to Anthropic through the user's Claude Code authentication. AmanERP operates no proxy and receives no prompts, credentials, diffs, responses, or usage telemetry.

By default, runs are stored under `.codex/amanerp-second-opinion/runs/` in the current workspace:

- `request.json` — sanitized configuration and source metadata;
- `input.sha256` — hash of the exact prompt and untrusted input bundle;
- `claude-response.json` — the model's JSON envelope;
- `result.json` — the locally schema-validated result;
- `report.md` — deterministic human-readable rendering;
- `receipt.json` — versions, revisions, hashes, limits, controls, outcome, and safe usage metadata;
- `stderr.log` — redacted child-process diagnostics.

Run files use owner-only permissions where supported. Input hashes prove identity, not content; preserve an approved source snapshot separately when content-level auditability is required.

## Security posture

The runner uses Claude Code safe mode, an empty tool list, Chrome disabled, and session persistence disabled. It screens likely secret-bearing paths and high-confidence credential patterns, but it is not a complete data-loss-prevention system. Review and minimize every input before sending it. An explicit sensitive-input override is recorded in the receipt.

Claude and GitHub child processes receive separate minimal environment allowlists. Failed, timed-out, or over-limit children are terminated as a POSIX process group so descendants cannot outlive the run.

Do not use personal Claude OAuth as a backend for other users. This is local software: every operator authenticates their own CLI. A hosted or shared service would require a separate API-based architecture, terms review, privacy assessment, and threat model.

See [SECURITY.md](SECURITY.md), [the full specification](docs/specification.md), and [the publication submission packet](submission/checklist.md).

## Upgrade from v0.1

Version 0.2 uses a new neutral public identity and skill names. Remove the retired package before installation:

```bash
codex plugin remove claude-advisor@aman-cerp
codex plugin marketplace remove aman-cerp
codex plugin marketplace add Aman-CERP/amanerp-second-opinion
codex plugin add amanerp-second-opinion@amanerp
```

The old GitHub URL redirects to the renamed repository. Existing `.codex/claude-advisor/` artifacts are not moved or deleted automatically.

## Update or remove

Refresh the marketplace snapshot, then reinstall:

```bash
codex plugin marketplace remove amanerp
codex plugin marketplace add Aman-CERP/amanerp-second-opinion
codex plugin remove amanerp-second-opinion@amanerp
codex plugin add amanerp-second-opinion@amanerp
```

To uninstall completely:

```bash
codex plugin remove amanerp-second-opinion@amanerp
codex plugin marketplace remove amanerp
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
