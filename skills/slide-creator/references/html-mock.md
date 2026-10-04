# HTML Storyboards Before PPTX

Use this for new decks and broad restructuring. A mock-only request ends at
the reviewed HTML; do not build a PPTX unless it is requested. Targeted edits
to an existing deck do not need a full new storyboard.

The mock exists to assess the title sequence, evidence, information density,
and what to remove or move to the appendix. Use actual intended text and
figures. Mark missing evidence visibly. Do not invent results to fill a
template, shrink body text to make it fit, or hide essential conditions in
review notes.

## Workflow

1. Draft a short Markdown title/claim spine. Record the audience question,
   evidence, necessary conditions, transitions, and omission decisions;
   follow [content-planning.md](content-planning.md) for technical content.
2. Put the intended slide content in `deck-plan.json`. From this point,
   the generated Markdown view and HTML share this source. The initial
   Markdown draft is a working note, not a second independently maintained
   manuscript.
3. Generate the mock:
   ```bash
   uv run "$SKILL_DIR/scripts/build_mock.py" deck-plan.json --out mock
   # After changing the plan:
   uv run "$SKILL_DIR/scripts/build_mock.py" deck-plan.json --out mock --overwrite
   ```
   `SKILL_DIR` is this skill's actual directory. Output: `mock/index.html`
   and `mock/plan.md`. The HTML embeds CSS, JavaScript, and local images;
   it opens without a server. It has an overview, slide detail navigation,
   and optional story/omission notes.
4. Open the HTML and export browser evidence:
   ```bash
   uv run "$SKILL_DIR/scripts/render_mock.py" mock/index.html --out mock/qa
   ```
   The default uses installed Google Chrome. Use `--channel msedge` for
   installed Edge, or `--channel chromium` when Playwright Chromium is
   already available. Do not install a browser merely to open the HTML.
   Output: `slide-NN.png`, paginated `overview-NN.png`, and
   `layout-report.json`. Inspect the overview and all relevant page images.
5. Review titles and transitions first, then the actual evidence and text.
   Check unexplained jumps, repetition, title/evidence disagreement, missing
   conditions, and whether to remove, split, or move content. Unresolved
   presenter-understanding items may be shown in a draft mock; do not mark
   them confirmed on the user's behalf. Existing delivery gates still apply.
6. Return adopted changes to the source and regenerate. Continue within the
   user's existing authorization; this stage does not impose routine approval
   on every deck. Ask about missing facts or decisions that materially change
   meaning when they cannot be resolved from the supplied evidence.
7. Build the PPTX from the same content data, preserving its titles, evidence,
   and necessary conditions. Read [creating.md](creating.md) or
   [template-following.md](template-following.md), then follow the existing
   BUILD → PACKAGE → EQUATIONS → VIDEO → VISUAL QA → ANIMATE → VERIFY order.
   HTML is a pre-build artifact; it does not replace PowerPoint rendering.

## Source format

Use `assets/html-mock/example.json` as a runnable example, not a fixed story
structure. Its content is explicitly a display sample, not research evidence.

```json
{
  "title": "研究の進捗",
  "audience": "研究室のメンバー",
  "goal": "次に調べる条件を決める",
  "size": {"width": 10, "height": 5.625},
  "theme": {"body_pt": 18, "title_pt": 28},
  "slides": [{
    "id": "result",
    "layout": "figure",
    "title": "条件Aと条件Bでは緩和時間が異なる",
    "question": "どの条件を詳しく調べるべきか",
    "bridge": "差の原因を切り分けるため、次の比較を計画する",
    "omit": ["全試行の図は付録へ。主な比較を読める大きさで示すため。"],
    "blocks": [
      {"type": "figure", "src": "figures/comparison.png",
       "caption": "ここに実際の単位・条件・誤差の意味を記載する"},
      {"type": "text", "text": "ここに図から読み取れる範囲を記載する"}
    ]
  }]
}
```

This is a format illustration. Replace the hypothetical title and explanatory
text with verified content before using it in a real deck.

- Required: deck `title`; non-empty `slides`; unique stable slide `id`,
  slide `title`, and non-empty `blocks`.
- Optional story metadata: `claim`, `question`, `bridge`, `status`
  (unresolved items), and `omit` (text entries with reasons/destinations).
- Optional style: physical `size.width/height` in inches; `theme.body_pt`,
  `title_pt`, `font_face`, and `accent` (hex color). Defaults: 10 ×
  5.625 inches, 18pt body, 28pt titles, Hiragino Kaku Gothic ProN.
- Body/title sizes below 16pt are rejected. Captions use the body size.
  `source` lines and page numbers use 12pt for secondary citations only;
  put interpretation-bearing conditions in normal text/captions.
- Blocks: `text`/`placeholder` with `text`; `list` with `items`;
  `figure` with local `src`; `table` with `headers` and matching
  `rows`; `equation` with `latex`. All can have `label`, `caption`,
  and `source`. A written source is not automatically verified evidence.
- Image paths are relative to the input plan. Use the intended figure assets.
  LaTeX is converted to browser MathML; for unsupported LaTeX provide an
  equation `src` preview image while retaining the original `latex`.

## Layouts and fidelity

Available layouts: `cover`, `statement`, `figure`, `comparison`,
`process`, `table`, `equation`, `summary`, and `free`.
These are options, not a required sequence. Item counts are variable. The
figure/equation layouts put that evidence in the primary region and other
blocks beside it. Comparison/process columns follow the block count; if
they become too narrow, split the slide or choose another arrangement.

`free` blocks additionally have `x, y, w, h` in inches relative to the
content region's top-left (0.5in from the left, 1.45in from the top).
The body ends 0.5in from the right and 0.48in from the bottom. This mode
supports individual arrangements without changing the shared viewer.

The HTML uses the chosen physical dimensions at 96 CSS px/in and point
sizes at 72pt/in. Only the whole canvas scales in overview/detail mode;
the slide's internal layout does not reflow with window width.
Font fallback, line wrapping, MathML versus OMML, and native charts can still
render differently in PowerPoint. Figure text and overlapping objects need
visual inspection; browser geometry checks are not full visual certification.

The renderer checks title/content invasion, elements/text outside their
content region, image loading, and browser errors. It exits nonzero on those
findings, but still writes images and the report for diagnosis. The report's
source hash identifies the input version represented by this HTML.

## Existing sources and hand edits

If an existing build script or managed `deckSpec` is already the primary
source, derive the mock plan from that current source as a disposable view.
Revise the primary source, then regenerate the view. The bundled generator
reads JSON plans; it does not automatically interpret arbitrary build scripts.

For a new deck, let the PPTX build script read the plan's actual content;
do not retype independent copies. If the deck moves into the managed
round-trip workflow, follow [roundtrip.md](roundtrip.md), reconcile accepted
PowerPoint changes into that source, and refresh the mock from it.
Do not regenerate a hand-edited live deck from a stale pre-build JSON plan.
There is no browser-edit/source-sync or universal HTML-to-editable-PPTX
conversion in this helper.
