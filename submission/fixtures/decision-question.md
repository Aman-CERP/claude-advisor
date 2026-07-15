# Decision

Choose whether a new parser should launch behind a reversible feature flag or replace the current parser in one deployment.

## Constraints

- Existing clients depend on the current output schema.
- Rollback must complete within ten minutes.
- Both parsers can run from the same immutable input during a one-week comparison period.
- The decision is due before the next release candidate.
