"""Each structural rule in scripts/check_content.py must fail on a broken copy.

Run: python3 -m unittest tests/test_check_content.py
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_content  # noqa: E402


class CheckContentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "content", self.tmp / "content")
        shutil.copytree(ROOT / "src" / "legacy", self.tmp / "src" / "legacy")
        self._saved = (check_content.CONTENT, check_content.SRC)
        check_content.CONTENT, check_content.SRC = self.tmp / "content", self.tmp / "src"

    def tearDown(self):
        check_content.CONTENT, check_content.SRC = self._saved
        shutil.rmtree(self.tmp)

    def run_check(self):
        errors, _notes, _clinical = check_content.run(no_build=True, notes_root=self.tmp / "no-notes")
        return errors

    def edit_json(self, name, fn):
        path = self.tmp / "content" / name
        doc = json.loads(path.read_text(encoding="utf-8"))
        fn(doc)
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    def edit_core(self, old, new):
        path = self.tmp / "content" / "core.html"
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def verified(self, doc):
        return next(q for q in doc["questions"] if q["reviewStatus"] == "verified")

    def assertFails(self, fragment):
        errors = self.run_check()
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors[:5]}")

    def test_current_content_passes(self):
        self.assertEqual(self.run_check(), [])

    def test_duplicate_question_id(self):
        self.edit_json("questions.json", lambda d: d["questions"].append(dict(d["questions"][0])))
        self.assertFails("duplicate question id")

    def test_duplicate_nav_target(self):
        self.edit_json("nav.json", lambda d: d.append({**d[0], "label": "같은 본문"}))
        self.assertFails("nav.json: duplicate target")

    def test_answer_out_of_range(self):
        self.edit_json("questions.json", lambda d: self.verified(d).update(answer=9))
        self.assertFails("out of range")

    def test_unknown_reference(self):
        self.edit_json("questions.json", lambda d: self.verified(d)["referenceIds"].append("no-such-ref"))
        self.assertFails("not in references.json")

    def test_unknown_core_section(self):
        self.edit_json("questions.json", lambda d: self.verified(d)["coreSectionIds"].append("sec-nope"))
        self.assertFails("not in core.html")

    def test_unknown_scope(self):
        self.edit_json("questions.json", lambda d: self.verified(d)["scopeIds"].append("spec-nope"))
        self.assertFails("not in exam-scope.json")

    def test_verified_without_evidence(self):
        self.edit_json("questions.json", lambda d: self.verified(d).update(evidence=[]))
        self.assertFails("verified without evidence")

    def test_pending_in_basic_set(self):
        def fn(d):
            q = next(q for q in d["questions"] if q["reviewStatus"] == "pending")
            q["includeInBasicSet"] = True
        self.edit_json("questions.json", fn)
        self.assertFails("includeInBasicSet")

    def test_legacy_section_removed(self):
        self.edit_core('id="sec-eval-0-영양평가-PN-직결만"', 'id="sec-eval-0-renamed"')
        self.assertFails("legacy section id missing")

    def test_fluorescent_mark_removed(self):
        self.edit_core('<mark class="hl-pink" title="전문약사 EXAM">키(m)² × 22</mark>', "키(m)² × 22")
        self.assertFails("fluorescent mark lost")

    def test_outdated_errata_text(self):
        self.edit_core("범주2 실온 24 h·냉장 3일", "범주2 실온 24 h·냉일")
        self.assertFails("E4-bud")

    def test_cheat_disagrees_with_core(self):
        self.edit_core("(2000 − 500 − 400) ÷ 3.4 = 324 g → D50 647 mL", "(2000 − 500 − 400) ÷ 3.4 = 330 g → D50 660 mL")
        self.assertFails("missing in cheat[계산]")

    def test_product_without_confirmation(self):
        def fn(d):
            p = next(x for x in d["products"] if x.get("status") != "confirmed")
            p["perLiter"] = dict(p.get("perLiter") or {}, totalKcal=2000)
            p["confirmedAsOf"] = None
            p["status"] = "unconfirmed"
        self.edit_json("products.json", fn)
        self.assertFails("without confirmedAsOf")

    def test_products_table_cell_count_mismatch(self):
        import build
        # Inject a broken confirmed-product table (header wider than a data row).
        build.render_products = lambda prod: (
            '<table class="jg nest compare"><tr>'
            '<th class="th">A</th><th class="th">B</th><th class="th">C</th></tr>\n'
            '<tr><td class="l1">x</td><td class="num">1</td></tr>\n</table>'
        )
        try:
            self.assertFails("products table: row")
        finally:
            import importlib
            importlib.reload(build)

    def test_scope_topic_unknown(self):
        self.edit_json("exam-scope.json", lambda d: d["scopes"][0]["topicIds"].append("sec-ghost"))
        self.assertFails("topicId sec-ghost not in core.html")


if __name__ == "__main__":
    unittest.main()
