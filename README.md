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

- Answer a question, then grade it; mark confidence (sure / unsure). Explanation and linked core section appear after submission.
- Review filters: wrong, unsure, unseen, bookmarked. Plus search, source chips, topic scoping, resume at the last question.
- Fixed practice session: freezes the current list (optional shuffle) so scrolling or moving between sub-sections does not change it.
- Backup / restore: export progress as JSON (`pn-study-backup-*.json`, git-ignored), preview the file, then restore with merge or replace.
- Progress is stored only in this browser's `localStorage` under the key `pn-study-progress-v1`. Clearing site data or switching browser/device loses it; use backup to move it. If storage is blocked (private mode, quota), the quiz still works but shows a notice that progress will not persist.
- No cloud sync, login, or Supabase wiring is part of this release (an earlier prototype is kept out of the tree).
- The mock exam (20 + 80) stays disabled until enough verified questions exist.

## Content version and verification status

- `contentVersion`: `2026-11-14.1` (`content/questions.json` `meta.contentVersion`). Backups record it; restoring a backup from another version shows a warning.
- Question bank: 586 questions embedded in the HTML (verified 54 · pending 400 · excluded 132). **The default quiz shows only the 54 verified Korean questions.** Pending and excluded questions are embedded but reachable only through the review UI.
- "Verified" means the ID, stem, choices, answer, and explanation were re-checked against the reference material the author holds. It is **not** official clinical certification and has not been reviewed by a licensed clinician or exam body. Do not treat any content here as authoritative for patient care or as an official answer key.
- Scope coverage: 31 partial, 7 missing, 0 fully covered. Missing: common EBM/EBCP, literature types, lung/heart/neuro disease, pregnancy, elderly.
- Domestic PN product table: shell only; the 4 candidate products are all `unconfirmed` and have no composition values.
- Of the designated references, 14 are not held and 11 are paywalled and unreviewed; the ASPEN Adult Nutrition Support Core Curriculum 4th ed. is not held, so values attributed to it are pending page checks.
- Details, errata (E1–E7), and open items: `docs/content-audit.md` (see section 14 for the Task 6 verification record).

## Remaining gaps

- Human clinical review of pending questions and of the new Task 3 sections (11 sections carry open-gap callouts).
- Obtain and check the missing references and domestic PN product labels.
- Enough verified questions for the 20 + 80 mock exam.
- Real-browser checks (print preview, phone layout, `/pn-study/` on the deployed Pages site) were not run in this pass; only static and script checks were.
