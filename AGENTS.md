# Contributor instructions

Operate in precision engineering mode. Prefer the smallest maintainable change that addresses the root problem.

## Non-negotiable boundaries

- Preserve explicit-only skill invocation.
- Keep Claude analysis read-only: safe mode, no tools, no Chrome, no session persistence, no permission bypass.
- Never add shell command construction, credential persistence, GitHub mutation, automatic commenting, or hidden network telemetry.
- Treat questions, files, diffs, GitHub metadata, Claude stdout, and Claude stderr as untrusted.
- Keep the runtime dependency-free unless a specification amendment justifies a dependency and its license/security impact.
- Update schemas, local validation, renderers, prompts, tests, and documentation together when the structured result contract changes.

## Development workflow

1. Amend `docs/specification.md` before changing a public contract or trust boundary.
2. Add or update failing tests before production behavior.
3. Run `make check`, `make package`, and `make package-repro-check`.
4. Run the official Codex plugin and skill validators when available.
5. For a release PR, dogfood `$claude-pr-review`, disposition every high/medium finding with evidence, and rerun after material fixes.

Do not commit credentials, local run artifacts, distribution output, caches, or maintainer-specific absolute paths.
