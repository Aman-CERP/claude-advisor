# v0.2.1 structured-output reliability review

Date: 2026-07-15

Status: Decision review converged; final PR review pending

## Incident

Team A's critical advisory run
`20260715T061008Z-advisory-e77a31c1` used Claude Code 2.1.210 with
`claude-opus-4-8`, xhigh effort, and all isolation controls enabled. Claude
terminated after six structured-output responses and five correction events with
`error_max_structured_output_retries` / `structured_output_retry_exhausted`.
The plugin failed closed and published no `result.json` or `report.md`.

The strongest supported contributors were a deeply nested advisory schema and a
question that carried a second bespoke output contract. The failed raw stream was
correctly not retained, so no stronger causal claim is made.

## Critical decision advisory

The in-branch v0.2.1 runner reviewed the schema, trusted prompt, advisory skill,
specification, and runtime implementation using the critical profile.

- Run: `20260715T070813Z-advisory-b5118cab`
- Outcome: `success`
- Model: `claude-opus-4-8` only; no auxiliary model
- Effort/profile: xhigh / critical
- Attempts authorized/started: 2 / 1; no retry triggered
- Turns: 2
- Reported cost: USD 1.045215 against USD 5 per-attempt and USD 10 aggregate
- Input SHA-256: `c2f09e7993952df5ba8e803fd574cc6da090f1163fba038e442963102bf593e6`
- Result SHA-256: `c54bc4db2b05b2bd4ca9b285bd74cb4676d3cb22f552cb70b67ad08f62123704`
- Isolation: safe mode, tools disabled, Chrome disabled, session persistence
  disabled, shell disabled

Claude's verdict was release-worthy with no material redesign. It required a
post-flatten representative live run, retry state-machine tests, and release
version consistency before tagging. The advisory itself satisfied the first
requirement; the automated suite covers the second; the release validator owns
the third.

## Findings and disposition

1. Accepted: generic terminal `result` prose could contain sensitive business
   analysis even after credential redaction. Failure summaries now omit terminal
   result prose for every failure and expose only a presence boolean.
2. Accepted: the advisory result shape is breaking for machine consumers. The
   changelog and submission release notes now contain an explicit migration
   contract, and ADR-001 records the decision.
3. Accepted: identical replay can recover only transient failure and two-attempt
   mode halves the requested ceiling per attempt. The advisory skill, README,
   release notes, and ADR now disclose both caveats.
4. Accepted and strengthened: a failed attempt must verify initialization,
   assistant, and usage model telemetry before a retry. A regression test proves
   observed Haiku use blocks retry as `model_policy_violation`.
5. Verified: the critical canary cost USD 1.045215, leaving substantial margin
   below its USD 5 per-attempt slice.
6. Rejected as stale evidence gap: Claude did not receive the test files in its
   bounded advisory context and therefore said retry tests were unverified. The
   local suite contains explicit tests for acknowledgment, exact same-model
   retry, unrelated-error no-retry, diagnostics, budget split, and failed-attempt
   downgrade rejection.
7. Accepted from skill forward-testing: retry authorization must follow disclosure
   of the exact aggregate and per-attempt requested ceilings. Both skills now list
   profile-specific figures and reject generic rerun permission given without that
   disclosure.

## Agreement state

Codex and Claude agree on the v0.2.1 architecture and the accepted hardening
changes. Final merge agreement remains pending the immutable PR-head critical
review and green CI.
