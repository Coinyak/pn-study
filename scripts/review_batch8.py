#!/usr/bin/env python3
"""Batch 8 pending-review promotions.

Fills evidence, choice explanations, and reference ids on items whose keyed
answer is already supported by a held source. Does not change stems, choices,
or answer indexes.

No pending item keys the filter-at-the-hub sentence, separate ILE 12 h versus
TNA 24 h, splitting a longer ILE into two containers, home PN started without
a prior hospital stay, peripheral PN limited to 10–14 days, acute-liver
glucose plus lipid, Child-Pugh ascites/encephalopathy, or grade-2 dysarthria.
Hyperacute liver failure without required amino acids is already verified
as kshp-35. Those sentences were cited on the core table anyway.

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
CONTENT_VERSION = "2026-11-14.10"

GILA = "imsangyoungyang-gilajabi"
KSHP = "kshp-yeongyang-yakryo-lecture-answers"
CCN = "ccn-summary-nestle-2022"
FACT = "aspen-adult-critically-ill-factsheet-2024"
MYTHS = "aspen-pn-myths-practice-tool-2024"
ESPEN_C = "espen-ped-pn-2018-14-complications"
ESPEN_L = "espen-ped-pn-2018-03-lipids"
HPN = "espen-hpn-2020"

EVAL = "sec-eval-0-영양평가-PN-직결만"
IND = "sec-indications-1-적응증-시작시점-지연"
CHO = "sec-cho_gir-2-1-탄수화물-dextrose"
LIP = "sec-lipid-2-2-지방-ILE"
LYTE = "sec-fluid_lytes-2-5-전해질"
ROUTE = "sec-route-3-1-말초-vs-중심"
CAP = "sec-stability-5-2-Ca-P-침전"
BUD = "sec-stability-5-4-필터-hang-time-세트-BUD"
COMP = "sec-complications-6-1-3열-요약"
DIS = "sec-disease-8-질환별-PN"

Q_CLABSI = "all bloodstream infections in patients with a CVC are classified as CLABSI"
Q_COAG = "The major pathogens isolated are Gram-positive coagulase-negative"
Q_PRO = "Suggest prokinetic agents be initiated in patients at high risk of aspiration"
Q_METO = "metoclopramide/erythromycin 등 prokinetic을 고려할 수 있다"
Q_CARN = "Carnitine은 지방산 운반에 관여"
Q_BETA = "less dependency on carnitine for beta-oxidation"
Q_WFH = "Weight-for-height 저하는 현재 체중 소모(wasting), 즉 급성 영양불량"
Q_STUNT = "만성 영양불량은 height-for-age 저하(stunting)"
Q_MATRIX = "matrix table should be sought from the supplier of the formulation detailing permissible limits for additions of electrolytes"
Q_ALT = "alteplase 2 mg/2 ml vs placebo"
Q_TPA = "Tissue plasminogen activator (tPA, alteplase) is currently the recommended agent"
Q_ETOH = "Ethyl alcohol at a 70% solution may be used to dissolve lipid occlusions"
Q_PINCH = "pinch-off syndrome"
Q_RIB = "compression of a CVC between the clavicle and first rib"
Q_ARM = "repeated compression (caused by shoulder and arm movement)"
Q_EDU = "education for users on correct maintenance and safety of the catheter are strongly recommended"
Q_K = "고K·고P·저Ca·대사성 산증"
Q_INS = "regular insulin(+glucose) → Na/K-ATPase로 K 세포내 이동"
Q_BG = "Optimal glycemic control and catheter care are also important factors in the provision of PN to reduce infectious complications"
Q_Q6 = "개시 후 혈당 안정까지 6시간마다"
Q_MED = "PN = 구 USP(pre-2023 중위험)"
Q_IV = "provided through the intravenous administration of nutrients"

OK = {
    "translation": "ok",
    "answerEvidence": "ok",
    "choiceExplanations": "complete",
    "coreLink": "override",
}
OK_NOTE = "배치8 verified. 정답 인덱스 유지."


def ev(ref, locator, quote):
    return {"referenceId": ref, "locator": locator, "quote": quote}


PROMOTIONS = [
    {
        "id": "bcnsp-031",
        "answer": 1,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [COMP, ROUTE],
        "explain": "중심정맥관이 있는 환자의 혈류감염은 다른 원인이 확인되기 전에는 CLABSI로 분류한다. 분리되는 주요 균에 응고효소 음성 포도알균이 들어 있다. 발열·오한과 그 균의 혈액배양은 카테터 관련 혈류감염 쪽이다.",
        "evidence": [
            ev(ESPEN_C, "ESPEN_compl_full.txt CLABSI definition", Q_CLABSI),
            ev(ESPEN_C, "ESPEN_compl_full.txt pathogens", Q_COAG),
        ],
        "choiceExplanations": [
            "오답. 요로감염은 그 혈류감염·응고효소 음성 포도알균 문장이 아니다.",
            "정답. 중심정맥관이 있는 혈류감염은 다른 원인이 없으면 CLABSI이고, 그 주요 균에 응고효소 음성 포도알균이 있다.",
            "오답. 지역사회 폐렴은 그 문장이 아니다.",
            "오답. 자발성 세균성 복막염은 그 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 소아 장부전 문장을 성인 증례에 옮겼다. 균 이름만으로 카테터가 확정 원인이라고 쓰지 않았다.",
    },
    {
        "id": "bcnsp-058",
        "answer": 1,
        "referenceIds": [CCN, KSHP],
        "coreSectionIds": [IND],
        "explain": "흡인 위험이 높으면 prokinetic을 시작한다. 그 예로 metoclopramide와 erythromycin이 적혀 있다. 이 보기에서 그 약물은 metoclopramide다.",
        "evidence": [
            ev(CCN, "CCN_Summary_full.txt aspiration", Q_PRO),
            ev(KSHP, "_kshp_extract.txt 중환자 prokinetic", Q_METO),
        ],
        "choiceExplanations": [
            "오답. ondansetron은 그 prokinetic 예가 아니다.",
            "정답. 흡인 고위험의 prokinetic 예로 metoclopramide가 적혀 있다.",
            "오답. loperamide는 그 문장의 위 배출 촉진제가 아니다.",
            "오답. diphenhydramine은 그 문장에 없다.",
        ],
        "reviewNote": OK_NOTE + " QTc·12주 제한은 이 문장에 없어 넣지 않았다.",
    },
    {
        "id": "bcnsp-075",
        "answer": 1,
        "referenceIds": [KSHP, ESPEN_L],
        "coreSectionIds": [LIP],
        "explain": "카르니틴은 지방산 운반에 관여한다. MCT는 LCT보다 카르니틴 의존이 적은 beta-oxidation을 한다. 항산화, 콜라겐, DNA 보조인자는 그 역할이 아니다.",
        "evidence": [
            ev(KSHP, "_kshp_extract.txt carnitine", Q_CARN),
            ev(ESPEN_L, "ESPEN_lipids_full.txt MCT vs LCT", Q_BETA),
        ],
        "choiceExplanations": [
            "오답. 세포막 항산화는 카르니틴 문장이 아니다.",
            "정답. 카르니틴은 지방산 운반에 관여하고, beta-oxidation과 연결된다.",
            "오답. 콜라겐·상처 치유는 그 문장이 아니다.",
            "오답. DNA 합성 보조인자는 그 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 미토콘드리아 내막·CPT 이름은 인용하지 않았다.",
    },
    {
        "id": "cnsc-nutrition-support-108",
        "answer": 2,
        "referenceIds": [KSHP],
        "coreSectionIds": [EVAL],
        "explain": "Weight-for-height가 낮으면 현재 체중 소모, 곧 급성 영양불량이다. 만성 영양불량은 height-for-age가 낮을 때이고, 그것을 성장지연이라고 한다.",
        "evidence": [
            ev(KSHP, "_kshp_extract.txt 소아 성장", Q_WFH),
            ev(KSHP, "_kshp_extract.txt 소아 성장", Q_STUNT),
        ],
        "choiceExplanations": [
            "오답. 과체중은 weight-for-height 저하 문장이 아니다.",
            "오답. 성장지연은 height-for-age 저하, 곧 만성 쪽이다.",
            "정답. weight-for-height 저하는 소모, 곧 급성 영양불량이다.",
            "오답. 정상 변이는 그 저하 문장이 아니다.",
        ],
        "reviewNote": OK_NOTE + " z-score −2·−3 절단은 이 문장에 없어 인용하지 않았다.",
    },
    {
        "id": "oep-bcscp-q-093",
        "answer": 1,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [CAP],
        "explain": "무기 인산염을 쓰면 안정성 표와 혼합 순서를 지켜야 한다. 그 표는 공급자에게 받아, 전해질과 다른 첨가의 허용 한도를 본다. 섞은 뒤 눈으로만 보거나 속도를 올려 침전을 가리는 방법은 그 문장이 아니다.",
        "evidence": [
            ev(ESPEN_C, "ESPEN_compl_full.txt R14.13", Q_MATRIX),
            ev(ESPEN_C, "ESPEN_compl_full.txt R14.16", "stability matrices and order of mixing must be strictly adhered to"),
        ],
        "choiceExplanations": [
            "오답. 한 시간 관찰만으로 배합 자료를 대신하지 않는다.",
            "정답. 공급자의 허용 한도 표로 칼슘·인산 첨가가 되는지 본다.",
            "오답. 조건과 관계없이 칼슘만 마지막에 넣는 문장은 없다. 표와 순서를 함께 지킨다.",
            "오답. 주입 속도를 올려 침전을 가리라는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-iib-022",
        "answer": 1,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [ROUTE, COMP],
        "explain": "혈전으로 막힌 카테터에는 섬유소 용해제를 쓴다. 현재 권하는 약은 alteplase다. 보유 문장에 alteplase 2 mg/2 mL가 있다.",
        "evidence": [
            ev(ESPEN_C, "ESPEN_compl_full.txt R14.8", Q_TPA),
            ev(ESPEN_C, "ESPEN_compl_full.txt Cochrane", Q_ALT),
        ],
        "choiceExplanations": [
            "오답. 헤파린 100 units/mL는 그 권고 약물이 아니다.",
            "정답. 혈전 폐색의 권고 약물은 alteplase이고, 2 mg/2 mL가 적혀 있다.",
            "오답. 아르가트로반은 그 문장에 없다.",
            "오답. 스트렙토키나제는 현재 권고 약물로 적혀 있지 않다. 권고 약물은 alteplase다.",
        ],
        "reviewNote": OK_NOTE + " FDA 승인 문구와 67–74% 회복률은 인용하지 않았다.",
    },
    {
        "id": "quizlet-iib-025",
        "answer": 1,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [ROUTE, CAP],
        "explain": "70% 에틸알코올은 지질 폐색을 녹이는 데 쓴다. 높은 pH 약물 결정은 중탄산염, 낮은 pH 약물 결정은 염산 쪽이다. 인산칼슘은 그 알코올 문장이 아니다.",
        "evidence": [ev(ESPEN_C, "ESPEN_compl_full.txt lipid occlusion", Q_ETOH)],
        "choiceExplanations": [
            "오답. 인산칼슘은 70% 에탄올 문장이 아니다.",
            "정답. 70% 에틸알코올은 지질 폐색에 쓴다.",
            "오답. 페니토인은 높은 pH 약물 예다. 에탄올 대상이 아니다.",
            "오답. 토브라마이신은 그 지질 폐색 문장에 없다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-iib-026",
        "answer": 1,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [ROUTE],
        "explain": "핀치오프는 카테터가 쇄골과 첫 갈비뼈 사이에서 눌리는 것이다. 어깨와 팔의 움직임이 그 압박을 반복하고, 그 결과 기계적 폐쇄가 생긴다. 팔을 들면 풀리는 간헐 이상은 그 팔 움직임 문장에 해당한다.",
        "evidence": [
            ev(ESPEN_C, "ESPEN_compl_full.txt pinch-off", Q_PINCH),
            ev(ESPEN_C, "ESPEN_compl_full.txt pinch-off", Q_RIB),
            ev(ESPEN_C, "ESPEN_compl_full.txt pinch-off", Q_ARM),
        ],
        "choiceExplanations": [
            "오답. 섬유소 덮개가 팔을 들면 풀린다는 문장은 없다.",
            "정답. 팔·어깨 움직임으로 쇄골과 첫 갈비뼈 사이가 눌려 기계적 폐쇄가 생긴다.",
            "오답. 상대정맥 증후군은 그 압박 문장이 아니다.",
            "오답. 카테터 이동은 그 팔 움직임 압박과 다른 문장이다.",
        ],
        "reviewNote": OK_NOTE,
    },
    {
        "id": "quizlet-iib-034",
        "answer": 3,
        "referenceIds": [ESPEN_C],
        "coreSectionIds": [ROUTE, COMP],
        "explain": "카테터를 고정하고, 사용자에게 올바른 유지와 안전을 교육하라고 한다. 이 보기에서 그 교육은 중심정맥관 유지 관리 교육이다.",
        "evidence": [ev(ESPEN_C, "ESPEN_compl_full.txt R14.11", Q_EDU)],
        "choiceExplanations": [
            "오답. 삽입 전 항생제는 그 교육 문장이 아니다.",
            "오답. 최소 차단 기법은 그 문장에 없다.",
            "오답. 2% 알코올 소독은 그 문장에 없다.",
            "정답. 사용자에게 카테터 유지와 안전을 교육한다.",
        ],
        "reviewNote": OK_NOTE + " 최대 차단·클로르헥시딘은 이 문장에 없어 넣지 않았다.",
    },
    {
        "id": "quizlet-iib-038",
        "answer": 3,
        "referenceIds": [GILA],
        "coreSectionIds": [LYTE, DIS],
        "explain": "신부전의 이상으로 고칼륨과 대사성 산증이 함께 적혀 있다. 인슐린은 칼륨을 세포 안으로 옮기므로 고인슐린은 그 고칼륨 방향이 아니다.",
        "evidence": [
            ev(GILA, "PN_jjageuri_summary.md 8 신부전", Q_K),
            ev(GILA, "PN_jjageuri_summary.md 2.5 고K", Q_INS),
        ],
        "choiceExplanations": [
            "오답. 임신은 그 고칼륨 목록이 아니다.",
            "오답. 인슐린은 칼륨을 세포 안으로 옮긴다.",
            "오답. 호흡부전은 그 고칼륨 목록이 아니다.",
            "정답. 고칼륨과 대사성 산증이 신부전 이상에 함께 있다.",
        ],
        "reviewNote": OK_NOTE + " pH 0.1당 0.6 mEq는 인용하지 않았다.",
    },
    {
        "id": "quizlet-iib-050",
        "answer": 1,
        "referenceIds": [FACT, GILA],
        "coreSectionIds": [COMP, CHO],
        "explain": "혈당 조절과 카테터 관리가 PN의 감염 합병증을 줄이는 요인이다. 보기 중 그 문장에 닿는 것은 카테터 관련 감염이 늘어난다는 항목이다. 혈당은 안정될 때까지 6시간마다 본다.",
        "evidence": [
            ev(FACT, "ASPEN_Fact_full.txt Question 3", Q_BG),
            ev(GILA, "PN_jjageuri_summary.md 2.1 혈당", Q_Q6),
        ],
        "choiceExplanations": [
            "오답. 당뇨 PN 전부를 2시간마다 본다는 문장은 없다. 안정 전까지는 6시간마다다.",
            "정답. 혈당 조절과 카테터 관리가 감염 합병증을 줄이는 요인이다.",
            "오답. 당뇨라는 이유만으로 고단백이 필요하다는 문장은 없다.",
            "오답. 당뇨라는 이유만으로 미량영양소 결핍이 늘다는 문장은 없다.",
        ],
        "reviewNote": OK_NOTE + " 당뇨 진단이 감염을 직접 늘린다는 별도 문장은 없다. 혈당·카테터 문장으로 보기를 닫았다.",
    },
    {
        "id": "quizlet-pn-038",
        "answer": 2,
        "referenceIds": [GILA],
        "coreSectionIds": [BUD],
        "explain": "구 USP에서 PN은 중위험으로 적혀 있다. 그 칸이 위험 없음, 저위험, 고위험은 아니다.",
        "evidence": [ev(GILA, "PN_jjageuri_summary.md 5.4 BUD", Q_MED)],
        "choiceExplanations": [
            "오답. 구 USP의 PN 칸은 위험 없음이 아니다.",
            "오답. 저위험은 그 PN 칸이 아니다.",
            "정답. 구 USP에서 PN은 중위험이다.",
            "오답. 고위험은 그 PN 칸이 아니다.",
        ],
        "reviewNote": OK_NOTE + " 현행 Category 1–3과 ISO Class 5는 이 문장에 없어 넣지 않았다.",
    },
    {
        "id": "rxk-1_1-4",
        "answer": 1,
        "referenceIds": [HPN],
        "coreSectionIds": [IND, ROUTE],
        "explain": "PN은 영양소를 정맥으로 주는 치료다. 비위관·비십이지장관·비공장관은 그 정맥 투여가 아니고, 야간만 주는 것도 정의가 아니다.",
        "evidence": [ev(HPN, "ESPEN_HPN_full.txt introduction", Q_IV)],
        "choiceExplanations": [
            "오답. 중심정맥을 못 쓸 때의 보조는 PN의 정의가 아니다.",
            "정답. PN은 영양소를 정맥으로 투여한다.",
            "오답. 관으로 장에 공급하는 것은 경장영양이다.",
            "오답. 야간에만 주는 것은 정의가 아니라 주입 시간이다.",
        ],
        "reviewNote": OK_NOTE + " TPN이라는 말은 경로를 숨긴다. 정답 보기는 정맥 투여라 인덱스는 유지한다.",
    },
]


BLOCKERS = [
    (
        "quizlet-iib-037",
        "BLOCKER 배치8: 필터를 카테터 허브에 가깝게 둔다는 문장과, 터널형 카테터의 감염 경로가 허브 오염이라는 문장은 다르다. 후자의 CDC 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-024",
        "BLOCKER 배치8: PICC를 감염원으로 의심·확인될 때만 제거한다는 CDC 문장을 보유 지침 추출에서 확인하지 못했다. 핵심표의 그 한 줄은 출처가 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-013",
        "BLOCKER 배치8: 낮은 pH 약물 결정에는 염산, 높은 pH 약물에는 중탄산염, 지질 폐색에는 70% 에탄올이다. 0.1N 염산의 대상이 인산칼슘이라는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-023",
        "BLOCKER 배치8: 고름이 없으면 출구 감염은 국소 항균제다. 전신 항생제와 카테터 제거는 터널·포트 감염 문장이다. 출구 고름의 정답이 전신 항균제 하나로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-032",
        "BLOCKER 배치8: 주입은 되고 흡인이 안 되는 섬유소 덮개 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-005",
        "BLOCKER 배치8: 피하 인슐린의 기저-볼루스 문장은 퀴즈 재게시에만 있다. 보유 지침 추출에는 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-036",
        "BLOCKER 배치8: 지용성 비경구 권장이 경구 DRI와 같다는 칸은 핵심표에만 있고 요약·강의 추출·지침 문장에는 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-037",
        "BLOCKER 배치8: 수용성 비경구 권장이 경구보다 높다는 칸은 핵심표에만 있고 요약·강의 추출·지침 문장에는 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-040",
        "BLOCKER 배치8: 크리밍이 재분산되고 크래킹은 투여하지 않는다는 문장은 있다. 표면에 반투명한 띠로 보인다는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-pn-043",
        "BLOCKER 배치8: 산증의 보유 조치는 acetate다. 칼륨을 나트륨·염소·마그네슘보다 더 면밀히 본다는 문장은 없고, pH 0.1당 0.6 mEq도 없다. 인덱스는 유지한다.",
    ),
    (
        "quizlet-iib-028",
        "BLOCKER 배치8: 난치성 저칼륨에서 마그네슘을 본다는 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-018",
        "BLOCKER 배치8: 만성 마그네슘 결핍이 저칼슘과 같이 온다는 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-062",
        "BLOCKER 배치8: QTc 연장의 원인이 저마그네슘이라는 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-088",
        "BLOCKER 배치8: 저마그네슘이 저칼륨·저칼슘 교정을 막는다는 문장은 보유 추출에 없다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-032",
        "BLOCKER 배치8: 6특징 중 최소 2개라는 합의 원문은 미보유다. 인덱스는 유지한다.",
    ),
    (
        "bcnsp-060",
        "BLOCKER 배치8: 6특징의 중증 기준을 닫는 합의 원문은 미보유다. 1개월 5% 초과 체중 감소만으로 그 문항을 올리지 않는다. 인덱스는 유지한다.",
    ),
    (
        "allaccess-002",
        "BLOCKER 배치8: 구역·구토·팽만·설사는 경장영양 합병증으로 적혀 있다. 위 끝이어서 설사가 해당 없다는 정답과 그 문장이 충돌한다. 인덱스는 유지한다.",
    ),
    (
        "medex-001",
        "BLOCKER 배치8: 혈청 칼륨 정상은 3.5–5.0 mEq/L다. 6.1에서 조제 보류 후 처방자와 확인하라는 절차 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "medex-002",
        "BLOCKER 배치8: 고칼륨에서 potassium phosphate를 빼고 확인하라는 절차 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "medex-019",
        "BLOCKER 배치8: 집에서 PN을 시작할 수 있다는 조건은 정책·적격·프로토콜·평가다. 표준 제형과 주 1회 방문이 그 문장으로 닫히지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-4_1-1",
        "BLOCKER 배치8: 안전한 재택 PN에는 동의와 보호자의 수행 능력이 있다. 보험 보장까지 모두 해당으로 닫는 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "rxk-2_1-1",
        "BLOCKER 배치8: MCT가 LCT보다 혈장에서 빨리 빠지고 산화된다는 문장은 정맥 지질유제다. 경장 기름의 소화·흡수 순서를 닫지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rx-pn-indication-enteral",
        "BLOCKER 배치8: EN이 목표를 못 채우면 PN이다. 수액 용량을 견딜 수 있어야 한다는 조건은 그 문장에 없다. 모두 해당으로 올리지 않는다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_2-3",
        "BLOCKER 배치8: 패혈증은 이화·영양불량 위험 쪽이다. 위험인자가 아니라는 정답과 충돌한다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_3-1",
        "BLOCKER 배치8: 삼두 피부두겹은 피하지방 평가에 들어간다. 영양평가에서 뺀다는 정답과 충돌한다. 인덱스는 유지한다.",
    ),
    (
        "rxk-1_3-7",
        "BLOCKER 배치8: 성인 수액은 30–40 mL/kg/일이다. 1–2 mL/kcal 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-006",
        "BLOCKER 배치8: BMI 27.8은 보유 계산 예제 네 가지가 아니다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-009",
        "BLOCKER 배치8: 여성 이상체중은 키(m)²×21이다. Hamwi 5 feet 100 lb 문장은 없다. 인덱스는 유지한다.",
    ),
    (
        "cnsc-nutrition-support-072",
        "BLOCKER 배치8: 1,800 kcal를 1.2 kcal/mL로 24시간에 나누는 63 mL/h는 보유 계산 예제가 아니다. 인덱스는 유지한다.",
    ),
    (
        "allaccess-006",
        "BLOCKER 배치8: Harris-Benedict로 1.4 L를 고르는 계산은 보유 예제 네 가지가 아니다. 인덱스는 유지한다.",
    ),
    (
        "medex-003",
        "BLOCKER 배치8: 0.9% 식염 1 L의 9 g은 보유 계산 예제가 아니다. 인덱스는 유지한다.",
    ),
]


def _norm(text):
    text = text.replace("**", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return re.sub(r"\s+", "", text)


def verify_quotes():
    files = {
        "sum": NOTES / "06_학습_노트/PN_jjageuri_summary.md",
        "kshp": NOTES / "06_학습_노트/_kshp_extract.txt",
        "ccn": NOTES / "06_학습_노트/_gl_extract/CCN_Summary_full.txt",
        "fact": NOTES / "06_학습_노트/_gl_extract/ASPEN_Fact_full.txt",
        "compl": NOTES / "06_학습_노트/_gl_extract/ESPEN_compl_full.txt",
        "lip": NOTES / "06_학습_노트/_gl_extract/ESPEN_lipids_full.txt",
        "hpn": NOTES / "06_학습_노트/_gl_extract/ESPEN_HPN_full.txt",
        "spn": NOTES / "06_학습_노트/_gl_extract/ASPEN_SPN_full.txt",
        "myths": NOTES / "06_학습_노트/_gl_extract/ASPEN_Myths_full.txt",
    }
    if not NOTES.is_dir():
        print(f"quote check skipped: {NOTES} not found")
        return
    blob = {k: _norm(p.read_text(encoding="utf-8")) for k, p in files.items()}
    need = {
        Q_CLABSI: "compl",
        Q_COAG: "compl",
        Q_PRO: "ccn",
        Q_METO: "kshp",
        Q_CARN: "kshp",
        Q_BETA: "lip",
        Q_WFH: "kshp",
        Q_STUNT: "kshp",
        Q_MATRIX: "compl",
        "stability matrices and order of mixing must be strictly adhered to": "compl",
        Q_ALT: "compl",
        Q_TPA: "compl",
        Q_ETOH: "compl",
        Q_PINCH: "compl",
        Q_RIB: "compl",
        Q_ARM: "compl",
        Q_EDU: "compl",
        Q_K: "sum",
        Q_INS: "sum",
        Q_BG: "fact",
        Q_Q6: "sum",
        Q_MED: "sum",
        Q_IV: "hpn",
        "Peripheral PN should only be used for no more than 10–14 days": "spn",
        "Place the inline filter closest to the catheter hub.": "myths",
        "the daily dose may be divided into two equal containers.": "myths",
        "Adult patients can have PN safely initiated in the home setting": "myths",
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
