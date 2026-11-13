// Pure helpers of src/study-ui.js (list building, search, fixed sessions, mock availability).
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

test("default pool is includeInBasicSet only; pending is opt-in; excluded never", () => {
  assert.deepEqual(ids(UI.basePool(BANK, false)), ["v1", "v2", "v3"]);
  assert.deepEqual(ids(UI.basePool(BANK, true)), ["v1", "v2", "v3", "p1"]);
});

test("buildList scopes by topic, and search spans all topics", () => {
  const st = SS.createEmptyState();
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "lipid", scope: "topic" }, SS)), ["v1", "v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "lipid", scope: "all" }, SS)), ["v1", "v2", "v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", topic: "protein", search: "유화제" }, SS)), ["v1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "all", search: "  v3 " }, SS)), ["v3"]);
});

test("buildList reacts to state: wrong/unsure/unseen/bookmarked", () => {
  let st = SS.createEmptyState();
  st = SS.recordAttempt(st, BANK[0], 0, "sure", 1);    // v1 wrong
  st = SS.recordAttempt(st, BANK[1], 1, "unsure", 2);  // v2 correct but unsure
  st = SS.toggleBookmark(st, "v3");
  const opts = (filter) => ({ filter, topic: "lipid", scope: "all" });
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("오답"), SS)), ["v1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("unsure"), SS)), ["v2"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("unseen"), SS)), ["v3"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, opts("bookmarked"), SS)), ["v3"]);
});

test("review filters still surface an answered pending item with the toggle off; excluded stays hidden", () => {
  let st = SS.createEmptyState();
  st = SS.recordAttempt(st, BANK[3], 0, "sure", 1);
  st = SS.recordAttempt(st, BANK[4], 0, "sure", 2);
  const list = UI.buildList(BANK, st, { filter: "wrong", scope: "all", includePending: false }, SS);
  assert.deepEqual(ids(list), ["p1"]);
  assert.deepEqual(ids(UI.buildList(BANK, st, { filter: "unseen", scope: "all", includePending: false }, SS)), ["v1", "v2", "v3"]);
});

test("createSession freezes order; shuffle uses the given rng once", () => {
  const pool = UI.basePool(BANK, false);
  const s = UI.createSession(pool, { now: 5 });
  assert.equal(s.id, "s5");
  assert.deepEqual(s.ids, ["v1", "v2", "v3"]);
  pool.reverse();
  assert.deepEqual(s.ids, ["v1", "v2", "v3"], "later changes to the source list do not leak into the session");
  const sh = UI.createSession(UI.basePool(BANK, false), { shuffle: true, rng: () => 0, now: 6 });
  assert.deepEqual(sh.ids, ["v2", "v3", "v1"]);
});

test("mock 20+80 is unavailable with the current small verified pool", () => {
  const m = UI.mockAvailability(BANK);
  assert.equal(m.ok, false);
  assert.deepEqual([m.common, m.pn], [0, 3]);
  const big = [];
  for (let i = 0; i < 20; i++) big.push(q("c" + i, "common"));
  for (let i = 0; i < 80; i++) big.push(q("n" + i, "lipid"));
  assert.equal(UI.mockAvailability(big).ok, true);
  const s = UI.createMockSession(big, { rng: () => 0.5, now: 1 });
  assert.equal(s.ids.length, 100);
  assert.equal(s.kind, "mock");
  assert.ok(s.ids.slice(0, 20).every((id) => id.startsWith("c")));
});

test("state-derived filters need a revision; focus moves to the next remaining card", () => {
  assert.equal(UI.filterUsesState("all"), false);
  ["unseen", "wrong", "unsure", "bookmarked"].forEach((f) => assert.equal(UI.filterUsesState(f), true, f));
  // submit under 미풀이 removes the answered card from membership
  let st = SS.createEmptyState();
  const opts = { filter: "unseen", topic: "lipid", scope: "topic" };
  assert.deepEqual(ids(UI.buildList(BANK, st, opts, SS)), ["v1", "v2"]);
  st = SS.recordAttempt(st, BANK[0], 1, "sure", 1);
  const after = ids(UI.buildList(BANK, st, opts, SS));
  assert.deepEqual(after, ["v2"]);
  assert.equal(UI.focusAfterRebuild(["v1", "v2"], "v1", after), "v2");
  // bookmark toggle off under 즐겨찾기 removes the card; falls back to the previous one at the end
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "c", ["a", "b"]), "b");
  assert.equal(UI.focusAfterRebuild(["a", "b", "c"], "b", ["a", "c"]), "c");
  assert.equal(UI.focusAfterRebuild(["a"], "a", []), null);
  assert.equal(UI.focusAfterRebuild(["a", "b"], "a", ["a", "b"]), "a");
});

test("focus falls back to the first new card when no old card survives (cleared source chip)", () => {
  // selected source's last question left the filter; chip reset shows only other-source cards
  assert.equal(UI.focusAfterRebuild(["a"], "a", ["x", "y"]), "x");
  assert.equal(UI.focusAfterRebuild(["a", "b"], "b", ["x", "y"]), "x");
  // mutated id unknown to the old list still lands on the first card
  assert.equal(UI.focusAfterRebuild([], "a", ["x"]), "x");
  assert.equal(UI.focusAfterRebuild(["a"], "a", []), null);
});
