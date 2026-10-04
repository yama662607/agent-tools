#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx>=0.6.23", "lxml>=5.0"]
# ///
"""Scan a presentation deck (.pptx) for stale template terms, outdated years/dates,
and unfinished placeholders.

Usage:
  uv run scripts/scan_stale_terms.py deck.pptx [--current-year 2026] [--bad-words terms.txt]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from pptx import Presentation

STALE_PATTERNS = [
    (re.compile(r"\b(201[0-9]|202[0-5])\b"), "Outdated year (prior to 2026)"),
    (re.compile(r"\b(lorem\s+ipsum|dolor\s+sit|consectetur)\b", re.I), "Lorem ipsum filler text"),
    (re.compile(r"\b(TODO|FIXME|XXX+|TBD|PLACEHOLDER)\b", re.I), "Unfinished tag/placeholder"),
    (re.compile(r"(ここに(タイトル|テキスト|図|データ|入力)|サンプル(テキスト|データ)|仮置き|未定)"), "Japanese placeholder text"),
    (re.compile(r"\b(Your\s+Name|Author\s+Name|University\s+Name|Department\s+Name)\b", re.I), "Template identity placeholder"),
]


def scan_deck(pptx_path: Path, current_year: int = 2026, custom_bad_words: list[str] | None = None,
              allow_years: set[int] | None = None) -> list[dict]:
    prs = Presentation(pptx_path)
    findings = []
    allow_years = allow_years or set()
    custom_regex = None
    if custom_bad_words:
        escaped = [re.escape(w.strip()) for w in custom_bad_words if w.strip()]
        if escaped:
            custom_regex = re.compile(rf"\b({'|'.join(escaped)})\b", re.I)

    for slide_idx, slide in enumerate(prs.slides, 1):
        for shape_idx, shape in enumerate(slide.shapes, 1):
            text_content = ""
            if shape.has_text_frame:
                text_content = shape.text_frame.text
            elif shape.has_table:
                text_content = "\n".join(cell.text for row in shape.table.rows for cell in row.cells)

            if not text_content.strip():
                continue

            for pattern, reason in STALE_PATTERNS:
                for match in pattern.finditer(text_content):
                    if "year" in reason.lower():
                        y = int(match.group(0))
                        if y in allow_years:
                            continue
                        start = max(0, match.start() - 20)
                        end = min(len(text_content), match.end() + 20)
                        surrounding = text_content[start:end]
                        if re.search(r"(et\s+al|Phys|Rev|arXiv|Lett|vol|pp|doi|vs|比較|データ|\([0-9]{4}\)|[0-9]{4}\))", surrounding, re.I):
                            continue  # Allowed citation year

                    matched_text = match.group(0)
                    findings.append({
                        "slide": slide_idx,
                        "shape_name": shape.name,
                        "matched": matched_text,
                        "reason": reason,
                        "context": text_content.strip()[:80]
                    })

            if custom_regex:
                for match in custom_regex.finditer(text_content):
                    findings.append({
                        "slide": slide_idx,
                        "shape_name": shape.name,
                        "matched": match.group(0),
                        "reason": "Custom forbidden keyword",
                        "context": text_content.strip()[:80]
                    })

    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="presentation file")
    parser.add_argument("--current-year", type=int, default=2026, help="current year (default 2026)")
    parser.add_argument("--allow-years", type=str, default="", help="comma-separated list of allowed historical years (e.g. 2023,2024)")
    parser.add_argument("--bad-words", type=Path, help="file with one forbidden term per line")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    if not args.pptx.is_file():
        sys.exit(f"error: file {args.pptx} not found")

    custom_words = []
    if args.bad_words and args.bad_words.is_file():
        custom_words = args.bad_words.read_text(encoding="utf-8").splitlines()

    allowed_years = {int(y.strip()) for y in args.allow_years.split(",") if y.strip().isdigit()}
    findings = scan_deck(args.pptx, args.current_year, custom_words, allowed_years)

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("✓ No stale template terms or unfinished placeholders detected.")
        else:
            print(f"⚠ Found {len(findings)} stale or suspicious term(s):")
            for f in findings:
                print(f"  - Slide {f['slide']} [{f['shape_name']}]: '{f['matched']}' ({f['reason']})")
                print(f"    Context: {f['context']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
