# Independent design review — Claude Advisor v0.1.0

Date: 2026-07-14  
Reviewer: Claude Code 2.1.209, Opus, high effort  
Isolation: `--safe-mode --tools "" --no-chrome --no-session-persistence`  
Reviewed: `docs/specification.md`, `docs/implementation-plan.md`  
Verdict: **GO WITH AMENDMENTS**

## Reviewer response

The reviewer found the design coherent, fail-closed, and non-mutating, and conditioned implementation on the following material amendments.

### High

#### H-1 — Isolation/control flags exceed the recorded verification baseline

The specification recorded only some flags from the mandatory analysis command and described the doctor's required-flag check without an explicit list. The reviewer required every mandatory flag and accepted effort value to be live-probed, explicitly listed, and tested individually for absence.

#### H-2 — Flag presence does not prove isolation behavior; compatibility had no upper tested bound

Argument-capture tests prove only that controls were requested. A later CLI could retain a flag while changing its semantics. The reviewer required a behavioral smoke check and a doctor warning whenever the installed version is newer than the highest tested version.

#### H-3 — GitHub PR metadata and diff capture have a force-push race

`gh pr view` and `gh pr diff` are separate requests. A force push between them could associate a diff hash with stale head metadata. The reviewer required reading `headRefOid` again after the diff and aborting on mismatch, recording GitHub's diff semantics, verifying `baseRefOid`/`headRefOid` availability, and testing the race.

### Medium

#### M-1 — Budget support behavior was underspecified

The reviewer requested a deterministic outcome when `--max-budget-usd` is unsupported. The amended design treats flag presence as required for this tested release, records whether Claude reports cost, and describes the flag as a request ceiling rather than a billing guarantee.

#### M-2 — Secret scanning omitted the question

The scanner must cover the entire assembled input. Generic secret detection must use named credential keys plus bounded value patterns rather than every assignment.

#### M-3 — Child-environment sanitization was vague

The design must name the customization variables removed, preserve authentication/provider variables, and test the resulting child environment.

#### M-4 — The local JSON Schema validator had an undefined subset

The validator must fail closed and support every keyword used by the bundled schemas, including types, required properties, enumerations, closed objects, and array bounds. Unsupported bundled constructs are build errors. Extra-property and invalid-enum outputs require exit 7.

#### M-5 — The exact authentication probe was not recorded

The grounded baseline must record `claude auth status --json`, its `loggedIn` success signal, and sanitization of identity fields before persistence or display.

#### M-6 — Compressed ZIP reproducibility can vary by toolchain

The package must use `ZIP_STORED` with normalized timestamps and modes so byte identity does not depend on zlib.

#### M-7 — Symlink checks can race

Supported systems must use `O_NOFOLLOW` for source files, with directory checks and an adversarial symlink test. A platform without the required primitive must fail closed rather than silently weaken the guarantee.

### Low

- Define material independent-review findings as severity `HIGH` or `MEDIUM`.
- Make the two-checkout installation criterion portable, while retaining AmanERP as the maintainer's verification environment.
- Record the resolved model returned by Claude when available.
- State explicitly that input hashes prove identity, not recover content.

## Disposition

| Finding | Disposition |
|---|---|
| H-1 | Accepted; specification and doctor tests amended before scaffolding. |
| H-2 | Accepted; highest-tested version warning and behavioral smoke added. |
| H-3 | Accepted; post-diff head re-verification and abort path added. |
| M-1 | Accepted with clarification; flag support is a compatibility prerequisite, enforcement is reported but not overstated. |
| M-2 | Accepted; scan scope and deterministic patterns amended. |
| M-3 | Accepted; explicit denylist/allowlist behavior and tests added. |
| M-4 | Accepted; validator keyword contract and negative tests added. |
| M-5 | Accepted; exact sanitized auth probe recorded. |
| M-6 | Accepted; package uses stored entries. |
| M-7 | Accepted; `O_NOFOLLOW` required on supported systems. |
| L-1 through L-4 | Accepted as documentation and gate clarifications. |

No finding was rejected or deferred.

## Live evidence added during disposition

- Claude Code: `2.1.209 (Claude Code)`.
- `claude auth status --json`: exit 0 with `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty`, and `subscriptionType: max`. Identity fields are not retained in plugin receipts.
- Required command flags and effort values are present in the local 2.1.209 help output.
- GitHub CLI: `2.92.0`.
- `gh pr view --json baseRefOid,headRefOid,...` returned both object IDs against a live GitHub PR.

