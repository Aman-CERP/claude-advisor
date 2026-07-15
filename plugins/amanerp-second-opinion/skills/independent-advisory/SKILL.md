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
- A same-model structured-output retry is also explicit: before requesting authorization, state the selected profile's exact aggregate and per-attempt requested ceilings (critical: USD 10 total, USD 5 each; deep/standard advisory: USD 5 total, USD 2.50 each). Use `--structured-output-attempts 2 --acknowledge-retry-cost` only after the user authorizes another attempt following that disclosure. A generic rerun permission given without the cost disclosure is insufficient. The runner retries only Claude's structured-output retry-exhausted outcome and never changes model, effort, input, prompt, schema, or isolation controls.
- The second attempt replays the identical request and is useful only for a transient/non-deterministic failure. Enabling two attempts divides the aggregate budget equally, so each attempt receives half the normal requested ceiling.
- Never run `doctor --check-update` automatically. Use it only when the user explicitly asks for update status, and never run a Codex marketplace command without separate authorization.

## Workflow

1. Define one bounded question, the decision deadline, constraints, viable options, and the evidence Claude may use. The question may request analysis topics or decision criteria, but it must not prescribe JSON keys, a schema, a response template, or another output-format contract. Translate such requests into plain analysis topics; the bundled schema is the sole machine-output contract. Resolve ambiguities locally before invoking Claude.
2. Resolve `../../scripts/second_opinion.py` relative to this `SKILL.md` to an absolute `RUNNER` path. Never guess a plugin-cache path.
3. Run `python3 "$RUNNER" doctor`. Stop and report its non-zero outcome.
4. Prefer `--question-file` for long or shell-sensitive questions. Before submission, remove competing machine-output instructions while preserving the substantive decision criteria. Add only specifically approved `--context-file` paths. The runner rejects symlinks, oversized input, and likely secrets.
5. Run the advisory. The default `deep` profile uses Opus/high, six turns, a USD 5 requested ceiling, and a 15-minute timeout. Add `--critical` for consequential work. Tighten resource ceilings when appropriate, but do not override the profile's model or effort.
6. Read `report.md`, `result.json`, and `receipt.json`. Confirm the receipt says `success`, the input hashes and resource limits are present, isolation controls are true, `primary_model_observed` matches the selected profile, and `auxiliary_models_observed` is empty.
7. Reconcile the recommendation with repository facts. Present agreements, disagreements, uncertainties, and your final recommendation. Never imply model consensus when the evidence remains unresolved.

## Command pattern

```bash
python3 "$RUNNER" advisory \
  --question-file /absolute/path/to/question.md \
  --context-file /absolute/path/to/approved-context.md
```

For critical analysis, add `--critical`. For a user-authorized standard Sonnet run, add `--quality standard --acknowledge-standard-quality` and disclose that choice before execution. For one user-authorized same-model retry after structured-output exhaustion, add `--structured-output-attempts 2 --acknowledge-retry-cost`; the timeout and budget remain aggregate across both attempts.

Output defaults to `.codex/amanerp-second-opinion/runs/` in the current workspace. The runner prints a compact JSON summary with the exact artifact paths.

## Completion standard

Report:

- the bounded question and reviewed evidence, without repeating sensitive content;
- Claude's recommendation and confidence;
- material agreements or disagreements after independent verification;
- unresolved evidence gaps;
- the quality profile and observed answering model;
- the local report and receipt paths.
