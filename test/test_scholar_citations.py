"""Offline regression tests for the site-owned citation updater."""
import os
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "bin/update_scholar_citations.py"


class CitationUpdates(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        previous = os.getcwd()
        os.chdir(self.directory.name)
        self.addCleanup(os.chdir, previous)
        Path("_data").mkdir()
        Path("_data/socials.yml").write_text("scholar_userid: test-profile\n")
        self.output = Path("_data/citations.yml")
        self.client = Mock()
        self.client.fill.return_value = {
            "scholar_id": "test-profile",
            "publications": [{
                "author_pub_id": "test-profile:paper",
                "bib": {"title": "Test paper", "pub_year": "2026"},
                "num_citations": 3,
            }],
        }
        self.updater = runpy.run_path(str(SCRIPT))["get_scholar_citations"]
        mock_module = types.ModuleType("scholarly")
        mock_module.scholarly = self.client
        self.modules = patch.dict(sys.modules, {"scholarly": mock_module})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_missing_profile_fails_before_fetch(self):
        Path("_data/socials.yml").write_text("{}\n")
        with self.assertRaises(SystemExit) as failure:
            runpy.run_path(str(SCRIPT))
        self.assertEqual(failure.exception.code, 1)
        self.client.fill.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_first_fetch_without_cache_and_repeat_refresh(self):
        self.updater()
        result = yaml.safe_load(self.output.read_text())
        self.assertEqual(result["metadata"]["scholar_userid"], "test-profile")
        self.assertEqual(result["papers"]["test-profile:paper"]["citations"], 3)
        self.updater()
        self.assertEqual(self.client.fill.call_count, 2)

    def test_failed_fetch_preserves_cache(self):
        self.output.write_text("previous snapshot\n")
        self.client.fill.side_effect = RuntimeError("network failed")
        with self.assertRaises(SystemExit):
            self.updater()
        self.assertEqual(self.output.read_text(), "previous snapshot\n")

    def test_wrong_profile_and_partial_data_preserve_cache(self):
        self.output.write_text("previous snapshot\n")
        for response in [
            {"scholar_id": "other-profile", "publications": []},
            {"scholar_id": "test-profile", "publications": [{}]},
            {"scholar_id": "test-profile", "publications": [{"author_pub_id": "other:paper"}]},
        ]:
            with self.subTest(response=response):
                self.client.fill.return_value = response
                with self.assertRaises(ValueError):
                    self.updater()
                self.assertEqual(self.output.read_text(), "previous snapshot\n")

    def test_failed_atomic_replace_preserves_cache(self):
        self.output.write_text("previous snapshot\n")
        with patch("os.replace", side_effect=OSError("write failed")):
            with self.assertRaises(SystemExit):
                self.updater()
        self.assertEqual(self.output.read_text(), "previous snapshot\n")
        self.assertEqual(sorted(p.name for p in Path("_data").iterdir()),
                         ["citations.yml", "socials.yml"])


if __name__ == "__main__":
    unittest.main()
