// STARTING POINT, not a template to keep: emits an empty A0 poster page with a
// column grid and named placeholder blocks. Every block has objectName
// "scid:p001.<id>" so tagged round-trip (sync_from_pptx.py) can address it.
// Replace the placeholder text and the BLOCKS table with the real content plan.
//
//   cd poster-build && bun add pptxgenjs && cp <skill>/scripts/poster_scaffold.mjs .
//   bun poster_scaffold.mjs [--landscape] [--cols 3] [--out poster.pptx]
//
// Units are inches at print size (A0 = 33.11 x 46.81; PowerPoint's limit is
// 56 in, so full size fits). Sizes in pt are final print sizes.
import pptxgen from "pptxgenjs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const landscape = process.argv.includes("--landscape");
const COLS = Number(arg("--cols", 3));
const OUT = arg("--out", "poster.pptx");

const W = landscape ? 46.81 : 33.11, H = landscape ? 33.11 : 46.81;
const MARGIN = 1.0, GUTTER = 0.6;               // ~25 mm / ~15 mm
const colW = (W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS;
const colX = (c) => MARGIN + c * (colW + GUTTER);   // c = 0-based column
const span = (n) => n * colW + (n - 1) * GUTTER;

const JP = "Hiragino Kaku Gothic ProN";
const INK = "1A1A1A", MUTED = "666666", ACCENT = "1B2A4A";

// id, x, y, w, h (inches), role -> font size (pt), placeholder text
const HEADER_H = landscape ? 5.0 : 6.5;
const top = MARGIN + HEADER_H + 1.8;               // below title + takeaway
const bodyH = H - top - MARGIN - 3.0;              // leave a footer row
const rows = (n) => (bodyH - (n - 1) * GUTTER) / n;
const BLOCKS = [
  { id: "title",     x: MARGIN, y: MARGIN,       w: W - 2 * MARGIN, h: 3.2, pt: 96, bold: true, text: "[タイトル: 結論を主張する一文]" },
  { id: "authors",   x: MARGIN, y: MARGIN + 3.3, w: W - 2 * MARGIN, h: 1.6, pt: 44, text: "[著者] ・ [所属]" },
  { id: "takeaway",  x: MARGIN, y: MARGIN + HEADER_H, w: W - 2 * MARGIN, h: 1.5, pt: 56, bold: true, color: ACCENT, text: "[一文の主張 (takeaway)]" },
];
// evidence blocks fill the columns top to bottom; edit counts per column
const PLAN = [["intro", "method"], ["result1", "result2"], ["result3", "conclusion"]].slice(0, COLS);
PLAN.forEach((ids, c) => ids.forEach((id, r) => {
  const h = rows(ids.length);
  BLOCKS.push({ id, x: colX(c), y: top + r * (h + GUTTER), w: colW, h, pt: 32, head: `[${id} の見出し(主張文)]`, text: "[本文・図]" });
}));
BLOCKS.push(
  { id: "refs", x: MARGIN, y: H - MARGIN - 2.6, w: span(Math.max(COLS - 1, 1)), h: 2.6, pt: 20, color: MUTED, text: "[参考文献・謝辞]" },
  { id: "qr",   x: W - MARGIN - 2.6, y: H - MARGIN - 2.6, w: 2.6, h: 2.6, pt: 20, color: MUTED, text: "[QR]" },
);

const pres = new pptxgen();
pres.defineLayout({ name: "A0", width: W, height: H });
pres.layout = "A0";
const slide = pres.addSlide();
for (const b of BLOCKS) {
  const name = `scid:p001.${b.id}`;
  if (b.head) {
    slide.addText(b.head, { objectName: `${name}.head`, x: b.x, y: b.y, w: b.w, h: 1.1, fontSize: 48, bold: true,
      fontFace: JP, color: ACCENT, margin: 0, valign: "top" });
    slide.addText(b.text, { objectName: name, x: b.x, y: b.y + 1.3, w: b.w, h: b.h - 1.3, fontSize: b.pt,
      fontFace: JP, color: INK, margin: 0, valign: "top" });
  } else {
    slide.addText(b.text, { objectName: name, x: b.x, y: b.y, w: b.w, h: b.h, fontSize: b.pt, bold: !!b.bold,
      fontFace: JP, color: b.color ?? INK, margin: 0, valign: "top" });
  }
}
await pres.writeFile({ fileName: OUT });
console.log(`wrote ${OUT} (${W} x ${H} in, ${COLS} columns, ${BLOCKS.length} blocks)`);
