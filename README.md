# PN Study (영양불백 · 정맥영양)

Static GitHub Pages site for PN core notes and linked quiz study HTML. Everything is client-side; there is no server, account, or cloud sync in this release.

## Live

- Home: https://coinyak.github.io/pn-study/
- Core + questions: https://coinyak.github.io/pn-study/PN_study_split.html
- Core only (A4 print): https://coinyak.github.io/pn-study/PN_core_A4_print.html

Internal links work under the `/pn-study/` sub-path and when the generated HTML is opened directly (`file://`). References may link to external publications.

## Source and build

`PN_study_split.html` and `PN_core_A4_print.html` are generated. Edit `content/` (core sections, menu, questions, products) or `src/` (layout shells, `study-state.js`, `study-ui.js`, `study.css`), then:

```sh
python3 scripts/build.py          # validates, then writes both HTML files (deterministic: two runs give identical bytes)
python3 scripts/check_content.py  # structural checks + clinical review summary
node --test tests/*.cjs           # study-state and study-ui tests
python3 -m unittest discover -s tests -p 'test_*.py'   # check_content tests
```

The curated bank is `content/questions.json`. Edit it there and run the build. The historical exporter only creates a comparison file: `python3 scripts/export_questions.py --output /tmp/pn-legacy-candidate.json`. Supply `--notes-dir` if the held lecture extract is outside the default directory. The historical batch scripts are replayed only for this comparison.

## Study features (quiz pane)

- Start with the full verified Korean bank. Use the scope, search and source controls to narrow the list.
- Use **미표시 / 표시 있음 / 즐겨찾기** to review. Your solve marks and favorites stay in this browser under `pn-study-progress-v1`. The site does not sync across devices.
- Open **정답·해설 보기** to see the answer, explanation and reference locations. Select a question card to jump to its related note.
- The public quiz HTML contains only the verified Korean set. Older marks and favorites remain stored by question ID even when the question is not currently in that set.

## Content version and verification status

- `contentVersion`: `2026-11-14.15`. The bank has 590 records: **259 verified**, 199 pending and 132 excluded.
- Verified means the question has been checked against recorded references for study. It is not an official exam answer or a clinical certification.
- Scope coverage: 34 partial, 4 missing, 0 fully covered. EBM/EBCP and literature types now have core notes and original practice. The scope map still lists lung, heart and neurological disease and older adults as gaps.
- Confirmed domestic product rows: 스모프카비벤주, 스모프리피드20% and 네프라민주.
- See `docs/content-audit.md` for scope and errata and `docs/pending-review-plan.md` for the historical review batches.

## Remaining gaps

- Human clinical review of pending questions and of disease subsections that still lack dedicated public-source numbers.
- Check the separate Nutriflex formulations and Furtman where relevant.
- Real-browser checks (print preview, phone layout, `/pn-study/` on the deployed Pages site) after each Pages deploy.
