# Opus model-governance adversarial review

Date: 2026-07-15  
Pull request: [Aman-CERP/amanerp-second-opinion#2](https://github.com/Aman-CERP/amanerp-second-opinion/pull/2)  
Scope: Opus-first quality profiles, auxiliary-model detection, Claude failure evidence, migration safety, and publication-readiness changes.

## Outcome

Agreement reached. No critical, high, or unresolved medium defect remains in the reviewed runtime or publication packet.

The installed **Second Opinion by AmanERP** plugin performed two critical PR reviews and one focused critical advisory. Every successful run used Claude Opus 4.8 at xhigh effort as the sole initialized, answering, and billed model. No Haiku or Sonnet use was observed. The explicit sensitive-input override was used only because the public test diff contains synthetic credential assignments.

## Independent review evidence

### Initial critical PR review

- Reviewed head: `1a0d3ee4d0d668d627e8882ffefd69d3bb09db2c`
- Base: `9ef4a7dc77270c4182fa9e10b0f33528ba04c497`
- Diff SHA-256: `4e506d31cb929e1b2dc88ea6b59d4c44d28acd02374a92087325095b86396629`
- Profile: `critical` (`opus`, xhigh, 10-turn/USD 10/1,500-second ceilings)
- Observed model: `claude-opus-4-8`; auxiliary models: none
- Usage: 2 turns; USD 1.566905 reported
- Verdict: `comment`; three medium findings, no critical/high finding

### Final critical PR review after fixes

- Reviewed head: `1ee84b486d8564709ef65d926164d09ad6b547a1`
- Base: `9ef4a7dc77270c4182fa9e10b0f33528ba04c497`
- Diff SHA-256: `a2f1ecebe5fb06297c72145b93645e5051d8616fae8522a7ea65c74514cbb6e7`
- Installed plugin: `0.2.0+codex.20260715024611`
- Profile: `critical` (`opus`, xhigh)
- Observed model: `claude-opus-4-8`; primary-family identifiers: only `claude-opus-4-8`; auxiliary models: none
- Usage: 2 turns; USD 1.5599015 reported
- Verdict: `comment`; one low-confidence conditional finding, no critical/high finding

### Focused agreement advisory

The final conditional finding was re-evaluated with the full current prompts, runner, injection tests, and PR-review report as context.

- Profile: `critical` (`opus`, xhigh)
- Observed model: `claude-opus-4-8`; auxiliary models: none
- Usage: 3 turns; USD 1.0086335 reported
- Recommendation confidence: high
- Decision: reject `prompt-boundary-marker-drift` as already mitigated and based on an invalid premise; make no prompt or marker-consistency change

## Finding dispositions

### F1 — Legacy artifact directory stopped being ignored

Accepted and fixed.

The rename initially replaced `.codex/claude-advisor/` with `.codex/amanerp-second-opinion/` in `.gitignore`, even though v0.1 artifacts are deliberately left in place. Both paths are now ignored, and `test_gitignore_preserves_current_and_legacy_run_artifacts` prevents regression. This eliminates an upgrade path that could expose prior local review artifacts to accidental staging.

### F2 — Claude 2.1.209 might lack `--name` or `--verbose`

Rejected after reproduction.

The retained local Claude Code 2.1.209 binary explicitly advertises both flags in `--help`. The declared minimum therefore remains compatible with the newly mandatory checks. The specification now records this direct probe. Claude 2.1.209 and 2.1.210 had already been live-verified to accept the hidden `--max-turns` control; 2.1.210 remains the highest behavior-tested release.

### F3 — Exact model-identifier equality was brittle

Accepted and fixed.

Policy enforcement now operates on the requested model family. Moving-alias, resolved, and dated identifiers within Opus are primary; Haiku, Sonnet, or any other family inside an Opus run remains a forbidden auxiliary and fails closed before result publication. Receipts expose `primary_family_models_observed`, and a regression proves distinct Opus identifiers across init, assistant, and billing telemetry are accepted while existing mismatch/auxiliary tests remain green.

### Final finding — Prompt boundary marker might have drifted

Rejected by agreement after full-context review.

Neither current prompt nor its byte-identical v0.1 predecessor names any delimiter. Both use the stronger delimiter-independent instruction that all stdin is untrusted and embedded instructions must never be followed. The runner passes the fixed prompt as a command argument and the JSON-serialized evidence only on stdin. The existing injection regression places a forged closing marker in an attacker-controlled question and proves that it remains JSON-escaped inside one outer envelope.

The focused Opus advisory concluded that adding a prompt-to-marker assertion would create a coupling that does not exist and would not improve the trust boundary. No change was made.

## Additional verification

- `make check` — 40 tests passed.
- `uvx ruff check plugins scripts tests` — passed.
- `uvx ruff format --check plugins scripts tests` — passed.
- Official OpenAI plugin validator — passed.
- Official OpenAI skill validators for both skills — passed.
- `make package` and `make package-repro-check` — passed.
- Final deterministic archive SHA-256: `45877ccf569e59d5592ecdb70185b0d9b3a1fb8a9a75f0aa9e17eb087ccc15d1`.
- The generated checksum sidecar passes `sha256sum --check`.
- Asset dimensions were inspected: icon 512x512, logo 1024x1024, screenshots 1600x1000.
- GitHub CI passed on Python 3.11, 3.12, 3.13, and 3.14 for head `1ee84b4`.
- The refreshed per-user install passed `doctor --require-gh` from Team A and Team L checkouts and is enabled for the A-L sibling workspaces on this workstation.
- A live critical advisory succeeded with Opus 4.8 as the sole model, 4 turns, USD 0.2083035, and schema-valid output. An intentionally under-provisioned Opus run failed visibly without downgrade.
- A separate no-tools probe produced attempted Bash-call prose but did not create its marker file, confirming that narration was not executed.

## Residual risks accepted

- A future Claude Code release that reintroduces a background Haiku/Sonnet call will fail closed until the behavior is reviewed; it will not silently publish a mixed-model result.
- Opus-first defaults cost more than Sonnet. This is intentional for critical reasoning; Sonnet remains an explicit, acknowledged standard profile only.
- Rejected/unverified Claude envelopes may remain in owner-only local artifacts for diagnosis. They are never published as validated results.

The review-record/changelog commit after `1ee84b4` is documentation-only and does not alter the reviewed runtime, plugin manifest, package contents, or submission assets.
