#!/usr/bin/env python3
"""ESPEN pediatric recommendation sweep.

Reads the recommendation sentences in the held pediatric PN chapters on
venous access, vitamins, and fluid and electrolytes. Promotes a pending
Korean item only when the keyed choice is that sentence. Does not change
stems, choices, or answer indexes.

Historical batch; replayed by export_questions.py in a comparison file.
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
GL = NOTES / "01_ESPEN_가이드라인"
CONTENT_VERSION = "2026-11-14.13"

VIT = "espen-ped-pn-2018-09-vitamins"
FLUID = "espen-ped-pn-2018-06-fluid-electrolytes"

VITAMIN = "sec-vit_te-2-6-비타민"
LYTE = "sec-fluid_lytes-2-5-전해질"

Q_FAT = (
    "Generally, daily parenteral doses of the fat-soluble vitamins are similar to "
    "oral recommended daily allowances (higher bioavailability, but also higher requirements)."
)
Q_WAT = (
    "Generally, daily parenteral doses of the water-soluble vitamins are several times higher "
    "than the oral recommended daily allowances (due to higher requirements and increased urinary excretion)."
)
Q_B1 = "Deficiency of thiamine may lead to beriberi with neurologic and cardiovascular symptoms."
Q_B1B = (
    "In parenterally fed infants and children a deficient thiamine supply may lead to severe "
    "lactic acidosis, Wernicke's encephalopathy and even death within a period of days to weeks"
)
Q_CL = (
    "replacing sodium losses only with sodium chloride solutions exposes to high cumulative "
    "Cl intake and risk of metabolic acidosis associated hyperchloraemia"
)
Q_AC = (
    "part of sodium intake, in the form of sodium chloride solutions, should be replaced by, "
    "for instance, sodium lactate or sodium acetate"
)

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치11 ESPEN 소아 권고 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "quizlet-pn-036",
        "answer": 1,
        "referenceIds": [VIT],
        "coreSectionIds": [VITAMIN],
        "explain": "비경구 지용성 비타민의 하루 용량은 경구 권장량과 비슷하다. 생체이용률은 더 높지만 요구량도 더 높다. 더 낮다, 2배, 4배는 그 문장이 아니다.",
        "evidence": [
            ev(VIT, "ESPEN 소아 PN 비타민, 지용성 용량", Q_FAT),
        ],
        "choiceExplanations": [
            "오답. 경구 권장량보다 낮다는 문장은 없다.",
            "정답. 비경구 지용성 하루 용량은 경구 권장량과 비슷하다.",
            "오답. 2배라는 배수는 지용성 문장에 없다.",
            "오답. 4배라는 배수는 지용성 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 원문은 similar to oral recommended daily allowances다. 보기 가운데 그 비교는 '같다'다.",
    },
    {
        "id": "quizlet-pn-037",
        "answer": 3,
        "referenceIds": [VIT],
        "coreSectionIds": [VITAMIN],
        "explain": "비경구 수용성 비타민의 하루 용량은 경구 권장량보다 여러 배 높다. 요구량이 더 크고 소변으로 더 많이 빠지기 때문이다. 1/3, 1/2, 같다는 그 문장이 아니다.",
        "evidence": [
            ev(VIT, "ESPEN 소아 PN 비타민, 수용성 용량", Q_WAT),
        ],
        "choiceExplanations": [
            "오답. 1/3은 그 문장이 아니다.",
            "오답. 1/2는 그 문장이 아니다.",
            "오답. 경구 권장량과 같다는 말은 지용성 문장이다.",
            "정답. 수용성 비경구 하루 용량은 경구 권장량보다 여러 배 높다.",
        ],
        "reviewNote": OK_NOTE + " 원문은 several times higher다. 해설에 있던 2–2.5배는 그 문장에 없어 뺐다.",
    },
    {
        "id": "bcnsp-039",
        "answer": 1,
        "referenceIds": [VIT],
        "coreSectionIds": [VITAMIN],
        "explain": "티아민이 부족하면 각기병으로 신경 증상과 심혈관 증상이 온다. 정맥영양을 받는 영아와 소아에서 공급이 부족하면 심한 젖산산증과 베르니케 뇌병증이 생기고, 수일에서 수주 안에 사망할 수 있다. 비타민 A·C·E의 그 문장은 아니다.",
        "evidence": [
            ev(VIT, "ESPEN 소아 PN 비타민, 티아민 결핍", Q_B1),
            ev(VIT, "ESPEN 소아 PN 비타민, 티아민과 젖산산증", Q_B1B),
        ],
        "choiceExplanations": [
            "오답. 젖산산증과 심혈관 증상을 적은 결핍 문장은 비타민 A가 아니다.",
            "정답. 각기병의 심혈관 증상과, 정맥영양에서 부족한 티아민의 젖산산증이 그 문장이다.",
            "오답. 그 문장은 비타민 C가 아니다.",
            "오답. 그 문장은 비타민 E가 아니다.",
        ],
        "reviewNote": OK_NOTE + " 심혈관 증상은 각기병 문장이고, 젖산산증은 정맥영양 결핍 문장이다. stem의 '장기'와 '심기능 장애'라는 단어는 없다. 피루브산 탈수소효소와 전국 품절은 이 쪽에 없어 뺐다.",
    },
    {
        "id": "medex-010",
        "answer": 0,
        "referenceIds": [FLUID],
        "coreSectionIds": [LYTE],
        "explain": "나트륨 손실을 염화나트륨으로만 보충하면 염소가 쌓여 고염소성 대사성 산증이 된다. 나트륨의 일부를 아세트산나트륨이나 젖산나트륨으로 바꾼다. 전해질을 모두 빼거나, 염소를 더 늘리거나, 포도당을 먼저 올리는 것은 그 문장이 아니다.",
        "evidence": [
            ev(FLUID, "ESPEN 소아 PN 수액·전해질, 염소와 산증", Q_CL),
            ev(FLUID, "ESPEN 소아 PN 수액·전해질, 아세트산염 교체", Q_AC),
        ],
        "choiceExplanations": [
            "정답. 염화나트륨으로 준 나트륨의 일부를 아세트산염으로 바꾼다.",
            "오답. 나트륨과 칼륨을 모두 빼라는 문장은 없다.",
            "오답. 염소를 더 늘리면 그 산증 쪽이다.",
            "오답. 포도당을 먼저 올려 중탄산염을 채운다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 문장은 미숙아와, 수분·전해질 손실이 큰 연장 소아에 있다. stem은 성인 용량의 회장루다. 닫은 것은 염화나트륨의 일부를 아세트산염으로 바꾸는 조치다. 아세트산이 중탄산염이 된다는 말은 이 문장에 없어 뺐다.",
    },
]


BLOCKERS = [
    (
        "bcnsp-082",
        "BLOCKER 배치11: ESPEN 소아 수액은 고나트륨혈증을 10–15 mmol/L/24 h로 내리라고 한다. 빠르게 내리면 뇌부종이 올 수 있다고 한다. 정답의 상한 10–12, PN 나트륨 감량, 자유수 추가는 그 문장으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_3-7",
        "BLOCKER 배치11: ESPEN 소아 수액은 수분 요구가 에너지와 나란히 1 mL/kcal라고 한다. 정답의 1–2 mL/kcal는 그 문장이 아니다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-044",
        "BLOCKER 배치11: ESPEN 소아 정맥접근은 차단 예방조치의 정도를 권고할 근거가 없다고 한다. 피부 소독 권고는 2% 클로르헥시딘·70% 이소프로필 알코올이고 보기에 없다. 예방적 항생제와 삽입 부위 국소 항균제의 일상 사용은 하지 말라고 한다. 정답이 최대 차단을 가장 효과적이라고 한 것과 어긋난다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-020",
        "BLOCKER 배치11: 염화나트륨의 일부를 아세트산염으로 바꾸는 문장은 고염소성 산증과 수분·전해질 손실이 큰 소아에 있다. stem은 급성 신부전이고 염소 부하가 적혀 있지 않다. 인덱스는 유지한다.",
    ),
    (
        "kshp-46",
        "BLOCKER 배치11: 수용성 비타민 과잉은 신장으로 빠져 독성이 적다고 한다. 비타민 A의 만성 독성에는 운동실조가 있다. C가 K보다 독성이 낮다는 순위는 없다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"-\s+", "", text)
    return re.sub(r"\s+", "", text)


def _pdf_text(path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def verify_quotes():
    vit = GL / "ESPEN_pediatric_PN_09_vitamins.pdf"
    fluid = GL / "ESPEN_pediatric_PN_06_fluid_electrolytes.pdf"
    if not vit.is_file() or not fluid.is_file():
        print(f"quote check skipped: pediatric PDFs missing ({vit}, {fluid})")
        return
    blobs = {
        VIT: _norm(_pdf_text(vit)),
        FLUID: _norm(_pdf_text(fluid)),
    }
    missing = []
    for p in PROMOTIONS:
        for e in p["evidence"]:
            if _norm(e["quote"]) not in blobs[e["referenceId"]]:
                missing.append(e["quote"])
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
        if q.get("language") != "ko":
            raise SystemExit(f"{p['id']}: refuse non-Korean promotion")
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
        q["includeInBasicSet"] = True
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
    sys.exit("Historical review batch; use export_questions.py --output NEW_FILE for a comparison.")
