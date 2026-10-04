#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.49"]
# ///
"""Export storyboard PNGs and inspect browser layout; requires Chrome or Chromium."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from playwright.sync_api import sync_playwright

INSPECT = """
() => {
  const issues = [];
  const tolerance = 2;
  const check = (rect, bounds, message) => {
    if (rect.width && rect.height && (
      rect.left < bounds.left - tolerance || rect.right > bounds.right + tolerance ||
      rect.top < bounds.top - tolerance || rect.bottom > bounds.bottom + tolerance
    )) issues.push(message);
  };
  for (const slide of document.querySelectorAll(".card .slide")) {
    const id = slide.dataset.slideId;
    const body = slide.querySelector(".content");
    const bounds = body.getBoundingClientRect();
    const title = slide.querySelector(".heading");
    const titleRect = title.getBoundingClientRect();
    check(titleRect, slide.getBoundingClientRect(), id + ": title outside slide");
    if (titleRect.bottom > bounds.top - tolerance) issues.push(id + ": title enters content area");
    for (const block of body.querySelectorAll(".block")) {
      const blockBounds = block.getBoundingClientRect();
      check(blockBounds, bounds, id + ": block outside content area");
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        if (!walker.currentNode.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(walker.currentNode);
        for (const rect of range.getClientRects()) {
          check(rect, bounds, id + ": text outside content area");
          check(rect, blockBounds, id + ": text outside its block");
        }
      }
      for (const img of block.querySelectorAll("img")) {
        if (!img.complete || !img.naturalWidth) issues.push(id + ": image failed to load");
        check(img.getBoundingClientRect(), bounds, id + ": image outside content area");
      }
    }
  }
  return [...new Set(issues)];
}
"""


def render_mock(source: Path, out: Path, channel: str = "chrome") -> dict:
    out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel=channel if channel != "chromium" else None)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(source.resolve().as_uri())
        page.evaluate("() => window.mockReady")
        page.wait_for_function("() => document.querySelector('.preview').clientWidth > 0")
        metadata = json.loads(page.locator("#mock-metadata").text_content())
        width, height = metadata["size"]["width"] * 96, metadata["size"]["height"] * 96
        page.set_viewport_size({"width": max(1440, math.ceil((width + 80) / .95)),
                                "height": max(1100, math.ceil((height + 180) / .94))})
        # Inspect unscaled slides; thumbnail scaling would hide small overflows.
        page.add_style_tag(content=".card .preview{width:var(--slide-w);height:var(--slide-h)}"
                                    ".card .slide{transform:none!important}")
        issues = page.evaluate(INSPECT)
        page.reload()
        page.evaluate("() => window.mockReady")
        for index, sid in enumerate(metadata["slide_ids"]):
            page.locator(f'.open-slide[data-index="{index}"]').click()
            page.locator("#detail-preview .slide").screenshot(path=str(out / f"slide-{index + 1:02d}.png"))
            page.locator("#close-detail").click()
        page.set_viewport_size({"width": 1440, "height": 1100})
        for start in range(0, len(metadata["slide_ids"]), 9):
            page.evaluate("""start => {
              document.querySelectorAll(".card").forEach((card, index) => {
                card.style.display = index >= start && index < start + 9 ? "" : "none";
              });
            }""", start)
            page.locator(".overview").screenshot(path=str(out / f"overview-{start // 9 + 1:02d}.png"))
        report = {**metadata, "layout_issues": issues, "browser_errors": errors,
                  "pages": len(metadata["slide_ids"]),
                  "page_images": [f"slide-{i + 1:02d}.png" for i in range(len(metadata["slide_ids"]))],
                  "overview_images": [f"overview-{i + 1:02d}.png" for i in range(
                      math.ceil(len(metadata["slide_ids"]) / 9))]}
        (out / "layout-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
        browser.close()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--channel", default="chrome", choices=["chrome", "msedge", "chromium"])
    args = parser.parse_args()
    report = render_mock(args.html, args.out, args.channel)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["layout_issues"] or report["browser_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
