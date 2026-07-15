# Contributing

Thank you for helping improve Second Opinion by AmanERP.

## Before proposing a change

- Open an issue for public-contract, trust-boundary, distribution, authentication, or hosted-service changes.
- Keep personal OAuth local. Hosted or shared execution is outside the current contract and requires API-based architecture plus a separate legal and security review.
- Do not add a runtime dependency without documenting license, supply-chain, maintenance, and reproducibility implications.

## Local workflow

```bash
git switch -c your-name/short-description
make check
make package
make package-repro-check
```

Tests use fake Claude and GitHub executables and require no credentials. Live tests are manual release gates and must use harmless, non-sensitive inputs.

For changes to the runner:

1. Add a failing contract test.
2. Implement the smallest safe behavior.
3. Exercise both success and failure receipts.
4. For model-policy changes, prove profile selection, observed answering-model validation, auxiliary-model rejection, and no fallback with the fake-Claude harness.
5. Inspect subprocess argument arrays and child environment handling.
6. Update the specification and README if operator-visible behavior changes.

Pull requests should explain the threat boundary affected, tests run, data-handling impact, and rollback. Report findings rather than style preferences during review.

By contributing, you agree that your contributions are licensed under Apache-2.0.
