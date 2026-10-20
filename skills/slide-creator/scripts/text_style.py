"""Explicit Japanese fonts for python-pptx edits; does not change other styling."""
from pptx.oxml.xmlchemy import OxmlElement


def set_japanese_font(run, font_face: str) -> None:
    """Set Latin, East Asian and complex-script typefaces on a text run."""
    if not isinstance(font_face, str) or not font_face.strip():
        raise ValueError("Japanese text requires a non-empty font_face")
    run.font.name = font_face
    rpr = run._r.get_or_add_rPr()
    for script, successors in (
        ("ea", ("a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst")),
        ("cs", ("a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst")),
    ):
        element = rpr.find(f"a:{script}", rpr.nsmap)
        if element is None:
            element = OxmlElement(f"a:{script}")
            rpr.insert_element_before(element, *successors)
        element.set("typeface", font_face)
