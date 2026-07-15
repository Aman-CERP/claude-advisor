#!/usr/bin/env python3
"""Validate immutable release identity before publishing artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "amanerp-second-opinion"
STABLE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def fail(message: str) -> None:
    print(f"release contract failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def declared_versions() -> dict[str, str]:
    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runner = (PLUGIN / "scripts" / "second_opinion.py").read_text(encoding="utf-8")
    runner_match = re.search(r'^PLUGIN_VERSION = "([^"]+)"$', runner, re.MULTILINE)
    require(runner_match is not None, "runner PLUGIN_VERSION is missing")
    return {
        "plugin manifest": str(manifest.get("version", "")),
        "Python project": str(project.get("project", {}).get("version", "")),
        "runner": runner_match.group(1),
    }


def validate(tag: str) -> str:
    require(
        STABLE_TAG.fullmatch(tag) is not None, "tag must be stable vMAJOR.MINOR.PATCH"
    )
    version = tag.removeprefix("v")
    for source, declared in declared_versions().items():
        require(declared == version, f"tag {tag} does not match {source} {declared!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(
        re.search(
            rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
            changelog,
            re.MULTILINE,
        )
        is not None,
        f"changelog has no dated {version} release heading",
    )

    notes = (ROOT / "submission" / "release-notes.md").read_text(encoding="utf-8")
    require(
        re.search(rf"^# V{re.escape(version)}(?:\s|$)", notes, re.MULTILINE)
        is not None,
        f"submission release notes do not declare {version}",
    )
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="immutable release tag")
    args = parser.parse_args(argv)
    version = validate(args.tag)
    print(f"release contract passed for v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
