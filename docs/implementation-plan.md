# Second Opinion by AmanERP v0.2.0 — Publication Hardening Plan

Status: Implemented; human-controlled publication gates remain
Date: 2026-07-14
Owner: AmanERP maintainers

## V0.2 execution sequence

This release preserves the v0.1 runtime trust boundary while replacing the public identity and completing the OpenAI Plugin Directory submission packet.

### Phase A — contract and migration tests

1. Amend `docs/specification.md` with the publisher, trademark, legal, surface, and submission contracts.
2. Update project, packaging, and runner tests to require the `amanerp-second-opinion` package, `independent-*` skills, AmanERP marketplace identity, public legal URLs, assets, and five-positive/three-negative submission packet.
3. Run the changed tests before production edits and retain their expected failure as the red phase.

### Phase B — neutral product identity

1. Rename the plugin folder to `plugins/amanerp-second-opinion`.
2. Rename the runner to `scripts/second_opinion.py` while preserving command and exit-code behavior.
3. Rename the two skills to `independent-advisory` and `independent-pr-review` and regenerate their `agents/openai.yaml` metadata.
4. Rename the marketplace to `amanerp`, set the publisher to AmanERP, and update active documentation and packaging paths.
5. Preserve v0.1 changelog and review records as explicitly historical provenance.

### Phase C — publication materials

1. Add AmanERP-owned icon, logo, and representative PNG screenshots to the plugin assets.
2. Complete the rich manifest with product, support, privacy, terms, brand color, asset paths, capabilities, and starter prompts.
3. Add `submission/listing.json`, `test-cases.json`, reviewer guide, release notes, policy attestations, and final checklist.
4. Add deterministic repository validation for submission counts, fields, public URLs, asset existence, retired active identifiers, and archive isolation.

### Phase D — AmanERP public pages

1. Add the English-first `/developer-tools/second-opinion` product page using the existing AmanERP design system and a truthful local data-flow visual.
2. Add dedicated support, privacy, and terms pages under the same path.
3. Keep untranslated French surfaces unavailable and legal pages noindex; do not fabricate jurisdiction-specific claims.
4. Run link, locale, lint, build, and visual checks.

### Phase E — verification and publication PRs

1. Run `make check`, `make package`, `make package-repro-check`, official plugin validation, and both skill validators.
2. Install the renamed marketplace/plugin locally using the documented cache-safe flow and run doctor plus a synthetic supplied-diff smoke.
3. Open focused PRs in the plugin and website repositories.
4. Dogfood `independent-pr-review` against the plugin PR, disposition every high/medium finding, and rerun after material changes.
5. Leave OpenAI business verification, portal attestations, final submit, website deploy, and Anthropic trademark permission as named human-controlled publication gates.

## V0.2 rollback

- GitHub redirects the former repository URL after the neutral repository rename.
- The retired marketplace/plugin remains removable by its former identifiers; it is not silently overwritten.
- Existing `.codex/claude-advisor/` artifacts remain untouched and are not migrated automatically.
- Reverting this release restores the v0.1 package without changing Claude or GitHub credentials.

## V0.1 implementation record

Status: Ready for independent review  
Date: 2026-07-14  
Depends on: `docs/specification.md`

## 1. Delivery strategy

Implement one cohesive, standard-library Python runner and two thin Codex skills. The runner owns validation, isolation, process execution, artifact creation, and deterministic rendering. Skills own user-facing workflow guidance and call the runner rather than duplicating command logic.

The release proceeds through specification, plan review, tests-first implementation, adversarial diff review, verification, packaging, publication, and global local installation.

## 2. Repository layout

```text
claude-advisor/
├── .agents/plugins/marketplace.json
├── .github/workflows/ci.yml
├── docs/
│   ├── specification.md
│   ├── implementation-plan.md
│   └── reviews/
├── plugins/claude-advisor/
│   ├── .codex-plugin/plugin.json
│   ├── skills/
│   │   ├── claude-advisory/
│   │   │   ├── SKILL.md
│   │   │   └── agents/openai.yaml
│   │   └── claude-pr-review/
│   │       ├── SKILL.md
│   │       └── agents/openai.yaml
│   ├── scripts/claude_advisor.py
│   └── references/
│       ├── advisory-prompt.md
│       ├── advisory-schema.json
│       ├── pr-review-prompt.md
│       └── pr-review-schema.json
├── scripts/package_plugin.py
├── tests/
│   ├── fixtures/
│   ├── helpers.py
│   ├── test_advisory.py
│   ├── test_artifacts.py
│   ├── test_cli.py
│   ├── test_doctor.py
│   ├── test_packaging.py
│   ├── test_pr_review.py
│   └── test_security.py
├── AGENTS.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── SECURITY.md
└── pyproject.toml
```

## 3. Phase 0 — prerequisite and source verification

1. Confirm GitHub organization create/push permission.
2. Confirm target repository does not already exist.
3. Confirm local Codex supports marketplace and plugin installation commands.
4. Confirm live Claude version, authentication, and required isolation/structured-output flags.
5. Refresh official OpenAI and Anthropic documentation links.

Exit evidence:

- public empty repository exists;
- versions and auth status captured without credentials;
- specification records researched baseline and constraints.

## 4. Phase 1 — scaffold from official creators

1. Use the bundled Codex `plugin-creator` scaffold to generate the plugin manifest, plugin directories, and repository marketplace entry.
2. Use the bundled `skill-creator` initializer for both skill folders and agent metadata.
3. Set plugin version to `0.1.0` and Apache-2.0 license metadata.
4. Set both skills to explicit invocation only.
5. Run plugin and skill validators before customization to isolate scaffold issues.

Exit evidence:

- valid baseline manifest and skills;
- marketplace source points to `./plugins/claude-advisor`;
- no personal absolute paths in committed artifacts.

## 5. Phase 2 — tests first

Write failing tests against the specification before production runner code.

### 5.1 Test harness

- A temporary fake `claude` executable responds to `--version`, `--help`, `auth status`, and analysis calls.
- A temporary fake `gh` executable responds to auth, PR metadata, and diff commands.
- Each fake records JSON argument arrays and selected environment fields for safety assertions.
- Tests invoke the real runner as a subprocess where exit codes/stdout/stderr are contract surfaces; pure helpers are unit-tested directly only where useful.

### 5.2 Required first-wave failures

- doctor success, bounded dependency output, dependency/auth failures, and hidden `--max-turns` parser recognition through a no-inference version probe;
- argument/ceiling validation;
- exact isolation flags;
- successful advisory parsing and artifact creation;
- timeout/non-zero/malformed/incomplete Claude results, extra properties, and invalid enum values;
- bounded PR metadata/diff capture, hashing, and post-diff base/head race rejection;
- secret-path and secret-pattern rejection/override, including secrets in questions and benign assignments;
- deterministic report and package output;
- child-environment allowlist, first-party authentication-variable preservation, and unknown/customization-variable removal;
- permission, `O_NOFOLLOW`, and symlink protections;
- prompt structure proving every untrusted source is inside the evidence delimiters.

Exit evidence:

- tests fail because runner behavior is absent, not because fixtures are broken.

## 6. Phase 3 — runner foundation

Implement in this dependency order:

1. constants, stable exit codes, bounded configuration dataclasses;
2. compact JSON stdout result and stderr diagnostics;
3. safe executable resolution and version parsing;
4. atomic owner-only file writer;
5. run-directory allocation and receipt lifecycle;
6. bounded, symlink-safe input reader with an incrementally consumed aggregate advisory budget;
7. sensitive-input scanner and redactor;
8. bounded subprocess executor with argument arrays, per-child credential environments, empty/provided stdin, incremental stdout/stderr ceilings, a named probe timeout, POSIX process-group termination, and distinct startup/runtime I/O classification;
9. doctor checks;
10. Claude envelope, mandatory typed usage evidence, and structured-output extraction;
11. deterministic schema validation and Markdown rendering; the validator implements every keyword used by bundled schemas (`type`, `required`, `properties`, `additionalProperties`, `enum`, `items`, `minItems`, `maxItems`, `minimum`, and `maximum`) and treats unsupported bundled keywords as build errors;
12. advisory orchestration;
13. GitHub/supplied-diff review orchestration.

The implementation must never require `shell=True`, dynamic imports, network libraries, YAML parsing, or third-party packages.

## 7. Phase 4 — prompts, schemas, and skills

### 7.1 Schemas

- Use JSON Schema accepted by Claude's `--json-schema` flag.
- Keep all objects closed with `additionalProperties: false` where compatible.
- Bound enumerations and required fields.
- Avoid schemas whose rendering needs arbitrary code execution.
- Fail the build if a bundled schema contains a keyword the local validator does not implement.

### 7.2 Prompts

- Embed task rules in bundled prompt files.
- Label all appended material as untrusted evidence inside unique delimiters.
- Reference context items by stable IDs and source labels rather than trusting embedded paths.
- Require evidence-grounded results and `unable_to_review` for insufficient input.

### 7.3 Skills

- Explain when explicit use is appropriate.
- Require the Codex operator to confirm scope and avoid secret-bearing context.
- Call `doctor` before the first run or after dependency failures.
- Prefer supplied diff when the operator has already computed the authoritative change set.
- Read `result.json`, `report.md`, and `receipt.json` before relaying a conclusion.
- State that Claude output is untrusted advice and must be reconciled with repository evidence.

## 8. Phase 5 — documentation and open-source hygiene

1. README with quick start, prerequisites, commands, examples, artifacts, limitations, data disclosure, team rollout, and uninstall/update instructions.
2. Apache-2.0 license.
3. Contribution guide with tests and compatibility policy.
4. Security policy with private reporting instructions and threat boundaries.
5. Repository AGENTS.md describing precision, test-first, security, and focused-diff expectations.
6. Make targets for check, test, validate, package, clean, and live smoke.
7. `.gitignore` excluding caches, distributions, local run artifacts, and credentials.
8. Minimal `pyproject.toml` for tooling metadata without a runtime dependency.

## 9. Phase 6 — CI and deterministic packaging

### 9.1 CI

On pull requests and pushes to `main`:

- Python 3.11 and 3.12 unit/integration tests;
- `compileall`;
- plugin and skill validators using repository-accessible validation scripts or equivalent committed checks;
- packaging and archive-content safety checks;
- deterministic-package test.

CI must not need Anthropic or GitHub credentials and must never make a live Claude call.

### 9.2 Package

- Package only the `plugins/claude-advisor` tree.
- Sort paths; use `ZIP_STORED`; normalize ZIP timestamps and mode bits so reproducibility does not depend on Python's zlib build.
- Exclude symlinks, dot caches, bytecode, test artifacts, runtime run directories, and secrets.
- Emit `dist/claude-advisor-0.1.0.zip` and adjacent `.sha256`.
- Verify the archive root and manifest before success.

## 10. Phase 7 — review and verification

### 10.1 Design review gate

Invoke raw Claude CLI in isolated mode against the specification and implementation plan. Record the response under `docs/reviews/`. Classify each material finding as accepted/fixed or rejected with evidence before production implementation.

### 10.2 Local quality gates

Run:

```bash
make check
make package
make package-repro-check
```

Inspect:

- no dangerous Claude flags;
- no `shell=True`;
- no credential strings or absolute maintainer paths;
- no mutable GitHub command in runner code;
- archive contents and SHA-256;
- git diff and untracked files.

### 10.3 Live smoke gate

With the maintainer's authenticated Claude CLI:

1. `doctor --require-gh` succeeds.
2. Advisory on a harmless bounded decision succeeds.
3. Supplied-diff review of a small test diff succeeds.
4. A tool-requiring probe in safe mode with an empty tool set confirms that no tool can execute on the highest-tested Claude version.
5. Receipts show safe mode, tools disabled, Chrome disabled, no session persistence, correct hashes, and bounded resources.
6. No unexpected repository files or Claude sessions are created.

### 10.4 Final independent diff review

Generate a review bundle from `git diff --no-index /dev/null` for the initial repository or from the staged commit diff. Invoke raw Claude CLI with no tools and the PR-review schema. Address all actionable high/medium findings, rerun tests, and retain the review record.

## 11. Phase 8 — publication and installation

1. Confirm clean status and explicit file set.
2. Commit the complete coherent V1 release on `main` in the new repository.
3. Push `main` and set it as the GitHub default branch.
4. Run public CI to green.
5. Create annotated tag `v0.1.0` and push it.
6. Create GitHub release `v0.1.0` with the ZIP and SHA-256 assets.
7. Add marketplace with `codex plugin marketplace add Aman-CERP/claude-advisor`.
8. Install `claude-advisor` from that marketplace and verify it is enabled.
9. From AmanERP Team B and another sibling checkout, verify global plugin visibility.
10. Run a fresh Codex task for an end-to-end skill discovery/invocation check if the host requires restart for newly installed skills.

## 12. Rollback

- Disable or remove the installed plugin with the supported Codex plugin command.
- Remove the marketplace configuration if no other plugin depends on it.
- Delete only local test run directories under `.codex/claude-advisor/`.
- Do not revoke Claude credentials unless compromise is suspected; the plugin never stores them.
- For a defective public release, publish a patch release. Do not replace immutable release assets or retag an existing version.

## 13. Acceptance-criteria traceability

| Specification AC | Primary implementation evidence |
|---|---|
| AC-1, AC-2 | plugin/skill validators and metadata tests |
| AC-3, AC-4 | fake executable argument capture and security tests |
| AC-5 | doctor integration tests |
| AC-6 | advisory success/failure tests |
| AC-7 | PR metadata and exact diff-hash tests |
| AC-8 | sensitive input scanner tests |
| AC-9 | artifact, permission, and deterministic renderer tests |
| AC-10 | bounds-validation parameterized tests |
| AC-11 | packaging reproducibility test |
| AC-12 | retained local live-smoke receipts, excluded from package |
| AC-13 | global plugin listing from multiple AmanERP checkouts |
| AC-14 | versioned design and final diff review records |
| AC-15 | public GitHub Actions checks |

## 14. Stop conditions

Stop publication and report the blocker if:

- required Claude isolation flags are missing or behave differently from the specification;
- structured output cannot be validated reliably;
- the plugin installer cannot consume the public marketplace layout;
- any credential or sensitive repository content enters the package or Git history;
- live review mutates source, GitHub state, Claude configuration, or installs unexpected components;
- high-severity independent-review findings remain unresolved.
