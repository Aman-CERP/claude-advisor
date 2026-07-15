#!/usr/bin/env python3
"""Prove Git marketplace upgrades in an isolated, loopback-only Codex home."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


PLUGIN_NAME = "amanerp-second-opinion"
MARKETPLACE_NAME = "amanerp"
INITIAL_VERSION = "1.0.0"
UPDATED_VERSION = "1.1.0"


class SmokeFailure(RuntimeError):
    pass


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        del format, args


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        rendered = " ".join(command)
        raise SmokeFailure(
            f"command failed ({rendered}): "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    return completed


def write_marketplace(source: Path) -> None:
    marketplace = source / ".agents" / "plugins" / "marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "name": MARKETPLACE_NAME,
                "interface": {"displayName": "AmanERP smoke"},
                "plugins": [
                    {
                        "name": PLUGIN_NAME,
                        "source": {
                            "source": "local",
                            "path": f"./plugins/{PLUGIN_NAME}",
                        },
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_USE",
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_plugin(source: Path, version: str, marker: str) -> None:
    plugin = source / "plugins" / PLUGIN_NAME
    manifest = plugin / ".codex-plugin" / "plugin.json"
    skill = plugin / "skills" / "update-smoke" / "SKILL.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    skill.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "name": PLUGIN_NAME,
                "version": version,
                "description": "Isolated marketplace update smoke fixture",
                "author": {"name": "AmanERP"},
                "skills": "./skills/",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    skill.write_text(
        "---\n"
        "name: update-smoke\n"
        "description: Verify isolated Codex Git marketplace update behavior.\n"
        "---\n\n"
        f"MARKER: {marker}\n",
        encoding="utf-8",
    )


def installed_entry(raw: str) -> dict[str, Any]:
    payload = json.loads(raw)
    entries = payload.get("installed", []) if isinstance(payload, dict) else []
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("pluginId") == f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
    ]
    if len(matches) != 1:
        raise SmokeFailure("Codex did not report exactly one installed smoke plugin")
    return matches[0]


def assert_cached(codex_home: Path, version: str, marker: str) -> Path:
    cache = codex_home / "plugins" / "cache" / MARKETPLACE_NAME / PLUGIN_NAME / version
    skill = cache / "skills" / "update-smoke" / "SKILL.md"
    if not skill.is_file() or f"MARKER: {marker}" not in skill.read_text(
        encoding="utf-8"
    ):
        raise SmokeFailure(f"cached plugin {version} does not contain {marker!r}")
    return cache


def execute(codex: str) -> dict[str, Any]:
    git = shutil.which("git")
    if git is None:
        raise SmokeFailure("git is required")

    with tempfile.TemporaryDirectory(prefix="second-opinion-marketplace-") as raw:
        root = Path(raw)
        source = root / "source"
        bare = root / "served" / "marketplace.git"
        codex_home = root / "codex-home"
        source.mkdir()
        bare.parent.mkdir()
        codex_home.mkdir()

        write_marketplace(source)
        write_plugin(source, INITIAL_VERSION, "before-upgrade")
        run([git, "init", "-b", "main"], cwd=source)
        run([git, "config", "user.name", "Marketplace Smoke"], cwd=source)
        run(
            [git, "config", "user.email", "marketplace-smoke@example.invalid"],
            cwd=source,
        )
        run([git, "add", "."], cwd=source)
        run([git, "commit", "-m", "fixture: initial"], cwd=source)
        run([git, "clone", "--bare", str(source), str(bare)], cwd=root)
        run([git, "remote", "add", "origin", str(bare)], cwd=source)
        run([git, "-C", str(bare), "update-server-info"], cwd=root)

        handler = functools.partial(QuietHandler, directory=str(bare.parent))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            marketplace_url = f"http://{host}:{port}/{bare.name}"
            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)

            run(
                [codex, "plugin", "marketplace", "add", marketplace_url],
                cwd=root,
                env=env,
            )
            run(
                [codex, "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"],
                cwd=root,
                env=env,
            )
            initial_cache = assert_cached(codex_home, INITIAL_VERSION, "before-upgrade")

            write_plugin(source, UPDATED_VERSION, "after-upgrade")
            run([git, "add", "."], cwd=source)
            run([git, "commit", "-m", "fixture: update"], cwd=source)
            run([git, "push", "origin", "main"], cwd=source)
            run([git, "-C", str(bare), "update-server-info"], cwd=root)

            run(
                [
                    codex,
                    "plugin",
                    "marketplace",
                    "upgrade",
                    MARKETPLACE_NAME,
                ],
                cwd=root,
                env=env,
            )
            assert_cached(codex_home, UPDATED_VERSION, "after-upgrade")
            if initial_cache.exists():
                raise SmokeFailure(
                    "marketplace upgrade retained the stale cache version"
                )

            listing = run([codex, "plugin", "list", "--json"], cwd=root, env=env)
            entry = installed_entry(listing.stdout)
            if (
                entry.get("version") != UPDATED_VERSION
                or entry.get("enabled") is not True
            ):
                raise SmokeFailure(
                    "Codex did not report the upgraded plugin as enabled"
                )

            codex_version = run([codex, "--version"], cwd=root, env=env).stdout.strip()
            return {
                "status": "ok",
                "codex_version": codex_version,
                "marketplace": MARKETPLACE_NAME,
                "plugin": PLUGIN_NAME,
                "initial_version": INITIAL_VERSION,
                "updated_version": UPDATED_VERSION,
                "isolated_codex_home": True,
                "transport": "loopback_git_http",
                "stale_cache_removed": True,
            }
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-bin",
        default=shutil.which("codex"),
        help="Codex CLI executable (default: resolved codex)",
    )
    args = parser.parse_args(argv)
    if not args.codex_bin:
        print("marketplace update smoke failed: codex is required", file=sys.stderr)
        return 1
    try:
        print(json.dumps(execute(args.codex_bin), sort_keys=True))
    except (
        SmokeFailure,
        json.JSONDecodeError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"marketplace update smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
