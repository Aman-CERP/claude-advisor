# V0.2.0 submission release notes

Initial OpenAI Plugin Directory submission for Second Opinion by AmanERP.

This release preserves the v0.1 read-only runtime boundary and introduces a neutral AmanERP product identity, two explicit-only skills (`independent-advisory` and `independent-pr-review`), complete public legal/support metadata, production listing assets, reviewer fixtures, and the required five positive and three negative test cases.

Both skills now default to an enforced Opus/high deep profile, while critical work uses Opus/xhigh. Sonnet is available only as an explicitly acknowledged standard profile and is never an automatic fallback. The runner suppresses auxiliary session-title generation, verifies the actual answering model from verbose Claude Code stream events, rejects mismatched or auxiliary model use, records normalized model-role usage in receipt schema 2, and preserves a redacted event summary when Claude exits non-zero.

The plugin requires local Codex, Python 3.11+, and the user's separately installed and authenticated Claude Code CLI. GitHub CLI is needed only for GitHub pull-request mode. It does not contain an MCP app or hosted service and is not available in ChatGPT web or Codex cloud.

Migration from v0.1 is intentionally explicit: remove `claude-advisor@aman-cerp`, refresh the renamed `Aman-CERP/amanerp-second-opinion` marketplace, then install `amanerp-second-opinion@amanerp`. Existing local v0.1 run artifacts are not moved or deleted.
