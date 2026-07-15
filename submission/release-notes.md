# V0.2.1 submission release notes

Publication-candidate patch for Second Opinion by AmanERP. OpenAI submission remains intentionally deferred.

Version 0.2.1 hardens advisory reliability after a real critical Opus run exhausted Claude Code's internal structured-output retries. The advisory schema is now a shallow closed envelope with one Markdown analysis field, the trusted prompt makes the output-contract boundary explicit, and receipt schema 3 records safe failure diagnostics and attempt metadata without retaining partial failed output.

The advisory `result.json` shape is intentionally breaking for machine consumers: the former nested facts, assumptions, options, recommendation, and open-questions structures are represented in Markdown `analysis`, with verdict, confidence, risks, change conditions, and validation steps remaining top-level. Update consumers before adopting v0.2.1.

One attempt remains the default. A user may explicitly authorize two attempts with `--structured-output-attempts 2 --acknowledge-retry-cost`; only Claude's structured-output retry-exhausted outcome is eligible, and the second attempt preserves the exact model, effort, input, prompt, schema, tool isolation, and turn ceiling within aggregate time and budget limits. There is no cross-model fallback.

This release preserves the v0.1 read-only runtime boundary and introduces a neutral AmanERP product identity, two explicit-only skills (`independent-advisory` and `independent-pr-review`), complete public legal/support metadata, production listing assets, reviewer fixtures, and the required five positive and three negative test cases.

Both skills default to an enforced Opus/high deep profile, while critical work uses Opus/xhigh. Sonnet is available only as an explicitly acknowledged standard profile and is never an automatic fallback. The runner suppresses auxiliary session-title generation, verifies the actual answering model from verbose Claude Code stream events, rejects mismatched or auxiliary model use, records normalized model-role and attempt usage in receipt schema 3, and preserves a redacted event summary when Claude exits non-zero.

Update discovery is explicit and off by default. An operator may run `doctor --check-update` to read the latest stable GitHub release through their authenticated GitHub CLI; the command sends no review content or telemetry and never changes plugin state. Git-marketplace updates use `codex plugin marketplace upgrade amanerp` followed by a fresh Codex task. Public-directory revisions remain separately reviewed update submissions.

The plugin requires local Codex, Python 3.11+, and the user's separately installed and authenticated Claude Code 2.1.210+ CLI. Version 2.1.210 is the behavior-tested baseline for mandatory verbose stream-model telemetry. GitHub CLI is needed only for GitHub pull-request mode or the optional explicit update check. It does not contain an MCP app or hosted service and is not available in ChatGPT web or Codex cloud.

Migration from v0.1 is intentionally explicit: remove `claude-advisor@aman-cerp`, refresh the renamed `Aman-CERP/amanerp-second-opinion` marketplace, then install `amanerp-second-opinion@amanerp`. Existing local v0.1 run artifacts are not moved or deleted.
