# PN Study (영양불백 · 정맥영양)

Static GitHub Pages site for PN core notes and linked quiz study HTML.

## Live

- Home: https://coinyak.github.io/pn-study/
- Core + questions: https://coinyak.github.io/pn-study/PN_study_split.html
- Core only (A4 print): https://coinyak.github.io/pn-study/PN_core_A4_print.html

## Source

`PN_study_split.html` and `PN_core_A4_print.html` are generated. Edit `content/` (core sections, menu, questions, products) or `src/` (layout shells), then:

```sh
python3 scripts/build.py          # validates, then writes both HTML files
python3 scripts/check_content.py  # structural checks + clinical review summary
python3 -m unittest tests/test_check_content.py
```

`scripts/export_questions.py` regenerates `content/questions.json` from the frozen legacy quiz array (`src/legacy/quiz-raw.json`).
