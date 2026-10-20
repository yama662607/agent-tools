#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10.0"]
# ///
"""Extract figure references, captions, and labels from LaTeX/Markdown paper sources,
and rasterize vector PDF figures to high-resolution 300dpi PNGs for presentation slides.

Usage:
  uv run scripts/extract_paper_assets.py paper.tex --out-dir assets/figures
  uv run scripts/extract_paper_assets.py paper.md --out-dir assets/figures
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

INCLUDEGRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\[(.*?)\])?\{([^}]+)\}"
)
CAPTION_RE = re.compile(
    r"\\caption(?:\[(.*?)\])?\{((?:[^{}]|\{[^{}]*\})*)\}"
)
LABEL_RE = re.compile(
    r"\\label\{([^}]+)\}"
)
GRAPHICSPATH_RE = re.compile(
    r"\\graphicspath\{((?:\{[^}]+\})+)\}"
)
MD_IMAGE_RE = re.compile(
    r"!\[(.*?)\]\((.*?)\)"
)


def rasterize_pdf_figure(pdf_path: Path, out_png: Path, dpi: int = 300) -> bool:
    """Rasterize a single-page PDF figure to PNG using pdftoppm or mutool if available."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    prefix = out_png.with_suffix("")
    # Try pdftoppm first (poppler)
    if shutil.which("pdftoppm"):
        cmd = ["pdftoppm", "-png", "-r", str(dpi), "-singlefile", str(pdf_path), str(prefix)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and out_png.exists():
            return True
    # Try sips on macOS
    if sys.platform == "darwin" and shutil.which("sips"):
        cmd = ["sips", "-s", "format", "png", str(pdf_path), "--out", str(out_png)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and out_png.exists():
            return True
    return False


def resolve_figure_file(raw_name: str, base_dir: Path, graphicspaths: list[Path]) -> Path | None:
    name = raw_name.strip()
    candidates = [name]
    if not any(name.lower().endswith(ext) for ext in [".pdf", ".png", ".jpg", ".jpeg"]):
        for ext in [".pdf", ".png", ".jpg", ".jpeg"]:
            candidates.append(name + ext)
    search_dirs = [base_dir] + graphicspaths
    for d in search_dirs:
        for c in candidates:
            p = (d / c).resolve()
            if p.is_file():
                return p
    return None


def parse_tex(content: str, base_dir: Path) -> list[dict]:
    graphicspaths = []
    for m in GRAPHICSPATH_RE.finditer(content):
        paths = re.findall(r"\{([^}]+)\}", m.group(1))
        for p in paths:
            graphicspaths.append((base_dir / p).resolve())

    figures = []
    # Split into figure environments if possible, or scan sequentially
    fig_envs = re.finditer(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", content, re.DOTALL)
    matched_positions = []
    for env in fig_envs:
        block = env.group(1)
        cap_m = CAPTION_RE.search(block)
        lbl_m = LABEL_RE.search(block)
        caption = cap_m.group(2).strip() if cap_m else ""
        label = lbl_m.group(1).strip() if lbl_m else ""
        for inc in INCLUDEGRAPHICS_RE.finditer(block):
            raw_path = inc.group(2).strip()
            figures.append({
                "raw_path": raw_path,
                "caption": caption,
                "label": label,
                "options": inc.group(1) or ""
            })
        matched_positions.append((env.start(), env.end()))

    # Also find any floating \includegraphics not enclosed in \begin{figure}
    for inc in INCLUDEGRAPHICS_RE.finditer(content):
        pos = inc.start()
        if any(start <= pos <= end for start, end in matched_positions):
            continue
        figures.append({
            "raw_path": inc.group(2).strip(),
            "caption": "",
            "label": "",
            "options": inc.group(1) or ""
        })
    return figures, graphicspaths


def parse_markdown(content: str) -> list[dict]:
    figures = []
    for m in MD_IMAGE_RE.finditer(content):
        caption = m.group(1).strip()
        raw_path = m.group(2).strip()
        figures.append({
            "raw_path": raw_path,
            "caption": caption,
            "label": "",
            "options": ""
        })
    return figures, []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file", type=Path, help="paper TeX or Markdown file")
    parser.add_argument("--out-dir", type=Path, default=Path("assets/figures"),
                        help="directory to output rasterized figure PNGs")
    parser.add_argument("--json", action="store_true", help="output inventory JSON to stdout")
    args = parser.parse_args()

    src = args.source_file.resolve()
    if not src.is_file():
        sys.exit(f"error: source file {src} not found")

    content = src.read_text(encoding="utf-8", errors="replace")
    if src.suffix.lower() in [".tex", ".latex"]:
        fig_items, gpaths = parse_tex(content, src.parent)
    else:
        fig_items, gpaths = parse_markdown(content)

    inventory = []
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for idx, item in enumerate(fig_items, 1):
        raw = item["raw_path"]
        resolved = resolve_figure_file(raw, src.parent, gpaths)
        png_path = None
        status = "not_found"

        if resolved:
            ext = resolved.suffix.lower()
            if ext == ".pdf":
                target_png = (args.out_dir / f"fig_{idx:02d}_{resolved.stem}.png").resolve()
                ok = rasterize_pdf_figure(resolved, target_png)
                if ok:
                    png_path = target_png
                    status = "rasterized"
                else:
                    status = "rasterize_failed"
            elif ext in [".png", ".jpg", ".jpeg"]:
                target_copy = (args.out_dir / f"fig_{idx:02d}_{resolved.name}").resolve()
                shutil.copy2(resolved, target_copy)
                png_path = target_copy
                status = "copied"
            else:
                status = "unsupported_format"

        inventory.append({
            "id": f"fig_{idx:02d}",
            "raw_name": raw,
            "source_file": str(resolved) if resolved else None,
            "slide_image": str(png_path) if png_path else None,
            "caption": item["caption"],
            "label": item["label"],
            "status": status
        })

    inv_file = args.out_dir / "inventory.json"
    inv_file.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print(f"Extracted {len(inventory)} figure reference(s) from {src.name}")
        print(f"Inventory saved to: {inv_file}")
        for item in inventory:
            print(f"  - [{item['status']}] {item['id']}: {item['raw_name']} -> {item['caption'][:40]}")


if __name__ == "__main__":
    main()
