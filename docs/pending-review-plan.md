# Pending review plan

확인일: 2026-11-14. 기준 파일: `content/questions.json` (배치 1 적용 후 verified 79 · pending 375 · excluded 132), `scripts/check_content.py`의 verified 규칙, `scripts/export_questions.py`, `content/references.json`, `docs/content-audit.md` §10.

verified의 뜻은 README와 같다. 보유한 자료로 stem·선지·정답 인덱스·해설을 되짚은 상태이며, 공식 임상 인증이 아니다.

## 1. 분류 (pending)

시작 시점 401건은 모두 한국어였다. 영문 원문은 이미 excluded다. 선택지 해설이 채워진 문항은 6건뿐이었고, 그중 승격 가능한 것은 `kshp-48` 하나였다.

| 버킷 | 의미 | 처리 |
|---|---|---|
| A. 거의 준비됨 | 한국어 stem, 정답 인덱스 유효, 해설이 답을 설명함. 빈 곳은 evidence·referenceIds·choiceExplanations | 보유 인용으로 채우면 verified |
| B. 핵심표에 사실이 없음 | 문항이 요구하는 숫자가 핵심표에 없음 | 공개 지침 또는 `references.json`의 보유 PDF에서 행을 추가한 뒤 검증. 숫자를 만들지 않음 |
| C. 충돌·정오 | `errataIds`, `answerEvidence=conflict/ambiguous`, 시대에 따라 정답이 바뀜, 단일 정답 불확정 | pending 유지 또는 이미 excluded인 항목은 그대로. 정답 인덱스는 바꾸지 않음 |
| D. 해설이 비거나 출처가 없음 | 해설이 정답 반복뿐이거나, 문제은행 빈도 태그(`[QB]`)만 있고 쪽·지침 문장이 없음 | 출처가 생기면 A로. 없으면 `reviewNote`에 BLOCKER를 남기고 pending |

배치 1 전에 A로 바로 올릴 수 있던 문항은 `kshp-48`뿐이었다. 나머지는 해설·근거를 보유 자료에서 채워야 A가 된다. `kshp-48`은 체크리스트는 통과하지만 `kshp-01`과 같은 혈당 문항이라 C에 준해 추가 연습으로 남긴다.

## 2. 승격 체크리스트

`scripts/check_content.py`가 verified에 요구하는 조건과 같다. 하나라도 빠지면 pending이다.

1. 한국어 stem이다. 영문은 excluded를 유지한다.
2. `answer`가 선지 범위 안이다. 배치 작업에서 이 인덱스를 바꾸지 않는다.
3. `referenceIds`가 `references.json`에 있고, `evidence`마다 `locator`와 `quote`가 있다. quote는 보유 추출본에 있는 문장이다.
4. `explain`이 비어 있지 않다.
5. `choiceExplanations` 길이가 선지와 같고 칸이 비어 있지 않다.
6. `checks.answerEvidence`는 `ok`, `checks.translation`은 `en-untranslated`가 아니다.
7. `duplicateOf`가 없다.
8. 정오표 E1–E8과 정답이 충돌하지 않는다. 정오가 그 답을 지지하면(E3의 3.4 kcal/g처럼) errata id를 달고 승격할 수 있다.
9. `includeInBasicSet`은 verified이면서 `language=ko`일 때만 true다.

## 3. 핵심표에 사실을 넣을 때

문항이 요구하는 사실이 `content/core.html`에 없으면, 공개 지침이나 이미 `references.json`에 있는 보유 PDF에서 학습용 행·칸을 추가한다. 형광(`hl-pink`·`hl-yellow`·`hl-both`)과 기존 표 숫자는 지우지 않는다.

숫자를 출처 없이 만들지 않는다. `not-held`·`paywalled-unreviewed` 문헌의 본문은 확인된 것으로 쓰지 않는다.

배치 1에서 핵심표에 더할 사실이 없었던 항목은 그대로 두었다. 이미 있던 칸에만 출처를 붙였다.

- 2.1 포도당 3.4 kcal/g 옆에 교재 p143
- 2.1 GIR 공식 옆에 교재 p144
- 2.2 TG ≥400 옆에 교재 p181
- 8장 중환자 단백을 `1.2–2.0 g/kg 실제체중(BMI <30)`으로 적음. 숫자는 원래 있던 1.2–2.0이고, 체중 기준은 CCN 요약 2022의 ABW·BMI <30 문장
- 2.7 알루미늄 칸에 ESPEN 소아 Ca·P R8.6. 유리병 글루콘산칼슘 문장만 해당한다

## 4. 문항을 고칠 때

stem·선지·정답 인덱스는 유지한다. 채우는 것은 referenceIds, evidence, choiceExplanations, 필요한 coreSectionIds, reviewNote다.

학습자에게 보이는 `explain`은 보유 문장과 어긋나는 귀속·숫자만 좁힌다. 배치 1에서 좁힌 문항은 `cnsc-nutrition-support-053`(2-in-1을 24시간이라고 한 문장), `quizlet-pn-004`·`cnsc-nutrition-support-085`(학회 원문이 없는 혈당 귀속), `quizlet-pn-031`(보유하지 않은 소아 속도), `quizlet-iib-004`(용량을 교재 50–100 mg/day로), `bcnsp-059`(원문 없는 FDA 25 mcg/L), `cnsc-nutrition-support-082`(표지에 없는 저칼슘 부가 설명)이다.

## 5. 배치 순서

1. pending `kshp-*` — 해설은 있으나 충돌이면 승격하지 않는다.
2. 보유 PDF·교재 정리로 정답이 닫히고 해설만 비어 있던 문항.
3. `reportedExam`은 위 kshp가 전부다. 나머지 고수익은 thirdParty 계산·수치 문항이다.
4. 영문은 이미 excluded. 번역 배치로 미룬다.

한 PR은 15–30문항이다. 401건을 한 번에 넣지 않는다.

## 6. 배치 완료의 뜻

- 그 배치에서 체크리스트를 통과한 N건이 verified가 된다.
- 막힌 문항은 pending이고 `reviewNote`에 이유가 있다.
- `python3 scripts/build.py`, `python3 scripts/check_content.py`, `node --test tests/*.cjs`, `python3 -m unittest discover -s tests -p 'test_*.py'`가 통과한다.
- `main`으로 PR을 열어 GitHub Pages에 반영한다.

재생성: `scripts/export_questions.py`는 끝에서 `scripts/review_batch1.py`를 적용하므로 배치 1 승격은 export 뒤에도 남는다. 다만 지금 `questions.json`의 영양약료 해설 다듬기는 legacy raw에 다시 넣기 전에는 export로 덮어쓰면 사라진다. 그 정리가 끝나기 전에는 export로 `questions.json`을 다시 쓰지 않는다. 승격만 다시 적용할 때는 `python3 scripts/review_batch1.py`를 쓴다.

## 7. 배치 1 — 승격 26건

| ID | 보유 근거 | 핵심표 |
|---|---|---|
| `cnsc-nutrition-support-041` | ASPEN Myths 2024 p.3, 말초 ≤900 mOsm/L | 3.1 |
| `cnsc-nutrition-support-042` | ESPEN 소아 탄수화물 서론, dextrose가 삼투압의 대부분 | 2.1·3.1 |
| `cnsc-nutrition-support-053` | Myths p.3, TNA 24 h · 별도 ILE 12 h | 5.4·2.2 |
| `cnsc-nutrition-support-022` | CCN 요약 2022 · ASPEN Factsheet 2024, 1.2–2.0 g/kg/day | 8 |
| `bcnsp-003` | CCN 요약, BMI <30은 1.2–2.0 g/kg 실제체중 | 8 |
| `quizlet-pn-014` | CCN 요약, 비만 단백은 IBW ≥2.0 (BMI ≥40은 최대 2.5) | 8.2 |
| `cnsc-nutrition-support-023` | 교재 p143의 3.4 kcal/g, ESPEN은 일수화물 형태 | 2.1 |
| `quizlet-pn-012` | 같은 계수로 1,830 kcal · 지방 45 g | 2.1·2.2 |
| `quizlet-pn-013` | 같은 계수로 25.3 kcal/kg/day | 2.1·2.2 |
| `allaccess-007` | 교재 p144 GIR 식, D15 2 L · 70 kg = 2.98 | 2.1 |
| `oe-tg400` | 교재 p181 TG ≥400 감량·중단. >200은 Myths의 시작 주의 | 2.2 |
| `quizlet-pn-047` | 교재 p181, 제한 컷 400 mg/dL | 2.2 |
| `bcnsp-004` | 450 mg/dL는 ≥400 구간 | 2.2 |
| `cnsc-nutrition-support-089` | 같은 기준 | 2.2 |
| `quizlet-pn-031` | ≥400, 속도 ≤0.11 g/kg/h, 20% 선호 | 2.2 |
| `quizlet-pn-046` | 교재 p182, propofol은 10% 지방유제·TG 합산 | 2.2 |
| `oe-hypergly-assess` | Myths p.1, 혈당 >180이면 보수적 증량·감시·인슐린 | 2.1·8.2 |
| `oep-bcscp-q-064` | 같은 사실 | 2.1·8.2 |
| `quizlet-pn-027` | 교재 p153 AA 농도↑, Myths의 Ca gluconate ≠ CaCl₂, p201 P 먼저·Ca 마지막 | 5.2 |
| `quizlet-pn-004` | 교재·영양약료 강의, 140–180 mg/dL | 8.2·2.1 |
| `cnsc-nutrition-support-085` | 같은 범위 | 8.2 |
| `quizlet-cnsc-practice-002` | 같은 범위. 110 미만 비권고는 강의 문제 1 | 8.2 |
| `quizlet-iib-004` | 교재 p184, thiamine 50–100 mg/day × 5–7일 | 6.2 |
| `cnsc-nutrition-support-082` | 재급식 표지: 저인산·저칼륨·저마그네슘 | 6.2 |
| `bcnsp-007` | 저인산혈증이 핵심 표지 | 6.2 |
| `bcnsp-059` | ESPEN 소아 Ca·P R8.6, 유리병 글루콘산칼슘의 알루미늄 | 2.7 |

## 8. 배치 1에서 pending으로 남긴 것

| ID | 이유 |
|---|---|
| `kshp-15` | 강의 84 g vs ESPEN 2024 91–105 g. ESPEN 원문 없음. 인덱스 유지 |
| `kshp-28` | 정답 0.22/1.2가 현행 단일 1.2 μm와 충돌 |
| `kshp-34` | AMA 1979 용량 vs 현행 ASPEN TE |
| `kshp-39` | NUTRIC ≥5와 ≥6이 섞여 단일 정답 불확정 |
| `kshp-46` | 해설이 비타민 K도 답이 될 수 있다고 함 |
| `kshp-48` | `kshp-01`과 같은 140–180. 추가 연습 |
| `cnsc-nutrition-support-059`, `bcnsp-086` | 정답 0.22 μm는 구 권고. 인덱스 유지 |
| `bcnsp-008` | 일반 CSP 4일. USP 원문 없음. PN BUD와 별개 |
| `cnsc-nutrition-support-043` | 1,500–2,800 mOsm/L의 보유 인용 없음 |
| `quizlet-pn-003` | '가장 흔한 합병증=고혈당'이 문제은행 빈도 표기뿐 |
| `rxk-3_2-5` | cracking 투여 금지의 태그가 문제은행 |

E1 영양지표, E2의 조건 없는 GIR 상한, E6의 조건 없는 '7일 후'는 이번 배치에서 승격하지 않았다. `allaccess-007`은 상한이 아니라 계산값이라 E2 연결을 뗐다.

## 9. 남은 일 · 다음 배치

pending 375. 영문 번역은 그다음이다.

다음 배치(배치 2, 15–30건) 후보:

1. Myths에 아직 안 묶인 투여 사실: 칼슘 10–15 mEq/일, 나트륨 1–2 mEq/kg/일, MCB는 챔버 활성화 전 완제품이 아님, 칼슘 염은 서로 바꾸지 못함. 이 문장과 선지가 맞는 문항을 찾아 같은 방식으로 승격한다.
2. 교재에 쪽수가 있는 재급식 시작 열량(10–20 kcal/kg) 문항. ASPEN refeeding 2020 PDF는 `paywalled-unreviewed`라 그 원문을 인용하지 않는다.
3. E1처럼 방향은 맞지만 AND/ASPEN 2012 합의 원문이 없는 영양평가 문항은, 합의 원문이나 교재 쪽 문장을 확보하기 전에는 pending이다.

배치 2에서도 필터 0.22를 정답으로 둔 문항의 인덱스는 바꾸지 않는다.
