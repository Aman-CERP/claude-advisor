# Changelog

All notable changes are documented here. The project follows Semantic Versioning.

## [Unreleased]

## [0.2.1] - 2026-07-15

### Added

- Precise `structured_output_retry_exhausted` failure classification with bounded event, subtype, correction, tool-attempt, usage, and model diagnostics that retain no partial structured response.
- An explicitly authorized two-attempt mode that retries only the same model after structured-output exhaustion, splits the aggregate budget, and preserves the aggregate parent timeout.
- Regression coverage for the observed six-response/five-correction failure shape and decision questions that previously embedded a competing output contract.
- Fail-closed failed-attempt model telemetry verification so an Opus retry cannot proceed after any observed downgrade or auxiliary-family use.
- Distinct `retry_blocked_model_unverified` classification for incomplete failed-attempt telemetry, preserving `model_policy_violation` for observed off-family use only.

### Changed

- Flattened the advisory schema to a stable closed envelope with one rich Markdown analysis field while preserving facts, options, controls, risks, estimate, and ADR reasoning requirements.
- Clarified that the question is the bounded decision, context is evidence, and the bundled JSON Schema is the sole machine-output contract.
- Bumped receipts to schema 3 with authorized attempts, attempts started, retry status, per-attempt budget, and safe attempt records.
- Tightened correction diagnostics to count only user events immediately following a StructuredOutput tool attempt instead of every user stream event.
- Added content-free attempt records for process-level timeout, start, I/O, and stream-limit failures so every started retry is auditable; correction matching now survives intervening non-participant system events.
- Made `retry_triggered` mean an actually started second process; aggregate-deadline preemption now leaves it false and records `retry_preempted_reason: aggregate_timeout`.
- Added a recovered-attempt regression proving the normal success-path model gate rejects a Haiku answering model after an Opus structured-output failure.
- Completed the every-started-attempt invariant for exit-zero responses rejected by stream parsing, model policy, usage, ceiling, structured-output extraction, or local schema validation.

### Migration

- Advisory `result.json` is intentionally schema-breaking: nested `facts`, `assumptions`, `options`, `recommendation`, and `open_questions` move into the Markdown `analysis` field, with top-level `verdict`, `confidence`, and `conditions_that_change_it`. Consumers must update before reading v0.2.1 advisory results.
- Two-attempt mode replays an identical request and halves the configured aggregate budget per attempt; it is intended only for explicitly authorized recovery from a transient structured-output failure.

## [0.2.0] - 2026-07-14

### Added

- OpenAI plugin-directory submission packet with listing copy, reviewer guidance, policy attestations, release notes, and exactly five positive plus three negative reviewer cases.
- AmanERP-owned public website, support, privacy, and terms URL contracts.
- AmanERP brand assets and two product-workflow screenshots for the plugin listing.
- Public issue forms, support and conduct guidance, pull-request template, and deterministic tag-release automation.
- Explicit, read-only `doctor --check-update` release discovery with strict stable-release metadata validation and no installation side effect.
- A release-contract validator, documented rollback policy, and loopback-only isolated Codex Git-marketplace upgrade smoke.

### Changed

- Renamed the public repository and package to `amanerp-second-opinion` and the listing to **Second Opinion by AmanERP**.
- Renamed the explicit skills to `$independent-advisory` and `$independent-pr-review`.
- Moved default artifacts to `.codex/amanerp-second-opinion/runs/` and renamed the runner to `second_opinion.py`.
- Added an explicit Anthropic non-affiliation notice and surface-availability disclosure.
- Replaced arbitrary model/effort overrides with auditable `standard`, `deep`, and `critical` quality profiles. Both skills now default to Opus/high, critical work uses Opus/xhigh, and Sonnet requires an explicitly acknowledged standard run.
- Switched analysis capture to verified verbose stream JSON while retaining the compact terminal response artifact. Receipts now distinguish requested, answering, and auxiliary models with normalized per-model usage.
- Added deterministic session names to suppress Claude Code's auxiliary Haiku title-generation call and fail closed on any unapproved answering or auxiliary model.
- Classified moving-alias and dated identifiers within the requested model family as primary while continuing to reject every different-family auxiliary model.
- Added redacted `claude-failure.json` diagnostics for non-zero Claude exits and prohibited automatic model fallback after failure.
- Replaced remove/re-add update guidance with the supported Git-marketplace upgrade command, a fresh-task boundary, and a clear separation between GitHub releases and reviewed OpenAI Plugin Directory updates.
- Raised the minimum Claude Code version to 2.1.210, the release behavior-tested for mandatory verbose stream-model telemetry, and redacted provider failure text before applying the diagnostic length bound.

### Migration

- Remove `claude-advisor@aman-cerp` before installing `amanerp-second-opinion@amanerp`.
- Existing `.codex/claude-advisor/` artifacts remain untouched.
- The legacy artifact directory remains gitignored alongside the new path to prevent an upgrade from exposing prior review data to accidental staging.

## [0.1.0] - 2026-07-14

### Added

- Explicit `$claude-advisory` and `$claude-pr-review` Codex skills.
- Isolated, no-tools Claude Code execution with structured output, bounded inputs/time, and fail-closed reported turn/cost breach detection.
- Read-only GitHub PR snapshot capture with post-diff head revision verification.
- Sensitive-input screening, local schema validation, redacted diagnostics, and owner-only run artifacts.
- Deterministic release packaging, public CI, and Codex marketplace distribution.

[Unreleased]: https://github.com/Aman-CERP/amanerp-second-opinion/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/Aman-CERP/amanerp-second-opinion/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Aman-CERP/amanerp-second-opinion/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Aman-CERP/amanerp-second-opinion/releases/tag/v0.1.0
