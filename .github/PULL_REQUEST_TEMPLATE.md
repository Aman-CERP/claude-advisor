## Outcome

Describe the user-visible result and the smallest coherent scope included.

## Trust boundary

- Data sent outside the workstation:
- Credential/environment handling:
- Model tools, persistence, or browser impact:
- GitHub or working-tree mutation impact:
- New dependency and license impact:

## Verification

List exact commands and summarized outcomes. Include failure-path coverage for runner changes.

```text
make check
make package
make package-repro-check
```

## Publication impact

State whether the manifest, skills, listing copy, screenshots, public URLs, reviewer cases, supported surfaces, migration path, or release notes changed.

## Checklist

- [ ] Specification and acceptance criteria are updated when the public contract changes.
- [ ] Tests failed for the intended reason before implementation when behavior changed.
- [ ] No real credential, private diff, personal data, or local absolute path is included.
- [ ] The read-only, explicit-invocation boundary is preserved or the change has a separately approved threat model.
- [ ] Documentation, changelog, and submission packet are synchronized.
- [ ] Material findings from an independent adversarial review are dispositioned.
