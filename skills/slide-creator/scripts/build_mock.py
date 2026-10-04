#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["latex2mathml>=3.78"]
# ///
"""Build an offline HTML storyboard and Markdown view from one content plan."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import mimetypes
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "html-mock"
LAYOUTS = {"cover", "statement", "figure", "comparison", "process",
           "table", "equation", "summary", "free"}
BLOCKS = {"text", "list", "figure", "table", "equation", "placeholder"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def number(value: object, label: str, minimum: float = 0) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < minimum):
        raise ValueError(f"{label} must be a finite number >= {minimum}")
    return float(value)


def validate_plan(plan: dict) -> None:
    if not isinstance(plan, dict) or not isinstance(plan.get("title"), str):
        raise ValueError("plan needs a title and a slides array")
    size = plan.setdefault("size", {"width": 10, "height": 5.625})
    for key in ("width", "height"):
        number(size.get(key), f"size.{key}", 1)
    theme = plan.setdefault("theme", {})
    number(theme.setdefault("body_pt", 18), "theme.body_pt", 16)
    number(theme.setdefault("title_pt", 28), "theme.title_pt", 16)
    theme.setdefault("font_face", "Hiragino Kaku Gothic ProN")
    if not isinstance(theme["font_face"], str) or not theme["font_face"].strip():
        raise ValueError("theme.font_face must name a font")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", theme.setdefault("accent", "#2456a6")):
        raise ValueError("theme.accent must be a six-digit hex color")
    if not isinstance(plan.get("slides"), list) or not plan["slides"]:
        raise ValueError("slides must be a non-empty array")
    ids = set()
    for i, slide in enumerate(plan["slides"], 1):
        if not isinstance(slide, dict):
            raise ValueError(f"slide {i} must be an object")
        sid = slide.get("id", "")
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", sid) or sid in ids:
            raise ValueError(f"slide {i} needs a unique stable id")
        ids.add(sid)
        if not isinstance(slide.get("title"), str) or not slide["title"].strip():
            raise ValueError(f"slide {sid} needs a title")
        layout = slide.setdefault("layout", "summary")
        if layout not in LAYOUTS:
            raise ValueError(f"slide {sid}: unknown layout {layout!r}")
        blocks = slide.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            raise ValueError(f"slide {sid} needs non-empty blocks; use a placeholder for missing evidence")
        for key in ("claim", "question", "bridge", "status"):
            if key in slide and not isinstance(slide[key], str):
                raise ValueError(f"slide {sid}: {key} must be text")
        if not isinstance(slide.get("omit", []), list) or not all(
                isinstance(item, str) for item in slide.get("omit", [])):
            raise ValueError(f"slide {sid}: omit must contain text")
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") not in BLOCKS:
                raise ValueError(f"slide {sid}: unsupported block type")
            kind = block["type"]
            field = {"text": "text", "placeholder": "text", "figure": "src",
                     "equation": "latex"}.get(kind)
            if field and (not isinstance(block.get(field), str) or not block[field].strip()):
                raise ValueError(f"slide {sid}: {kind} needs {field}")
            if kind == "list" and (not isinstance(block.get("items"), list)
                                   or not all(isinstance(x, str) for x in block["items"])):
                raise ValueError(f"slide {sid}: list needs text items")
            if kind == "table":
                headers, rows = block.get("headers"), block.get("rows")
                if (not isinstance(headers, list) or not headers
                        or not isinstance(rows, list)
                        or any(not isinstance(row, list) or len(row) != len(headers) for row in rows)):
                    raise ValueError(f"slide {sid}: table rows must match the headers")
            if layout == "free":
                for key in ("x", "y", "w", "h"):
                    number(block.get(key), f"slide {sid} block.{key}", 0.01 if key in ("w", "h") else 0)


def image_uri(src: str, base: Path) -> str:
    path = (base / src).resolve()
    mime = mimetypes.guess_type(path.name)[0]
    if not mime or not mime.startswith("image/") or not path.is_file():
        raise ValueError(f"figure needs an existing local image: {src}")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def render_block(block: dict, base: Path, free: bool) -> str:
    kind = block["type"]
    label = f'<h3>{esc(block["label"])}</h3>' if block.get("label") else ""
    if kind in ("text", "placeholder"):
        body = f'<p>{esc(block["text"]).replace(chr(10), "<br>")}</p>'
    elif kind == "list":
        body = "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in block["items"]) + "</ul>"
    elif kind == "figure":
        body = f'<img src="{image_uri(block["src"], base)}" alt="{esc(block.get("caption", ""))}">'
    elif kind == "equation":
        if block.get("src"):
            body = f'<img src="{image_uri(block["src"], base)}" alt="{esc(block["latex"])}">'
        else:
            from latex2mathml.converter import convert
            try:
                body = convert(block["latex"], display="block")
            except Exception as error:
                raise ValueError("equation preview failed; simplify LaTeX or provide a local src preview") from error
    else:
        head = "".join(f"<th>{esc(x)}</th>" for x in block["headers"])
        rows = "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in row) + "</tr>"
                       for row in block["rows"])
        body = f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"
    if block.get("caption"):
        body += f'<p class="caption">{esc(block["caption"])}</p>'
    if block.get("source"):
        body += f'<p class="source">{esc(block["source"])}</p>'
    position = ""
    if free:
        position = ' style="' + ";".join(
            f"{css}:{block[key] * 96:g}px"
            for key, css in (("x", "left"), ("y", "top"), ("w", "width"), ("h", "height")))
        position += '"'
    return f'<div class="block block-{kind}"{position}>{label}{body}</div>'


def render_notes(slide: dict) -> str:
    fields = (("claim", "伝えたいこと"), ("question", "答える問い"),
              ("bridge", "次へのつながり"), ("status", "未解決・確認事項"))
    lines = [f"<dt>{label}</dt><dd>{esc(slide[key])}</dd>"
             for key, label in fields if slide.get(key)]
    if slide.get("omit"):
        lines.append("<dt>省いた内容・理由</dt><dd><ul>" +
                     "".join(f"<li>{esc(x)}</li>" for x in slide["omit"]) + "</ul></dd>")
    return "<dl>" + "".join(lines) + "</dl>" if lines else ""


def render_slide(slide: dict, index: int, total: int, base: Path) -> str:
    layout = slide["layout"]
    blocks = slide["blocks"]
    rendered = [render_block(b, base, layout == "free") for b in blocks]
    if layout in ("figure", "equation"):
        dominant = "figure" if layout == "figure" else "equation"
        primary = "".join(x for b, x in zip(blocks, rendered) if b["type"] == dominant)
        secondary = "".join(x for b, x in zip(blocks, rendered) if b["type"] != dominant)
        if not primary:
            raise ValueError(f"slide {slide['id']}: {layout} layout needs a {dominant} block")
        content = f'<div class="primary">{primary}</div><div class="secondary">{secondary}</div>'
    else:
        content = "".join(rendered)
    return (
        f'<section class="slide layout-{layout}" data-slide-id="{esc(slide["id"])}">'
        f'<header class="heading"><h2>{esc(slide["title"])}</h2></header>'
        f'<div class="content" style="--block-count:{len(blocks)}">{content}</div>'
        f'<footer class="page-number">{index} / {total}</footer></section>')


def markdown_view(plan: dict) -> str:
    lines = [f'# {plan["title"]}', ""]
    for key, label in (("audience", "対象"), ("goal", "目的")):
        if plan.get(key):
            lines += [f'{label}: {plan[key]}', ""]
    for i, slide in enumerate(plan["slides"], 1):
        lines += [f'## {i}. {slide["title"]}', "", f'ID: {slide["id"]}', ""]
        for key, label in (("claim", "伝えたいこと"), ("question", "答える問い"),
                           ("bridge", "次へのつながり"), ("status", "確認事項")):
            if slide.get(key):
                lines += [f'{label}: {slide[key]}', ""]
        for block in slide["blocks"]:
            if block.get("label"):
                lines += [f'### {block["label"]}', ""]
            kind = block["type"]
            if kind == "list":
                lines += [f"- {x}" for x in block["items"]]
            elif kind == "figure":
                lines += [f'図: {block["src"]}']
            elif kind == "equation":
                lines += ["$$", block["latex"], "$$"]
            elif kind == "table":
                row_text = lambda row: "| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |"
                lines += [row_text(block["headers"]), row_text(["---"] * len(block["headers"]))]
                lines += [row_text(row) for row in block["rows"]]
            else:
                prefix = "未確定: " if kind == "placeholder" else ""
                lines += [prefix + block["text"]]
            lines += [str(block[x]) for x in ("caption", "source") if block.get(x)] + [""]
        if slide.get("omit"):
            lines += ["省いた内容・理由:"] + [f"- {x}" for x in slide["omit"]] + [""]
    return "\n".join(lines)


def build_mock(source: Path, out: Path, overwrite: bool = False) -> dict:
    original = source.read_bytes()
    plan = json.loads(original)
    validate_plan(plan)
    targets = [out / "index.html", out / "plan.md"]
    if not overwrite and any(path.exists() for path in targets):
        raise ValueError("mock output already exists; use --overwrite to regenerate these two files")
    cards = []
    for i, slide in enumerate(plan["slides"], 1):
        cards.append(
            f'<article class="card" data-index="{i - 1}">'
            f'<button class="open-slide" data-index="{i - 1}" aria-label="{esc(str(i) + "枚目を開く")}">'
            f'<div class="preview">{render_slide(slide, i, len(plan["slides"]), source.parent)}</div>'
            f'<div class="card-title"><span>{i:02d}</span>{esc(slide["title"])}</div></button>'
            f'<div class="notes">{render_notes(slide)}</div></article>')
    size, theme = plan["size"], plan["theme"]
    font = json.dumps(theme["font_face"], ensure_ascii=False).replace("<", "\\3c ")
    css_vars = (f':root{{--slide-w:{size["width"] * 96:g}px;--slide-h:{size["height"] * 96:g}px;'
                f'--ratio:{size["width"] / size["height"]:g};--body:{theme["body_pt"]}pt;'
                f'--title:{theme["title_pt"]}pt;--font:{font};--accent:{theme["accent"]};}}')
    metadata = {"source_sha256": hashlib.sha256(original).hexdigest(),
                "slide_ids": [s["id"] for s in plan["slides"]], "size": size}
    substitutions = {
        "TITLE": esc(plan["title"]), "GOAL": esc(plan.get("goal", "")),
        "AUDIENCE": esc(plan.get("audience", "")),
        "COUNT": str(len(plan["slides"])), "CARDS": "\n".join(cards),
        "CSS": css_vars + (ASSETS / "mock.css").read_text(encoding="utf-8"),
        "JS": (ASSETS / "mock.js").read_text(encoding="utf-8"),
        "META": json.dumps(metadata, ensure_ascii=False).replace("<", "\\u003c"),
    }
    template = (ASSETS / "viewer.html").read_text(encoding="utf-8")
    document = re.sub(r"@@([A-Z]+)@@", lambda match: substitutions[match[1]], template)
    out.mkdir(parents=True, exist_ok=True)
    targets[0].write_text(document, encoding="utf-8")
    targets[1].write_text(markdown_view(plan), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        metadata = build_mock(args.plan.resolve(), args.out.resolve(), args.overwrite)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f'{len(metadata["slide_ids"])} slides: {args.out / "index.html"}')
    print(f"Markdown view: {args.out / 'plan.md'}")


if __name__ == "__main__":
    main()
