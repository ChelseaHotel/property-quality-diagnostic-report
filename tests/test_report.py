#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_report  # noqa: E402
import make_sample  # noqa: E402
import scan_sensitive  # noqa: E402


class QualityReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_preflight_and_safe_generation(self):
        source = make_sample.create_sample(self.dir / "合成花园7月品质整改记录.xlsx")
        args = build_report.make_parser().parse_args([str(source), "--privacy", "safe", "--out", str(self.dir / "out")])
        config = build_report.load_config(None)
        rows, metadata = build_report.load_rows(str(source), args, config)
        preflight = build_report.build_preflight(str(source), rows, metadata, args, config)
        self.assertEqual(preflight["records"], 10)
        self.assertEqual(preflight["actual_issues"], 9)
        self.assertFalse(preflight["confirmation_required"])
        context, output_rows = build_report.build_context(rows, str(source), args, config, preflight)
        self.assertEqual(context["metrics"]["issues"], 9)
        self.assertEqual(context["metrics"]["pending"], 3)
        self.assertAlmostEqual(context["metrics"]["score"], 11.0)
        self.assertTrue(all(row["id"].startswith("ISSUE-") for row in output_rows))
        self.assertNotIn("测试人员", json.dumps(output_rows, ensure_ascii=False))

    def test_default_local_preserves_uploaded_business_data(self):
        source = make_sample.create_sample(self.dir / "测试1.xlsx")
        args = build_report.make_parser().parse_args([str(source)])
        self.assertEqual(args.privacy, "local")
        config = build_report.load_config(None)
        rows, metadata = build_report.load_rows(str(source), args, config)
        preflight = build_report.build_preflight(str(source), rows, metadata, args, config)
        context, output_rows = build_report.build_context(rows, str(source), args, config, preflight)
        serialized = json.dumps(output_rows, ensure_ascii=False)
        self.assertEqual(context["project"], "合成花园")
        self.assertIn("测试人员", serialized)
        self.assertIn("SYN-0001", serialized)
        self.assertIn("公共区域积尘", serialized)

    def test_multi_project_blocks(self):
        source = make_sample.create_sample(self.dir / "合成多项目.xlsx", multi_project=True)
        code = build_report.main([str(source), "--privacy", "safe", "--out", str(self.dir / "out")])
        self.assertEqual(code, 2)

    def test_public_requires_synthetic(self):
        source = make_sample.create_sample(self.dir / "合成花园.xlsx")
        code = build_report.main([str(source), "--privacy", "public", "--out", str(self.dir / "out")])
        self.assertEqual(code, 2)
        code = build_report.main([str(source), "--privacy", "public", "--synthetic", "--out", str(self.dir / "out")])
        self.assertEqual(code, 0)
        report = self.dir / "out" / "示例项目品质诊断报告.html"
        text = report.read_text(encoding="utf-8")
        self.assertNotIn(str(source), text)
        self.assertNotIn("测试人员", text)

    def test_generic_filename_is_not_a_project_conflict(self):
        source = make_sample.create_sample(self.dir / "测试1.xlsx")
        args = build_report.make_parser().parse_args([str(source), "--privacy", "safe"])
        config = build_report.load_config(None)
        rows, metadata = build_report.load_rows(str(source), args, config)
        preflight = build_report.build_preflight(str(source), rows, metadata, args, config)
        self.assertFalse(preflight["confirmation_required"])

    def test_sensitive_scanner(self):
        clean = self.dir / "clean.html"
        clean.write_text("<html>synthetic report</html>", encoding="utf-8")
        self.assertEqual(scan_sensitive.scan(clean, []), [])
        risky = self.dir / "risky.html"
        risky.write_text("C:/Users/private/Desktop/report.xlsx 13800138000", encoding="utf-8")
        self.assertGreaterEqual(len(scan_sensitive.scan(risky, [])), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
