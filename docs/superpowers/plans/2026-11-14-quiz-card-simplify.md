# Quiz card simplify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore quieter learn-mode quiz cards with ★ favorites, five independent solve marks, collapsed details explanation, and remapped filters — without losing source colors or study-bar search/scope.

**Architecture:** Extend `StudyState` with `marksByQuestionId` (5 booleans per id). Learn-mode `cardHtml` returns numbered list + marks + `<details>` + 핵심 위치; drill/mock session cards keep grading UI. Filters: 미표시=`unseen` (no marks), 표시 있음=`marked`, 즐겨찾기=`bookmarked`. Rebuild HTML via `python3 scripts/build.py`.

**Tech Stack:** Vanilla JS (`src/study-state.js`, `src/study-ui.js`, `src/study.css`), Node `node:test`, Python `scripts/build.py`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-11-14-quiz-card-simplify-design.md`
- Storage key stays `pn-study-progress-v1`; `schemaVersion` stays `1` (additive marks field)
- Preserve focusAfterRebuild / source-chip focus behavior
- Drill/mock grading UI left as-is when `ui.session` is set

---

### Task 1: marks in study-state — DONE
### Task 2: learn card UI + filters — DONE
### Task 3: build + verify — DONE

Verification: `node --test tests/study-state.test.cjs tests/study-ui.test.cjs` (60 pass); `python3 scripts/build.py`.
