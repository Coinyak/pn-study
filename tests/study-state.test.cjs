"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const S = require("../src/study-state.js");

const Q = (id, answer, revision) => ({
  id,
  revision: revision === undefined ? 1 : revision,
  answer,
  choices: ["a", "b", "c", "d"],
  stem: "s-" + id,
});
const QUESTIONS = [Q("q1", 2), Q("q2", 0), Q("q3", 1), Q("q4", 3)];
const CV = "2026-11-14.1";

function fakeStorage(initial) {
  const m = new Map(Object.entries(initial || {}));
  return {
    m,
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => void m.set(k, String(v)),
    removeItem: (k) => void m.delete(k),
  };
}

// ---------- grading ----------
test("gradeAttempt: correct and wrong", () => {
  assert.deepEqual(S.gradeAttempt(Q("q1", 2), 2), { correct: true, answer: 2 });
  assert.deepEqual(S.gradeAttempt(Q("q1", 2), 0), { correct: false, answer: 2 });
});

test("gradeAttempt: no grading without a valid submitted choice", () => {
  for (const bad of [null, undefined, -1, 4, 1.5, "2", NaN]) {
    assert.throws(() => S.gradeAttempt(Q("q1", 2), bad), /selectedIndex/, String(bad));
  }
});

test("constants: storage key and schema version", () => {
  assert.equal(S.STORAGE_KEY, "pn-study-progress-v1");
  assert.equal(S.SCHEMA_VERSION, 1);
  assert.notEqual(S.STORAGE_KEY, "pn-study-split-core-pct");
});

// ---------- recordAttempt ----------
test("recordAttempt: submitting nothing records nothing and returns same state", () => {
  const s0 = S.createEmptyState(CV);
  assert.equal(S.recordAttempt(s0, QUESTIONS[0], null, "sure", 1000), s0);
  assert.equal(S.recordAttempt(s0, QUESTIONS[0], undefined, "sure", 1000), s0);
  assert.deepEqual(s0.attemptsByQuestionId, {});
});

test("recordAttempt: immutable, records grading and revision", () => {
  const s0 = S.createEmptyState(CV);
  const s1 = S.recordAttempt(s0, QUESTIONS[0], 1, "sure", 1000);
  assert.notEqual(s1, s0);
  assert.deepEqual(s0.attemptsByQuestionId, {});
  assert.deepEqual(s1.attemptsByQuestionId.q1, [
    { at: 1000, selected: 1, correct: false, answer: 2, confidence: "sure", revision: 1 },
  ]);
  assert.equal(s1.contentVersion, CV);
  assert.deepEqual(s1.lastSession, { questionId: "q1", at: 1000 });
});

test("recordAttempt: keeps retry history in order", () => {
  let s = S.createEmptyState(CV);
  s = S.recordAttempt(s, QUESTIONS[0], 0, "sure", 1);
  s = S.recordAttempt(s, QUESTIONS[0], 2, "sure", 2);
  s = S.recordAttempt(s, QUESTIONS[0], 3, "unsure", 3);
  assert.deepEqual(
    s.attemptsByQuestionId.q1.map((a) => [a.selected, a.correct]),
    [[0, false], [2, true], [3, false]]
  );
});

test("recordAttempt: confidence normalised; boolean unsure flag supported; bad value rejected", () => {
  const s0 = S.createEmptyState(CV);
  assert.equal(S.recordAttempt(s0, QUESTIONS[0], 2, undefined, 1).attemptsByQuestionId.q1[0].confidence, "sure");
  assert.equal(S.recordAttempt(s0, QUESTIONS[0], 2, true, 1).attemptsByQuestionId.q1[0].confidence, "unsure");
  assert.equal(S.recordAttempt(s0, QUESTIONS[0], 2, false, 1).attemptsByQuestionId.q1[0].confidence, "sure");
  assert.throws(() => S.recordAttempt(s0, QUESTIONS[0], 2, "maybe", 1), /confidence/);
});

test("recordAttempt: ISO timestamps accepted, garbage rejected", () => {
  const s0 = S.createEmptyState(CV);
  const s1 = S.recordAttempt(s0, QUESTIONS[0], 2, "sure", "2026-11-14T06:00:00+09:00");
  assert.equal(s1.attemptsByQuestionId.q1[0].at, "2026-11-14T06:00:00+09:00");
  assert.throws(() => S.recordAttempt(s0, QUESTIONS[0], 2, "sure", "not-a-date"), /timestamp/);
});

// ---------- selectReviewQuestions ----------
function build(steps) {
  let s = S.createEmptyState(CV);
  let t = 1;
  for (const [q, sel, conf] of steps) s = S.recordAttempt(s, q, sel, conf, t++);
  return s;
}
const ids = (qs) => qs.map((q) => q.id);

test("selectReviewQuestions: wrong / unseen / unsure / bookmarked / marked", () => {
  let s = build([
    [QUESTIONS[0], 0, "sure"], // q1 wrong
    [QUESTIONS[1], 0, "unsure"], // q2 correct but unsure
    [QUESTIONS[2], 1, "sure"], // q3 correct sure
  ]);
  s = S.toggleBookmark(s, "q4");
  s = S.setCheck(s, "q1", "o");
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "wrong")), ["q1"]);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "unsure")), ["q2"]);
  // unseen/marked are mark-based (attempts do not matter)
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "unseen")), ["q2", "q3", "q4"]);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "marked")), ["q1"]);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "bookmarked")), ["q4"]);
});

test("selectReviewQuestions: aliases and unknown filter", () => {
  let s = build([[QUESTIONS[0], 0, "sure"]]);
  s = S.setCheck(s, "q1", "o");
  for (const a of ["incorrect", "오답"]) assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, a)), ["q1"], a);
  for (const a of ["new", "미풀이", "미표시"]) assert.equal(S.selectReviewQuestions(QUESTIONS, s, a).length, 3, a);
  for (const a of ["marked", "표시 있음"]) assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, a)), ["q1"], a);
  assert.equal(S.normalizeFilter("confused"), "unsure");
  assert.equal(S.normalizeFilter("헷갈림"), "unsure");
  assert.equal(S.normalizeFilter("favorites"), "bookmarked");
  assert.equal(S.normalizeFilter("즐겨찾기"), "bookmarked");
  assert.throws(() => S.selectReviewQuestions(QUESTIONS, s, "bogus"), /filter/);
});

test("cycleCheck: none → o → x → none", () => {
  const s0 = S.createEmptyState(CV);
  assert.equal(S.getCheck(s0, "q1"), "none");
  const s1 = S.cycleCheck(s0, "q1");
  assert.equal(S.getCheck(s1, "q1"), "o");
  assert.equal(s1.marksByQuestionId.q1, "o");
  const s2 = S.cycleCheck(s1, "q1");
  assert.equal(S.getCheck(s2, "q1"), "x");
  const s3 = S.cycleCheck(s2, "q1");
  assert.equal(S.getCheck(s3, "q1"), "none");
  assert.equal(Object.prototype.hasOwnProperty.call(s3.marksByQuestionId, "q1"), false);
  assert.throws(() => S.setCheck(s0, "q1", "yes"), /check/);
});

test("sanitize/backup: missing marks ok; legacy arrays migrate; merge prefers x over o", () => {
  const st = fakeStorage();
  const store = S.createStore({ storage: st, contentVersion: CV });
  let s = S.setCheck(S.createEmptyState(CV), "q1", "o");
  assert.deepEqual(store.save(s), { ok: true });
  assert.equal(store.load().state.marksByQuestionId.q1, "o");

  const oldText = JSON.stringify({
    schemaVersion: 1, contentVersion: CV, attemptsByQuestionId: {}, bookmarks: [], lastSession: null,
  });
  const old = S.parseBackup(oldText, QUESTIONS);
  assert.equal(old.ok, true);
  assert.deepEqual(old.payload.marksByQuestionId, {});

  const badText = JSON.stringify({
    schemaVersion: 1, contentVersion: CV, attemptsByQuestionId: {}, bookmarks: [], lastSession: null,
    marksByQuestionId: { q2: [true], q3: [1, 0, 0, 0, 0], q4: [true, false, false, false, false], q5: "x" },
  });
  const bad = S.parseBackup(badText, QUESTIONS);
  assert.equal(bad.ok, true);
  assert.deepEqual(bad.payload.marksByQuestionId, { q4: "o", q5: "x" });
  assert.ok(bad.summary.invalidDropped >= 2);

  const remote = S.setCheck(S.createEmptyState(CV), "q1", "x");
  const prev = S.parseBackup(S.exportBackup(remote), QUESTIONS);
  const merged = S.applyBackup(prev, s, { confirmed: true });
  assert.equal(merged.marksByQuestionId.q1, "x");
});

test("re-solving a wrong question correctly removes it from wrong (latest state wins)", () => {
  let s = build([[QUESTIONS[0], 0, "sure"]]);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "wrong")), ["q1"]);
  s = S.recordAttempt(s, QUESTIONS[0], 2, "sure", 50);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "wrong")), []);
  assert.equal(s.attemptsByQuestionId.q1.length, 2); // history kept
  assert.equal(S.latestAttempt(QUESTIONS[0], s).correct, true);
});

test("re-solving correct question wrongly adds it to wrong again", () => {
  let s = build([[QUESTIONS[0], 2, "sure"]]);
  s = S.recordAttempt(s, QUESTIONS[0], 1, "sure", 50);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "wrong")), ["q1"]);
});

test("unsure is cleared when later attempt is sure", () => {
  let s = build([[QUESTIONS[1], 0, "unsure"]]);
  s = S.recordAttempt(s, QUESTIONS[1], 0, "sure", 9);
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, s, "unsure")), []);
});

test("out-of-order timestamps: latest by time wins, not by insertion order", () => {
  let s = S.createEmptyState(CV);
  s = S.recordAttempt(s, QUESTIONS[0], 2, "sure", 100); // correct at t=100
  s = S.recordAttempt(s, QUESTIONS[0], 0, "sure", 50); // wrong but older (clock skew / import)
  assert.equal(S.latestAttempt(QUESTIONS[0], s).correct, true);
});

test("bookmarks: toggle, explicit set, dedupe, immutability", () => {
  const s0 = S.createEmptyState(CV);
  const s1 = S.toggleBookmark(s0, "q1");
  assert.deepEqual(s0.bookmarks, []);
  assert.deepEqual(s1.bookmarks, ["q1"]);
  assert.deepEqual(S.toggleBookmark(s1, "q1").bookmarks, []);
  assert.deepEqual(S.toggleBookmark(s1, "q1", true).bookmarks, ["q1"]);
  assert.deepEqual(S.toggleBookmark(s1, "q2", false).bookmarks, ["q1"]);
});

// ---------- revision handling ----------
test("revision bump: history preserved but excluded from current mastery", () => {
  const s = build([
    [QUESTIONS[0], 0, "sure"], // q1 wrong @rev1
    [QUESTIONS[1], 0, "sure"], // q2 correct @rev1
  ]);
  const bumped = [Q("q1", 2, 2), Q("q2", 0, 2), QUESTIONS[2], QUESTIONS[3]];
  assert.equal(s.attemptsByQuestionId.q1.length, 1); // history kept
  assert.deepEqual(ids(S.selectReviewQuestions(bumped, s, "wrong")), []); // no stale wrong
  assert.deepEqual(ids(S.selectReviewQuestions(bumped, s, "unseen")), ["q1", "q2", "q3", "q4"]); // no marks
  assert.equal(S.latestAttempt(bumped[0], s), null);
  const sum = S.summarizeProgress(bumped, s);
  assert.deepEqual(sum, {
    total: 4, seen: 0, unseen: 4, marked: 0, correct: 0, wrong: 0, unsure: 0,
    bookmarked: 0, staleQuestions: 2, orphanIds: 0,
  });
});

test("revision bump: new attempt after bump counts, old stays in history", () => {
  let s = build([[QUESTIONS[0], 0, "sure"]]);
  const q1v2 = Q("q1", 2, 2);
  s = S.recordAttempt(s, q1v2, 2, "sure", 99);
  assert.deepEqual(s.attemptsByQuestionId.q1.map((a) => a.revision), [1, 2]);
  assert.equal(S.latestAttempt(q1v2, s).correct, true);
  assert.deepEqual(ids(S.selectReviewQuestions([q1v2], s, "wrong")), []);
});

test("missing revision on question is treated as 1", () => {
  const q = { id: "x", answer: 0, choices: ["a", "b"] };
  const s = S.recordAttempt(S.createEmptyState(CV), q, 0, "sure", 1);
  assert.equal(s.attemptsByQuestionId.x[0].revision, 1);
  assert.equal(S.latestAttempt(q, s).correct, true);
});

test("orphan ids (removed from bank) are preserved and never linked to other questions", () => {
  let s = build([[QUESTIONS[0], 0, "sure"]]); // q1 wrong
  const remaining = [QUESTIONS[1], QUESTIONS[2]]; // q1 gone
  const s2 = S.recordAttempt(s, QUESTIONS[1], 0, "sure", 77);
  assert.ok(s2.attemptsByQuestionId.q1, "orphan history preserved");
  assert.deepEqual(ids(S.selectReviewQuestions(remaining, s2, "wrong")), []);
  assert.equal(S.summarizeProgress(remaining, s2).orphanIds, 1);
  // bookmark on removed id is also not surfaced
  const s3 = S.toggleBookmark(s2, "q1");
  assert.deepEqual(ids(S.selectReviewQuestions(remaining, s3, "bookmarked")), []);
});

// ---------- storage adapter ----------
test("store: load from empty storage -> empty state, no writes", () => {
  const st = fakeStorage();
  const store = S.createStore({ storage: st, contentVersion: CV });
  const r = store.load();
  assert.equal(r.status, "empty");
  assert.deepEqual(r.state, S.createEmptyState(CV));
  assert.equal(st.m.size, 0);
});

test("store: save then load round-trips and stamps contentVersion", () => {
  const st = fakeStorage();
  const store = S.createStore({ storage: st, contentVersion: CV });
  let s = store.load().state;
  s = S.recordAttempt(s, QUESTIONS[0], 2, "unsure", 5);
  s = S.toggleBookmark(s, "q3");
  const res = store.save({ ...s, contentVersion: "stale" });
  assert.deepEqual(res, { ok: true });
  const raw = JSON.parse(st.getItem("pn-study-progress-v1"));
  assert.equal(raw.schemaVersion, 1);
  assert.equal(raw.contentVersion, CV);
  assert.deepEqual(Object.keys(raw).sort(), ["attemptsByQuestionId", "bookmarks", "contentVersion", "lastSession", "marksByQuestionId", "schemaVersion"]);
  const again = store.load();
  assert.equal(again.status, "ok");
  assert.deepEqual(again.state.attemptsByQuestionId, s.attemptsByQuestionId);
  assert.deepEqual(again.state.bookmarks, ["q3"]);
});

test("store: older contentVersion in storage still loads, attempts kept", () => {
  const old = { schemaVersion: 1, contentVersion: "2020-01-01.1", attemptsByQuestionId: { q1: [{ at: 1, selected: 0, correct: false, answer: 2, confidence: "sure", revision: 1 }] }, bookmarks: [], lastSession: null };
  const st = fakeStorage({ "pn-study-progress-v1": JSON.stringify(old) });
  const r = S.createStore({ storage: st, contentVersion: CV }).load();
  assert.equal(r.status, "ok");
  assert.equal(r.state.attemptsByQuestionId.q1.length, 1);
});

test("store: save swallows storage exceptions (quota) and reports error", () => {
  const st = fakeStorage();
  st.setItem = () => { throw new Error("QuotaExceededError"); };
  const store = S.createStore({ storage: st, contentVersion: CV });
  const res = store.save(S.createEmptyState(CV));
  assert.equal(res.ok, false);
  assert.equal(res.reason, "storage-error");
  assert.match(res.error, /Quota/);
});

test("store: load swallows getItem exceptions", () => {
  const st = fakeStorage();
  st.getItem = () => { throw new Error("SecurityError"); };
  const r = S.createStore({ storage: st, contentVersion: CV }).load();
  assert.equal(r.status, "unavailable");
  assert.deepEqual(r.state, S.createEmptyState(CV));
});

test("store: save does NOT write and reports storage-error when pre-save getItem throws", () => {
  for (const saveOpts of [undefined, { overwrite: true }]) {
    const st = fakeStorage({ "pn-study-progress-v1": "{not json" });
    let writes = 0;
    st.getItem = () => { throw new Error("SecurityError"); };
    st.setItem = () => { writes++; };
    const res = S.createStore({ storage: st, contentVersion: CV }).save(S.createEmptyState(CV), saveOpts);
    assert.equal(res.ok, false);
    assert.equal(res.reason, "storage-error");
    assert.match(res.error, /SecurityError/);
    assert.equal(writes, 0);
    assert.equal(st.m.get("pn-study-progress-v1"), "{not json");
  }
});

test("store: no storage available -> unavailable, save reports it", () => {
  const store = S.createStore({ storage: null, contentVersion: CV });
  assert.equal(store.load().status, "unavailable");
  assert.deepEqual(store.save(S.createEmptyState(CV)), { ok: false, reason: "no-storage" });
});

test("store: truncated JSON -> corrupt, raw untouched, save refuses to clobber", () => {
  const good = JSON.stringify({ schemaVersion: 1, contentVersion: CV, attemptsByQuestionId: {}, bookmarks: [], lastSession: null });
  const truncated = good.slice(0, good.length - 7);
  const st = fakeStorage({ "pn-study-progress-v1": truncated });
  const store = S.createStore({ storage: st, contentVersion: CV });
  const r = store.load();
  assert.equal(r.status, "corrupt");
  assert.deepEqual(r.state, S.createEmptyState(CV));
  assert.equal(st.getItem("pn-study-progress-v1"), truncated);
  const res = store.save(S.createEmptyState(CV));
  assert.deepEqual(res, { ok: false, reason: "blocked-corrupt" });
  assert.equal(st.getItem("pn-study-progress-v1"), truncated);
  assert.deepEqual(store.save(S.createEmptyState(CV), { overwrite: true }), { ok: true });
});

test("store: unknown schemaVersion -> unknown-schema, never overwritten without opt-in", () => {
  const future = JSON.stringify({ schemaVersion: 99, whatever: true });
  const st = fakeStorage({ "pn-study-progress-v1": future });
  const store = S.createStore({ storage: st, contentVersion: CV });
  assert.equal(store.load().status, "unknown-schema");
  assert.equal(store.save(S.createEmptyState(CV)).reason, "blocked-unknown-schema");
  assert.equal(st.getItem("pn-study-progress-v1"), future);
});

test("store: non-object JSON values are corrupt", () => {
  for (const raw of ["null", "[]", "42", '"x"']) {
    const st = fakeStorage({ "pn-study-progress-v1": raw });
    assert.equal(S.createStore({ storage: st, contentVersion: CV }).load().status, "corrupt", raw);
  }
});

test("store: malformed entries are dropped, valid ones kept", () => {
  const raw = {
    schemaVersion: 1, contentVersion: CV,
    attemptsByQuestionId: {
      q1: [{ at: 1, selected: 0, correct: false, answer: 2, confidence: "sure", revision: 1 }, { nonsense: true }, null],
      q2: "not-an-array",
    },
    bookmarks: ["q1", "q1", 5, null, "q2"],
    lastSession: "bad",
  };
  const st = fakeStorage({ "pn-study-progress-v1": JSON.stringify(raw) });
  const r = S.createStore({ storage: st, contentVersion: CV }).load();
  assert.equal(r.status, "ok");
  assert.equal(r.state.attemptsByQuestionId.q1.length, 1);
  assert.equal(r.state.attemptsByQuestionId.q2, undefined);
  assert.deepEqual(r.state.bookmarks, ["q1", "q2"]);
  assert.equal(r.state.lastSession, null);
});

test("store never touches other keys (pn-study-split-core-pct)", () => {
  const st = fakeStorage({ "pn-study-split-core-pct": "55" });
  const store = S.createStore({ storage: st, contentVersion: CV });
  store.save(S.recordAttempt(store.load().state, QUESTIONS[0], 2, "sure", 1));
  assert.equal(st.getItem("pn-study-split-core-pct"), "55");
  assert.deepEqual([...st.m.keys()].sort(), ["pn-study-progress-v1", "pn-study-split-core-pct"]);
});

test("store: save re-reads storage, so data written by another tab after load is not clobbered", () => {
  const st = fakeStorage();
  const store = S.createStore({ storage: st, contentVersion: CV });
  assert.equal(store.load().status, "empty"); // stale lastStatus would be "empty"
  const future = JSON.stringify({ schemaVersion: 99, whatever: true });
  st.setItem("pn-study-progress-v1", future); // another tab upgrades the schema
  assert.deepEqual(store.save(S.createEmptyState(CV)), { ok: false, reason: "blocked-unknown-schema" });
  assert.equal(st.getItem("pn-study-progress-v1"), future);
  const trunc = '{"schemaVersion":1,"attempts'; // another tab leaves corrupt data
  st.setItem("pn-study-progress-v1", trunc);
  assert.deepEqual(store.save(S.createEmptyState(CV)), { ok: false, reason: "blocked-corrupt" });
  assert.equal(st.getItem("pn-study-progress-v1"), trunc);
  assert.deepEqual(store.save(S.createEmptyState(CV), { overwrite: true }), { ok: true });
  assert.equal(JSON.parse(st.getItem("pn-study-progress-v1")).schemaVersion, 1);
});

test("store: save after load of ok data still works (re-read does not over-block)", () => {
  const st = fakeStorage();
  const store = S.createStore({ storage: st, contentVersion: CV });
  store.load();
  assert.deepEqual(store.save(S.createEmptyState(CV)), { ok: true });
  assert.deepEqual(store.save(S.createEmptyState(CV)), { ok: true });
});

test("createStore refuses any key other than pn-study-progress-v1", () => {
  const st = fakeStorage({ "pn-study-split-core-pct": "55" });
  for (const key of ["pn-study-split-core-pct", "other", "pn-study-progress-v2"]) {
    assert.throws(() => S.createStore({ storage: st, key, contentVersion: CV }), /pn-study-progress-v1/, key);
  }
  assert.equal(st.getItem("pn-study-split-core-pct"), "55");
  assert.deepEqual([...st.m.keys()], ["pn-study-split-core-pct"]);
  // omitted or the fixed key are accepted
  assert.equal(S.createStore({ storage: st, contentVersion: CV }).key, "pn-study-progress-v1");
  assert.equal(S.createStore({ storage: st, key: "pn-study-progress-v1", contentVersion: CV }).key, "pn-study-progress-v1");
});

// ---------- backup ----------
test("exportBackup -> parseBackup round trip", () => {
  let s = build([[QUESTIONS[0], 0, "sure"], [QUESTIONS[1], 0, "unsure"]]);
  s = S.toggleBookmark(s, "q3");
  const text = S.exportBackup(s, { exportedAt: "2026-11-14T00:00:00Z" });
  const p = S.parseBackup(text, QUESTIONS);
  assert.equal(p.ok, true);
  assert.deepEqual(p.errors, []);
  assert.equal(p.payload.attemptsByQuestionId.q1.length, 1);
  assert.deepEqual(p.payload.bookmarks, ["q3"]);
  assert.equal(p.summary.attempts, 2);
  assert.equal(p.summary.questions, 2);
  assert.equal(p.summary.matchedQuestions, 2);
  assert.equal(p.summary.staleQuestions, 0);
  assert.equal(p.summary.orphanIds, 0);
});

test("parseBackup never writes storage (even if a global localStorage exists)", () => {
  const calls = [];
  const prev = globalThis.localStorage;
  globalThis.localStorage = { getItem() { calls.push("get"); return null; }, setItem() { calls.push("set"); }, removeItem() { calls.push("rm"); } };
  try {
    const text = S.exportBackup(build([[QUESTIONS[0], 0, "sure"]]));
    S.parseBackup(text, QUESTIONS);
    S.parseBackup("{broken", QUESTIONS);
    assert.deepEqual(calls, []);
  } finally {
    if (prev === undefined) delete globalThis.localStorage; else globalThis.localStorage = prev;
  }
});

test("parseBackup: truncated / empty / non-string / wrong shape", () => {
  const text = S.exportBackup(build([[QUESTIONS[0], 0, "sure"]]));
  for (const bad of [text.slice(0, text.length - 5), "", "   ", null, undefined, 42]) {
    const p = S.parseBackup(bad, QUESTIONS);
    assert.equal(p.ok, false, String(bad));
    assert.ok(p.errors.length > 0);
    assert.equal(p.payload, null);
  }
  for (const bad of ["null", "[]", "42", '"x"', "{}"]) {
    assert.equal(S.parseBackup(bad, QUESTIONS).ok, false, bad);
  }
});

test("parseBackup: unknown schema version rejected; foreign kind rejected", () => {
  const p = S.parseBackup(JSON.stringify({ schemaVersion: 2, attemptsByQuestionId: {} }), QUESTIONS);
  assert.equal(p.ok, false);
  assert.match(p.errors.join(" "), /schema/i);
  const k = S.parseBackup(JSON.stringify({ kind: "other-app", schemaVersion: 1, attemptsByQuestionId: {}, bookmarks: [] }), QUESTIONS);
  assert.equal(k.ok, false);
});

test("parseBackup: duplicate attempts in input are collapsed with a warning", () => {
  const a = { at: 1, selected: 0, correct: false, answer: 2, confidence: "sure", revision: 1 };
  const text = JSON.stringify({ schemaVersion: 1, contentVersion: CV, attemptsByQuestionId: { q1: [a, { ...a }, a] }, bookmarks: ["q1", "q1"], lastSession: null });
  const p = S.parseBackup(text, QUESTIONS);
  assert.equal(p.ok, true);
  assert.equal(p.payload.attemptsByQuestionId.q1.length, 1);
  assert.deepEqual(p.payload.bookmarks, ["q1"]);
  assert.equal(p.summary.duplicatesRemoved, 3);
  assert.ok(p.warnings.length > 0);
});

test("parseBackup: re-grades attempts for matching revision (does not trust 'correct')", () => {
  const forged = { at: 1, selected: 0, correct: true, answer: 0, confidence: "sure", revision: 1 };
  const text = JSON.stringify({ schemaVersion: 1, contentVersion: CV, attemptsByQuestionId: { q1: [forged] }, bookmarks: [], lastSession: null });
  const p = S.parseBackup(text, QUESTIONS); // q1 answer is 2
  assert.equal(p.payload.attemptsByQuestionId.q1[0].correct, false);
  assert.equal(p.payload.attemptsByQuestionId.q1[0].answer, 2);
  assert.equal(p.summary.regraded, 1);
});

test("parseBackup: old-revision attempts kept as history, flagged stale; orphan ids kept, flagged", () => {
  const mk = (rev) => ({ at: 1, selected: 0, correct: false, answer: 2, confidence: "sure", revision: rev });
  const text = JSON.stringify({
    schemaVersion: 1, contentVersion: "old",
    attemptsByQuestionId: { q1: [mk(0)], gone: [mk(1)] },
    bookmarks: [], lastSession: null,
  });
  const p = S.parseBackup(text, QUESTIONS);
  assert.equal(p.ok, true);
  assert.equal(p.summary.staleQuestions, 1);
  assert.equal(p.summary.orphanIds, 1);
  assert.equal(p.summary.matchedQuestions, 0);
  assert.equal(p.payload.attemptsByQuestionId.q1[0].revision, 0); // history intact
  assert.equal(p.payload.attemptsByQuestionId.q1[0].correct, false); // old record not regraded
  assert.ok(p.payload.attemptsByQuestionId.gone);
  const merged = S.applyBackup(p, S.createEmptyState(CV), { confirmed: true });
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, merged, "wrong")), []); // stale excluded
});

test("parseBackup: dangerous keys are skipped", () => {
  const text = '{"schemaVersion":1,"attemptsByQuestionId":{"__proto__":[{"at":1,"selected":0,"correct":false,"answer":0,"confidence":"sure","revision":1}],"q1":[]},"bookmarks":["__proto__"]}';
  const p = S.parseBackup(text, QUESTIONS);
  assert.equal(p.ok, true);
  assert.equal(Object.prototype.hasOwnProperty.call(p.payload.attemptsByQuestionId, "__proto__"), false);
  assert.deepEqual(p.payload.bookmarks, []);
  assert.equal({}.polluted, undefined);
});

test("parseBackup: tolerates missing questions argument", () => {
  const text = S.exportBackup(build([[QUESTIONS[0], 0, "sure"]]));
  const p = S.parseBackup(text);
  assert.equal(p.ok, true);
  assert.equal(p.summary.orphanIds, 1);
});

// ---------- applyBackup ----------
test("applyBackup requires explicit confirmation and an ok preview", () => {
  const p = S.parseBackup(S.exportBackup(build([[QUESTIONS[0], 0, "sure"]])), QUESTIONS);
  assert.throws(() => S.applyBackup(p, S.createEmptyState(CV)), /confirm/i);
  assert.throws(() => S.applyBackup(p, S.createEmptyState(CV), { confirmed: false }), /confirm/i);
  const bad = S.parseBackup("{x", QUESTIONS);
  assert.throws(() => S.applyBackup(bad, S.createEmptyState(CV), { confirmed: true }), /preview/i);
});

test("applyBackup: merge is idempotent (restoring the same backup twice)", () => {
  const backup = S.parseBackup(S.exportBackup(build([[QUESTIONS[0], 0, "sure"], [QUESTIONS[1], 0, "unsure"]])), QUESTIONS);
  const base = S.recordAttempt(S.createEmptyState(CV), QUESTIONS[2], 1, "sure", 500);
  const once = S.applyBackup(backup, base, { confirmed: true });
  const twice = S.applyBackup(backup, once, { confirmed: true });
  assert.deepEqual(twice, once);
  assert.equal(once.attemptsByQuestionId.q1.length, 1);
  assert.equal(once.attemptsByQuestionId.q3.length, 1); // local data kept
  assert.deepEqual(base.attemptsByQuestionId.q1, undefined); // input state not mutated
});

test("applyBackup: merge keeps attempts sorted by time and takes newest lastSession", () => {
  const local = S.recordAttempt(S.createEmptyState(CV), QUESTIONS[0], 2, "sure", 200);
  const remote = S.recordAttempt(S.createEmptyState(CV), QUESTIONS[0], 0, "sure", 100);
  const p = S.parseBackup(S.exportBackup(remote), QUESTIONS);
  const m = S.applyBackup(p, local, { confirmed: true });
  assert.deepEqual(m.attemptsByQuestionId.q1.map((a) => a.at), [100, 200]);
  assert.deepEqual(m.lastSession, { questionId: "q1", at: 200 });
  assert.equal(S.latestAttempt(QUESTIONS[0], m).correct, true);
});

test("applyBackup: replace mode discards local data; result carries current contentVersion", () => {
  const remote = build([[QUESTIONS[0], 0, "sure"]]);
  const local = S.recordAttempt(S.createEmptyState(CV), QUESTIONS[2], 1, "sure", 500);
  const p = S.parseBackup(S.exportBackup(remote), QUESTIONS);
  const r = S.applyBackup(p, local, { confirmed: true, mode: "replace", contentVersion: "NEW" });
  assert.deepEqual(Object.keys(r.attemptsByQuestionId), ["q1"]);
  assert.equal(r.contentVersion, "NEW");
  assert.throws(() => S.applyBackup(p, local, { confirmed: true, mode: "bogus" }), /mode/);
});

test("end-to-end: preview does nothing; explicit apply + save restores", () => {
  const src = S.createStore({ storage: fakeStorage(), contentVersion: CV });
  src.save(build([[QUESTIONS[0], 0, "sure"]]));
  const text = S.exportBackup(src.load().state);
  const dst = fakeStorage();
  const store = S.createStore({ storage: dst, contentVersion: CV });
  const preview = S.parseBackup(text, QUESTIONS);
  assert.equal(dst.m.size, 0);
  store.save(S.applyBackup(preview, store.load().state, { confirmed: true }));
  assert.deepEqual(ids(S.selectReviewQuestions(QUESTIONS, store.load().state, "wrong")), ["q1"]);
});

test("setLastSession: immutable update", () => {
  const s0 = S.createEmptyState(CV);
  const s1 = S.setLastSession(s0, { questionId: "q2", topic: "route", filter: "wrong", at: 9 });
  assert.equal(s0.lastSession, null);
  assert.deepEqual(s1.lastSession, { questionId: "q2", topic: "route", filter: "wrong", at: 9 });
});
