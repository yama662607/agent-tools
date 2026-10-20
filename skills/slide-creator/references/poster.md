# Posters (A0 academic poster)

A poster is not a slide deck. It is one page read standing up, at 1–2 m, by
people who walk past in seconds and stop only if the claim is clear. It is
consumed **standalone but interactively**: the author is usually beside it, so
the poster carries the claim and the evidence, and the author carries the
explanation. Never reuse talk slides as poster blocks; rebuild the argument for
one page.

Read [design-principles.md](design-principles.md) once, then the `poster`
profile in [design-profiles.md](design-profiles.md), then this file. Where the
profile and a slide rule disagree (font floors, density, bullets), the poster
wins.

## 1. Page setup

Use inches (PowerPoint/pptxgenjs/python-pptx all work in them). ISO sizes:

| Size | mm | inches (W x H, portrait) |
|---|---|---|
| A0 | 841 x 1189 | **33.11 x 46.81** |
| A1 | 594 x 841 | 23.39 x 33.11 |
| A2 | 420 x 594 | 16.54 x 23.39 |

Many Japanese venues state a board size in cm (e.g. width x height) instead of
an A size. Use the venue's numbers exactly, as a custom size, and run the
checkers with that page; `poster_check.py` reports "non-ISO" for it, which is
fine.

- **PowerPoint's maximum slide dimension is 56 in (142.2 cm).** A0 in either
  orientation (46.81 in long side) fits at **1:1 — build at full print size**.
  Only a poster with a side over 56 in needs scaling: build at 1/N of the
  print size, state the scale in the build script header, and pass
  `--scale N` to `poster_check.py` (and `verify_deck.py --profile poster`, for
  the size report) so floors and dpi are computed at print size. Do not use "Maximize/Ensure Fit"
  when changing the size of an existing hand-edited file; it rescales shapes.
- Orientation follows the venue; **portrait is the default** unless told
  otherwise. The A0 landscape page is 46.81 x 33.11 in.
- A poster is **one slide**. Notes, hidden slides, and animations do nothing
  in print.

pptxgenjs (see [creating.md](creating.md)): `pres.defineLayout({ name: "A0",
width: 33.11, height: 46.81 }); pres.layout = "A0";` python-pptx:
`prs.slide_width = Inches(33.11); prs.slide_height = Inches(46.81)`
(`Presentation()` starts as 4:3 with placeholder layouts you should not use).
`scripts/poster_scaffold.mjs` emits an empty A0 grid with named `scid:` blocks;
it is a starting point to copy into the build directory, not a template to
keep.

## 2. Grid, margins, bleed

- 3 columns for A0 portrait (4 only if figures are small multiples); 2 columns
  for A1/A2. Landscape A0: 4 columns, or a 3-column body under a full-width
  header. Gutter 0.5–0.7 in (13–18 mm); **all blocks snap to the column grid**,
  one left edge per column.
- Margins ≥ 1.0 in (25 mm). Printers trim and mount unevenly; keep every
  object ≥ 15 mm inside the page (`poster_check.py --margin-mm`). The pptx has
  no bleed box: if a background colour must reach the edge, extend that one
  shape past the page by ~5 mm (the checker allows full-page backgrounds) and
  ask the printer. Prefer a white or very light page: it prints reliably and
  saves a failed-edge risk.
- Read order is **top-to-bottom within a column, columns left to right**
  (Western and horizontal Japanese). Number blocks only if the order is not
  obvious from the grid; use native numbering, never typed numbers.
- Whitespace is structure: at least ~25% of the page empty, gutters larger
  than inner padding so blocks read as units.

## 3. Type scale (print size, A0)

Viewing distance 1–2 m. These are floors that `poster_check.py` enforces
(FAIL < 18 pt, WARN < 24 pt except references/credits shapes) plus targets:

| Element | Target (pt) | Floor (pt) |
|---|---|---|
| Title (claim-style, ≤ 2 lines) | 96–120 | 80 |
| Authors | 48–60 | 40 |
| Affiliations, poster ID | 36–40 | 28 |
| Section / block heads (assertion) | 54–64 | 48 |
| Body | 32–36 | 28 |
| Figure labels, axis text, captions | 26–30 | 24 |
| References, acknowledgements, funding | 20–24 | 18 (hard) |

A1 = x0.71, A2 = x0.5 of these. Body copy of ≥ 28 pt at A0 is what limits
word count: that is intended. One Japanese font family for text (Hiragino Kaku
Gothic ProN on this Mac; weight W3 body, W6/W7 heads, since regular-weight
Japanese looks faint at distance); keep equations in Cambria Math. Line
spacing ≥ 1.15. Left-aligned, ragged-right, ≤ ~35 full-width Japanese
characters per line for body (about 18–22 words in English): wider columns
tire the reader.

Native bullets only, as everywhere. Prefer 3–5 short items per block; a block
of prose paragraphs means the block is not finished.

## 4. Figures and resolution

**Effective dpi = visible pixels / placed inches at print size** (after
cropping). `poster_check.py` computes it for every picture: FAIL < 150, WARN
< 300. Targets: raster photos and microscopy ≥ 200 dpi, rasterised plots and
diagrams ≥ 300. A 10 in wide figure needs ≥ 3000 px for 300 dpi.

- Prefer vector for plots and schematics: export matplotlib as SVG/EMF/PDF-
  derived vector (PowerPoint takes SVG and EMF), or as PNG at `dpi=300` of the
  *final placed size* (set `figsize` in inches to the placed size so fonts
  come out at the intended pt: axis labels 24–28 pt, line width ≥ 3 pt,
  markers ≥ 12 pt).
- Do not upscale small images in PowerPoint; regenerate. Screenshots of
  slides/web pages are almost always < 150 dpi at A0.
- Simulation snapshots: render at the target pixel size directly; add a scale
  bar and the time stamp in the image at ≥ 24 pt equivalent. Videos cannot play
  on paper: use a frame sequence (time-lapse strip) and a QR link to the movie.
- Same palette and colormap rules as the figure section of
  design-profiles.md; colour must also survive a greyscale print.

## 5. Japanese conference poster structure

Top band (full width), then 3 columns of evidence, then a footer:

1. **Header**: poster ID (発表番号, where the venue places it, usually top-left,
   large), **claim-style title** (the result, not the topic), authors
   (presenter marked), affiliation, venue/date small. Logos small and few.
2. **One-sentence takeaway** directly below the header, ≥ 56 pt, the single
   sentence a passer-by should leave with. Test: can it be read aloud in one
   breath and be true on its own?
3. **3–5 evidence blocks**, each headed by an *assertion* (a full-sentence
   claim, "AはBによってCになる", not "結果" / "Results") and dominated by one
   figure. Typical flow: why it matters / approach (one schematic) / result 1 /
   result 2 (/ result 3). Methods stay minimal: what a reader needs to trust
   the figure.
4. **Conclusion** block (3 bullets max) at the end of the last column, echoing
   the takeaway in different words, plus the open question or next step if
   honest.
5. **Footer**: references (only those cited on the poster, 18–24 pt),
   acknowledgements/funding, contact, **QR code** to the paper/preprint/code/
   movie.

QR code: black on white with a quiet zone of ≥ 4 modules, error correction M,
short URL, side ≥ 1/10 of the scanning distance (≥ 6 in for 1.5 m). Generate
it as a high-resolution image or vector; verify by scanning a printed A4 mock.

## 6. Claim-first, assertion-evidence on a poster

Same principle as slides (design-principles.md), applied per block:

- The title and every block head are claims; reading only the heads (title,
  takeaway, block assertions, conclusion) must tell the whole story. Check this
  by listing them in order, as in the slide title-read-through.
- Each block = assertion + one proof object (figure/diagram/table) + at most
  2–3 lines interpreting it. A figure without an explicit "what to see"
  annotation (arrow, highlighted curve, label on the figure) is not finished.
- Put conditions (n, error-bar type, parameters) in the caption at ≥ 24 pt,
  because a reader cannot ask the slide.
- Do not invent claims or numbers for the poster: every number traces to the
  author's results (content-planning.md provenance rules apply).

## 7. What not to put on a poster

- The abstract pasted in, or paper paragraphs: a poster is not a printed paper.
  Target ≤ ~500–800 words in total body text.
- Long related-work or background sections, full derivations, parameter tables,
  more than ~5 references' worth of citations.
- Tables larger than ~5 x 5; chart-heavy appendices; every robustness check.
- Text over photos or gradients; 3D charts; dark full-bleed backgrounds (heavy
  ink, fingerprints, glare on laminate); thin low-contrast hairlines.
- Fake bullets/numbering, accent bars/stripes under heads, identical card
  grids (see qa-checklist "AI slop" tells), emoji icons.
- Animations, video, hover or click content. Anything dynamic becomes a QR link.
- Logos at title size, decorative clip art, unexplained jargon and
  abbreviations (define on first use).

## 8. Print export and colour

- **Hand the printer a PDF, not the pptx.** Fonts are embedded in the PDF;
  a pptx opened on a printer's Windows PowerPoint substitutes missing fonts
  (Hiragino is macOS-only). If the pptx itself must travel, use fonts present
  on both (Noto Sans JP, BIZ UDPGothic, Yu Gothic) and check with the printer.
- Export from PowerPoint: File > Export > PDF (or Save As PDF) with the
  **print-quality** option, not the "minimum size/electronic" one, since the
  latter downsamples pictures. Then confirm in the PDF: page size reads 841 x
  1189 mm (or the venue size), fonts embedded (Acrobat/Preview font list), and
  zoom to 100% on a figure to check sharpness.
- `scripts/powerpoint_pdf_qa.py` produces a PDF through PowerPoint for visual
  QA; its raster is capped to 3000 px on the long side (`--max-side`) and is
  **not** the print file. Use `--pdf-only` for posters and read the PDF.
- Colour: PowerPoint is RGB-only; printers convert to CMYK. Saturated
  greens/cyans/oranges and pure neon shift duller. Keep ≤ 4 colours, mid-
  saturation, dark ink on a light page, and prefer a paper proof or a printed
  A3 scaled test over trusting the screen.
- Mock-up check: print the whole page on A4 (scale 1/4 linear) and look at it
  at arm's length (~50 cm): that approximates A0 at 2 m. See the poster items
  in [qa-checklist.md](qa-checklist.md).

## 9. Tools

| Need | Command |
|---|---|
| Empty A0 grid with named `scid:` blocks (starting point) | `bun poster_scaffold.mjs [--landscape] [--cols 3] --out poster.pptx` (after `bun add pptxgenjs` in the build dir) |
| Structural gate | `uv run scripts/normalize_package.py p.pptx && uv run scripts/verify_deck.py p.pptx --profile poster` |
| Poster audit: size, fonts, dpi, bounds, overflow, overlap | `uv run scripts/poster_check.py p.pptx [--json] [--scale N] [--margin-mm 15]` |
| PDF for visual QA | `uv run scripts/powerpoint_pdf_qa.py p.pptx --out qa --pdf-only` (PowerPoint must have no open presentations) |
| Approximate render (LibreOffice) | `uv run scripts/render_slides.py p.pptx --slides 1 --out qa/approx` (2122 x 3000 px for A0; label results approximate) |

`poster_check.py` heuristics: the text-overflow estimate treats a CJK character
as 1 em and a Latin character as 0.5 em and ignores run-specific line wrap, so
it warns at ≥ 90% fill and fails at > 105%; confirm in the PowerPoint PDF.
Inherited font sizes are assumed 18 pt and labelled "assumed": set explicit
sizes in generated posters. Overlap reports only partial overlaps between
top-level blocks (text on a card is contained, so not reported). Pictures
inside groups are measured with the group's transform.

## 10. Hand-edit-first workflow (human edits in PowerPoint, then the agent edits)

The common case: the author builds or tweaks the poster by hand in PowerPoint,
later asks an agent for more changes. The human-saved .pptx is the **master**;
the agent never regenerates it from a build script (that would discard the
hand edits, and there may be no script at all).

1. **Gate**: `uv run scripts/safe_rebuild.py --deck MASTER.pptx --reference
   MASTER.pptx --poster [--backup-dir DIR]`. It refuses (exit 2) if PowerPoint
   has the deck open (process running + `~$` lock file), and writes a
   timestamped backup. Stop and ask the user to save and close if it refuses.
   Check the file mtime is newer than anything you last built.
2. **Ingest**: `uv run scripts/ingest_deck.py MASTER.pptx` and
   `scripts/dump_layout.py MASTER.pptx` (inches; an A0 page is 33 x 47 in, so
   expect values like 11.57 / 25.30). Learn the existing grid, fonts and
   palette from the file itself and reuse them. Note which shapes carry
   `scid:` names (tagged) and which do not.
3. **Edit a copy**: `cp MASTER.pptx work.pptx`; make surgical python-pptx
   edits on `work.pptx` (replace run text in place keeping the first run's
   formatting, move/resize by EMU, swap an image by writing the new blob to the
   same shape position/size, or re-add a picture with identical geometry).
   Do not delete-and-recreate shapes that were not asked to change, do not
   re-apply fonts globally, and do not change the page size. If a new
   picture is added, size it from the target dpi (section 4).
4. **Verify the residual**: `uv run scripts/capture_edits.py --poster
   --reference MASTER.pptx --edited work.pptx`. The only reported changes must
   be the intended ones; anything else is collateral damage to undo. `--poster`
   raises the defaults for a 47-in page (threshold 0.25 in instead of 0.03,
   proximity window 2.0 in instead of 0.30, title band 6 in); override with
   `--threshold` / `--pos-tol`. A no-op python-pptx open/save reports
   "No differences".
5. **Check**: `verify_deck.py --profile poster` and `poster_check.py` on
   `work.pptx`; run them on MASTER first so existing problems are not
   attributed to your edit. Do not fix pre-existing issues unasked; report them.
6. **Promote**: only after the user agrees, replace MASTER with `work.pptx`
   (the backup from step 1 stays). Never ask PowerPoint to open the master via
   automation while the user is working in it.

If a build script does exist and the user also hand-edited, use the tagged
round trip in [roundtrip.md](roundtrip.md) (the scaffold already emits
`scid:` names) or capture the edits with
[capturing-manual-edits.md](capturing-manual-edits.md) (`--poster`).
`clone_slide.py` is rarely needed for a one-slide poster.
