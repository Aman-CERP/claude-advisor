# ADR-001: Advisory output and retry contract

Status: Accepted

Date: 2026-07-15

## Context

A critical Opus advisory exhausted Claude Code's internal structured-output repair
loop after six assistant responses and five correction events. The plugin failed
closed, but the previous advisory schema was deeply nested and the submitted
question contained a competing bespoke output contract. `--max-turns` bounded the
outer Claude run; it did not guarantee successful internal schema repair.

A later full-PR dogfood run failed in the same way after five StructuredOutput
calls. Current Anthropic documentation says the Agent SDK validates and
re-prompts on mismatch, recommends focused schemas, and exposes an `errors`
field on the terminal result. Anthropic's open issue #502 separately documents
an intermittent agent-side wrapper defect in which otherwise valid data is sent
under `output`, `response`, or `json`, making a root payload fail validation.

## Decision

1. Advisory results use a shallow, closed JSON object. Rich facts, assumptions,
   option tradeoffs, controls, operational failure modes, estimate/ADR
   implications, and open questions live in one Markdown `analysis` string.
   Both advisory and PR-review provider contracts place their existing payload
   inside one required root property named `output`. The runner validates the
   whole provider envelope locally, removes exactly one `output` layer, and
   publishes the unchanged consumer payload in `result.json`.
2. The question defines the bounded decision and analysis topics; context is
   evidence. Neither may replace the bundled JSON Schema, which is the sole
   machine-output contract.
3. One attempt is the default. A second attempt requires
   `--structured-output-attempts 2 --acknowledge-retry-cost` and is eligible only
   after Claude's structured-output retry-exhausted terminal outcome.
4. A retry preserves model, effort, input, prompt, schema, no-tools isolation, and
   per-attempt turn ceiling. Initialization, assistant, and usage telemetry from
   the failed attempt must all verify the selected family before retry. There is
   no model fallback. Observed off-family use is a model-policy violation;
   incomplete error telemetry blocks retry under a distinct unverified label and
   must not be reported as proof of a downgrade.
5. Timeout and budget are aggregate across attempts. Attempt one receives the full
   aggregate ceiling. After an eligible failure, the retry receives only the
   verified unused balance, rounded down to cents; reported first-attempt usage
   must be valid and within the aggregate before retry. Less than USD 0.10 of
   remaining balance preempts retry.
   A retry is recorded as triggered only when the second process starts; deadline
   expiry before that point is recorded as aggregate-timeout preemption.
6. Failed streams are never retained. Failure summaries omit terminal result prose
   and validation messages, preserving only bounded control/usage counts,
   content-free terminal error categories, and validated model identifiers.
   Every started attempt receives an audit record, including process-level
   failures that do not return a parseable terminal and exit-zero responses later
   rejected by a post-parse gate. Unexpected internal exceptions finalize the
   current attempt as `internal_error` before the receipt is persisted.

## Consequences

- Advisory generation has a materially simpler structured-output target while the
  human reasoning rubric remains intact.
- The single-property compatibility envelope aligns the schema with the most
  common provider-generated wrapper while keeping `result.json` independent of
  that provider quirk. Alternative or nested wrappers still fail closed.
- `result.json` is schema-breaking for downstream v0.2.0 consumers; the changelog
  and release notes provide the migration contract.
- An identical retry can recover only transient/non-deterministic failure and may
  spend the remaining aggregate balance without success.
- Retry authorization does not reduce attempt one's ceiling. A high-cost failure
  may leave too little balance for a second process, which is reported as a
  preemption instead of silently exceeding the aggregate.
- Receipt schema 3 makes retry authorization and execution auditable.
