#!/usr/bin/env python3
"""Batch 9 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes.

No pending item keys the CCN sentences for gastric residual under 500 mL,
head of bed 30–45°, or chlorhexidine mouthwash twice daily. Those sentences
were added to the core table anyway. Hub, hang time, home start, peripheral
10–14 days, and the liver sentences still do not close a single choice.

Usage: python3 scripts/review_batch9.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "content" / "questions.json"
CORE = ROOT / "content" / "core.html"
REFS = ROOT / "content" / "references.json"
NOTES = ROOT.parent.parent.parent / "참고문헌_정리"
CONTENT_VERSION = "2026-11-14.11"

CCN = "ccn-summary-nestle-2022"
ESPEN_C = "espen-ped-pn-2018-14-complications"
HPN = "espen-hpn-2020"

ROUTE = "sec-route-3-1-말초-vs-중심"
COMP = "sec-complications-6-1-3열-요약"
HPN_SEC = "sec-hpn-10-재택-PN-HPN"

Q_NECK = "include head and neck swelling"
Q_PINCH = "compression of a CVC between the clavicle and first rib"
Q_PICC = "possible higher risk of catheter-related venous thrombosis"
Q_CRBSI = "quality of care (e.g. CRBSI rate, readmission rate etc.)"
Q_CLABSI = "all bloodstream infections in patients with a CVC are classified as CLABSI"
Q_GRV = "gastric residual volumes < 500mL in the absence of other signs of intolerance."
Q_HOB = "Elevating head of bed 30°– 45° is suggested."
Q_CHX = "Use of chlorhexidine mouthwash twice daily is suggested."
Q_HUB = "needles to access ports should be replaced at least once per week."

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치9 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "quizlet-iib-051",
        "answer": 1,
        "referenceIds": [ESPEN_C, HPN],
        "coreSectionIds": [ROUTE, COMP],
        "explain": "상대정맥이 막히면 머리와 목이 붓는다. 그 문장은 중심정맥 혈전 쪽에 있다. 재택 PN에서 PICC는 카테터 관련 정맥 혈전 위험이 더 높을 수 있다. 핀치오프는 쇄골과 첫 갈비뼈 사이의 압박이다.",
        "evidence": [
            ev(ESPEN_C, "ESPEN_compl_full.txt SVC occlusion", Q_NECK),
            ev(ESPEN_C, "ESPEN_compl_full.txt pinch-off", Q_PINCH),
            ev(HPN, "ESPEN_HPN_full.txt PICC thrombosis", Q_PICC),
        ],
        "choiceExplanations": [
            "오답. 핀치오프는 쇄골과 첫 갈비뼈 사이 압박이다. 머리·목 부종 문장은 그 압박이 아니다.",
            "정답. 상대정맥 폐색의 증상에 머리·목 부종이 있고, 그 문장은 중심정맥 혈전 쪽이다.",
            "오답. 섬유소 덮개가 팔·목 부종을 만든다는 문장은 없다.",
            "오답. 카테터 이동이 머리·목 부종을 만든다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 닫은 징후는 머리·목 부종이다. stem의 팔·어깨는 그 문장에 항목으로 없다. 소아 합병증 문장을 성인 재택 PICC에 옮겼다.",
    },
    {
        "id": "bcnsp-045",
        "answer": 1,
        "referenceIds": [HPN, ESPEN_C],
        "coreSectionIds": [HPN_SEC, COMP],
        "explain": "HPN 모니터링에서 돌봄의 질을 보는 예에 CRBSI 발생률이 들어 있다. 중심정맥관이 있는 환자의 혈류감염은 다른 원인이 확인되기 전에는 CLABSI로 분류한다. 환자 만족도, 약국 매출, 전체 재원일수는 그 예가 아니다.",
        "evidence": [
            ev(HPN, "ESPEN_HPN_full.txt R53", Q_CRBSI),
            ev(ESPEN_C, "ESPEN_compl_full.txt CLABSI definition", Q_CLABSI),
        ],
        "choiceExplanations": [
            "오답. 환자 만족도는 돌봄의 질 예에 없다.",
            "정답. 돌봄의 질 예로 CRBSI 발생률이 적혀 있고, 중심정맥관 혈류감염은 CLABSI로 분류한다.",
            "오답. 약국 매출은 그 예에 없다.",
            "오답. 전체 입원 재원일수는 그 예에 없다. 재입원률은 다른 예다.",
        ],
        "reviewNote": OK_NOTE + " 품질 예의 단어는 CRBSI다. CLABSI는 같은 장의 중심정맥관 혈류감염 분류 이름이다.",
    },
]


BLOCKERS = [
    (
        "quizlet-iib-011",
        "BLOCKER 배치9: ESPEN HPN R12는 상대정맥 접근의 첫 선택이 내경정맥 또는 쇄골하다. 정답은 쇄골하 하나다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-003",
        "BLOCKER 배치9: ESPEN HPN R55는 비타민·미량금속을 적어도 연 1회 본다. 6개월마다 미량영양소 평가는 그 문장으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-009",
        "BLOCKER 배치9: ESPEN HPN은 터널형·이식형 포트, 기간이 6개월 미만이면 PICC, 끝은 우심방-상대정맥 접합부다. 미드라인 금지를 그 이름으로 적은 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-094",
        "BLOCKER 배치9: 안정 후 주 2–3회는 투여 점검표의 체중이다. 전해질은 안정 후 주 1–2회다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-044",
        "BLOCKER 배치9: CCN의 클로르헥시딘은 가글 하루 2회다. 정답은 삽입 시 최대 차단이다. 피부 소독 클로르헥시딘은 보기에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-033",
        "BLOCKER 배치9: 비혈전 폐색으로 적힌 것은 지질·인산칼슘·꼬임·끝 위치·핀치오프다. 섬유소 덮개와 사용 중 이동은 그 문장에 이름이 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-046",
        "BLOCKER 배치9: 기계적 폐색은 꼬임·끝 위치·핀치오프를 본다. 처음부터 가이드와이어 교체가 부적절하다는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-116",
        "BLOCKER 배치9: CCN은 위잔류 500 mL 미만에서 EN을 끊지 말라고 한다. 정답은 목표 도달 시간 단축과 급식 중단 감소다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
        "compl": NOTES / "06_학습_노트/_gl_extract/ESPEN_compl_full.txt",
        "hpn": NOTES / "06_학습_노트/_gl_extract/ESPEN_HPN_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_NECK: "compl",
        Q_PINCH: "compl",
        Q_CLABSI: "compl",
        Q_PICC: "hpn",
        Q_CRBSI: "hpn",
        Q_HUB: "hpn",
        Q_GRV: "ccn",
        Q_HOB: "ccn",
        Q_CHX: "ccn",
    }
    missing = [f"{key}: {phrase}" for phrase, key in need.items() if _norm(phrase) not in blob[key]]
    if missing:
        raise SystemExit("quote not in held text:\n" + "\n".join(missing))


def apply_to_records(records):
    by = {q["id"]: q for q in records}
    missing = [p["id"] for p in PROMOTIONS if p["id"] not in by]
    if missing:
        raise SystemExit(f"promotion ids missing: {missing}")
    for p in PROMOTIONS:
        q = by[p["id"]]
        if q.get("answer") != p["answer"]:
            raise SystemExit(f"{p['id']}: refuse answer change {q.get('answer')} -> {p['answer']}")
        if q.get("duplicateOf"):
            raise SystemExit(f"{p['id']}: refuse promote duplicateOf")
        n = len(q.get("choices") or [])
        ce = p["choiceExplanations"]
        if len(ce) != n or not all(str(x).strip() for x in ce):
            raise SystemExit(f"{p['id']}: choiceExplanations must cover {n} choices")
        if not p.get("referenceIds") or not p.get("evidence"):
            raise SystemExit(f"{p['id']}: evidence required")
        if not all(e.get("locator") and e.get("quote") and e.get("referenceId") for e in p["evidence"]):
            raise SystemExit(f"{p['id']}: locator+quote required")
        q["referenceIds"] = list(p["referenceIds"])
        q["evidence"] = p["evidence"]
        q["choiceExplanations"] = ce
        q["coreSectionIds"] = list(p["coreSectionIds"])
        q["errataIds"] = list(p.get("errataIds") or [])
        q["reviewStatus"] = "verified"
        q["priority"] = "high"
        q["includeInBasicSet"] = q.get("language") == "ko"
        q["checks"] = dict(OK)
        if p.get("explain"):
            q["explain"] = p["explain"]
        note = p.get("reviewNote") or ""
        if note and note not in (q.get("reviewNote") or ""):
            prev = (q.get("reviewNote") or "").strip()
            q["reviewNote"] = (prev + " " + note).strip() if prev else note
    for qid, note in BLOCKERS:
        q = by.get(qid)
        if not q:
            raise SystemExit(f"blocker id missing: {qid}")
        if q.get("reviewStatus") == "verified":
            raise SystemExit(f"{qid}: blocker landed on a verified item")
        prev = q.get("reviewNote") or ""
        if note not in prev:
            q["reviewNote"] = (prev + " " + note).strip() if prev.strip() else note
    return records


def apply_to_document(doc):
    apply_to_records(doc["questions"])
    st = Counter(q["reviewStatus"] for q in doc["questions"])
    meta = doc["meta"]
    meta["contentVersion"] = CONTENT_VERSION
    meta["verifiedCount"] = st["verified"]
    meta["pendingCount"] = st["pending"]
    meta["excludedCount"] = st["excluded"]
    meta["finalCount"] = len(doc["questions"])
    return doc


def main():
    verify_quotes()
    doc = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    core_ids = set(re.findall(r'id="(sec-[^"]+)"', CORE.read_text(encoding="utf-8")))
    ref_ids = {r["id"] for r in json.loads(REFS.read_text(encoding="utf-8"))["references"]}
    apply_to_document(doc)
    promoted = {p["id"] for p in PROMOTIONS}
    for q in doc["questions"]:
        if q["id"] not in promoted:
            continue
        if q["reviewStatus"] != "verified" or not q["includeInBasicSet"]:
            raise SystemExit(f"{q['id']}: not in the basic set")
        for c in q["coreSectionIds"]:
            if c not in core_ids:
                raise SystemExit(f"{q['id']}: bad section {c}")
        for r in q["referenceIds"]:
            if r not in ref_ids:
                raise SystemExit(f"{q['id']}: bad ref {r}")
        for e in q["evidence"]:
            if e["referenceId"] not in ref_ids:
                raise SystemExit(f"{q['id']}: bad evidence ref")
    QUESTIONS.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    st = Counter(q["reviewStatus"] for q in doc["questions"])
    print(f"promoted={len(promoted)} verified={st['verified']} pending={st['pending']} excluded={st['excluded']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
