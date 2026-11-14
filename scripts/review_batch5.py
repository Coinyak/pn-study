#!/usr/bin/env python3
"""Batch 5 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes. Explain text is narrowed only where it attributed a number
or a rule the held page does not say.

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
CONTENT_VERSION = "2026-11-14.7"

GILA = "imsangyoungyang-gilajabi"
CCN = "ccn-summary-nestle-2022"
FACT = "aspen-adult-critically-ill-factsheet-2024"
MYTHS = "aspen-pn-myths-practice-tool-2024"

EVAL = "sec-eval-0-영양평가-PN-직결만"
IND = "sec-indications-1-적응증-시작시점-지연"
CHO = "sec-cho_gir-2-1-탄수화물-dextrose"
LIP = "sec-lipid-2-2-지방-ILE"
PROT = "sec-protein-2-3-단백질-아미노산-AA"
FLUID = "sec-fluid_lytes-2-4-수분"
LYTE = "sec-fluid_lytes-2-5-전해질"
TE = "sec-vit_te-2-7-미량원소-TE"
INF = "sec-complications-6-1-3열-요약"
PNALD = "sec-complications-6-3-간담도-합병증-PNALD"
STOP = "sec-monitor-7-3-PN-중단-이행"
LUNG = "sec-disease-8-1-폐-심장-신경계"
DIS = "sec-disease-8-질환별-PN"
DDI = "sec-disease-8-5-영양소-약물-상호작용"

Q_FLUID = "30–40 mL/kg/d"
Q_DEX = "≤7 g/kg/day"
Q_ILE = "≤2.5 g/kg"
Q_AA = "max 2.5 g/kg/d"
Q_AZO = "과도 AA"
Q_CLABSI = "CLABSI (가장 심각)"
Q_ENX = "확산형 복막염 · 심한 장폐색 · 장관 마비 · 난치성 구토·설사 · 심각한 GI 출혈"
Q_FIST = "위장관 누공"
Q_ENF = "EN 불가 누공"
Q_PANC = "EN 우선, 불가 시 PN"
Q_80 = "목표열량의 ≥80%"
Q_TAPER = "1–2 h"
Q_REB = "taper (rebound 방지)"
Q_7580 = "75–80%까지 PN 유지"
Q_STOP = "급중단 ⟶ rebound 저혈당"
Q_NPC = "동화 목적 NPC:N 120–180:1"
Q_EXCL = "NPC:N 계산엔 제외"
Q_150 = "무스트레스 150:1"
Q_STRESS = "스트레스 80~100:1"
Q_TOTN = "총열량:N 100–150:1"
Q_O2 = "흡기 O₂ · 호기 CO₂"
Q_IC = "IC 가능하면 IC 우선"
Q_STE = "지방증 = 과다 열량·포도당"
Q_GLU = "과도 포도당"
Q_PHEN = "phenytoin = EN 튜브 흡착"
Q_HOLD = "1–2 h EN 중지"
Q_IV = "IV 전환"
Q_WASH = "튜브 세척 = 물, 성인 최소 15 mL"
Q_NA = "장루·설사·위액 손실 시 Na↑"
Q_GI = "GI 손실"
Q_ZN = "과다 GI 손실"
Q_FISTZN = "누공 고배출"
Q_EH = "장간순환 문제"
Q_SBS = "장부전·SBS"
Q_ILEUM = "회장 소실"
Q_ORAL = "경구 자극"
Q_UDCA = "UDCA"
Q_CYC = "cyclic PN"
Q_MYTH = "a contraindication to Enteral Nutrition (EN) exists, inadequate EN tolerance is"
Q_BOWEL = "insufficient bowel function to maintain or restore nutrition"
Q_CCN = "Suggest indirect calorimetry (IC) be used to determine energy requirements when available and in the absence of variables that affect accuracy."
Q_12 = "12–25 kcal/kg/d"
Q_710 = "first 7-10 days of ICU stay"
Q_OVER = "Avoidance of energy overfeeding may be the most important decision to make regarding PN use."
Q_RESP = "respiratory acidosis or high serum triglyceride concentrations, consider whether feedings should be reduced"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치5 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "quizlet-iib-019",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [FLUID, CHO, LIP, PROT, INF],
        "explain": "3 L ÷ 50 kg = 60 mL/kg/일이다. 성인 수액은 30–40 mL/kg/일이다. 포도당 210 g은 4.2 g/kg/일로 하루 상한 7 g/kg/일 안이고, 지질 45 g은 0.9 g/kg/일로 하루 상한 2.5 g/kg 안이며, 아미노산 75 g은 1.5 g/kg/일로 상한 2.5 g/kg/일 안이다. 넘은 상한은 수분이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.4 성인 수액", Q_FLUID),
            ev(GILA, "PN_jjageuri_summary.md 2.1 하루 총량", Q_DEX),
            ev(GILA, "PN_jjageuri_summary.md 2.2 성인 용량", Q_ILE),
            ev(GILA, "PN_jjageuri_summary.md 2.3 상한", Q_AA),
            ev(GILA, "PN_jjageuri_summary.md 6.1 Azotemia", Q_AZO),
        ],
        "choiceExplanations": [
            "정답. 60 mL/kg/일은 성인 30–40 mL/kg/일을 넘는다.",
            "오답. 지질 0.9 g/kg/일은 하루 상한 2.5 g/kg 안이다.",
            "오답. 아미노산 1.5 g/kg/일은 상한 2.5 g/kg/일 안이다. 고질소혈증으로 적힌 것은 과도한 아미노산이다.",
            "오답. 포도당 4.2 g/kg/일은 하루 상한 7 g/kg/일 안이다.",
        ],
        "reviewNote": OK_NOTE + " 처방 숫자로 상한만 비교했다. 말초 혈전정맥염은 보기에 없다.",
    },
    {
        "id": "cnsc-nutrition-support-048",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [INF],
        "explain": "감염 합병증으로 적힌 것은 CLABSI이고, 가장 심각한 감염으로 적혀 있다. 공기색전·기흉·카테터 폐쇄는 그 감염 항목이 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 6.1 감염", Q_CLABSI)],
        "choiceExplanations": [
            "정답. 감염 합병증으로 이름이 있는 것은 CLABSI이고, 가장 심각하다고 적혀 있다.",
            "오답. 공기색전은 감염 항목이 아니다.",
            "오답. 기흉은 기계적 합병증이다.",
            "오답. 카테터 폐쇄는 기계적 합병증 쪽이다.",
        ],
        "reviewNote": OK_NOTE + " '가장 흔함'과 '카테터 제거의 주요 사유'는 그 문장에 없어 해설에서 뺐다.",
    },
    {
        "id": "quizlet-pn-015",
        "answer": 0,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [IND, DIS],
        "explain": "위장관을 쓸 수 없으면 PN을 본다. 위장관 누공과 EN이 불가한 누공이 그 적응이다. 크론병 자체는 적응이 아니고, 급성췌장염은 경장영양을 먼저 본다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 1 GI 흡수 불가", Q_FIST),
            ev(GILA, "PN_jjageuri_summary.md 8 Crohn", Q_ENF),
            ev(GILA, "PN_jjageuri_summary.md 8 급성췌장염", Q_PANC),
            ev(MYTHS, "ASPEN Myths 2024 p.1", Q_MYTH),
        ],
        "choiceExplanations": [
            "정답. 위장관 누공, 그중 EN이 불가한 누공이 PN 적응으로 적혀 있다.",
            "오답. 크론병 자체의 일상 PN은 없고, 적응은 단장·지속 소장폐색·EN 불가 누공·고배출 장루이다.",
            "오답. 급성췌장염은 경장영양을 우선하고, 불가할 때 PN이다.",
            "오답. 임신오조는 이 적응 목록에 이름이 없다.",
        ],
        "reviewNote": OK_NOTE + " >500 mL/d는 문제은행이라 쓰지 않았다. E6의 개시 시점과는 다른 문항이라 정오 id는 떼었다.",
    },
    {
        "id": "allaccess-001",
        "answer": 1,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [IND, DIS],
        "explain": "EN이 금기이거나 장이 영양을 유지하지 못하면 PN이다. EN이 불가한 누공이 그 경우다. 섭취가 부족한 것, 혼수, 삼킴장애만으로는 그 금기 문장에 해당하지 않는다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 EN 금기", Q_ENX),
            ev(GILA, "PN_jjageuri_summary.md 8 Crohn", Q_ENF),
            ev(MYTHS, "ASPEN Myths 2024 p.1", Q_MYTH),
        ],
        "choiceExplanations": [
            "오답. 섭취 부족만으로 EN이 금기라고 적혀 있지 않다.",
            "정답. EN이 불가한 누공은 PN 쪽이다. 고유출 장피부 누공이 그 보기다.",
            "오답. 혼수가 EN 금기 목록에 없다.",
            "오답. 삼킴장애가 EN 금기 목록에 없다.",
        ],
        "reviewNote": OK_NOTE + " >500 mL/d는 쓰지 않았다. 금기 문장은 확산형 복막염·심한 장폐색·장관 마비·난치성 구토·설사·심각한 GI 출혈이다.",
    },
    {
        "id": "hoag-faq-001",
        "answer": 0,
        "referenceIds": [MYTHS, GILA],
        "coreSectionIds": [IND, EVAL],
        "explain": "EN이 금기이거나 내성이 없거나 장 기능이 영양을 유지·회복하지 못하면 PN을 쓴다. 경구 보충제, 위관 급식, 근육 주사는 그 문장이 아니다.",
        "evidence": [
            ev(MYTHS, "ASPEN Myths 2024 p.1", Q_MYTH),
            ev(MYTHS, "ASPEN Myths 2024 p.1", Q_BOWEL),
            ev(GILA, "PN_jjageuri_summary.md 0 EN 금기", Q_ENX),
        ],
        "choiceExplanations": [
            "정답. 장을 충분히 쓸 수 없을 때 정맥으로 영양을 공급하는 것이 그 적응 문장이다.",
            "오답. 경구 보충제는 정맥영양이 아니다.",
            "오답. 위로 넣는 관급식은 경장영양이다.",
            "오답. 근육 주사 비타민은 정맥영양이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 해설의 '7–10일 치료 후 이득'은 Myths의 개시 시점과 달라 뺐다. E6 개시 시점 문항이 아니라 정오 id는 떼었다.",
    },
    {
        "id": "hoag-faq-002",
        "answer": 0,
        "referenceIds": [GILA, MYTHS],
        "coreSectionIds": [IND, EVAL, DIS],
        "explain": "PN은 EN이 금기이거나 장 기능이 부족할 때다. 보유 금기는 확산형 복막염, 심한 장폐색, 장관 마비, 난치성 구토·설사, 심각한 위장관 출혈이다. 누공과 단장도 장을 쓸 수 없는 쪽에 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 EN 금기", Q_ENX),
            ev(GILA, "PN_jjageuri_summary.md 1 GI 흡수 불가", Q_FIST),
            ev(GILA, "PN_jjageuri_summary.md 8 SBS", Q_SBS),
            ev(MYTHS, "ASPEN Myths 2024 p.1", Q_BOWEL),
        ],
        "choiceExplanations": [
            "정답. 장폐색·장마비·출혈·누공·단장처럼 장을 쓸 수 없는 경우가 PN을 고려하는 쪽이다.",
            "오답. 먹지 않으려는 모든 입원 환자가 적응은 아니다.",
            "오답. 다른 위험이 없는 경미한 변비는 금기 목록에 없다.",
            "오답. 경구로 요구량을 채우면 PN 적응이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 보기의 '감염'은 보유 단어가 아니고, 감염 쪽에 가까운 보유 단어는 확산형 복막염이다. >500 mL/d는 쓰지 않았다.",
    },
    {
        "id": "nbnsc-cnsc-sample-07",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [STOP, INF],
        "explain": "성인은 경구·경장으로 목표열량의 80% 이상을 공급할 수 있으면 PN 중단을 고려하고, 끊기 전에 1–2시간 감속한다. 소아는 75–80%가 될 때까지 PN을 유지한다. 급중단은 반동 저혈당이다. 경장 내성이 생기기 전에 PN을 일부 남기는 보기가 그 이행이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 7.3 성인 중단", Q_80),
            ev(GILA, "PN_jjageuri_summary.md 7.3 감량", Q_TAPER),
            ev(GILA, "PN_jjageuri_summary.md 7.3 감량", Q_REB),
            ev(GILA, "PN_jjageuri_summary.md 9 이행", Q_7580),
            ev(GILA, "PN_jjageuri_summary.md 9 이행", Q_STOP),
        ],
        "choiceExplanations": [
            "오답. 이행의 기본이 말초 포도당 주입으로 적혀 있지 않다. 10% 포도당은 이미 급중단한 뒤의 조치이다.",
            "오답. 설사가 나면 전환을 그만둔다는 문장은 없다.",
            "정답. 목표에 못 미치면 PN을 유지한다. 성인 기준은 목표열량 80% 이상, 소아는 75–80%이고, 중단은 1–2시간 감속이다.",
            "오답. 요구량이 채워지자마자 중심정맥관을 빼라는 문장은 없다. 급중단은 반동 저혈당이다.",
        ],
        "reviewNote": OK_NOTE + " 보기는 '내성'이고 보유 기준은 목표열량 비율이다. 60–75%는 초안에서 뺀 숫자라 쓰지 않았다.",
    },
    {
        "id": "quizlet-nsr-015",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [STOP],
        "explain": "경구 또는 경장으로 목표열량의 80% 이상을 공급할 수 있으면 PN 중단을 고려하고, 1–2시간 감속한다. 맑은 유동식 처방이나 목표 속도의 25%는 그 기준에 못 미친다. 일반식을 견디지 못하는 것도 공급이 된 상태가 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 7.3 성인 중단", Q_80),
            ev(GILA, "PN_jjageuri_summary.md 7.3 감량", Q_TAPER),
            ev(GILA, "PN_jjageuri_summary.md 9 이행", Q_STOP),
        ],
        "choiceExplanations": [
            "오답. 맑은 유동식 처방이 목표열량 80%는 아니다.",
            "오답. 목표 속도의 25%는 80%에 못 미친다.",
            "정답. 입으로 충분히 먹는 보기가, 경구로 목표열량을 채운 뒤에 중단한다는 문장에 가깝다. 중단은 1–2시간 감속이다.",
            "오답. 일반식을 견디지 못하면 목표 공급이 된 것이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 보유 문장은 경구 또는 경장으로 80% 이상이다. 보기는 고형식만 말한다. 25%와 유동식은 그 기준 밖이다.",
    },
    {
        "id": "cnsc-nutrition-support-036",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT],
        "explain": "NPC:N은 동화 목적의 비다. 단백 열량은 총열량에는 넣고 NPC:N에서는 빼서, 포도당과 지질이 에너지를 담당하게 한다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.3 NPC:N", Q_NPC),
            ev(GILA, "PN_jjageuri_summary.md 4.1 단백 kcal", Q_EXCL),
        ],
        "choiceExplanations": [
            "정답. 비단백 열량으로 에너지를 대어 아미노산을 동화에 쓰게 하는 비가 NPC:N이다.",
            "오답. 단백을 에너지로 쓰게 하려고 이 비를 두지 않는다. 단백 열량은 NPC:N에서 뺀다.",
            "오답. 지질을 최소화하라는 비가 아니다.",
            "오답. 포도당을 최대화하라는 비가 아니다.",
        ],
        "reviewNote": OK_NOTE + " 무스트레스 150:1, 스트레스 80–100:1, 동화 목적 120–180:1.",
    },
    {
        "id": "bcnsp-057",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT],
        "explain": "무스트레스 NPC:N은 150:1이고 스트레스는 80–100:1이다. 총열량 대 질소는 100–150:1이다. 중환자가 아닌 표준으로 100–150:1이 그 총열량 칸이고, 150:1도 그 안에 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.3 NPC:N", Q_150),
            ev(GILA, "PN_jjageuri_summary.md 2.3 NPC:N", Q_STRESS),
            ev(GILA, "PN_jjageuri_summary.md 2.3 NPC:N", Q_TOTN),
        ],
        "choiceExplanations": [
            "오답. 50:1은 무스트레스 150:1도, 총열량:N 100–150:1도 아니다.",
            "정답. 총열량:N은 100–150:1이다. 무스트레스 NPC:N 150:1은 그 범위에 들어간다.",
            "오답. 200:1은 총열량:N 100–150:1 밖이다. 소아는 150–250:1로 따로 적혀 있다.",
            "오답. 300:1은 보유 비 밖이다.",
        ],
        "reviewNote": OK_NOTE + " 문항은 '열량-질소'이고 보유 문장은 총열량:N 100–150:1과 무스트레스 NPC:N 150:1을 구분한다. 문제은행의 대략 100–150:1은 인용하지 않았다.",
    },
    {
        "id": "cnsc-nutrition-support-090",
        "answer": 1,
        "referenceIds": [GILA, FACT],
        "coreSectionIds": [PNALD, INF, LUNG],
        "explain": "과다 열량·포도당은 지방증과 간효소 상승으로 이어진다. 고혈당의 원인에도 과도 포도당이 있다. 호흡성 산증이나 높은 중성지방이면 공급량 감량을 검토한다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증", Q_STE),
            ev(GILA, "PN_jjageuri_summary.md 6.1 고혈당 원인", Q_GLU),
            ev(FACT, "ASPEN Critically Ill Factsheet 2024 Question 1", Q_RESP),
        ],
        "choiceExplanations": [
            "오답. 체중 감소와 저혈당은 과다 공급의 방향이 아니다.",
            "정답. 혈당 상승, CO2·호흡 부담, 간효소 상승이 과다 열량·포도당과 호흡성 산증 문장에 해당한다.",
            "오답. 과다 공급에서 중성지방이 감소한다고 적혀 있지 않다. 높은 중성지방이면 감량을 검토한다.",
            "오답. 저체온이 과다 공급의 소견으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 체액 과부하는 재급식 칸의 수분 저류이고, 과다 공급 문장으로 닫지 않았다. 정답 보기의 혈당·CO2·간효소가 보유 방향이다.",
    },
    {
        "id": "cnsc-nutrition-support-100",
        "answer": 1,
        "referenceIds": [FACT, GILA],
        "coreSectionIds": [LUNG, PNALD],
        "explain": "PN에서 에너지 과급식을 피하는 것이 가장 중요한 결정일 수 있다. 호흡성 산증이나 높은 중성지방이면 공급량 감량을 검토한다. 탄수화물 과다는 CO2 생성을 올리지만, 먼저 보는 것은 총 열량 과다이다.",
        "evidence": [
            ev(FACT, "ASPEN Critically Ill Factsheet 2024 Question 3", Q_OVER),
            ev(FACT, "ASPEN Critically Ill Factsheet 2024 Question 1", Q_RESP),
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증", Q_STE),
        ],
        "choiceExplanations": [
            "오답. 열량을 올리려고 탄수화물을 매우 높이는 것은 과급식을 피하는 문장과 반대다.",
            "정답. 에너지 과급식을 피하는 것이 PN에서 가장 중요한 결정으로 적혀 있다. 호흡성 산증이면 공급량을 줄일지를 본다.",
            "오답. 지방을 모두 빼라는 문장은 없다.",
            "오답. CO2 정체에서 단백을 심하게 제한하라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " Factsheet는 탄수화물 비율보다 총열량이 크다고 숫자로 비교하지는 않는다. '과급식을 피하는 것이 가장 중요할 수 있다'는 문장으로 닫았다.",
    },
    {
        "id": "quizlet-iib-002",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD, DIS],
        "explain": "회장 소실은 담즙산의 장간 순환을 끊는다. 장간 순환 문제는 PN 관련 간 합병증의 위험으로 적혀 있다. 주기 주입, 경구 자극, UDCA는 그 관리이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8 SBS", Q_SBS),
            ev(GILA, "PN_jjageuri_summary.md 8 회장", Q_ILEUM),
            ev(GILA, "PN_jjageuri_summary.md 9 PNALD 위험", Q_EH),
            ev(GILA, "PN_jjageuri_summary.md 9 PNALD 치료", Q_CYC),
            ev(GILA, "PN_jjageuri_summary.md 9 PNALD 치료", Q_ORAL),
            ev(GILA, "PN_jjageuri_summary.md 9 PNALD 치료", Q_UDCA),
        ],
        "choiceExplanations": [
            "정답. 단장, 그중 회장 소실은 담즙산 장간 순환을 끊고, 그게 간 합병증 위험으로 적혀 있다.",
            "오답. 주기 주입은 간 합병증의 위험이 아니라 관리이다.",
            "오답. 경구·경장 자극은 관리이다. 위험이 아니다.",
            "오답. UDCA는 치료로 적혀 있다. 위험 요인이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 남은 소장 50 cm, 75% 절제는 보유 길이가 아니라 뺐다. 보유 길이는 공장만 1 m 이하 등이다.",
    },
    {
        "id": "bcnsp-071",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [DDI],
        "explain": "Phenytoin은 경장 튜브에 흡착되어 혈중 농도가 떨어진다. 투여 전후 1–2시간 경장을 멈추거나 정맥으로 바꾸고, 농도를 본다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_PHEN),
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_HOLD),
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_IV),
        ],
        "choiceExplanations": [
            "오답. Acetaminophen이 그 흡착 문장에 없다.",
            "정답. Phenytoin은 경장 튜브 흡착으로 혈중 농도가 떨어진다.",
            "오답. Metoprolol이 그 문장에 없다.",
            "오답. Famotidine이 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 칼슘 카제이네이트 결합이라는 기전 이름은 보유 문장에 없어 뺐다. 보유 문장은 튜브 흡착이다.",
    },
    {
        "id": "cnsc-nutrition-support-070",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [DDI],
        "explain": "Phenytoin은 경장 튜브에 흡착된다. 투여 전후 1–2시간 경장을 멈추거나 정맥으로 바꾼다. 공장 급식관으로 흡수 부위를 건너뛰면 흡수가 달라지는 약도 따로 보지만, 이름이 있는 약은 phenytoin이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_PHEN),
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_HOLD),
            ev(GILA, "PN_jjageuri_summary.md 8.5 phenytoin", Q_IV),
        ],
        "choiceExplanations": [
            "정답. 경장과 함께 문제가 된다고 이름이 있는 약은 phenytoin이다. 흡착되면 농도가 떨어지고, 정맥 전환이 선택이다.",
            "오답. Acetaminophen이 그 문장에 없다.",
            "오답. Famotidine이 그 문장에 없다.",
            "오답. Lactulose가 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 위·근위 소장 흡수를 phenytoin에만 묶는 문장은 없다. 공장관에서 흡수가 달라지는 약은 별도 칸이고, 약물 이름이 있는 상호작용은 phenytoin이다.",
    },
    {
        "id": "cnsc-nutrition-support-069",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [DDI],
        "explain": "튜브는 물로 씻는다. 성인은 최소 15 mL이다. 탄산음료로 일상 세척하라는 문장은 없다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 8.5 튜브 세척", Q_WASH)],
        "choiceExplanations": [
            "오답. 장용정을 부숴 넣으라는 세척 문장은 없다.",
            "오답. 모든 약물을 섞어 한 번에 주라는 문장은 없다.",
            "정답. 약물·급식 전후에 물로 씻는 것이 보유 세척이다. 성인 최소 15 mL.",
            "오답. 탄산음료로 일상 세척하라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " '가능하면 액상 약'은 보유 문장에 없다. 물 세척이 정답 보기를 고르는 문장이다.",
    },
    {
        "id": "nbnsc-cnsc-sample-06",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL],
        "explain": "간접열량측정은 들이쉬는 산소와 내쉬는 이산화탄소로 안정시 에너지 소비를 낸다. 지난 섭취량이나 체중 증가에 필요한 열량을 재는 검사가 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_O2),
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_IC),
        ],
        "choiceExplanations": [
            "오답. 기초대사율이라는 이름과, 산소·이산화탄소로 내는 안정시 에너지 소비는 같은 칸이 아니다.",
            "오답. 지난 24시간 섭취량은 간접열량측정이 재는 값이 아니다.",
            "정답. 들이쉬는 산소와 내쉬는 이산화탄소로 에너지 소비를 낸다.",
            "오답. 체중 증가에 필요한 열량을 재는 검사가 아니다.",
        ],
        "reviewNote": OK_NOTE + " 요약의 측정값은 흡기 산소·호기 이산화탄소이고, 산출은 REE이다.",
    },
    {
        "id": "cnsc-nutrition-support-027",
        "answer": 3,
        "referenceIds": [GILA, CCN],
        "coreSectionIds": [EVAL],
        "explain": "간접열량측정이 가능하고 정확도를 흔드는 변수가 없으면 그것으로 에너지 요구를 정한다. 없으면 예측식이나 체중 식을 쓴다. Harris-Benedict나 체중×활동계수가 그 우선 문장은 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_IC),
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_O2),
            ev(CCN, "CCN Summary 2022 Calories", Q_CCN),
        ],
        "choiceExplanations": [
            "오답. Harris-Benedict는 IC가 없을 때의 예측식 쪽이다. 우선 문장은 IC이다.",
            "오답. 이중표지수분법이 임상 에너지 소비의 우선 방법으로 적혀 있지 않다.",
            "오답. 체중×활동계수는 IC가 없을 때의 추정이다.",
            "정답. 가능하면 간접열량측정으로 에너지 요구를 정한다.",
        ],
        "reviewNote": OK_NOTE + " 'gold standard'라는 단어는 보유 문장에 없다. 문장은 IC가 가능하면 IC를 쓴다는 것이다.",
    },
    {
        "id": "bcnsp-026",
        "answer": 1,
        "referenceIds": [GILA, CCN],
        "coreSectionIds": [EVAL],
        "explain": "간접열량측정은 그 환자의 산소 소비와 이산화탄소 생성으로 안정시 에너지 소비를 낸다. 예측식은 IC가 없을 때 쓴다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_O2),
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_IC),
            ev(CCN, "CCN Summary 2022 Calories", Q_CCN),
        ],
        "choiceExplanations": [
            "오답. 비용이 적고 더 쉽다는 문장은 없다.",
            "정답. 그 환자의 가스 교환으로 안정시 에너지 소비를 측정한다.",
            "오답. 높은 FiO2에서도 제한 없이 쓴다는 문장은 없다. CCN은 정확도를 흔드는 변수가 없을 때를 말한다.",
            "오답. 다량영양소 비율을 권한다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 개인 대사 변이라는 표현은 가스 교환으로 그 환자의 REE를 낸다는 문장으로 좁혔다.",
    },
    {
        "id": "medex-016",
        "answer": 1,
        "referenceIds": [CCN, GILA],
        "coreSectionIds": [EVAL, LUNG],
        "explain": "가능하고 정확도를 흔드는 변수가 없으면 간접열량측정으로 에너지 요구를 정한다. 없으면 예측식 또는 중환자 첫 7–10일의 12–25 kcal/kg이다. 이미 들어간 PN 열량을 측정값으로 보지 않는다.",
        "evidence": [
            ev(CCN, "CCN Summary 2022 Calories", Q_CCN),
            ev(CCN, "CCN Summary 2022 Calories", Q_12),
            ev(CCN, "CCN Summary 2022 Calories", Q_710),
            ev(GILA, "PN_jjageuri_summary.md 0 간접열량측정", Q_IC),
        ],
        "choiceExplanations": [
            "오답. PN이 이미 처방되었다고 IC가 불필요해지지는 않는다. IC가 없으면 12–25 kcal/kg는 첫 7–10일의 체중 식이다.",
            "정답. 가능하면 간접열량측정을 쓴다. 승압제가 변동하는 환자에서는 정확도를 흔드는 변수가 있는지도 같이 본다.",
            "오답. 처방된 비단백 열량은 측정된 안정시 에너지 소비가 아니다.",
            "오답. IC가 없을 때 예측식을 쓰더라도, 체중이 그대로면 재평가를 피하라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 화상 전용 Curreri 식은 없다. 12–25 kcal/kg는 BMI 30 미만 중환자의 IC가 없을 때, 첫 7–10일이다.",
    },
    {
        "id": "cnsc-nutrition-support-060",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [LYTE, TE, FLUID],
        "explain": "위장관 손실은 요구량을 올린다. 장루·설사·위액 손실이면 나트륨을 늘린다. 과다 위장관 손실과 누공 고배출은 아연 보충 대상이다. 나트륨을 제한하거나 인을 빼는 방향이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.5 요구 증가", Q_GI),
            ev(GILA, "PN_jjageuri_summary.md 2.5 나트륨", Q_NA),
            ev(GILA, "PN_jjageuri_summary.md 2.7 아연", Q_ZN),
            ev(GILA, "PN_jjageuri_summary.md 2.7 아연", Q_FISTZN),
        ],
        "choiceExplanations": [
            "오답. 장루·설사·위액 손실이면 나트륨을 늘린다. 고나트륨으로 제한하는 방향이 아니다.",
            "오답. 고인산혈증으로 인산염을 빼라는 문장은 이 손실 칸에 없다.",
            "정답. 위장관 손실은 요구량을 올리고, 이름이 있는 보충은 나트륨과 아연이다.",
            "오답. 요구량이 변하지 않는다는 문장과 반대다.",
        ],
        "reviewNote": OK_NOTE + " 칼륨·마그네슘을 고배액 손실의 이름으로 적는 문장은 없다. 같은 요구 증가 칸의 재급식이 K·P·Mg이다. 보충을 늘리는 보기는 이 하나다.",
    },
]

BLOCKERS = [
    (
        "quizlet-pn-032",
        "BLOCKER 배치5: 핵심표 2.2에 구조지질(Structolipid) 행이 있으나, 형광 전사·교재 추출·요약에는 그 문장이 없다. 문제은행 해설은 '연구용뿐'이고 핵심표 행은 '미국 연구용 / EU 시판'이라 한 문장으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-028",
        "BLOCKER 배치5: 성인 중단 기준은 목표열량 80% 이상이고, 소아는 75–80%까지 PN을 유지한다. 정답 보기의 60–75%는 요약 초안에서 불확실로 뺀 숫자이다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-041",
        "BLOCKER 배치5: 경장과 겹치면 과다 공급·고혈당이 될 수 있고, 급중단이면 반동 저혈당이다. 전환 때 어느 쪽이 더 생기기 쉬운지 가리는 문장이 없다. 해설의 4 mg/kg/min은 고혈당 위험 GIR이지 전환 규칙이 아니다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-052",
        "BLOCKER 배치5: 주사 알루미늄 5 μg/kg/일은 요약에서 문제은행 표기이다. 셀레늄 상한 5 μg/kg/일은 다른 칸이다. 유리병 글루콘산칼슘의 알루미늄은 ESPEN이고 하루 상한 숫자가 아니다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-056",
        "BLOCKER 배치5: Curreri 공식은 보유 문장에 없다. 화상 스트레스계수는 2.1–2.5이고, IC가 가능하면 IC를 쓴다. 'Curreri 또는 IC'를 한 정답으로 닫지 않는다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-093",
        "BLOCKER 배치5: 간경화·간성뇌증 단백은 표4-5에서 1.0–1.5이고, 만성 간질환에서 결핍이 없으면 1.0–1.2이다. 정답 보기의 1.2–1.5만으로 닫지 않는다. 난치 뇌증의 BCAA 이득은 근거가 낮다는 서술과 갈린다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-055",
        "BLOCKER 배치5: PN에 넣는 인슐린은 regular insulin뿐이다. 직전 24시간 교정량의 얼마를 넣는지, 슬라이딩 스케일 전량과 어떻게 다른지는 OCR이 불확실한 용량이라 닫지 않는다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-015",
        "BLOCKER 배치5: 고혈당이면 GIR을 낮추고 PN에는 regular insulin을 섞는다고 적혀 있다. 처음부터 별도 insulin 점적을 추가한다는 정답은, 혈당 300 초과의 펌프 분리라는 불확실 문장에 기대야 한다. 인덱스는 유지한다.",
    ),
    (
        "rx-biliary-sludge",
        "BLOCKER 배치5: 담낭 슬러지는 장 자극이 없을 때 생긴다고 적혀 있다. '거의 100%'는 보유 문장에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-010",
        "BLOCKER 배치5: 반동 저혈당의 보유 문장은 과도 인슐린, 급중단, 중단 전 1–2시간 감속, 급중단 시 10% 포도당, 50% 포도당이다. 영양불량·간질환·신부전을 위험으로, 고혈압을 예외로 닫는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-3_3-2",
        "BLOCKER 배치5: 지방증은 PN 2주 내로 적혀 있다. 담즙정체가 조기 합병증이 아니라는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-3_1-4",
        "BLOCKER 배치5: 성인 열량은 일반 20–35, 중환자 25–30, 안정 30–35 kcal/kg이다. 28–30이라는 칸은 없다. 인덱스는 유지한다.",
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
        "fact": NOTES / "06_학습_노트/_gl_extract/ASPEN_Fact_full.txt",
        "myths": NOTES / "06_학습_노트/_gl_extract/ASPEN_Myths_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_FLUID: "sum", Q_DEX: "sum", Q_ILE: "sum", Q_AA: "sum", Q_AZO: "sum",
        Q_CLABSI: "sum", Q_ENX: "sum", Q_FIST: "sum", Q_ENF: "sum", Q_PANC: "sum",
        Q_80: "sum", Q_TAPER: "sum", Q_REB: "sum", Q_7580: "sum", Q_STOP: "sum",
        Q_NPC: "sum", Q_EXCL: "sum", Q_150: "sum", Q_STRESS: "sum", Q_TOTN: "sum",
        Q_O2: "sum", Q_IC: "sum", Q_STE: "sum", Q_GLU: "sum", Q_PHEN: "sum",
        Q_HOLD: "sum", Q_IV: "sum", Q_WASH: "sum", Q_NA: "sum", Q_GI: "sum",
        Q_ZN: "sum", Q_FISTZN: "sum", Q_EH: "sum", Q_SBS: "sum", Q_ILEUM: "sum",
        Q_ORAL: "sum", Q_UDCA: "sum", Q_CYC: "sum",
        Q_MYTH: "myths", Q_BOWEL: "myths",
        Q_CCN: "ccn", Q_12: "ccn", Q_710: "ccn",
        Q_OVER: "fact", Q_RESP: "fact",
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
