#!/usr/bin/env python3
"""Dependency-free repository checks suitable for public CI."""

from __future__ import annotations

import json
import re
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "claude-advisor"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate_manifest() -> None:
    path = PLUGIN / ".codex-plugin" / "plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(manifest.get("name") == PLUGIN.name, "plugin name must match its folder")
    require(
        isinstance(manifest.get("version"), str)
        and bool(SEMVER.fullmatch(manifest["version"])),
        "invalid semver",
    )
    require(bool(manifest.get("description")), "plugin description is required")
    require(bool(manifest.get("author", {}).get("name")), "plugin author is required")
    require(
        manifest.get("skills") == "./skills/", "plugin skills path must be ./skills/"
    )
    interface = manifest.get("interface", {})
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "defaultPrompt",
    ):
        require(key in interface, f"plugin interface is missing {key}")
    for key in ("homepage", "repository"):
        require(
            str(manifest.get(key, "")).startswith("https://"), f"{key} must use https"
        )
    require(manifest.get("license") == "Apache-2.0", "license metadata mismatch")


def validate_marketplace() -> None:
    marketplace = json.loads(
        (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    require(marketplace.get("name") == "aman-cerp", "marketplace name mismatch")
    entries = marketplace.get("plugins", [])
    matches = [entry for entry in entries if entry.get("name") == "claude-advisor"]
    require(
        len(matches) == 1, "marketplace must contain exactly one claude-advisor entry"
    )
    entry = matches[0]
    require(
        entry.get("source") == {"source": "local", "path": "./plugins/claude-advisor"},
        "marketplace source mismatch",
    )
    require(
        entry.get("policy", {}).get("installation") == "AVAILABLE",
        "plugin must be available",
    )
    require(
        entry.get("policy", {}).get("authentication") in {"ON_INSTALL", "ON_USE"},
        "invalid auth policy",
    )


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"missing frontmatter: {path}")
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        fail(f"invalid frontmatter: {path}")
    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        require(bool(separator), f"invalid frontmatter line: {path}")
        values[key.strip()] = value.strip()
    require(
        set(values) == {"name", "description"},
        f"skill frontmatter has unsupported keys: {path}",
    )
    return values


def validate_skills() -> None:
    expected = {"claude-advisory", "claude-pr-review"}
    actual = {path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir()}
    require(actual == expected, "unexpected skill set")
    for name in sorted(expected):
        skill = PLUGIN / "skills" / name
        values = parse_frontmatter(skill / "SKILL.md")
        require(values["name"] == name, f"skill name mismatch: {name}")
        require(
            len(values["description"]) >= 80,
            f"skill description is not informative: {name}",
        )
        yaml = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        require(
            "allow_implicit_invocation: false" in yaml,
            f"skill must require explicit invocation: {name}",
        )
        require(f"${name}" in yaml, f"default prompt must name ${name}")


def validate_source_safety() -> None:
    forbidden = {
        "--dangerously-skip-permissions": "dangerous Claude permission bypass",
        "shell=True": "shell subprocess execution",
        "/Users/nirajkumar": "maintainer-specific absolute path",
        "[TODO:": "unfinished scaffold placeholder",
    }
    scanned_suffixes = {".md", ".json", ".yaml", ".py"}
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file() or path.suffix not in scanned_suffixes:
            continue
        if any(part in {".git", "dist", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle, label in forbidden.items():
            if needle in text:
                fail(f"{label} found in {path.relative_to(ROOT)}")
    runner = PLUGIN / "scripts" / "claude_advisor.py"
    require(bool(runner.stat().st_mode & stat.S_IXUSR), "runner must be executable")


def main() -> int:
    validate_manifest()
    validate_marketplace()
    validate_skills()
    validate_source_safety()
    print("project validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
