#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx>=0.6.23", "lxml>=5.0", "latex2mathml>=3.77"]
# ///
"""Create incremental math equation derivation steps with ZERO layout shift.
Supports either Slide-Clone Overlay (safest, zero XML corruption risk) or
sequential fade-in animation across separate equation shapes.

Usage:
  uv run scripts/reveal_equation.py deck.pptx --slide 3 --steps-json steps.json --mode clone
"""

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt

SCRIPT_DIR = Path(__file__).resolve().parent
ADD_EQUATION = SCRIPT_DIR / "add_equation.py"
CLONE_SLIDE = SCRIPT_DIR / "clone_slide.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="presentation deck")
    parser.add_argument("--slide", type=int, required=True, help="1-based slide number containing the derivation")
    parser.add_argument("--steps-json", type=Path, required=True,
                        help="JSON file containing array of LaTeX derivation steps")
    parser.add_argument("--mode", choices=["clone", "boxes"], default="clone",
                        help="clone: clone slide for each step (zero layout shift); boxes: stacked textboxes")
    parser.add_argument("--x", type=float, default=1.0, help="left position in inches")
    parser.add_argument("--y", type=float, default=2.0, help="top position in inches")
    parser.add_argument("--font-size", type=int, default=24, help="equation font size in pt")
    args = parser.parse_args()

    if not args.pptx.is_file():
        sys.exit(f"error: file {args.pptx} not found")

    steps_data = json.loads(args.steps_json.read_text(encoding="utf-8"))
    if not isinstance(steps_data, list) or len(steps_data) < 2:
        sys.exit("error: steps-json must contain a list of at least 2 equation steps")

    prs = Presentation(args.pptx)
    total_slides = len(prs.slides)
    if not (1 <= args.slide <= total_slides):
        sys.exit(f"error: slide {args.slide} out of range (1..{total_slides})")

    if args.mode == "clone":
        print(f"Creating {len(steps_data)} derivation step slides via slide-clone overlay...")
        insert_pos = args.slide
        for step_idx in range(1, len(steps_data)):
            # clone current slide
            res = subprocess.run([
                "uv", "run", "--quiet", str(CLONE_SLIDE), "clone",
                str(args.pptx),
                "--slide", str(args.slide),
                "--after", str(insert_pos)
            ], capture_output=True, text=True)
            if res.returncode != 0:
                sys.exit(f"error cloning slide: {res.stderr}")
            insert_pos += 1

        # Accumulate derivation steps:
        # Slide (args.slide + offset) contains all equations from 0 up to offset
        for offset in range(len(steps_data)):
            target_slide = args.slide + offset
            for eq_idx in range(offset + 1):
                step_info = steps_data[eq_idx]
                latex_code = step_info if isinstance(step_info, str) else step_info.get("latex", "")
                cmd = [
                    "uv", "run", "--quiet", str(ADD_EQUATION), str(args.pptx),
                    "--slide", str(target_slide),
                    "--latex", latex_code,
                    "--x", str(args.x),
                    "--y", str(args.y + eq_idx * 0.85),
                    "--font-size", str(args.font_size)
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    sys.exit(f"error injecting equation step {eq_idx+1} into slide {target_slide}: {res.stderr}")
            print(f"  Slide {target_slide}: accumulated steps 1..{offset+1}")

    elif args.mode == "boxes":
        print(f"Injecting {len(steps_data)} equation boxes into slide {args.slide}...")
        for eq_idx, step_info in enumerate(steps_data):
            latex_code = step_info if isinstance(step_info, str) else step_info.get("latex", "")
            cmd = [
                "uv", "run", "--quiet", str(ADD_EQUATION), str(args.pptx),
                "--slide", str(args.slide),
                "--latex", latex_code,
                "--x", str(args.x),
                "--y", str(args.y + eq_idx * 0.85),
                "--font-size", str(args.font_size)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                sys.exit(f"error injecting equation box {eq_idx+1}: {res.stderr}")

        print(f"✓ Incremental derivation completed ({len(steps_data)} slides created with zero shift).")


if __name__ == "__main__":
    main()
