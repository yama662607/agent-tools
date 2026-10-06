# Japanese fonts, title reserve, and the 16pt gate

Use this reference when creating Japanese text or handling a font-size failure
from `verify_deck.py`. The gate is a lower safety floor, not a promise that a
slide is readable. Body text should normally be 18–24pt; keep the visual QA
and genre guidance in [qa-checklist.md](qa-checklist.md).

## Japanese text in pptxgenjs

Copy `scripts/text_options.mjs` from this skill beside the deck's build script
and retain it with that script. Import the helpers:

```javascript
import { japaneseTextOptions, singleLineTitleOptions } from "./text_options.mjs";

slide.addText("日本語とEnglishを明示した書体で表示する", japaneseTextOptions({
  x: 0.5, y: 1.4, w: 8, h: 0.8, fontSize: 22,
  fontFace: "Hiragino Kaku Gothic ProN",
}));
```

The default typeface is `Hiragino Kaku Gothic ProN`, and the default language
is `ja-JP`. Both can be set explicitly for the target environment. With
pptxgenjs 4.0.1, `fontFace` writes `a:latin`, `a:ea` and `a:cs` together. Do
not add an extra ZIP-wide font rewrite to that generation path. Rich-text
run options can override the box's options; intentional per-run fonts must
also have the right typeface. Pass the helper's options to table text too.

Explicit OOXML font names do not install/embed fonts or guarantee glyphs.
Choose a Japanese font available on the presentation computer and inspect
the deck there when it is delivered across Mac/Windows environments.

## Reserve width only for intended single-line titles

```javascript
slide.addText("条件の違いが結果の解釈に影響する", singleLineTitleOptions({
  x: 0.5, y: 0.35, w: 8.875, h: 0.7,
  fontSize: 26, align: "left", objectName: "scid:s001.title",
}, 10));  // slide width in inches; use 13.333333 for LAYOUT_WIDE
```

This adds **0.125in**, equivalent to 12 CSS pixels at 96px/in. This is not
12 points, and it is not a universal estimate of the text's width. The
horizontal alignment anchor remains unchanged:

| Alignment | New x | New width | Preserved anchor |
|---|---|---|---|
| left | x | w + 0.125 | left edge |
| center | x − 0.0625 | w + 0.125 | center |
| right | x − 0.125 | w + 0.125 | right edge |

The helper returns a fresh options object, sets zero internal margin unless
supplied, defaults to bold, disables wrapping and automatic shrink/resize,
and refuses geometry extending off the slide. Reserve the extra room inside
the layout's own safe margins; the helper does not check adjacent objects.
It accepts numeric inch coordinates and left/center/right alignment only.

Use `japaneseTextOptions` for intentionally multiline titles instead.
Disabling wrapping can cause overflow when a title is too long. Shorten it,
widen the region, or use a deliberate line break and move the body region;
do not treat the reserve as a substitute for PowerPoint PDF inspection.

Apply the reserve **once**. For managed round-trip source, store the final
adjusted `x`/`w` in the JSON block before initializing state. Rebuild those
coordinates directly with `japaneseTextOptions`, `wrap: false`, `fit: "none"`
and `margin: 0`; do not apply `singleLineTitleOptions` to coordinates already
measured/imported by `sync_from_pptx.py`. That would accumulate width/position
changes with each round trip.

## Japanese text when editing with python-pptx

Put this skill's `scripts` directory on your edit script's import path and
use `from text_style import set_japanese_font`. Apply it only to the runs
whose font should change:

```python
set_japanese_font(run, "Yu Gothic")
```

It sets `a:latin`, `a:ea` and `a:cs`, preserves font size, emphasis and
hyperlinks, and keeps the font children before hyperlink children in OOXML.
`run.font.name` alone sets the Latin typeface. Preserve existing template
fonts when no font change is requested.

## Static font-size verification

```bash
uv run scripts/verify_deck.py deck.pptx
# A deck with deliberately small source notes:
uv run scripts/verify_deck.py deck.pptx --font-size-exceptions text-exceptions.json
```

All non-empty native slide text defaults to a **16pt minimum**, including
table cells, nested groups, field text and the paragraph base size used by
`add_equation.py` for OMML equations.
Exactly 16pt passes; 15.99pt fails. The checker resolves run and paragraph
sizes, list levels, layout/master placeholder defaults, master text styles
and presentation defaults. Saved `normAutofit/fontScale` is included. An
unresolved or invalid size fails instead of being assumed safe. Blank
paragraphs and end-paragraph insertion formatting are not visible text.

Failures identify slide number, shape ID/name, paragraph, table cell when
applicable, effective size and a text sample. Correct the source and rebuild.
Shorten or split body content when it cannot fit at a readable size.

### Small auxiliary text needs an exact exception

Keep a small JSON file beside the build script. This is a font-size exception
list, not a deck manifest:

```json
{
  "exceptions": [
    {
      "slide": 1,
      "shape": "scid:s001.source",
      "role": "source",
      "reason": "Bibliographic credit only; the necessary explanation is in the body"
    }
  ]
}
```

Slide numbers are 1-based. `shape` is the exact PowerPoint shape name
(`objectName` in pptxgenjs); each entry must match exactly one non-empty text
shape. Roles are `page-number`, `source`, `axis-label`, `auxiliary-label`.
The reason is mandatory. Duplicate entries, missing/ambiguous targets,
unknown fields and a `body` role fail verification. The checker prints each
small exempted run with its role and reason. Exceptions only waive size;
all other structural checks still apply, and unknown sizes still fail.

Split body text and auxiliary text into separate shapes; a shape exception
covers all its text, including all cells if the shape is a table. A caption
or condition required to understand the claim belongs to readable content.
Do not call it an auxiliary label just to bypass a failure. Pass the same
exception file at PACKAGE and final VERIFY. No role is inferred from a small
size, bottom-of-slide position, name substring or slide-number field.

### What this gate cannot establish

The gate reads native text stored on slides and its supported style
inheritance. It does not measure image/SVG text, chart-owned labels, SmartArt,
standalone text objects owned by a layout/master, WordArt rendering, or font
availability. Internal OMML run/control formatting and sub/superscripts,
geometric scaling, and dynamic shrink
PowerPoint computes after editing still require visual inspection. A saved
fontScale can be checked; a future computed fontScale cannot be predicted.
No static pass proves text fits, contrast, visual hierarchy or room-scale
readability. Inspect the PowerPoint PDF and the intended display environment.
