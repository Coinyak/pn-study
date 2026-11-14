#!/usr/bin/env python3
"""Batch 1 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes. Optional explain text is only a narrowing to that source.

Usage: python3 scripts/review_batch1.py
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
CONTENT_VERSION = "2026-11-14.3"

MYTHS = "aspen-pn-myths-practice-tool-2024"
CARBS = "espen-ped-pn-2018-05-carbohydrates"
FACT = "aspen-adult-critically-ill-factsheet-2024"
CCN = "ccn-summary-nestle-2022"
GILA = "imsangyoungyang-gilajabi"
KSHP = "kshp-yeongyang-yakryo-lecture-answers"
CAP = "espen-ped-pn-2018-08-calcium-phosphorus-magnesium"
COMPOUND = "aspen-pn-checklist-03-compounding-2024"

G21 = "sec-cho_gir-2-1-탄수화물-dextrose"
LIP = "sec-lipid-2-2-지방-ILE"
RT31 = "sec-route-3-1-말초-vs-중심"
S54 = "sec-stability-5-4-필터-hang-time-세트-BUD"
S52 = "sec-stability-5-2-Ca-P-침전"
DZ = "sec-disease-8-질환별-PN"
DZ82 = "sec-disease-8-2-당뇨-비만"
RS = "sec-complications-6-2-재급식-증후군-Refeeding"
TE = "sec-vit_te-2-7-미량원소-TE"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


# answer = current keyed index. The applier refuses to write a different index.
PROMOTIONS = [
    {
        "id": "cnsc-nutrition-support-041",
        "answer": 0,
        "referenceIds": [MYTHS],
        "coreSectionIds": [RT31],
        "errataIds": [],
        "evidence": [ev(MYTHS, "p.3 'PN must always be infused through a central line' 항목",
                        "For peripheral PN, do not exceed 900 mOsm/L.")],
        "choiceExplanations": [
            "정답. ASPEN Myths 2024: 말초 PN은 900 mOsm/L를 넘기지 않는다.",
            "오답. 600 mOsm/L는 그 상한보다 낮다. 상한으로 외우는 값은 900이다.",
            "오답. 1,500 mOsm/L는 말초 상한 900을 넘는다.",
            "오답. 2,800 mOsm/L도 말초 상한 900을 넘는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. ASPEN Myths 2024 p.3 말초 PN ≤900 mOsm/L.",
    },
    {
        "id": "cnsc-nutrition-support-042",
        "answer": 3,
        "referenceIds": [CARBS, MYTHS],
        "coreSectionIds": [G21, RT31],
        "errataIds": [],
        "evidence": [ev(CARBS, "Introduction",
                        "In parenteral nutrition (PN) carbohydrate is provided as dextrose (D-Glucose), in its monohydrate form. Dextrose usually contributes most to the osmolality of the PN-solution."),
                     ev(MYTHS, "p.3 ILE hang time 항목",
                        "This is due to the increased risk of microbial contamination due to the isotonic nature of ILE solutions.")],
        "choiceExplanations": [
            "오답. 따로 주는 지질유제는 등장성에 가깝다. 최종 용액 삼투압의 대부분은 포도당이 만든다.",
            "오답. 미량원소는 소량이라 최종 삼투압의 주성분이 아니다.",
            "오답. 종합비타민도 소량이라 최종 삼투압의 주성분이 아니다.",
            "정답. ESPEN 소아 탄수화물 지침: PN의 탄수화물은 일수화물 dextrose이고, 보통 PN 용액 삼투압에 가장 크게 기여한다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. ESPEN pediatric carbohydrates 서론.",
    },
    {
        "id": "cnsc-nutrition-support-053",
        "answer": 2,
        "referenceIds": [MYTHS],
        "coreSectionIds": [S54, LIP],
        "errataIds": [],
        "explain": "지질이 3-in-1(TNA)에 들어 있으면 최대 24시간까지 주입할 수 있다. 2-in-1과 따로 주는 지질유제는 등장성이라 미생물 위험이 커서 12시간으로 제한한다.",
        "evidence": [ev(MYTHS, "p.3 'ILE has a hang time of 24 hours when y-sited' 항목",
                        "If ILE are formulated in a Total Nutrient Admixture (TNA), the TNA can be infused for up to 24 hours."),
                     ev(MYTHS, "p.3 같은 항목",
                        "If ILE are infused separately from a 2–in–1 PN admixture (whether in a repackaged container or in the original container), the maximum hang time should be limited to 12 hours.")],
        "choiceExplanations": [
            "오답. 12시간은 2-in-1과 따로 주입하는 지질유제의 상한이다. 3-in-1이 아니다.",
            "오답. 48시간은 TNA hang time 상한 24시간을 넘는다.",
            "정답. 지질이 TNA(3-in-1) 안에 있으면 최대 24시간까지 주입할 수 있다.",
            "오답. 72시간은 24시간 상한을 넘는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 해설에서 근거 없는 2-in-1 24시간 문장만 뺐다.",
    },
    {
        "id": "cnsc-nutrition-support-022",
        "answer": 1,
        "referenceIds": [CCN, FACT],
        "coreSectionIds": [DZ],
        "errataIds": [],
        "evidence": [ev(CCN, "PROTEIN",
                        "Suggest sufficient (high-dose) protein should be provided in the range of 1.2-2.0g/kg ABW*/day in the patient with BMI less than 30 and may likely be even higher in burn or multi-trauma patients."),
                     ev(FACT, "Guideline question 2",
                        "we cannot make a new recommendation at this time beyond the 2016 guideline suggestion for 1.2-2.0 g/kg/day.")],
        "choiceExplanations": [
            "오답. 0.6–0.8 g/kg/day는 중환자 권고 범위보다 낮다.",
            "정답. 2016 SCCM/ASPEN을 요약한 자료와 2024 팩트시트 모두 대부분 중환자 단백을 1.2–2.0 g/kg/day로 둔다.",
            "오답. 0.8–1.0 g/kg/day도 그 범위보다 낮다.",
            "오답. 2.5–3.0 g/kg/day는 대부분 중환자의 기본 범위가 아니다. 화상·다발외상은 더 높일 수 있으나 이 보기 자체가 기본 권고는 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. CCN 요약 2022 PROTEIN 항·ASPEN Factsheet 2024 question 2.",
    },
    {
        "id": "bcnsp-003",
        "answer": 1,
        "referenceIds": [CCN],
        "coreSectionIds": [DZ],
        "errataIds": [],
        "evidence": [ev(CCN, "PROTEIN",
                        "Suggest sufficient (high-dose) protein should be provided in the range of 1.2-2.0g/kg ABW*/day in the patient with BMI less than 30"),
                     ev(CCN, "각주", "*ABW is Actual Body Weight")],
        "choiceExplanations": [
            "오답. 0.6–0.8 g/kg 실제체중은 BMI 30 미만 중환자 범위보다 낮다.",
            "정답. BMI 28은 30 미만이므로 1.2–2.0 g/kg 실제체중(ABW)/일이다.",
            "오답. 2.5–3.0 g/kg 이상체중은 BMI 28의 권고가 아니다.",
            "오답. 0.8–1.0 g/kg 이상체중은 범위와 체중 기준이 모두 다르다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. BMI 28은 CCN 요약의 BMI <30 · ABW 1.2–2.0에 해당.",
    },
    {
        "id": "quizlet-pn-014",
        "answer": 1,
        "referenceIds": [CCN],
        "coreSectionIds": [DZ82],
        "errataIds": [],
        "evidence": [ev(CCN, "OBESITY",
                        "Protein is suggested at ≥ 2.0 gm/kg IBW**/day for BMI 30–40, and up to 2.5 gm/kg IBW**/day for BMI ≥ 40."),
                     ev(CCN, "각주", "**IBW is Ideal Body Weight")],
        "choiceExplanations": [
            "오답. 이상체중 기준 2.0 g/kg/day 미만은 BMI 30–40 권고보다 낮다.",
            "정답. 비만 중환자 단백은 실제체중이 아니라 이상체중 기준이다. BMI 30–40은 2.0 g/kg/day 이상, BMI ≥40은 최대 2.5 g/kg/day까지이며 둘 다 이상체중 기준 2.0 이상에 해당한다.",
            "오답. 실제체중 기준 2.0 미만은 체중 기준부터 다르다.",
            "오답. 2.0 이상이어도 실제체중 기준이면 이 권고와 맞지 않는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. stem의 BMI >33.4는 보기 중 IBW ≥2.0만 CCN 비만 단백과 맞다.",
    },
    {
        "id": "cnsc-nutrition-support-023",
        "answer": 0,
        "referenceIds": [GILA, CARBS],
        "coreSectionIds": [G21],
        "errataIds": ["E3-dextrose-factor"],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 형태·열량 행 [TXT p143]",
                        "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본"),
                     ev(CARBS, "Introduction",
                        "carbohydrate is provided as dextrose (D-Glucose), in its monohydrate form."),
                     ev(GILA, "같은 행 [TXT p033]", "무수화물 4")],
        "choiceExplanations": [
            "정답. IV 포도당은 일수화물로 3.4 kcal/g이다.",
            "오답. 4.0 kcal/g는 무수 포도당·경구 탄수화물 계수이다.",
            "오답. 7.0 kcal/g는 IV 포도당 계수가 아니다.",
            "오답. 9.0 kcal/g는 순수 지방의 Atwater 계수에 가깝고 포도당 계수가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. E3와 같은 방향(3.4). 수치는 교재 p143, 일수화물 형태는 ESPEN carbs.",
    },
    {
        "id": "quizlet-pn-012",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [G21, LIP],
        "errataIds": ["E3-dextrose-factor"],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 형태·열량 [TXT p143]", "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본"),
                     ev(GILA, "단백질 행", "결정 AA 형태 · 4 kcal/g"),
                     ev(GILA, "지질 열량 행 [EXAM p144]", "10% 1.1 kcal/mL · 20% 2.0 kcal/mL · 3-in-1 계산 시 지방 10 kcal/g")],
        "choiceExplanations": [
            "오답. 열량 1,830 kcal는 맞지만 지방은 40 g이 아니다. 20% 225 mL는 지방 45 g이다.",
            "오답. 포도당을 4 kcal/g로 두면 총열량이 2,010 kcal 쪽으로 올라가고, 지방 40 g도 틀리다.",
            "정답. 포도당 300×3.4=1,020, 단백 90×4=360, 20% 225 mL=450 kcal·지방 45 g. 합은 1,830 kcal, 지방 45 g.",
            "오답. 지방 45 g은 맞지만 1,470 kcal는 단백 360 kcal가 빠진 값이다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 계수 3.4·4·20% 2 kcal/mL는 교재 정리. 산술만 검산.",
    },
    {
        "id": "quizlet-pn-013",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [G21, LIP],
        "errataIds": ["E3-dextrose-factor"],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 형태·열량 [TXT p143]", "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본"),
                     ev(GILA, "단백질 행", "결정 AA 형태 · 4 kcal/g"),
                     ev(GILA, "지질 열량 행 [EXAM p144]", "20% 2.0 kcal/mL")],
        "choiceExplanations": [
            "오답. 27.5 kcal/kg/day는 포도당을 3.4이 아닌 4 kcal/g로 둔 쪽에 가깝다.",
            "오답. 21.9 kcal/kg/day는 1,896 kcal를 75 kg으로 나눈 값이 아니다.",
            "오답. 26.5 kcal/kg/day도 같은 계수로 나누면 나오지 않는다.",
            "정답. 단백 117×4=468, 포도당 273×3.4=928, 20% 250 mL=500. 합 1,896 kcal ÷ 75 kg = 25.3 kcal/kg/day. 65 mL/h는 이 일일 계산에 쓰지 않는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 273×3.4는 928.2이며 합을 75로 나누면 25.3으로 반올림된다.",
    },
    {
        "id": "allaccess-007",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [G21],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md GIR 공식 [TXT p144]",
                        "GIR (mg/kg/min) = [Dex(%) × 속도(mL/h) × 0.167] ÷ 체중(kg) = mg dextrose ÷ (kg × 1440)")],
        "choiceExplanations": [
            "오답. 0.003은 mg 환산이나 1,440분 환산이 빠진 자릿수이다.",
            "오답. 0.30은 2.98보다 10배 작다.",
            "정답. D15 2 L는 포도당 300 g = 300,000 mg. 300,000 ÷ (70 × 1,440) = 2.98 mg/kg/min.",
            "오답. 30은 2.98보다 10배 크다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. E2(조건 없는 GIR 상한)와 무관한 계산 문항이라 errata 연결을 뗐다.",
    },
    {
        "id": "oe-tg400",
        "answer": 2,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md TG 컷 감량·중단 [EXAM p181]",
                        "TG ≥400 ⟶ ILE 회피·감량·중단"),
                     ev(MYTHS, "p.1 hypertriglyceridemia 항목",
                        "Cautious initiation of PN may be warranted in adult patients with hypertriglyceridemia (serum triglycerides >200 mg/dL)."),
                     ev(GILA, "TG 컷 췌장염 유발 [TXT p182·p210]", "대개 TG >1,000")],
        "choiceExplanations": [
            "오답. 150 mg/dL는 감량·중단 기준이 아니다.",
            "오답. 200 mg/dL 초과는 저용량으로 신중히 시작하는 기준이다. 감량·중단 컷이 아니다.",
            "정답. 성인에서 ILE를 피하거나 감량·중단하는 기준으로 외우는 값은 TG ≥400 mg/dL이다.",
            "오답. 1,000 mg/dL 초과는 췌장염을 일으킬 수 있는 더 높은 값이다. 감량·중단을 고려하는 컷은 400이다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. ≥400은 교재 p181, >200 개시는 ASPEN Myths 2024.",
    },
    {
        "id": "quizlet-pn-047",
        "answer": 0,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md TG 컷 [EXAM p181]", "TG ≥400 ⟶ ILE 회피·감량·중단"),
                     ev(MYTHS, "p.1 hypertriglyceridemia 항목",
                        "serum triglycerides >200 mg/dL")],
        "choiceExplanations": [
            "정답. 성인 PN에서 ILE를 제한하는 혈청 중성지방 컷은 400 mg/dL이다.",
            "오답. 300 mg/dL는 그 컷이 아니다.",
            "오답. 200 mg/dL 초과는 시작을 낮춰 신중히 하는 기준이지, 사용을 제한하는 컷은 아니다.",
            "오답. 100 mg/dL는 제한 기준이 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 교재 p181 ≥400.",
    },
    {
        "id": "bcnsp-004",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md TG 컷 [EXAM p181]", "TG ≥400 ⟶ ILE 회피·감량·중단")],
        "choiceExplanations": [
            "오답. 450 mg/dL는 400 이상이므로 같은 속도로 유지하지 않는다.",
            "정답. TG ≥400 mg/dL이면 ILE를 감량하거나 보류하고 다시 측정한다.",
            "오답. 중성지방이 올랐다고 정맥영양 전체를 바로 끊는 기준은 아니다.",
            "오답. 30% 제형으로 바꾸는 것이 보유 기준의 대응이 아니다. 대응은 감량·보류 후 재검이다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 450 mg/dL는 교재 ≥400 감량·중단 구간에 들어간다.",
    },
    {
        "id": "cnsc-nutrition-support-089",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md TG 컷 [EXAM p181]", "TG ≥400 ⟶ ILE 회피·감량·중단")],
        "choiceExplanations": [
            "오답. 중성지방이 이미 450 mg/dL인데 지질을 늘리지 않는다.",
            "오답. 1,000 mg/dL까지 기다리지 않는다. 감량·중단 컷은 400이다.",
            "오답. 덱스트로스를 늘리는 것은 고중성지방의 대응이 아니다.",
            "정답. 정맥 지질을 줄이거나 보류하고 중성지방을 다시 측정한다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. bcnsp-004와 같은 교재 p181 기준.",
    },
    {
        "id": "quizlet-pn-031",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "explain": "성인에서 지질유제는 혈청 중성지방이 400 mg/dL 이상이 되지 않도록 감량하거나 중단한다. 성인 주입 속도 상한은 0.11 g/kg/h이다. 20% 제형은 10%보다 인지질 대 중성지방 비가 낮아 청소에 유리하다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md TG 컷 [EXAM p181]", "TG ≥400 ⟶ ILE 회피·감량·중단"),
                     ev(GILA, "주입속도 행 [EXAM p144]", "성인 ≤0.11 g/kg/h"),
                     ev(GILA, "20% 선호 행 [EXAM p044]", "인지질:TG 비 낮음(유리인지질↓)")],
        "choiceExplanations": [
            "오답. L-카르니틴 보충은 성인 ILE 부작용을 막는 보유 기준이 아니다.",
            "오답. 0.05 g/kg/h가 상한이 아니다. 성인 속도 상한은 0.11 g/kg/h이다.",
            "오답. 10%보다 20%가 인지질 대 중성지방 비가 낮아 선호된다.",
            "정답. 혈청 중성지방이 400 mg/dL를 넘지 않도록 용량을 맞추는 것이 보유 기준의 예방이다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 해설의 소아 속도·TG 수치는 보유 인용과 달라 성인 기준만 남겼다.",
    },
    {
        "id": "quizlet-pn-046",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md Propofol 행 [TXT p182]",
                        "10% 지방유제 vehicle(1.1 kcal/mL) ⟶ kcal·TG 합산, PN 지질 감량/중단 고려")],
        "choiceExplanations": [
            "오답. 프로포폴 운반체와 겹치는 문제는 혈당이 아니라 지질 열량과 중성지방이다.",
            "정답. 프로포폴은 10% 지방유제에 들어 있다. PN 지질과 열량·중성지방을 합산하지 않으면 고중성지방혈증이 될 수 있다.",
            "오답. 고질소혈증은 이 병용의 보유 결과가 아니다.",
            "오답. 고나트륨혈증은 이 병용의 보유 결과가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 교재 p182 propofol은 10% 지방유제, kcal·TG 합산.",
    },
    {
        "id": "oe-hypergly-assess",
        "answer": 1,
        "referenceIds": [MYTHS, GILA],
        "coreSectionIds": [G21, DZ82],
        "errataIds": [],
        "relatedAdd": ["oep-bcscp-q-064"],
        "evidence": [ev(MYTHS, "p.1 hyperglycemia 항목",
                        "Cautious initiation of PN may be warranted in adult patients with hyperglycemia (glucose >180 mg/dL)."),
                     ev(MYTHS, "p.1 같은 항목",
                        "Advance PN more conservatively with vigilant laboratory monitoring and prompt intervention, if indicated."),
                     ev(MYTHS, "p.1 같은 항목",
                        "Use insulin per institutional protocols to control glucose levels."),
                     ev(GILA, "GIR 공식 [TXT p144]", "mg dextrose ÷ (kg × 1440)")],
        "choiceExplanations": [
            "오답. 혈당이 180 mg/dL를 넘으면 포도당을 더 올리지 않는다. 시작 용량을 낮추는 쪽이다.",
            "정답. 이 처방의 GIR은 250,000 mg ÷ (70×1,440) ≈ 2.5 mg/kg/min이라 포도당 과다만으로 단정하지 않는다. 원인을 보고 증량을 보류하며 혈당을 감시하고 인슐린으로 조절한다.",
            "오답. 혈당 350 mg/dL만으로 평가 없이 PN 전체를 즉시 끊는 권고는 아니다. 고혈당은 PN 절대 금기가 아니다.",
            "오답. 영양팀과 상의하지 않고 당장 경장영양만으로 바꾸는 대응은 보유 권고가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 혈당 >180의 보수적 증량·감시·인슐린은 ASPEN Myths 2024 p.1.",
    },
    {
        "id": "oep-bcscp-q-064",
        "answer": 1,
        "referenceIds": [MYTHS, GILA],
        "coreSectionIds": [G21, DZ82],
        "errataIds": [],
        "relatedAdd": ["oe-hypergly-assess"],
        "evidence": [ev(MYTHS, "p.1 hyperglycemia 항목",
                        "Cautious initiation of PN may be warranted in adult patients with hyperglycemia (glucose >180 mg/dL)."),
                     ev(MYTHS, "p.1 같은 항목",
                        "Initiate PN with lower dextrose dose adjusted for hyperglycemia."),
                     ev(GILA, "GIR 공식 [TXT p144]", "mg dextrose ÷ (kg × 1440)")],
        "choiceExplanations": [
            "오답. 혈당 350 mg/dL에서 덱스트로스 부하를 늘리지 않는다.",
            "정답. 250 g ÷ (70 kg × 1,440 min) ≈ 2.48 mg/kg/min이다. 증량을 보류하고 원인 평가, 감시, 혈당 조절을 같이 한다.",
            "오답. 평가 없이 PN을 전부 중단하는 것은 고혈당 환자의 보유 대응이 아니다.",
            "오답. 상의 없이 즉시 경장영양으로 바꾸라는 권고는 없다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. oe-hypergly-assess와 같은 사실.",
    },
    {
        "id": "quizlet-pn-027",
        "answer": 0,
        "referenceIds": [GILA, MYTHS, COMPOUND],
        "coreSectionIds": [S52],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md Ca-P 용해도↑ [EXAM p153] [TXT p153]",
                        "AA 농도↑ · cysteine 포함(산성화) · Ca gluconate(CaCl₂보다 해리↓) · pH↓ · 온도↓"),
                     ev(MYTHS, "p.4 calcium salts 항목",
                        "Calcium gluconate and calcium chloride are not interchangeable."),
                     ev(MYTHS, "p.4 같은 항목",
                        "rendering less free calcium ions to form calcium phosphate precipitates."),
                     ev(GILA, "Ca-P 위험 행 [TXT p201]", "P 먼저 / Ca 마지막"),
                     ev(COMPOUND, "Manual compounding sequence, calcium row",
                        "Calcium gluconate. The preferred source of calcium when using inorganic phosphate salts.")],
        "choiceExplanations": [
            "정답. 아미노산 농도를 높이면 인산칼슘이 덜 침전된다.",
            "오답. 염화칼슘은 글루콘산칼슘보다 잘 해리되어 침전에 쓸 유리 칼슘이 늘어난다.",
            "오답. 온도가 오르면 용해도가 떨어진다. 온도를 낮추는 쪽이 침전을 줄인다.",
            "오답. 인산염을 먼저 넣고 칼슘은 마지막에 넣는다. 인산염 직후 칼슘을 바로 넣지 않는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 교재 p153·p201, ASPEN Myths p.4, Compounding checklist 순서.",
    },
    {
        "id": "quizlet-pn-004",
        "answer": 2,
        "referenceIds": [GILA, KSHP],
        "coreSectionIds": [DZ82, G21],
        "errataIds": [],
        "relatedAdd": ["kshp-01", "cnsc-nutrition-support-085", "quizlet-cnsc-practice-002"],
        "explain": "성인 입원 PN과 중환자에서 목표 혈당으로 외우는 범위는 140–180 mg/dL이다. 110 mg/dL 미만을 목표로 한 집중 조절은 저혈당 위험 때문에 권하지 않는다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 혈당 PN 성인 [EXAM p034] [TXT p179]", "PN 성인 140~180 mg/dL"),
                     ev(KSHP, "1. 탄수화물.pdf p.42–43, 문제 1",
                        "ASPEN guideline에서 추천하는 정맥영양을 받는 성인 입원환자에서의 적절한 혈당 조절 범위는 140–180 mg/dL이다. 110 mg/dL 미만을 목표로 한 집중 혈당조절은 저혈당 위험 때문에 권고되지 않는다.")],
        "choiceExplanations": [
            "오답. 80–110 mg/dL는 110 mg/dL 미만 집중 조절에 걸쳐 있어 표준 목표가 아니다.",
            "오답. 220–240 mg/dL는 180 mg/dL를 넘는 고혈당 쪽이다.",
            "정답. 성인 입원 PN·중환자 목표 혈당은 140–180 mg/dL이다.",
            "오답. 180–220 mg/dL는 상한이 180을 넘는다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 해설의 AACE/ADA 귀속은 원문이 없어 교재·영양약료 강의 문장으로 좁혔다.",
    },
    {
        "id": "cnsc-nutrition-support-085",
        "answer": 1,
        "referenceIds": [GILA, KSHP],
        "coreSectionIds": [DZ82],
        "errataIds": [],
        "relatedAdd": ["kshp-01", "quizlet-pn-004", "quizlet-cnsc-practice-002"],
        "explain": "영양지원을 받는 대부분의 중환자에서 목표 혈당은 140–180 mg/dL이다. 80–110 mg/dL처럼 더 조이거나 70 mg/dL 미만은 이 목표가 아니다.",
        "evidence": [ev(GILA, "중환자 행 BG", "BG 140–180"),
                     ev(KSHP, "1. 탄수화물.pdf p.42–43, 문제 1",
                        "110 mg/dL 미만을 목표로 한 집중 혈당조절은 저혈당 위험 때문에 권고되지 않는다.")],
        "choiceExplanations": [
            "오답. 80–110 mg/dL는 표준 목표 140–180보다 낮다.",
            "정답. 대부분의 중환자 목표 혈당은 140–180 mg/dL이다.",
            "오답. 200–250 mg/dL는 180을 넘는 범위이다.",
            "오답. 70 mg/dL 미만은 저혈당이지 목표 범위가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 사망률 문장은 보유 인용에 없어 범위 설명만 남겼다.",
    },
    {
        "id": "quizlet-cnsc-practice-002",
        "answer": 1,
        "referenceIds": [GILA, KSHP],
        "coreSectionIds": [DZ82],
        "errataIds": [],
        "relatedAdd": ["kshp-01", "quizlet-pn-004", "cnsc-nutrition-support-085"],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 혈당 PN 성인 [EXAM p034] [TXT p179]", "PN 성인 140~180 mg/dL"),
                     ev(KSHP, "1. 탄수화물.pdf p.42–43, 문제 1 선택지 해설",
                        "110 mg/dL 미만을 목표로 한 집중 혈당조절은 저혈당 위험 때문에 권고되지 않는다.")],
        "choiceExplanations": [
            "오답. 80–110 mg/dL는 110 미만 집중 조절에 걸치고 표준 목표가 아니다.",
            "정답. 중환자 입원 중 목표 혈당은 140–180 mg/dL이다.",
            "오답. 181–210 mg/dL는 180을 넘는다.",
            "오답. 211–240 mg/dL도 목표 범위가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 기존 해설(110 미만 비권고)은 영양약료 강의 문제 1과 맞다.",
    },
    {
        "id": "quizlet-iib-004",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "재급식 위험이 있으면 티아민을 보충한다. 장기 기아·알코올 환자에서 PN 초기 5–7일간 thiamine 50–100 mg/day와 folate 1 mg/day를 준다. 포도당을 주면 티아민 요구가 늘어난다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md Vit B1 [TXT p184]",
                        "장기기아/알코올: PN 초기 5–7일 thiamine 50–100 mg/d + folate 1 mg/d"),
                     ev(GILA, "재급식 정의 [TXT p185]",
                        "수분·전해질·비타민·미네랄(P·Mg·K·thiamine) 대사변화")],
        "choiceExplanations": [
            "오답. 비타민 A는 재급식 때 우선 보충하는 비타민이 아니다.",
            "오답. 비타민 K도 그 보충 대상이 아니다.",
            "정답. 재급식 위험 환자에게 보충하는 것은 티아민이다. 교재는 초기 5–7일 50–100 mg/day이다.",
            "오답. 아스코르브산이 아니라 티아민이다. 같이 적힌 보조는 folate 1 mg/day이다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 용량 문장을 교재 p184(50–100 mg/d, folate 1 mg)에 맞췄다.",
    },
    {
        "id": "cnsc-nutrition-support-082",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "재급식 증후군은 저인산혈증·저칼륨혈증·저마그네슘혈증이 같이 오고 티아민 결핍이 동반된다. 탄수화물을 다시 주면 이들 전해질이 세포 안으로 이동해 혈청 농도가 떨어진다.",
        "evidence": [ev(GILA, "재급식 표지", "저인산혈증(핵심) + ↓K · ↓Mg (+ thiamine 결핍)"),
                     ev(GILA, "재급식 정의 [TXT p185]", "P·Mg·K·thiamine")],
        "choiceExplanations": [
            "오답. 인산·칼륨·마그네슘이 오르는 쪽이 아니다. 떨어진다.",
            "정답. 저인산혈증, 저칼륨혈증, 저마그네슘혈증이 재급식의 전해질 삼징후이다.",
            "오답. 고나트륨·저칼슘·고인산 조합이 아니다.",
            "오답. 저칼륨은 맞을 수 있으나 고나트륨·고인산은 삼징후가 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 교재 재급식 표지(저인산·↓K·↓Mg).",
    },
    {
        "id": "bcnsp-007",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", "저인산혈증(핵심) + ↓K · ↓Mg (+ thiamine 결핍)")],
        "choiceExplanations": [
            "오답. 고나트륨혈증이 재급식의 대표 소견이 아니다.",
            "정답. 재급식 증후군의 핵심 대사 이상은 저인산혈증이다.",
            "오답. 칼륨은 오르지 않고 떨어진다.",
            "오답. 고칼슘혈증이 대표 소견이 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. 교재는 저인산혈증을 재급식의 핵심 표지로 둔다.",
    },
    {
        "id": "bcnsp-059",
        "answer": 2,
        "referenceIds": [CAP],
        "coreSectionIds": [TE],
        "errataIds": [],
        "explain": "유리병에 담긴 글루콘산칼슘은 알루미늄에 오염될 수 있어 PN 알루미늄 노출의 주요 공급원으로 다룬다. 아미노산, 포도당, 종합비타민은 그 문장에 없다.",
        "evidence": [ev(CAP, "R 8.6",
                        "Acidic solutions packaged in glass vials, such as calcium gluconate, are contaminated with aluminum and should not be used in PN")],
        "choiceExplanations": [
            "오답. 아미노산이 그 알루미늄 오염원으로 지목되지 않는다.",
            "오답. 포도당도 아니다.",
            "정답. ESPEN 소아 Ca·P 권고 R8.6은 유리병의 글루콘산칼슘을 알루미늄 오염원으로 지목한다. 그 성분이 들어 있는 보기가 정답이다.",
            "오답. 종합비타민 첨가제는 그 문장의 오염원이 아니다.",
        ],
        "reviewNote": "배치1 verified. 정답 인덱스 유지. FDA 25 mcg/L 문장은 원문이 없어 해설에서 뺐다. 인산염은 정답 보기에 함께 적혀 있고, 보유 문장이 이름 붙인 성분은 글루콘산칼슘이다.",
    },
]

BLOCKERS = [
    ("kshp-15", "배치1 재확인: 강의 정답 84 g은 유지한다. ESPEN 2024 원문이 없어 verified로 올리지 않는다."),
    ("kshp-28", "배치1 재확인: 정답 0.22/1.2는 현행 단일 1.2 μm와 충돌한다. 인덱스를 바꾸지 않고 pending을 유지한다."),
    ("kshp-34", "배치1 재확인: 정답 용량은 AMA 1979 값이라 현행 ASPEN TE와 다르다. 인덱스를 바꾸지 않고 pending을 유지한다."),
    ("kshp-39", "배치1 재확인: NUTRIC ≥5와 ≥6이 한 문항에 섞여 단일 정답이 불확정이다. pending을 유지한다."),
    ("kshp-46", "배치1 재확인: 해설이 비타민 K도 답이 될 수 있다고 적는다. 인덱스를 바꾸지 않고 pending을 유지한다."),
    ("kshp-48", "배치1 재확인: kshp-01과 같은 140–180 문항이다. 기본 세트에 넣지 않고 추가 연습으로 pending을 유지한다."),
    ("cnsc-nutrition-support-043", "BLOCKER: 중심 PN 1,500–2,800 mOsm/L를 적은 보유 원문 인용을 찾지 못했다. 정답 인덱스는 유지하고 pending으로 둔다."),
    ("quizlet-pn-003", "BLOCKER: '가장 흔한 합병증=고혈당'은 교재 정리의 문제은행 빈도 표기만 있고 쪽·지침 문장으로 확인하지 못했다. pending을 유지한다."),
    ("rxk-3_2-5", "BLOCKER: 유화가 깨진 TNA를 주지 않는다는 문장은 핵심표에 있으나 태그가 문제은행이라 지침 인용으로 승격하지 않았다. 정답(해롭다)은 유지한다."),
    ("bcnsp-008", "BLOCKER: 일반 CSP 실온 4일을 적은 USP <797> 원문이 없다. PN BUD(실온 30시간·냉장 9일)와 섞지 않도록 pending을 유지한다."),
    ("cnsc-nutrition-support-059", "BLOCKER: 정답 0.22 μm는 구 권고이다. 현행 단일 1.2 μm와 충돌하므로 인덱스를 바꾸지 않고 pending을 유지한다."),
    ("bcnsp-086", "BLOCKER: 정답 0.22 μm는 구 권고이다. 현행이면 1.2 μm라 답이 시대에 따라 바뀐다. pending을 유지한다."),
]


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
        for other in p.get("relatedAdd") or []:
            if other not in by:
                raise SystemExit(f"{p['id']}: related id {other} missing")
            q.setdefault("relatedIds", [])
            if other not in q["relatedIds"]:
                q["relatedIds"].append(other)
            by[other].setdefault("relatedIds", [])
            if p["id"] not in by[other]["relatedIds"]:
                by[other]["relatedIds"].append(p["id"])
            q["relatedIds"] = sorted(set(q["relatedIds"]))
            by[other]["relatedIds"] = sorted(set(by[other]["relatedIds"]))
    seen = set()
    for qid, note in BLOCKERS:
        if (qid, note) in seen:
            continue
        seen.add((qid, note))
        q = by.get(qid)
        if not q:
            raise SystemExit(f"blocker id missing: {qid}")
        if q.get("reviewStatus") == "verified" and qid not in {p["id"] for p in PROMOTIONS}:
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
