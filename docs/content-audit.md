# 콘텐츠 감사 (Task 1: 공식 범위 대조와 문헌 확보표)

작성 기준: 2026-11-14 (KST) · 대상 스냅샷: `PN_study_split.html` @ `91b1e3b`
관련 데이터: [`content/exam-scope.json`](../content/exam-scope.json) · [`content/references.json`](../content/references.json)

이 문서는 **임상 정오표가 아니다.** 학습 사이트가 공식 시험범위를 어디까지 다루는지, 지정 문헌을 실제로 갖고 있는지를 기록한다. 임상 수치의 옳고 그름 판정은 Task 2의 몫이며, 이 문서는 어떤 수치도 확정하지 않는다.

## 1. 기준 공지 (확인일·URL)

| 항목 | 내용 |
|---|---|
| 확인일 | **2026-11-14** (한국 시간) |
| 공식 URL | <https://exam.kshp.or.kr/sub/guide/guide_03_6.asp> (한국병원약사회 2026년도 제4회 전문약사 자격시험, 정맥영양) |
| 구성 | 공통영역(의학통계·의약논문비평) 객관식 20문항 × 1점 + 전문영역(정맥영양) 객관식 80문항 × 1점 |
| 시간 | 총 180분. 시험 준비·안내·공지 시간 포함이므로 순수 풀이 시간으로 단정하지 않음 |
| 공지에 없는 것 | 세부 단원별 문항 수·출제빈도·난이도. 이 저장소의 어떤 우선순위도 공식 비중이 아님 |
| 비고 | 전문영역 범위의 '영양소–약물 상호작용'은 **정맥영양 이외의 일반적인 영양소–약물 상호작용을 포함**한다고 공지에 명시돼 있다. 이전의 "PN 밖 내용은 부록" 제안은 철회 |

공지의 출제범위·출제유형 22줄(공통 4 + 전문 13 + 출제유형 5)은 `exam-scope.json`의 `meta.officialLines`에 원문 그대로 보관했고, 모든 줄이 최소 1개 scope 행에 연결된다. 한 줄이 여러 항목을 묶은 경우(질환 나열 등)는 항목별로 행을 나눴다.

## 2. 판정 기준과 한계

- `covered`: 핵심표 전용 단락 + **검증 완료 문항** + 지정 문헌 **장·쪽 추적**이 모두 있을 때만. **이번 감사에서 `covered`인 행은 0개다.** 문항 검증(Task 2)과 지정 문헌 대조가 아직 없기 때문이다.
- `partial`: 핵심표에 전용 단락/행이 있으나 범위 일부이거나 임상 내용·문항·원문 대조가 끝나지 않음.
- `missing`: 전용 핵심표·문항이 없음. 한 줄 언급·단편 수치는 충족으로 치지 않음.
- 키워드가 HTML에 있다는 이유만으로 상태를 올리지 않았다. 핵심표(`sec-*`)를 읽고 판정했다.
- 문항 단위 매핑은 §9의 키워드·주제 휴리스틱 v1(`questionMapping: keyword-heuristic-v1`)로만 수행했다. 문항 정답·내용 검증은 아니며, 매핑 건수가 있어도 `covered`로 올리지 않았다. `questionTopicKeys`는 기존 UI의 문항 주제 키(eval, route 등)다.
- `PN_study_split.html`의 `const QUESTIONS` 배열: 총 583건(ID 583종, 중복 없음) — eval 75, route 72, monitor 65, fluid_lytes 44, lipid 40, cho_gir 38, calc_filter 37, complications 37, disease 37, indications 32, stability 28, vit_te 28, hpn 24, protein 22, peds 4. 배열은 `const`이며 파일 내 후처리(push/splice/재할당)가 없고, 화면 표시 목록은 `QUESTIONS.filter(q => q.topic === activeTopic)`이므로 최종 표시 ID = 이 583건이다(확인: 참조 4곳 = 정의 1 + filter 2 + find 1). `index.html`·`PN_core_A4_print.html`에는 문항 배열이 없다.

## 3. Coverage 요약

| coverage | 행 수 |
|---|---|
| covered | 0 |
| partial | 25 |
| missing | 13 |
| unreviewed | 0 |
| **합계** | **38** |

영역별: 공통 {'missing': 4} · 전문 {'partial': 23, 'missing': 6} · 출제유형 {'missing': 3, 'partial': 2}

핵심 해석:

1. **공통영역 4개 행은 전부 `missing`.** 핵심표·문항이 없고 지정 교재도 미확보다. 보유 CMAJ EBM 3편은 공지 지정 문헌이 아니므로 보조로만 쓴다.
2. 질환 영역에서 **폐·심장·신경계·수술·임부·노인은 `missing`**, 당뇨·비만·화상·섭식장애·암은 단편이거나 짧은 행이라 `partial`로 두되 갭을 명시했다.
3. 성분·평가·요구량·계산·경로·합병증·모니터링·HPN·소아는 내용이 풍부하지만 출처가 지정 문헌이 아니라 『임상영양길라잡이』(6절 참고)라서 `partial`이다.
4. 국내 PN 제품 비교표와 처방 검토·DRP·환자 교육 사례는 아직 없다.

## 4. 행별 대조표

핵심표 열은 `sec-<주제>-<번호>` 형식의 HTML 섹션 ID를 줄여 쓴 것이다(전체 ID는 JSON의 `topicIds`).

| scope id | 공식 항목 | coverage | 핵심표 | 문항 키 | 갭 |
|---|---|---|---|---|---|
| `common-ebm-ebcp` | EBM·EBCP 이해 | missing | — | — | 핵심표·문항 모두 없음(핵심표 본문에 EBM/NNT/RRR/신뢰구간 용어 0건). 지정 교재(Users' Guides 3판 등)는 미확보. 보유 CMAJ EBM 시리즈 3편은 공지 지정 문헌이 아니므로 보조 자료로만 사용. 단원 신설은 Task 3. |
| `common-literature-types` | 의약문헌의 종류·특징 | missing | — | — | 전용 단원·문항 없음. 지정 교재(Malone Drug Information 7판, 약료정보학 Section III 제9–13·16장)는 미확보라 장·쪽 확인 대기. |
| `common-clinical-statistics` | 임상통계 기본 개념 | missing | — | — | 전용 단원·문항 없음. 효과지표(RRR/ARR/NNT)·신뢰구간은 보유 CMAJ 2편이 있으나 아직 어떤 핵심표에도 반영되지 않음. 교재 장·쪽(DiCenzo 2판, Browner 5판, 임상실무약학 27·29장 등) 확인 대기. |
| `common-appraisal-application` | 논문 해석·비평·임상적용 | missing | — | — | 전용 단원·문항 없음. 영양지원 논문(보유 OA 논문 4편 등)을 이용한 해석 사례는 아직 없음. 공통영역 문항은 검증 가능한 원문 확보 전 작성하지 않는다. |
| `spec-components` | 영양공급 구성 성분의 특징 | partial | cho_gir 2, cho_gir 2.1, lipid 2.2, protein 2.3, fluid_lytes 2.4, fluid_lytes 2.5, vit_te 2.6, vit_te 2.7 | cho_gir, lipid, protein, fluid_lytes, vit_te | 탄수화물·지질·AA·수분·전해질·비타민·TE 소단원이 있으나 값은 임상영양길라잡이 OCR/형광 중심이고 지정 문헌(성인 Core 4판) 장·쪽 대조는 안 됨. 조건부 필수 AA·MCT/어유 제제 비교·비타민 제제별 조성 등 심화 내용 미확인. GIR·dextrose kcal/g 등 수치 충돌 후보는 Task 2에서 검증. |
| `spec-assessment` | 영양상태 평가 | partial | eval 0 | eval | IC/Weir, 체중감소 기준, NRS-2002·NUTRIC, AND/ASPEN 영양불량 진단, 알부민·prealbumin 항목이 있음. prealbumin 해석(염증지표 vs 영양지원 모니터)과 소아·노인·비만 평가는 원문 대조 전. 신체계측·근감소 평가 도구(GLIM 등) 서술 여부 미확인. |
| `spec-requirements` | 영양요구량 산정 | partial | calc_filter 4.1, protein 2.3, fluid_lytes 2.4 | calc_filter, protein, fluid_lytes | 에너지(TEE=BEE×AF×SF)·단백·수분 요구량 값이 있으나 성인 일반/중환자/비만/신부전/소아 등 환자군별 값이 한 표에 혼재. 환자군·연도·권고문을 나란히 놓은 비교는 아직 없음(Task 2·3). |
| `spec-plan-personalized` | 환자맞춤형 영양지원계획(처방 검토·선택) | partial | calc_filter 4, indications 1, route 3 | calc_filter, indications, route | 적응증·시작 시점·경로·계산 흐름은 있으나 환자 사례 기반 처방 검토·DRP 해결 훈련 콘텐츠는 없음. 상위 항목이라 하위 S2c1·S2c2와 함께 판단. |
| `spec-plan-calc` | 영양공급량 계산 | partial | calc_filter 4, calc_filter 4.1, calc_filter 4.2, calc_filter 4.3, calc_filter 4.4, cho_gir 2.1 | calc_filter, cho_gir | 계산 5단계·삼투압·교정 공식 예제 있음. 예제 내부에서 dextrose를 3.85 kcal/g(교재 예제)와 3.4 kcal/g(본문 기본)로 혼용해 결과가 달라지는 점이 명시돼 있어 Task 2에서 근거 확정 필요. 문항 단위 계산 검증 미실시. |
| `spec-plan-route` | 투여경로 선택·주입 | partial | route 3, route 3.1, route 3.2, route 3.3, stability 5.4, hpn 10 | route, calc_filter, stability | 말초 vs 중심, 2-in-1 vs 3-in-1, MCB, 필터, 주입 시간은 있음. 접근기구(CVC/PICC/port) 선택·관리는 HPN 단락에 일부만, ASPEN CVAD 2019는 미확보. 필터 구/현행 서술 충돌과 BUD 숫자 누락은 Task 2. |
| `spec-dz-renal` | 신부전 | partial | disease 8 | disease | 질환별 PN 소단원 안의 신부전 블록(AKI/CKD/HD/PD/CRRT/IDPN 값). ESPEN 2021 신질환 지침 미확보. 최신 ESPEN 2024 AKI 단백 91–105 g/d와 강의자료 84 g/d 불일치가 기존 노트에 있음(Task 2). |
| `spec-dz-liver` | 간질환 | partial | disease 8, vit_te 2.7, complications 6.3 | disease, vit_te, complications | 질환별 PN 소단원 안의 급·만성 간질환·HE·Child-Pugh 블록 + PNALD·TE(Cu/Mn 담즙정체) 일부. ESPEN 2019 간질환 지침 미확보. |
| `spec-dz-gi` | 위장관질환 | partial | disease 8 | disease | 췌장염·크론/IBD·장부전·SBS 블록이 있음. 장피누공(ASPEN-FELANPE 2017 지정), 위마비, 흡수장애, 수술 후 장폐색 등은 전용 내용 없음. ESPEN 췌장염 2020·IBD 2023·CIF 지침 미확보. |
| `spec-dz-lung` | 폐질환 | missing | — | — | 전용 내용 없음(COPD·호흡부전 용어 0건; 재급식의 '호흡 증상', 지질/CO2 언급 정도). 호흡계수·과다 열량 CO2 생성·ARDS 영양 등은 성인 Core 4판 해당 장 확인 후 작성. |
| `spec-dz-heart` | 심장질환 | missing | — | — | 전용 내용 없음(심부전·심장 용어 0건). 수분·나트륨 제한, 심장악액질 등은 원문 확인 후 작성. |
| `spec-dz-neuro` | 신경계질환 | missing | — | — | 전용 내용 없음(뇌졸중·삼킴장애·TBI 등 0건). 간성뇌증(HE)은 간질환 행, thiamine/Wernicke는 재급식·비타민 일부로만 존재. |
| `spec-dz-diabetes` | 당뇨 | partial | cho_gir 2.1, monitor 7.1 | cho_gir, monitor | PN 중 고혈당 관리(BG 140–180, 인슐린, GIR)만 있고 당뇨 환자 영양지원 전반(당뇨 특화 제형·경구 혈당강하제 조정·저혈당 관리)은 없음. ASPEN 고혈당 2013 지침은 미확보. |
| `spec-dz-obesity` | 비만 | partial | protein 2.3, calc_filter 4.1 | protein, calc_filter | 중환자 비만 단백·에너지 값(ASPEN 2016/ESPEN 2019 비교) 한두 줄만 있음. 비만 일반·대사수술 후 영양은 없음. |
| `spec-surgery` | 수술 | missing | indications 1, calc_filter 4.1 | indications, calc_filter | '수술 전후' 적응증 한 줄과 스트레스계수(수술 1.44)뿐. 수술 전후 영양·ERAS·면역영양은 없음. ESPEN 수술 2017 미확보. |
| `spec-cancer` | 암 | partial | disease 8 | disease | 질환별 PN 소단원에 '암(non_PN, 짧게)' 요약 행(단백·지방 비율)만 있음. 악액질·방사선·항암 관련 합병증·말기 영양은 없음. ESPEN 암 2021 미확보. |
| `spec-critical-care` | 중환자 | partial | disease 8, indications 1, protein 2.3 | disease, indications, protein | 중환자 블록(NUTRIC, GIR≤4, 단백 1.2–2.0, SPN day 7, ILE 첫주)이 있음. ASPEN 2022 원문은 유료 미확보(공개 Factsheet·요약본만 보유). SCCM/ASPEN 소아 중환자 2017 미확보. |
| `spec-burn` | 화상 | partial | cho_gir 2.1, protein 2.3, calc_filter 4.1 | cho_gir, protein, calc_filter | 독립 단원 없이 GIR ≤5, 스트레스 계수(화상 2.1–2.5), 단백 1.5–2.0 등 단편 값만 흩어져 있음. 화상 에너지식·미량원소·글루타민 등은 없음. |
| `spec-eating-disorder` | 섭식장애 | partial | complications 6.2, indications 1 | complications, indications | 신경성 식욕부진은 재급식 고위험군·적응증 한 줄로만 등장. 재급식 소단원(P·K·Mg↓, thiamine, 천천히 증량)은 있으나 섭식장애 전용 영양지원은 없음. ASPEN Refeeding 2020 유료 미확보. |
| `spec-pregnancy` | 임부 | missing | indications 1 | indications | 임신성 과다구토 적응증 한 줄, 양의 질소평형, 임신 중 엽산 결핍 언급 정도. 임부 영양요구량·임신성 당뇨·임신 중 PN은 없음. |
| `spec-neonate` | 신생아 | partial | peds 9 | peds | 소아·신생아 소단원에 신생아 GIR/지질/단백/Ca·P/TE 값이 있음(주로 ESPEN 2018 값 병기). 원시 문항 배열 중 peds 키는 4건뿐. ASPEN Pediatric Core 2판 미확보. |
| `spec-preterm` | 미숙아 | partial | peds 9 | peds | 미숙아 단백/TE/Ca·P 값이 소아 소단원에 일부 있음. ASPEN 미숙아 2023(JPEN 47:830–858) 원문은 유료 미확보라 신·구 권고 비교 불가. |
| `spec-pediatric` | 소아 | partial | peds 9 | peds | 소아 GIR(교재 5–13 vs ESPEN 병기표)·지질·단백·NPC:N·성장평가 일부. 교재 압축식과 ESPEN 표가 불일치로 기록돼 있음. 소아 중환자(SCCM/ASPEN 2017)·소아 질환별 PN은 없음. |
| `spec-elderly` | 노인 | missing | — | — | 노인 전용 내용 없음(TBW 계수 '고령' 구분만). 노인 영양요구량·삼킴·약물 동반·재급식 위험 등 없음. ESPEN 노인 2019 미확보. |
| `spec-hpn` | 재택영양 | partial | hpn 10 | hpn | 적응·접근로·주기주입·모니터(표19-7)·CVC 감염 치료·MBD·IFALD가 있고 보유 ESPEN HPN 2020과 일부 대조됨(값 단위 중심). 환자 교육(보관·주입·무균·이상 징후)·재택 EN은 부족. ASPEN CVAD 2019 미확보. |
| `spec-monitoring` | 영양지원 효과·합병증 모니터링 | partial | monitor 7, monitor 7.1, monitor 7.2, monitor 7.3, complications 6, complications 6.2, complications 6.3, complications 6.4, lipid 6.5 | monitor, complications | 모니터링 표·Lab 정상범위·PN 중단 이행·재급식·PNALD·MBD·EFAD는 있음. 효과지표(prealbumin 등)·소아 합병증 대조는 원문 확인 전. 문항 수(원시 배열 monitor 65, complications 37)와 무관하게 임상 검증 전. |
| `spec-ddi-nutrient-drug` | 영양소–약물 상호작용(일반 포함) | partial | disease 8, vit_te 2.6 | disease, vit_te | EN–약물(phenytoin·warfarin·튜브 세척) 짧은 블록과 약물 유발 엽산 결핍 등 일부만 있고, '정맥영양 이외의 일반 상호작용'(식품·경장 포함)은 핵심표에서 사실상 비어 있음. 공식 범위가 일반 상호작용을 포함한다고 명시. |
| `spec-compatibility` | PN compatibility(배합성) | partial | stability 5.3, stability 5.2, stability 5.1, route 3.2 | stability, route | 혼합 순서·Ca–P 침전·Y-site 금기 표가 있으나 ASPEN PN compatibility 2022 유료 원문 미확보. 3-in-1 vs 2-in-1 데이터 외삽 금지 문구는 있음. 약물별 근거 확인 전. |
| `spec-products-stability` | PN 제품 특징·안정성 | partial | route 3.3, route 3.2, stability 5.4, stability 5, lipid 2.2, vit_te 2.7, vit_te 2.6 | route, stability, lipid, vit_te | 제품명은 Furtman·Smoflipid 20%·Nutriflex lipid 10% 등 단편 언급뿐이고, 국내 허가 제품별 조성·용량 규격·확인일 표는 없음(Task 3에서 허가자료 확인 후 작성). 안정성 규칙(필터·hang time·BUD)은 있으나 BUD 일부 숫자 누락이 확인돼 있음. |
| `format-appropriateness` | 약물요법 적절성 검토(처방 검토) | missing | — | — | 처방 검토 사례형 콘텐츠 없음(치트 블록은 수치 암기). 출제유형이므로 Task 3에서 처방 검토 사례를 추가. |
| `format-drp` | DRP 파악·해결 | missing | — | — | DRP 사례 없음. PN 안전 체크리스트(보유 ASPEN 4종)를 사례 설계 근거 후보로만 확인. |
| `format-selection-plan` | 환자 맞춤형 약물 선택·약물요법 계획 | partial | calc_filter 4 | calc_filter | 계산·조성 선택 표는 있으나 환자 사례형 선택·계획 훈련은 없음(S2c와 동일 한계). |
| `format-monitoring` | 치료효과·이상반응 모니터링 | partial | monitor 7, monitor 7.1 | monitor | S4(모니터링·합병증) 행과 동일한 내용으로 판단. 사례형 해석 없음. |
| `format-patient-education` | 환자 교육 | missing | hpn 10 | hpn | 환자 교육 전용 내용 없음. HPN 단락에 접근기구·flush 등 실무 사실은 있으나 교육 시나리오·설명 포인트는 아님. |

## 5. 문헌 확보 현황

총 81행. 확보 상태: {'public-url': 3, 'not-held': 23, 'have-pdf': 42, 'paywalled-unreviewed': 11, 'have-extract': 2}.
공지가 이름으로 열거한 항목은 33행이며 그중 확보 상태는 {'public-url': 3, 'not-held': 14, 'have-pdf': 5, 'paywalled-unreviewed': 11}.

| 구분 | 상태 |
|---|---|
| 보유 PDF/추출문 | ESPEN HPN 2020, ESPGHAN/ESPEN/ESPR/CSPEN 2018 소아 PN 14편(공지가 열거한 5개 항목 중 에너지·비타민·표준 vs 개별화·합병증 4편 + 총칭 항목에 대응하는 개요 후보 1편 포함), ASPEN 공개 자료 15종, CMAJ EBM 3편 |
| 공지 지정이나 미보유 | ASPEN 성인 Core 4판(2025), ASPEN 소아 Core 2판(2015), 공통영역 교재 11종, ASPEN 학회지 지침·합의 11종 |
| 공지 지정이나 서지 불명 | "ASPEN guidelines on adult parenteral nutrition for specific diseases" (공지에 서지 없음) |
| 지정 아님·참고 | 해외 시험 자료(BCNSP·CNSC), 제조사 요약, 영양약료 강의 정답집, 문제 PDF 등 |

기존 노트가 2026-11-13에 추출본으로 일부 수치만 대조한 문헌은 `reviewScope: partial-values`로 표시했다. 그 외 보유 PDF는 `reviewedAt: null`이며 전권 검토를 주장하지 않는다.

### 5.1 미확보 문헌 (not-held / paywalled-unreviewed)

| id | 제목 | 연도 | 상태 | 구분 |
|---|---|---|---|---|
| `aspen-adult-core-4e-2025` | The A.S.P.E.N. Adult Nutrition Support Core Curriculum, 4th ed. | 2025 | not-held | 공지 지정 |
| `espen-icu-2019` | ESPEN guideline on clinical nutrition in the intensive care unit | 2019 | not-held | 후보 |
| `espen-liver-2019` | ESPEN practical guideline: Clinical nutrition in liver disease | 2019 | not-held | 후보 |
| `espen-surgery-2017` | ESPEN guidelines: Clinical nutrition in surgery | 2017 | not-held | 후보 |
| `espen-cancer-2021` | ESPEN practical guideline: Clinical nutrition in cancer | 2021 | not-held | 후보 |
| `espen-geriatrics-2019` | ESPEN guideline on clinical nutrition and hydration in geriatrics | 2019 | not-held | 후보 |
| `espen-kidney-2021` | ESPEN guideline on clinical nutrition in hospitalised patients with acute or chronic kidney disease | 2021 | not-held | 후보 |
| `espen-pancreas-2020` | ESPEN practical guideline: Clinical nutrition in acute and chronic pancreatitis | 2020 | not-held | 후보 |
| `espen-ibd-2023` | ESPEN practical guideline on clinical nutrition in inflammatory bowel disease | 2023 | not-held | 후보 |
| `espen-cif-2016` | ESPEN guidelines on chronic intestinal failure in adults | 2016 | not-held | 후보 |
| `aspen-ped-core-2e-2015` | The A.S.P.E.N. Pediatric Nutrition Support Core Curriculum, 2nd ed. | 2015 | not-held | 공지 지정 |
| `aspen-adult-disease-pn-guidelines` | ASPEN guidelines on adult parenteral nutrition for specific diseases (공지 표기 그대로) | — | not-held | 공지 지정 |
| `aspen-preterm-pn-2023` | Guidelines for parenteral nutrition in preterm infants: The American Society for Parenteral and Enteral Nutrition. JPEN 2023;47:830-858 | 2023 | paywalled-unreviewed | 공지 지정 |
| `aspen-adult-critically-ill-2022` | Guidelines for the provision of nutrition support therapy in the adult critically ill patient: ASPEN. JPEN 2022;46:12-41 | 2022 | paywalled-unreviewed | 공지 지정 |
| `aspen-pn-compat-2022` | Parenteral Nutrition Compatibility and Stability: A Comprehensive Review. JPEN 2022;46(2):273-299 | 2022 | paywalled-unreviewed | 공지 지정 |
| `aspen-ile-safety-part1-2020` | ASPEN Lipid Injectable Emulsion Safety Recommendations, Part 1: Background and Adult Considerations. NCP 2020;35(5):769-782 | 2020 | paywalled-unreviewed | 공지 지정 |
| `aspen-refeeding-2020` | ASPEN Consensus Recommendations for Refeeding Syndrome. NCP 2020;35:178-195 | 2020 | paywalled-unreviewed | 공지 지정 |
| `aspen-cvad-hpn-2019` | The Selection and Care of Central Venous Access Devices for Adult Home Parenteral Nutrition Administration. JPEN 2019;43(1):15-31 | 2019 | paywalled-unreviewed | 공지 지정 |
| `sccm-aspen-ped-critical-2017` | Guidelines for the Provision and Assessment of Nutrition Support Therapy in the Pediatric Critically Ill Patient: SCCM and ASPEN. JPEN 2017;41:706-742 | 2017 | paywalled-unreviewed | 공지 지정 |
| `aspen-felanpe-ecf-2017` | ASPEN-FELANPE Clinical Guidelines: Nutrition Support of Adult Patients With Enterocutaneous Fistula. JPEN 2017;41:1041-(공지 표기 '1041-112') | 2017 | paywalled-unreviewed | 공지 지정 |
| `aspen-pn-safety-consensus-2014` | A.S.P.E.N. Parenteral Nutrition Safety Consensus Recommendations. JPEN 2014;38(3):296-333 | 2014 | paywalled-unreviewed | 공지 지정 |
| `aspen-pn-ordering-review-compounding-2014` | Parenteral Nutrition Ordering, Order Review, Compounding, Labeling, and Dispensing. JPEN 2014;38(3):334-377 | 2014 | paywalled-unreviewed | 공지 지정 |
| `aspen-hyperglycemia-2013` | A.S.P.E.N. Clinical Guidelines: Nutrition Support of Adult Patients With Hyperglycemia. JPEN 2013;37:23-36 | 2013 | paywalled-unreviewed | 공지 지정 |
| `dipiro-13e-2026` | Haines ST, et al. DiPiro's Pharmacotherapy: A Pathophysiologic Approach, 13th ed. | 2026 | not-held | 공지 지정 |
| `casebook-12e-2023` | Schwinghammer TL, et al. Pharmacotherapy Casebook: A Patient-Focused Approach, 12th ed. | 2023 | not-held | 공지 지정 |
| `applied-therapeutics-12e-2023` | Zeind CS, et al. Applied Therapeutics: The Clinical Use of Drugs, 12th ed. | 2023 | not-held | 공지 지정 |
| `chisholm-pp-6e-2022` | Chisholm-Burns MA, et al. Pharmacotherapy Principles & Practice, 6th ed. | 2022 | not-held | 공지 지정 |
| `kscp-pharmacotherapy-6th-2025` | 한국임상약학회. 약물치료학 제6개정. 신일북스 | 2025 | not-held | 공지 지정 |
| `yakryojeongbo-2021` | 약국실무분과회. 약료정보학. 신일북스 (Section III 제9–13장, 16장) | 2021 | not-held | 공지 지정 |
| `imsangsilmu-yakhak-2024` | 약국실무분과회. 임상실무약학. 신일북스 (27장, 29장) | 2024 | not-held | 공지 지정 |
| `users-guides-3e-2015` | Guyatt G, Rennie D, Meade MO, Cook DJ. Users' Guides to the Medical Literature, 3rd ed. | 2015 | not-held | 공지 지정 |
| `dicenzo-biostat-2e-2015` | DiCenzo R, ed. Clinical Pharmacist's Guide to Biostatistics and Literature Evaluation, 2nd ed. ACCP | 2015 | not-held | 공지 지정 |
| `browner-designing-5e-2022` | Browner WS, Newman TB, Cummings SR. Designing Clinical Research, 5th ed. Wolters Kluwer | 2022 | not-held | 공지 지정 |
| `malone-drug-info-7e-2022` | Malone PM, Witt BA, Malone MJ, Peterson DM. Drug Information: A Guide for Pharmacists, 7th ed. McGraw Hill | 2022 | not-held | 공지 지정 |

판본 불일치 주의: 공지의 DiPiro는 13판(2026)인데 수집 정리 문서는 12판을, 공지의 ASPEN 소아 Core는 2판인데 수집 정리 문서는 3판(2024)을 안내한다. 지정 판본이 아니므로 대체하지 않는다.

### 5.2 장·쪽 확인 대기 항목

원문을 확보하기 전에는 아래 항목의 임상 내용을 확정하지 않는다. 쪽·장 번호를 기록하는 시점은 원문을 직접 열람한 뒤다.

- `aspen-adult-core-4e-2025` — 영양선별·평가·영양불량 진단(prealbumin 취급 포함): 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 에너지·단백 요구량 식(일반/중환자/비만/신부전): 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — PN 적응증·시작 시점·SPN: 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — PN 구성 성분(탄수화물·GIR·dextrose kcal/g·지질·AA·전해질·비타민·TE): 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 접근기구·투여경로·필터·조제·안정성·BUD: 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 합병증(재급식·PNALD·MBD·EFAD)·모니터링: 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 질환별: 신장·간·GI·폐·심장·신경계·당뇨·비만·수술·암·중환자·화상·섭식장애·임부·노인: 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 재택영양: 장·쪽 확인 대기
- `aspen-adult-core-4e-2025` — 영양소–약물 상호작용·EN–약물: 장·쪽 확인 대기
- `espen-icu-2019` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-liver-2019` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-surgery-2017` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-cancer-2021` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-geriatrics-2019` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-kidney-2021` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-pancreas-2020` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-ibd-2023` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `espen-cif-2016` — 권고문·환자군·연도 대조 필요: 원문 확보 후 장·쪽 기록
- `aspen-ped-core-2e-2015` — 소아 요구량·GIR·지질·AA·전해질·Ca/P·TE·비타민: 장·쪽 확인 대기
- `aspen-ped-core-2e-2015` — 신생아·미숙아 PN, 소아 질환별·재택: 장·쪽 확인 대기
- `aspen-adult-disease-pn-guidelines` — 서지 식별 대기(공지 문구만으로는 특정 불가)
- `aspen-preterm-pn-2023` — 미숙아 GIR·지질·AA·전해질 권고문과 쪽 확인 대기
- `aspen-adult-critically-ill-2022` — 단백·에너지·SPN 시기·ILE 권고문과 쪽 확인 대기
- `aspen-pn-compat-2022` — 약물·전해질 배합성 표의 쪽 확인 대기
- `aspen-ile-safety-part1-2020` — ILE 속도·TG 기준·EFAD·제품 비동등 권고문과 쪽 확인 대기
- `aspen-refeeding-2020` — 위험군 정의·열량 증량·전해질·thiamine 권고문과 쪽 확인 대기
- `aspen-cvad-hpn-2019` — 카테터 선택·관리·감염 권고문과 쪽 확인 대기
- `sccm-aspen-ped-critical-2017` — 소아 중환자 에너지·단백·시기 권고문과 쪽 확인 대기
- `aspen-felanpe-ecf-2017` — 서지 쪽수 확인 및 권고문 확인 대기
- `aspen-pn-safety-consensus-2014` — 필터·라벨·투여 안전 권고문과 쪽 확인 대기
- `aspen-pn-ordering-review-compounding-2014` — 처방·검토·조제 권고문과 쪽 확인 대기
- `aspen-hyperglycemia-2013` — PN 중 혈당 목표·인슐린 권고문과 쪽 확인 대기
- `dipiro-13e-2026` — 영양지원·영양소 관련 장·쪽은 원문 확보 후 확인
- `casebook-12e-2023` — 영양지원·영양소 관련 장·쪽은 원문 확보 후 확인
- `applied-therapeutics-12e-2023` — 영양지원·영양소 관련 장·쪽은 원문 확보 후 확인
- `chisholm-pp-6e-2022` — 영양지원·영양소 관련 장·쪽은 원문 확보 후 확인
- `kscp-pharmacotherapy-6th-2025` — 영양지원·영양소 관련 장·쪽은 원문 확보 후 확인
- `yakryojeongbo-2021` — 공지가 지정한 Section III 제9–13장·16장의 쪽 확인 대기
- `imsangsilmu-yakhak-2024` — 27장·29장 쪽 확인 대기
- `users-guides-3e-2015` — 장·쪽 확인 대기
- `dicenzo-biostat-2e-2015` — 장·쪽 확인 대기
- `browner-designing-5e-2022` — 장·쪽 확인 대기
- `malone-drug-info-7e-2022` — 장·쪽 확인 대기

### 5.3 연결된 scope가 없는 문헌

연결할 근거 항목을 아직 확인하지 못했거나, 공지 자체·시험 안내 자료라 범위와 직접 연결되지 않는 행이다.

- `kshp-2026-iv-notice` — 한국병원약사회 2026년도 제4회 전문약사 자격시험 공지 - 정맥영양 (시험과목별 공지사항)
- `espen-scientific-guidelines-index` — ESPEN Scientific Guidelines (PDF versions index)
- `espen-practical-guidelines-index` — ESPEN Practical Guidelines (PDF versions index)
- `espen-ped-pn-2018-11-organisational-aspects` — ESPGHAN/ESPEN/ESPR/CSPEN guidelines on pediatric parenteral nutrition:
- `aspen-adult-disease-pn-guidelines` — ASPEN guidelines on adult parenteral nutrition for specific diseases (
- `dipiro-13e-2026` — Haines ST, et al. DiPiro's Pharmacotherapy: A Pathophysiologic Approac
- `casebook-12e-2023` — Schwinghammer TL, et al. Pharmacotherapy Casebook: A Patient-Focused A
- `applied-therapeutics-12e-2023` — Zeind CS, et al. Applied Therapeutics: The Clinical Use of Drugs, 12th
- `chisholm-pp-6e-2022` — Chisholm-Burns MA, et al. Pharmacotherapy Principles & Practice, 6th e
- `kscp-pharmacotherapy-6th-2025` — 한국임상약학회. 약물치료학 제6개정. 신일북스
- `aspen-role-of-pn-malnutrition-2025` — The Role of Parenteral Nutrition in Managing Malnutrition
- `aspen-pn-checklist-institutions-2025` — How to Improve PN Safety in Your Institution Checklist
- `aspen-direct-access-infusion-statement-2025` — Direct Access Infusion Statement
- `hoag-tpn-qa` — Hoag Healthcare TPN Frequently Asked Questions + Answers
- `allaccess-enteral-parenteral-pqs` — AllAccessDietetics Enteral & Parenteral Nutrition practice questions
- `bcnsp-exam-specs-2025` — BPS BCNSP Examination Specifications 2025
- `nbnsc-cnsc-handbook-2026` — NBNSC CNSC Candidate Handbook 2026 (+ PTCNY 사본)
- `oa-bcnsp-pn-nicu` — The impact of BCNSP board certified nutrition support pharmacist on pa
- `oa-refeeding-anemia-prematurity-2026` — Refeeding Syndrome May Increase the Risk of Anemia of Prematurity (Nut
- `oa-en-intolerance-pancreatitis-2026` — Predictors of enteral nutrition intolerance in severe acute pancreatit
- `kshp-yeongyang-yakryo-lecture-answers` — 병원약사회 영양약료 심화강의 시험 정답 및 선택지별 해설 (55문항, 검토 기준일 2026-08-14)

## 6. 출처 사용상 주의

- **현 핵심표의 실제 출처는 『임상영양길라잡이』다.** 핵심표의 '표9-16', '표14-4', '표19-7' 같은 번호와 `[EXAM]` 분홍 형광은 이 책(저장소 밖 OCR 353쪽, 판본·연도 미확정, OCR 품질 불량 구간 다수)을 가리키며, 공지 지정 문헌이 아니다. 지정 성인 Core 4판의 표·쪽으로 읽으면 안 된다.
- **형광은 공식 중요도·기출이 아니다.** 사용자 사진에 기반한 개인 표시이며 자동으로 빈출·중요로 해석하지 않는다.
- **'병원약사회 영양약료 시험' 출처 문항(원시 배열 52건)**은 이번 전문약사 정맥영양 시험과 다른 교육/시험 자료(55문항, 검토 기준일 2026-08-14)에서 왔다. 기출 여부를 추정하지 않으며 originType은 Task 2에서 분류한다.
- **BCNSP·CNSC 등 해외 자료**는 국내 출제비중으로 해석하지 않는다(문항 수·영역 비율 포함).
- `_audit_smart_*.md`는 퀴즈→핵심표 점프(형광 착지) 점검 기록이지 임상 정확성 검증이 아니다.
- 개인 학습 기록(답안·오답)은 이 저장소에 포함하지 않는다.

## 7. Task 2에서 우선 검토할 충돌·누락 후보

각 항목은 현재 HTML 또는 기존 노트에서 확인된 **확인 필요 지점**이며 정답이 아니다.

| 후보 | 현재 상태(확인된 사실) | 검토 방향 |
|---|---|---|
| prealbumin | 평가 단락이 "진단 지표에서 제외(음성 급성기 반응)"와 "염증 지표·영양위험 평가, 영양지원 효과 모니터링 지표로는 근거 미확립"을 함께 서술 | 성인 Core 4판·ASPEN 영양불량 합의 원문 대조, 문항 해설과 일치 여부 |
| GIR | 일반 5–7, 안정 4–5, ICU/고혈당 ≤4, 화상 ≤5, 일일 ≤7 g/kg, ESPEN HPN 5–7(주기 순간속도), 소아 5–13 vs ESPEN 표가 병존. 한 줄로 외우면 충돌한다는 기존 노트 기록 | 환자군·연도·조건을 분리한 비교표, 문항 stem에 조건 명시, 단일 '시험 정답' 금지 |
| dextrose 계수 | 기본 3.4 kcal/g(일수화물), 무수 4, 교재 예제는 3.85로 계산 → 같은 예제에서 286 g vs 324 g로 갈림 | 근거 확정, 예제·치트·A4 일관화 |
| BUD | 구 USP(상온 30 h/냉장 9일) 값은 있으나 국내(2019) 범주 1·2의 일부 숫자가 비어 있음("냉 h", "냉일") | 누락 수치 복원(원문 대조), 구/현행 구분 |
| 필터 | 구 2-in-1 0.22 μm / 3-in-1·ILE 1.2 μm와 현행 단일 1.2 μm가 병존. 영양약료 55문항 해설은 2-in-1 0.22 μm / 3-in-1·ILE 1.2 μm 조합을 정답으로 둠 | 시대·기관별 권고 비교, 해당 문항 pending 처리 여부 |
| PN 적응증·시작 시점 | 영양위험 3–5일, 잘 영양된 환자 7일 대기, SPN day 7 이전 비시작, 말초 PN ≤10–14일 등 서로 다른 기준이 한 단락에 있음 | ASPEN 2022·ESPEN·성인 Core 4판 원문 대조 |
| TG 기준 | 개시 >200 주의 vs ≥400 중단·감량 vs 소아 265/400 | 의미(개시/중단/감량)별 분리 |
| ICU 지질 첫 주 | 교재의 첫 주 hold 서술과 ASPEN 2022 allow가 병존 | 연도·기관 병기 |
| 소아 NPC:N·GIR | 소아 NPC:N 150–250:1과 중환자 성인 70–100:1이 한 단락에 있고, 영양약료 문항은 소아에 80–100:1을 적용하면 오답으로 처리 | 환자군 분리 |
| AKI 단백 | 강의자료 정답 84 g/d(1.2 g/kg)와 ESPEN 2024 91–105 g/d(1.3–1.5 g/kg) 불일치가 기존 노트에 기록 | '최신 지침 vs 강의자료' 병기, 문항 pending |
| 영양약료 55문항 | 출제 맥락이 강의자료 기준. 최신 지침과 다른 항목 있음 | 문항별 근거·originType 분류 |

## 8. 이번 작업에서 하지 않은 것

- `PN_study_split.html`, `PN_core_A4_print.html` 수정, `questions.json` 생성.
- 임상 수치의 정답 판정 및 문항 내용 검증(문항 범위 매핑은 §9의 휴리스틱 v1만 수행).
- 미확보 문헌의 쪽·장·권고문 기록(원문 확인 전에는 기록하지 않음).

## 9. 기존 문항 ID → 범위 행 매핑 (Task 1 보정)

### 방법

1. **문항 모집단:** `PN_study_split.html`의 `const QUESTIONS` 583건(§2). ID를 새로 만들지 않았고 `questions.json`도 만들지 않았다. HTML은 수정하지 않았다.
2. **기존 링크:** 데이터에 들어 있는 연결은 문항별 `topic` 키(15종)뿐이다. 이 키가 핵심표 `#core .sec[data-topic]` 및 퀴즈 패널 필터로 이어지며, 개별 문항→`sec-*` ID 고정 링크는 없다(런타임에 `needle`/`CORE_HINTS`로 점수화해 이동). 따라서 문항→소단원은 topic 단위까지만 추적 가능하다.
3. **topic 연결 우선:** 범위 행이 좁게 한 주제에 대응하는 경우(`spec-components`=cho_gir·lipid·protein·fluid_lytes·vit_te, `spec-pediatric`=peds, `spec-hpn`=hpn, `spec-monitoring`=monitor·complications, `spec-compatibility`=stability)는 그 topic의 문항을 `topicOnly`로, 키워드까지 맞으면 `topicAndKeyword`로 분류했다. `spec-plan-personalized`는 topic=indications이면서 문항에 PN 용어(PN·TPN·정맥영양·비경구)가 있을 때만 topic 일치로 취급했다.
4. **키워드 보충:** 나머지 행은 `stem`+`needle`(정답 선지·해설은 제외)에 대한 키워드 정규식 일치만 사용했다(`keywordOnly`, 최저 신뢰도). 질환·집단 행(신장, 간, GI, 폐, 심장, 신경, 당뇨, 비만, 수술, 암, 중환자, 화상, 섭식장애, 임신, 신생아·미숙아·소아, 노인)은 질환/집단명이 `stem`/`needle`에 있어야 한다. `format-appropriateness`는 `약사가…검토/확인` 형태의 처방 검토 사례형 stem, `format-monitoring`은 같은 사례형 중 '모니터' 언급, `format-patient-education`은 상담·교육 키워드다.
5. **중복 허용:** 한 문항이 여러 행에 매핑될 수 있다(예: 중환자 GIR 문항 → components·plan-calc·critical-care). 행별 건수의 합은 문항 수(583)가 아니다.
6. **JSON 필드:** `content/exam-scope.json`의 각 행에 `questionIds`(전체), `questionIdsByBasis`(`topicAndKeyword`/`topicOnly`/`keywordOnly`), `questionMapping`(`keyword-heuristic-v1` 또는 `none-found`)을 추가했고, `meta.questionMapping`에 총계와 미매핑 ID를 기록했다. 행의 `gapNote` 끝에 매핑 불확실성을 덧붙였다.

### 결과 요약

- 583건 중 **550건이 1개 이상 행에 매핑**, **33건은 미매핑**.
- 문항이 0건인 행(6): `common-literature-types`, `common-clinical-statistics`, `common-appraisal-application`, `format-drp`, `format-selection-plan`, `format-monitoring`.
- 행 `coverage`는 바꾸지 않았다. 매핑 건수는 문항 존재 여부 참고치이며 문항 검증·지정 문헌 장·쪽 대조가 없으므로 `covered` 조건을 충족하지 못한다.

| scope id | coverage | questionIds | topic+keyword | topic only | keyword only |
|---|---|---|---|---|---|
| `common-ebm-ebcp` | missing | 3 | 0 | 0 | 3 |
| `common-literature-types` | missing | 0 | 0 | 0 | 0 |
| `common-clinical-statistics` | missing | 0 | 0 | 0 | 0 |
| `common-appraisal-application` | missing | 0 | 0 | 0 | 0 |
| `spec-components` | partial | 230 | 76 | 96 | 58 |
| `spec-assessment` | partial | 73 | 0 | 0 | 73 |
| `spec-requirements` | partial | 39 | 0 | 0 | 39 |
| `spec-plan-personalized` | partial | 27 | 4 | 3 | 20 |
| `spec-plan-calc` | partial | 31 | 0 | 0 | 31 |
| `spec-plan-route` | partial | 89 | 0 | 0 | 89 |
| `spec-dz-renal` | partial | 22 | 0 | 0 | 22 |
| `spec-dz-liver` | partial | 29 | 0 | 0 | 29 |
| `spec-dz-gi` | partial | 28 | 0 | 0 | 28 |
| `spec-dz-lung` | missing | 3 | 0 | 0 | 3 |
| `spec-dz-heart` | missing | 2 | 0 | 0 | 2 |
| `spec-dz-neuro` | missing | 1 | 0 | 0 | 1 |
| `spec-dz-diabetes` | partial | 33 | 0 | 0 | 33 |
| `spec-dz-obesity` | partial | 6 | 0 | 0 | 6 |
| `spec-surgery` | missing | 14 | 0 | 0 | 14 |
| `spec-cancer` | partial | 5 | 0 | 0 | 5 |
| `spec-critical-care` | partial | 57 | 0 | 0 | 57 |
| `spec-burn` | partial | 7 | 0 | 0 | 7 |
| `spec-eating-disorder` | partial | 2 | 0 | 0 | 2 |
| `spec-pregnancy` | missing | 2 | 0 | 0 | 2 |
| `spec-neonate` | partial | 5 | 0 | 0 | 5 |
| `spec-preterm` | partial | 3 | 0 | 0 | 3 |
| `spec-pediatric` | partial | 7 | 3 | 1 | 3 |
| `spec-elderly` | missing | 3 | 0 | 0 | 3 |
| `spec-hpn` | partial | 33 | 13 | 11 | 9 |
| `spec-monitoring` | partial | 145 | 41 | 61 | 43 |
| `spec-ddi-nutrient-drug` | partial | 6 | 0 | 0 | 6 |
| `spec-compatibility` | partial | 35 | 5 | 23 | 7 |
| `spec-products-stability` | partial | 7 | 0 | 0 | 7 |
| `format-appropriateness` | missing | 5 | 0 | 0 | 5 |
| `format-drp` | missing | 0 | 0 | 0 | 0 |
| `format-selection-plan` | partial | 0 | 0 | 0 | 0 |
| `format-monitoring` | partial | 0 | 0 | 0 | 0 |
| `format-patient-education` | missing | 3 | 0 | 0 | 3 |

### 한계·불확실성

- 문항 상당수가 PN이 아닌 **경장영양(EN)·일반 영양** 문항이다(`indications`·`eval`·`calc_filter` topic에 특히 많음). 키워드·topic 매핑은 이를 완전히 걸러내지 못한다. 예: 비위관 위치 확인 문항이 `spec-plan-route`에, 흡수 변화 문항이 `spec-ddi-nutrient-drug`에 걸릴 수 있다.
- `spec-components`·`spec-monitoring`의 `topicOnly` 건은 topic만 일치하고 키워드는 확인하지 않았다. topic 라벨이 실제 문항 내용과 어긋난 경우(예: topic=`disease`인데 HPN 문항)도 있어 `keywordOnly`로 재분류된다.
- 공통영역(`common-*`): 키워드 일치는 `common-ebm-ebcp` 3건(`kshp-09` 메타분석 언급, `cnsc-nutrition-support-119`·`122` 근거 계층·EBM 틀)뿐이며 이 중 의미상 EBM 문항은 119·122다. 임상통계·문헌 종류·논문 비평 문항은 0건 — 핵심표도 없으므로 `missing` 유지.
- 질환 행의 1~7건 규모 매핑(폐 3, 심장 2, 신경 1 등)은 대부분 EN 문항이거나 한 줄 사례이며 해당 행이 `missing`인 근거를 바꾸지 않는다. `spec-dz-diabetes`는 PN 고혈당 문항이 다수 포함돼 있어 '당뇨 환자 영양지원' 문항 수로 읽으면 안 된다.
- `format-drp`·`format-selection-plan`은 DRP/선택·계획 사례를 키워드로 구분할 수 없어 0건으로 두었다(사례형 5건은 `format-appropriateness`에만 연결).
- 이 휴리스틱은 정답·해설의 임상 정확성을 판단하지 않는다(§7 충돌 후보 검증은 Task 2).

### 미매핑 문항 (33건)

어떤 행에도 키워드/topic 규칙이 맞지 않은 문항이다. 대부분 EN 급식관·접근, 비영양 주제(식량 불안정, 영양관리과정), 또는 PN 일반 서술이다. Task 2에서 개별 판정한다.

- `quizlet-pn-008` (calc_filter): 정맥영양(PN) 처방 오류 증가와 관련된 요인은?
- `quizlet-home-ns-003` (disease): 장기 정맥영양(PN) 환자의 미량영양소 관리에서 가장 현실적인 방법은?
- `bcnsp-081` (eval): 영양 중심 신체진찰에서 골격근량을 가장 잘 반영하는 평가 항목은?
- `cnsc-nutrition-support-008` (eval): 자유수가 부족한 환자에서 혈청 나트륨 165 mEq/L이면 어떤 상태를 가장 잘 반영하는가?
- `cnsc-nutrition-support-105` (eval): Academy of Nutrition and Dietetics 영양관리과정(Nutrition Care Process)에서 영양
- `cnsc-nutrition-support-106` (eval): 임상에서 가구 식량 불안정(food insecurity)을 확인하는 데 흔히 쓰는 두 문항 선별 도구는?
- `cnsc-nutrition-support-024` (calc_filter): 20% 정맥 지질 유제는 1 mL당 몇 kcal를 공급하는가?
- `allaccess-011` (calc_filter): 유당(lactose)은 어떤 두 단당류로 분해되는가?
- `cnsc-nutrition-support-068` (indications): 대부분 상황에서 급식을 시작하기 전 비위관 위치 확인에 가장 적절한 방법은?
- `cnsc-nutrition-support-070` (indications): 보통 위·근위 소장에서 흡수되고 관급식에 결합하므로, 흡수 변화를 고려하지 않고 공장 급식관으로 주면 안 되는 약물은?
- `cnsc-nutrition-support-072` (indications): 1.2 kcal/mL 제제로 하루 1,800 kcal를 24시간 지속 주입할 때, 처방할 시간당 속도(반올림)는?
- `cnsc-nutrition-support-074` (indications): 급식관 선단이 공장에 있을 때 볼루스 급식이 일반적으로 금기인 이유는?
- `allaccess-002` (indications): 선단이 위에 끝나는 경장 접근 환자에서 위험할 수 있는 문제 중 해당하지 않는 것은?
- `allaccess-003` (indications): 경장 급식 환자가 지난 1주간 볼루스 급식 30분 후 복부 경련성 통증을 호소한다. 적절한 조치는?
- `allaccess-006` (indications): 좌식 생활 남성 환자, 키 5 ft 9 in, 체중 80 kg, 41세이다. 1.5 kcal/mL 제제로 12시간 주기 급식을
- `bcnsp-009` (route): 정맥영양 중 대사성 알칼리증이 생겼다. PN 처방에서 조절해야 할 성분은?
- `hoag-faq-001` (route): 정맥영양(PN)이란 무엇인가?
- `hoag-faq-002` (route): 정맥영양을 쓰는 일반적인 이유로 가장 적절한 것은?
- `bcnsp-028` (indications): PN에서 EN으로 전환 중인 환자에서, 목표 EN 섭취의 몇 %에 도달하면 PN을 중단하는가?
- `bcnsp-077` (indications): 입원 성인에서 체중 기반 방법으로 적절한 수분 요구 추정은?
- `medex-007` (eval): oxycodone 5 mg 경구 6시간마다, ondansetron 4 mg IV 필요 시 8시간마다 투여 중인 68세 성인의
- `rxk-1_3-2` (eval): 신체계측(anthropometry)이 유용한 평가는?
- `rxk-1_3-5` (eval): 가장 반응성이 빠른 영양지표는?
- `rxk-2_2-1` (route): 폐흡인 위험이 가장 높은 EN 경로는?
- `rxk-2_2-2` (route): 폐흡인 위험이 가장 낮은 EN 경로는?
- `rxk-3_1-2` (disease): TPN이 흔히 도움이 되는 상황은?
- `quizlet-iib-049` (disease): 정맥영양(PN)에서 탄수화물을 과다 투여하면 무엇과 연관되는가?
- `quizlet-a14pn-008` (route): According to the A.S.P.E.N. Safe Practices Guidelines, the following a
- `quizlet-ach-001` (calc_filter): Which of the following practices is most likely to succeed in improvin
- `quizlet-ach-002` (calc_filter): Which of the following statements explains why fermentable fiber is a
- `quizlet-ach-004` (calc_filter): Which of the following is the largest component of total energy expend
- `quizlet-ach-005` (calc_filter): Which of the following is the most commonly used method for assessing
- `quizlet-m4-003` (calc_filter): In pulmonary insufficiency, excessive calorie administration may cause
