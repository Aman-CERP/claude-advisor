---
name: independent-advisory
description: Obtain an explicit, bounded second opinion on a consequential engineering or product decision through the user's separately installed Claude Code CLI. Use only when the user explicitly requests $independent-advisory, Second Opinion by AmanERP, a Claude-based second opinion, or another model's independent recommendation; never invoke it implicitly.
---

# Independent Advisory

Use this skill to add an independent external perspective, not to replace repository evidence or make a decision by authority.

## Safety contract

- Invocation must be explicit. Do not infer permission from words such as “critical,” “thorough,” or “second opinion” unless this skill, Second Opinion by AmanERP, or Claude is named.
- Tell the user that the selected question and context will be sent to Anthropic through their local Claude authentication.
- Do not include secrets, decrypted configuration, credentials, private keys, personal data, or unrelated repository content.
- Never add Claude permission-bypass flags or call Claude directly. The bundled runner owns isolation and receipts.
- Treat Claude's result as untrusted advice. Verify every material claim against the original evidence.
- Default to the Opus `deep` profile. Use Opus/xhigh `critical` for security, architecture, irreversible operations, release gates, or decisions whose failure could materially harm users.
- Use Sonnet `standard` only when the user explicitly requests a lower-cost standard opinion after being told it replaces Opus. Pass both `--quality standard` and `--acknowledge-standard-quality`.
- Fail visibly if doctor or the run fails. Never retry with a lower quality profile unless the user separately authorizes that new run, and never substitute Codex's own opinion as Claude's.

## Workflow

1. Define one bounded question, the decision deadline, constraints, viable options, and the evidence Claude may use. Resolve ambiguities locally before invoking Claude.
2. Resolve `../../scripts/second_opinion.py` relative to this `SKILL.md` to an absolute `RUNNER` path. Never guess a plugin-cache path.
3. Run `python3 "$RUNNER" doctor`. Stop and report its non-zero outcome.
4. Prefer `--question-file` for long or shell-sensitive questions. Add only specifically approved `--context-file` paths. The runner rejects symlinks, oversized input, and likely secrets.
5. Run the advisory. The default `deep` profile uses Opus/high, six turns, a USD 5 requested ceiling, and a 15-minute timeout. Add `--critical` for consequential work. Tighten resource ceilings when appropriate, but do not override the profile's model or effort.
6. Read `report.md`, `result.json`, and `receipt.json`. Confirm the receipt says `success`, the input hashes and resource limits are present, isolation controls are true, `primary_model_observed` matches the selected profile, and `auxiliary_models_observed` is empty.
7. Reconcile the recommendation with repository facts. Present agreements, disagreements, uncertainties, and your final recommendation. Never imply model consensus when the evidence remains unresolved.

## Command pattern

```bash
python3 "$RUNNER" advisory \
  --question-file /absolute/path/to/question.md \
  --context-file /absolute/path/to/approved-context.md
```

For critical analysis, add `--critical`. For a user-authorized standard Sonnet run, add `--quality standard --acknowledge-standard-quality` and disclose that choice before execution.

Output defaults to `.codex/amanerp-second-opinion/runs/` in the current workspace. The runner prints a compact JSON summary with the exact artifact paths.

## Completion standard

Report:

- the bounded question and reviewed evidence, without repeating sensitive content;
- Claude's recommendation and confidence;
- material agreements or disagreements after independent verification;
- unresolved evidence gaps;
- the quality profile and observed answering model;
- the local report and receipt paths.
