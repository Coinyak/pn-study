#!/usr/bin/env python3
"""Structural validation for content/* and the generated HTML.

Exit 0 only when every structural check passes. A structural pass says the
data is internally consistent (IDs, references, answer indexes, section links,
errata numbers shared by core / cheat / A4). It does NOT say anything is
clinically verified: the clinical review state is printed separately under
"CLINICAL REVIEW" and never changes the exit code.

Usage: python3 scripts/check_content.py [--no-build] [--notes-root PATH]
  --no-build   skip the "generated HTML is up to date" check (use before build)
"""
import argparse
import html as htmllib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SRC = ROOT / "src"
DEFAULT_NOTES_ROOT = ROOT.parent.parent.parent / "참고문헌_정리"

SECTION_OPEN = re.compile(r'<section class="sec" data-topic="([^"]+)" id="([^"]+)"( data-added="[^"]+")?>')
CHEAT_ROW = re.compile(r'<tr><th class="l1" scope="row">\[([^\]]+)\]\s*</th><td>(.*?)</td></tr>', re.S)
MARK = re.compile(r'<mark class="(hl-[a-z]+)" title="([^"]*)">(.*?)</mark>', re.S)
CHEAT_ID = "sec-cheat-11-치트-암기-블록"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Errata numbers that must read the same in the core section, the cheat row and
# both generated pages. Tokens are compared with all whitespace removed.
FACTS = [
    {"id": "E1-prealbumin", "section": "sec-eval-0-영양평가-PN-직결만", "cheat": "평가",
     "tokens": ["진단·효과단독X"], "forbidden": ["영양위험평가", "염증·위험지표"]},
    {"id": "E2-gir", "section": "sec-cho_gir-2-1-탄수화물-dextrose", "cheat": "GIR",
     "tokens": ["안정4–5", "ICU≤5", "고혈당위험≤4", "HPN주기순간5–7", "일일≤7g/kg"], "forbidden": ["소아max5–13"]},
    {"id": "E3-dextrose-factor", "section": "sec-calc_filter-4-2-계산-5단계-상한-체크", "cheat": "계산",
     "tokens": ["÷3.4", "324g", "D50647mL"], "forbidden": ["÷3.85=286g→D50572mL"]},
    {"id": "E4-bud", "section": "sec-stability-5-4-필터-hang-time-세트-BUD", "cheat": "투여",
     "tokens": ["상온30h/냉장9일", "범주1실온12h·냉장24h", "범주2실온24h·냉장3일"], "forbidden": ["냉h", "냉일"]},
    {"id": "E5-filter", "section": "sec-stability-5-4-필터-hang-time-세트-BUD", "cheat": "투여",
     "tokens": ["단일1.2"], "forbidden": []},
    {"id": "E5-filter-peds", "section": "sec-peds-9-소아-신생아", "cheat": None,
     "tokens": ["단일1.2", "구권고"], "forbidden": []},
    {"id": "E7-aki-protein", "section": "sec-disease-8-질환별-PN", "cheat": None,
     "tokens": ["84g", "91–105g"], "forbidden": []},
]
# Unsourced claim that must carry its hold note wherever it appears.
HOLD_PATTERNS = [(re.compile(r"≤10–14일(?!\(출처미확인)"), "E6: '≤10–14일' without '(출처 미확인…)' note")]


def squash(fragment):
    text = htmllib.unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", "", text)


def parse_core(text, errors):
    sections = []
    for m in SECTION_OPEN.finditer(text):
        end = text.find("</section>", m.end())
        nxt = text.find("<section", m.end())
        if end < 0 or (0 <= nxt < end):
            errors.append(f"core.html: section {m.group(2)} is not closed before the next section")
            continue
        sections.append({"topic": m.group(1), "id": m.group(2), "added": bool(m.group(3)),
                         "html": text[m.end():end]})
    opens, closes = text.count("<section"), text.count("</section>")
    if opens != closes or opens != len(sections):
        errors.append(f"core.html: {opens} <section> / {closes} </section> / {len(sections)} parsed")
    return sections


def load_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errors.append(f"{path.name}: cannot load ({e})")
        return None


def check_core(core_text, sections, nav, errors):
    ids = [s["id"] for s in sections]
    for sid, n in Counter(ids).items():
        if n > 1:
            errors.append(f"core.html: duplicate section id {sid}")
    base = json.loads((SRC / "legacy" / "core-baseline.json").read_text(encoding="utf-8"))
    for sid in base["sectionIds"]:
        if sid not in ids:
            errors.append(f"core.html: legacy section id missing: {sid}")
    have = Counter(MARK.findall(core_text))
    for m in base["marks"]:
        key = (m["class"], m["title"], m["html"])
        if have[key] < m["count"]:
            errors.append(f"core.html: fluorescent mark lost {key} ({have[key]}/{m['count']})")
    for s in sections:
        if s["added"] and s["id"] in base["sectionIds"]:
            errors.append(f"core.html: legacy section {s['id']} marked data-added")
    for n in nav:
        if n["target"] not in ids:
            errors.append(f"nav.json: target {n['target']} not in core.html")
    nav_targets = {n["target"] for n in nav}
    for s in sections:
        if s["added"] and s["id"] not in nav_targets:
            errors.append(f"nav.json: new section {s['id']} has no menu entry")
    if "<!--@@PRODUCTS@@-->" not in core_text:
        errors.append("core.html: <!--@@PRODUCTS@@--> placeholder missing (domestic product table)")


def check_questions(qdoc, ids_core, scope_ids, ref_ids, nav_topics, errors):
    meta, qs = qdoc["meta"], qdoc["questions"]
    ids = [q["id"] for q in qs]
    for qid, n in Counter(ids).items():
        if n > 1:
            errors.append(f"questions.json: duplicate question id {qid}")
    idset = set(ids)
    errata = set(meta.get("errata", {}))
    st = Counter(q["reviewStatus"] for q in qs)
    for key, status in (("verifiedCount", "verified"), ("pendingCount", "pending"), ("excludedCount", "excluded")):
        if meta.get(key) != st[status]:
            errors.append(f"questions.json: meta.{key}={meta.get(key)} but array has {st[status]}")
    if meta.get("finalCount") != len(qs):
        errors.append(f"questions.json: meta.finalCount={meta.get('finalCount')} but array has {len(qs)}")
    for q in qs:
        qid = q["id"]
        n = len(q.get("choices") or [])
        if n < 2:
            errors.append(f"{qid}: fewer than 2 choices")
        if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < n:
            errors.append(f"{qid}: answer index {q.get('answer')} out of range 0..{n - 1}")
        if len(q.get("choiceExplanations") or []) != n:
            errors.append(f"{qid}: choiceExplanations length != choices length")
        if q["reviewStatus"] not in ("verified", "pending", "excluded"):
            errors.append(f"{qid}: unknown reviewStatus {q['reviewStatus']}")
        if q.get("originType") not in ("officialSample", "reportedExam", "thirdParty", "originalPractice"):
            errors.append(f"{qid}: unknown originType {q.get('originType')}")
        if q["topic"] not in nav_topics:
            errors.append(f"{qid}: topic {q['topic']} has no menu entry")
        for r in q.get("referenceIds", []):
            if r not in ref_ids:
                errors.append(f"{qid}: referenceId {r} not in references.json")
        for ev in q.get("evidence", []):
            if ev.get("referenceId") not in ref_ids:
                errors.append(f"{qid}: evidence referenceId {ev.get('referenceId')} not in references.json")
        for c in q.get("coreSectionIds", []):
            if c not in ids_core:
                errors.append(f"{qid}: coreSectionId {c} not in core.html")
        for s in q.get("scopeIds", []):
            if s not in scope_ids:
                errors.append(f"{qid}: scopeId {s} not in exam-scope.json")
        for e in q.get("errataIds", []):
            if e not in errata:
                errors.append(f"{qid}: errataId {e} not in meta.errata")
        for rel in q.get("relatedIds", []) + ([q["duplicateOf"]] if q.get("duplicateOf") else []):
            if rel not in idset:
                errors.append(f"{qid}: related/duplicate id {rel} does not exist")
        if q.get("language") not in ("ko", "en"):
            errors.append(f"{qid}: language must be ko|en")
        if q.get("includeInBasicSet") != (q["reviewStatus"] == "verified" and q.get("language") == "ko"):
            errors.append(f"{qid}: includeInBasicSet must equal verified && language=='ko'")
        if q.get("language") == "en" and q["reviewStatus"] != "excluded":
            errors.append(f"{qid}: English stem must stay excluded (Korean-only study set)")
        if q["reviewStatus"] == "verified":
            if not q.get("referenceIds"):
                errors.append(f"{qid}: verified without referenceIds")
            if not q.get("evidence") or not all(ev.get("locator") and ev.get("quote") for ev in q["evidence"]):
                errors.append(f"{qid}: verified without evidence locator+quote")
            if not str(q.get("explain") or "").strip():
                errors.append(f"{qid}: verified without explain")
            if not all(str(x).strip() for x in q.get("choiceExplanations") or []):
                errors.append(f"{qid}: verified with an empty choice explanation")
            chk = q.get("checks", {})
            if chk.get("answerEvidence") != "ok" or chk.get("translation") == "en-untranslated":
                errors.append(f"{qid}: verified but checks={chk}")
            if q.get("duplicateOf"):
                errors.append(f"{qid}: verified item marked duplicateOf")
    return st


def check_scope(scope, ids_core, ref_ids, q_ids, errors):
    allowed = {"covered", "partial", "missing", "unreviewed"}
    sids = [s["id"] for s in scope["scopes"]]
    for sid, n in Counter(sids).items():
        if n > 1:
            errors.append(f"exam-scope.json: duplicate scope id {sid}")
    for s in scope["scopes"]:
        if s["coverage"] not in allowed:
            errors.append(f"{s['id']}: coverage {s['coverage']} not in {sorted(allowed)}")
        for t in s.get("topicIds", []):
            if t not in ids_core:
                errors.append(f"{s['id']}: topicId {t} not in core.html")
        for r in s.get("referenceIds", []):
            if r not in ref_ids:
                errors.append(f"{s['id']}: referenceId {r} not in references.json")
        for q in s.get("questionIds", []):
            if q not in q_ids:
                errors.append(f"{s['id']}: questionId {q} not in questions.json")
    return set(sids)


def check_refs(refs, scope_ids, notes_root, errors, notes):
    allowed = set(refs["meta"].get("accessStatusValues") or [])
    ids = [r["id"] for r in refs["references"]]
    for rid, n in Counter(ids).items():
        if n > 1:
            errors.append(f"references.json: duplicate id {rid}")
    root_ok = notes_root.is_dir()
    if not root_ok:
        notes.append(f"held-file check skipped: {notes_root} not found")
    for r in refs["references"]:
        if allowed and r.get("accessStatus") not in allowed:
            errors.append(f"{r['id']}: accessStatus {r.get('accessStatus')} not in meta.accessStatusValues")
        for s in r.get("scopeIds", []):
            if s not in scope_ids:
                errors.append(f"{r['id']}: scopeId {s} not in exam-scope.json")
        if r.get("reviewedAt") and not DATE.match(r["reviewedAt"]):
            errors.append(f"{r['id']}: reviewedAt {r['reviewedAt']} is not YYYY-MM-DD")
        held = r.get("heldFile")
        if root_ok and held and r.get("accessStatus") == "have-pdf":
            p = notes_root / held
            if not p.is_file():
                errors.append(f"{r['id']}: heldFile {held} not found")
            elif p.suffix.lower() == ".pdf" and p.read_bytes()[:5] != b"%PDF-":
                errors.append(f"{r['id']}: heldFile {held} is not a PDF (accessStatus have-pdf)")
    return set(ids)


def check_products(prod, ref_ids, errors):
    fields = prod["meta"]["compositionFields"]
    for p in prod["products"]:
        filled = [f for f in fields if p.get("perLiter", {}).get(f) is not None]
        if filled or p.get("status") == "confirmed":
            if p.get("status") != "confirmed":
                errors.append(f"products.json: {p['name']} has composition but status={p.get('status')}")
            if not DATE.match(str(p.get("confirmedAsOf") or "")):
                errors.append(f"products.json: {p['name']} has composition without confirmedAsOf")
            src = p.get("source") or {}
            if not (src.get("url") or src.get("heldFile")):
                errors.append(f"products.json: {p['name']} has composition without source url/heldFile")
            if src.get("referenceId") and src["referenceId"] not in ref_ids:
                errors.append(f"products.json: {p['name']} referenceId {src['referenceId']} unknown")


def check_products_table(prod, errors):
    """When a numeric comparison table is rendered, each row must match the header width.

    Unconfirmed-only catalogs intentionally render empty string (no learning-view work notes).
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build  # noqa: E402
    html = build.render_products(prod)
    for bad in ("미확인", "허가자료 확인 후", "표 밖 후보", "허가자료 확인 전", "후보:"):
        if bad in html:
            errors.append(f"products table: learning HTML must not contain work-note '{bad}'")
    if "</table>" not in html:
        # No confirmed products → empty render; do not require a grid.
        return
    table = html.split("</table>")[0]
    rows = re.findall(r"<tr>(.*?)</tr>", table, flags=re.S)
    if not rows:
        errors.append("products table: no rows rendered")
        return
    heads = len(re.findall(r"<th\b", rows[0]))
    for i, row in enumerate(rows[1:], 1):
        cells = len(re.findall(r"<td\b", row))
        if cells != heads:
            errors.append(f"products table: row {i} has {cells} cells but header has {heads} columns")


def check_facts(sections, label, text_by_section, cheat_rows, errors):
    for f in FACTS:
        body = text_by_section.get(f["section"])
        if body is None:
            errors.append(f"{label}: {f['id']} section {f['section']} missing")
            continue
        targets = [("section", body)]
        if f["cheat"]:
            row = cheat_rows.get(f["cheat"])
            if row is None:
                errors.append(f"{label}: {f['id']} cheat row [{f['cheat']}] missing")
                continue
            targets.append((f"cheat[{f['cheat']}]", row))
        for where, txt in targets:
            for tok in f["tokens"]:
                if tok not in txt:
                    errors.append(f"{label}: {f['id']} token '{tok}' missing in {where}")
    whole = "".join(text_by_section.values())
    for f in FACTS:
        for bad in f["forbidden"]:
            if bad in whole:
                errors.append(f"{label}: {f['id']} outdated text '{bad}' still present")
    for pat, why in HOLD_PATTERNS:
        if pat.search(whole):
            errors.append(f"{label}: {why}")


def sections_text(text, sec_regex):
    out = {}
    for m in sec_regex.finditer(text):
        end = text.find("</section>", m.end())
        out[m.group(1)] = squash(text[m.end():end])
    return out


def cheat_of(text, sec_regex):
    for m in sec_regex.finditer(text):
        if m.group(1) == CHEAT_ID:
            end = text.find("</section>", m.end())
            return {k: squash(v) for k, v in CHEAT_ROW.findall(text[m.end():end])}
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-build", action="store_true", help="skip the generated-HTML freshness check")
    ap.add_argument("--notes-root", type=Path, default=DEFAULT_NOTES_ROOT,
                    help="held 참고문헌_정리 folder (heldFile paths are relative to it)")
    args = ap.parse_args()
    return report(*run(args.no_build, args.notes_root))


def run(no_build=False, notes_root=DEFAULT_NOTES_ROOT):
    """Return (errors, notes, clinical_lines). Empty errors = structural pass."""
    errors, notes = [], []
    core_text = (CONTENT / "core.html").read_text(encoding="utf-8")
    sections = parse_core(core_text, errors)
    ids_core = {s["id"] for s in sections}
    nav = load_json(CONTENT / "nav.json", errors) or []
    qdoc = load_json(CONTENT / "questions.json", errors)
    scope = load_json(CONTENT / "exam-scope.json", errors)
    refs = load_json(CONTENT / "references.json", errors)
    prod = load_json(CONTENT / "products.json", errors)
    if None in (qdoc, scope, refs, prod):
        return errors, notes, None

    check_core(core_text, sections, nav, errors)
    ref_ids = {r["id"] for r in refs["references"]}
    q_ids = {q["id"] for q in qdoc["questions"]}
    scope_ids = check_scope(scope, ids_core, ref_ids, q_ids, errors)
    check_refs(refs, scope_ids, notes_root, errors, notes)
    st = check_questions(qdoc, ids_core, scope_ids, ref_ids, {n["topic"] for n in nav}, errors)
    check_products(prod, ref_ids, errors)
    check_products_table(prod, errors)

    core_secs = {s["id"]: squash(s["html"]) for s in sections}
    core_cheat = {}
    for s in sections:
        if s["id"] == CHEAT_ID:
            core_cheat = {k: squash(v) for k, v in CHEAT_ROW.findall(s["html"])}
    check_facts(sections, "core.html", core_secs, core_cheat, errors)

    if not no_build:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import build  # noqa: E402
        rendered = build.render_all()
        for name, text in rendered.items():
            path = ROOT / name
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                errors.append(f"{name}: out of date with content/* — run python3 scripts/build.py")
        split_re = re.compile(r'<section class="sec" data-topic="[^"]+" id="([^"]+)"[^>]*>')
        a4_re = re.compile(r'<section class="print-sec[^"]*" id="([^"]+)">')
        for name, rx in (("PN_study_split.html", split_re), ("PN_core_A4_print.html", a4_re)):
            text = rendered[name]
            secs = sections_text(text, rx)
            missing = ids_core - set(secs)
            if missing:
                errors.append(f"{name}: {len(missing)} core sections missing, e.g. {sorted(missing)[:3]}")
            check_facts(sections, name, secs, cheat_of(text, rx), errors)

    return errors, notes, clinical_report(qdoc, scope, refs, prod, sections, st)


def clinical_report(qdoc, scope, refs, prod, sections, st):
    qs = qdoc["questions"]
    lines = [f"questions: verified {st['verified']} · pending {st['pending']} · excluded {st['excluded']} "
             f"(default quiz pool = verified Korean only: {sum(1 for q in qs if q.get('includeInBasicSet'))})"]
    hi = [q["id"] for q in qs if q["reviewStatus"] == "pending" and q.get("errataIds")]
    lines.append(f"pending linked to errata: {len(hi)}")
    lines.append("verified by topic: " + ", ".join(
        f"{k} {v}" for k, v in sorted(Counter(q["topic"] for q in qs if q["reviewStatus"] == "verified").items())))
    cov = Counter(s["coverage"] for s in scope["scopes"])
    lines.append("scope coverage: " + ", ".join(f"{k} {cov[k]}" for k in ("covered", "partial", "missing", "unreviewed")))
    lines.append("missing scopes: " + ", ".join(s["id"] for s in scope["scopes"] if s["coverage"] == "missing"))
    des = [r for r in refs["references"] if r.get("designatedByNotice")]
    held = Counter(r.get("accessStatus") for r in des)
    lines.append("designated references by access: " + ", ".join(f"{k} {v}" for k, v in sorted(held.items())))
    pc = Counter(p.get("status") for p in prod["products"])
    lines.append(f"domestic products: {len(prod['products'])} listed · " + ", ".join(f"{k} {v}" for k, v in sorted(pc.items())))
    gaps = [s["id"] for s in sections if s["added"] and 'class="callout gap"' in s["html"]]
    lines.append(f"Task 3 sections with open-gap callouts: {len(gaps)}")
    return lines


def report(errors, notes, clinical):
    for n in notes:
        print(f"note: {n}")
    if clinical:
        print("CLINICAL REVIEW (reported only; a structural pass does not verify any of this):")
        for line in clinical:
            print(f"  - {line}")
    if errors:
        print(f"STRUCTURE: FAIL ({len(errors)} errors)")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print("STRUCTURE: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
