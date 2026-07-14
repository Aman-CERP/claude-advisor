from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_plugin.py"
VALIDATOR = ROOT / "scripts" / "validate_project.py"


class PackagingTests(unittest.TestCase):
    def test_package_is_deterministic_and_contains_only_plugin_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            command = [sys.executable, str(PACKAGER), "--output-dir", str(output)]
            first = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            archive = Path(json.loads(first.stdout)["archive"])
            first_bytes = archive.read_bytes()
            second = subprocess.run(
                command, text=True, capture_output=True, check=False
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first_bytes, archive.read_bytes())

            checksum = archive.with_suffix(".zip.sha256").read_text().split()[0]
            self.assertEqual(checksum, hashlib.sha256(first_bytes).hexdigest())
            with zipfile.ZipFile(archive) as packaged:
                names = packaged.namelist()
                self.assertEqual(names, sorted(names))
                self.assertIn("claude-advisor/.codex-plugin/plugin.json", names)
                self.assertIn("claude-advisor/scripts/claude_advisor.py", names)
                self.assertFalse(
                    any("tests/" in name or "__pycache__" in name for name in names)
                )
                self.assertTrue(
                    all(
                        item.compress_type == zipfile.ZIP_STORED
                        for item in packaged.infolist()
                    )
                )

    def test_repository_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
