# Update and release policy

Status: Active for v0.2.1

Last verified: 2026-07-15

Verified Codex CLI: 0.144.1

## Operator contract

Second Opinion never checks for or installs updates in the background. Review and
advisory skills do not make release-discovery requests. An operator can request a
read-only check explicitly:

```bash
python3 plugins/amanerp-second-opinion/scripts/second_opinion.py \
  doctor --check-update
```

The command uses the authenticated GitHub CLI to read only the latest stable
release for `Aman-CERP/amanerp-second-opinion` on `github.com`. It sends no
prompt, diff, context, receipt, credential, or usage data to AmanERP. The result reports whether the
installed base version is current, behind, or ahead. It does not run a Codex
plugin command.

## Distribution channels

| Channel | Discovery | Apply an update | Activation boundary |
|---|---|---|---|
| Git marketplace | GitHub Release notification, team announcement, or explicit doctor check | `codex plugin marketplace upgrade amanerp` | Start a new Codex task |
| Local development marketplace | Maintainer knows source changed | Apply a temporary Codex cachebuster and reinstall from the confirmed local marketplace | Start a new Codex task or restart the desktop app |
| ChatGPT workspace share | Workspace owner announces the shared revision | Install or refresh through the desktop plugin directory as supported | Start a new task |
| Public Plugin Directory | Directory listing and publisher release notes | OpenAI-reviewed update submitted and published through the portal | Follow the client prompt and start a new task |

OpenAI documents Git-backed marketplace add, pin, list, upgrade, and remove
commands in [Build plugins](https://learn.chatgpt.com/docs/build-plugins). The
same documentation requires a new session after CLI installation and a new task
or desktop restart after local plugin changes. The public directory has a
separate [submission and review flow](https://learn.chatgpt.com/docs/submit-plugins):
release notes identify an initial submission or update, OpenAI reviews it, and an
authorized publisher publishes only after approval. A GitHub release therefore
does not prove that the public directory has the same revision.

## Git-marketplace update

1. Read the GitHub release notes and verify the intended version and checksum.
2. Optionally run the explicit update check.
3. Refresh the Git marketplace:

   ```bash
   codex plugin marketplace upgrade amanerp
   ```

4. Confirm the installed version:

   ```bash
   codex plugin list --json
   ```

5. Start a new Codex task before invoking either skill.

Codex CLI 0.144.1 was integration-tested with a loopback Git marketplace in an
isolated `CODEX_HOME`. Refreshing the marketplace replaced the installed cached
plugin from 1.0.0 with 1.1.0, removed the stale cache directory, and reported the
new version enabled. Stable `codex plugin list --json` output did not expose a
separate update-available field in that release, so this project does not promise
an in-app update badge or button.

## Rollback

For a defective Git-marketplace release, pin an immutable known-good tag and
reinstall:

```bash
codex plugin marketplace remove amanerp
codex plugin marketplace add Aman-CERP/amanerp-second-opinion --ref v0.2.0
codex plugin add amanerp-second-opinion@amanerp
```

Start a new task. A pinned tag intentionally stops following later marketplace
updates. To return to the normal channel after a fixed release is available,
remove the pinned marketplace, add the repository without `--ref`, reinstall,
and start another new task.

Maintainers never replace a published ZIP, checksum, tag, or GitHub release. A
fix is a new patch or minor version. A public-directory rollback is a reviewed
listing update or superseding release, not a silent GitHub-side change.

## Maintainer release gate

Before pushing `vMAJOR.MINOR.PATCH`:

1. Classify compatibility under Semantic Versioning and finalize the changelog.
2. Run `make release-contract TAG=vMAJOR.MINOR.PATCH`.
3. Run `make check`, `make package`, and `make package-repro-check`.
4. Run `make marketplace-update-smoke` with the supported Codex CLI.
5. Validate the plugin and both skills with the official validators.
6. Install the release candidate in a clean local cache and run doctor plus safe
   synthetic live smokes.
7. Run the installed Opus critical adversarial PR review, disposition every
   critical/high/medium finding, and rerun after material fixes.
8. Publish the immutable tag and GitHub Release only after CI is green.
9. Announce the release. GitHub users can select Watch, Custom, Releases to
   receive release-only notifications; maintainers also post the release link in
   the team-owned release channel.
10. Submit a directory update separately, identify it as an update in release
    notes, wait for OpenAI review, and publish only with authorized approval.

[GitHub notification settings](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)
support release-only repository notifications. Notifications are the discovery
layer; explicit operator action remains the installation boundary.
