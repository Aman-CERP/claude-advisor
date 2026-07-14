#!/usr/bin/env python3
"""Create a deterministic, uncompressed Claude Advisor plugin archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "claude-advisor"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
EXCLUDED_NAMES = {".DS_Store", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included_files() -> list[Path]:
    files: list[Path] = []
    for path in PLUGIN.rglob("*"):
        relative = path.relative_to(PLUGIN)
        if any(part in EXCLUDED_NAMES for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise SystemExit(f"refusing to package symlink: {relative}")
        if stat.S_ISREG(info.st_mode):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(PLUGIN).as_posix())


def version() -> str:
    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    value = manifest.get("version")
    if not isinstance(value, str) or not value:
        raise SystemExit("plugin manifest has no version")
    return value


def write_archive(destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    os.close(fd)
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True
        ) as archive:
            for path in included_files():
                relative = path.relative_to(PLUGIN).as_posix()
                name = f"claude-advisor/{relative}"
                info = zipfile.ZipInfo(name, FIXED_TIME)
                info.create_system = 3
                executable = os.access(path, os.X_OK)
                mode = 0o755 if executable else 0o644
                info.external_attr = (stat.S_IFREG | mode) << 16
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, destination)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    checksum = destination.with_suffix(destination.suffix + ".sha256")
    checksum.write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    archive = args.output_dir / f"claude-advisor-{version()}.zip"
    digest = write_archive(archive)
    print(json.dumps({"archive": str(archive), "sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
