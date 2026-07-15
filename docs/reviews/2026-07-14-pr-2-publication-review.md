# PR #2 publication-readiness dogfood review

Date: 2026-07-14  
Pull request: <https://github.com/Aman-CERP/amanerp-second-opinion/pull/2>  
Reviewer: installed `amanerp-second-opinion@amanerp` v0.2.0 using Claude Code 2.1.209 and Claude Opus 4.8  
Review mode: critical, read-only, isolated, tool-free

## Reviewed snapshots

| Pass | Head | Diff SHA-256 | Verdict | Confidence |
|---|---|---|---|---|
| Initial full PR | `3b3b135b17a96af857bb91a0d9f3ccd9c16772aa` | `de8384bead0613f10ed687663a3f7f21c0678e134a1ea47761258999845006fa` | `comment` | medium |
| Identifier-hardening rerun | `469cdb137a12750996b9c4ffcda5222f25dfd07c` | `274aff709fdd8fcdc48f02343cc815308af39971d9c4e08bdddc7d0b6f833224` | `comment` | medium |

Both reviews used base `9ef4a7dc77270c4182fa9e10b0f33528ba04c497`. Receipts confirm safe mode, tools disabled, Chrome disabled, shell disabled, session persistence disabled, no sensitive-input override, observed budget and turn enforcement, and successful structured results. The initial review used two turns and reported USD 0.976502; the rerun used three turns and reported USD 1.0083215.

## Finding disposition

### F1 — Release checksum sidecar may not be created

Disposition: **rejected as factually invalid, then hardened and independently reconciled**.

The complete packager computes the archive digest and writes `destination.with_suffix(destination.suffix + ".sha256")`. The packaging regression reads that sidecar and compares it with a fresh SHA-256 of the archive. The review saw only the unchanged portions of `scripts/package_plugin.py` in the PR patch and therefore inferred that the checksum existed only on stdout.

Commit `997dfbb` added a pre-publication workflow invariant: the release job now changes into `dist` and runs `sha256sum --check amanerp-second-opinion-*.zip.sha256` before `gh release create`. A local equivalent, `(cd dist && shasum -a 256 -c amanerp-second-opinion-0.2.0.zip.sha256)`, passed.

A targeted advisory was then given the complete packager, packaging test, and release workflow. It resolved F1 as no longer valid with high confidence, confirmed the verification ordering, and recommended merging with no critical, high, or medium blocker. Its receipt records input SHA-256 `86c5a2c581b04a785ece2a50f74e252cc6778c8243ad786970b79c9efcbd8f4b`, result SHA-256 `83c6dc4ff82860a6edf91c64074ee33e7b645b4c1c513d2bc916860c0a51b8af`, two turns, and reported USD 0.160393.

### F2 — Retired identifiers were not fully denied

Disposition: **accepted and fixed**.

The initial review correctly found that active-file validation did not reject all former customer-facing identifiers. Commit `469cdb1` expanded the retired-token guard to cover `claude-advisor`, `claude_advisor.py`, `claude-advisory`, `claude-pr-review`, and `aman-cerp`. Historical changelog and review records remain explicit provenance exceptions. The rerun did not repeat the finding.

### F3 — Public AmanERP URLs were not yet deployed

Disposition: **accepted as an intentional publication dependency, not a merge defect**.

The plugin manifest and submission packet point to the product, support, privacy, and terms routes implemented by AmanERP website PR #28. No release tag or OpenAI directory submission may occur until that PR is merged, deployed, and all URLs are verified live. Business verification, portal attestations, final submission, and final publisher-controlled publication remain human gates.

## Residual observations reconciled by Codex

- The package target invokes `scripts/package_plugin.py` with its default `dist` output, matching both release globs.
- The current packaging test asserts deterministic bytes, checksum agreement, archive isolation, and required `LICENSE` and `NOTICE` files.
- Project validation checks manifest/listing synchronization, exact five-positive/three-negative submission counts, local-only surface claims, trademark non-affiliation copy, PNG signatures and dimensions, and retired active identifiers.
- The renamed runner retained its isolation and bounded-process behavior; 32 unit and integration tests pass, including failure-path and process-group termination coverage.
- Binary asset dimensions and submission paths are checked from the actual files by the repository validator, not inferred from the PR renderer.

## Agreement

**AGREED — MERGE RECOMMENDED.** Claude and Codex agree that no unresolved critical, high, or medium blocker remains in the publication-readiness change. Public release tagging and OpenAI directory submission remain deliberately blocked on website deployment, live URL verification, publisher/business verification, and explicit maintainer approval.
