# PN Study (영양불백 · 정맥영양)

Static GitHub Pages site for PN core notes and linked quiz study HTML. Everything is client-side; there is no server, account, or cloud sync in this release.

## Live

- Home: https://coinyak.github.io/pn-study/
- Core + questions: https://coinyak.github.io/pn-study/PN_study_split.html
- Core only (A4 print): https://coinyak.github.io/pn-study/PN_core_A4_print.html

All links inside the pages are relative, so the site also works under the `/pn-study/` sub-path and when a generated HTML file is opened directly (`file://`). The only external request is the Google Fonts stylesheet; without network access the pages fall back to system fonts.

## Source and build

`PN_study_split.html` and `PN_core_A4_print.html` are generated. Edit `content/` (core sections, menu, questions, products) or `src/` (layout shells, `study-state.js`, `study-ui.js`, `study.css`), then:

```sh
python3 scripts/build.py          # validates, then writes both HTML files (deterministic: two runs give identical bytes)
python3 scripts/check_content.py  # structural checks + clinical review summary
node --test tests/*.cjs           # study-state and study-ui tests
python3 -m unittest discover -s tests -p 'test_*.py'   # check_content tests
```

`scripts/export_questions.py` regenerates `content/questions.json` from the frozen legacy quiz array (`src/legacy/quiz-raw.json`). Do not hand-edit the generated HTML; the next build overwrites it.

## Study features (quiz pane)

- Learn cards: numbered choices, up to five independent solve marks, ★ favorite, collapsed 정답·해설, and 핵심 위치. No radio grading, submit, resume, or drill/mock session UI.
- Filters: 전체 / 미표시 / 표시 있음 / 즐겨찾기 (`marksByQuestionId` + bookmarks). Plus search, source chips, and topic vs all-scope.
- Example flow:
  1. Open `PN_study_split.html`, pick a sub-section; the quiz pane lists verified questions (보기 전체, 검토 대기 포함 off).
  2. Tick solve marks and/or ★ as you work; open 정답·해설 when needed; use 핵심 위치 for the core pane.
  3. Set 보기 to 미표시 / 표시 있음 / 즐겨찾기 to narrow the list; search spans all topics.
  4. Press 백업 for `pn-study-backup-YYYYMMDD.json`; later 복원 → preview → merge or replace.
- Progress is stored only in this browser's `localStorage` under `pn-study-progress-v1`. Clearing site data or switching device loses it; use backup to move it. Older attempt (wrong/unsure) records may still exist in storage but are not used by learn filters.
- No cloud sync or login in this release.

## Content version and verification status

- `contentVersion`: `2026-11-14.13` (`content/questions.json` `meta.contentVersion`). Backups record it; restoring a backup from another version shows a warning.
- Question bank: 586 questions embedded in the HTML (verified 248 · pending 206 · excluded 132). **The default topic quiz shows the 248 verified Korean questions** (kshp-48 stays pending practice; same glucose target as kshp-01). Turning "검토 대기 포함" on also adds pending Korean questions (badge). Filters 표시 있음 / 즐겨찾기 can still show pending items you already marked or bookmarked with the toggle off. Excluded questions are embedded but never displayed.
- "Verified" means the ID, stem, choices, answer, and explanation were re-checked against the reference material the author holds. It is **not** official clinical certification and has not been reviewed by a licensed clinician or exam body. Do not treat any content here as authoritative for patient care or as an official answer key.
- Scope coverage: 31 partial, 7 missing, 0 fully covered. Missing: common EBM/EBCP, literature types, lung/heart/neuro disease, pregnancy, elderly.
- Domestic PN product table: **스모프카비벤주 · 스모프리피드20% · 네프라민주** confirmed from public 허가. Unconfirmed items stay in `products.json` only — learning HTML never shows work-queue notes.
- Learnability pass (2026-11-14): GIR/kcal/indications/assessment/peds/stats cleaned; open-gap callouts removed from the learning view; kidney/HPN/food–drug rows filled from public ESPEN/FDA sources.
- Details and errata (E1–E8): `docs/content-audit.md`. Pending-review pipeline and batch 1: `docs/pending-review-plan.md`.

## Remaining gaps

- Human clinical review of pending questions and of disease subsections that still lack dedicated public-source numbers.
- Confirm remaining domestic PN product labels (Smoflipid, Nutriflex, 네프라민, Furtman).
- Real-browser checks (print preview, phone layout, `/pn-study/` on the deployed Pages site) after each Pages deploy.
