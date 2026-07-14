# OpenAI Plugin Directory reviewer guide

Second Opinion by AmanERP is a skills-only plugin for local Codex workflows. It invokes the reviewer's separately installed Claude Code CLI; it does not include an MCP app, hosted service, shared account, or AmanERP credential.

## Supported review environment

- Local Codex on macOS or Linux
- Python 3.11 or newer
- Claude Code 2.1.209 or newer for optional live inference
- GitHub CLI 2.x only for the public-PR test

The plugin is not functional in ChatGPT web, Codex cloud, mobile, or Windows-native environments because those surfaces cannot satisfy its documented local-process contract.

## Credential-free automated verification

From the repository root, run:

```bash
make check
make package
make package-repro-check
```

The test harness supplies fake `claude` and `gh` executables. It performs no inference, needs no account, and verifies command isolation, bounded subprocess behavior, secret screening, schema validation, receipts, public listing metadata, exact submission test counts, and deterministic packaging.

Validate the packaged plugin with OpenAI's current local validators:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/amanerp-second-opinion
python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/amanerp-second-opinion/skills/independent-advisory
python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/amanerp-second-opinion/skills/independent-pr-review
```

## Optional live verification

Use only the reviewer's own Claude Code account and applicable Anthropic terms. AmanERP does not provide or request a demo credential.

1. Install and authenticate Claude Code.
2. Run `make doctor`.
3. Run positive cases P1, P3, and P4 from `test-cases.json`.
4. Inspect `report.md`, `result.json`, and `receipt.json` in the printed run directory.
5. Confirm the receipt records read-only isolation controls and the expected source hash or PR object IDs.

Do not include private repository content, personal data, or credentials in reviewer prompts. The supplied fixtures are synthetic or public.

## Data path

User-selected question, diff, metadata, and context travel directly from the user's workstation to Anthropic through the user's Claude Code authentication. AmanERP operates no proxy and receives no prompt, diff, credential, model response, report, or receipt. Artifacts remain local unless the user independently shares them.

## Trademark and affiliation

Second Opinion by AmanERP is independently maintained and is not affiliated with or endorsed by Anthropic. Claude and Claude Code are referenced only to identify the separately installed dependency and data destination.
