#!/usr/bin/env python3
"""Dependency-free repository checks suitable for public CI."""

from __future__ import annotations

import json
import re
import stat
import struct
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "amanerp-second-opinion"
SUBMISSION = ROOT / "submission"
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
    require(
        manifest.get("author", {}).get("name") == "AmanERP",
        "plugin publisher must be AmanERP",
    )
    require(
        manifest.get("author", {}).get("email") == "hello@amanerp.com",
        "plugin support email mismatch",
    )
    require(
        interface.get("displayName") == "Second Opinion by AmanERP",
        "plugin display name mismatch",
    )
    require(
        interface.get("developerName") == "AmanERP",
        "plugin developer name mismatch",
    )
    require(interface.get("category") == "Productivity", "plugin category mismatch")
    prompts = interface.get("defaultPrompt")
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "invalid prompts")
    require(
        all(isinstance(prompt, str) and len(prompt) <= 128 for prompt in prompts),
        "starter prompts must be strings no longer than 128 characters",
    )
    for key in (
        "homepage",
        "repository",
    ):
        require(
            str(manifest.get(key, "")).startswith("https://"), f"{key} must use https"
        )
    require(
        manifest.get("homepage")
        == "https://amanerp.com/developer-tools/second-opinion",
        "plugin homepage mismatch",
    )
    require(
        manifest.get("repository")
        == "https://github.com/Aman-CERP/amanerp-second-opinion",
        "plugin repository mismatch",
    )
    for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        require(
            str(interface.get(key, "")).startswith("https://amanerp.com/"),
            f"{key} must use the AmanERP HTTPS origin",
        )
    for key in ("composerIcon", "logo"):
        relative = str(interface.get(key, "")).removeprefix("./")
        require(relative and (PLUGIN / relative).is_file(), f"missing asset: {key}")
    screenshots = interface.get("screenshots")
    require(
        isinstance(screenshots, list) and len(screenshots) >= 2,
        "at least two screenshots are required",
    )
    for relative_value in screenshots:
        relative = str(relative_value).removeprefix("./")
        require(relative.endswith(".png"), "screenshots must be PNG files")
        require((PLUGIN / relative).is_file(), f"missing screenshot: {relative}")
    icon = PLUGIN / str(interface["composerIcon"]).removeprefix("./")
    logo = PLUGIN / str(interface["logo"]).removeprefix("./")
    require(png_dimensions(icon) == (512, 512), "composer icon must be 512x512")
    require(png_dimensions(logo) == (1024, 1024), "logo must be 1024x1024")
    for relative_value in screenshots:
        width, height = png_dimensions(PLUGIN / str(relative_value).removeprefix("./"))
        require(width >= 1200 and height >= 675, "listing screenshot is too small")
    require(manifest.get("license") == "Apache-2.0", "license metadata mismatch")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    require(project.get("name") == manifest["name"], "project name mismatch")
    require(project.get("version") == manifest["version"], "project version mismatch")


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    require(
        len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n",
        f"invalid PNG asset: {path.relative_to(ROOT)}",
    )
    return struct.unpack(">II", header[16:24])


def validate_marketplace() -> None:
    marketplace = json.loads(
        (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    require(marketplace.get("name") == "amanerp", "marketplace name mismatch")
    require(
        marketplace.get("interface", {}).get("displayName") == "AmanERP",
        "marketplace display name mismatch",
    )
    entries = marketplace.get("plugins", [])
    matches = [
        entry for entry in entries if entry.get("name") == "amanerp-second-opinion"
    ]
    require(
        len(matches) == 1,
        "marketplace must contain exactly one amanerp-second-opinion entry",
    )
    entry = matches[0]
    require(
        entry.get("source")
        == {"source": "local", "path": "./plugins/amanerp-second-opinion"},
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
    expected = {"independent-advisory", "independent-pr-review"}
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
    runner = PLUGIN / "scripts" / "second_opinion.py"
    require(bool(runner.stat().st_mode & stat.S_IXUSR), "runner must be executable")


def validate_submission() -> None:
    listing = json.loads((SUBMISSION / "listing.json").read_text(encoding="utf-8"))
    require(listing.get("plugin_name") == "Second Opinion by AmanERP", "listing name")
    require(listing.get("publisher") == "AmanERP", "listing publisher mismatch")
    require(listing.get("submission_type") == "skills_only", "submission type")
    require(listing.get("category") == "Productivity", "listing category mismatch")
    for key in (
        "website_url",
        "support_url",
        "privacy_policy_url",
        "terms_of_service_url",
    ):
        require(
            str(listing.get(key, "")).startswith("https://amanerp.com/"),
            f"invalid listing URL: {key}",
        )
    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    interface = manifest["interface"]
    require(
        listing.get("website_url") == interface.get("websiteURL"),
        "listing and manifest website URLs differ",
    )
    require(
        listing.get("privacy_policy_url") == interface.get("privacyPolicyURL"),
        "listing and manifest privacy URLs differ",
    )
    require(
        listing.get("terms_of_service_url") == interface.get("termsOfServiceURL"),
        "listing and manifest terms URLs differ",
    )
    require(
        listing.get("starter_prompts") == interface.get("defaultPrompt"),
        "listing and manifest starter prompts differ",
    )
    require(
        listing.get("runtime", {}).get("supported_surfaces") == ["Codex local"],
        "listing must disclose its local-only surface",
    )
    require(
        "not affiliated" in str(listing.get("non_affiliation_notice", "")).lower(),
        "listing must contain the Anthropic non-affiliation notice",
    )
    packet = json.loads((SUBMISSION / "test-cases.json").read_text(encoding="utf-8"))
    positive = packet.get("positive", [])
    negative = packet.get("negative", [])
    require(len(positive) == 5, "submission requires exactly five positive tests")
    require(len(negative) == 3, "submission requires exactly three negative tests")
    identifiers = [case.get("id") for case in positive + negative]
    require(
        all(isinstance(identifier, str) and identifier for identifier in identifiers),
        "submission test IDs are required",
    )
    require(len(identifiers) == len(set(identifiers)), "duplicate submission test ID")
    for name in (
        "reviewer-guide.md",
        "release-notes.md",
        "policy-attestations.md",
        "checklist.md",
    ):
        require((SUBMISSION / name).is_file(), f"missing submission document: {name}")


def validate_public_identity() -> None:
    retired = (
        "claude-advisor",
        "claude_advisor.py",
        "claude-advisory",
        "claude-pr-review",
        "aman-cerp",
    )
    active_files = (
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / "pyproject.toml",
        ROOT / "Makefile",
        ROOT / "scripts" / "package_plugin.py",
    )
    active_files += tuple(
        path
        for path in PLUGIN.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md", ".py", ".yaml"}
    )
    for path in active_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in retired:
            require(
                token not in text,
                f"retired public identifier {token!r} found in {path.relative_to(ROOT)}",
            )


def validate_update_lifecycle() -> None:
    for relative in (
        "docs/update-policy.md",
        "scripts/marketplace_update_smoke.py",
        "scripts/validate_release.py",
    ):
        require((ROOT / relative).is_file(), f"missing update artifact: {relative}")

    runner = (PLUGIN / "scripts" / "second_opinion.py").read_text(encoding="utf-8")
    require('"--check-update"' in runner, "runner is missing explicit update check")
    require(
        'UPDATE_ENDPOINT = f"repos/{UPDATE_REPOSITORY}/releases/latest"' in runner,
        "runner update endpoint must remain fixed",
    )
    require(
        "codex plugin marketplace upgrade amanerp" in runner,
        "runner update guidance mismatch",
    )

    for name in ("independent-advisory", "independent-pr-review"):
        skill = (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        require(
            "Never run `doctor --check-update` automatically." in skill,
            f"skill must prohibit automatic update checks: {name}",
        )

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("release-contract:", "marketplace-update-smoke:"):
        require(target in makefile, f"Makefile is missing {target}")


def main() -> int:
    validate_manifest()
    validate_marketplace()
    validate_skills()
    validate_source_safety()
    validate_submission()
    validate_public_identity()
    validate_update_lifecycle()
    print("project validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
