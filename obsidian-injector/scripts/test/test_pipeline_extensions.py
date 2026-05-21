import unittest
import sys
import os
import json
import tempfile
import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules to test
import parse_distiller_output
import validate_operations
import templates
import distiller_payload


class TestParseDistillerOutput(unittest.TestCase):
    def test_clean_json(self):
        raw = '{"updates": [{"heading": "A", "op": "skip"}]}'
        parsed, was_clean = parse_distiller_output.parse_json(raw, strict=False)
        self.assertTrue(was_clean)
        self.assertEqual(parsed["updates"][0]["heading"], "A")

    def test_json_with_fences(self):
        raw = '```json\n{"updates": [{"heading": "A", "op": "skip"}]}\n```'
        parsed, was_clean = parse_distiller_output.parse_json(raw, strict=False)
        self.assertFalse(was_clean)
        self.assertEqual(parsed["updates"][0]["heading"], "A")

        # In strict mode, this should raise ValueError
        with self.assertRaises(ValueError):
            parse_distiller_output.parse_json(raw, strict=True)

    def test_json_with_prose_noise(self):
        raw = 'Here is the JSON you requested:\n```json\n{"updates": [{"heading": "A", "op": "skip"}]}\n```\nHope this helps!'
        parsed, was_clean = parse_distiller_output.parse_json(raw, strict=False)
        self.assertFalse(was_clean)
        self.assertEqual(parsed["updates"][0]["heading"], "A")

        # In strict mode, this should raise ValueError
        with self.assertRaises(ValueError):
            parse_distiller_output.parse_json(raw, strict=True)


class TestTemplatesFrontmatterFallback(unittest.TestCase):
    def test_patch_snippet_with_frontmatter(self):
        existing = "---\nrelated:\n  - \"[[Old Hub]]\"\n---\nSome text"
        result = templates.patch_snippet(
            heading="Concept",
            snippet="New info",
            source_basename="inbox.md",
            hub="New Hub",
            existing_content=existing
        )
        self.assertIn("[[New Hub]]", result)
        self.assertIn("## Note aggiuntive — Concept", result)

    def test_patch_snippet_without_frontmatter_fallback(self):
        existing = "# Concept Title\nSome content without YAML."
        result = templates.patch_snippet(
            heading="Concept",
            snippet="New info",
            source_basename="inbox.md",
            hub="New Hub",
            existing_content=existing
        )
        
        # Verify it has created a valid YAML frontmatter
        self.assertTrue(result.startswith("---"))
        self.assertIn("parent note: \"[[New Hub]]\"", result)
        self.assertIn("related:", result)
        self.assertIn("- \"[[New Hub]]\"", result)
        self.assertIn("AI: true", result)
        self.assertIn("last modified:", result)
        
        # Verify the date is today
        today = datetime.date.today().strftime("%Y, %m, %d")
        self.assertIn(today, result)
        
        # Verify it still contains original text and patched snippet
        self.assertIn("# Concept Title\nSome content without YAML.", result)
        self.assertIn("## Note aggiuntive — Concept", result)


class TestValidateOperations(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.tmp_dir.name) / "vault"
        self.target.mkdir()
        self.inbox_dir = Path(self.tmp_dir.name) / "inbox"
        self.inbox_dir.mkdir()

        # Create collision file in target vault
        self.collision_file = self.target / "Backpropagation.md"
        self.collision_file.write_text("Old content", encoding="utf-8")

        # Prepare dummy payload
        self.payload = {
            "schema_version": 1,
            "batches": [
                {
                    "inbox_file": str(self.inbox_dir / "Lezione 04.md"),
                    "concepts": [
                        {
                            "name": "Backpropagation",
                            "action_hint": "enrich",
                            "inbox_excerpt": "Backprop details...",
                            "vault_collision": {
                                "path": str(self.collision_file),
                                "match_type": "title"
                            }
                        },
                        {
                            "name": "Adam Optimizer",
                            "action_hint": "create",
                            "inbox_excerpt": "Adam details...",
                            "vault_collision": None
                        }
                    ]
                }
            ]
        }
        self.payload_file = Path(self.tmp_dir.name) / "payload.json"
        self.payload_file.write_text(json.dumps(self.payload), encoding="utf-8")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def run_validator(self, operations_list):
        ops_file = Path(self.tmp_dir.name) / "operations.json"
        ops_file.write_text(json.dumps({"updates": operations_list}), encoding="utf-8")

        validated_file = Path(self.tmp_dir.name) / "operations.validated.json"
        rejected_file = Path(self.tmp_dir.name) / "operations.rejected.json"

        # Mock sys.argv to call main()
        sys.argv = [
            "validate_operations.py",
            "--operations", str(ops_file),
            "--payload", str(self.payload_file),
            "--target", str(self.target),
            "--out", str(validated_file),
            "--rejected-out", str(rejected_file)
        ]

        try:
            validate_operations.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code

        validated = json.loads(validated_file.read_text(encoding="utf-8")) if validated_file.exists() else []
        rejected = json.loads(rejected_file.read_text(encoding="utf-8")) if rejected_file.exists() else []

        return exit_code, validated, rejected

    def test_valid_operations(self):
        # 1 valid patch, 1 valid write, 1 valid skip (should be ignored in validated.json)
        ops = [
            {
                "heading": "Backpropagation",
                "op": "patch",
                "path": str(self.collision_file),
                "source_basename": "Lezione 04.md",
                "snippet": "New backprop facts"
            },
            {
                "heading": "Adam Optimizer",
                "op": "write",
                "path": str(self.target / "Adam Optimizer.md"),
                "source_basename": "Lezione 04.md",
                "snippet": "New Adam facts"
            },
            {
                "heading": "Backpropagation",
                "op": "skip",
                "source_basename": "Lezione 04.md"
            }
        ]
        
        exit_code, validated, rejected = self.run_validator(ops)
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(validated), 2)
        self.assertEqual(len(rejected), 0)
        
        # Verify skips are not in validated.json
        ops_headings = [o["heading"] for o in validated]
        self.assertIn("Backpropagation", ops_headings)
        self.assertIn("Adam Optimizer", ops_headings)

    def test_invalid_operations_rejected(self):
        # 1 valid, 1 invalid (hallucinated heading) -> 50% rejection (should exit with 2)
        ops = [
            {
                "heading": "Backpropagation",
                "op": "patch",
                "path": str(self.collision_file),
                "source_basename": "Lezione 04.md",
                "snippet": "New backprop facts"
            },
            {
                "heading": "Hallucinated Concept",
                "op": "write",
                "path": str(self.target / "Hallucinated.md"),
                "source_basename": "Lezione 04.md",
                "snippet": "Fake concept info"
            }
        ]

        exit_code, validated, rejected = self.run_validator(ops)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(validated), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["op"]["heading"], "Hallucinated Concept")
        self.assertIn("not present in payload concepts", rejected[0]["reason"])

    def test_write_outside_target_rejected(self):
        ops = [
            {
                "heading": "Adam Optimizer",
                "op": "write",
                "path": str(Path(self.tmp_dir.name) / "Outside.md"),
                "source_basename": "Lezione 04.md",
                "snippet": "New Adam facts"
            }
        ]
        exit_code, validated, rejected = self.run_validator(ops)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(validated), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn("is not within the target folder", rejected[0]["reason"])

    def test_patch_path_mismatch_rejected(self):
        # Patching to a different path than the vault_collision in payload
        ops = [
            {
                "heading": "Backpropagation",
                "op": "patch",
                "path": str(self.target / "WrongPath.md"),
                "source_basename": "Lezione 04.md",
                "snippet": "New backprop facts"
            }
        ]
        exit_code, validated, rejected = self.run_validator(ops)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(validated), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn("does not match expected collision path", rejected[0]["reason"])

    def test_inbox_path_segment_rejected(self):
        # Targeting inside the inbox folder is forbidden
        ops = [
            {
                "heading": "Adam Optimizer",
                "op": "write",
                "path": str(self.inbox_dir / "Adam.md"),
                "source_basename": "Lezione 04.md",
                "snippet": "New Adam facts"
            }
        ]
        exit_code, validated, rejected = self.run_validator(ops)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(validated), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn("contains or points to a forbidden inbox directory segment", rejected[0]["reason"])


class TestDistillerPayload(unittest.TestCase):
    def test_expand_to_double_newline(self):
        content = "Para 1.\n\nPara 2 (concept match).\n\nPara 3."
        # Match starts at index 9 ('Para 2') and ends at 32
        start, end = 9, 32
        ns, ne = distiller_payload.expand_to_double_newline(content, start, end)
        self.assertEqual(ns, 9)
        self.assertEqual(ne, 32)
        self.assertEqual(content[ns:ne], "Para 2 (concept match).")

    def test_safe_truncate(self):
        text = "This is a paragraph.\n\nThis is a code block:\n```python\nprint(1)\n```\n\nFinal block."
        # Truncating with limit that lands around code block end (char index ~65)
        truncated = distiller_payload.safe_truncate(text, 68)
        self.assertTrue(truncated.endswith("```"))
        self.assertNotIn("Final block.", truncated)
        
        # Fallback to hard limit if max_chars is extremely short
        short_truncated = distiller_payload.safe_truncate(text, 10)
        self.assertEqual(short_truncated, "This is a")


if __name__ == "__main__":
    unittest.main()
