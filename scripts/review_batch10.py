#!/usr/bin/env python3
"""Held-PDF page sweep promotions.

Reads textbook OCR pages and short ASPEN PDFs already on disk, then promotes
pending Korean items whose keyed answer matches a sentence on those pages.
Does not change stems, choices, or answer indexes.

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
TEXTBOOK = Path("/Users/hoyeon/Downloads/임상영양길라잡이_OCR.pdf")
CONTENT_VERSION = "2026-11-14.12"

BOOK = "imsangyoungyang-gilajabi"
COMPOUND = "aspen-pn-checklist-03-compounding-2024"
PRESCRIBE = "aspen-pn-checklist-01-prescribing-2024"
ROLE = "aspen-role-of-pn-malnutrition-2025"

MIX = "sec-stability-5-1-혼합-순서"
PROTEIN = "sec-protein-2-3-단백질-아미노산-AA"
EVAL = "sec-eval-0-영양평가-PN-직결만"
TE = "sec-vit_te-2-7-미량원소-TE"
LIVER = "sec-complications-6-3-간담도-합병증-PNALD"

Q_ACD = "The volume of PN component to be mixed is less than the ACD can accurately deliver."
Q_CPOE = "detect real-time relevant compatibility and stability problems and dosing safety concerns."
Q_OMEG = (
    "Omegaven (fish oil triglycerides) injectable emulsion is FDA-approved as a source of calories "
    "and fatty acids for pediatric patients with parenteral nutrition-associated cholestasis (PNAC)."
)
Q_N4 = "+ 4g*]x 6.25"
Q_N4B = "소변을 통해 배출되는 비요소 질소 + 대변과 피부를 통한 질소"
Q_SGA = "SGA-C (severely malnourished)"
Q_ETI = "1) 급성 질환 및손상 관련 영양 불량, 2) 만성 질환 관련 영양 불량, 3) 기아 등"
Q_MN = "파킨슨과 같은 운동 장애 (떨림, 보행 어려움, 안면근육 경련)"
Q_ISO = "Class 5S 만족하는 장비와 공간에서 균 조제해야 하며"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치10 쪽 스윕 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "quizlet-pn-039",
        "answer": 2,
        "referenceIds": [COMPOUND],
        "coreSectionIds": [MIX],
        "explain": "섞을 PN 성분의 부피가 자동 조제기(ACD)가 정확히 전달할 수 있는 양보다 적으면 수동 조제가 맞다. ACD를 쓴다고 오류가 없어지는 것은 아니고, 한계 경고를 무시하라는 문장도 없다.",
        "evidence": [
            ev(COMPOUND, "Compounding Checklist 2024 p.2 Manual Compounding", Q_ACD),
        ],
        "choiceExplanations": [
            "오답. ACD 조제가 오류 없는 과정을 보장한다는 문장은 없다.",
            "오답. 한계 경고를 무시할 권한을 주라는 문장은 없다.",
            "정답. 전달량이 ACD의 정확 범위보다 작으면 수동 조제다.",
            "오답. 모든 환자군을 같은 시각에 조제하라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " stem은 2014 안전 합의를 가리키지만, 그 논문은 읽지 않았다. 같은 규칙은 보유한 2024 조제 점검표에 있다. 해설의 22%·37% 오류율은 그 점검표에 없어 뺐다.",
    },
    {
        "id": "bcnsp-089",
        "answer": 1,
        "referenceIds": [PRESCRIBE],
        "coreSectionIds": [MIX],
        "explain": "전산 처방 입력(CPOE)은 실시간으로 배합·안정성 문제와 용량 안전 경고를 잡도록 쓴다. 라벨 출력, 청구 연동, 경장 재고는 그 문장이 아니다.",
        "evidence": [
            ev(PRESCRIBE, "Prescribing Checklist 2024 p.2 CPOE", Q_CPOE),
        ],
        "choiceExplanations": [
            "오답. 영양 라벨 자동 출력은 그 문장에 없다.",
            "정답. CPOE에 배합·안정성 문제와 용량 안전 경고를 넣으라고 한다.",
            "오답. 청구 시스템 연동은 그 문장에 없다.",
            "오답. 경장 제품 재고는 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " '가장 중요한 요소'라는 순위 문장은 없다. 보기 중 점검표에 있는 기능은 용량·배합 경고다. 해설의 오류 30–60% 감소는 그 점검표에 없어 뺐다.",
    },
    {
        "id": "bcnsp-036",
        "answer": 1,
        "referenceIds": [ROLE],
        "coreSectionIds": [LIVER],
        "explain": "Omegaven은 어유 중성지방 주사제로, 소아의 정맥영양 관련 담즙정체(PNAC)에서 칼로리와 지방산 공급으로 FDA 승인되었다고 적혀 있다. Intralipid, SMOFlipid, Clinolipid는 그 문장에 없다.",
        "evidence": [
            ev(ROLE, "Role of PN in Malnutrition 2025 p.2 note", Q_OMEG),
        ],
        "choiceExplanations": [
            "오답. Intralipid는 그 FDA 승인 문장에 없다.",
            "정답. 문장이 이름으로 적은 FDA 승인 어유 유제는 Omegaven이다.",
            "오답. SMOFlipid는 그 문장에 없다.",
            "오답. Clinolipid는 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 닫은 것은 상품의 FDA 승인 적응이다. ESPEN의 순수 어유 단기 rescue와는 다른 질문이다. 빌리루빈이 줄어든다는 해설은 그 각주에 없어 뺐다.",
    },
    {
        "id": "bcnsp-053",
        "answer": 0,
        "referenceIds": [BOOK],
        "coreSectionIds": [PROTEIN],
        "explain": "질소평형이 0일 때의 단백량은 [소변요소질소 + 4 g] × 6.25다. 4 g은 소변의 비요소 질소와 대변·피부 손실이다. 그래서 질소 균형 = 단백 섭취(g) / 6.25 − (24시간 요요소질소 + 4 g)이다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF62", Q_N4),
            ev(BOOK, "임상영양길라잡이 OCR PDF62 4 g 주석", Q_N4B),
        ],
        "choiceExplanations": [
            "정답. 단백 섭취를 6.25로 나눈 값에서 (요요소질소 + 4 g)을 뺀다.",
            "오답. 빼는 방향이 반대다.",
            "오답. 총칼로리를 단백으로 나누는 식은 그 문장이 아니다.",
            "오답. 프리알부민에 체중을 곱하는 식은 그 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " OCR은 깨져 있으나 '+ 4g]x 6.25'와 비요소 질소·대변·피부 주석은 그 쪽에 있다.",
    },
    {
        "id": "rxk-1_3-4",
        "answer": 3,
        "referenceIds": [BOOK],
        "coreSectionIds": [PROTEIN],
        "explain": "교재의 평형 0 식은 [소변요소질소 + 4 g] × 6.25다. 보기 가운데 그 4 g을 요질소에 더해 섭취 질소에서 빼는 것이 가장 가깝다. BUN 변화를 더하는 식은 그 쪽에 없다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF62", Q_N4),
            ev(BOOK, "임상영양길라잡이 OCR PDF62 4 g 주석", Q_N4B),
        ],
        "choiceExplanations": [
            "오답. BUN 변화를 더하는 항은 그 식에 없다.",
            "오답. 요질소를 6.25로 나누고 단백 섭취를 빼는 방향이 아니다.",
            "오답. 여기도 BUN 변화 항이 들어가 있다.",
            "정답. 섭취 질소에서 (요질소 + 4)를 뺀다. 4 g은 교재 식에 있다.",
        ],
        "reviewNote": OK_NOTE + " 문항의 '요질소'는 교재의 소변요소질소보다 넓다. 4 g이 있는 보기만 그 식과 맞다.",
    },
    {
        "id": "cnsc-nutrition-support-101",
        "answer": 2,
        "referenceIds": [BOOK],
        "coreSectionIds": [EVAL],
        "explain": "SGA-C는 severely malnourished, 중증 영양불량이다. SGA-A는 정상, SGA-B는 경도에서 중등도다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF115 SGA", Q_SGA),
        ],
        "choiceExplanations": [
            "오답. 영양 상태 양호는 SGA-A다.",
            "오답. 경도–중등은 SGA-B다. '의심'은 그 등급 문장에 없다.",
            "정답. SGA-C는 중증 영양불량이다.",
            "오답. 과영양은 SGA 등급 문장에 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "cnsc-nutrition-support-017",
        "answer": 0,
        "referenceIds": [BOOK],
        "coreSectionIds": [EVAL],
        "explain": "교재는 영양불량을 급성 질환·손상, 만성 질환, 기아 등 사회 환경의 세 맥락으로 나눈다. 급성·만성·말기, 경도·중등·중증, 입원·외래·재가는 그 문장이 아니다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF115 병인", Q_ETI),
        ],
        "choiceExplanations": [
            "정답. 세 이름은 기아(사회 환경), 만성 질환, 급성 질환·손상이다.",
            "오답. 말기는 그 세 이름에 없다.",
            "오답. 경도·중등·중증은 중증도 등급이지 병인이 아니다.",
            "오답. 입원·외래·재가는 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 교재 순서는 급성, 만성, 기아 등 사회 환경이다. 보기는 같은 세 이름을 다른 순서로 적었다.",
    },
    {
        "id": "quizlet-pn-035",
        "answer": 0,
        "referenceIds": [BOOK],
        "coreSectionIds": [TE],
        "explain": "정맥영양 뒤에 신경절에 망간이 침착하면 파킨슨과 같은 운동장애가 온다. 그 표의 예는 떨림, 보행 어려움, 안면근육 경련이다. 구리·아연·셀레늄 독성 문장이 아니다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF99 망간 독성", Q_MN),
        ],
        "choiceExplanations": [
            "정답. 파킨슨과 같은 운동장애는 망간 침착 문장이다.",
            "오답. 그 증상 문장은 구리가 아니다.",
            "오답. 그 증상 문장은 아연이 아니다.",
            "오답. 그 증상 문장은 셀레늄이 아니다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-iib-006",
        "answer": 1,
        "referenceIds": [BOOK],
        "coreSectionIds": [TE],
        "explain": "장기 정맥영양 뒤의 떨림과 파킨슨 같은 운동장애는 망간 독성 쪽이다. 망간 결핍, 셀레늄 결핍, 셀레늄 독성이 그 문장은 아니다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF99 망간 독성", Q_MN),
        ],
        "choiceExplanations": [
            "오답. 문장은 침착과 운동장애라 결핍이 아니다.",
            "정답. 파킨슨과 같은 운동장애는 망간 독성 표에 있다.",
            "오답. 셀레늄 결핍의 그 증상 문장은 없다.",
            "오답. 셀레늄 독성의 그 증상 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 쪽에 있는 증상은 떨림·보행 어려움·안면근육 경련이다. stem의 경직이라는 단어는 그 문장에 없다.",
    },
    {
        "id": "cnsc-nutrition-support-112",
        "answer": 1,
        "referenceIds": [BOOK],
        "coreSectionIds": [MIX],
        "explain": "무균 조제, 그리고 정맥영양은 그 안의 중위험으로, ISO Class 5를 만족하는 장비와 공간에서 조제한다. 일반 조제·불출 구역, 개방 흄 후드, 투약실 카운터는 그 문장이 아니다.",
        "evidence": [
            ev(BOOK, "임상영양길라잡이 OCR PDF172", Q_ISO),
        ],
        "choiceExplanations": [
            "오답. 일반 약국 조제·불출 구역은 ISO Class 5 문장이 아니다.",
            "정답. 닫은 기준은 ISO Class 5 장비와 공간이다.",
            "오답. 개방 흄 후드는 그 문장이 아니다.",
            "오답. 깨끗한 카운터는 그 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " '완충구역'과 '아이솔레이터'라는 단어는 PDF172의 그 문장에 없다. 범주2 조절실온 4일은 같은 쪽의 24시간과 다르다.",
    },
]


BLOCKERS = [
    (
        "bcnsp-099",
        "BLOCKER 배치10: Omegaven의 소아 PNAC FDA 승인 각주는 이제 보유한다. 정답은 직접 빌리루빈 4.5에서 가장 근거가 확실한 변경이 상품명 전환이다. ESPEN의 강권고는 대두유 감량·중단 또는 어유 혼합유제이고, 순수 어유는 단기 rescue다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-047",
        "BLOCKER 배치10: PDF99에 파킨슨과 같은 운동장애가 망간 침착으로 있다. 미량원소 첨가에서 망간을 중단하라는 문장은 그 쪽에 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-019",
        "BLOCKER 배치10: Role of PN 2025는 미숙아 아미노산을 최소 3 g/kg/일, 3.5 g/kg/일을 넘기지 말라고 한다. 정답의 시작 1.5–2.0과 증량 3.5–4.0과 한 칸이 아니다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-044",
        "BLOCKER 배치10: 7일 대기는 잘 영양되고 안정된 성인이다. 중등·중증 영양불량은 가능한 빨리. stem의 중증 성인에 조건이 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-008",
        "BLOCKER 배치10: PDF172 범주2의 조절실온 사용가능시간은 24시간이다. 정답 4일과 다르다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-094",
        "BLOCKER 배치10: 처방 점검표의 전해질은 안정 전 매일 또는 3일, 이후 주 1–2회다. 정답의 주 2–3회는 그 칸이 아니다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-001",
        "BLOCKER 배치10: PDF115는 6가지와 세 병인을 적지만, '2가지'가 6특징 중 2개인지 병인 목록인지 OCR이 붙어서 단정하지 못한다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-032",
        "BLOCKER 배치10: 6특징 중 최소 2개의 깨끗한 문장을 PDF115에서 확정하지 못했다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-020",
        "BLOCKER 배치10: 세 병인 이름은 PDF115에 있다. 염증이 없으면 기아 쪽이라는 구분 문장은 그 쪽에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-010",
        "BLOCKER 배치10: 2024 처방 점검표는 모니터링 변수를 기록 항목에 넣는다. 검사실 모니터링이 필수에서 빠지는 구분은 2014 합의 본문이 있어야 한다. 그 논문은 읽지 않았다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-011",
        "BLOCKER 배치10: 전해질을 완전한 염으로 적는 문장은 처방 점검표에 있다. 라벨 필수에서 이온 표기가 빠지고 필터 1.2 또는 0.22가 필수라는 목록은 2014 합의 본문이다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-010",
        "BLOCKER 배치10: 모니터링 표에 Baseline 열이 있다. 시작 전과 시작 당일을 가르는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-4_1-1",
        "BLOCKER 배치10: 전환 점검표에 보호자 수행 능력과 급여·상환 확인이 있다. 환자 수용도를 같은 문장으로 적어 '모두 해당'이 되지는 않는다. 인덱스는 유지한다.",
    ),
    (
        "oep-bcscp-q-034",
        "BLOCKER 배치10: PDF172 표의 냉장 칸은 2–8°C다. 가정 PN을 냉장했다가 지시에 따라 실온화하라는 복약 문장은 아니다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-021",
        "BLOCKER 배치10: ESPEN 소아 정맥접근은 Groshong 같은 밸브 카테터가 끝 혈전을 막을 것으로 기대했으나 임상에서 확인되지 않았다고 한다. 압력 밸브가 폐색을 줄인다는 정답과 어긋난다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-103",
        "BLOCKER 배치10: 잘영양·안정은 7일, 영양위험은 3–5일이다. 정답 5–7일은 그 두 칸을 한 간격으로 묶는다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return re.sub(r"\s+", "", text)


def _pdf_text(path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def verify_quotes():
    if not NOTES.is_dir() or not TEXTBOOK.is_file():
        print(f"quote check skipped: notes or textbook missing ({NOTES}, {TEXTBOOK})")
        return
    aspen = NOTES / "02_ASPEN_공개자료"
    blobs = {
        "compound": _norm(_pdf_text(aspen / "ASPEN_PN_Checklist_03_Compounding_2024.pdf")),
        "prescribe": _norm(_pdf_text(aspen / "ASPEN_PN_Checklist_01_Prescribing_2024.pdf")),
        "role": _norm(_pdf_text(aspen / "ASPEN_Role_of_PN_in_Malnutrition_2025.pdf")),
        "book": _norm(_pdf_text(TEXTBOOK)),
    }
    need = {
        Q_ACD: "compound",
        Q_CPOE: "prescribe",
        Q_OMEG: "role",
        Q_N4: "book",
        Q_N4B: "book",
        Q_SGA: "book",
        Q_ETI: "book",
        Q_MN: "book",
        Q_ISO: "book",
    }
    missing = [phrase for phrase, key in need.items() if _norm(phrase) not in blobs[key]]
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
