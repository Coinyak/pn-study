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

test("buildList sourceLabel keeps a single label and unions several", () => {
  const st = SS.createEmptyState();
  const bank = [
    q("kshp-1", "lipid"),
    q("bcnsp-1", "lipid"),
    q("cnsc-1", "lipid"),
    q("kshp-2", "protein"),
  ];
  const all = { filter: "all", scope: "all" };
  assert.deepEqual(ids(UI.buildList(bank, st, Object.assign({ sourceLabel: "병원약사회" }, all), SS)), ["kshp-1", "kshp-2"]);
  assert.deepEqual(ids(UI.buildList(bank, st, Object.assign({ sourceLabel: ["병원약사회", "BCNSP"] }, all), SS)), ["kshp-1", "bcnsp-1", "kshp-2"]);
  assert.deepEqual(ids(UI.buildList(bank, st, Object.assign({ sourceLabel: new Set(["CNSC", "BCNSP"]) }, all), SS)), ["bcnsp-1", "cnsc-1"]);
  assert.deepEqual(ids(UI.buildList(bank, st, Object.assign({ sourceLabel: "" }, all), SS)), ["kshp-1", "bcnsp-1", "cnsc-1", "kshp-2"]);
  assert.deepEqual(ids(UI.buildList(bank, st, Object.assign({ sourceLabel: [] }, all), SS)), ["kshp-1", "bcnsp-1", "cnsc-1", "kshp-2"]);
  assert.deepEqual(
    ids(UI.buildList(bank, st, { filter: "all", scope: "topic", topic: "lipid", sourceLabel: ["병원약사회", "CNSC"] }, SS)),
    ["kshp-1", "cnsc-1"]
  );
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
  st = SS.setCheck(st, "v1", "o");
  st = SS.setCheck(st, "v2", "x");
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
    st = SS.setCheck(st, id, "o");
    st = SS.toggleBookmark(st, id);
  }
  const view = (filter, search) => ids(UI.buildList(BANK, st, { filter, scope: "all", includePending: true, search }, SS));
  assert.deepEqual(view("all"), ["v1", "v2", "v3"]);
  assert.deepEqual(view("marked"), ["v1"]);
  assert.deepEqual(view("bookmarked"), ["v1"]);
  assert.deepEqual(view("unseen"), ["v2", "v3"]);
  assert.deepEqual(view("bookmarked", "p1"), []);
  assert.equal(SS.getCheck(st, "p1"), "o");
  assert.ok(st.bookmarks.includes("p1"));
});

test("state-derived filters need a revision; focus moves to the next remaining card", () => {
  assert.equal(UI.filterUsesState("all"), false);
  ["unseen", "marked", "o", "x", "bookmarked"].forEach((f) => assert.equal(UI.filterUsesState(f), true, f));
  let st = SS.createEmptyState();
  const opts = { filter: "unseen", topic: "lipid", scope: "topic" };
  assert.deepEqual(ids(UI.buildList(BANK, st, opts, SS)), ["v1", "v2"]);
  st = SS.setCheck(st, "v1", "o");
  const after = ids(UI.buildList(BANK, st, opts, SS));
  assert.deepEqual(after, ["v2"]);
  assert.equal(UI.focusAfterRebuild(["v1", "v2"], "v1", after), "v2");
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "c", ["a", "b"]), "b");
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "b", ["a", "c"]), "c");
  assert.equal(UI.focusAfterRebuild(["a"], "a", []), null);
  assert.equal(UI.focusAfterRebuild(["a", "b"], "a", ["a", "b"]), "a");
});

test("FILTERS are the four mark buttons", () => {
  assert.deepEqual(UI.FILTERS.map((f) => f[0]), ["all", "o", "x", "bookmarked"]);
  assert.deepEqual(UI.FILTERS.map((f) => f[1]), ["전체", "O", "X", "별"]);
});

test("buildList o and x follow the card check, not attempt correctness", () => {
  let st = SS.createEmptyState();
  st = SS.setCheck(st, "v1", "o");
  st = SS.recordAttempt(st, BANK[0], 0, "sure", 1);
  st = SS.setCheck(st, "v2", "x");
  st = SS.recordAttempt(st, BANK[1], 1, "sure", 2);
  st = SS.toggleBookmark(st, "v3");
  const opts = (filter) => ({ filter, scope: "all" });
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("o"), SS)), ["v1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("O"), SS)), ["v1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("x"), SS)), ["v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("X"), SS)), ["v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("bookmarked"), SS)), ["v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("별"), SS)), ["v3"]);
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
