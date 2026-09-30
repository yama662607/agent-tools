// pptxgenjs emits a:latin/a:ea/a:cs from fontFace (verified with 4.0.1).
export function japaneseTextOptions(options = {}) {
  const result = {
    fontFace: "Hiragino Kaku Gothic ProN",
    lang: "ja-JP",
    ...options,
  };
  if (typeof result.fontFace !== "string" || !result.fontFace.trim()) {
    throw new Error("Japanese text requires a non-empty fontFace");
  }
  return result;
}

// 12 CSS px at 96 px/in. This is a small reserve, not a text-fit guarantee.
const TITLE_SLACK_IN = 12 / 96;

export function singleLineTitleOptions(options, slideWidth) {
  const { x, w, align = "left" } = options;
  if (![x, w, slideWidth].every(Number.isFinite) || w <= 0 || slideWidth <= 0) {
    throw new Error("Title x, w and slideWidth must be numeric inches");
  }
  if (!["left", "center", "right"].includes(align)) {
    throw new Error("Single-line title align must be left, center or right");
  }
  const shift = align === "center" ? TITLE_SLACK_IN / 2
    : align === "right" ? TITLE_SLACK_IN : 0;
  const adjustedX = x - shift;
  const adjustedW = w + TITLE_SLACK_IN;
  if (adjustedX < 0 || adjustedX + adjustedW > slideWidth + 1e-9) {
    throw new Error("Reserve 0.125in title slack inside the slide bounds");
  }
  return {
    margin: 0,
    bold: true,
    ...japaneseTextOptions(options),
    x: adjustedX,
    w: adjustedW,
    align,
    wrap: false,
    fit: "none",
    shrinkText: false,
    autoFit: false,
  };
}
