# Changelog

All notable changes are documented here. The project follows Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2026-07-14

### Added

- OpenAI plugin-directory submission packet with listing copy, reviewer guidance, policy attestations, release notes, and exactly five positive plus three negative reviewer cases.
- AmanERP-owned public website, support, privacy, and terms URL contracts.
- AmanERP brand assets and two product-workflow screenshots for the plugin listing.
- Public issue forms, support and conduct guidance, pull-request template, and deterministic tag-release automation.

### Changed

- Renamed the public repository and package to `amanerp-second-opinion` and the listing to **Second Opinion by AmanERP**.
- Renamed the explicit skills to `$independent-advisory` and `$independent-pr-review`.
- Moved default artifacts to `.codex/amanerp-second-opinion/runs/` and renamed the runner to `second_opinion.py`.
- Added an explicit Anthropic non-affiliation notice and surface-availability disclosure.

### Migration

- Remove `claude-advisor@aman-cerp` before installing `amanerp-second-opinion@amanerp`.
- Existing `.codex/claude-advisor/` artifacts remain untouched.

## [0.1.0] - 2026-07-14

### Added

- Explicit `$claude-advisory` and `$claude-pr-review` Codex skills.
- Isolated, no-tools Claude Code execution with structured output, bounded inputs/time, and fail-closed reported turn/cost breach detection.
- Read-only GitHub PR snapshot capture with post-diff head revision verification.
- Sensitive-input screening, local schema validation, redacted diagnostics, and owner-only run artifacts.
- Deterministic release packaging, public CI, and Codex marketplace distribution.

[Unreleased]: https://github.com/Aman-CERP/amanerp-second-opinion/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Aman-CERP/amanerp-second-opinion/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Aman-CERP/amanerp-second-opinion/releases/tag/v0.1.0
