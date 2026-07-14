# Claude Advisor v0.1.0 — Product and Engineering Specification

Status: Approved for implementation  
Date: 2026-07-14  
Owner: Aman-CERP maintainers  
Repository: `Aman-CERP/claude-advisor`  
License: Apache-2.0

## 1. Executive summary

Claude Advisor is an open-source Codex plugin that lets an operator explicitly ask a locally installed Claude Code CLI for a second opinion. Version 0.1.0 ships two skills:

- `claude-advisory`: structured analysis and recommendations for a bounded decision.
- `claude-pr-review`: an independent, evidence-oriented review of a GitHub pull request or a supplied Git diff.

The plugin is a local orchestration layer, not a hosted Claude service. Each operator installs and authenticates Claude Code on their own workstation. The plugin never redistributes a personal OAuth session, never exposes a network service, and never publishes comments or changes code by itself.

The central design rule is fail-closed independence: Claude receives only the prompt and bounded context intentionally assembled for the run, with Claude customizations and tools disabled. Every successful run produces a human-readable report plus a machine-readable receipt that records what was reviewed, which controls were active, and which Claude CLI version and model were used.

## 2. Problem statement

Critical architecture decisions and pull-request reviews benefit from a genuinely independent model perspective. Today, an operator can invoke `claude -p` manually, but that workflow has recurring weaknesses:

- prompts and review rubrics vary;
- source context and reviewed revisions are not consistently recorded;
- local Claude hooks, plugins, MCP servers, and repository instructions can undermine reviewer independence;
- failures or malformed output can be mistaken for a valid review;
- token, turn, time, and input-size ceilings are inconsistent;
- output is easy to lose and hard to audit;
- review results can accidentally be treated as approval rather than advice.

Claude Advisor standardizes that boundary while preserving human judgment.

## 3. Goals

1. Provide explicit Codex skills for advisory and PR-review use cases.
2. Invoke the operator's local Claude Code CLI non-interactively and capture its result in durable files.
3. Disable Claude-side customizations, tools, Chrome integration, and session persistence for independent, read-only analysis.
4. Produce structured, schema-validated results and provenance receipts.
5. Enforce deterministic input/time ceilings and fail closed when Claude reports exceeding requested turn or spend ceilings.
6. Fail visibly on missing prerequisites, authentication failures, timeouts, non-zero exits, incomplete results, or malformed output.
7. Make the plugin installable from a public Codex marketplace repository and available across all local workspaces for that Codex user.
8. Keep V1 dependency-free beyond Python 3.11+, Git, GitHub CLI for PR mode, and Claude Code.

## 4. Non-goals

- Hosting a Claude proxy, MCP service, or shared OAuth session.
- Supporting ChatGPT web or Codex cloud environments that cannot execute the local CLI.
- Automatically invoking Claude based on task classification.
- Automatically posting GitHub reviews, comments, approvals, labels, commits, or status checks.
- Allowing Claude to edit files, run shell commands, browse, use MCP servers, or read arbitrary repository content.
- Replacing project-specific quality gates, security review, human approval, or Codex's own analysis.
- Comparing or scoring model vendors.
- Persisting prompts or results outside the operator-selected local output directory.

## 5. Users and primary workflows

### 5.1 Decision advisory

An engineer has a bounded decision with multiple viable options. Codex gathers the decision, constraints, evidence, and optionally selected context files, then explicitly invokes `claude-advisory`. The output must distinguish facts, inferences, assumptions, unresolved questions, options, risks, and a recommended next step.

### 5.2 Pull-request review

An engineer requests an independent review of a GitHub PR. The runner resolves immutable PR metadata and diff content through read-only `gh` commands, asks Claude to review the supplied snapshot, and returns prioritized findings with file/line evidence and a verdict. The review is advisory only and does not touch GitHub state.

### 5.3 Supplied-diff review

An engineer wants a pre-PR or offline review. Codex supplies an existing unified-diff file plus explicit metadata. No GitHub access is required.

### 5.4 Team distribution

The public repository is registered as a Codex plugin marketplace. Installation is global to the local Codex user, so one installation is visible from every AmanERP checkout on that machine. Teammates on separate machines run the documented marketplace-add and plugin-add commands once and authenticate their own Claude CLI.

## 6. Scope-challenge record

### 6.1 User-value lens

Verdict: GO WITH AMENDMENTS.

- The smallest lovable product is two explicit workflows backed by one hardened runner.
- Automatic invocation and GitHub mutation add risk without improving the core second-opinion value.
- Durable receipts are part of the product, not optional observability, because a review without an identifiable snapshot is not dependable.

### 6.2 Engineering lens

Verdict: GO WITH AMENDMENTS.

- Use Python standard library and subprocess argument arrays; do not introduce a shell wrapper or dependency tree.
- Claude receives a closed context bundle over stdin and no tools. The runner, not Claude, performs the narrowly scoped GitHub reads.
- V1 pins a tested minimum Claude CLI version rather than guessing backward compatibility for newly observed safety flags.
- GitHub PR mode must identify base and head object IDs and hash the exact diff.

### 6.3 Security and trust lens

Verdict: GO WITH AMENDMENTS.

- Invocation is explicit only; both skills declare `allow_implicit_invocation: false`.
- Claude runs with `--safe-mode`, `--tools ""`, `--no-chrome`, and `--no-session-persistence`.
- Inputs are labeled as untrusted evidence, not instructions. Prompt-injection text inside a diff must not change the task.
- The runner rejects likely secret-bearing files and high-confidence secret patterns by default. An operator may override only with an explicit flag recorded in the receipt.
- Output is local and created with restrictive permissions where the platform supports them.

### 6.4 Distribution and operations lens

Verdict: GO.

- A public marketplace repository is the right distribution primitive for a reusable team workflow.
- A local CLI integration is portable across local Codex workspaces but cannot transparently run in hosted environments. That limitation must remain prominent.
- Every teammate supplies their own Anthropic authentication and bears their own usage limits or API billing.

### 6.5 Scope decision

Proceed with V1 as a local-only, non-mutating, explicit plugin. Defer remote MCP/service support, automatic review posting, repository-wide Claude tools, and policy automation until separate threat models and terms reviews exist.

## 7. Grounded platform baseline

Research was refreshed on 2026-07-14 against official documentation and live local probes.

- OpenAI documents plugins as the stable packaging mechanism for sharing skills across teams; a plugin requires `.codex-plugin/plugin.json` and can be distributed through a marketplace repository.
- OpenAI documents skills as instruction bundles with `SKILL.md`; plugin-owned skills can opt out of implicit invocation.
- Anthropic documents `claude -p` for non-interactive execution, `--output-format json`, structured output with `--json-schema`, and resource controls including `--max-turns` and `--max-budget-usd`.
- The locally tested Claude CLI is `2.1.209`. Its help confirms these mandatory V1 flags: `--print`, `--safe-mode`, `--tools`, `--no-chrome`, `--no-session-persistence`, `--output-format`, `--json-schema`, `--max-budget-usd`, `--model`, and `--effort`. Accepted effort values are `low`, `medium`, `high`, `xhigh`, and `max`. Help states that safe mode disables CLAUDE.md, skills, plugins, hooks, MCP servers, commands, agents, and other customizations while retaining authentication; `--tools ""` disables built-in tools; `--no-session-persistence` avoids saving resumable sessions.
- Claude 2.1.209 accepts `--max-turns` but does not advertise it in local `--help`. A live isolated probe with `--max-turns 1` exited successfully and returned `num_turns: 1`. Doctor verifies parser recognition without an API call by placing `--max-turns 1` and a near-zero positive budget before a deliberate sentinel unknown option, redirecting stdin from an empty source, applying a five-second timeout, and requiring the sentinel—not `--max-turns`—to be identified as unknown.
- The exact authentication probe `claude auth status --json` was live-verified on 2.1.209. Exit 0 plus JSON boolean `loggedIn: true` is success. The command also returns identity and organization fields; the plugin must neither print nor persist those fields.
- GitHub CLI `2.92.0` was live-verified. `gh pr view --json baseRefOid,headRefOid,...` returned both object IDs against a live GitHub PR.
- Anthropic documents that Pro and Max subscriptions can authenticate Claude Code and that Claude/Claude Code usage shares plan limits. API Console billing is separate. The plugin must not claim that a run is free or that a spend cap guarantees subscription availability.

Primary sources:

- [OpenAI: Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Plugins](https://learn.chatgpt.com/docs/plugins)
- [Anthropic: Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference)
- [Anthropic: Run Claude Code programmatically](https://code.claude.com/docs/en/headless)
- [Anthropic: Set up Claude Code](https://docs.anthropic.com/en/docs/claude-code/getting-started)
- [Anthropic: Using Claude Code with Pro or Max](https://support.anthropic.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)

## 8. Functional requirements

### FR-1: Explicit skill invocation

The plugin exposes exactly two user-facing skills in V1. Neither may be implicitly invoked.

### FR-2: Preflight doctor

The runner provides `doctor` and verifies:

- Python version is supported;
- Claude executable resolution;
- Claude version is parseable and meets the minimum tested version;
- Claude authentication status succeeds;
- GitHub CLI resolution and authentication when requested;
- all advertised mandatory flags are present in `claude --help`: `--print`, `--safe-mode`, `--tools`, `--no-chrome`, `--no-session-persistence`, `--output-format`, `--json-schema`, `--max-budget-usd`, `--model`, and `--effort`;
- the installed version is at least the version on which the hidden-but-accepted `--max-turns` behavior was live-tested;
- a no-API parser sentinel confirms that the installed CLI still recognizes `--max-turns`.

Doctor fails closed when a mandatory flag is missing. It warns, but does not fail, when Claude is newer than the highest behavior-tested version, because flag presence does not prove unchanged semantics. Authentication output is reduced to non-identifying status fields before display or persistence.

It returns structured JSON and a non-zero exit when a required check fails. It must not print credentials or full environment contents.

### FR-3: Advisory command

The runner provides `advisory` with:

- exactly one question source: `--question` or `--question-file`;
- zero or more `--context-file` arguments;
- explicit `--output-dir` or a safe default under `.codex/claude-advisor/`;
- configurable model, effort, requested maximum turns/budget, parent-enforced timeout, and total input bytes within validated bounds;
- schema-validated Claude output.

### FR-4: PR-review command

The runner provides `pr-review` with exactly one review source:

- `--pr NUMBER` plus optional `--repo OWNER/REPO`; or
- `--diff-file PATH` plus required source labels.

GitHub mode uses argument-safe, read-only commands:

- `gh pr view` for repository, number, title, URL, author, base branch, head branch, base object ID, head object ID, additions, deletions, and changed-file count;
- `gh pr diff` for unified diff content.

GitHub stdout and stderr are read incrementally with byte ceilings; an oversized diff is terminated and rejected before assembly. The same bounded subprocess primitive caps Claude stdout and stderr before parsing. The runner reads `baseRefOid` and `headRefOid` before and after `gh pr diff` and aborts with exit 8 if either changed. The exact diff is hashed with SHA-256 and recorded. The receipt labels the content as the unified diff returned by GitHub's PR-diff endpoint; it does not claim that the content equals a local two-dot object range.

V1 ceilings are 6 MiB for a PR diff or individual context file, 8 MiB for the assembled advisory input, 1 MiB for GitHub metadata, 16 MiB for Claude stdout, and 1 MiB for child-process stderr. The runner terminates the child and returns the corresponding fail-closed outcome as soon as a stream crosses its ceiling.

### FR-5: Structured outcomes

Claude's structured-output envelope remains untrusted. The runner validates the extracted result locally and fail-closed. Its validator implements every keyword used by the bundled schemas: `type`, `required`, `properties`, `additionalProperties`, `enum`, `items`, `minItems`, `maxItems`, `minimum`, and `maximum`. A bundled schema using any unsupported keyword is a build error.

Advisory output includes:

- executive summary;
- facts and cited evidence references;
- assumptions and uncertainties;
- options with tradeoffs;
- material risks;
- recommendation, confidence, and conditions that would change it;
- validation steps.

PR-review output includes:

- verdict: `approve`, `comment`, `request_changes`, or `unable_to_review`;
- overall confidence and summary;
- prioritized findings;
- each finding's severity, confidence, category, file, optional line, evidence, failure scenario, impact, and recommended fix;
- residual risks and verification gaps.

### FR-6: Durable artifacts

Every attempted run creates a unique run directory containing:

- `request.json`: sanitized command configuration and source metadata;
- `input.sha256`: hash of the exact assembled input;
- `claude-response.json`: raw JSON envelope returned by Claude on success;
- `result.json`: validated structured result on success;
- `report.md`: deterministic human-readable rendering on success;
- `receipt.json`: timing, versions, controls, hashes, exit classification, and artifact paths;
- `stderr.log`: redacted stderr, including for failed runs.

The receipt is always written once a run directory exists, including on timeout or child-process failure.

### FR-7: Machine-readable command result

The runner writes one compact JSON object to stdout. Human diagnostics go to stderr. Exit codes are stable:

- `0`: success;
- `2`: invalid usage or rejected input;
- `3`: missing or incompatible dependency;
- `4`: authentication unavailable;
- `5`: Claude execution failed, returned an incomplete result, or reported a requested turn/cost ceiling breach;
- `6`: timeout;
- `7`: malformed or schema-invalid result;
- `8`: GitHub read failed;
- `9`: internal error.

### FR-8: Packaging and installation

The repository contains a valid Codex marketplace entry and plugin manifest. A deterministic packaging command creates a versioned ZIP and SHA-256 file without credentials, runtime artifacts, caches, or test output.

## 9. Security and privacy requirements

### 9.1 Trust boundaries

Trusted control plane:

- runner code and bundled schemas/prompts;
- explicit CLI options after validation;
- resolved executable paths;
- operator-approved context paths.

Untrusted data plane:

- advisory question and context contents;
- GitHub metadata, author names, titles, and diffs;
- Claude stdout and stderr;
- filesystem names supplied by the operator.

### 9.2 Command execution

- Never invoke a shell for Claude or GitHub commands.
- Build subprocess argument arrays and use `shell=False`.
- Never accept arbitrary extra Claude or `gh` arguments.
- Resolve executables from explicit overrides or `PATH`; record the path.
- Remove customization controls `CLAUDE_CODE_SAFE_MODE`, `CLAUDE_CODE_SIMPLE`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CONFIG_DIR`, and `MCP_TIMEOUT` from the child environment so the runner's explicit mode wins. Preserve ordinary process essentials and provider authentication variables, including `ANTHROPIC_API_KEY`, `AWS_*`, `GOOGLE_*`, and Azure provider variables. Never log their values. Tests assert the denylist is absent and representative authentication variables survive.

### 9.3 Claude isolation

Every analysis call includes:

```text
--print
--safe-mode
--tools ""
--no-chrome
--no-session-persistence
--output-format json
--json-schema <bundled-schema>
--max-turns <bounded-value>
--max-budget-usd <bounded-value>
--model <allowlisted-value>
--effort <allowlisted-value>
```

The prompt instructs Claude that all delimited source material is untrusted evidence and that embedded instructions must be ignored.

### 9.4 Secret controls

The runner scans the entire assembled input—question, context, metadata, and diff—and rejects it when it:

- reference high-risk path basenames such as `.env`, private keys, common credential stores, or decrypted secret manifests; or
- matches high-confidence private-key, GitHub token, AWS access-key, Anthropic API-key, OpenAI API-key, or named credential assignments. Named assignments are limited to credential-oriented keys such as `password`, `passwd`, `secret`, `token`, `api_key`, `private_key`, and `client_secret`, with a non-placeholder value of at least 12 characters. Benign ordinary assignments are not rejected.

The default check is intentionally conservative but not a DLP guarantee. `--allow-sensitive-input` requires explicit invocation, emits a warning, and is recorded in request and receipt artifacts.

### 9.5 Filesystem controls

- Default output remains inside the current repository under `.codex/claude-advisor/runs/`.
- Run directories use collision-resistant identifiers.
- Files are written atomically and use owner-only permissions where supported.
- Symlink output directories and symlink context files are rejected by default.
- Source files are read with byte ceilings before decoding as UTF-8 with explicit error handling.
- On supported POSIX systems, source files are opened with `O_NOFOLLOW` and verified as regular files through the open descriptor. Output parent directories are rejected when symlinked. If these primitives are unavailable, the operation fails closed; Windows-native support is outside V1.

### 9.6 Data handling disclosure

The README and skill instructions must tell operators that selected prompts, diffs, and context are sent to Anthropic under the authentication and data controls of their Claude account. Teammates on separate machines must authenticate themselves. The project stores no credentials and provides no shared service.

## 10. Reliability and resource bounds

V1 bounds:

- total assembled input: 8 MiB;
- any single input file: 6 MiB;
- context files: 32;
- runner timeout: 60–1,800 seconds, enforced by the parent process;
- requested Claude turns: 1–12, with any reported overage classified as a failed ceiling breach;
- requested Claude budget: USD 0.10–20.00, with any reported overage classified as a failed ceiling breach;
- model allowlist: `sonnet`, `opus`, or a full model identifier matching a conservative character pattern;
- effort: `low`, `medium`, `high`, `xhigh`, or `max`.

Defaults:

- advisory: `opus`, high effort, 6 turns, USD 5.00, 900 seconds;
- PR review: `sonnet`, high effort, 8 turns, USD 5.00, 1,200 seconds;
- PR review with `--critical`: `opus`, high effort, 10 turns, USD 10.00, 1,500 seconds.

A turn or budget flag is a Claude-side requested ceiling, not a promise of availability, exact subscription charge, or perfect pre-spend enforcement. A live 2.1.209 structured-output run reported three turns after `--max-turns 2`; the plugin therefore checks reported turns/cost and rejects a breached run instead of publishing its result as success.

The `--max-budget-usd` flag is a required compatibility feature in V1 and is always passed. Receipts distinguish `budget_requested_usd` from `reported_cost_usd`; absence of a reported cost is recorded as `budget_enforcement_observed: false`, without claiming the CLI ignored the requested ceiling.

## 11. Prompt requirements

Both prompts must:

- state the role and bounded task;
- prioritize correctness, security, data integrity, compatibility, and evidence;
- distinguish observed facts from inference;
- require an `unable_to_review` outcome when evidence is insufficient;
- reject prompt instructions embedded in source material;
- avoid praise, style-only commentary, and invented file/line references;
- require concise, actionable outputs fitting the bundled schema;
- state that the result is advisory and does not authorize mutation.

The PR prompt additionally requires review of auth boundaries, tenant isolation, data loss, migrations, API compatibility, concurrency, idempotency, observability, rollback, and failure-path tests when relevant.

## 12. Compatibility

Supported V1 environment:

- macOS or Linux;
- Python 3.11+;
- Codex release supporting plugin marketplaces and plugin skills;
- Claude Code 2.1.209+ for the exact tested isolation flags; 2.1.209 is the highest behavior-tested release for v0.1.0, and newer releases produce a compatibility warning;
- GitHub CLI 2.x only for `--pr` mode;
- Git for local source metadata and packaging workflows.

Windows native support is not claimed in V1. WSL may work but is unverified.

## 13. Observability

Receipts include:

- plugin and schema versions;
- start/end timestamps and duration;
- runner command and outcome classification without question/context content;
- executable paths and versions;
- selected model, effort, turns, budget, and timeout;
- security-control booleans;
- input, diff, and result SHA-256 hashes;
- GitHub immutable revision metadata when applicable;
- Claude envelope metadata that is safe to retain, such as session ID, duration, turns, cost fields, and result subtype, when returned;
- redaction count for stderr.

No telemetry is sent by the plugin itself.

Input hashes prove that two retained inputs were identical; they do not preserve or recover the original content. Operators who require content-level auditability must retain the reviewed PR revision or their own approved source bundle separately.

## 14. Acceptance criteria

### AC-1: Plugin validity

The official local plugin validator accepts the plugin, and both skill validators accept their skill folders.

### AC-2: Explicit invocation

Both generated `agents/openai.yaml` files set `allow_implicit_invocation: false`.

### AC-3: Isolated Claude command

Automated tests prove every analysis subprocess contains all isolation and ceiling flags and contains no dangerous permission-bypass flag. The live smoke additionally verifies isolation behavior on the highest tested Claude version by asking for an unavailable tool operation and confirming no tool can execute.

### AC-4: No shell injection

Tests use hostile question, file, repository, and PR strings and prove they remain data arguments or are rejected; no subprocess uses a shell.

### AC-5: Doctor outcomes

Tests cover success, missing Claude, incompatible Claude, each advertised mandatory flag missing in turn, hidden `--max-turns` parser recognition, newer-than-tested warning, unauthenticated Claude, sanitized auth status, and optional/missing GitHub CLI.

### AC-6: Advisory outcomes

Tests cover valid structured output, non-zero Claude exit, timeout, malformed envelope, missing structured output, and schema-invalid result.

### AC-7: PR snapshot integrity

Tests prove PR mode records owner/repository, PR number, base/head object IDs, and the SHA-256 of the exact reviewed diff. Separate tests bound GitHub diff output and change `baseRefOid` and `headRefOid` between the pre- and post-diff reads, requiring an exit-8 abort without a review result.

### AC-8: Sensitive-input fail-closed behavior

Tests cover sensitive filenames, secrets in the question and context, representative high-confidence secret patterns, benign assignments, default rejection, explicit override, and receipt disclosure.

### AC-9: Artifact durability

Tests prove success and failure receipts are written atomically, output files have restrictive permissions, and reports are deterministic for a fixed result.

### AC-10: Bounded inputs

Tests cover file count, single-file size, total input size, timeout, turns, budget, model, effort validation, and reported turn/cost ceiling breaches.

### AC-11: Deterministic package

Two clean packaging runs from the same source revision produce byte-identical archives and matching SHA-256 files.

### AC-12: Live smoke

On the maintainer workstation, `doctor`, one advisory, one supplied-diff or public-PR review, and one no-tools behavioral probe complete successfully against the authenticated, highest-tested Claude CLI, with receipts inspected for isolation controls.

### AC-13: Team-wide local availability

After adding the public marketplace and installing the plugin once, `codex plugin list` reports it enabled from two sibling checkouts on the same machine. Maintainer evidence uses AmanERP Team B and another AmanERP checkout. Documentation explains the per-user installation boundary for separate machines.

### AC-14: Independent reviews

Before release, Claude reviews this specification/plan and the final release diff through a separate raw CLI invocation. `HIGH` and `MEDIUM` findings are material; each is fixed or explicitly documented with evidence and rationale.

### AC-15: CI

Public GitHub Actions validate manifests/skills, run the full test suite, perform static Python compilation, and verify deterministic packaging without requiring Claude or GitHub credentials.

## 15. Release and support policy

- Semantic versioning.
- Git tags and GitHub releases are immutable publication points.
- Every release publishes the deterministic ZIP and SHA-256 file.
- Minimum supported CLI versions are documented per release.
- Security reports follow `SECURITY.md` and should not be filed publicly until coordinated disclosure is appropriate.
- V1 is advisory software. Maintainers do not warrant review completeness or correctness.

## 16. Deferred decisions

The following require new specifications, threat models, and terms review:

- remote MCP/server mode for hosted ChatGPT or Codex;
- enterprise API-key or Bedrock/Vertex execution profiles;
- automatic repository-context selection;
- GitHub review publishing and status checks;
- organization-managed installation policy;
- multi-model aggregation or consensus scoring;
- Windows-native support.
