#!/usr/bin/env python3
"""Batch 2 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes. Explain text is narrowed only where it attributed a number
the held page does not say.

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
CONTENT_VERSION = "2026-11-14.4"

MYTHS = "aspen-pn-myths-practice-tool-2024"
GILA = "imsangyoungyang-gilajabi"
COMPOUND = "aspen-pn-checklist-03-compounding-2024"

G21 = "sec-cho_gir-2-1-탄수화물-dextrose"
LIP = "sec-lipid-2-2-지방-ILE"
PROT = "sec-protein-2-3-단백질-아미노산-AA"
FL24 = "sec-fluid_lytes-2-4-수분"
FL25 = "sec-fluid_lytes-2-5-전해질"
EN = "sec-calc_filter-4-1-에너지"
CALC = "sec-calc_filter-4-2-계산-5단계-상한-체크"
S52 = "sec-stability-5-2-Ca-P-침전"
RS = "sec-complications-6-2-재급식-증후군-Refeeding"
PNALD = "sec-complications-6-3-간담도-합병증-PNALD"
MBD = "sec-complications-6-4-대사성-골질환-MBD"
EFAD = "sec-lipid-6-5-필수지방산-결핍-EFAD"
MON = "sec-monitor-7-1-PN-대사합병증-모니터-표11-1-TXT-p179"
STOP = "sec-monitor-7-3-PN-중단-이행"
IND = "sec-indications-1-적응증-시작시점-지연"
DZ = "sec-disease-8-질환별-PN"
TE = "sec-vit_te-2-7-미량원소-TE"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


Q_NA = "Patients may need more sodium in PN if they have high sodium losses from stoma, diarrhea, or gastric output."
Q_NA_STD = "ASPEN standard sodium dosing requirements for adults = 1–2 mEq/kg/day"
Q_CA_STD = "ASPEN standard calcium dosing requirements for adults = 10–15 mEq per day"
Q_SALT = "Calcium gluconate and calcium chloride are not interchangeable."
Q_SALT2 = "Calcium gluconate has a pH of 6.0 to 8.2 and dissociates less extensively in water than calcium chloride, rendering less free calcium ions to form calcium phosphate precipitates."
Q_EN = "a contraindication to Enteral Nutrition (EN) exists, inadequate EN tolerance is present"
Q_KCAL = "20% 2.0 kcal/mL"
Q_FAT10 = "3-in-1 계산 시 지방 10 kcal/g(대두유)"
Q_AA4 = "결정 AA 형태 · 4 kcal/g"
Q_N = "N = 단백(g) ÷ 6.25"
Q_FLUID = "Fluid 30–40 mL/kg"
Q_SOL_AA = "AA 농도↑ · cysteine 포함(산성화)"
Q_SOL = "Ca gluconate(CaCl₂보다 해리↓) · pH↓ · 온도↓"
Q_CAP = "Ca(mEq/L) + 2 × P(mmol/L) ≤ 45~60"
Q_RS_DEF = "영양불량 환자에 적극 영양 ⟶ 수분·전해질·비타민·미네랄(P·Mg·K·thiamine) 대사변화"
Q_RS_MARK = "저인산혈증(핵심) + ↓K · ↓Mg (+ thiamine 결핍)"
Q_RS_SLOW = "열량·수액은 천천히 시작·진행"
Q_RS_FIX = "PN 전 K·Mg·P 교정"
Q_RS15 = "위험군 15–20 kcal/kg"
Q_RISK = "알코올 중독 · 신경성 식욕부진 · 심한 영양결핍"
Q_CU = "담즙정체 → Cu·Mn↓"
Q_REBOUND = "급중단 ⟶ rebound"
Q_LA = "LA ~50% · ALA ~7% ⟶ EFAD 예방"
Q_EFAD = "LA 2–4% + ALA 0.25–0.5%"
Q_TG = "TG ≥400 ⟶ ILE 회피·감량·중단"
Q_ENFIRST = "EN 우선, 불가 시 PN"
Q_PROT = "high protein(Ca)"
Q_HPN = "단백 0.8~1 g/kg/d"
Q_BMP = "BMP+P+Mg: 안정 전 daily"
Q_GLU = "Capillary glucose: 개시 후 goal 도달까지 q6h"
Q_GI = "진행 손실(설사·누공·위장관 흡인)은 추가"
Q_GLUCOSE_PREF = "The preferred source of calcium when using inorganic phosphate salts"

# answer = current keyed index. The applier refuses to write a different index.
PROMOTIONS = [
    {
        "id": "cnsc-nutrition-support-024",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 지질 열량 [EXAM p144]", Q_KCAL)],
        "choiceExplanations": [
            "정답. 20% 정맥 지질유제는 2.0 kcal/mL이다.",
            "오답. 1.1 kcal/mL는 10% 지질유제이다.",
            "오답. 3.4 kcal/g는 정맥 포도당 계수이지 지질 mL 계수가 아니다.",
            "오답. 9 kcal/g는 순수 지방의 Atwater 계수이다. 20% 유제의 mL 계수가 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 20% ILE 2.0 kcal/mL.",
    },
    {
        "id": "cnsc-nutrition-support-030",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT, EN],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 아미노산 기본 [TXT p146]", Q_AA4)],
        "choiceExplanations": [
            "오답. 9 kcal/g는 지방 계수이다. 아미노산은 4 kcal/g이다.",
            "정답. 결정 아미노산은 4 kcal/g이다. 그 계수를 적은 보기가 이것이다.",
            "오답. 아미노산은 4 kcal/g의 열량을 낸다.",
            "오답. 3.4 kcal/g는 정맥 포도당 계수이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 AA 4 kcal/g. NPC 제외 문장은 문제은행 표기라 근거로 쓰지 않았다.",
    },
    {
        "id": "cnsc-nutrition-support-037",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_source_textbook_extract.md 아미노산 PDF146", "N 환산 6.25:1"),
                     ev(GILA, "PN_jjageuri_summary.md 아미노산 기본 [EXAM p061]", Q_N)],
        "choiceExplanations": [
            "오답. 4는 아미노산 kcal/g이다. 질소 환산 제수가 아니다.",
            "오답. 9는 순수 지방 계수이다.",
            "정답. 단백 g을 6.25로 나누면 질소 g이다.",
            "오답. 3.4는 정맥 포도당 kcal/g이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 N = 단백 ÷ 6.25.",
    },
    {
        "id": "bcnsp-017",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [G21, PROT, LIP, CALC],
        "errataIds": ["E3-dextrose-factor"],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 형태·열량 [TXT p143]", "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본"),
                     ev(GILA, "아미노산 기본", Q_AA4),
                     ev(GILA, "지질 열량 [EXAM p144]", Q_FAT10)],
        "choiceExplanations": [
            "오답. 1,690 kcal는 포도당을 3.4로 두지 않거나 지방 500 kcal가 빠진 쪽에 가깝다.",
            "정답. 포도당 350×3.4=1,190, 아미노산 100×4=400, 지방 50×10=500. 합은 2,090 kcal.",
            "오답. 2,190 kcal는 이 계수 합과 100 kcal가 다르다.",
            "오답. 2,500 kcal는 포도당을 4 kcal/g에 가깝게 둔 값이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. E3와 같은 3.4. 지방은 교재 3-in-1 10 kcal/g.",
    },
    {
        "id": "cnsc-nutrition-support-029",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [G21, PROT, LIP, CALC],
        "errataIds": ["E3-dextrose-factor"],
        "explain": "포도당 250×3.4=850 kcal, 아미노산 100×4=400 kcal, 3-in-1 지방은 10 kcal/g라 50 g는 500 kcal이다. 합은 1,750 kcal이고, 보기 중 가장 가까운 대략값은 1,700 kcal이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 형태·열량 [TXT p143]", "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본"),
                     ev(GILA, "아미노산 기본", Q_AA4),
                     ev(GILA, "지질 열량 [EXAM p144]", Q_FAT10)],
        "choiceExplanations": [
            "오답. 1,400 kcal는 아미노산 400 kcal가 빠진 쪽에 가깝다.",
            "오답. 2,400 kcal는 이 계수 합보다 크다.",
            "오답. 2,000 kcal는 1,750보다 멀다.",
            "정답. 3.4·4·10 kcal/g로 합하면 1,750 kcal이다. 대략값으로 가장 가까운 보기는 1,700 kcal이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 해설의 지방 9 kcal/g는 교재 3-in-1 10 kcal/g로 좁혔다. 1,750에 가장 가까운 보기가 1,700이다.",
    },
    {
        "id": "cnsc-nutrition-support-025",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [FL24],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_source_textbook_extract.md PDF166", Q_FLUID)],
        "choiceExplanations": [
            "정답. 교재의 성인 유지 수액은 30–40 mL/kg/일이다.",
            "오답. 10–15 mL/kg/일은 그 범위보다 낮다.",
            "오답. 60–70 mL/kg/일은 그 범위보다 높다.",
            "오답. 100 mL/kg/일은 10 kg 이하 소아의 Holliday-Segar 값이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 PDF166 성인 수액 30–40 mL/kg.",
    },
    {
        "id": "bcnsp-054",
        "answer": 1,
        "referenceIds": [MYTHS],
        "coreSectionIds": [FL25],
        "errataIds": [],
        "explain": "장루로 나트륨 손실이 크면 PN의 나트륨을 더 준다. 성인 표준은 1–2 mEq/kg/일이다. 칼슘·철·인은 그 문장이 지목하는 손실 전해질이 아니다.",
        "evidence": [ev(MYTHS, "p.2 hyponatremia 항목", Q_NA),
                     ev(MYTHS, "p.2 같은 항목", Q_NA_STD)],
        "choiceExplanations": [
            "오답. 장루 손실로 더 준다고 적힌 전해질은 칼슘이 아니다.",
            "정답. 장루·설사·위액으로 나트륨 손실이 크면 PN 나트륨을 더 준다. 성인 표준량은 1–2 mEq/kg/일이다.",
            "오답. 철은 그 문장의 손실 성분이 아니다.",
            "오답. 인도 그 문장에서 장루 손실로 더 주는 전해질로 적히지 않는다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 해설의 장루액 100–140 mEq/L는 보유 문장에 없어 뺐다.",
    },
    {
        "id": "quizlet-iib-024",
        "answer": 1,
        "referenceIds": [MYTHS, GILA],
        "coreSectionIds": [FL25, FL24],
        "errataIds": [],
        "explain": "회장루 손실이 크면 나트륨을 더 주고, 이미 빠진 수액과 진행 중인 장루 손실도 보충한다. 단백 제한이나 수분 제한은 그 문장이 아니다.",
        "evidence": [ev(MYTHS, "p.2 hyponatremia 항목", Q_NA),
                     ev(MYTHS, "p.2 같은 항목", Q_NA_STD),
                     ev(GILA, "PN_jjageuri_summary.md 성인 수분 [TXT p152]", Q_GI)],
        "choiceExplanations": [
            "오답. 나트륨을 늘리는 점은 맞지만, 단백 제한은 장루 나트륨 손실의 조치가 아니다.",
            "정답. 장루 손실에는 나트륨을 더 주고, 진행 중인 장루 수액 손실도 보충한다.",
            "오답. 수액만 늘리고 나트륨을 그대로 두면 장루 나트륨 손실을 메우지 못한다.",
            "오답. 나트륨은 늘리되 수분을 제한하면, 진행 중인 장루 손실을 보충하라는 문장과 어긋난다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 해설의 회장루액 100 mEq/L는 보유 문장에 없어 뺐다. 성인 Na 표준 1–2 mEq/kg/일.",
    },
    {
        "id": "cnsc-nutrition-support-046",
        "answer": 2,
        "referenceIds": [GILA, MYTHS, COMPOUND],
        "coreSectionIds": [S52],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 5.2 용해도↑ [EXAM p153]", Q_SOL_AA),
                     ev(GILA, "같은 행 [TXT p153]", Q_SOL),
                     ev(GILA, "같은 표 용해도 식 [EXAM p153]", Q_CAP),
                     ev(MYTHS, "p.4 calcium salts 항목", Q_SALT),
                     ev(COMPOUND, "p.2 mixing sequence, calcium gluconate", Q_GLUCOSE_PREF)],
        "choiceExplanations": [
            "오답. pH가 낮을수록 용해도가 오른다. pH를 낮추는 것은 침전 위험을 높이지 않는다.",
            "오답. 아미노산 농도가 높을수록 용해도가 오른다.",
            "정답. 온도가 낮을수록 용해도가 오르므로 온도가 오르면 침전이 늘고, Ca + 2×P가 45–60을 넘으면 농도 한도를 넘는다. 글루콘산칼슘과 염화칼슘은 서로 바꾸지 못한다.",
            "오답. 시스테인을 넣으면 산성화되어 용해도가 오른다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 용해도 방향과 Ca+2P 한도. 칼슘 염 비교환은 Myths p.4.",
    },
    {
        "id": "nbnsc-cnsc-sample-09",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK),
                     ev(GILA, "재급식 정의 [TXT p185]", Q_RS_DEF)],
        "choiceExplanations": [
            "오답. 재급식에서 칼륨은 오르는 쪽이 아니다.",
            "오답. 저혈당이 재급식의 핵심 대사 결과로 적히지 않는다.",
            "오답. 마그네슘은 오르는 쪽이 아니다.",
            "정답. 재급식의 핵심 표지는 저인산혈증이고, 칼륨·마그네슘도 같이 떨어진다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 재급식 표지 저인산혈증.",
    },
    {
        "id": "cnsc-nutrition-support-081",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK)],
        "choiceExplanations": [
            "정답. 재급식의 특징적 검사실 소견은 저인산혈증이다.",
            "오답. 인산은 오르는 쪽이 아니다.",
            "오답. 고나트륨혈증이 그 표지가 아니다. 재급식은 수분 저류 쪽이다.",
            "오답. 칼륨은 오르는 쪽이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 재급식 표지.",
    },
    {
        "id": "quizlet-iib-027",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK),
                     ev(GILA, "재급식 정의 [TXT p185]", Q_RS_DEF)],
        "choiceExplanations": [
            "오답. 인산이 오르는 조합은 표지와 반대이다.",
            "오답. 칼륨과 인산이 모두 오르는 조합은 표지와 반대이다.",
            "오답. 마그네슘이 오르는 조합은 표지와 반대이다.",
            "정답. 재급식에서 같이 떨어지는 전해질은 칼륨, 인산, 마그네슘이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 ↓K·저인산·↓Mg.",
    },
    {
        "id": "rxk-3_3-7",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "재급식에서 떨어지는 쪽으로 적힌 것은 인·마그네슘·칼륨이다. 나트륨은 그 목록에 없고, 수분 저류·체액 과부하로 적힌다.",
        "evidence": [ev(GILA, "재급식 정의 [TXT p185]", Q_RS_DEF),
                     ev(GILA, "재급식 표지", "신경근·심혈관·호흡 증상, 체액과부하·부종")],
        "choiceExplanations": [
            "오답. 칼륨은 재급식에서 떨어지는 전해질이다.",
            "정답. 나트륨은 P·Mg·K 목록에 없다. 재급식은 체액 과부하 쪽이다.",
            "오답. 마그네슘은 떨어지는 전해질이다.",
            "오답. 인은 떨어지는 전해질이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 나트륨은 감소 목록에 없음.",
    },
    {
        "id": "quizlet-iib-018",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "재급식 표지는 저인산·저칼륨·저마그네슘에서 오는 신경근·심혈관·호흡 증상이고, 수분 쪽은 체액 과부하와 부종이다. 탈수는 그 양상이 아니다.",
        "evidence": [ev(GILA, "재급식 표지", "신경근·심혈관·호흡 증상, 체액과부하·부종"),
                     ev(GILA, "재급식 표지", Q_RS_MARK)],
        "choiceExplanations": [
            "오답. 호흡 증상은 재급식 표지에 있다.",
            "오답. 근력 약화는 신경근 증상에 해당한다.",
            "오답. 부정맥은 심혈관 증상에 해당한다.",
            "정답. 재급식의 수분 양상은 체액 과부하·부종이지 탈수가 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 체액과부하가 탈수와 반대.",
    },
    {
        "id": "bcnsp-011",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "교재 PDF209의 재급식 위험군 시작 열량은 15–20 kcal/kg이고, 열량과 수액은 천천히 올린다. 그 값이 들어가는 보기는 10–20 kcal/kg이다. 전량, 첫날 30–35, 5 kcal를 14일 끄는 보기는 그 범위가 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 시작열량 [TXT p209]", Q_RS15),
                     ev(GILA, "재급식 원칙 [EXAM p185]", Q_RS_SLOW)],
        "choiceExplanations": [
            "오답. 추정 열량을 첫날 전량 주면 천천히 시작하라는 문장과 어긋난다.",
            "정답. 교재의 위험군 시작은 15–20 kcal/kg이다. 보기 가운데 그 값이 들어 있는 것은 10–20 kcal/kg이다.",
            "오답. 첫날 30–35 kcal/kg는 위험군 시작 15–20보다 높다.",
            "오답. 5 kcal/kg를 14일 끄는 값은 교재 15–20이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 보유 쪽수는 15–20 kcal/kg(PDF209)이고 10–20 보기에 들어간다. ASPEN 2020 원문은 인용하지 않았다. 해설의 25–50%·3–5일 귀속은 뺐다.",
    },
    {
        "id": "cnsc-nutrition-support-083",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "위험군은 15–20 kcal/kg에서 열량을 천천히 올리고, 인·칼륨·마그네슘을 보정하며 티아민을 준다. 그 내용이 들어 있는 보기는 열량을 줄여 시작하는 쪽이다. ASPEN 2020 원문은 인용하지 않는다.",
        "evidence": [ev(GILA, "시작열량 [TXT p209]", Q_RS15),
                     ev(GILA, "재급식 원칙 [EXAM p185]", Q_RS_SLOW),
                     ev(GILA, "재급식 정의 [TXT p185]", Q_RS_DEF)],
        "choiceExplanations": [
            "오답. 목표 열량을 처음부터 전량 주면 천천히 시작하라는 문장과 어긋난다.",
            "오답. 탄수화물 없이 단백만 주는 방식이 교재 시작 원칙이 아니다.",
            "오답. 영양을 7일간 전부 보류하라는 문장은 없다.",
            "정답. 15–20 kcal/kg는 열량을 줄여 시작하는 보기에 들어간다. 전해질 보정과 티아민도 재급식 정의에 있다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 10–20·목표 25%는 문제은행 표기라 근거로 쓰지 않았다. 15–20이 그 보기를 고른다.",
    },
    {
        "id": "rxk-2_3-5",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 원칙 [EXAM p185]", Q_RS_SLOW),
                     ev(GILA, "같은 행 [TXT p186]", Q_RS_FIX)],
        "choiceExplanations": [
            "오답. 맞는 말이지만 이것만은 아니다. 전해질 교정과 과다 공급을 피하는 것도 같은 원칙이다.",
            "오답. 맞는 말이지만 이것만은 아니다.",
            "오답. 맞는 말이지만 이것만은 아니다. 천천히 시작하는 것이 과다 공급을 피하는 쪽이다.",
            "정답. 열량은 천천히 올리고, 영양 전에 칼륨·마그네슘·인을 교정한다. 세 가지가 모두 그 원칙이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 재급식 원칙.",
    },
    {
        "id": "medex-004",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [RS, MON],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK),
                     ev(GILA, "재급식 원칙 [EXAM p185]", Q_RS_SLOW)],
        "choiceExplanations": [
            "오답. 인슐린을 더 올리면 인·칼륨·마그네슘이 세포 안으로 더 이동할 수 있다. 재급식 표지의 조치가 아니다.",
            "오답. 칼륨 염만 바꾸고 포도당 증량을 유지하면, 떨어진 인과 마그네슘을 그대로 둔 채 열량을 올린다.",
            "정답. 포도당을 올린 뒤 인·칼륨·마그네슘이 같이 떨어졌다. 열량 증량을 멈추고 그 전해질을 보충한다.",
            "오답. 세 전해질이 같이 떨어진 것을 희석으로 보고 처방을 유지하지 않는다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 재급식 표지 P·K·Mg와 열량 천천히.",
    },
    {
        "id": "cnsc-nutrition-support-086",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "explain": "시작 이틀째 인 1.2 mg/dL는 교재 정상 3.0–4.5보다 낮다. 재급식의 핵심 표지는 저인산혈증이므로 열량 증량을 멈추고 인을 보충한다.",
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK),
                     ev(GILA, "PN_jjageuri_summary.md 혈청 정상 [EXAM+ p078]", "P 3.0–4.5 mg/dL"),
                     ev(GILA, "재급식 원칙", Q_RS_SLOW)],
        "choiceExplanations": [
            "정답. 저인산이면 열량 증량을 보류하고 인을 보충한다.",
            "오답. 목표 열량으로 더 빨리 올리면 천천히 진행하라는 문장과 어긋난다.",
            "오답. 전해질 감시를 끊지 않는다. 안정 전에는 매일 본다.",
            "오답. 인을 올리려고 포도당을 더 넣으면 인을 더 떨어뜨리는 쪽이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 인 1.2 mg/dL는 교재 정상 3.0–4.5 아래.",
    },
    {
        "id": "medex-009",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [RS, MON],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 표지", Q_RS_MARK),
                     ev(GILA, "혈청 정상 [EXAM+ p078]", "P 3.0–4.5 mg/dL"),
                     ev(GILA, "재급식 원칙", Q_RS_SLOW)],
        "choiceExplanations": [
            "오답. 인 1.4 mg/dL는 정상 3.0–4.5 아래이다. 현재 인 용량을 유지한 채 포도당을 더 올리지 않는다.",
            "정답. 낮은 인이 있으면 포도당 증량을 보류하고 인을 더 보충한 뒤 열량을 다시 본다.",
            "오답. 저칼륨이 동반되어 있는데 칼륨 인을 나트륨 인으로 바꾸면 칼륨 보충이 빠진다.",
            "오답. 인 용량만 백 안에서 올리고 중심정맥이 필요 없는지를 묻는 보기는, 증량 보류와 재평가가 먼저인 이 상황의 답이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 인 1.4 mg/dL는 저인산. 열량 증량 보류.",
    },
    {
        "id": "cnsc-nutrition-support-087",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [MON, RS],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_source_textbook_extract.md PDF179", Q_BMP),
                     ev(GILA, "같은 쪽", Q_GLU)],
        "choiceExplanations": [
            "오답. 안정 전 기본 대사 패널은 주 1회가 아니라 매일이다.",
            "오답. 미량원소를 매달 보는 것은 시작 직후의 감시가 아니다.",
            "정답. 안정 전에는 인·칼륨·마그네슘이 포함된 검사를 매일 하고, 혈당은 목표에 닿기까지 6시간마다 본다.",
            "오답. 간효소를 1년에 한 번 보는 것은 시작 직후의 감시가 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 PDF179 BMP+P+Mg 매일, 혈당 q6h.",
    },
    {
        "id": "cnsc-nutrition-support-084",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [RS],
        "errataIds": [],
        "evidence": [ev(GILA, "재급식 고위험 [TXT p185]", Q_RISK)],
        "choiceExplanations": [
            "정답. 신경성 식욕부진과 심한 영양결핍이 교재의 재급식 고위험이다.",
            "오답. 영양이 양호하고 금식 하루인 환자는 그 고위험 목록이 아니다.",
            "오답. 먹고 있는 안정 당뇨 환자는 그 목록이 아니다.",
            "오답. 규칙적으로 식사하는 과체중 환자는 그 목록이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 PDF185 고위험: 알코올·식욕부진·심한 영양결핍.",
    },
    {
        "id": "quizlet-pn-033",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [TE, PNALD],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_source_textbook_extract.md 미량원소", Q_CU),
                     ev(GILA, "PN_exam_highlights_all.md PDF185", "간담도계 질환 → 망간·구리 감량")],
        "choiceExplanations": [
            "오답. 셀레늄은 담즙정체에서 감량하는 쌍이 아니다. 신부전에서 제한하는 쪽에 가깝다.",
            "오답. 구리와 셀레늄이 아니라 구리와 망간이다.",
            "오답. 아연은 설사에서 늘리고, 크롬은 담즙정체 감량 쌍이 아니다.",
            "정답. 간담도·담즙정체에서는 구리와 망간을 감량한다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 담즙정체 Cu·Mn 감량, PDF185.",
    },
    {
        "id": "bcnsp-035",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [STOP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 대사-저혈당 [TXT p181]", Q_REBOUND),
                     ev(GILA, "PN_source_textbook_extract.md PDF181", "저혈당·반동: 감속 1–2h 또는 속도 절반")],
        "choiceExplanations": [
            "오답. 고농도 포도당을 갑자기 끊을 때의 위험은 고혈당이 아니다.",
            "정답. 급중단은 반동 저혈당이다. 끊기 전 1–2시간에 걸쳐 감속한다.",
            "오답. 대사성 알칼리증이 그 위험이 아니다.",
            "오답. 고나트륨혈증이 그 위험이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 PDF181 급중단 반동 저혈당.",
    },
    {
        "id": "quizlet-pn-030",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [EFAD, LIP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md EFAD 예방 %kcal [TXT p167]", "LA 2–4% + ALA 0.25–0.5%")],
        "choiceExplanations": [
            "오답. 리놀레산·알파리놀렌산 결핍의 이름으로 적힌 것은 대사성 산증이 아니다.",
            "오답. 고혈당이 그 결핍의 이름이 아니다.",
            "오답. 대사성 골질환이 그 결핍의 이름이 아니다.",
            "정답. 총열량의 리놀레산 2–4%와 알파리놀렌산 0.25–0.5%를 주지 않으면 필수지방산 결핍이다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 EFAD 예방 LA 2–4%, ALA 0.25–0.5%.",
    },
    {
        "id": "bcnsp-005",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP, EFAD],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 대두유 [EXAM p044]", Q_LA)],
        "choiceExplanations": [
            "오답. EPA·DHA 공급이 대두유의 필수지방산 예방 기전으로 적히지 않는다.",
            "정답. 대두유는 리놀레산이 많아 필수지방산 결핍을 예방한다.",
            "오답. 올레산이 그 예방 기전으로 적히지 않는다.",
            "오답. 중쇄중성지방은 필수 지방산이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 대두유 LA로 EFAD 예방.",
    },
    {
        "id": "nbnsc-cnsc-sample-01",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP, MON],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 지질 감량·중단 [EXAM p181]", Q_TG)],
        "choiceExplanations": [
            "오답. 혈당은 포도당 감시이다. 지질유제 감시로 적힌 항목은 중성지방이다.",
            "오답. 암모니아가 지질유제 감시 항목으로 적히지 않는다.",
            "오답. 콜레스테롤이 아니라 중성지방이다.",
            "정답. 지질유제는 중성지방으로 본다. TG가 400 이상이면 감량·중단을 고려한다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 ILE는 TG로 감시, >400 감량·중단.",
    },
    {
        "id": "cnsc-nutrition-support-094",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [DZ],
        "errataIds": [],
        "explain": "급성췌장염은 경장영양을 우선하고, 경장이 불가능할 때 정맥영양을 쓴다. 위인지 공장이인지는 그 문장이 나누지 않는다. 경장을 고르는 보기가 맞다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 급성 췌장염 [TXT p218]", Q_ENFIRST)],
        "choiceExplanations": [
            "정답. 경장을 우선한다. 위 또는 공장으로 주는 보기가 경장이다.",
            "오답. 장을 쉬게 하려고 정맥영양만 쓰는 것은 EN 우선과 어긋난다.",
            "오답. 고지방 경구는 그 문장의 우선 경로가 아니다.",
            "오답. 증상이 끝날 때까지 영양을 주지 않는 것은 EN 우선이 아니다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 교재 췌장염 EN 우선. 24–48시간·공장관 한정은 보유 문장에 없어 해설에서 뺐다.",
    },
    {
        "id": "quizlet-iib-014",
        "answer": 3,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [MBD, FL25],
        "errataIds": [],
        "explain": "고단백은 소변 칼슘을 늘린다. 이 처방전 단백은 2 g/kg/day이고, 장기 가정정맥영양의 단백은 0.8–1 g/kg/day로 적혀 있다. 고용량 단백을 줄인다. 성인 칼슘 표준은 10–15 mEq/일이며, 글루콘산칼슘을 더 올리는 보기는 그 조정이 아니다.",
        "evidence": [ev(GILA, "PN_source_textbook_extract.md 전해질 요구↑ PDF147", Q_PROT),
                     ev(GILA, "PN_jjageuri_summary.md 표11-3 [EXAM p193]", "고용량 단백 피하기"),
                     ev(GILA, "장기 HPN 표19-9 [EXAM p286]", Q_HPN),
                     ev(MYTHS, "p.2 calcium 항목", Q_CA_STD)],
        "choiceExplanations": [
            "오답. 성인 칼슘 표준은 10–15 mEq/일이다. 고칼슘뇨에서 글루콘산칼슘을 더 올리는 것이 표11-3의 조정이 아니다.",
            "오답. 인 표준은 20–40 mmol/일이다. 인을 줄이는 것이 고용량 단백을 피하는 조정이 아니다.",
            "오답. 주입 시간을 10시간으로 줄이라는 문장은 없다.",
            "정답. 단백 2 g/kg/day는 장기 가정정맥영양 0.8–1 g/kg/day보다 높다. 고단백은 소변 칼슘을 늘리므로 아미노산을 줄인다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. 해설의 단백 1.5 g/kg 상한은 보유 문장에 없어 뺐다. 성인 Ca 10–15 mEq/일은 Myths.",
    },
    {
        "id": "quizlet-pn-016",
        "answer": 2,
        "referenceIds": [MYTHS],
        "coreSectionIds": [IND],
        "errataIds": [],
        "explain": "경장이 금기이거나 버티지 못하거나 장 기능이 부족할 때 정맥영양을 시작한다. 화상 면적이나 입원 직후라는 이유만으로 시작하지 않는다.",
        "evidence": [ev(MYTHS, "p.1–2 'PN is not indicated until NPO for 7 days' 항목", Q_EN)],
        "choiceExplanations": [
            "오답. 체표면적 20%를 넘는다는 이유만으로 PN을 시작하라는 문장은 없다.",
            "오답. 열량 요구가 높다고 입원 직후 PN을 시작하라는 문장은 없다.",
            "정답. 경장이 금기이거나 영양 요구를 채우지 못할 때 PN을 시작한다.",
            "오답. 7–10일 이내라는 기한만으로 시작을 정하지 않는다. 잘영양에서의 7일 대기는 조건이 따로 있다.",
        ],
        "reviewNote": "배치2 verified. 정답 인덱스 유지. E6의 조건 없는 7일이 아니라 EN 금기·불내성 문장. 사망률 연구 귀속은 해설에서 뺐다.",
    },
]

BLOCKERS = [
    ("bcnsp-043", "BLOCKER 배치2: 교재 계수(포도당 5 mOsm/g, 아미노산 10 mOsm/g)로 포도당·아미노산만 보면 약 1,050 mOsm/L이다. 850이 1,500보다 가깝다. 정답 인덱스는 유지하고 pending으로 둔다."),
    ("bcnsp-077", "BLOCKER 배치2: 교재 성인 수액은 30–40 mL/kg/일이다. 정답 보기 25–35와 숫자가 어긋난다. 인덱스는 유지한다."),
    ("bcnsp-021", "BLOCKER 배치2: 교재 티아민은 50–100 mg/일 × 5–7일이다. 정답 100–300 mg × 3일과 숫자가 다르다. ASPEN 2020 원문은 인용하지 않는다. 인덱스는 유지한다."),
    ("bcnsp-009", "BLOCKER 배치2: 알칼리증에서 염화를 늘리고 아세트산을 줄인다는 방향은 문제은행 표기이다. 교재 PDF174는 중탄산염 대신 acetate 1:1만 말한다. 인덱스는 유지한다."),
    ("medex-010", "BLOCKER 배치2: 산증에서 염화 일부를 acetate로 바꾼다는 방향은 문제은행 표기이다. 보유 쪽 문장은 중탄산염 대신 acetate 1:1이다. 인덱스는 유지한다."),
    ("quizlet-iib-020", "BLOCKER 배치2: 염화물:아세트산 비를 낮추는 방향은 문제은행 표기이다. 인덱스는 유지한다."),
    ("nbnsc-cnsc-sample-02", "BLOCKER 배치2: 난치성 설사에 acetate를 늘린다는 문장을 보유 쪽에서 확인하지 못했다. 인덱스는 유지한다."),
    ("nbnsc-cnsc-sample-08", "BLOCKER 배치2: 교재는 고용량 포도당의 요구 증가를 인에 연결한다. 칼륨과 인의 쌍을 그 문장만으로 닫지 못했다. 인덱스는 유지한다."),
    ("quizlet-pn-007", "BLOCKER 배치2: 철덱스트란이 TNA를 가장 불안정하게 한다는 문장은 문제은행 표기이다. 인덱스는 유지한다."),
    ("bcnsp-040", "BLOCKER 배치2: 교재는 급성췌장염에서 EN 우선만 말한다. 24–48시간 경비공장관은 그 문장에 없다. 인덱스는 유지한다."),
    ("bcnsp-044", "BLOCKER 배치2: '중증 성인이면 7일 후'는 조건이 없다. Myths는 영양위험 3–5일, 중등–중증 영양불량은 가능한 한 빨리, 잘영양·안정만 7일 대기이다. 인덱스는 유지한다."),
    ("cnsc-nutrition-support-103", "BLOCKER 배치2: 문항은 PN이 아닌 영양지원 일반의 5–7일이다. Myths의 7일은 잘영양·안정에서 PN을 기다릴 수 있다는 문장이다. 인덱스는 유지한다."),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "myths": NOTES / "06_학습_노트/_gl_extract/ASPEN_Myths_full.txt",
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "ext": NOTES / "06_학습_노트/PN_source_textbook_extract.md",
        "hi": NOTES / "06_학습_노트/PN_exam_highlights_all.md",
        "cmp": NOTES / "06_학습_노트/_gl_extract/ASPEN_Compound_full.txt",
        "core": CORE,
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    # phrase -> which blobs must contain it
    need = {
        Q_NA: "myths", Q_NA_STD: "myths", Q_CA_STD: "myths", Q_SALT: "myths",
        Q_SALT2: "myths", Q_EN: "myths", Q_GLUCOSE_PREF: "cmp",
        Q_KCAL: "sum", Q_FAT10: "sum", Q_AA4: "sum", Q_N: "sum",
        Q_SOL: "sum", Q_SOL_AA: "sum", Q_CAP: "sum", Q_RS_DEF: "sum", Q_RS_MARK: "sum",
        Q_RS_SLOW: "sum", Q_RS_FIX: "sum", Q_RS15: "sum", Q_RISK: "sum",
        Q_REBOUND: "sum", Q_LA: "sum", Q_ENFIRST: "sum", Q_HPN: "sum",
        Q_GI: "sum", "P 3.0–4.5 mg/dL": "sum", "고용량 단백 피하기": "sum",
        "일수화물(monohydrate) 3.4 kcal/g = IV 계산 기본": "sum",
        "LA 2–4% + ALA 0.25–0.5%": "sum",
        "신경근·심혈관·호흡 증상, 체액과부하·부종": "sum",
        Q_FLUID: "ext", Q_CU: "ext", Q_PROT: "ext", Q_BMP: "ext", Q_GLU: "ext",
        "N 환산 6.25:1": "ext",
        Q_TG: "sum",
        "저혈당·반동: 감속 1–2h 또는 속도 절반": "ext",
        "간담도계 질환 → 망간·구리 감량": "hi",
    }
    missing = []
    for phrase, key in need.items():
        if _norm(phrase) not in blob[key]:
            missing.append(f"{key}: {phrase}")
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
