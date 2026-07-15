from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_release.py"


class ReleaseContractTests(unittest.TestCase):
    def run_validator(self, tag: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--tag", tag],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def test_release_contract_accepts_the_declared_version(self) -> None:
        version = json.loads(
            (
                ROOT
                / "plugins"
                / "amanerp-second-opinion"
                / ".codex-plugin"
                / "plugin.json"
            ).read_text(encoding="utf-8")
        )["version"]
        tag = f"v{version}"
        completed = self.run_validator(tag)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(tag, completed.stdout)

    def test_release_contract_rejects_a_mismatched_tag(self) -> None:
        completed = self.run_validator("v999.999.999")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("tag", completed.stderr.lower())


if __name__ == "__main__":
    unittest.main()
