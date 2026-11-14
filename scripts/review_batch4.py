#!/usr/bin/env python3
"""Batch 4 pending-review promotions.

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
CONTENT_VERSION = "2026-11-14.6"

GILA = "imsangyoungyang-gilajabi"
CCN = "ccn-summary-nestle-2022"
TEOL = "aspen-pn-trace-element-practice-tool-2024"
FACT = "aspen-adult-critically-ill-factsheet-2024"

IND = "sec-indications-1-적응증-시작시점-지연"
CHO = "sec-cho_gir-2-1-탄수화물-dextrose"
LIP = "sec-lipid-2-2-지방-ILE"
PROT = "sec-protein-2-3-단백질-아미노산-AA"
TE = "sec-vit_te-2-7-미량원소-TE"
R31 = "sec-route-3-1-말초-vs-중심"
E41 = "sec-calc_filter-4-1-에너지"
CALC = "sec-calc_filter-4-2-계산-5단계-상한-체크"
NA = "sec-calc_filter-4-4-교정-공식-EXAM-p155-여러-수치-주고-옳은-것-찾기-NOTE"
PNALD = "sec-complications-6-3-간담도-합병증-PNALD"
MBD = "sec-complications-6-4-대사성-골질환-MBD"
EFAD = "sec-lipid-6-5-필수지방산-결핍-EFAD"
MON = "sec-monitor-7-1-PN-대사합병증-모니터-표11-1-TXT-p179"
LUNG = "sec-disease-8-1-폐-심장-신경계"
OB = "sec-disease-8-2-당뇨-비만"
DIS = "sec-disease-8-질환별-PN"
HPN = "sec-hpn-10-재택-PN-HPN"

Q_CYC = "주기 12–18 h(간독성 예방·HPN)"
Q_NIGHT = "HPN 대부분 야간 10–12 h"
Q_SKIN = "피부염(기출) · 탈모"
Q_STE = "지방증 = 과다 열량·포도당"
Q_EX = "원인 = 과도 공급"
Q_ZN = "Zn 결핍 = 피부염·설사·상처치유 지연"
Q_TASTE = "미각변화"
Q_GI = "과다 GI 손실"
Q_FIST = "누공 고배출"
Q_MN = "복합제 함량 높아 독성"
Q_MULTI = "1 mL = Zn 3 mg + Cu 0.3 mg + Mn 55 μg + Se 60 μg"
Q_SER = "혈청 TE 농도 = 신뢰도 낮음"
Q_D10 = "포도당 5~10%"
Q_PICC = "독립성↓"
Q_TUN = "수개월–수 년 = 터널형 중심정맥"
Q_PORT = "implanted port = 활동↑ but 천자·감염·수술"
Q_SLUD = "sludge·담석 (장 자극 부재)"
Q_ORAL = "경구 자극"
Q_DEXA = "진단: DEXA"
Q_TG = "TG >1,000"
Q_PAN = "췌장염 유발"
Q_AA = "AKI/신부전 ⟶ 표준 AA"
Q_CKD = "비투석 0.6–0.8"
Q_DAY = "목표·안정 전 매일"
Q_G = "g/kg × 체중"
Q_ENF = "EN 불가 누공"
Q_LONG = "장기 PN 대부분"
Q_AL = "Al 최소화"
Q_7 = "≤7 g/kg/d"
Q_GLU = "과도 포도당"
Q_11 = "11–14 kcal/kg 실제체중"
Q_22 = "22–25 kcal/kg IBW"
Q_CU = "Cu 결핍 = 호중구감소·빈혈"
Q_SE = "Se 결핍 = 심근병증"
Q_20 = "성인 일반 20–35"
Q_25 = "중환자 25–30"
Q_NA = "고혈당 Na 교정"
Q_016 = "0.016"
Q_PHL = "말초 혈전정맥염 위험 → 중심정맥 권장"
Q_KCAL = "11–14 kcal/kg ABW*/day for BMI 30–50"
Q_IBW = "22–25 kcal/kg IBW**/day for"
Q_CAP = "not exceed 65–70% of target energy"
Q_EN = "early EN should be initiated in 24–48 hours"
Q_TR = "manganese 55 mcg, selenium 60 mcg"
Q_RESP = "respiratory acidosis or high serum triglyceride concentrations, consider whether feedings should be reduced"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치4 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "bcnsp-063",
        "answer": 1,
        "referenceIds": [CCN, GILA],
        "coreSectionIds": [OB, E41],
        "explain": "IC가 없으면 BMI 30–50은 11–14 kcal/kg 실제체중, BMI 50 초과는 22–25 kcal/kg IBW이다. 보기의 11–14 kcal/kg 실제체중은 BMI 30–50 수치이다. IC가 있으면 목표 에너지의 65–70%를 넘기지 않는다. CCN 요약은 이 열량을 EN 목표로 적는다.",
        "evidence": [
            ev(CCN, "CCN Summary 2022 Obesity", Q_KCAL),
            ev(CCN, "CCN Summary 2022 Obesity", Q_IBW),
            ev(CCN, "CCN Summary 2022 Obesity", Q_CAP),
            ev(GILA, "PN_jjageuri_summary.md 4.1 ICU", Q_11),
            ev(GILA, "PN_jjageuri_summary.md 4.1 ICU", Q_22),
        ],
        "choiceExplanations": [
            "오답. 30–35 kcal/kg 실제체중은 비만 중환자의 IC 없을 때 수치가 아니다.",
            "정답. BMI 30–50에서 IC가 없을 때의 11–14 kcal/kg 실제체중이다. BMI 50 초과는 22–25 kcal/kg IBW로 따로 적혀 있다.",
            "오답. BMI 50 초과의 IBW 수치는 22–25 kcal/kg이다. 40–45가 아니다.",
            "오답. IC가 있어도 목표 에너지의 65–70%를 넘기지 않는다. 보정 없이 전량을 주지 않는다.",
        ],
        "reviewNote": OK_NOTE + " stem의 BMI >30은 30–50과 >50이 갈린다. 11–14는 실제체중·BMI 30–50이고, 해설에 >50의 22–25 kcal/kg IBW를 남겼다. EN 목표 문장이다.",
    },
    {
        "id": "quizlet-pn-048",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN, PNALD],
        "explain": "주기 12–18시간 주입은 간독성 예방으로 적혀 있다. 간 기능이 나빠질 위험이 있는 환자가 그 대상이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p154]", Q_CYC),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", "과도 포도당 피하기 · cyclic PN"),
        ],
        "choiceExplanations": [
            "오답. 단기 PN이 주기 주입의 대상으로 적혀 있지 않다.",
            "정답. 주기 12–18시간은 간독성 예방이다. 간 기능 장애 위험이 그 문장에 해당한다.",
            "오답. 고혈당 위험 환자가 주기 주입의 권고 대상으로 적혀 있지 않다. 주기 주입은 혈당 변동을 따로 본다.",
            "오답. 침상 안정이 주기 주입의 대상은 아니다.",
        ],
        "reviewNote": OK_NOTE + " 간독성 예방 문장으로 닫았다. '장기 PN에서 선호'는 문제은행이라 쓰지 않았다. 간효소·빌리루빈이 낮아진다는 부가 문장은 뺐다.",
    },
    {
        "id": "rx-cyclic-pn-night",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN],
        "explain": "주기 주입의 시간은 12–18시간이고, HPN은 대부분 야간 10–12시간이다. 보기의 '주로 야간'이 그 야간 주입이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p210]", Q_NIGHT),
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p154]", Q_CYC),
        ],
        "choiceExplanations": [
            "오답. 중심정맥이 불가능할 때의 보조 방법이 주기 주입의 정의는 아니다.",
            "오답. 말초정맥으로만 준다는 문장은 없다.",
            "오답. 위루·공장루는 경장영양이다.",
            "정답. HPN은 대부분 야간 10–12시간이다. '주로 야간'이 그 주입이다.",
        ],
        "reviewNote": OK_NOTE + " 야간 10–12시간은 HPN. 주기 창 12–18시간은 간독성 예방 문장.",
    },
    {
        "id": "rxk-1_1-5",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN],
        "explain": "HPN의 주기 주입은 대부분 야간 10–12시간이다. 보유 문장은 '대부분'이고, 보기 중 야간 투여가 그 주입이다. 다른 보기는 경로가 다르다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p210]", Q_NIGHT),
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p154]", Q_CYC),
        ],
        "choiceExplanations": [
            "오답. 중심정맥이 불가능할 때의 보조가 주기 주입은 아니다.",
            "오답. 말초정맥 투여가 주기 주입의 정의는 아니다.",
            "오답. 위루·공장루는 경장영양이다.",
            "정답. HPN은 대부분 야간에 10–12시간 주입한다. 보기의 야간 투여가 그 문장이다.",
        ],
        "reviewNote": OK_NOTE + " 보유 문장은 '대부분 야간'이다. 보기는 '야간에만'이라 범위를 조금 좁히지만, 맞는 보기는 야간 주입뿐이다.",
    },
    {
        "id": "nbnsc-cnsc-sample-03",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [EFAD],
        "explain": "필수지방산 결핍의 증상은 피부염과 탈모이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 6.5 증상 [EXAM p182]", Q_SKIN)],
        "choiceExplanations": [
            "오답. 저인산혈증의 표지가 피부염·탈모로 적혀 있지 않다.",
            "오답. 마그네슘 결핍의 표지가 피부염·탈모는 아니다.",
            "오답. 비타민 A 결핍이 이 증상 쌍으로 적혀 있지 않다.",
            "정답. 필수지방산 결핍 증상은 피부염·탈모이다.",
        ],
        "reviewNote": OK_NOTE + " 교재 6.5 증상.",
    },
    {
        "id": "quizlet-iib-049",
        "answer": 1,
        "referenceIds": [GILA, FACT],
        "coreSectionIds": [PNALD, CHO, LUNG],
        "explain": "지방증은 과다 열량·과다 포도당과 연관된다. 과다 공급에서 문제가 되는 호흡 쪽은 이산화탄소가 늘어 호흡성 산증이 오는 쪽이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 기여인자 [TXT p188]", Q_STE),
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증 [TXT p186]", Q_EX),
            ev(FACT, "ASPEN Critically Ill Factsheet Q1 clinical application", Q_RESP),
        ],
        "choiceExplanations": [
            "오답. 탄수화물 과다가 고칼슘혈증으로 적혀 있지 않다.",
            "정답. 지방증의 기여 인자는 과다 열량·포도당이다.",
            "오답. 과다 공급의 호흡 문제는 이산화탄소가 줄어드는 쪽이 아니다. 호흡성 산증이 생기면 공급량 감량을 검토한다.",
            "오답. 대사성 골질환은 장기 PN의 뼈 문제이다. 탄수화물 과다의 간 쪽 결과는 지방증이다.",
        ],
        "reviewNote": OK_NOTE + " 지방증 = 과다 열량·포도당. CO2 감소 보기는 호흡성 산증 문장과 방향이 반대이다.",
    },
    {
        "id": "medex-012",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "explain": "아연 결핍은 피부염·설사·상처치유 지연이다. 과다 위장관 손실과 누공 고배출은 아연을 보충하는 대상이다. 고배출 장루의 지속 손실이 그 위장관 손실에 들어간다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.7 [TXT p273]", Q_ZN),
            ev(GILA, "PN_jjageuri_summary.md 2.7 [EXAM p093]", Q_GI),
            ev(GILA, "PN_jjageuri_summary.md 2.7 [EXAM p093]", Q_FIST),
            ev(GILA, "PN_jjageuri_summary.md 2.7", Q_SE),
            ev(GILA, "PN_jjageuri_summary.md 2.7", Q_CU),
        ],
        "choiceExplanations": [
            "정답. 지속되는 위장관 손실은 아연 보충 대상이고, 결핍 표지는 피부염과 상처치유 지연이다.",
            "오답. 셀레늄 결핍으로 적힌 표지는 심근병증이다. 입주위 피부염이 그 문장은 아니다.",
            "오답. 비타민 A 결핍을 이 피부염·창상 치유 표지로 적은 문장은 없다.",
            "오답. 구리 결핍은 호중구감소·빈혈이다. 피부염이 먼저 나타나는 결핍으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 12 mg/L 같은 추가 용량은 보유 문장에 없어 해설에 넣지 않았다. 입주위는 교재의 '피부염'으로 닫았다.",
    },
    {
        "id": "quizlet-home-ns-002",
        "answer": 2,
        "referenceIds": [GILA, TEOL],
        "coreSectionIds": [TE],
        "explain": "시판 복합 미량원소 예는 1 mL에 망간 55 μg가 들어 있다(Tralement도 망간 55 mcg). 복합제의 망간 함량이 높아 독성이 된다. 혈청 미량원소 농도는 신뢰도가 낮다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.7 시판 예", Q_MULTI),
            ev(TEOL, "ASPEN TE Practice Tool, Tralement", Q_TR),
            ev(GILA, "PN_jjageuri_summary.md 2.7 [TXT p273]", Q_MN),
            ev(GILA, "PN_jjageuri_summary.md 2.7 [TXT p185]", Q_SER),
        ],
        "choiceExplanations": [
            "오답. 장기 PN에서 적힌 망간 문제는 결핍이 아니라 복합제 함량으로 인한 독성이다.",
            "오답. 담즙정체에서는 망간을 감량한다. 독성이 담즙정체에서만 생긴다는 문장은 아니다. 복합제 함량 문장은 따로 있다.",
            "정답. 시판 복합 미량원소에 망간이 들어 있고, 그 함량이 높아 독성이 된다.",
            "오답. 혈청 미량원소 농도는 신뢰도가 낮다고 적혀 있다. 혈청 망간이 가장 잘 반영한다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 파킨슨양·가정 PN 50%·1.1 mg·전혈·MRI는 보유 문장에 없어 뺐다. 파킨슨양 문항은 올리지 않았다.",
    },
    {
        "id": "quizlet-home-ns-005",
        "answer": 0,
        "referenceIds": [GILA, TEOL],
        "coreSectionIds": [TE],
        "explain": "복합 미량원소의 망간 함량이 높아 독성이 된다. 시판 예는 망간 55 μg이다. 장기 PN에서 모니터링하지 않으면 문제가 되는 쪽으로 적힌 것은 이 망간이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.7 [TXT p273]", Q_MN),
            ev(GILA, "PN_jjageuri_summary.md 2.7 시판 예", Q_MULTI),
            ev(TEOL, "ASPEN TE Practice Tool, Tralement", Q_TR),
        ],
        "choiceExplanations": [
            "정답. 복합제 망간 함량이 높아 독성이 된다.",
            "오답. 아연은 결핍 표지와 고용량 때의 구리 결핍이 따로 적혀 있다. 복합제 함량 독성으로 지목된 원소는 망간이다.",
            "오답. 엽산이 장기 PN의 미량원소 독성으로 적혀 있지 않다.",
            "오답. 몰리브덴은 미국 성인 PN에 일상 첨가하지 않는 쪽으로 적혀 있다. 복합제 함량 독성의 원소는 망간이다.",
        ],
        "reviewNote": OK_NOTE + " 파킨슨양 증상은 문제은행이라 해설에 쓰지 않았다.",
    },
    {
        "id": "bcnsp-014",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [CHO, R31],
        "explain": "말초의 최종 포도당은 5–10%이다. 10%를 넘으면 말초 혈전정맥염 위험으로 중심정맥이 된다.",
        "evidence": [
            ev(GILA, "PN_source_textbook_extract.md PDF143", Q_PHL),
            ev(GILA, "PN_jjageuri_summary.md 3.1 농도", Q_D10),
        ],
        "choiceExplanations": [
            "오답. 5%는 말초 범위 안이지만 적힌 위쪽 끝은 10%이다.",
            "정답. 말초 최종 포도당은 5–10%이고, 10%를 넘으면 중심정맥이다.",
            "오답. 20%는 10%를 넘겨 말초 혈전정맥염 쪽으로 중심정맥이 된다.",
            "오답. 35%는 말초 최종 농도가 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 PDF143의 >10% 혈전정맥염. 해설의 중심 PN 20–70% 범위는 이 문항의 정답 근거가 아니라 뺐다.",
    },
    {
        "id": "quizlet-pn-022",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN],
        "explain": "PICC는 제거는 쉽지만 독립성이 떨어진다. 자가 관리가 제한되는 단점이 그 문장이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 10 접근로 [TXT p280]", Q_PICC)],
        "choiceExplanations": [
            "정답. PICC는 독립성이 떨어져 자가 관리가 제한된다.",
            "오답. 기흉 위험이 높다는 문장이 PICC 단점으로 적혀 있지 않다.",
            "오답. 반복 피부 천자는 이식형 포트 쪽이다. PICC 단점으로 적힌 것은 독립성 저하다.",
            "오답. 단일 내강만 가능하다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 교재의 독립성 저하. 위치 이상·폐색·기흉 없음 같은 부가 설명은 그 문장 밖이라 뺐다.",
    },
    {
        "id": "cnsc-nutrition-support-044",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN],
        "explain": "수개월에서 수년은 터널형 중심정맥관이다. 이식형 포트도 장기 접근으로 적혀 있다. PICC는 주로 3개월 미만이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 접근로 [EXAM p280]", Q_TUN),
            ev(GILA, "PN_jjageuri_summary.md 10 접근로 [TXT p280]", Q_PORT),
        ],
        "choiceExplanations": [
            "정답. 수개월–수년은 터널형이고, 이식형 포트도 장기 접근으로 적혀 있다.",
            "오답. 미드라인 카테터는 그 기간의 중심정맥 접근으로 적혀 있지 않다.",
            "오답. 말초 정맥 카테터로는 장기 중심 PN을 주지 않는다.",
            "오답. 단기 말초 캐뉼라는 수개월–수년 재택 PN의 접근이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 감염률이 낮다는 부가 문장은 보유 문장에 없어 뺐다.",
    },
    {
        "id": "quizlet-iib-015",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD],
        "explain": "담낭 슬러지·담석은 장 자극이 없을 때 생긴다. 관리에는 경구 자극이 들어 있다. 경구 또는 경장영양이 그 자극이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 담낭 [TXT p186]", Q_SLUD),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리 [TXT p273]", Q_ORAL),
        ],
        "choiceExplanations": [
            "오답. 콜린이 담석 예방으로 적혀 있지 않다.",
            "오답. CCK 옥타펩티드가 그 예방 문장은 아니다.",
            "오답. UDCA는 간담도 관리 목록에 있으나, 담낭 칸이 짚는 원인은 장 자극이 없는 것이다.",
            "정답. 장 자극이 없으면 슬러지·담석이 생기고, 경구 자극이 관리에 들어 있다.",
        ],
        "reviewNote": OK_NOTE + " CCK 성적과 우르소 6–15 mg/kg는 보유 문장에 없어 뺐다.",
    },
    {
        "id": "quizlet-iib-040",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [MBD],
        "explain": "대사성 골질환의 진단은 DEXA로 골밀도를 보는 것이다. T-score로 골다공증과 골감소를 나눈다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 6.4 진단 [TXT p191]", Q_DEXA)],
        "choiceExplanations": [
            "정답. DEXA로 골밀도를 측정한다.",
            "오답. 혈청 칼슘이 진단 방법으로 적혀 있지 않다.",
            "오답. 혈청 인산이 그 진단 방법은 아니다.",
            "오답. 부갑상선호르몬이 그 진단 방법은 아니다.",
        ],
        "reviewNote": OK_NOTE + " 코르티코스테로이드를 가장 큰 위험으로 적은 문장은 보유 목록에 없어 뺐다.",
    },
    {
        "id": "nbnsc-cnsc-sample-05",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "explain": "아연 결핍 표지에 미각 변화가 있다. 구리·셀레늄·크롬의 표지는 미각이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.7 [EXAM p093]", Q_TASTE),
            ev(GILA, "PN_jjageuri_summary.md 2.7", Q_CU),
            ev(GILA, "PN_jjageuri_summary.md 2.7", Q_SE),
            ev(GILA, "PN_jjageuri_summary.md 2.7 [EXAM p035]", "Cr 결핍 = 포도당불내성"),
        ],
        "choiceExplanations": [
            "정답. 아연 결핍에 미각 변화가 적혀 있다.",
            "오답. 구리 결핍은 호중구감소·빈혈이다.",
            "오답. 셀레늄 결핍은 심근병증이다.",
            "오답. 크롬 결핍은 포도당불내성·고혈당 쪽이다.",
        ],
        "reviewNote": OK_NOTE + " stem의 후각은 교재 문장에 없다. 미각 변화로 닫았다.",
    },
    {
        "id": "quizlet-iib-008",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP, DIS],
        "explain": "중성지방이 1,000 mg/dL를 넘으면 췌장염을 유발하는 수준으로 적혀 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.2 TG 컷 [TXT p182]", Q_TG),
            ev(GILA, "PN_jjageuri_summary.md 2.2 TG 컷", Q_PAN),
        ],
        "choiceExplanations": [
            "오답. 고질소혈증이 고중성지방의 합병증으로 적혀 있지 않다.",
            "정답. TG >1,000이 췌장염 유발 수준이다.",
            "오답. 다뇨가 그 합병증으로 적혀 있지 않다.",
            "오답. 말초신경병증이 그 합병증으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 폐기능 변화와 신생아 TG 200, Safe Practices 2004 인용은 보유 문장에 없어 뺐다. 감량 컷 400과 췌장염 컷 1,000은 다른 문장이다.",
    },
    {
        "id": "quizlet-pn-028",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT, DIS],
        "explain": "급성 신손상·신부전에서는 표준 아미노산 제제를 쓴다. 특수 필수아미노산 제제는 근거가 부족하다고 적혀 있다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 2.3 [EXAM p063·p227]", Q_AA)],
        "choiceExplanations": [
            "정답. AKI·신부전은 표준 아미노산이다.",
            "오답. 분지쇄 아미노산이 AKI의 제제로 적혀 있지 않다.",
            "오답. 필수아미노산 위주 특수 제제는 근거가 부족하다고 적혀 있다.",
            "오답. 신장 전용 제제로 바꾸라는 문장은 없다. 표준 제제이다.",
        ],
        "reviewNote": OK_NOTE + " 사망률 연구가 없다는 부가 문장은 보유 문장에 없어 뺐다.",
    },
    {
        "id": "bcnsp-034",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [DIS],
        "explain": "투석 전 만성콩팥병의 단백은 0.6–0.8 g/kg/일이다. 4기·투석 전이 그 구간이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 8 신부전 [EXAM p227]", Q_CKD)],
        "choiceExplanations": [
            "정답. 비투석 단백은 0.6–0.8 g/kg/일이다.",
            "오답. 1.5–2.0 g/kg/일은 투석 전 만성콩팥병 수치가 아니다.",
            "오답. 2.5 g/kg/일은 그 권고가 아니다.",
            "오답. 단백을 완전히 제한하지 않는다. 0.6–0.8 g/kg/일이다.",
        ],
        "reviewNote": OK_NOTE + " 해설의 투석 시작 후 1.0–1.2 g/kg는 교재의 HD·PD 1.2–1.3과 달라 뺐다. 이 문항은 투석 전만 묻는다.",
    },
    {
        "id": "rx-electrolyte-daily",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [MON],
        "explain": "PN을 시작하고 목표에 안정되기 전에는 BMP와 인·마그네슘을 매일 본다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 7.1 표11-1 [TXT p179]", Q_DAY)],
        "choiceExplanations": [
            "오답. 하루 3회가 전해질 모니터 빈도로 적혀 있지 않다.",
            "정답. 안정 전에는 매일이다.",
            "오답. 주 2–3회는 안정 전 빈도가 아니다. 안정 후는 주 1–2회이다.",
            "오답. 주 1회는 장기 PN 쪽이다. 급성기는 매일이다.",
        ],
        "reviewNote": OK_NOTE + " 표11-1. 안정 후 주 1–2회와 주 2–3회는 다른 문항에서 갈린다.",
    },
    {
        "id": "cnsc-nutrition-support-061",
        "answer": 0,
        "referenceIds": [CCN],
        "coreSectionIds": [IND],
        "explain": "스스로 섭취를 유지하지 못하는 환자에게 조기 경장영양은 24–48시간 이내에 시작한다.",
        "evidence": [ev(CCN, "CCN Summary 2022 Initiate EN", Q_EN)],
        "choiceExplanations": [
            "정답. 조기 경장영양은 24–48시간 이내이다.",
            "오답. 7일을 기다린 뒤가 그 시작 시점은 아니다.",
            "오답. 발관 후에만 시작한다는 문장은 없다.",
            "오답. 정맥영양을 시작한 뒤가 경장영양의 시작 조건은 아니다.",
        ],
        "reviewNote": OK_NOTE + " CCN 요약의 24–48시간. 감염 합병증이 적다는 부가 결과는 그 문장에 없어 뺐다.",
    },
    {
        "id": "bcnsp-090",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [CALC, PROT],
        "explain": "아미노산 그램은 g/kg에 체중을 곱한다. 1.5 g/kg × 60 kg = 90 g이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 4.2 AA 부피", Q_G)],
        "choiceExplanations": [
            "오답. 60 g는 1 g/kg × 60 kg이다. 처방은 1.5 g/kg이다.",
            "정답. 1.5 × 60 = 90 g이다.",
            "오답. 120 g는 2 g/kg × 60 kg이다.",
            "오답. 150 g는 2.5 g/kg × 60 kg이다. 처방 단백은 1.5 g/kg이다.",
        ],
        "reviewNote": OK_NOTE + " stem의 1.5 g/kg와 60 kg만 곱했다. 열량 1,500 kcal 배분은 묻지 않아 해설에서 뺐다.",
    },
    {
        "id": "quizlet-iib-030",
        "answer": 3,
        "referenceIds": [FACT, GILA],
        "coreSectionIds": [LUNG, E41],
        "explain": "경장 또는 정맥영양 중에 호흡성 산증이 생기면 공급량을 줄일지를 본다. 2,800 kcal ÷ 63 kg는 약 44 kcal/kg로, 중환자 25–30과 성인 일반 20–35보다 높다. stem의 낮은 pH와 높은 PaCO2가 그 호흡성 산증이다.",
        "evidence": [
            ev(FACT, "ASPEN Critically Ill Factsheet Q1 clinical application", Q_RESP),
            ev(GILA, "PN_jjageuri_summary.md 4.1 kcal/kg", Q_25),
            ev(GILA, "PN_jjageuri_summary.md 4.1 kcal/kg", Q_20),
        ],
        "choiceExplanations": [
            "오답. 호흡성 산증이 있으면 공급량을 그대로 두지 않고 감량을 검토한다.",
            "오답. 염화물:아세트산 비율을 올리는 것이 이 호흡성 산증의 문장은 아니다.",
            "오답. 염화물:아세트산 비율을 내리는 것이 그 문장은 아니다.",
            "정답. 호흡성 산증이 있으면 영양 공급량 감량을 검토한다.",
        ],
        "reviewNote": OK_NOTE + " 약 44 kcal/kg는 stem의 2,800÷63이다. 새 권고 숫자를 만들지 않았다.",
    },
    {
        "id": "quizlet-iib-047",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [CHO],
        "explain": "포도당 일일 상한은 7 g/kg 이하이다. 400 g ÷ 45 kg는 약 8.9 g/kg로 그 상한을 넘는다. 과도한 포도당은 고혈당의 원인으로 적혀 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.1 일일 상한", Q_7),
            ev(GILA, "PN_jjageuri_summary.md 6.1 고혈당 원인 [EXAM p035]", Q_GLU),
        ],
        "choiceExplanations": [
            "오답. 지방 25 g가 고중성지방의 상한을 넘는 근거로 이 문항에서 쓰이지 않는다. 상한을 넘는 것은 포도당이다.",
            "오답. 단백 70 g가 질소혈증을 가리키는 상한 초과로 적히지 않는다. 넘는 것은 포도당 7 g/kg이다.",
            "정답. 약 8.9 g/kg는 7 g/kg를 넘고, 과도한 포도당은 고혈당의 원인이다.",
            "오답. 폐부종이 이 포도당 상한의 결과로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 8.9 g/kg는 400÷45이다. 해설의 단백 상한 2 g/kg는 교재 2.5와 달라 뺐다.",
    },
    {
        "id": "quizlet-iib-005",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [NA],
        "explain": "고혈당에서는 측정 나트륨이 낮게 보이므로, 측정값에 0.016×(포도당−100)을 더해 보정한다. 그 방향이 고장성 저나트륨혈증이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 4.4 고혈당 Na", Q_NA),
            ev(GILA, "PN_jjageuri_summary.md 4.4 Katz", Q_016),
        ],
        "choiceExplanations": [
            "정답. 고혈당 보정은 측정 나트륨에 더하는 식이다. 측정 나트륨이 낮게 보이는 고장성 저나트륨혈증이다.",
            "오답. 저장성 저나트륨혈증이 고혈당 보정 식의 유형으로 적혀 있지 않다.",
            "오답. 고나트륨혈증이 아니다. 보정은 낮게 측정된 나트륨에 더한다.",
            "오답. 고장성 고나트륨혈증이 고혈당 나트륨 보정의 방향은 아니다.",
        ],
        "reviewNote": OK_NOTE + " 해설의 1.6 mEq/100 mg/dL는 Katz 0.016이다. 0.024와 간이 +2도 표에 있어 0.016만 요인으로 적었다.",
    },
    {
        "id": "quizlet-iib-001",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [MBD, TE],
        "explain": "대사성 골질환 조정에는 알루미늄을 최소화하는 항목이 있다. 보기 가운데 그 목록에 걸리는 것은 알루미늄 독성이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 6.4 표11-3 [EXAM p193]", Q_AL)],
        "choiceExplanations": [
            "정답. 조정 목록은 알루미늄을 최소화하라고 한다.",
            "오답. 칼슘 보충이 골질환의 기여 요인으로 적혀 있지 않다. 위험 쪽은 칼슘 부족이다.",
            "오답. 적정량의 아미노산이 기여 요인은 아니다. 위험 쪽은 고단백이다.",
            "오답. 균형 잡힌 아세트산 부하가 기여 요인은 아니다. 위험 쪽은 대사성 산증이다.",
        ],
        "reviewNote": OK_NOTE + " '가장 크게'의 순위는 교재에 없다. 보기 중 조정 목록에 있는 것은 알루미늄뿐이다. 인덱스는 유지한다.",
    },
    {
        "id": "bcnsp-013",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [IND, DIS],
        "explain": "경장영양이 불가능한 누공은 PN 적응으로 적혀 있다. 위장관을 쓸 수 없는 고배출 장피부 누공이 그 상황이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 8 Crohn [TXT p211]", Q_ENF)],
        "choiceExplanations": [
            "오답. 선택 수술 후 2일 NPO는 그 적응이 아니다.",
            "정답. 경장영양이 불가능한 누공이 PN 적응이다. 비기능 위장관의 고배출 누공이 그 보기이다.",
            "오답. 경구로 열량의 60%를 섭취하는 환자는 그 적응이 아니다.",
            "오답. 약으로 조절되는 경증 위마비는 그 적응이 아니다.",
        ],
        "reviewNote": OK_NOTE + " >500 mL/d는 문제은행 표기라 인용하지 않았다. 닫은 문장은 EN 불가 누공이다.",
    },
    {
        "id": "quizlet-iib-016",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [MBD, HPN],
        "explain": "대사성 골질환의 위험은 장기 PN이다. 단기 합병증으로 적힌 항목이 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 6.4 위험 [TXT p191]", Q_LONG)],
        "choiceExplanations": [
            "오답. 탈수가 장기 골질환 문장의 대상은 아니다. 단기에서 빼는 항목으로 적힌 것은 골질환이다.",
            "정답. 대사성 골질환은 장기 PN의 위험이다. 단기 합병증이 아니다.",
            "오답. 재급식 증후군은 영양을 시작하는 때의 문제이다.",
            "오답. 카테터 위치 이상은 삽입 때의 문제이다. 장기 골질환이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 장기 PN 위험. Siepler 2007 인용은 보유 문헌이 아니라 뺐다.",
    },
]


BLOCKERS = [
    ("cnsc-nutrition-support-050", "BLOCKER 배치4: ESPEN HPN R48은 주기 주입을 끝낼 때 속도를 낮춰 반동 저혈당을 피한다(예: 마지막 30분 절반 속도). 정답 보기는 시작 시 고혈당까지 포함한다. 요약의 시작·끝 1시간은 p155로 되어 있으나 p155 전사는 교정 칼슘·나트륨이다. 인덱스는 유지한다."),
    ("rxk-3_2-6", "BLOCKER 배치4: '장기 PN에서 선호'는 문제은행 표기이다. 보유 문장은 주기 12–18시간의 간독성 예방과 HPN 야간 주입이다. 선호로 닫지 않는다. 인덱스는 유지한다."),
    ("bcnsp-094", "BLOCKER 배치4: 안정 전에는 매일이다. 안정 후 표11-1은 주 1–2회이고, 정답 보기는 주 2–3회이다. 인덱스는 유지한다."),
    ("quizlet-pn-029", "BLOCKER 배치4: 형광은 만성 뇌증 stage II 이상에서 BCAA를 인정하고, 교재 서술은 간성뇌증의 BCAA에 일관된 근거가 낮다고 한다. '표준 단백 불내성'은 문제은행 표기이다. 한 문장으로 닫지 않는다. 인덱스는 유지한다."),
    ("rxk-4_1-7", "BLOCKER 배치4: 국내 종합비타민에는 비타민 K가 없고, 성인 MVI 표는 비타민 K 150 μg를 포함한다. 문항이 국내 제품인지 표인지 가리지 않는다. 인덱스는 유지한다."),
    ("cnsc-nutrition-support-021", "BLOCKER 배치4: 25–30 kcal/kg는 중환자 칸이다. stem은 중증이 아닌 입원 성인이고, 그 칸은 성인 일반 20–35·안정 30–35이다. 인덱스는 유지한다."),
    ("bcnsp-091", "BLOCKER 배치4: 24–48시간은 섭취를 유지하지 못하는 중환자의 조기 경장영양이다. stem은 중증 TBI 지침을 묻고 해설은 Brain Trauma Foundation을 인용하는데 그 원문은 없다. 인덱스는 유지한다."),
    ("cnsc-nutrition-support-091", "BLOCKER 배치4: 교재 구표기의 CRRT 상한은 2.0–2.5 g/kg이고, 핵심표의 기본 암기는 ESPEN 신장 CRRT 1.5–1.7이다. '흔히 2.0–2.5'로 한 숫자에 닫지 않는다. 인덱스는 유지한다."),
    ("quizlet-pn-034", "BLOCKER 배치4: 유리병 글루콘산칼슘의 알루미늄은 ESPEN R8.6이다. 인산염을 주요 오염원으로 묶는 문장은 ≤5 μg/kg와 함께 문제은행 표기이다. 지질이 아니라는 배제는 그 문장으로 닫지 않는다. 인덱스는 유지한다."),
    ("quizlet-iib-009", "BLOCKER 배치4: 고혈당 원인으로 적힌 것은 과도 포도당·스트레스·크롬 결핍·인슐린 부족이다. 간경변·비만·췌장염이 그 목록에 없어 '아닌 것'이 갑상선기능저하 하나로 닫히지 않는다. 인덱스는 유지한다."),
    ("quizlet-iib-017", "BLOCKER 배치4: 산증에서 acetate를 올리고 염소를 내리는 방향은 문제은행 표기이다. 교재가 확정한 것은 중탄산염 대신 acetate 1:1이다. 아세트산 과다가 중탄산염을 올린다는 보기는 그 방향 표기에 기대므로 올리지 않는다. 인덱스는 유지한다."),
    ("quizlet-iib-035", "BLOCKER 배치4: 지방증과 고혈당은 과다 공급 문장에 있다. 인공호흡기 이탈 실패는 보유 문장이 호흡성 산증일 때 감량을 검토하라는 것까지이고, 이탈 실패 자체는 없다. '아닌 것'이 인 상승 하나로 닫히지 않는다. 인덱스는 유지한다."),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "ext": NOTES / "06_학습_노트/PN_source_textbook_extract.md",
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
        "te": NOTES / "06_학습_노트/_gl_extract/ASPEN_TE_full.txt",
        "fact": NOTES / "06_학습_노트/_gl_extract/ASPEN_Fact_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_CYC: "sum", Q_NIGHT: "sum", Q_SKIN: "sum", Q_STE: "sum", Q_EX: "sum",
        Q_ZN: "sum", Q_TASTE: "sum", Q_GI: "sum", Q_FIST: "sum", Q_MN: "sum",
        Q_MULTI: "sum", Q_SER: "sum", Q_D10: "sum", Q_PICC: "sum", Q_TUN: "sum",
        Q_PORT: "sum", Q_SLUD: "sum", Q_ORAL: "sum", Q_DEXA: "sum", Q_TG: "sum",
        Q_PAN: "sum", Q_AA: "sum", Q_CKD: "sum", Q_DAY: "sum", Q_G: "sum",
        Q_ENF: "sum", Q_LONG: "sum", Q_AL: "sum", Q_7: "sum", Q_GLU: "sum",
        Q_11: "sum", Q_22: "sum", Q_CU: "sum", Q_SE: "sum", Q_20: "sum", Q_25: "sum",
        Q_NA: "sum", Q_016: "sum", "과도 포도당 피하기 · cyclic PN": "sum",
        "Cr 결핍 = 포도당불내성": "sum",
        Q_PHL: "ext",
        Q_KCAL: "ccn", Q_IBW: "ccn", Q_CAP: "ccn", Q_EN: "ccn",
        Q_TR: "te",
        Q_RESP: "fact",
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
