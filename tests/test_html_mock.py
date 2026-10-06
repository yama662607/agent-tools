"""Content preservation, offline output, and regeneration guards for storyboards."""

import base64
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "slide-creator" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_mock import build_mock, validate_plan


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.words = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.words.append(data)


class MockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "plan.json"
        self.plan = {"title": "構成テスト", "slides": [
            {"id": "s1", "title": "根拠を選ぶ", "layout": "comparison",
             "bridge": "条件を確認する", "omit": ["導出は付録へ"],
             "blocks": [{"type": "text", "text": f"比較条件{i}"} for i in range(4)]}
        ]}

    def build(self):
        self.source.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
        before = self.source.read_bytes()
        report = build_mock(self.source, self.root / "mock")
        self.assertEqual(before, self.source.read_bytes())
        output = self.root / "mock"
        return report, Document((output / "index.html").read_text(encoding="utf-8")), output

    def test_all_content_and_notes_survive_without_fixed_item_count(self):
        report, doc, out = self.build()
        self.assertEqual(report["slide_ids"], ["s1"])
        words = "\n".join(doc.words)
        markdown = (out / "plan.md").read_text(encoding="utf-8")
        for value in ["比較条件0", "比較条件1", "比較条件2", "比較条件3", "条件を確認する", "導出は付録へ"]:
            self.assertIn(value, words)
            self.assertIn(value, markdown)

    def test_plain_text_does_not_become_html_or_template_code(self):
        literal = '<script>alert("x")</script> @@CSS@@'
        self.plan["slides"][0]["blocks"] = [{"type": "text", "text": literal}]
        _, doc, _ = self.build()
        self.assertIn(literal, "".join(doc.words))
        self.assertEqual(len([x for x in doc.tags if x[0] == "script"]), 2)

    def test_figure_is_embedded_and_source_is_preserved(self):
        image = self.root / "figure.svg"
        image.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
        self.plan["slides"][0]["blocks"] = [
            {"type": "figure", "src": image.name, "caption": "条件は一定", "source": "実験記録"}
        ]
        _, doc, _ = self.build()
        uri = next(attrs["src"] for tag, attrs in doc.tags if tag == "img")
        self.assertEqual(base64.b64decode(uri.split(",")[1]), image.read_bytes())
        self.assertIn("条件は一定", "".join(doc.words))
        self.assertIn("実験記録", "".join(doc.words))

    def test_regeneration_requires_explicit_overwrite(self):
        _, _, out = self.build()
        (out / "index.html").write_text("user review")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            build_mock(self.source, out)
        self.assertEqual((out / "index.html").read_text(), "user review")
        build_mock(self.source, out, overwrite=True)

    def test_bad_ids_layouts_sizes_and_tables_are_rejected(self):
        cases = []
        duplicate = copy.deepcopy(self.plan)
        duplicate["slides"].append(copy.deepcopy(duplicate["slides"][0]))
        cases.append(duplicate)
        bad_layout = copy.deepcopy(self.plan)
        bad_layout["slides"][0]["layout"] = "unknown"
        cases.append(bad_layout)
        small_text = copy.deepcopy(self.plan)
        small_text["theme"] = {"body_pt": 15}
        cases.append(small_text)
        table = copy.deepcopy(self.plan)
        table["slides"][0]["blocks"] = [{"type": "table", "headers": ["A", "B"], "rows": [["x"]]}]
        cases.append(table)
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_plan(case)

    def test_missing_image_does_not_replace_existing_output(self):
        _, _, out = self.build()
        original = (out / "index.html").read_bytes()
        self.plan["slides"][0]["blocks"] = [{"type": "figure", "src": "missing.png"}]
        self.source.write_text(json.dumps(self.plan), encoding="utf-8")
        with self.assertRaises(ValueError):
            build_mock(self.source, out, overwrite=True)
        self.assertEqual((out / "index.html").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
