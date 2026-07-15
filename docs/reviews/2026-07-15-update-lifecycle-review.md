# Update lifecycle adversarial review

Date: 2026-07-15

PR: [Aman-CERP/amanerp-second-opinion#2](https://github.com/Aman-CERP/amanerp-second-opinion/pull/2)

Reviewer: the cache-safe locally installed `amanerp-second-opinion@amanerp`
plugin using Claude Code 2.1.210, the `critical` quality profile, Opus/xhigh,
model-identity enforcement, no tools, and no session persistence.

## Scope

The review covered the complete publication-readiness PR after adding an explicit
update lifecycle. The update change adds opt-in `doctor --check-update`, a fixed
`github.com` stable-release lookup, no implicit polling or installation,
Git-marketplace update and rollback guidance, a release-contract validator, and
a loopback-only marketplace-upgrade smoke in an isolated `CODEX_HOME`.

The PR contains synthetic credential-like fixtures. Every live review therefore
used the explicit sensitive-input override; the receipt records that decision.
The runner remained read-only and did not post a GitHub review or mutate the PR.

## Review pass 1 — update implementation

Immutable head: `7d4f2a04e482499bb042386736cf9eff4ded437d`

Claude found no critical, high, or medium issue. It reported two low findings:

1. The release workflow selected ZIP and checksum assets with broad globs.
2. The Codex-only marketplace smoke appeared in the routine contributor workflow.

Both were accepted. Commit `5dffa240dd6033d93c44ac68d966dffc9343036c`
uses the tag-derived exact artifact names and keeps the smoke only as a named
manual release gate. A residual diagnostic concern was also accepted: the
explicit update path now authenticates specifically against `github.com`, while
ordinary enterprise-host PR review keeps the existing host behavior.

Receipt evidence:

- input SHA-256: `644a8275686968ea224e1213a459e8f10d9f7fbd2618f04358fca6fba1a56d95`
- result SHA-256: `0c9491420d0f5945fb6acfada906d2e37d12dd17cb2325ebad73487954003826`
- observed model: `claude-opus-4-8`; auxiliary models: none
- turns: 2; reported cost: USD 1.790315

## Review pass 2 — reconciliation

Immutable head: `5dffa240dd6033d93c44ac68d966dffc9343036c`

Claude confirmed the update-lifecycle fixes but identified one medium
compatibility gap and one low local-diagnostic gap in the broader release:

1. Mandatory verbose stream-model telemetry was behavior-tested on Claude Code
   2.1.210, while the public minimum still claimed 2.1.209.
2. Provider failure text was truncated before credential redaction, which could
   preserve a partial boundary-split token in an owner-only diagnostic.

Both were accepted. Commit `74c39d9f32959208bfc3e576a9129d8a6f989171`
raises the supported minimum to the behavior-tested 2.1.210 baseline across the
runner and publication packet, adds a fail-closed minimum-version regression,
redacts before bounding failure text, and adds a boundary-split regression.

Receipt evidence:

- input SHA-256: `72a3d37a3b9ba9c9d07fde22acb17aef4a5bc0a13a53c65458803290316501a8`
- result SHA-256: `7590647cdec25b17c22d321b88ec9d6cd6d862ec3bc3ed10f9ce56cbdbcbd349`
- observed model: `claude-opus-4-8`; auxiliary models: none
- turns: 2; reported cost: USD 1.6909715

## Review pass 3 — agreement gate

Immutable head: `74c39d9f32959208bfc3e576a9129d8a6f989171`

Claude found no critical, high, or medium issue. Its only low finding is the
already-declared external publication gate: the product, support, privacy, and
terms routes in the manifest are not deployed. Direct checks returned HTTP 404
for all four routes on 2026-07-15. Website PR
[nirajkvinit/amanerp_website#28](https://github.com/nirajkvinit/amanerp_website/pull/28)
is open, clean, and green, but has not been merged or deployed.

This finding is accepted as a release blocker, not hidden as code-complete
evidence. Do not merge the plugin publication PR, create `v0.2.0`, submit to the
OpenAI Plugin Directory, or instruct marketplace users to upgrade until the
website PR is deliberately merged, deployed, and all four routes return the
reviewed public content successfully. Business verification, portal
attestations, final submission, OpenAI approval, and publisher-controlled
publication remain separate human gates.

Receipt evidence:

- input SHA-256: `39279666dc843601fb08d7bf9afccc34e08c691aff30197d7cdde15d026c57ae`
- result SHA-256: `edd16266498a1abf02277f4ac2f1c5f656a1ae65b731324ca3365c57773c1aab`
- observed model: `claude-opus-4-8`; auxiliary models: none
- turns: 3; reported cost: USD 2.1953275

## Verification evidence

- `make check`: 49 tests passed.
- Ruff 0.15.21 check and format verification: passed.
- `make release-contract TAG=v0.2.0`: passed.
- `make marketplace-update-smoke`: Codex CLI 0.144.1 upgraded an isolated Git
  marketplace cache from 1.0.0 to 1.1.0, removed the stale cache, and reported
  the new version enabled.
- Official plugin validator and both official skill validators: passed.
- `make package` and `make package-repro-check`: passed; release-candidate ZIP
  SHA-256 is `2c06a5d4c0f95745d376e10e9f7626ae8c3cb42305928d33f62755e5b59a6160`.
- Installed-cache source comparisons: runner and both skills matched the source;
  the source manifest was restored to `0.2.0` after each cache-safe reinstall.
- Live `doctor --check-update`: passed on Python 3.14.3, Claude Code 2.1.210,
  and GitHub CLI 2.92.0; it correctly reported local 0.2.0 ahead of public 0.1.0.
- PR checks: Python 3.11, 3.12, 3.13, and 3.14 are green; merge state is clean.

## Agreement

**AGREED — CODE REVIEW GATE PASSED; PUBLICATION HOLD REMAINS.** Codex and Claude
agree that no unresolved critical, high, or medium correctness, security,
privacy, packaging, or update-lifecycle finding remains. The implementation is
ready once the named external publication gates are satisfied. The current 404
legal/support routes are an explicit no-go for merge, tag, release, marketplace
announcement, or directory submission.
