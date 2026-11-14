// Pure helpers of src/study-ui.js (list building, search, mark filters).
// Run: node --test tests/study-ui.test.cjs
const test = require("node:test");
const assert = require("node:assert/strict");
const SS = require("../src/study-state.js");
const UI = require("../src/study-ui.js");

const q = (id, topic, extra) => Object.assign({
  id, topic, revision: 1, stem: "문항 " + id, choices: ["가", "나", "다", "라"], answer: 1, explain: "",
  source: "SRC", language: "ko", reviewStatus: "verified", includeInBasicSet: true,
}, extra);
const BANK = [
  q("v1", "lipid", { stem: "지질 유화제 용량" }),
  q("v2", "lipid"),
  q("v3", "protein"),
  q("p1", "lipid", { reviewStatus: "pending", includeInBasicSet: false }),
  q("x1", "lipid", { reviewStatus: "excluded", includeInBasicSet: false }),
  q("e1", "lipid", { reviewStatus: "excluded", includeInBasicSet: false, language: "en" }),
];
const ids = (list) => list.map((x) => x.id);

test("public pool is verified Korean only even if legacy flags are supplied", () => {
  assert.deepEqual(ids(UI.basePool(BANK, true)), ["v1", "v2", "v3"]);
});

test("buildList scopes by topic, and search spans all topics", () => {
  const st = SS.createEmptyState();
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "lipid", scope: "topic" }, SS)), ["v1", "v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "lipid", scope: "all" }, SS)), ["v1", "v2", "v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "protein", search: "유화제" }, SS)), ["v1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", search: "  v3 " }, SS)), ["v3"]);
});

test("buildList reacts to state: unseen/marked/bookmarked (mark-based)", () => {
  let st = SS.createEmptyState();
  st = SS.setMark(st, "v1", 0, true);
  st = SS.setMark(st, "v2", 3, true);
  st = SS.toggleBookmark(st, "v3");
  const opts = (filter) => ({ filter, topic: "lipid", scope: "all" });
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("marked"), SS)), ["v1", "v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("unseen"), SS)), ["v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("미표시"), SS)), ["v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("bookmarked"), SS)), ["v3"]);
});

test("old pending/excluded marks and favorites stay stored but never appear", () => {
  let st = SS.createEmptyState();
  for (const id of ["v1", "p1", "x1", "e1"]) {
    st = SS.setMark(st, id, 0, true);
    st = SS.toggleBookmark(st, id);
  }
  const view = (filter, search) => ids(UI.buildList(BANK, st, { filter, scope: "all", includePending: true, search }, SS));
  assert.deepEqual(view("all"), ["v1", "v2", "v3"]);
  assert.deepEqual(view("marked"), ["v1"]);
  assert.deepEqual(view("bookmarked"), ["v1"]);
  assert.deepEqual(view("unseen"), ["v2", "v3"]);
  assert.deepEqual(view("bookmarked", "p1"), []);
  assert.equal(SS.getMarks(st, "p1")[0], true);
  assert.ok(st.bookmarks.includes("p1"));
});

test("state-derived filters need a revision; focus moves to the next remaining card", () => {
  assert.equal(UI.filterUsesState("all"), false);
  ["unseen", "marked", "bookmarked"].forEach((f) => assert.equal(UI.filterUsesState(f), true, f));
  let st = SS.createEmptyState();
  const opts = { filter: "unseen", topic: "lipid", scope: "topic" };
  assert.deepEqual(ids(UI.buildList(BANK, st, opts, SS)), ["v1", "v2"]);
  st = SS.setMark(st, "v1", 0, true);
  const after = ids(UI.buildList(BANK, st, opts, SS));
  assert.deepEqual(after, ["v2"]);
  assert.equal(UI.focusAfterRebuild(["v1", "v2"], "v1", after), "v2");
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "c", ["a", "b"]), "b");
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "b", ["a", "c"]), "c");
  assert.equal(UI.focusAfterRebuild(["a"], "a", []), null);
  assert.equal(UI.focusAfterRebuild(["a", "b"], "a", ["a", "b"]), "a");
});

test("FILTERS expose mark-based views only", () => {
  assert.deepEqual(UI.FILTERS.map((f) => f[0]), ["all", "unseen", "marked", "bookmarked"]);
  assert.deepEqual(UI.FILTERS.map((f) => f[1]), ["전체", "미표시", "표시 있음", "즐겨찾기"]);
});

test("focus falls back to the first new card when no old card survives", () => {
  assert.equal(UI.focusAfterRebuild(["a"], "a", ["x", "y"]), "x");
  assert.equal(UI.focusAfterRebuild(["a", "b"], "b", ["x", "y"]), "x");
  assert.equal(UI.focusAfterRebuild([], "a", ["x"]), "x");
  assert.equal(UI.focusAfterRebuild(["a"], "a", []), null);
});

test("learn UI has no session/mock/resume helpers exported", () => {
  assert.equal(UI.createSession, undefined);
  assert.equal(UI.createMockSession, undefined);
  assert.equal(UI.mockAvailability, undefined);
});
