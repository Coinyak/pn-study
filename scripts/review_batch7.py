#!/usr/bin/env python3
"""Batch 7 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes.

No pending item keys vitamin-immediately-before-use within 24 h, selenite kept
1–4 h from vitamin C, or 50% dextrose for hypoglycemia. Refeeding high-risk
lists do not close a single leftover choice. quizlet-iib-023 stays pending
because the keyed choice is systemic antibiotics.

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
CONTENT_VERSION = "2026-11-14.9"

GILA = "imsangyoungyang-gilajabi"
CCN = "ccn-summary-nestle-2022"
FACT = "aspen-adult-critically-ill-factsheet-2024"
MYTHS = "aspen-pn-myths-practice-tool-2024"
ADMIN = "aspen-pn-checklist-04-administration-2024"

EVAL = "sec-eval-0-영양평가-PN-직결만"
IND = "sec-indications-1-적응증-시작시점-지연"
CHO = "sec-cho_gir-2-1-탄수화물-dextrose"
PROT = "sec-protein-2-3-단백질-아미노산-AA"
FLUID = "sec-fluid_lytes-2-4-수분"
LYTE = "sec-fluid_lytes-2-5-전해질"
TE = "sec-vit_te-2-7-미량원소-TE"
ROUTE = "sec-route-3-1-말초-vs-중심"
ENERGY = "sec-calc_filter-4-1-에너지"
MIX = "sec-stability-5-1-혼합-순서"
COMP = "sec-complications-6-1-3열-요약"
LAB = "sec-monitor-7-2-Lab-정상범위"
LUNG = "sec-disease-8-1-폐-심장-신경계"
OBESE = "sec-disease-8-2-당뇨-비만"
DIS = "sec-disease-8-질환별-PN"

Q_IBW = "Protein is suggested at ≥ 2.0 gm/kg IBW**/day for BMI 30–40, and up to 2.5 gm/kg IBW**/day for BMI ≥ 40"
Q_TBW = "고령♀ 0.45 × 체중"
Q_BG = "BG 140–180"
Q_REDUCE = "When EN or PN is associated with problems in glycemic control, respiratory acidosis or high serum triglyceride concentrations, consider whether feedings should be reduced."
Q_RISK = "Nutritionally at risk: 3-5 days"
Q_ENCON = "a contraindication to Enteral Nutrition (EN) exists"
Q_USP = "조제는 USP 797 무균 지침"
Q_NRS = "NRS 2002 · NUTRIC"
Q_NONHD = "비투석 0.6–0.8"
Q_HD = "HD·PD 1.2–1.3 → 1.5–1.8"
Q_CRRT = "CRRT 1.2–1.3 → 최대 2.0–2.5"
Q_SF = "경수술 1.2 · 골격외상 1.35 · 수술 1.44 · 감염 1.1–1.8 · 패혈증 1.6–1.8 · 화상 2.1–2.5"
Q_BCAA = "BCAA(leucine·valine·isoleucine)"
Q_STD = "표준 AA"
Q_RENAL = "체액↑·Na 조절이상·고K·고P·저Ca·대사성 산증"
Q_NA = "Higher doses of sodium in the setting of hyponatremia is not always required."
Q_VOL = "If hyponatremia etiology is from volume overload, additional sodium may worsen"
Q_MN = "복합제 함량 높아 독성(신경계"
Q_CXR = "tip 위치 확인(CXR)"
Q_XRAY = "x-ray confirmation at VAD placement"
Q_CLABSI = "CLABSI (가장 심각)"
Q_NAREF = "Na | 135–145 mEq/L"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치7 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "medex-015",
        "answer": 3,
        "referenceIds": [CCN],
        "coreSectionIds": [OBESE, PROT],
        "explain": "BMI 40.4는 40 이상이다. 그 구간 단백은 이상체중 기준 최대 2.5 g/kg/일이다. BMI 30–40은 이상체중 기준 2.0 g/kg/일 이상이다. 보정체중, 통상체중, 실제체중은 그 단백 칸이 아니다.",
        "evidence": [ev(CCN, "CCN_Summary_full.txt Obesity protein", Q_IBW)],
        "choiceExplanations": [
            "오답. 비만 단백의 CCN 칸은 보정체중이 아니다.",
            "오답. 통상체중으로 단백을 잡는 문장은 없다.",
            "오답. BMI 40 이상의 단백은 실제체중이 아니라 이상체중이다.",
            "정답. BMI ≥40 단백은 이상체중 기준 최대 2.5 g/kg/일이다.",
        ],
        "reviewNote": OK_NOTE + " 처방 110 g이 과다인지는 묻지 않아 계산하지 않았다.",
    },
    {
        "id": "medex-008",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL, FLUID],
        "explain": "총체수분은 남성 0.6, 여성·고령 남성 0.5, 고령 여성 0.45×체중이다. 72세 여성은 0.45라 체중 대비 비율이 남성 0.6보다 낮다. 그 계수로 체중만 보면 수액이 커질 수 있다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 0 TBW", Q_TBW)],
        "choiceExplanations": [
            "오답. 총체수분을 혈청 나트륨 농도가 정한다는 문장은 없다.",
            "정답. 고령 여성 계수는 0.45×체중이라 남성 0.6보다 낮다.",
            "오답. 나이·성별에 따라 계수가 달라진다.",
            "오답. 고령 여성 계수는 더 높은 비율이 아니다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "medex-006",
        "answer": 2,
        "referenceIds": [FACT, GILA],
        "coreSectionIds": [OBESE, CHO, LUNG],
        "explain": "혈당 248 mg/dL는 목표 140–180 밖이다. PN에서 혈당 조절이 문제면 공급량 감량을 검토한다. 아미노산을 끊고 지질만 늘리거나, 포도당을 유지한 채 인슐린만 올리거나, 포도당을 더 올리는 보기는 그 감량 문장이 아니다.",
        "evidence": [
            ev(FACT, "ASPEN_Fact_full.txt Question 1 clinical application", Q_REDUCE),
            ev(GILA, "PN_jjageuri_summary.md 8 중환자", Q_BG),
        ],
        "choiceExplanations": [
            "오답. 패혈증에서 지질만 남기고 아미노산을 끊으라는 문장은 없다.",
            "오답. 혈당이 목표를 넘으면 공급량 감량을 검토한다. 포도당을 그대로 두고 인슐린만 올리는 문장은 아니다.",
            "정답. 혈당 조절이 문제인 PN은 공급량 감량을 검토하고 혈당을 본다.",
            "오답. 포도당을 더 올리라는 방향은 감량 문장과 반대다.",
        ],
        "reviewNote": OK_NOTE + " 포도당 생성 증가·흡수 감소는 인용하지 않았다.",
    },
    {
        "id": "medex-007",
        "answer": 0,
        "referenceIds": [MYTHS],
        "coreSectionIds": [IND, EVAL],
        "explain": "영양위험은 3–5일이다. 5일간 섭취가 25% 미만이면 그 구간에 들어간다. PN을 일찍 시작하는 조건은 EN 금기, EN 불내성, 장 기능 부족이다. 위장관이 기능하므로 즉시 PN은 그 조건이 아니고, 위험을 평가에서 빼도 된다는 뜻도 아니다.",
        "evidence": [
            ev(MYTHS, "ASPEN_Myths_full.txt p.2 timing", Q_RISK),
            ev(MYTHS, "ASPEN_Myths_full.txt p.2 PN early", Q_ENCON),
        ],
        "choiceExplanations": [
            "정답. 5일은 영양위험 3–5일에 들어가고, 위장관이 기능하므로 즉시 PN 대신 영양 평가를 본다.",
            "오답. 즉시 PN은 EN 금기·불내성·장 기능 부족일 때다.",
            "오답. 진토제를 끊고 72시간 뒤에야 위험을 적는다는 문장은 없다.",
            "오답. 위장관이 기능해도 5일 저섭취는 영양위험 구간이다.",
        ],
        "reviewNote": OK_NOTE + " 급성질환 표의 섭취 <50%·>5일은 이 문항에 붙이지 않았다.",
    },
    {
        "id": "cnsc-nutrition-support-123",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [MIX],
        "explain": "PN 조제는 USP 797 무균 지침을 따른다. Affordable Care Act, HIPAA, ADA는 그 조제 문장이 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 5.1 혼합", Q_USP)],
        "choiceExplanations": [
            "오답. Affordable Care Act는 무균 조제 기준으로 적혀 있지 않다.",
            "정답. 조제는 USP 797 무균 지침이다.",
            "오답. HIPAA는 그 조제 문장이 아니다.",
            "오답. ADA는 그 조제 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " ISO Class 5와 BUD 숫자는 이 문장에 없어 넣지 않았다.",
    },
    {
        "id": "bcnsp-024",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL],
        "explain": "중환자 선별 도구는 NRS 2002와 NUTRIC이다. 이 보기 가운데 그 선별 도구는 NRS 2002다. BMI 계산, Harris-Benedict, 알부민은 그 선별 도구가 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 0 ICU 선별", Q_NRS)],
        "choiceExplanations": [
            "오답. BMI 계산은 NRS 2002·NUTRIC 선별 도구가 아니다.",
            "정답. NRS 2002는 중환자 선별 도구다. NUTRIC도 있으나 이 보기에는 없다.",
            "오답. Harris-Benedict는 열량식이다.",
            "오답. 알부민은 그 선별 도구가 아니다.",
        ],
        "reviewNote": OK_NOTE + " NUTRIC를 배제하는 문장으로 쓰지 않았다. 보기에 NRS 2002만 있다.",
    },
    {
        "id": "bcnsp-083",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT, DIS],
        "explain": "비투석 신부전 단백은 0.6–0.8 g/kg/일이다. 혈액투석·복막투석은 1.2–1.3에서 1.5–1.8로 올라가고, CRRT는 1.2–1.3에서 최대 2.0–2.5다. 단백을 줄인 제형은 비투석 CKD에 맞다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_NONHD),
            ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_HD),
            ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_CRRT),
        ],
        "choiceExplanations": [
            "오답. CRRT 단백은 감량 칸이 아니라 최대 2.0–2.5까지 올라간다.",
            "정답. 투석을 하지 않는 신부전은 0.6–0.8 g/kg/일이다.",
            "오답. 간헐 혈액투석은 1.2–1.3에서 1.5–1.8이다.",
            "오답. 신기능이 정상인 이식 환자가 0.6–0.8 칸은 아니다.",
        ],
        "reviewNote": OK_NOTE + " 저칼륨·저인 제품 문구는 보유 문장에 없어 단백 칸만 썼다. CRRT 상한을 정답으로 고르지 않았다.",
    },
    {
        "id": "rxk-1_3-6",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [ENERGY],
        "explain": "스트레스계수는 경수술 1.2, 골격외상 1.35, 수술 1.44, 감염 1.1–1.8, 패혈증 1.6–1.8, 화상 2.1–2.5다. 기초요구량에 그 정도를 반영하는 방법이 그 표다. Harris-Benedict만 쓰거나 25 kcal/kg만 쓰는 보기, 질소평형은 그 열량 표가 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 4.1 스트레스계수", Q_SF)],
        "choiceExplanations": [
            "오답. Harris-Benedict만 쓴다는 문장은 스트레스계수 표가 아니다.",
            "오답. 25 kcal/kg만 쓴다는 문장은 그 표가 아니다.",
            "정답. 기초요구량에 스트레스 정도를 반영하는 계수가 교재에 있다.",
            "오답. 질소평형은 열량 산정 방법이 아니다.",
        ],
        "reviewNote": OK_NOTE + " IC가 가능하면 IC가 우선이라는 문장은 이 보기를 지우지 않는다. 문항은 스트레스 반영이 적절한지를 묻는다.",
    },
    {
        "id": "rxk-2_1-5",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [DIS, PROT],
        "explain": "간질환에 적힌 아미노산은 BCAA(leucine, valine, isoleucine)다. 신부전은 표준 아미노산이다. ARDS와 당뇨병은 그 BCAA 대상이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8 간질환", Q_BCAA),
            ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_STD),
        ],
        "choiceExplanations": [
            "오답. 신부전은 표준 아미노산이다.",
            "오답. ARDS가 BCAA 제형의 대상으로 적혀 있지 않다.",
            "오답. 당뇨병이 그 BCAA 대상으로 적혀 있지 않다.",
            "정답. 간질환에 BCAA가 적혀 있다.",
        ],
        "reviewNote": OK_NOTE + " 저AAA·저전해질 제품 설명은 그 문장에 없어 대상만 닫았다. stage II 한정은 이 보기를 지우지 않는다.",
    },
    {
        "id": "rxk-3_1-6",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [DIS, FLUID, LYTE],
        "explain": "신부전의 소견은 체액 증가, 나트륨 조절 이상, 고칼륨, 고인산, 저칼슘, 대사성 산증이다. 당뇨병과 폐질환은 그 목록이 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_RENAL)],
        "choiceExplanations": [
            "오답. 당뇨병이 그 체액·전해질 목록에 없다.",
            "정답. 신부전에 체액 증가와 고칼륨·고인산·저칼슘·대사성 산증이 있다.",
            "오답. 폐질환이 그 목록에 없다.",
            "오답. 셋이 함께 해당한다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "rxk-3_3-6",
        "answer": 1,
        "referenceIds": [MYTHS],
        "coreSectionIds": [LYTE],
        "explain": "저나트륨이라고 나트륨을 항상 늘리지는 않는다. 원인이 체액 과부하면 나트륨을 더할 때 과부하와 저나트륨이 나빠질 수 있다. 나트륨이 수액 상태와 묶여 적힌 전해질이다.",
        "evidence": [
            ev(MYTHS, "ASPEN_Myths_full.txt p.2 hyponatremia", Q_NA),
            ev(MYTHS, "ASPEN_Myths_full.txt p.2 volume overload", Q_VOL),
        ],
        "choiceExplanations": [
            "오답. 칼륨을 수액 상태와 그렇게 묶는 문장은 없다.",
            "정답. 저나트륨의 나트륨 용량은 체액 과부하를 먼저 가른다.",
            "오답. 마그네슘을 수액 상태와 그렇게 묶는 문장은 없다.",
            "오답. 인을 수액 상태와 그렇게 묶는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-iib-039",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "explain": "망간은 복합제 함량이 높아 독성이 생기고, 그 독성은 신경계다. 보기 가운데 신경계 장기는 뇌다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 2.7 Mn", Q_MN)],
        "choiceExplanations": [
            "오답. 신장에 쌓인다는 문장은 없다. 담즙정체에서는 망간을 감량한다.",
            "정답. 망간 독성은 신경계이고, 그 장기로 적힌 보기는 뇌다.",
            "오답. 근육에 쌓인다는 문장은 없다.",
            "오답. 심장에 쌓인다는 문장은 없다. 심근병증은 셀레늄 결핍 쪽이다.",
        ],
        "reviewNote": OK_NOTE + " 파킨슨양 증상은 문제은행이라 인용하지 않았다.",
    },
    {
        "id": "quizlet-pn-023",
        "answer": 2,
        "referenceIds": [GILA, ADMIN],
        "coreSectionIds": [COMP, ROUTE],
        "explain": "기계적 합병증에는 위치이상이 있고, 끝 위치는 흉부 X선으로 확인한다. 투여 점검표도 혈관접근기구를 넣을 때 X선으로 위치를 확인한다. 청진 뒤나 확인 없이 바로 시작하는 보기는 그 문장이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.1 기계적", Q_CXR),
            ev(ADMIN, "ASPEN_Admin_full.txt VAD examination", Q_XRAY),
        ],
        "choiceExplanations": [
            "오답. 위치 확인 없이 즉시 시작한다는 문장은 없다.",
            "오답. 청진으로 끝을 확인한다는 문장은 없다.",
            "정답. 끝 위치는 흉부 X선으로 확인하고, 삽입 시에도 X선 확인이 있다.",
            "오답. 합병증이 없다는 말만으로 끝 위치를 대신하지 않는다.",
        ],
        "reviewNote": OK_NOTE + " 병상 삽입 후 CXR 전 시작 금지 한 줄은 문제은행이라 인용하지 않았다.",
    },
    {
        "id": "allaccess-005",
        "answer": 2,
        "referenceIds": [FACT, GILA],
        "coreSectionIds": [COMP, LUNG],
        "explain": "PN이나 EN에서 혈당 조절, 호흡성 산증, 고중성지방이 생기면 공급량 감량을 검토한다. CLABSI는 가장 심각한 감염 합병증이다. PN 관련 신장질환은 그 목록에 없다.",
        "evidence": [
            ev(FACT, "ASPEN_Fact_full.txt Question 1 clinical application", Q_REDUCE),
            ev(GILA, "PN_jjageuri_summary.md 6.1 감염", Q_CLABSI),
        ],
        "choiceExplanations": [
            "오답. 고중성지방은 공급량 감량을 검토하는 문제에 들어 있다.",
            "오답. 호흡성 산증도 그 감량 검토에 들어 있다.",
            "정답. PN 관련 신장질환은 합병증 목록에 없다.",
            "오답. CLABSI는 가장 심각한 감염 합병증이다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "cnsc-nutrition-support-008",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [LAB, LYTE],
        "explain": "나트륨 정상은 135–145 mEq/L다. 165 mEq/L는 그 위라 고나트륨혈증이다. 나머지 보기는 저나트륨혈증이다. 문항이 이미 자유수가 부족하다고 주었다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 7.2 Na", Q_NAREF)],
        "choiceExplanations": [
            "오답. 165 mEq/L는 135–145보다 높아 저나트륨이 아니다.",
            "오답. 희석성 저나트륨도 165와 방향이 반대다.",
            "정답. 165 mEq/L는 고나트륨이고, 문항의 자유수 부족과 같이 읽는다.",
            "오답. 가성 저나트륨도 165와 방향이 반대다.",
        ],
        "reviewNote": OK_NOTE + " 자유수 결핍의 계산식은 인용하지 않았다.",
    },
]


BLOCKERS = [
    (
        "cnsc-nutrition-support-079",
        "BLOCKER 배치7: CCN은 SICU 수술 전후·수술 후·중증 외상·TBI에서 아르기닌 포함 면역조절 제형을 고려하라고 한다. 중증 패혈증에서 신중히 쓰라는 문장은 없다. 아르기닌이 일산화질소가 된다는 줄은 노트 표기라 인용하지 않았다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-cnsc-practice-004",
        "BLOCKER 배치7: 중증 패혈증에서 아르기닌이 해롭다는 문장은 없다. CCN은 일부 수술·외상·TBI에서 아르기닌 포함 제형을 고려한다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-070",
        "BLOCKER 배치7: 면역조절 제형의 보유 대상은 SICU 수술 전후, 수술 후 EN, 중증 외상, TBI다. 대기 주요 위장관암 수술 전은 그 문장에 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-116",
        "BLOCKER 배치7: CCN 프로토콜 문장은 목표 열량 비율을 올리라는 것이다. 목표 도달 시간이 줄고 급식 중단이 적어진다는 결과 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-076",
        "BLOCKER 배치7: 열량 밀도 1.5–2.0 kcal/mL는 보유 문장에 없다. 고농도 아미노산 15–20%는 수분 제한 PN이지 이 경장 제제 숫자가 아니다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-068",
        "BLOCKER 배치7: 흉부 X선으로 확인하는 문장은 중심정맥관 끝이다. 비위관 선단의 방사선 확인 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-109",
        "BLOCKER 배치7: 경비장관과 경피 튜브를 예상 기간으로 가르는 문장, 4주 기준은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_2-1",
        "BLOCKER 배치7: CCN은 흡인 위험이 높거나 위 내 경장영양이 불내성이면 유문 이후로 바꾸라고 한다. 비위관이 위루보다 더 높다는 비교는 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_2-2",
        "BLOCKER 배치7: 유문 이후가 흡인 고위험의 대안이다. 비공장관과 공장루 중 공장루가 가장 낮다는 순위는 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_2-3",
        "BLOCKER 배치7: CCN은 위 볼루스 불내성 또는 흡인 고위험이면 지속 주입으로 바꾸라고 한다. 간헐·주기보다 볼루스가 가장 높다는 순위는 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_3-5",
        "BLOCKER 배치7: 단기간 영양지원 모니터로 적힌 것은 프리알부민이다. 질소평형이 가장 빠르다는 문장은 없고 프리알부민이 보기에 있다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-087",
        "BLOCKER 배치7: 프리알부민은 단기 모니터다. 주간 질소평형이 그보다 적절하다는 문장은 없다. 알부민을 진단 단독 지표로 쓰지 말라는 뜻과 질소평형 우선은 다르다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-005",
        "BLOCKER 배치7: 알부민 반감기 18–20일, 프리알부민 2–3일의 문장은 있다. 음성 급성기 반응물질이라는 표현은 교재 추출에 없다. 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-002",
        "BLOCKER 배치7: 6특징 합의 원문은 미보유다. 급성 중증 기준은 체중 감소·섭취·부종이다. 알부민 3.5 미만이 6특징 밖이라는 결론은 그 원문이 있어야 한다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-001",
        "BLOCKER 배치7: 6특징 중 최소 2개라는 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-016",
        "BLOCKER 배치7: 단일 검사 수치가 없다는 문장은 없다. 프리알부민과 알부민은 모니터 항목으로 적혀 있다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-017",
        "BLOCKER 배치7: 기아·만성질환·급성 질환의 세 병인 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-020",
        "BLOCKER 배치7: 염증 없는 만성 식욕부진을 기아 관련 영양불량으로 닫는 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "medex-013",
        "BLOCKER 배치7: 기아 관련 영양불량 표현형의 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-017",
        "BLOCKER 배치7: EN이 불가하고 중등–중증 영양불량이면 가능한 한 빨리 PN이다. 수술 전 PN을 중증에게만 일상적으로 쓴다는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-103",
        "BLOCKER 배치7: 잘영양·안정은 7일까지 기다릴 수 있고, 영양위험은 3–5일이다. 정답 5~7일은 그 두 칸을 한 간격으로 묶는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-3_2-1",
        "BLOCKER 배치7: 칼슘 글루콘산과 염화칼슘은 바꾸지 못한다. 칼슘염의 영향이 가장 작다는 보기와 그 문장이 충돌한다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-051",
        "BLOCKER 배치7: PICC는 혈전 증가와 tip 이동이 한 줄에 있다. 팔·어깨·목 부종이 혈전으로 닫힌다는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-041",
        "BLOCKER 배치7: 중환자 글루타민은 일상 투여하지 않는다고 적혀 있다. 조건부 필수 예는 신생아 taurine·tyrosine·cysteine이다. 장세포의 주된 연료라는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-010",
        "BLOCKER 배치7: HPN 혈액검사는 첫 달 매주 뒤 매달이다. 시작 전과 시작 당일을 가르는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-4_1-2",
        "BLOCKER 배치7: 24시간 홈케어 업체 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "oep-bcscp-q-034",
        "BLOCKER 배치7: 구 USP BUD는 실온 30시간·냉장 9일이다. 2–8°C로 보관한 뒤 실온화하라는 복약 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-014",
        "BLOCKER 배치7: 질소는 단백÷6.25다. 24시간 요요소질소로 질소 균형을 본다는 문장은 없고, +4 g도 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-023",
        "BLOCKER 배치7: 출구 감염은 온찜질·매일 국소치료·경구 항생제다. 정답 보기는 전신 항균제다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_3-6",
        "BLOCKER 배치7: 재급식 고위험은 알코올 중독·신경성 식욕부진·심한 영양결핍이다. 장기 정맥영양과 심한 스트레스·고갈이 그 목록 밖에 같이 남는다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-029",
        "BLOCKER 배치7: 재급식 고위험 세 항목으로 흡수장애·비만대사수술·3일 섭취 부족이 함께 목록 밖에 남는다. 아닌 것이 하나로 닫히지 않는다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
        "myths": NOTES / "06_학습_노트/_gl_extract/ASPEN_Myths_full.txt",
        "fact": NOTES / "06_학습_노트/_gl_extract/ASPEN_Fact_full.txt",
        "admin": NOTES / "06_학습_노트/_gl_extract/ASPEN_Admin_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_IBW: "ccn",
        Q_TBW: "sum",
        Q_BG: "sum",
        Q_REDUCE: "fact",
        Q_RISK: "myths",
        Q_ENCON: "myths",
        Q_USP: "sum",
        Q_NRS: "sum",
        Q_NONHD: "sum",
        Q_HD: "sum",
        Q_CRRT: "sum",
        Q_SF: "sum",
        Q_BCAA: "sum",
        Q_STD: "sum",
        Q_RENAL: "sum",
        Q_NA: "myths",
        Q_VOL: "myths",
        Q_MN: "sum",
        Q_CXR: "sum",
        Q_XRAY: "admin",
        Q_CLABSI: "sum",
        Q_NAREF: "sum",
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
    sys.exit("Historical review batch; use export_questions.py --output NEW_FILE for a comparison.")
