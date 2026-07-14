# PR #1 dogfood review and agreement record

Date: 2026-07-14  
Pull request: <https://github.com/Aman-CERP/claude-advisor/pull/1>  
Reviewer: installed `claude-advisor@aman-cerp` v0.1.0 using Claude Opus 4.8  
Initial reviewed head: `461099429d0350431683be232810e3764484666d`  
Base: `f62d2abb97a20bec962748ea4d181cc32c3a3cc1`  
Initial diff SHA-256: `d2075ba12547c973322c18b0fc3d28e1b91caa9b297609bf45fefd5abadac58b`

## Initial verdict

`comment`, medium confidence. Claude reported no critical or high security/correctness defect and two low-severity reliability findings. The run used critical mode, safe mode, an empty tool set, no Chrome, no session persistence, and the explicit sensitive-input override because the public test diff intentionally contains synthetic credential fixtures. The receipt reported two turns and USD 0.964286 against requested ceilings of ten turns and USD 10.

## Finding disposition

### F-1 — GitHub diff capture was unbounded before input assembly

Disposition: **accepted and fixed**.

Evidence: `gh_command` previously used `subprocess.run(..., capture_output=True)`, so a pathological PR diff could accumulate in memory before the 8 MiB assembled-input check. It now reads stdout/stderr incrementally with `selectors`, kills the child when the stream crosses its ceiling, caps metadata at 1 MiB and diffs at 6 MiB, and rejects with exit 8. A fake GitHub regression test emits 6 MiB plus one byte and requires pre-assembly rejection.

### F-2 — Doctor did not verify hidden `--max-turns` recognition

Disposition: **accepted and fixed**.

Evidence: Claude 2.1.209 accepts `--max-turns` but omits it from help. Doctor now invokes a zero-API parser probe with `--max-turns 1` followed by a deliberate sentinel unknown option. Success requires the CLI to identify the sentinel as unknown; a CLI that identifies `--max-turns` or accepts the sentinel fails preflight. A fake-Claude regression test covers the missing-control path.

## Verification gaps reconciled by Codex

- Public CI passed on Python 3.11 and 3.12.
- `make check` passed after both fixes with 23 tests.
- Ruff lint and formatting checks passed.
- Official Codex plugin and both skill validators passed before the initial PR review and will be rerun after the fixes.
- Deterministic package and SHA-256 verification passed before the initial review and will be rerun on the final head.
- Live Claude 2.1.209 doctor, structured advisory, turn-ceiling breach behavior, and no-tools side effects were exercised locally.

## Agreement status

Pending a second installed-plugin review of the updated PR head. Agreement requires no unresolved critical/high finding and explicit disposition of any new material finding.
