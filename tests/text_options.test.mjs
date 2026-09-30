import assert from "node:assert/strict";
import test from "node:test";
import {
  japaneseTextOptions,
  singleLineTitleOptions,
} from "../skills/slide-creator/scripts/text_options.mjs";

test("Japanese text has an explicit font and language without mutating inputs", () => {
  const input = { fontSize: 22, fontFace: "Yu Gothic", color: "112233" };
  const options = japaneseTextOptions(input);
  assert.deepEqual(options, { ...input, lang: "ja-JP" });
  assert.notEqual(options, input);
  assert.equal(input.lang, undefined);
  assert.equal(japaneseTextOptions().fontFace, "Hiragino Kaku Gothic ProN");
  assert.throws(() => japaneseTextOptions({ fontFace: " " }), /fontFace/);
});

for (const [align, shift] of [["left", 0], ["center", 0.0625], ["right", 0.125]]) {
  test(`single-line ${align} title keeps its alignment anchor`, () => {
    const input = { x: 1, y: 0.3, w: 8, h: 0.7, align, fontSize: 26 };
    const result = singleLineTitleOptions(input, 10);
    assert.equal(result.x, input.x - shift);
    assert.equal(result.w, input.w + 0.125);
    assert.equal(result.y, input.y);
    assert.equal(result.h, input.h);
    assert.equal(result.wrap, false);
    assert.equal(result.fit, "none");
    assert.equal(result.margin, 0);
    assert.equal(input.w, 8);
    assert.equal(result.fontFace, "Hiragino Kaku Gothic ProN");
  });
}

test("title slack never silently pushes a box off the slide", () => {
  assert.throws(() => singleLineTitleOptions({ x: 1, w: 9 }, 10), /slide/);
  assert.throws(() => singleLineTitleOptions({ x: 0, w: 8, align: "center" }, 10), /slide/);
  assert.throws(() => singleLineTitleOptions({ x: "10%", w: 8 }, 10), /inches/);
  assert.throws(() => singleLineTitleOptions({ x: 1, w: 8, align: "justify" }, 10), /align/);
});
