#!/usr/bin/env python3
"""Fail when public artifacts contain common sensitive-data patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".html", ".htm", ".json", ".md", ".txt", ".csv", ".tsv", ".log", ".js", ".mjs"}
BINARY_RISK_SUFFIXES = {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}
SKILL_ROOT = Path(__file__).resolve().parent.parent
# These files are generated from scripts/make_sample.py in public mode and must
# be visually reviewed before replacement. All other binary artifacts still fail.
APPROVED_PUBLIC_PREVIEWS = {
    (SKILL_ROOT / "assets" / "readme" / "report-full.png").resolve(),
    (SKILL_ROOT / "assets" / "readme" / "dashboard.png").resolve(),
    (SKILL_ROOT / "assets" / "readme" / "risk-analysis.png").resolve(),
    (SKILL_ROOT / "assets" / "readme" / "problem-list.png").resolve(),
}
PATTERNS = {
    "Windows absolute path": re.compile(r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings|Desktop|Downloads|AppData|Temp)[\\/]"),
    "Unix home path": re.compile(r"/(?:home|Users)/[^/\s]+/"),
    "mobile phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "Chinese ID": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "quality work order": re.compile(r"\b(?:ZG|QA|QC)[A-Za-z0-9-]{12,}\b", re.I),
}


def scan(path: Path, deny: list[str]) -> list[tuple[str, str, int, str]]:
    findings = []
    files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
    for file in files:
        if any(part in {".git", "__pycache__", "node_modules"} for part in file.parts):
            continue
        if file.suffix.lower() in BINARY_RISK_SUFFIXES and file.resolve() not in APPROVED_PUBLIC_PREVIEWS:
            findings.append((str(file), "binary artifact", 0, file.suffix.lower()))
            continue
        if file.suffix.lower() in BINARY_RISK_SUFFIXES:
            continue
        if file.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = file.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            findings.append((str(file), "non-UTF8 text", 0, "decode failed"))
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                match = pattern.search(line)
                if match:
                    findings.append((str(file), label, line_number, match.group(0)[:80]))
            for token in deny:
                if token and token in line:
                    findings.append((str(file), "deny-list token", line_number, token[:80]))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="扫描公开报告和仓库中的敏感信息")
    parser.add_argument("path")
    parser.add_argument("--deny", action="append", default=[], help="禁止出现的项目名、公司名或人员名；可重复")
    args = parser.parse_args(argv)
    findings = scan(Path(args.path), args.deny)
    if findings:
        for file, label, line, sample in findings:
            location = f":{line}" if line else ""
            print(f"{file}{location}: {label}: {sample}")
        print(f"发现 {len(findings)} 项潜在敏感内容。", file=sys.stderr)
        return 2
    print("敏感信息扫描通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
