#!/usr/bin/env python3
"""Build PN_study_split.html and PN_core_A4_print.html from content/* and src/*.

Inputs (all read, none written):
  content/core.html       core sections (single source for study page, A4 and cheat)
  content/nav.json        left menu (topic, target section, label)
  content/questions.json  question bank; only the verified Korean study set is published
  content/products.json   domestic product comparison rows (<!--@@PRODUCTS@@-->)
  src/split-shell.html    study page layout, CSS and quiz JS
  src/a4-shell.html       A4 print layout
  src/study.css, src/study-state.js, src/study-ui.js  inlined at <!--@@STUDY_UI@@--> when present

Output is deterministic: no timestamps, no environment-dependent ordering, JSON
embedded with fixed separators. Structural validation (scripts/check_content.py)
runs first; the build aborts without writing if it fails.

Usage: python3 scripts/build.py [--check-only]
"""
import argparse
import html as htmllib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SRC = ROOT / "src"
OUT_SPLIT = "PN_study_split.html"
OUT_A4 = "PN_core_A4_print.html"

# Publish display fields and citation locations, leaving review notes and excerpts in the bank.
BANK_FIELDS = ["id", "revision", "topic", "source", "stem", "choices", "answer", "explain", "needle",
               "reviewStatus", "includeInBasicSet", "language", "coreSectionIds"]
STUDY_UI_FILES = [("study.css", "style"), ("study-state.js", "script"), ("study-ui.js", "script")]
SECTION_OPEN = re.compile(
    r'<section class="sec" data-topic="[^"]+" id="([^"]+)"(?: data-added="[^"]+")?( data-hub="1")?(?: hidden)?>'
)


def read(path):
    return path.read_text(encoding="utf-8")


def esc(s):
    return htmllib.escape(str(s), quote=True)


def script_json(obj):
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render_products(prod):
    """Render domestic PN product comparison for the learning view.

    Only confirmed products with held 허가 수치 appear. Unconfirmed / out-of-table
    entries stay in products.json for authors but must never emit work-queue copy
    (미확인, 허가자료 확인 후, 후보, 표 밖 후보, 확인 전) into HTML.

    Numeric columns stay on the data row; 허가일·출처·비고 go on a full-width
    note row so A4 print (and narrow study panes) stay readable.
    """
    table_products = [p for p in prod["products"] if p.get("inComparisonTable", True)]
    confirmed = [p for p in table_products if p.get("status") == "confirmed"]
    if not confirmed:
        return ""

    fields = prod["meta"]["compositionFields"]
    rows = []
    for p in confirmed:
        per = p.get("perLiter") or {}
        cells = [esc(per[f]) if per.get(f) is not None else "—" for f in fields[:5]]
        kcal = per.get("totalKcal")
        kcal_target = prod["meta"]["comparisonTargets"]["kcalPerDay"]
        vol = f"{round(kcal_target / kcal * 1000):,} mL" if kcal else "—"
        aa = per.get("aminoAcidG")
        aa_vol = f"{1000 / aa:.1f} mL" if aa else "—"
        aa_kcal = f"{kcal / aa:.1f} kcal" if aa and kcal else "—"
        src = p.get("source") or {}
        src_txt = esc(src.get("url") or src.get("heldFile") or "")
        note_bits = [f"허가 {esc(p['confirmedAsOf'])}"]
        if src_txt:
            note_bits.append(src_txt)
        src_note = src.get("note")
        if src_note:
            note_bits.append(esc(src_note))
        if p.get("note"):
            note_bits.append(esc(p["note"]))
        derived = f"2,000 kcal → {vol} · AA 1 g → {aa_vol} · {aa_kcal}/g"
        rows.append(
            "<tr>\n"
            f'<td class="l1">{esc(p["name"])}</td>\n'
            f"<td>{esc(p.get('kind', ''))}</td>\n"
            + "".join(f'<td class="num">{c}</td>\n' for c in cells)
            + "</tr>\n"
            '<tr class="compare-note">\n'
            f'<td colspan="7">{derived} · {" · ".join(note_bits)}</td>\n'
            "</tr>"
        )
    head = (
        '<table class="jg nest compare">'
        "<colgroup>"
        '<col class="c-name"><col class="c-kind">'
        '<col class="c-num"><col class="c-num"><col class="c-num"><col class="c-num"><col class="c-num">'
        "</colgroup>\n"
        "<tr>\n"
        '<th class="th">제품</th>\n<th class="th">형태</th>\n'
        '<th class="th">AA g/L</th>\n<th class="th">포도당 g/L</th>\n'
        '<th class="th">지질 g/L</th>\n<th class="th">kcal/L</th>\n<th class="th">mOsm/L</th>\n'
        "</tr>\n"
    )
    return head + "\n".join(rows) + "\n</table>"



def core_with_products(core, prod):
    return core.replace("<!--@@PRODUCTS@@-->", render_products(prod))


_CELL = re.compile(r"(<(td|th)([^>]*)>)(.*?)(</\2>)", re.S)
_TABLE = re.compile(
    r"(<table\b[^>]*\b(?:conc|compare)\b[^>]*>)(.*?)(</table>)",
    re.S | re.I,
)


def _plain_cell(inner: str) -> str:
    text = re.sub(r"<[^>]+>", "", inner)
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _column_mode(values):
    """Most common value; None if empty or every value is unique in a way we still mark all diffs."""
    if not values:
        return None
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    # Prefer the value that appears most often; ties → no single mode (mark all non-unanimous).
    best = max(counts.values())
    modes = [v for v, n in counts.items() if n == best]
    if len(modes) == 1 and best > 1:
        return modes[0]
    if len(counts) == 1:
        return values[0]
    return None  # no clear majority: mark every cell that is not unanimous (i.e. all)


def mark_compare_outliers(html: str) -> str:
    """On tables with class `conc` or `compare`, add `diff` to .num cells that lose the column majority.

    Example: adult/pediatric/NICU max-concentration table — NICU Mg 13 vs 24/24 gets colored.
    Reusable: any numeric comparison table can opt in with class `compare` (or existing `conc`).
    """

    def process(m):
        open_tag, body, close = m.group(1), m.group(2), m.group(3)
        row_matches = list(re.finditer(r"<tr>(.*?)</tr>", body, re.S))
        if len(row_matches) < 2:
            return m.group(0)
        parsed = []
        for rm in row_matches:
            cells = list(_CELL.finditer(rm.group(1)))
            parsed.append((rm, cells))
        data = [(rm, cells) for rm, cells in parsed if any(c.group(2) == "td" for c in cells)]
        if len(data) < 2:
            return m.group(0)
        ncols = max(len(cells) for _, cells in data)
        # Per column: collect (row_i, cell_match, plain) for td.num cells
        col_vals = [[] for _ in range(ncols)]
        for ri, (_, cells) in enumerate(data):
            for ci, c in enumerate(cells):
                attrs = c.group(3) or ""
                if c.group(2) != "td" or not re.search(r'\bclass="[^"]*\bnum\b', attrs):
                    continue
                col_vals[ci].append((ri, c, _plain_cell(c.group(4))))
        # Decide which cells are outliers
        outlier_ids = set()
        for ci, entries in enumerate(col_vals):
            if len(entries) < 2:
                continue
            plains = [p for _, _, p in entries]
            if len(set(plains)) <= 1:
                continue
            mode = _column_mode(plains)
            for ri, c, p in entries:
                if mode is None or p != mode:
                    outlier_ids.add(id(c))
        if not outlier_ids:
            return m.group(0)
        # Rebuild body with diff class on outlier cells
        parts = []
        last = 0
        for rm, cells in parsed:
            parts.append(body[last:rm.start()])
            row_html = rm.group(1)
            # rebuild row from cells
            row_parts = []
            rlast = 0
            # Need original positions within row
            for c in cells:
                # c is match within row group(1), so offsets are relative to row
                row_parts.append(row_html[rlast:c.start()])
                attrs = c.group(3) or ""
                inner = c.group(4)
                if id(c) in outlier_ids:
                    if re.search(r'\bclass="', attrs):
                        attrs = re.sub(r'\bclass="([^"]*)"', r'class="\1 diff"', attrs, count=1)
                    else:
                        attrs += ' class="num diff"'
                    # Prefer class color over bare <b> wrapping the whole value
                    if re.fullmatch(r"\s*<b>(.*?)</b>\s*", inner, re.S):
                        inner = re.fullmatch(r"\s*<b>(.*?)</b>\s*", inner, re.S).group(1)
                row_parts.append(f"<{c.group(2)}{attrs}>{inner}</{c.group(2)}>")
                rlast = c.end()
            row_parts.append(row_html[rlast:])
            parts.append("<tr>" + "".join(row_parts) + "</tr>")
            last = rm.end()
        parts.append(body[last:])
        return open_tag + "".join(parts) + close

    return _TABLE.sub(process, html)


def prepare_core(core, prod):
    return mark_compare_outliers(core_with_products(core, prod))


def render_nav(nav):
    return "".join(
        f'<button type="button" class="nav-item" data-topic="{esc(n["topic"])}" data-target="{esc(n["target"])}">'
        f'<span class="nav-lab">{esc(n["label"])}</span></button>' for n in nav)


def question_bank(qdoc):
    return [
        {
            **{k: q[k] for k in BANK_FIELDS},
            "evidence": [{k: e[k] for k in ("referenceId", "locator") if k in e} for e in q["evidence"]],
        }
        for q in qdoc["questions"]
        if q["includeInBasicSet"] and q["reviewStatus"] == "verified" and q["language"] == "ko"
    ]


def study_ui_block(content_version):
    parts = [f"<script>const PN_CONTENT_VERSION = {script_json(content_version)};</script>"]
    for name, tag in STUDY_UI_FILES:
        path = SRC / name
        if path.is_file():
            parts.append(f"<{tag}>\n{read(path).rstrip()}\n</{tag}>")
    hook = "<!-- STUDY_UI_HOOK: src/study.css · src/study-state.js · src/study-ui.js are inlined here when present (Task 4–5) -->"
    return "\n".join([hook] + parts)


def render_split(core, nav, qdoc, refs):
    shell = read(SRC / "split-shell.html")
    for token in ("<!--@@NAV@@-->", "<!--@@CORE@@-->\n", "/*@@QUESTION_BANK@@*/[]", "/*@@QUESTION_REFERENCES@@*/{}", "<!--@@STUDY_UI@@-->"):
        if shell.count(token) != 1:
            raise SystemExit(f"split-shell.html: placeholder {token!r} must appear once")
    out = shell.replace("<!--@@NAV@@-->", render_nav(nav))
    out = out.replace("<!--@@CORE@@-->\n", core.rstrip("\n") + " ")
    bank = question_bank(qdoc)
    used = {e["referenceId"] for q in bank for e in q["evidence"] if e.get("referenceId")}
    citations = {r["id"]: {"title": r["title"], "url": r.get("url")} for r in refs["references"] if r["id"] in used}
    out = out.replace("/*@@QUESTION_BANK@@*/[]", script_json(bank))
    out = out.replace("/*@@QUESTION_REFERENCES@@*/{}", script_json(citations))
    return out.replace("<!--@@STUDY_UI@@-->", study_ui_block(qdoc["meta"].get("contentVersion")))


def a4_heading(m):
    title = m.group(1)
    tag = "h3" if re.match(r"\s*\d+\.\d+", title) else "h2"
    return f"<{tag}>{title}</{tag}>"


def render_a4(core):
    shell = read(SRC / "a4-shell.html")
    if shell.count("<!--@@CORE@@-->") != 1:
        raise SystemExit("a4-shell.html: placeholder <!--@@CORE@@--> must appear once")

    def _sec_open(m):
        # Hub TOC stubs are study-nav only — drop from A4 entirely.
        if m.group(2):
            return f'<section class="print-sec hub" id="{m.group(1)}" hidden>'
        return f'<section class="print-sec" id="{m.group(1)}">'

    body = SECTION_OPEN.sub(_sec_open, core)
    body = re.sub(r'<div class="sec-h">(.*?)</div>', a4_heading, body)
    body = re.sub(
        r'<section class="print-sec hub"[^>]*>.*?</section>\n?',
        "",
        body,
        flags=re.S,
    )
    # Leftover hub chrome if any non-hub section still carries it.
    body = re.sub(r'<p class="hub-lead">.*?</p>\n<ul class="hub-list">.*?</ul>\n', "", body, flags=re.S)
    body = re.sub(r'<div class="cell hub">\n</div>\n', "", body)
    return shell.replace("<!--@@CORE@@-->", body.rstrip("\n"))


def render_all():
    core = read(CONTENT / "core.html")
    nav = json.loads(read(CONTENT / "nav.json"))
    qdoc = json.loads(read(CONTENT / "questions.json"))
    prod = json.loads(read(CONTENT / "products.json"))
    refs = json.loads(read(CONTENT / "references.json"))
    core = prepare_core(core, prod)
    return {OUT_SPLIT: render_split(core, nav, qdoc, refs), OUT_A4: render_a4(core)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check-only", action="store_true", help="validate and render, but do not write files")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_content
    errors, notes, _clinical = check_content.run(no_build=True)
    if errors:
        check_content.report(errors, notes, None)
        print("build aborted: structural validation failed")
        return 1
    rendered = render_all()
    for name, text in rendered.items():
        if args.check_only:
            print(f"rendered {name} ({len(text.encode('utf-8'))} bytes, not written)")
            continue
        (ROOT / name).write_bytes(text.encode("utf-8"))
        print(f"wrote {name} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
