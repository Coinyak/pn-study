#!/usr/bin/env python3
"""Build PN_study_split.html and PN_core_A4_print.html from content/* and src/*.

Inputs (all read, none written):
  content/core.html       core sections (single source for study page, A4 and cheat)
  content/nav.json        left menu (topic, target section, label)
  content/questions.json  question bank; the default quiz pool is includeInBasicSet
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

# Fields the study page needs now (Task 4–5 grading/review UI reads the rest).
BANK_FIELDS = ["id", "revision", "topic", "source", "stem", "choices", "answer", "explain", "needle",
               "choiceExplanations", "reviewStatus", "includeInBasicSet", "originType",
               "coreSectionIds", "scopeIds", "referenceIds", "errataIds"]
STUDY_UI_FILES = [("study.css", "style"), ("study-state.js", "script"), ("study-ui.js", "script")]
SECTION_OPEN = re.compile(r'<section class="sec" data-topic="[^"]+" id="([^"]+)"(?: data-added="[^"]+")?>')


def read(path):
    return path.read_text(encoding="utf-8")


def esc(s):
    return htmllib.escape(str(s), quote=True)


def script_json(obj):
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render_products(prod):
    fields = prod["meta"]["compositionFields"]
    rows = []
    for p in prod["products"]:
        if not p.get("inBagTable", True):
            continue
        per = p.get("perLiter") or {}
        confirmed = p.get("status") == "confirmed"
        cells = [("—" if per.get(f) is None else esc(per[f])) for f in fields[:5]]
        kcal = per.get("totalKcal")
        vol = f"{round(2000 / kcal * 1000):,} mL" if confirmed and kcal else "—"
        src = p.get("source") or {}
        src_txt = esc(src.get("url") or src.get("heldFile") or "") if confirmed else "허가자료 미확인"
        rows.append(
            "<tr>\n"
            f'<td class="l1">{esc(p["name"])}</td>\n'
            f"<td>{esc(p.get('kind', ''))}</td>\n"
            f"<td>{esc(p['confirmedAsOf']) if confirmed else '미확인'}</td>\n"
            + "".join(f'<td class="num">{c}</td>\n' for c in cells)
            + f'<td class="num">{vol}</td>\n'
            f"<td>{src_txt} · {esc(p.get('note', ''))}</td>\n"
            "</tr>")
    head = ("<table class=\"jg nest\"><tr>\n<th class=\"th\">제품</th>\n<th class=\"th\">형태</th>\n"
            "<th class=\"th\">허가 확인일</th>\n<th class=\"th\">AA g/L</th>\n<th class=\"th\">포도당 g/L</th>\n"
            "<th class=\"th\">지질 g/L</th>\n<th class=\"th\">kcal/L</th>\n<th class=\"th\">mOsm/L</th>\n"
            "<th class=\"th\">2,000 kcal 공급 부피</th>\n<th class=\"th\">출처 · 비고</th>\n</tr>\n")
    others = [p for p in prod["products"] if not p.get("inBagTable", True)]
    tail = ""
    if others:
        tail = '\n<div class="cell">표 밖 후보(PN 백이 아닌 첨가제): ' + " · ".join(
            f"{esc(p['name'])} — {esc(p.get('note', ''))}" for p in others) + "</div>"
    return head + "\n".join(rows) + "\n</table>" + tail


def core_with_products(core, prod):
    return core.replace("<!--@@PRODUCTS@@-->", render_products(prod))


def render_nav(nav):
    return "".join(
        f'<button type="button" class="nav-item" data-topic="{esc(n["topic"])}" data-target="{esc(n["target"])}">'
        f'<span class="nav-lab">{esc(n["label"])}</span></button>' for n in nav)


def question_bank(qdoc):
    bank = []
    for q in qdoc["questions"]:
        if q.get("language") != "ko":
            continue  # Korean-only study set; English originals stay archived in questions.json
        bank.append({k: q.get(k, "" if k == "needle" else None) for k in BANK_FIELDS})
    return bank


def study_ui_block():
    parts = []
    for name, tag in STUDY_UI_FILES:
        path = SRC / name
        if path.is_file():
            parts.append(f"<{tag}>\n{read(path).rstrip()}\n</{tag}>")
    hook = "<!-- STUDY_UI_HOOK: src/study.css · src/study-state.js · src/study-ui.js are inlined here when present (Task 4–5) -->"
    return "\n".join([hook] + parts)


def render_split(core, nav, qdoc):
    shell = read(SRC / "split-shell.html")
    for token in ("<!--@@NAV@@-->", "<!--@@CORE@@-->\n", "/*@@QUESTION_BANK@@*/[]", "<!--@@STUDY_UI@@-->"):
        if shell.count(token) != 1:
            raise SystemExit(f"split-shell.html: placeholder {token!r} must appear once")
    out = shell.replace("<!--@@NAV@@-->", render_nav(nav))
    out = out.replace("<!--@@CORE@@-->\n", core.rstrip("\n") + " ")
    out = out.replace("/*@@QUESTION_BANK@@*/[]", script_json(question_bank(qdoc)))
    return out.replace("<!--@@STUDY_UI@@-->", study_ui_block())


def a4_heading(m):
    title = m.group(1)
    tag = "h3" if re.match(r"\s*\d+\.\d+", title) else "h2"
    return f"<{tag}>{title}</{tag}>"


def render_a4(core):
    shell = read(SRC / "a4-shell.html")
    if shell.count("<!--@@CORE@@-->") != 1:
        raise SystemExit("a4-shell.html: placeholder <!--@@CORE@@--> must appear once")
    body = SECTION_OPEN.sub(lambda m: f'<section class="print-sec allow-break" id="{m.group(1)}">', core)
    body = re.sub(r'<div class="sec-h">(.*?)</div>', a4_heading, body)
    # Hub menus only repeat the left nav; keep any other content of the hub cell.
    body = re.sub(r'<p class="hub-lead">.*?</p>\n<ul class="hub-list">.*?</ul>\n', "", body, flags=re.S)
    body = re.sub(r'<div class="cell hub">\n</div>\n', "", body)
    return shell.replace("<!--@@CORE@@-->", body.rstrip("\n"))


def render_all():
    core = read(CONTENT / "core.html")
    nav = json.loads(read(CONTENT / "nav.json"))
    qdoc = json.loads(read(CONTENT / "questions.json"))
    prod = json.loads(read(CONTENT / "products.json"))
    core = core_with_products(core, prod)
    return {OUT_SPLIT: render_split(core, nav, qdoc), OUT_A4: render_a4(core)}


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
