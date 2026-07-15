# v0.2.1 structured-output reliability review

Date: 2026-07-15

Status: Agreement achieved; no unresolved actionable finding

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
3. Accepted, then strengthened after final-head review: identical replay can
   recover only transient failure. The initial fixed half-budget design could
   starve attempt one, so it now uses the verified remaining aggregate. The
   skills, README, release notes, and ADR disclose the ledger and preemption rule.
4. Accepted and strengthened: a failed attempt must verify initialization,
   assistant, and usage model telemetry before a retry. A regression test proves
   observed Haiku use blocks retry as `model_policy_violation`.
5. Verified: the critical canary cost USD 1.045215, leaving substantial margin
   below its USD 5 per-attempt slice.
6. Rejected as stale evidence gap: Claude did not receive the test files in its
   bounded advisory context and therefore said retry tests were unverified. The
   local suite contains explicit tests for acknowledgment, exact same-model
   retry, unrelated-error no-retry, diagnostics, remaining-budget accounting, and failed-attempt
   downgrade rejection.
7. Accepted from skill forward-testing: retry authorization must follow disclosure
   of the exact aggregate ledger and deterministic attempt-ceiling rule. Both
   skills now list profile-specific aggregate figures, explain that retry receives
   only verified unused balance, and reject generic rerun permission given without
   that disclosure.

## Agreement state

### Initial immutable-head PR review

- PR: #3
- Reviewed head: `1419bc529ef46cd621d075a431caf889f703ae31`
- Diff SHA-256: `6e4faf85efdaadf54db530d13d1dcb8fb2dd7922e7342c14c934a0ada7ffcefa`
- Run: `20260715T071943Z-pr-review-0cb81d36`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.196645

Claude reported one medium and one low finding:

1. Accepted (medium): incomplete non-zero-exit telemetry was being relabeled as
   `model_policy_violation`, overloading a security-relevant outcome and blocking
   an authorized retry. Actual observed off-family use now remains
   `model_policy_violation`; incomplete telemetry preserves an ordinary failure or
   blocks an eligible retry as `retry_blocked_model_unverified`. Regression tests
   cover both paths.
2. Accepted (low): every user stream event was counted as a correction. The
   diagnostic now counts only a user event immediately following an assistant
   StructuredOutput tool attempt, with a test that excludes unrelated user events.

Codex and Claude agree on the architecture and both initial PR findings are fixed.
Final merge agreement remains pending the new immutable-head critical rerun and
green CI.

### Second immutable-head PR review

- Reviewed head: `875d459edde8425713532877b7a96fcee3a5c71d`
- Diff SHA-256: `d8487db41b183f11f70cc3e837528bc8569f4b38fee8625ebbd1929434d5df6e`
- Run: `20260715T072910Z-pr-review-f24475d8`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.1471865
- Material gate: no critical, high, or medium finding

Claude reported two low audit-quality findings, both accepted:

1. Process-level failures did not append attempt records. Timeout, start, I/O,
   and stream-limit branches now append minimal content-free records; tests cover
   both first-attempt timeout and retry-attempt timeout after a recorded structured
   failure.
2. Correction matching could undercount when a system event occurred between the
   StructuredOutput attempt and correction. The state now carries across
   non-participant events and clears only on an assistant or user event; the test
   includes an intervening system event and an unrelated user event.

The additional verification gap for two structured-output failures is also
closed: a test proves both attempt-numbered summaries, both attempt records, the
canonical final failure, and the terminal structured-output outcome.

### Third immutable-head PR review

- Reviewed head: `b3c315920dcabd55f3ecae96d2b6bb0f8a504fda`
- Diff SHA-256: `4c55a81b8922a0d15b1b8388472b64212dd3adfa4fcb5118fd93e8242d7c0281`
- Run: `20260715T073844Z-pr-review-26828129`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 3 / USD 1.377668
- Material gate: no critical, high, or medium finding

Claude reported one low observability finding: `retry_triggered` was set after a
retry decision but before the aggregate-time guard for attempt two. If the first
attempt consumed the deadline, the receipt could say triggered while only one
attempt started. Accepted and fixed: the field is now set after attempt two
passes the time guard and starts; deadline preemption keeps it false and records
`retry_preempted_reason: aggregate_timeout`. A monotonic-clock regression test
proves the boundary.

Claude also noted no direct test for a successful recovered attempt using an
off-family answering model. The normal success gate already enforced this, and a
new regression now forces Opus exhaustion followed by a Haiku success envelope;
the run exits `model_policy_violation` and publishes no result.

### Fourth immutable-head PR review

- Reviewed head: `e24496a5a2fb70e5ae070e40c0a2bc1a09345824`
- Diff SHA-256: `2b911c1f32f52667b4c321c413466a1e548586095873c70f802f4f53b8aadced`
- Run: `20260715T074727Z-pr-review-470a47c6`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.1737865
- Material gate: no critical, high, or medium finding

Claude reported one low audit-completeness finding: an exit-zero attempt rejected
by a post-parse model, usage, ceiling, extraction, or schema gate did not receive
an attempt record. Accepted and fixed: the runner appends a pending content-free
record as soon as an exit-zero envelope is parsed, then finalizes the concrete
gate outcome. Malformed exit-zero streams receive a minimal invalid-result record
at the parse boundary. Regression assertions cover schema-invalid, ceiling-breach,
and recovered-attempt model-policy outcomes, including two attempt records for the
Opus-to-Haiku case.

### Focused closure advisory

The current implementation and tests were supplied directly to a final critical
advisory focused on the every-started-attempt invariant.

- Run: `20260715T075607Z-advisory-b3897a00`
- Verdict/confidence: invariant closed / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 5 / USD 1.89472
- Input SHA-256: `d216ef17444383ebc250204457d193f7d3bb3d58cd7ec66cf328952b9b9b91e7`
- Result SHA-256: `42fdafc886b43b9117f2625e2f54bb27cbd214d974dd602f08ca70b19d8a5015`

Claude concluded that every enumerated process, parse, model, usage, ceiling,
extraction, schema, and success path now creates exactly one content-free attempt
record, with no duplication or persisted pending state, and found no remaining
critical/high/medium blocker. Codex reproduced that conclusion against the code
and green tests.

Claude noted a narrower unexpected-internal-exception window outside the original
finding. That defense-in-depth residual is also closed: the outer exception
boundary now fills a missing current record or finalizes it as `internal_error`.
A fault-injection test makes model-telemetry collection raise after an attempt has
started and proves the persisted record is finalized. Representative success and
retry tests also assert `len(attempts) == attempts_started`.

### Fifth immutable-head dogfood attempt

- Reviewed head: `347a460a1d28c24efe1170a84c39071aaa7b22fe`
- Diff SHA-256: `a04113305927387b5a971085417672491bc7fd1c291561c693a1f6575a92cc0a`
- Run: `20260715T080932Z-pr-review-8892f417`
- Outcome: `structured_output_retry_exhausted`
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 6 / USD 2.1308245
- StructuredOutput attempts/corrections: 5 / 5

This run produced no review and therefore cannot support merge agreement. It did
prove that the failure classifier, Opus-only model gate, content-free diagnostic,
and no-result fail-closed behavior work on the final head. It also falsified the
earlier assumption that flattening the advisory payload plus an optional outer
replay was sufficient for general reliability.

Grounded follow-up found that Anthropic's Agent SDK uses a validate/re-prompt
loop and recommends focused schemas. More importantly, Anthropic issue #502 is
still open and documents intermittent extra root wrappers (`output`, `response`,
and `json`) causing otherwise valid StructuredOutput calls to exhaust their
repair loop. Both plugin schemas now intentionally require one root `output`
property; the runner validates that provider-facing envelope and unwraps exactly
one layer before persisting the unchanged consumer payload. Terminal `errors`
are reduced to counts and fixed categories without retaining message text.

### Sixth immutable-head PR review

- Reviewed head: `90783ea023d17a4c477423de7bc57b6ad33881d2`
- Diff SHA-256: `f0d0939e4bf4e38d804e97f452a14edc232a2d1209956d34c93f977e0ce6ae57`
- Run: `20260715T082745Z-pr-review-9887ed90`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.41404
- Result SHA-256: `45fc04783664a2c2d8c02b0834af23c6d49800d47d637ac08fba45153f6ddb87`

The compatibility-envelope canary succeeded on the full 165,201-byte PR diff,
closing the prior live-validation gap. Claude found no critical, high, or medium
correctness/security defect and one low reliability footgun: fixed half-budget
slices could make an otherwise-successful expensive first attempt fail merely
because retry was authorized. Accepted and fixed. Attempt one now receives the
full aggregate; an eligible retry receives the verified unused balance rounded
down to cents, or is preempted below USD 0.10. Tests cover a USD 6 first-attempt
success under a USD 10 two-attempt authorization, a USD 0.42 failure followed by
a USD 9.58 retry ceiling, and insufficient-balance preemption.

### Seventh immutable-head PR review

- Reviewed head: `7b3a76d36285e87fd07782f42ac5b47ce22fb39a`
- Diff SHA-256: `8183b9194d048e588ea0177cdd8ea34ada5cd034807c3415c6cb48b4e9deac34`
- Run: `20260715T083934Z-pr-review-133242a3`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.363714
- Result SHA-256: `46803fa6543fd51bbda48dd5a9b10809a39e97870784f769d95bbab6368f06df`

Claude found no code-level correctness or security regression and reported one
medium documentation contradiction plus one low drift risk:

1. Accepted (medium): FR-4 and Phase H still described equal budget slices while
   the code, skills, ADR, and later specification section described the remaining
   aggregate ledger. Both stale passages now match the runtime contract.
2. Accepted (low): profile-specific skill disclosure figures duplicate runner
   defaults. A repository test now imports the runner profiles and constructs the
   exact required skill phrases, failing CI if code and operator disclosure drift.

Two verification gaps were rejected with direct evidence. The sixth and seventh
runs are themselves successful live Claude Code 2.1.210 envelope canaries, so the
claim that no live evidence exists is stale. The fake critical PR-review test runs
the provider envelope end to end through the PR schema and now explicitly asserts
that the unwrapped `result.json` equals the PR payload.

### Eighth immutable-head PR review

- Reviewed head: `db50d6118f1d7b71b9a6df74291f6ad6b84d58c9`
- Diff SHA-256: `0e15fc22ccd15fcc166a81c9ad3aaf57e9025dcc5f77b3dfb822542571c8fd51`
- Run: `20260715T084815Z-pr-review-0b9d8098`
- Verdict/confidence: comment / medium
- Model: `claude-opus-4-8` only; no auxiliary model
- Turns/cost: 2 / USD 1.569909
- Result SHA-256: `d3ca5b463f884bada3492fd1a2229f1e5a5564fcd8f854eb988c5d8fb1513132`
- Material gate: no critical, high, or medium finding

Claude found one low observability inconsistency: after attempt one exhausted
structured output and aggregate time preempted attempt two before process start,
only the attempt-numbered failure remained while the top-level outcome was
`timeout`. Accepted and fixed. The runner now also writes that last bounded
failure summary as canonical `claude-failure.json`; the top-level timeout and
`retry_preempted_reason: aggregate_timeout` remain accurate. The regression test
asserts both failure files are identical and the receipt points to the canonical
artifact.

The remaining verification gaps do not block agreement. This eighth run is a
successful live structured-output canary on its reviewed head, following two
earlier successful canaries. Codex ran the full suite and official validators;
the reviewer was intentionally limited to the immutable unified diff. The
provider wrapper remains a documented probabilistic mitigation that fails closed,
not a claim that external Claude Code behavior is under AmanERP's control.

## Final agreement

**AGREED — MERGE RECOMMENDED.** The fifth call failed closed and exposed the
provider-wrapper gap. The sixth, seventh, and eighth calls successfully validated
the compatibility envelope on progressively newer immutable heads. Every
critical, high, medium, and low actionable finding across the design advisory,
eight PR passes, and focused closure advisory was reproduced and fixed. The final
low fix is localized to canonical failure-artifact promotion and has direct
regression coverage; it does not materially alter model, schema, retry, budget,
or isolation behavior. Merge still requires green CI on the final head.
