from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"
PLUGIN = ROOT / "plugins" / "amanerp-second-opinion"


class SubmissionPacketTests(unittest.TestCase):
    def test_advisory_contract_is_shallow_and_skill_owns_format_boundary(self) -> None:
        schema = json.loads(
            (PLUGIN / "references" / "advisory-schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("description", schema)
        self.assertEqual(schema["required"], ["output"])
        self.assertEqual(set(schema["properties"]), {"output"})
        payload_schema = schema["properties"]["output"]
        self.assertEqual(
            set(payload_schema["required"]),
            {
                "status",
                "verdict",
                "confidence",
                "executive_summary",
                "analysis",
                "material_risks",
                "conditions_that_change_it",
                "validation_steps",
            },
        )
        self.assertFalse(
            any(
                property_schema.get("type") == "object"
                for property_schema in payload_schema["properties"].values()
            )
        )
        for name in ("advisory-schema.json", "pr-review-schema.json"):
            contract = json.loads(
                (PLUGIN / "references" / name).read_text(encoding="utf-8")
            )
            self.assertEqual(contract["required"], ["output"])
            self.assertEqual(set(contract["properties"]), {"output"})
            self.assertEqual(contract["additionalProperties"], False)
        skill = (PLUGIN / "skills" / "independent-advisory" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("sole machine-output contract", skill)
        self.assertIn("--structured-output-attempts 2", skill)
        self.assertIn("--acknowledge-retry-cost", skill)

    def test_listing_uses_verified_amanerp_surfaces(self) -> None:
        listing = json.loads((SUBMISSION / "listing.json").read_text(encoding="utf-8"))

        self.assertEqual(listing["plugin_name"], "Second Opinion by AmanERP")
        self.assertEqual(listing["publisher"], "AmanERP")
        self.assertEqual(listing["submission_type"], "skills_only")
        self.assertEqual(listing["category"], "Productivity")
        self.assertEqual(len(listing["starter_prompts"]), 3)
        self.assertTrue(
            any("$independent-advisory" in item for item in listing["starter_prompts"])
        )
        self.assertTrue(
            any("$independent-pr-review" in item for item in listing["starter_prompts"])
        )

        for key in (
            "website_url",
            "support_url",
            "privacy_policy_url",
            "terms_of_service_url",
        ):
            parsed = urlparse(listing[key])
            self.assertEqual(parsed.scheme, "https", key)
            self.assertEqual(parsed.hostname, "amanerp.com", key)

        runtime = listing["runtime"]
        self.assertEqual(runtime["supported_surfaces"], ["Codex local"])
        self.assertIn("ChatGPT web", runtime["unsupported_surfaces"])
        self.assertIn("Codex cloud", runtime["unsupported_surfaces"])
        self.assertIn("not affiliated", listing["non_affiliation_notice"].lower())

    def test_exactly_five_positive_and_three_negative_cases(self) -> None:
        packet = json.loads(
            (SUBMISSION / "test-cases.json").read_text(encoding="utf-8")
        )
        positive = packet["positive"]
        negative = packet["negative"]

        self.assertEqual(len(positive), 5)
        self.assertEqual(len(negative), 3)
        identifiers = [case["id"] for case in positive + negative]
        self.assertEqual(len(identifiers), len(set(identifiers)))

        for case in positive:
            self.assertEqual(
                set(case),
                {
                    "id",
                    "title",
                    "user_prompt",
                    "prerequisites",
                    "fixture",
                    "expected_workflow",
                    "expected_result_shape",
                },
            )
            self.assertTrue(case["user_prompt"].strip())
            self.assertTrue(case["expected_workflow"])
            self.assertTrue(case["expected_result_shape"])

        for case in negative:
            self.assertEqual(
                set(case),
                {
                    "id",
                    "title",
                    "scenario",
                    "prerequisites",
                    "expected_safe_fallback",
                    "reason",
                },
            )
            self.assertTrue(case["expected_safe_fallback"])
            self.assertTrue(case["reason"])

    def test_submission_documents_and_manifest_assets_exist(self) -> None:
        for name in (
            "reviewer-guide.md",
            "release-notes.md",
            "policy-attestations.md",
            "checklist.md",
        ):
            self.assertTrue((SUBMISSION / name).is_file(), name)

        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        interface = manifest["interface"]
        asset_paths = [
            interface["composerIcon"],
            interface["logo"],
            *interface["screenshots"],
        ]
        self.assertGreaterEqual(len(interface["screenshots"]), 2)
        for relative in asset_paths:
            path = PLUGIN / relative.removeprefix("./")
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 0, relative)
        self.assertTrue(all(item.endswith(".png") for item in interface["screenshots"]))


if __name__ == "__main__":
    unittest.main()
