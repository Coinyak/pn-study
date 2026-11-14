#!/usr/bin/env python3
"""Batch 3 pending-review promotions.

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
CONTENT_VERSION = "2026-11-14.5"

MYTHS = "aspen-pn-myths-practice-tool-2024"
GILA = "imsangyoungyang-gilajabi"
CAP = "espen-ped-pn-2018-08-calcium-phosphorus-magnesium"
CCN = "ccn-summary-nestle-2022"
KSHP = "kshp-yeongyang-yakryo-lecture-answers"
LIPGL = "espen-ped-pn-2018-03-lipids"

LIP = "sec-lipid-2-2-지방-ILE"
VIT = "sec-vit_te-2-6-비타민"
TE = "sec-vit_te-2-7-미량원소-TE"
R31 = "sec-route-3-1-말초-vs-중심"
R32 = "sec-route-3-2-2-in-1-vs-3-in-1-TNA"
S52 = "sec-stability-5-2-Ca-P-침전"
S54 = "sec-stability-5-4-필터-hang-time-세트-BUD"
PNALD = "sec-complications-6-3-간담도-합병증-PNALD"
EFAD = "sec-lipid-6-5-필수지방산-결핍-EFAD"
MON = "sec-monitor-7-1-PN-대사합병증-모니터-표11-1-TXT-p179"
STOP = "sec-monitor-7-3-PN-중단-이행"
OB = "sec-disease-8-2-당뇨-비만"
HPN = "sec-hpn-10-재택-PN-HPN"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


Q_BAG = "3-in-1: 투여 간편·24h 가능"
Q_ONE = "1 bag·1 line"
Q_SEE = "침전 육안 확인 쉬움"
Q_OPAQUE = "불투명 ⟶ 침전 육안 확인 어려움"
Q_UNST = "3-in-1이 2-in-1보다 유화제 때문에 불안정↑"
Q_DEATH = "CaHPO₄ 침전 = 카테터 폐색·색전 ⟶ 사망 가능"
Q_EYE = "환자·라벨 확인 · 육안 검사"
Q_ORG = "The use of organic phosphorus compounds circumvents this problem."
Q_R87 = "It is recommended to use organic Ca and P salts for compounding of PN solutions to prevent precipitation"
Q_FISH = "SO+MCT+어유 복합 ILE / fish oil 기반"
Q_MAN = "과도 포도당 피하기 · cyclic PN · SO-ILE 감량"
Q_MN = "간담도 ⟶ Mn·Cu 감량"
Q_LA = "LA 2~4% + ALA 0.25~0.5%"
Q_R418 = "a discontinuation of SO ILE, a reduction of other ILE dosage and/or the use of composite"
Q_FO = "fish oil 기반 ILE 추천"
Q_TT = "triene:tetraene ≥ 0.2"
Q_TTB = "0.2 이상"
Q_SKIN = "피부도포 = 효과 낮음"
Q_Q6 = "Capillary glucose: 개시 후 goal 도달까지 q6h"
Q_REB = "저혈당·반동: 감속 1–2h 또는 속도 절반"
Q_ADULT = "성인 흔함 · PN 2주 내 AST/ALT 경미 상승"
Q_EXCESS = "원인 = 과도 공급"
Q_LAB = "ALP·GGT·DB↑"
Q_DB = "conjugated(direct) bilirubin ≥2 mg/dL = 담즙정체 정의"
Q_CIRR = "⟶ 간경변·간부전"
Q_SLUD = "sludge·담석 (장 자극 부재)"
Q_ORAL = "경구 자극"
Q_KCAL = "20% 2.0 kcal/mL"
Q_FAT10 = "3-in-1 계산 시 지방 10 kcal/g(대두유)"
Q_MAX = "하루 ≤2.5 g/kg"
Q_MAX2 = "일일 ≤2.5 g/kg"
Q_MTX = "MTX·trimethoprim·항경련제도 결핍 유발"
Q_PROT = "Protein is suggested at ≥ 2.0 gm/kg IBW**/day for BMI 30–40, and up to 2.5 gm/kg IBW**/day for BMI ≥ 40."
Q_AA = "AA 3~5% · 포도당 5~10%"
Q_D10 = "말초 혈전정맥염 위험 → 중심정맥 권장"
Q_K = "K 150 μg"
Q_PICC = "PICC tip SVC"
Q_FEM = "대퇴 카테터 PN 회피"
Q_ZN = "발진·탈모·야맹증·미각변화"
Q_ZNS = "Zn 결핍 = 피부염·설사·상처치유 지연"
Q_FIST = "누공 고배출"
Q_ZNCU = "고용량 Zn(≥40 mg/d) ⟶ Cu 결핍"
Q_CU = "Cu 결핍 = 호중구감소·빈혈"
Q_B1 = "장기기아/알코올: PN 초기 5–7일 thiamine 50–100 mg/d"
Q_BEFORE = "포도당 투여 전에 보충해야 한다"
Q_NIGHT = "HPN 대부분 야간 10–12 h"
Q_CYC = "주기 12–18 h(간독성 예방·HPN)"
Q_FILT = "A single 1.2 micron filter is recommended for use when infusing all types of PN"
Q_PART = "A single 1.2 micron filter is likely to prevent infusing particles >2 microns"
Q_RAMP = "시작·끝 1 h씩 단계 증감"

OK_NOTE = "배치3 verified. 정답 인덱스 유지."

PROMOTIONS = [
    {
        "id": "bcnsp-068",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [R32],
        "errataIds": [],
        "explain": "3-in-1은 아미노산·포도당·지방유제를 한 백에 넣어 라인 하나로 준다. 교재는 투여가 간편하고 24시간 주입이 가능하다고 적는다. 침전을 눈으로 확인하기 쉬운 쪽은 2-in-1이고, 3-in-1은 불투명하다.",
        "evidence": [
            ev(GILA, "PN_source_textbook_extract.md PDF145", Q_BAG),
            ev(GILA, "PN_jjageuri_summary.md 3.2 장점", Q_ONE),
            ev(GILA, "PN_jjageuri_summary.md 3.2 장점·단점", Q_SEE),
            ev(GILA, "PN_jjageuri_summary.md 3.2 단점", Q_OPAQUE),
        ],
        "choiceExplanations": [
            "오답. 3-in-1은 유화제 때문에 2-in-1보다 불안정하다. 칼슘-인 적합성이 더 좋다는 문장은 없다.",
            "정답. 다량영양소를 한 백에 담아 투여가 단순해진다. 교재는 1 bag·1 line으로 간편하다고 적는다.",
            "오답. 3-in-1의 사용기한이 2-in-1보다 길다는 문장은 없다. 적힌 차이는 간편함과 24시간 주입이다.",
            "오답. 침전을 육안으로 보기 쉬운 것은 2-in-1이다. 3-in-1은 불투명하다.",
        ],
        "reviewNote": OK_NOTE + " 교재 PDF145의 한 백 간편함. 해설의 0.22/1.2 이원 필터 문장은 구 권고라 뺐고 E5 연결도 뗐다. 정답은 필터가 아니다.",
    },
    {
        "id": "cnsc-nutrition-support-049",
        "answer": 3,
        "referenceIds": [GILA, LIPGL],
        "coreSectionIds": [PNALD, LIP, HPN],
        "errataIds": [],
        "explain": "ALP와 결합 빌리루빈이 오르는 담즙정체에는 과도한 포도당을 피하고, 대두유 지질을 줄이며, 어유가 든 지방유제를 쓰고, 주기 주입을 한다. 망간은 담즙정체에서 감량한다. 지질을 전부 빼면 필수지방산(LA 2–4%, ALA 0.25–0.5%)을 남기지 못한다. ESPEN 소아 지질 R4.18은 소아 IFALD에서 대두유 중단·다른 지질 감량 또는 어유 혼합유제를 회복 조치로 적는다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", Q_MAN),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", Q_FISH),
            ev(GILA, "PN_jjageuri_summary.md 6.3 TE 조정", Q_MN),
            ev(GILA, "PN_jjageuri_summary.md 6.5 예방 %kcal", Q_LA),
            ev(GILA, "PN_jjageuri_summary.md 10 IFALD", Q_FO),
            ev(LIPGL, "ESPEN pediatric PN lipids R4.18", Q_R418),
        ],
        "choiceExplanations": [
            "오답. 관리 문장은 과도한 포도당을 피하라고 한다. 열량을 맞추려고 포도당을 더 올리지 않는다.",
            "오답. 간담도 합병증에서는 망간과 구리를 감량한다. 망간을 추가하지 않는다.",
            "오답. 대두유는 줄이되, 필수지방산(LA 2–4% + ALA 0.25–0.5%)은 남긴다. 지질을 영구히 전부 제거하지 않는다.",
            "정답. 대두유 감량, 어유 함유 지방유제, 주기 주입이 관리 문장에 함께 있다.",
        ],
        "reviewNote": OK_NOTE + " 교재 6.3 관리 문장. R4.18은 소아 IFALD 문장으로 대두유·어유 쪽에만 붙였다. 주기 주입은 교재.",
    },
    {
        "id": "cnsc-nutrition-support-045",
        "answer": 2,
        "referenceIds": [MYTHS, GILA],
        "coreSectionIds": [S54, S52, R32],
        "errataIds": [],
        "explain": "3-in-1은 유화 때문에 2-in-1보다 불안정하고, 인산칼슘 침전은 카테터 폐색·색전으로 사망할 수 있다. 현행 권고는 모든 PN에 단일 1.2 μm 필터이고, 2 μm를 넘는 입자를 걸러 내기 위한 것이다.",
        "evidence": [
            ev(GILA, "PN_source_textbook_extract.md PDF201", Q_UNST),
            ev(GILA, "PN_jjageuri_summary.md 5.2 위험", Q_DEATH),
            ev(MYTHS, "p.3 Filters are required", Q_FILT),
            ev(MYTHS, "p.3 같은 항목", Q_PART),
        ],
        "choiceExplanations": [
            "오답. 1.2 μm 필터가 막으려는 대상으로 적힌 것은 2 μm를 넘는 입자이다. 공기색전이 그 문장은 아니다.",
            "오답. 포도당 결정화가 3-in-1에서 1.2 μm 필터를 쓰는 이유로 적혀 있지 않다.",
            "정답. 인산칼슘 침전과 3-in-1의 유화 불안정이 입자 쪽 합병증이다. 단일 1.2 μm 필터는 그 입자를 걸러 내려고 모든 PN에 쓴다.",
            "오답. 비타민 분해는 필터 공극으로 막는 합병증으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 정답은 필터 크기가 아니라 3-in-1의 입자 합병증이다. 해설의 2-in-1 0.22 μm 문장은 구 권고라 뺐고 E5 연결도 뗐다. 0.22 μm를 정답으로 둔 문항은 올리지 않았다.",
    },
    {
        "id": "quizlet-pn-045",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [EFAD],
        "errataIds": [],
        "explain": "필수지방산 결핍의 생화학 표지는 triene:tetraene 비 0.2 이상이다. 보기의 '> 0.2'는 그 컷을 가리키는 표기이다. 피부 도포의 예방 효과는 낮다고 적혀 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.5 진단 [EXAM p182]", Q_TT),
            ev(GILA, "PN_jjageuri_summary.md 6.5 진단", Q_TTB),
            ev(GILA, "PN_jjageuri_summary.md 6.5 예방 용량", Q_SKIN),
        ],
        "choiceExplanations": [
            "오답. 중성지방 50 mg/dL 미만은 필수지방산 결핍의 생화학 표지가 아니다.",
            "오답. 림프구 수는 이 표지가 아니다.",
            "오답. 콜레스테롤 100 mg/dL 미만은 이 표지가 아니다.",
            "정답. 교재는 triene:tetraene 0.2 이상을 진단 표지로 적는다. '> 0.2' 보기가 그 비이다.",
        ],
        "reviewNote": OK_NOTE + " 교재 ≥0.2. 보기 >0.2는 요약이 같은 컷으로 적어 둔 표기. 피부 도포가 결핍을 완화한다는 문장은 효과가 낮다는 교재 문장과 달라 뺐다.",
    },
    {
        "id": "bcnsp-029",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [EFAD],
        "errataIds": [],
        "explain": "필수지방산 결핍과 맞는 검사는 triene:tetraene 비 상승이다. 교재 본문은 0.2 이상이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.5 진단 [EXAM p182]", Q_TT),
            ev(GILA, "PN_jjageuri_summary.md 6.5 진단", Q_TTB),
        ],
        "choiceExplanations": [
            "정답. triene:tetraene 비가 오른 것이 필수지방산 결핍의 검사 소견이다. 교재 컷은 0.2 이상이다.",
            "오답. 중성지방 상승은 이 결핍의 표지가 아니다. 지질 과다는 따로 감시한다.",
            "오답. 콜레스테롤 저하만으로 이 결핍을 진단하지 않는다.",
            "오답. 프리알부민 상승은 필수지방산 결핍의 소견이 아니다.",
        ],
        "reviewNote": OK_NOTE + " quizlet-pn-045와 같은 교재 컷.",
    },
    {
        "id": "quizlet-pn-050",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [MON],
        "errataIds": [],
        "explain": "PN을 시작한 뒤 목표 혈당에 닿기까지 모세혈 혈당은 6시간마다 본다. 안정되면 간격을 늘릴 수 있다.",
        "evidence": [ev(GILA, "PN_source_textbook_extract.md PDF179", Q_Q6)],
        "choiceExplanations": [
            "정답. 개시 후 목표에 닿기까지 모세혈 혈당은 q6h이다.",
            "오답. 8시간마다는 그 간격이 아니다.",
            "오답. 12시간마다는 목표 도달 전 간격이 아니다.",
            "오답. 24시간마다는 목표 도달 전 간격이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 PDF179 q6h. 인슐린이 들어 있을 때만이라는 한정은 그 문장에 없다.",
    },
    {
        "id": "quizlet-pn-051",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [STOP],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_source_textbook_extract.md PDF181", Q_REB)],
        "choiceExplanations": [
            "오답. 급중단의 반동으로 적힌 것은 저혈당이다. 저칼륨이 그 문장은 아니다.",
            "정답. PN을 갑자기 끊으면 반동 저혈당이 난다. 중단 전 1–2시간 감속한다.",
            "오답. 과혈량이 급중단의 위험으로 적혀 있지 않다.",
            "오답. 저마그네슘이 급중단의 반동으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 교재 PDF181 반동 저혈당.",
    },
    {
        "id": "quizlet-iib-007",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [STOP],
        "errataIds": [],
        "explain": "급중단은 반동 저혈당을 부른다. 교재는 중단 전 1–2시간 감속하거나 속도를 절반으로 낮추라고 적는다.",
        "evidence": [ev(GILA, "PN_source_textbook_extract.md PDF36·PDF181", Q_REB)],
        "choiceExplanations": [
            "오답. 감속 없이 바로 끊는 것이 반동 저혈당을 막는 방법이 아니다.",
            "정답. 중단 전 1–2시간에 걸쳐 속도를 줄인다.",
            "오답. 2–3시간은 교재의 감속 시간이 아니다.",
            "오답. 3–4시간은 교재의 감속 시간이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 1–2시간. 보유하지 않은 2004 논문 귀속은 해설에서 뺐다.",
    },
    {
        "id": "bcnsp-023",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [S52],
        "errataIds": [],
        "explain": "칼슘과 인이 한 PN에 있으면 인산칼슘 침전이 문제이다. 침전은 카테터 폐색·색전으로 사망할 수 있다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 5.2 위험", Q_DEATH)],
        "choiceExplanations": [
            "오답. 지질 크리밍은 칼슘과 인이 함께 있을 때의 대표 문제가 아니다.",
            "정답. 칼슘과 인의 배합 문제는 인산칼슘 침전이다.",
            "오답. 아미노산 분해가 그 배합 문제로 적혀 있지 않다.",
            "오답. 포도당 캐러멜화가 그 배합 문제로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 교재 인산칼슘 침전.",
    },
    {
        "id": "bcnsp-072",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [S52, S54],
        "errataIds": [],
        "explain": "백이 혼탁하고 입자가 보이면 주입하지 않는다. 인산칼슘 침전은 카테터 폐색·색전으로 사망할 수 있다. 투여 전에 육안 확인을 한다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 5.2 위험", Q_DEATH),
            ev(GILA, "PN_jjageuri_summary.md 5.4 투여 전", Q_EYE),
        ],
        "choiceExplanations": [
            "오답. 따뜻하게 하거나 세게 흔들어 침전을 되돌리고 주입하지 않는다.",
            "정답. 주입하지 않고 교체를 요청한다. 입자가 보이면 주지 않는다.",
            "오답. 0.22 μm 필터를 달아 침전 백을 천천히 주입하지 않는다.",
            "오답. 생리식염수로 희석해 주입하지 않는다.",
        ],
        "reviewNote": OK_NOTE + " 침전은 주입하지 않는다. FDA 고유 사례 귀속은 교재의 '사망 가능'으로 좁혔다.",
    },
    {
        "id": "oep-bcscp-q-060",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [S52],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 5.2 위험", Q_DEATH)],
        "choiceExplanations": [
            "오답. 결정이 보인 백을 흔든 뒤 계속 주입하지 않는다.",
            "정답. 주입을 멈추고 주입팀에 연락한다. 인산칼슘 침전은 색전과 사망으로 이어질 수 있다.",
            "오답. 백을 데워 결정을 녹이지 않는다.",
            "오답. 물을 넣어 침전을 희석하지 않는다.",
        ],
        "reviewNote": OK_NOTE + " bcnsp-072와 같은 침전 문장.",
    },
    {
        "id": "bcnsp-097",
        "answer": 1,
        "referenceIds": [CAP],
        "coreSectionIds": [S52],
        "errataIds": [],
        "explain": "유기 인 화합물은 무기 인산염이 칼슘과 침전하는 문제를 피한다. ESPEN 소아 PN은 침전을 막으려고 유기 칼슘·인 염을 쓰라고 한다.",
        "evidence": [
            ev(CAP, "ESPEN pediatric PN Ca·P, parenteral mineral supply", Q_ORG),
            ev(CAP, "R 8.7", Q_R87),
        ],
        "choiceExplanations": [
            "오답. 유기 인산염이 더 싸다는 문장은 없다.",
            "정답. 유기 인은 칼슘과의 침전을 피한다. sodium glycerophosphate가 그 유기 인 화합물의 예로 적혀 있다.",
            "오답. 밀리리터당 인 함량이 더 높다는 문장은 이 권고에 없다.",
            "오답. 말초정맥 흡수가 더 좋다는 문장은 없다. 정맥영양의 인산염은 장에서 흡수되는 제형이 아니다.",
        ],
        "reviewNote": OK_NOTE + " ESPEN 소아 Ca·P. 비용·고농도 주장은 그 문장에 없어 해설에서 뺐다.",
    },
    {
        "id": "bcnsp-010",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "errataIds": [],
        "explain": "아연 결핍은 미각 변화, 탈모, 발진·피부염으로 나타난다. 구리 결핍은 호중구감소·빈혈, 셀레늄 결핍은 심근병증, 크롬 결핍은 포도당 불내성이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md Zn [EXAM+ p093]", Q_ZN),
            ev(GILA, "PN_jjageuri_summary.md 결핍/독성 [TXT p273]", Q_ZNS),
            ev(GILA, "PN_jjageuri_summary.md Cu [TXT p273]", Q_CU),
        ],
        "choiceExplanations": [
            "오답. 구리 결핍은 호중구감소와 빈혈이다. 미각이상·탈모·피부염의 조합이 아니다.",
            "오답. 셀레늄 결핍은 심근병증이다.",
            "정답. 아연 결핍은 미각 변화, 탈모, 발진·피부염이다.",
            "오답. 크롬 결핍은 포도당 불내성과 고혈당 쪽이다.",
        ],
        "reviewNote": OK_NOTE + " 교재 아연 결핍 증상. 소장 1 L당 12 mg, 대변 1 kg당 17 mg은 보유 문장에 없어 뺐다.",
    },
    {
        "id": "quizlet-iib-003",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD],
        "errataIds": [],
        "explain": "성인에서 흔한 PN 간 합병증은 지방증이고, 원인은 과도한 공급이다. 이 환자는 70 kg에 3,000 kcal라 약 43 kcal/kg이다. 담즙정체의 표지는 ALP·GGT·직접 빌리루빈이고 소아에 더 흔하다고 적혀 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증 [TXT p186]", Q_ADULT),
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증", Q_EXCESS),
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체", Q_LAB),
        ],
        "choiceExplanations": [
            "정답. 성인에게 흔하고 과도 공급이 원인인 유형은 간 지방증이다.",
            "오답. 담즙정체는 ALP·GGT·직접 빌리루빈이 표지이고 소아에 더 흔하다고 적혀 있다. 이 증례의 축은 성인의 과다 열량이다.",
            "오답. 담낭 슬러지는 장 자극이 없을 때의 담낭 문제이다. 아미노전이효소 상승의 유형 이름이 아니다.",
            "오답. 전격성 간부전은 이 경한 효소 상승의 유형으로 적혀 있지 않다.",
        ],
        "reviewNote": OK_NOTE + " 성인·과도 공급 = 지방증. 지방증이 ALP·빌리루빈을 올린다는 귀속은 교재가 그 표지를 담즙정체에 적어 해설에서 뺐다.",
    },
    {
        "id": "rx-pnald-prevent",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD],
        "errataIds": [],
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 지방증", Q_EXCESS),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", Q_MAN),
            ev(GILA, "PN_jjageuri_summary.md 6.3 담낭", Q_SLUD),
            ev(GILA, "PN_jjageuri_summary.md 6.3 TE", Q_MN),
        ],
        "choiceExplanations": [
            "정답. 지방증의 원인은 과도 공급이다. 과도한 포도당을 피한다.",
            "오답. 포도당을 더 주면 과도 공급 쪽이 된다.",
            "오답. 간담도 합병증에서는 구리와 망간을 감량한다. 구리를 늘리지 않는다.",
            "오답. 장 자극이 없으면 슬러지·담석이 생긴다. 경구 섭취를 끊지 않고 경구 자극을 남긴다.",
        ],
        "reviewNote": OK_NOTE + " 과도 공급을 피하고 경구 자극을 남긴다.",
    },
    {
        "id": "quizlet-iib-041",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD],
        "errataIds": [],
        "explain": "담즙정체는 ALP, GGT, 직접 빌리루빈이 오른다. 직접 빌리루빈 ≥2 mg/dL가 담즙정체 정의로 적혀 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체", Q_LAB),
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체 [EXAM p186]", Q_DB),
        ],
        "choiceExplanations": [
            "오답. 프로트롬빈 시간은 담즙정체의 표지 조합이 아니다.",
            "오답. AST/ALT 비는 ALP·GGT·직접 빌리루빈 조합이 아니다.",
            "오답. 콜레스테롤 상승이 그 정의는 아니다.",
            "정답. ALP, GGT, 직접 빌리루빈 상승이 담즙정체를 가리킨다. 직접 빌리루빈 ≥2 mg/dL가 정의이다.",
        ],
        "reviewNote": OK_NOTE + " 해설의 >2 mg/dL는 교재 ≥2 mg/dL로 맞췄다.",
    },
    {
        "id": "quizlet-iib-042",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN, PNALD],
        "errataIds": [],
        "explain": "주기 12–18시간 주입은 간독성 예방으로 적혀 있다. 장기 PN의 간담도 관리에도 cyclic PN이 들어 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p154]", Q_CYC),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", Q_MAN),
        ],
        "choiceExplanations": [
            "오답. 카르니틴을 넣어 간담도 합병증을 예방한다는 문장은 없다.",
            "오답. 지방유제를 전부 중단하는 것이 관리 문장이 아니다. 대두유는 감량하고 필수지방산은 남긴다.",
            "정답. 주기 투여는 간독성 예방으로 적혀 있고, 관리 목록의 cyclic PN이다.",
            "오답. 미량원소를 일괄로 줄이라는 문장은 없다. 담즙정체에서 감량하는 것은 망간과 구리이다.",
        ],
        "reviewNote": OK_NOTE + " 주기 주입의 '선호' 태그는 문제은행이라 근거로 쓰지 않았다. 간독성 예방은 교재 PDF154.",
    },
    {
        "id": "bcnsp-025",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [HPN, PNALD],
        "errataIds": [],
        "explain": "장기 PN에서 간효소와 직접 빌리루빈이 오르면 연속 주입 대신 주기 주입을 한다. HPN은 대부분 야간 10–12시간이고, 간독성 예방의 주기 주입은 12–18시간이다. 보기의 10–12시간이 야간 주기 주입이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p210]", Q_NIGHT),
            ev(GILA, "PN_jjageuri_summary.md 10 주기주입 [TXT p154]", Q_CYC),
            ev(GILA, "PN_jjageuri_summary.md 6.3 관리", Q_MAN),
        ],
        "choiceExplanations": [
            "오답. 대두유를 늘려 열량을 올리지 않는다. 대두유는 감량하는 쪽이다.",
            "정답. 24시간 연속 대신 10–12시간 주기 주입이다. HPN 야간 주입이 10–12시간으로 적혀 있다.",
            "오답. 지질을 줄인 자리에 포도당을 더 넣지 않는다. 과도한 포도당을 피한다.",
            "오답. 아미노산을 3 g/kg/일로 올리지 않는다. 성인 단백 상한은 2.5 g/kg/일이다.",
        ],
        "reviewNote": OK_NOTE + " 10–12시간은 HPN 야간. 12–18시간도 교재에 있다. 상품명 Omegaven은 교재 문장에 없어 해설에서 뺐다.",
    },
    {
        "id": "bcnsp-085",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [PNALD],
        "errataIds": [],
        "explain": "직접 빌리루빈, ALP, GGT가 오르고 간경변으로 갈 수 있는 것은 담즙정체이다. 정리본은 이 간담도 합병증을 PNALD/IFALD로 적는다. 직접 빌리루빈 ≥2 mg/dL가 담즙정체 정의이다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체", Q_LAB),
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체 [EXAM p186]", Q_DB),
            ev(GILA, "PN_jjageuri_summary.md 6.3 담즙정체", Q_CIRR),
        ],
        "choiceExplanations": [
            "오답. 고중성지방혈증의 표지는 중성지방이다. ALP·GGT·직접 빌리루빈이 아니다.",
            "정답. 그 검사와 간경변 진행은 담즙정체이고, IFALD/PNALD로 부른다.",
            "오답. 재급식증후군은 저인산·저칼륨·저마그네슘이다.",
            "오답. 카테터 혈류감염은 발열과 혈액배양의 문제이다. 이 간효소 조합이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 담즙정체 정의와 간경변 진행. IFALD는 요약의 PNALD/IFALD 이름.",
    },
    {
        "id": "allaccess-008",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 지질 열량 [EXAM p144]", Q_KCAL),
            ev(GILA, "PN_jjageuri_summary.md 지질 열량", Q_FAT10),
        ],
        "choiceExplanations": [
            "오답. 0.02 g/kg/h는 40 g을 43 kg, 12시간으로 나눈 값의 약 1/4이다.",
            "오답. 0.04 g/kg/h는 그 값의 약 절반이다.",
            "정답. 20% 200 mL는 2 kcal/mL로 400 kcal이고, 10 kcal/g로 40 g이다. 40 ÷ 43 ÷ 12 ≈ 0.078 g/kg/h라 가장 가까운 보기는 0.08이다.",
            "오답. 0.16 g/kg/h는 그 값의 약 두 배이다.",
        ],
        "reviewNote": OK_NOTE + " 20% 2.0 kcal/mL와 10 kcal/g. 0.078에 가장 가까운 보기 0.08.",
    },
    {
        "id": "allaccess-009",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LIP],
        "errataIds": [],
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 성인 용량 [EXAM p144]", Q_MAX),
            ev(GILA, "PN_source_textbook_extract.md PDF144", Q_MAX2),
        ],
        "choiceExplanations": [
            "오답. 82 g/일은 1 g/kg이다. 일일 상한이 아니다.",
            "오답. 108 g/일은 2.5 g/kg의 곱이 아니다.",
            "오답. 180 g/일은 82 × 2.5와 다르다.",
            "정답. 일일 상한 2.5 g/kg × 82 kg = 205 g/일이다.",
        ],
        "reviewNote": OK_NOTE + " 교재 일일 ≤2.5 g/kg. 상용 1 g/kg와 상한을 구분했다.",
    },
    {
        "id": "bcnsp-027",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [VIT],
        "errataIds": [],
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 엽산 [TXT p071]", Q_MTX)],
        "choiceExplanations": [
            "오답. 메트포르민이 엽산을 고갈시킨다는 문장은 이 목록에 없다.",
            "정답. MTX는 엽산 결핍을 유발하는 약물로 적혀 있다.",
            "오답. 리시노프릴은 그 목록에 없다.",
            "오답. 오메프라졸은 그 목록에 없다.",
        ],
        "reviewNote": OK_NOTE + " 교재 MTX·trimethoprim·항경련제.",
    },
    {
        "id": "cnsc-nutrition-support-028",
        "answer": 2,
        "referenceIds": [CCN],
        "coreSectionIds": [OB],
        "errataIds": [],
        "explain": "BMI 30–40의 단백은 ≥2.0 g/kg 이상체중/일이고, BMI ≥40은 최대 2.5 g/kg 이상체중/일이다. class I·II는 BMI 30–40이라 보기 중 2.0 g/kg IBW가 그 문장이다.",
        "evidence": [ev(CCN, "CCN Summary 2022 Obesity", Q_PROT)],
        "choiceExplanations": [
            "오답. 0.8 g/kg 실제체중은 이 비만 단백 문장이 아니다.",
            "오답. 실제체중 1.0 g/kg 초과도 그 문장이 아니다. 기준 체중은 IBW이다.",
            "정답. BMI 30–40은 ≥2.0 g/kg IBW/일이다. 보기의 2.0 g/kg IBW가 그 값이다.",
            "오답. 4.0 g/kg IBW는 BMI ≥40의 상한 2.5를 넘는다.",
        ],
        "reviewNote": OK_NOTE + " CCN 2022. 문장은 ≥2.0이다. 4.0과 실제체중 보기와 구분했다.",
    },
    {
        "id": "quizlet-pn-026",
        "answer": 0,
        "referenceIds": [GILA],
        "coreSectionIds": [R31],
        "errataIds": [],
        "explain": "말초 PN의 최종 농도는 아미노산 3–5%, 포도당 5–10%이다. 포도당이 10%를 넘으면 말초 혈전정맥염 위험으로 중심정맥을 쓴다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 3.1 농도", Q_AA),
            ev(GILA, "PN_source_textbook_extract.md PDF143", Q_D10),
        ],
        "choiceExplanations": [
            "정답. 포도당 10%와 아미노산 3%는 말초 농도 범위 안이다.",
            "오답. 포도당 20%는 10%를 넘어 중심정맥 쪽이다.",
            "오답. 아미노산 6%는 말초의 3–5%를 넘는다.",
            "오답. 포도당 20%와 아미노산 6%는 둘 다 말초 범위를 넘는다.",
        ],
        "reviewNote": OK_NOTE + " 말초 농도 AA 3–5% · 포도당 5–10%. D10+AA 3% 예시는 문제은행 표기라 근거로 쓰지 않았다.",
    },
    {
        "id": "bcnsp-066",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [VIT],
        "errataIds": [],
        "explain": "교재 성인 종합비타민 표의 비타민 K는 150 μg이다. 국내 제품에 K가 없는 것은 별도 문장이고, 이 문항은 그 표준 용량을 묻는다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 성인 MVI 표9-11 [TXT p149]", Q_K)],
        "choiceExplanations": [
            "오답. 0 mcg는 국내 종합비타민에 K가 없다는 다른 문장이다. 성인 MVI 표의 표준 용량이 아니다.",
            "정답. 성인 종합비타민의 비타민 K는 150 μg이다.",
            "오답. 1,000 mcg는 그 표의 값이 아니다.",
            "오답. 5,000 mcg는 그 표의 값이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 표9-11 K 150 μg. FDA 승인 제형 귀속은 그 표에 없어 뺐다.",
    },
    {
        "id": "quizlet-pn-021",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [R31],
        "errataIds": [],
        "explain": "PICC의 끝은 상대정맥(SVC)에 둔다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 카테터", Q_PICC)],
        "choiceExplanations": [
            "오답. 요측피정맥은 삽입에 쓰는 말초 정맥이지 카테터 끝이 놓이는 곳이 아니다.",
            "정답. PICC tip은 SVC, 상대정맥이다.",
            "오답. 내경정맥이 PICC 끝의 위치로 적혀 있지 않다.",
            "오답. 쇄골상정맥이 그 끝 위치가 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 정리 PICC tip SVC. 하대정맥까지 끝 위치라고 한 문장은 그 줄에 없어 뺐다.",
    },
    {
        "id": "quizlet-pn-025",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [R31],
        "errataIds": [],
        "explain": "대퇴 카테터로는 PN을 피한다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 카테터 [TXT p174]", Q_FEM)],
        "choiceExplanations": [
            "오답. PICC는 피하라는 접근이 아니다. 끝은 SVC에 둔다.",
            "정답. 대퇴 카테터 PN은 피한다.",
            "오답. 쇄골하 카테터가 대퇴보다 불리하다고 적혀 있지 않다.",
            "오답. 내경정맥이 대퇴 회피 문장의 대상이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 PDF174 대퇴 회피. IHI 번들 귀속은 그 문장에 없어 뺐다.",
    },
    {
        "id": "bcnsp-037",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "errataIds": [],
        "explain": "누공처럼 위장관 손실이 많으면 아연을 더 준다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md Zn 보충 대상", Q_FIST),
            ev(GILA, "PN_jjageuri_summary.md 질환 조정", "설사 ⟶ Zn 보충"),
        ],
        "choiceExplanations": [
            "오답. 고배출 누공에서 더 준다고 적힌 미량원소는 크롬이 아니다.",
            "정답. 누공 고배출에서는 아연을 보충한다.",
            "오답. 셀레늄을 줄이라는 문장은 이 손실의 조정이 아니다. 셀레늄 감량은 신부전 쪽이다.",
            "오답. 구리를 줄이는 것은 담즙정체이다. 누공 손실의 조정이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 누공 고배출 → 아연. 1 L당 12 mg, 1.5 L에서 18 mg은 보유 문장에 없어 뺐다.",
    },
    {
        "id": "bcnsp-049",
        "answer": 1,
        "referenceIds": [GILA],
        "coreSectionIds": [TE],
        "errataIds": [],
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md Zn [TXT p093]", Q_ZNCU),
            ev(GILA, "PN_jjageuri_summary.md Cu [TXT p273]", Q_CU),
        ],
        "choiceExplanations": [
            "오답. 오메프라졸이 고용량 아연처럼 구리 결핍을 만든다는 문장은 없다.",
            "정답. 고용량 아연(≥40 mg/일)은 구리 결핍으로 이어진다. 구리 결핍은 호중구감소와 빈혈이다.",
            "오답. 메트포르민은 그 아연-구리 문장에 없다.",
            "오답. 리시노프릴은 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " 교재 고용량 Zn ≥40 mg/d → Cu 결핍.",
    },
    {
        "id": "bcnsp-067",
        "answer": 1,
        "referenceIds": [GILA, KSHP],
        "coreSectionIds": [VIT],
        "errataIds": [],
        "explain": "장기 기아 뒤 PN을 시작할 때 티아민은 50–100 mg/일을 5–7일 준다. 포도당을 주기 전에 티아민을 보충한다는 문장은 영양약료 강의 해설에 있다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md Vit B1 [TXT p184]", Q_B1),
            ev(KSHP, "영양약료 해설집, 비타민과 전해질", Q_BEFORE),
        ],
        "choiceExplanations": [
            "오답. 비타민 D가 장기 기아 뒤 포도당 전에 주는 비타민으로 적혀 있지 않다.",
            "정답. 티아민(B1)이다. 장기 기아의 PN 초기는 50–100 mg/일 × 5–7일이고, 포도당 전에 보충한다.",
            "오답. 피리독신(B6) 결핍을 유발한다고 적힌 약은 이소니아지드이다. 이 상황의 비타민이 아니다.",
            "오답. 비타민 E가 그 보충 비타민이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 교재 50–100 mg × 5–7일. 해설의 100–300 mg은 그 문장과 달라 뺐다. 인덱스는 유지한다.",
    },
]

BLOCKERS = [
    ("bcnsp-052", "BLOCKER 배치3: 보유 문장은 말단회장 ≥20 cm 절제 → B12 매달 1 mg, 그리고 회장 소실 → 담즙산·B12·지용성 비타민 흡수↓이다. stem은 절제 길이가 없는 '침범'이다. 해설의 60 cm는 교재 20 cm와 다르다. 지용성 비타민(A·K)도 회장 소실 문장에 있다. 인덱스는 유지한다."),
    ("bcnsp-053", "BLOCKER 배치3: 질소평형 식의 '+4 g'은 교재 추출과 요약에 없다. 그 문장을 확보하기 전에는 올리지 않는다. 인덱스는 유지한다."),
    ("rxk-1_3-4", "BLOCKER 배치3: 질소평형 식의 '+4'는 교재 추출과 요약에 없다. bcnsp-053과 같이 둔다. 인덱스는 유지한다."),
    ("bcnsp-030", "BLOCKER 배치3: 조건 없는 '성인 최대 GIR 4–5'이다. 교재는 일반 5–7, 안정 4–5, 고혈당 위험 <4가 갈린다. E2. 인덱스는 유지한다."),
    ("cnsc-nutrition-support-047", "BLOCKER 배치3: stem은 지방증과 고혈당 위험을 함께 묻는데, 고혈당 위험 GIR은 <4이고 정답 보기는 4–5이다. E2. 인덱스는 유지한다."),
    ("bcnsp-012", "BLOCKER 배치3: 성인 최대는 0.11 g/kg/h이고 20% 환산은 약 0.55 mL/kg/h이다. 정답 보기의 괄호는 10% 1 mL/kg/h이고, 0.5 mL/kg/h 보기도 20% 환산에 가깝다. 단위가 한 보기로 닫히지 않는다. 인덱스는 유지한다."),
    ("quizlet-pn-049", "BLOCKER 배치3: 지질유제와 비타민이 함께 INR에 영향이라는 문장은 문제은행 표기이다. 교재에 있는 것은 고용량 비타민 E가 warfarin 작용을 올린다는 문장이다. 인덱스는 유지한다."),
    ("bcnsp-036", "BLOCKER 배치3: Omegaven의 FDA 승인과 상품명 대조는 보유 지침 문장에 없다. ESPEN 소아 지질은 순수 어유를 일반 사용으로 권하지 않고 중증 IFALD의 단기 rescue로만 적는다. 인덱스는 유지한다."),
    ("bcnsp-099", "BLOCKER 배치3: '근거가 가장 확실한' 변경이 상품명 Omegaven이다. ESPEN R4.19의 순수 어유는 증례 보고 수준의 단기 rescue이고, R4.18의 강권고는 대두유 중단·감량 또는 어유 혼합유제이다. 인덱스는 유지한다."),
    ("bcnsp-039", "BLOCKER 배치3: 교재는 장기 기아·알코올에 티아민 50–100 mg을 적는다. 종합비타민 없이 젖산산증과 심기능 장애가 온다는 표현은 그 문장에 없다. 인덱스는 유지한다."),
    ("bcnsp-047", "BLOCKER 배치3: 파킨슨양 망간 독성은 문제은행 표기이다. 교재가 확정한 표현은 복합제 함량이 높아 신경계 독성이라는 쪽이다. 인덱스는 유지한다."),
    ("quizlet-pn-035", "BLOCKER 배치3: 파킨슨병 유사 증상을 망간으로 닫는 문장은 문제은행 표기이다. 인덱스는 유지한다."),
    ("quizlet-iib-006", "BLOCKER 배치3: 떨림·경직의 파킨슨 유사 증상을 망간 독성으로 닫는 문장은 문제은행 표기이다. 인덱스는 유지한다."),
    ("rxk-3_2-2", "BLOCKER 배치3: 용해도 요인으로 적힌 것은 아미노산·pH·칼슘염·온도이다. 동시에 최종 포도당 농도를 높게 유지하라고 하므로, 포도당 농도의 영향이 가장 작다는 보기는 그 문장으로 닫히지 않는다. 인덱스는 유지한다."),
    ("quizlet-pn-011", "BLOCKER 배치3: 라벨 필수 항목에서 빠지는 것이 이온 표기라는 결론은 2014 안전 합의 원문이 있어야 한다. 그 합의는 미보유이고, 해설의 필터 1.2 또는 0.22는 구 표기이다. 인덱스는 유지한다."),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "ext": NOTES / "06_학습_노트/PN_source_textbook_extract.md",
        "myths": NOTES / "06_학습_노트/_gl_extract/ASPEN_Myths_full.txt",
        "cap": NOTES / "06_학습_노트/_gl_extract/ESPEN_CaP_full.txt",
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
        "kshp": NOTES / "06_학습_노트/_kshp_extract.txt",
        "lip": NOTES / "06_학습_노트/_gl_extract/ESPEN_lipids_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_ONE: "sum", Q_SEE: "sum", Q_OPAQUE: "sum", Q_FISH: "sum", Q_MAN: "sum",
        Q_MN: "sum", Q_LA: "sum", Q_FO: "sum", Q_TT: "sum", Q_TTB: "sum", Q_SKIN: "sum",
        Q_DEATH: "sum", Q_EYE: "sum", Q_ADULT: "sum", Q_EXCESS: "sum", Q_LAB: "sum",
        Q_DB: "sum", Q_CIRR: "sum", Q_SLUD: "sum", Q_ORAL: "sum", Q_KCAL: "sum",
        Q_FAT10: "sum", Q_MAX: "sum", Q_MTX: "sum", Q_AA: "sum", Q_K: "sum",
        Q_PICC: "sum", Q_FEM: "sum", Q_ZN: "sum", Q_ZNS: "sum", Q_FIST: "sum",
        Q_ZNCU: "sum", Q_CU: "sum", Q_B1: "sum", Q_NIGHT: "sum", Q_CYC: "sum",
        Q_RAMP: "sum", "설사 ⟶ Zn 보충": "sum",
        Q_BAG: "ext", Q_UNST: "ext", Q_Q6: "ext", Q_REB: "ext", Q_MAX2: "ext", Q_D10: "ext",
        Q_FILT: "myths", Q_PART: "myths",
        Q_ORG: "cap", Q_R87: "cap",
        Q_PROT: "ccn",
        Q_BEFORE: "kshp",
        Q_R418: "lip",
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
