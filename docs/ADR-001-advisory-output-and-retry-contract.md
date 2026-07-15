# ADR-001: Advisory output and retry contract

Status: Accepted

Date: 2026-07-15

## Context

A critical Opus advisory exhausted Claude Code's internal structured-output repair
loop after six assistant responses and five correction events. The plugin failed
closed, but the previous advisory schema was deeply nested and the submitted
question contained a competing bespoke output contract. `--max-turns` bounded the
outer Claude run; it did not guarantee successful internal schema repair.

## Decision

1. Advisory results use a shallow, closed JSON object. Rich facts, assumptions,
   option tradeoffs, controls, operational failure modes, estimate/ADR
   implications, and open questions live in one Markdown `analysis` string.
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
5. Timeout and budget are aggregate across attempts. The budget is divided evenly;
   reported first-attempt usage must be valid and within its slice before retry.
6. Failed streams are never retained. Failure summaries omit terminal result prose
   and preserve only bounded control/usage counts and validated model identifiers.
   Every started attempt receives an audit record, including process-level
   failures that do not return a parseable terminal.

## Consequences

- Advisory generation has a materially simpler structured-output target while the
  human reasoning rubric remains intact.
- `result.json` is schema-breaking for downstream v0.2.0 consumers; the changelog
  and release notes provide the migration contract.
- An identical retry can recover only transient/non-deterministic failure and may
  spend the second budget slice without success.
- Selecting two attempts halves the requested ceiling for each attempt. Current
  critical live evidence used USD 1.045215 against a USD 5 per-attempt ceiling;
  maintainers must continue to watch this margin.
- Receipt schema 3 makes retry authorization and execution auditable.
