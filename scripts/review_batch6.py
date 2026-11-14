#!/usr/bin/env python3
"""Batch 6 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes. Explain text is narrowed only where it attributed a number
or a rule the held page does not say.

The held calculation examples (Holliday-Segar 50 kg = 2,100 mL, corrected Ca
9.12, osmolarity 1,183 mOsm/L, Na 129.2/130.8) have no pending item with those
numbers. Chromium/glucose intolerance and selenium/cardiomyopathy are already
verified. No pending stem asks for egg-phospholipid allergy, the compounding
order, or acetate 1:1 in place of bicarbonate.

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
CONTENT_VERSION = "2026-11-14.8"

GILA = "imsangyoungyang-gilajabi"
CCN = "ccn-summary-nestle-2022"

EVAL = "sec-eval-0-영양평가-PN-직결만"
IND = "sec-indications-1-적응증-시작시점-지연"
PROT = "sec-protein-2-3-단백질-아미노산-AA"
FLUID = "sec-fluid_lytes-2-4-수분"
LYTE = "sec-fluid_lytes-2-5-전해질"
TE = "sec-vit_te-2-7-미량원소-TE"
INF = "sec-complications-6-1-3열-요약"
DIS = "sec-disease-8-질환별-PN"
PEDS = "sec-peds-9-소아-신생아"

Q_CROHN = "EN 실패/불가 후"
Q_REST = "장휴식 목적 단독 PN X"
Q_SBO = "지속 소장폐색"
Q_57 = "5~7일 이상"
Q_OBS = "장폐색"
Q_AA4 = "4 kcal/g"
Q_STRESS = "중증 스트레스 1.5~2.0"
Q_NORM = "일반 성인 0.8~1.0"
Q_RENAL = "신부전(비투석) 0.6–0.8"
Q_HE = "간경화·간성뇌증 1.0–1.5"
Q_FIST = "진행 손실(설사·누공·위장관 흡인)은 추가"
Q_IRON = "PN과 별도"
Q_IRONDOSE = "필요시 별도, 월 25\u201350 mg"
Q_KW = "콰시오커 = 단백 결핍"
Q_MAR = "마라스무스 = 열량 결핍"
Q_ALB = "알부민 >3.0 유지"
Q_FAT = "체지방·근육 소모"
Q_UNIT = "성인 g/day·mEq/day"
Q_PEDU = "소아 g/kg/day"
Q_CLABSI = "출입구/터널/포켓/혈류"
Q_EXIT = "출입구 = 온찜질·매일 국소치료·경구 항생제"
Q_BLOOD = "혈류 = antimicrobial lock + 전신 항균제 + 카테터 제거"
Q_CUMN = "담즙울체/간담도 ⟶ Cu·Mn 감량·제한"
Q_WT = ">2%/1주 · >5%/1월 · >7.5%/3월"
Q_DRY = "복수 ⟶ dry weight"
Q_IBW = "최근 최저체중 또는 IBW"
Q_TROPH = "소아 Primene/Trophamine/Aminoven infant"
Q_BOLUS = "intolerant to bolus gastric EN"
Q_HOLD = "EN should not be automatically interrupted for diarrhea"
Q_FIBER = "10\u201320 gm of fermentable soluble fiber is suggested"
Q_PEP = "small peptide formulations in the patient with persistent diarrhea, suspected malabsorption"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치6 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "quizlet-pn-019",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [IND, DIS],
        "explain": "크론병에서 PN은 EN이 실패하거나 쓸 수 없을 때다. 장 휴식을 목적으로 한 PN은 적응이 아니다. 적응으로 적힌 것은 단장, 지속 소장폐색, EN이 불가한 누공, 고배출 장루다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 1 Crohn", Q_CROHN),
            ev(GILA, "PN_jjageuri_summary.md 1 Crohn", Q_REST),
            ev(GILA, "PN_jjageuri_summary.md 8 Crohn", Q_SBO),
        ],
        "choiceExplanations": [
            "오답. 장 휴식 목적의 단독 PN은 적응이 아니다.",
            "정답. EN이 실패하거나 불가한 뒤에 PN을 본다.",
            "오답. 영양불량 예방만으로 PN을 시작한다는 문장은 없다.",
            "오답. 영양 상태와 관계없이 수술 전에 PN을 쓴다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " EN 불내성은 요약의 EN 실패/불가 안에 둔다.",
    },
    {
        "id": "quizlet-pn-018",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [IND, DIS],
        "explain": "위장관 흡수·통과가 되지 않아 5~7일 이상 섭취가 곤란하면 PN을 본다. 장폐색과 지속 소장폐색이 그 경우다. 완화 목적의 전이암, 항암·방사선 자체, 경도 영양불량의 가까운 수술은 그 문장이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 1 GI 흡수 불가", Q_57),
            ev(GILA, "PN_jjageuri_summary.md 1 GI 흡수 불가", Q_OBS),
            ev(GILA, "PN_jjageuri_summary.md 8 Crohn", Q_SBO),
        ],
        "choiceExplanations": [
            "정답. 소장 폐쇄가 7일 넘게 풀리지 않으면 5~7일 이상의 통과 장애에 해당한다.",
            "오답. 전이암의 완화치료 자체가 PN 적응으로 적혀 있지 않다.",
            "오답. 항암과 방사선을 함께 받는다는 사실만으로는 적응이 아니다.",
            "오답. 경도 영양불량이고 3일 뒤 수술인 경우는 5~7일 이상의 통과 장애가 아니다.",
        ],
        "reviewNote": OK_NOTE + " >500 mL/d 누공 숫자는 쓰지 않았다.",
    },
    {
        "id": "bcnsp-088",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PEDS, PROT],
        "explain": "교재의 소아용 아미노산 예는 Primene, Trophamine, Aminoven infant다. Clinisol·Travasol은 그 소아용 예에 없고, HepatAmine은 간질환용이다.",
        "evidence": [
            ev(GILA, "PN_source_textbook_extract.md PDF147", Q_TROPH),
        ],
        "choiceExplanations": [
            "오답. Clinisol 15%는 소아용 예로 적혀 있지 않다.",
            "정답. Trophamine이 소아용 아미노산 예에 있다. Premasol은 그 문장에 없다.",
            "오답. Travasol 10%는 소아용 예로 적혀 있지 않다.",
            "오답. HepatAmine은 간용 제제 쪽이다. 소아용 예는 Primene·Trophamine·Aminoven infant다.",
        ],
        "reviewNote": OK_NOTE + " 보기 안의 Premasol은 교재 추출에 없어 해설에서 근거로 쓰지 않았다.",
    },
    {
        "id": "rxk-4_1-5",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "explain": "철은 배합 제한 때문에 PN과 따로 준다. 필요할 때의 용량으로 적힌 것은 월 25–50 mg이다. TNA에 섞거나 TNA에 곁달아 주거나, 주 3회 피하 25 mg은 그 문장이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.7 철", Q_IRON),
            ev(GILA, "PN_jjageuri_summary.md 2.7 철", Q_IRONDOSE),
        ],
        "choiceExplanations": [
            "오답. 철은 PN에 섞지 않고 따로 준다.",
            "오답. TNA에 곁달아 주는 방법은 그 별도 주입 문장이 아니다.",
            "오답. 주 3회 피하 25 mg은 월 25–50 mg 별도 용량이 아니다.",
            "정답. 세 방법 모두 보유 문장과 같지 않다.",
        ],
        "reviewNote": OK_NOTE + " iron dextran 혼합 금지는 문제은행이라 인용하지 않았다. 별도 주입과 월 25–50 mg만 썼다.",
    },
    {
        "id": "rxk-3_1-3",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [FLUID],
        "explain": "이미 있는 탈수는 먼저 맞추고, 진행 중인 설사·누공·위장관 흡인은 수분에 더한다. 누공이 그 진행 손실이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 2.4 성인 수액", Q_FIST)],
        "choiceExplanations": [
            "오답. 신부전이 진행 손실로 수분을 더하는 상황으로 적혀 있지 않다.",
            "정답. 누공은 설사·위장관 흡인과 함께 진행 손실이라 수분을 더한다.",
            "오답. 울혈성 심부전이 그 추가 목록에 없다.",
            "오답. 간경변이 그 추가 목록에 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "rxk-3_1-5",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT],
        "explain": "아미노산은 4 kcal/g다. 총열량에서 단백을 절대 빼라는 문장은 그 계수와 맞지 않는다. 그래서 '절대 포함하지 않는다'는 거짓이다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 2.3 기본", Q_AA4)],
        "choiceExplanations": [
            "오답. 아미노산 4 kcal/g는 에너지 계수다. 총열량에서 절대 빼라는 뜻이 아니다.",
            "정답. 단백을 에너지 계산에 절대 넣지 않는다는 말은 4 kcal/g와 맞지 않아 거짓이다.",
        ],
        "reviewNote": OK_NOTE + " NPC:N에서 단백 열량을 빼는 칸은 문제은행 표기라 인용하지 않았다.",
    },
    {
        "id": "rxk-1_3-8",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [PROT, DIS],
        "explain": "일반 성인 단백은 0.8~1.0 g/kg/일이고, 중증 스트레스는 1.5~2.0 g/kg/일이다. 비투석 신부전은 0.6–0.8 g/kg/일로 줄인다. 간경화·간성뇌증은 1.0–1.5이고, 결핍이 없으면 1.0–1.2라 스트레스 증량 칸이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.3 요구량", Q_STRESS),
            ev(GILA, "PN_jjageuri_summary.md 2.3 요구량", Q_NORM),
            ev(GILA, "PN_jjageuri_summary.md 2.3 표4-5", Q_RENAL),
            ev(GILA, "PN_jjageuri_summary.md 2.3 표4-5", Q_HE),
        ],
        "choiceExplanations": [
            "오답. 비투석 신부전은 0.6–0.8 g/kg/일로 일반보다 낮다.",
            "오답. 호흡부전이 단백을 올리는 칸으로 적혀 있지 않다.",
            "정답. 중증 스트레스는 1.5~2.0 g/kg/일로 일반 0.8~1.0보다 높다.",
            "오답. 간성뇌증은 1.0–1.5이고 결핍이 없으면 1.0–1.2다. 스트레스 증량 칸이 아니다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "rxk-1_1-3",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL],
        "explain": "마라스무스는 열량 결핍이다. 알부민은 3.0 g/dL보다 높게 유지되고 체지방과 근육이 준다. 알부민이 3.0 미만이고 부종이 있는 쪽은 콰시오커(단백 결핍)다. 단백-열량 영양불량은 그 열량 결핍 형태인 마라스무스에 해당한다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_KW),
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_MAR),
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_ALB),
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_FAT),
        ],
        "choiceExplanations": [
            "정답. 열량 결핍 형태는 마라스무스다. 알부민은 3.0보다 높게 유지된다.",
            "오답. 수주에서 수개월에 걸친다는 시간 경과는 그 문장에 없다.",
            "오답. 저알부민혈증은 콰시오커(단백 결핍, 알부민 <3.0) 쪽이다.",
            "오답. 스트레스 반응 뒤에 따른다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 발생 기간은 보유 문장에 없어 해설에 넣지 않았다.",
    },
    {
        "id": "rxk-1_2-1",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL],
        "explain": "기아성 영양불량의 두 이름은 콰시오커와 마라스무스다. 콰시오커는 단백 결핍이고, 마라스무스는 열량 결핍이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_KW),
            ev(GILA, "PN_jjageuri_summary.md 0 기아성 영양불량", Q_MAR),
        ],
        "choiceExplanations": [
            "오답. 콰시오커는 단백 결핍이라, 빈칸의 단백 영양불량과 같은 쪽이다.",
            "오답. 저알부민은 콰시오커의 소견이지 다른 형태의 이름이 아니다.",
            "정답. 단백 결핍(콰시오커)과 짝인 이름은 열량 결핍인 마라스무스다.",
            "오답. 교재가 쓴 짝 이름은 에너지 영양불량이 아니라 마라스무스다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "medex-011",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [TE, "sec-complications-6-3-간담도-합병증-PNALD"],
        "explain": "담즙정체·간담도 질환에서는 구리와 망간을 감량한다. 신생아라도 성인 칼슘-인 농도, 성인 나트륨, 성인 종합비타민을 그대로 쓰는 문장은 그 감량 문장이 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 2.7 질환 조정", Q_CUMN)],
        "choiceExplanations": [
            "오답. 성인과 같은 칼슘-인 농도를 신생아 목표로 둔다는 문장은 없다.",
            "정답. 담즙정체에서는 구리와 망간을 감량하므로 그 용량을 확인한다.",
            "오답. 신생아 나트륨을 성인 유지량까지 올린다는 문장은 없다.",
            "오답. 성인 종합비타민 용량을 이 연령에 쓴다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 처방의 지질 2 g/kg는 신생아 상한 3–4 안이라 정답 근거로 쓰지 않았다.",
    },
    {
        "id": "quizlet-iib-045",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [INF],
        "explain": "카테터 감염은 출입구, 터널, 포켓, 혈류로 나뉜다. 출구는 국소 치료(온찜질·국소·경구 항생제) 쪽이고, 혈류는 전신 항균제가 들어가는 쪽이다. 출구에 발적·고름이 없고 오한·발열·혈액배양 양성이면 혈류 감염이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.1 감염", Q_CLABSI),
            ev(GILA, "PN_jjageuri_summary.md 10 감염 치료", Q_EXIT),
            ev(GILA, "PN_jjageuri_summary.md 10 감염 치료", Q_BLOOD),
        ],
        "choiceExplanations": [
            "오답. 터널 감염은 출구 소견이 없는 발열·양성 배양과 다른 칸이다.",
            "오답. 출구 감염은 출구의 국소 소견을 치료하는 칸이다. 발적·고름이 없다.",
            "오답. 카테터 관련 정맥염은 출입구·터널·포켓·혈류 분류에 없다.",
            "정답. 국소 출구 소견 없이 발열과 혈액배양이 양성이면 혈류 감염이다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-pn-009",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LYTE, PEDS],
        "explain": "성인 PN 성분은 하루 총량인 g/day·mEq/day로 적는다. 소아는 g/kg/day다. 처음 농도와 부피, 리터당 그램, 최종 백분율은 그 하루 총량 단위가 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 2.5 단위", Q_UNIT),
            ev(GILA, "PN_jjageuri_summary.md 2.5 단위", Q_PEDU),
        ],
        "choiceExplanations": [
            "오답. 50% 포도당 500 mL처럼 처음 농도와 부피로 적는 방식은 하루 총량이 아니다.",
            "오답. 리터당 그램은 g/day가 아니다.",
            "오답. 최종 농도 백분율은 g/day가 아니다.",
            "정답. 성인은 24시간 주입량의 그램, 곧 g/day로 적는다.",
        ],
        "reviewNote": OK_NOTE + " 2014 안전성 합의 PDF는 인용하지 않았다. 교재의 성인 g/day 단위만 썼다.",
    },
    {
        "id": "cnsc-nutrition-support-015",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [EVAL],
        "explain": "급성 질환·외상의 중증 영양불량에서 체중 감소는 1주에 2% 초과, 1개월에 5% 초과, 3개월에 7.5% 초과다. 1개월을 묻는 칸은 5% 초과다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 0 중증 영양불량", Q_WT)],
        "choiceExplanations": [
            "정답. 1개월 기준의 중증 체중 감소는 5% 초과다.",
            "오답. 2% 초과는 1주 기준이다.",
            "오답. 1% 초과는 그 기준에 없다.",
            "오답. 15% 초과는 1개월 기준이 아니다. 3개월은 7.5% 초과다.",
        ],
        "reviewNote": OK_NOTE + " 6특징 합의 원문은 인용하지 않았다. 교재의 기간별 체중 감소만 썼다.",
    },
    {
        "id": "cnsc-nutrition-support-010",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [DIS, EVAL],
        "explain": "복수가 있으면 열량에 쓰는 체중은 최근 최저체중 또는 이상체중이고, 그것을 dry weight로 적는다. 측정 체중에 수분 무게를 더하지 않는다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8 간질환", Q_DRY),
            ev(GILA, "PN_jjageuri_summary.md 8 간질환", Q_IBW),
        ],
        "choiceExplanations": [
            "오답. 복수가 있는데 측정 체중을 그대로 쓰는 방법이 아니다.",
            "오답. 수분 무게를 더하면 dry weight의 반대다.",
            "정답. 과잉 수분을 빼 dry weight로 본다. 복수는 최근 최저체중 또는 이상체중이다.",
            "오답. BMI만 쓰고 체중을 보지 말라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "cnsc-nutrition-support-064",
        "answer": 3,
        "referenceIds": [CCN],
        "coreSectionIds": [IND],
        "explain": "설사가 계속되거나 흡수장애가 의심되면 작은 펩타이드 제제를 고려한다. 흡수장애가 그 경우다. 표준 고분자 제제, 신장용 농축 제제, 고섬유 제제는 그 문장이 아니다.",
        "evidence": [ev(CCN, "CCN Summary 2022 Peptides", Q_PEP)],
        "choiceExplanations": [
            "오답. 표준 고분자 온전 단백은 흡수장애에 권한 펩타이드 제제가 아니다.",
            "오답. 신장 특화 농축 제제는 그 문장에 없다.",
            "오답. 고섬유는 흡수장애의 펩타이드 제제 문장이 아니다. 섬유에 반응이 없을 때 펩타이드를 본다.",
            "정답. 흡수장애가 의심되면 작은 펩타이드 제제다. 보기의 요소 제제까지 그 문장이 말하진 않는다.",
        ],
        "reviewNote": OK_NOTE + " 췌장 기능부전의 별도 문장은 없다. 흡수장애의 펩타이드 제제로 닫았다.",
    },
    {
        "id": "bcnsp-069",
        "answer": 1,
        "referenceIds": [CCN],
        "coreSectionIds": [IND],
        "explain": "설사가 있다고 경장영양을 바로 끊지 않는다. 섬유가 금기가 아니면 발효성 가용성 섬유 10–20 g을 24시간에 나눠 고려하고, 설사가 계속되거나 흡수장애가 의심되면 작은 펩타이드 제제를 고려한다.",
        "evidence": [
            ev(CCN, "CCN Summary 2022 Diarrhea", Q_HOLD),
            ev(CCN, "CCN Summary 2022 Diarrhea", Q_FIBER),
            ev(CCN, "CCN Summary 2022 Peptides", Q_PEP),
        ],
        "choiceExplanations": [
            "오답. 설사가 있을 때 볼루스로 바꾸는 문장은 없다. 볼루스 불내성에는 지속 주입을 본다.",
            "정답. EN을 유지한 채 섬유 또는 펩타이드(반요소) 제제를 보는 쪽이다. 속도 감량의 보유 숫자는 없다.",
            "오답. 설사만으로 EN을 끊고 PN으로 바꾸지 않는다.",
            "오답. 로페라미드 16 mg을 하루 4회 쓴다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 공장루와 속도 감량은 보유 문장에 없어 근거로 쓰지 않았다.",
    },
    {
        "id": "allaccess-003",
        "answer": 2,
        "referenceIds": [CCN],
        "coreSectionIds": [IND],
        "explain": "위 볼루스 급식에 불내성이면 지속 주입으로 바꾼다. 급식 30분 뒤 반복되는 경련통은 그 불내성이다.",
        "evidence": [ev(CCN, "CCN Summary 2022 Aspiration", Q_BOLUS)],
        "choiceExplanations": [
            "오답. 머리 올리기는 흡인 위험의 조치로 적혀 있고, 볼루스 불내성의 조치는 지속 주입이다.",
            "오답. 고장성 제제로 바꾸라는 문장은 없다.",
            "정답. 볼루스에 불내성이면 지속 주입으로 바꾼다.",
            "오답. 솔비톨 함유 약을 확인하라는 문장은 이 불내성 조치에 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
]


BLOCKERS = [
    (
        "quizlet-pn-001",
        "BLOCKER 배치6: 임신성 과다구토는 적응 후보로만 있다. EN 시도와 보존치료에 불내성인 뒤에만 PN이라는 조건 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-002",
        "BLOCKER 배치6: 급속 인 보충의 저칼슘·테타니·말초 혈전정맥염은 문제은행 표기다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-006",
        "BLOCKER 배치6: 디펩티벤 20%는 조혈모세포이식 등 조건부 급여다. 디펩티드가 유리 글루타민보다 안정하다는 문장은 요약에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-023",
        "BLOCKER 배치6: 병상 삽입 후 흉부 X선 확인 전 PN을 시작하지 말라는 문장은 문제은행 표기다. 교재 추출은 끝이 SVC–우심방이고 대퇴 카테터를 피하라고 한다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-039",
        "BLOCKER 배치6: 자동 조제기가 정확히 전달할 수 있는 양보다 적으면 수동 조제라는 문장을 요약·지침 추출에서 확인하지 못했다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-042",
        "BLOCKER 배치6: 급속 인 보충의 테타니는 문제은행 표기다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-044",
        "BLOCKER 배치6: Ca×P >55의 연조직·혈관 석회화 문장을 요약·교재 추출에서 확인하지 못했다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-011",
        "BLOCKER 배치6: 교재는 대퇴 카테터 PN을 피하라고 한다. 감염을 줄이려고 쇄골하를 선호한다는 문장은 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-023",
        "BLOCKER 배치6: 출구 감염은 온찜질·매일 국소치료·경구 항생제다. 정답 보기는 전신 항균제다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-029",
        "BLOCKER 배치6: 재급식 고위험은 알코올 중독·신경성 식욕부진·심한 영양결핍이다. 흡수장애와 3일 섭취 부족이 그 목록 밖에 있어 아닌 것이 하나로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-036",
        "BLOCKER 배치6: 알칼리증에서 염화물:아세트산 비를 올린다는 방향은 문제은행 표기다. 교재가 확정한 것은 중탄산염 대신 acetate 1:1이다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-003",
        "BLOCKER 배치6: 장기 PN 미량원소·비타민은 3–12개월마다다. 6개월과 매년이 둘 다 그 안에 들어 하나로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-home-ns-009",
        "BLOCKER 배치6: 미드라인이 고장성 PN·가정 PN에 부적합하다는 문장을 요약·교재 추출에서 확인하지 못했다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-003",
        "BLOCKER 배치6: (80−68)/80 = 15%는 보유 예제(Holliday-Segar 50 kg = 2,100 mL, 교정 칼슘 9.12, 삼투압 1,183 mOsm/L, 나트륨 129.2/130.8)가 아니다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-007",
        "BLOCKER 배치6: ICU 선별도구는 NRS 2002와 NUTRIC 둘 다다. NUTRIC만으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-052",
        "BLOCKER 배치6: 기계적 합병증으로 적힌 것은 기흉·동맥손상·위치이상·혈전·폐쇄다. 공기색전 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-074",
        "BLOCKER 배치6: 공장 볼루스의 덤핑 문장은 없다. CCN은 위 볼루스 불내성일 때 지속 주입을 말한다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-019",
        "BLOCKER 배치6: 미숙아 단백은 교재 3.0–4.0 g/kg/일이고 ESPEN은 첫날 1.5–2.5, 다음 2.5–3.5다. 정답의 시작 1.5–2.0과 증량 3.5–4.0은 한 칸이 아니다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-033",
        "BLOCKER 배치6: 고용량 포도당에서 요구가 는다고 적힌 전해질은 인이다. 칼륨만으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-076",
        "BLOCKER 배치6: 말초신경병증은 크롬 결핍과 셀레늄 독성 문장에 있다. 비타민 E 결핍이 운동실조라는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-082",
        "BLOCKER 배치6: 나트륨 교정은 ≤12 mmol/L/일이다. 정답의 10–12 mEq/L와 PN 나트륨 감량·자유수 추가는 그 문장으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "kshp-46",
        "BLOCKER 배치6: 지용성 A·D·E는 주의, 수용성 C는 상대적으로 낮고, 자연형 K 독성도 낮다고 적혀 C와 K가 같이 남는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_4-1",
        "BLOCKER 배치6: EN 금기 목록에 폐질환은 없다. 중증 급성췌장염도 경장영양 우선이라 아닌 것이 폐질환 하나로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_3-6",
        "BLOCKER 배치6: 재급식 고위험은 알코올 중독·신경성 식욕부진·심한 영양결핍이다. 장기 정맥영양과 심한 스트레스·고갈이 그 목록 밖에 같이 남는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-3_1-7",
        "BLOCKER 배치6: BCAA는 만성 뇌증 stage II에서만 인정한다는 문장과, 간성뇌증에 일관된 근거가 낮아 권하지 않는다는 문장이 갈린다. 간질환 일반으로 올리지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-3_3-4",
        "BLOCKER 배치6: 인을 빨리 주면 저칼슘이라는 문장은 문제은행 표기다. 인덱스는 유지한다.",
    ),
    (
        "rxk-4_1-4",
        "BLOCKER 배치6: 대사성 골질환 조정은 고단백·과도한 나트륨을 피하고 칼슘·인·마그네슘을 맞추며 알루미늄을 최소화한다. 운동 문장은 없다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "txt": NOTES / "06_학습_노트/PN_source_textbook_extract.md",
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_CROHN: "sum", Q_REST: "sum", Q_SBO: "sum", Q_57: "sum", Q_OBS: "sum",
        Q_AA4: "sum", Q_STRESS: "sum", Q_NORM: "sum", Q_RENAL: "sum", Q_HE: "sum",
        Q_FIST: "sum", Q_IRON: "sum", Q_IRONDOSE: "sum", Q_KW: "sum", Q_MAR: "sum",
        Q_ALB: "sum", Q_FAT: "sum", Q_UNIT: "sum", Q_PEDU: "sum", Q_CLABSI: "sum",
        Q_EXIT: "sum", Q_BLOOD: "sum", Q_CUMN: "sum", Q_WT: "sum", Q_DRY: "sum",
        Q_IBW: "sum", Q_TROPH: "txt",
        Q_BOLUS: "ccn", Q_HOLD: "ccn", Q_FIBER: "ccn", Q_PEP: "ccn",
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
