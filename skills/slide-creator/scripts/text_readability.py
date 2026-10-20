"""Static 16pt floor for native slide text and tables (no rendering or mutation)."""
import json
from pathlib import Path

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
MIN_FONT_PT = 16
EXCEPTION_ROLES = {"page-number", "source", "axis-label", "auxiliary-label"}


def load_exceptions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"exceptions"} or not isinstance(data["exceptions"], list):
        raise ValueError('expected {"exceptions": [...]}')
    seen = set()
    for entry in data["exceptions"]:
        if not isinstance(entry, dict) or set(entry) != {"slide", "shape", "role", "reason"}:
            raise ValueError("each exception needs slide, shape, role and reason only")
        if type(entry["slide"]) is not int or entry["slide"] < 1:
            raise ValueError("exception slide must be a positive integer (1-based)")
        if not isinstance(entry["shape"], str) or not entry["shape"].strip():
            raise ValueError("exception shape must be an exact, non-empty shape name")
        if not isinstance(entry["role"], str) or entry["role"] not in EXCEPTION_ROLES:
            raise ValueError(f"exception role must be one of {sorted(EXCEPTION_ROLES)}")
        if not isinstance(entry["reason"], str) or not entry["reason"].strip():
            raise ValueError("exception reason must be non-empty")
        key = (entry["slide"], entry["shape"])
        if key in seen:
            raise ValueError(f"duplicate font-size exception: {key}")
        seen.add(key)
    return data["exceptions"]


def _find(element, path):
    return None if element is None else element.find(path, NS)


def _level(para) -> int:
    ppr = _find(para, "a:pPr")
    return int(ppr.get("lvl", "0")) if ppr is not None else 0


def _list_defaults(style, level):
    return [_find(style, f"a:lvl{level + 1}pPr/a:defRPr"),
            _find(style, "a:defPPr/a:defRPr")]


def _inherited_bodies(shape, slide):
    ph = _find(shape._element, ".//p:ph")
    if ph is None:
        return [], "otherStyle"
    layout = slide.slide_layout
    layout_ph = next((item for item in layout.placeholders
                      if item.placeholder_format.idx == int(ph.get("idx", "0"))), None)
    kind = ph.get("type", "obj")
    bodies = []
    if layout_ph is not None:
        bodies.append(_find(layout_ph._element, "p:txBody"))
        kind = _find(layout_ph._element, ".//p:ph").get("type", "obj")
    title = kind in {"title", "ctrTitle"}
    body = kind in {"body", "subTitle", "obj", "chart", "tbl", "dgm", "media", "clipArt", "pic"}
    master_kind = "title" if title else "body" if body else kind
    master_ph = next((item for item in layout.slide_master.placeholders
                      if _find(item._element, ".//p:ph").get("type", "obj") == master_kind), None)
    if master_ph is not None:
        bodies.append(_find(master_ph._element, "p:txBody"))
    return [item for item in bodies if item is not None], (
        "titleStyle" if title else "bodyStyle" if body else "otherStyle"
    )


def _size_defaults(para, text_body, inherited_bodies, master_style, default_style):
    level = _level(para)
    if not 0 <= level <= 8:
        raise ValueError(f"invalid paragraph level {level}")
    props = [_find(para, "a:pPr/a:defRPr")]
    props += _list_defaults(_find(text_body, "a:lstStyle"), level)
    for body in inherited_bodies:
        inherited_para = next((p for p in body.findall("a:p", NS) if _level(p) == level), None)
        props.append(_find(inherited_para, "a:pPr/a:defRPr"))
        props += _list_defaults(_find(body, "a:lstStyle"), level)
    props += _list_defaults(master_style, level)
    props += _list_defaults(default_style, level)
    return props


def _font_size(run_props, defaults):
    for props in [run_props, *defaults]:
        if props is not None and props.get("sz") is not None:
            size = int(props.get("sz")) / 100
            if size <= 0:
                raise ValueError("font size must be positive")
            return size
    return None


def _font_scale(bodies):
    for body in bodies:
        body_pr = _find(body, "a:bodyPr")
        if body_pr is None:
            continue
        for child in body_pr:
            if child.tag == f"{{{NS['a']}}}normAutofit":
                scale = int(child.get("fontScale", "100000")) / 100000
                if scale <= 0:
                    raise ValueError("autofit fontScale must be positive")
                return scale
            if child.tag in {f"{{{NS['a']}}}noAutofit", f"{{{NS['a']}}}spAutoFit"}:
                return 1
    return 1


def _shapes(shapes):
    for shape in shapes:
        if hasattr(shape, "shapes"):  # nested groups
            yield from _shapes(shape.shapes)
        else:
            yield shape


def _text_bodies(shape):
    if shape.has_text_frame:
        yield "", shape.text_frame._txBody
    if shape.has_table:
        for row_idx, row in enumerate(shape.table.rows, 1):
            for col_idx, cell in enumerate(row.cells, 1):
                if not cell.is_spanned:
                    yield f" cell {row_idx},{col_idx}", cell.text_frame._txBody


def check_text_sizes(prs, exceptions: list[dict]) -> tuple[list[str], list[str]]:
    issues, exempted = [], []
    allowlist = {(entry["slide"], entry["shape"]): entry for entry in exceptions}
    matches = {key: 0 for key in allowlist}
    default_style = _find(prs._element, "p:defaultTextStyle")
    for slide_idx, slide in enumerate(prs.slides, 1):
        for shape in _shapes(slide.shapes):
            inherited, style_kind = _inherited_bodies(shape, slide)
            master_style = _find(slide.slide_layout.slide_master._element, f"p:txStyles/p:{style_kind}")
            key = (slide_idx, shape.name)
            matched_text = False
            for cell_label, body in _text_bodies(shape):
                for para_idx, para in enumerate(body.findall("a:p", NS), 1):
                    segments = []
                    for node in para:
                        if node.tag in {f"{{{NS['a']}}}r", f"{{{NS['a']}}}fld"}:
                            text = _find(node, "a:t")
                            if text is not None and (text.text or "").strip():
                                segments.append((text.text, _find(node, "a:rPr")))
                    # Inspect the equation's base size, not its intrinsic sub/superscripts.
                    math_text = "".join(node.text or "" for node in para.findall(".//m:t", NS))
                    if math_text.strip():
                        segments.append((math_text, None))
                    if not segments:
                        continue
                    matched_text = True
                    where = f"slide {slide_idx}, shape {shape.shape_id} {shape.name!r}{cell_label}, paragraph {para_idx}"
                    try:
                        defaults = _size_defaults(para, body, inherited, master_style, default_style)
                        scale = _font_scale([body, *inherited])
                        sizes = [(text, _font_size(props, defaults)) for text, props in segments]
                        for text, size in sizes:
                            sample = " ".join(text.split())[:60]
                            if size is None:
                                issues.append(f"{where}: unresolved font size for {sample!r}; set an explicit size")
                            elif size * scale + 1e-9 < MIN_FONT_PT:
                                message = f"{where}: {size * scale:g}pt < {MIN_FONT_PT}pt for {sample!r}"
                                if key in allowlist:
                                    entry = allowlist[key]
                                    exempted.append(f"{message} ({entry['role']}: {entry['reason']})")
                                else:
                                    issues.append(message)
                    except ValueError as error:
                        issues.append(f"{where}: invalid font size/style: {error}")
            if key in matches and matched_text:
                matches[key] += 1
    for key, count in matches.items():
        if count != 1:
            issues.append(f"font-size exception {key}: matched {count} text shapes; expected exactly one")
    return issues, exempted
