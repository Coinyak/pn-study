# Quiz card simplify — design

Date: 2026-11-14  
Branch: `feature/pn-national-exam-study`  
Scope: learn-mode question cards + progress marks; keep study-bar sorting/source colors

## Goal

The interactive grading card became too busy. Restore the quieter original problem style, keep favorites (yellow star), add five independent “I worked this” checkboxes in a horizontal row, and keep explanations collapsed by default. Keep source-origin coloring and the top sorting/filter/search bar.

## Decisions (locked)

| Topic | Choice |
| --- | --- |
| Answer UI | Numbered list only — no radio select / submit / grade |
| Favorites | Keep yellow ★ / ☆ bookmark toggle |
| Progress marks | Five independent checkboxes in a horizontal row (not progressive fill, not answer choices) |
| Explanation | Collapsed by default (`<details>` / “정답·해설 보기”) |
| 핵심 위치 | Keep (jump/highlight in core pane when linked) |
| 헷갈림 | Remove from card and from view filters |
| Study bar | Keep mode/view/scope/search and source chips with origin colors |
| Drill / mock | Out of scope — leave existing mode UI as-is; do not redesign or remove in this change |

## Card layout

Each learn-mode card renders as:

1. **Top row:** colored core-origin label · question id · optional “핵심 연결 없음” / pending note · **bookmark ★/☆** on the right  
2. **Stem:** question text  
3. **Choices:** ordered numbered list (`1.` … `n.`) — not interactive for grading  
4. **Action row:** five independent mark checkboxes · **핵심 위치** only when the question is core-linked  
5. **Explain:** `<details>` with summary “정답·해설 보기”, **closed by default**; body shows correct answer + explanation text

Removed from the card: radio choices, 제출, 다시 풀기, 헷갈림, 지난 풀이 맞음/틀림 badge, open-by-default explain panel, “해설 보기/닫기” toggle button.

## Data model

Extend persisted progress (same storage key `pn-study-progress-v1`, `schemaVersion` stays `1`, additive field) with:

```text
marksByQuestionId: {
  [questionId]: [boolean, boolean, boolean, boolean, boolean]
}
```

Rules:

- Exactly five booleans per id when present; missing id ⇒ treat as `[false, false, false, false, false]`
- Each index toggles independently; toggling one does not force neighbors on/off
- Persist on every toggle via existing `StudyState` store save path
- Keep existing `bookmarks` unchanged
- Keep existing `attemptsByQuestionId` in storage for backup compatibility; **learn UI no longer reads or writes attempts**

## View filters (remap)

| Filter UI label | Canonical key | Meaning |
| --- | --- | --- |
| 전체 | `all` | All displayable questions in scope |
| 미표시 | `unseen` (reuse key) | All five marks false (or missing) |
| 표시 있음 | `marked` (new; replaces `wrong` in the learn filter dropdown) | At least one mark true |
| 즐겨찾기 | `bookmarked` | id in `bookmarks` |

Remove `헷갈림` / `unsure` from the learn filter dropdown. Summary line: `표시 {markedCount}/{total} · ★{bookmarked}` (no 오답/헷갈림 counts).

Source chips, scope (topic/all), and search stay as they are, including `coreSourceLabel` / `sourceToneClass` coloring.

## Backup / restore / errors

- Backup payload includes `marksByQuestionId`
- Older backups without marks: treat as empty marks (not an error)
- Invalid mark arrays (wrong length / non-boolean): coerce to `[false×5]` and count toward invalid/dropped stats like other sanitize paths
- Orphan ids (not in bank) keep marks in storage but do not attach to a card
- Save failure: keep on-screen state; show the existing storage-error notice pattern

## Non-goals

- Rebuilding drill/mock grading UX
- Auto-counting “times solved” from grading attempts
- Changing question bank content or core HTML
- Progressive (left-fill) mark semantics

## Files likely touched

- `src/study-ui.js` — card HTML, actions, filters, summary
- `src/study-state.js` — marks CRUD, filter/select/summarize, backup parse/merge
- `src/study.css` — mark row + restore quieter list styles; drop unused choice-grade chrome if unused
- Built `PN_study_split.html` via existing generate/build script
- Tests under `tests/` for state marks + filter remap

## Success criteria

- Card reads like the original quiet problem card, plus ★ and five mark boxes
- Explanation starts collapsed
- Marks and bookmarks survive reload and round-trip backup/restore
- Source colors and sorting/search/source chips still work
- No 헷갈림 control on the card; 핵심 위치 still works for linked items
