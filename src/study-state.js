/* study-state.js — grading, progress state, review filters, storage adapter, backup.
 *
 * Dual-loadable: `require("./study-state.js")` in Node (CommonJS) and `<script src>` in the
 * browser (exposes `globalThis.StudyState`). No DOM access. The only storage key this module
 * ever touches is STORAGE_KEY ("pn-study-progress-v1"); "pn-study-split-core-pct" belongs to
 * the split shell and is never read or written here.
 *
 * State shape (also the persisted payload):
 *   { schemaVersion: 1,
 *     contentVersion: string|null,          // questions.json meta.contentVersion at save time
 *     attemptsByQuestionId: { [id]: Attempt[] },   // append-only history, oldest -> newest
 *     marksByQuestionId: { [id]: "o"|"x" }, // self-check: O (green) / X (red); absent = none
 *     bookmarks: string[],                  // question ids
 *     lastSession: { questionId, at, topic?, filter? } | null }
 *   Attempt = { at, selected, correct, answer, confidence: "sure"|"unsure", revision }
 *   Legacy boolean[5] mark arrays still load: any true slot → "o".
 *
 * Revision rule: an attempt only counts toward current mastery when attempt.revision ===
 * question.revision (missing revision == 1). Older-revision attempts stay in history. Ids that
 * no longer exist in the bank stay in storage ("orphans") but are never matched to a question.
 *
 * Review filters (selectReviewQuestions): canonical
 * `wrong | unsure | unseen | marked | o | x | bookmarked`, plus `all`.
 * Aliases: incorrect/오답 -> wrong; confused/헷갈림 -> unsure;
 * new/미풀이/미표시 -> unseen; 표시 있음 -> marked;
 * bookmark/bookmarks/favorite/favorites/즐겨찾기/별 -> bookmarked.
 *   wrong      latest current-revision attempt is incorrect (session/compat)
 *   unsure     latest current-revision attempt was marked "unsure" (session/compat)
 *   unseen     no O/X check (or missing); attempts do not affect this
 *   marked     check is "o" or "x"
 *   o          getCheck === "o" (not latestAttempt.correct)
 *   x          getCheck === "x"
 *   bookmarked id is in state.bookmarks
 *
 * Restore flow: parseBackup(text, questions) -> preview (pure, no storage) ->
 * applyBackup(preview, state, {confirmed:true}) -> new state (pure) -> store.save(newState).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else root.StudyState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const STORAGE_KEY = "pn-study-progress-v1";
  const SCHEMA_VERSION = 1;
  const BACKUP_KIND = "pn-study-progress-backup";
  const CHECK_NONE = "none";
  const CHECK_O = "o";
  const CHECK_X = "x";
  const CHECK_CYCLE = [CHECK_NONE, CHECK_O, CHECK_X];
  const CHECK_RANK = { none: 0, o: 1, x: 2 };
  const CONFIDENCES = ["sure", "unsure"];
  const UNSAFE_KEYS = ["__proto__", "constructor", "prototype"];
  const FILTER_ALIASES = {
    wrong: "wrong", incorrect: "wrong", "오답": "wrong",
    unsure: "unsure", confused: "unsure", "헷갈림": "unsure",
    unseen: "unseen", new: "unseen", "미풀이": "unseen", "미표시": "unseen",
    marked: "marked", "표시 있음": "marked", "표시있음": "marked",
    bookmarked: "bookmarked", bookmark: "bookmarked", bookmarks: "bookmarked",
    favorite: "bookmarked", favorites: "bookmarked", "즐겨찾기": "bookmarked", "별": "bookmarked",
    o: "o", x: "x",
    all: "all",
  };

  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const isPlainObject = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
  const isIdx = (n) => typeof n === "number" && Number.isInteger(n) && n >= 0;
  const isSafeKey = (k) => typeof k === "string" && k !== "" && UNSAFE_KEYS.indexOf(k) < 0;
  const revisionOf = (q) => (q && isIdx(q.revision) ? q.revision : 1);

  function toMillis(at) {
    if (typeof at === "number") return Number.isFinite(at) ? at : NaN;
    if (typeof at === "string" && at.trim() !== "") return Date.parse(at);
    return NaN;
  }

  function normalizeConfidence(c) {
    if (c === undefined || c === null || c === false || c === "sure") return "sure";
    if (c === true || c === "unsure") return "unsure";
    throw new TypeError('confidence must be "sure", "unsure", or a boolean unsure flag');
  }

  // ---------- grading ----------
  function gradeAttempt(question, selectedIndex) {
    const n = question && Array.isArray(question.choices) ? question.choices.length : Infinity;
    if (!isIdx(selectedIndex) || selectedIndex >= n) {
      throw new TypeError("selectedIndex must be an integer index of a choice");
    }
    return { correct: selectedIndex === question.answer, answer: question.answer };
  }

  // ---------- state ----------
  function createEmptyState(contentVersion) {
    return {
      schemaVersion: SCHEMA_VERSION,
      contentVersion: contentVersion === undefined ? null : contentVersion,
      attemptsByQuestionId: {},
      marksByQuestionId: {},
      bookmarks: [],
      lastSession: null,
    };
  }

  /** Coerce stored mark value → "none" | "o" | "x". Legacy boolean[5] → "o" if any true. */
  function coerceCheck(raw) {
    if (raw === CHECK_O || raw === CHECK_X) return raw;
    if (Array.isArray(raw) && raw.length === 5) {
      for (let i = 0; i < 5; i++) if (raw[i] === true) return CHECK_O;
      return CHECK_NONE;
    }
    return CHECK_NONE;
  }

  /** Always returns "none" | "o" | "x". Missing id ⇒ "none". */
  function getCheck(state, id) {
    if (!state || !isSafeKey(id) || !isPlainObject(state.marksByQuestionId) || !has(state.marksByQuestionId, id)) {
      return CHECK_NONE;
    }
    return coerceCheck(state.marksByQuestionId[id]);
  }

  function hasCheck(check) {
    return check === CHECK_O || check === CHECK_X;
  }

  /**
   * Set self-check to "none" | "o" | "x". "none" clears the id from the map.
   */
  function setCheck(state, id, value) {
    if (!isSafeKey(id)) throw new TypeError("check id must be a non-empty string");
    if (CHECK_CYCLE.indexOf(value) < 0) throw new TypeError('check must be "none", "o", or "x"');
    const marksByQuestionId = Object.assign({}, state.marksByQuestionId || {});
    if (value === CHECK_NONE) delete marksByQuestionId[id];
    else marksByQuestionId[id] = value;
    return Object.assign({}, state, { marksByQuestionId });
  }

  /** Cycle none → o → x → none (one click each). */
  function cycleCheck(state, id) {
    const cur = getCheck(state, id);
    const next = CHECK_CYCLE[(CHECK_CYCLE.indexOf(cur) + 1) % CHECK_CYCLE.length];
    return setCheck(state, id, next);
  }

  function withAttempts(state, id, list) {
    const attempts = Object.assign({}, state.attemptsByQuestionId);
    attempts[id] = list;
    return Object.assign({}, state, { attemptsByQuestionId: attempts });
  }

  function recordAttempt(state, question, selectedIndex, confidence, timestamp) {
    if (selectedIndex === null || selectedIndex === undefined) return state; // nothing submitted -> no grading
    const at = timestamp === undefined ? Date.now() : timestamp;
    if (Number.isNaN(toMillis(at))) throw new TypeError("timestamp must be epoch ms or a parseable date string");
    const conf = normalizeConfidence(confidence);
    const g = gradeAttempt(question, selectedIndex);
    if (!isSafeKey(question.id)) throw new TypeError("question.id is required");
    const prev = has(state.attemptsByQuestionId, question.id) ? state.attemptsByQuestionId[question.id] : [];
    const attempt = { at, selected: selectedIndex, correct: g.correct, answer: g.answer, confidence: conf, revision: revisionOf(question) };
    const next = withAttempts(state, question.id, prev.concat([attempt]));
    next.lastSession = { questionId: question.id, at };
    return next;
  }

  function currentAttempts(question, state) {
    if (!question || !has(state.attemptsByQuestionId, question.id)) return [];
    const rev = revisionOf(question);
    return state.attemptsByQuestionId[question.id].filter((a) => a.revision === rev);
  }

  function latestAttempt(question, state) {
    const list = currentAttempts(question, state);
    let best = null, bestT = -Infinity;
    for (const a of list) {
      const t = toMillis(a.at);
      if (best === null || t >= bestT) { best = a; bestT = t; } // ties: later entry wins
    }
    return best;
  }

  function toggleBookmark(state, id, on) {
    if (!isSafeKey(id)) throw new TypeError("bookmark id must be a non-empty string");
    const present = state.bookmarks.indexOf(id) >= 0;
    const want = on === undefined ? !present : !!on;
    if (want === present) return Object.assign({}, state, { bookmarks: state.bookmarks.slice() });
    return Object.assign({}, state, {
      bookmarks: want ? state.bookmarks.concat([id]) : state.bookmarks.filter((b) => b !== id),
    });
  }

  function setLastSession(state, session) {
    const ls = sanitizeLastSession(session);
    return Object.assign({}, state, { lastSession: ls });
  }

  // ---------- review ----------
  function normalizeFilter(filter) {
    const key = typeof filter === "string" ? filter.trim().toLowerCase() : "";
    if (!has(FILTER_ALIASES, key)) throw new TypeError("unknown review filter: " + String(filter));
    return FILTER_ALIASES[key];
  }

  function selectReviewQuestions(questions, state, filter) {
    const f = normalizeFilter(filter);
    return questions.filter((q) => {
      if (f === "all") return true;
      if (f === "bookmarked") return state.bookmarks.indexOf(q.id) >= 0;
      if (f === "unseen") return !hasCheck(getCheck(state, q.id));
      if (f === "marked") return hasCheck(getCheck(state, q.id));
      if (f === "o") return getCheck(state, q.id) === CHECK_O;
      if (f === "x") return getCheck(state, q.id) === CHECK_X;
      const last = latestAttempt(q, state);
      if (last === null) return false;
      if (f === "wrong") return !last.correct;
      return last.confidence === "unsure"; // f === "unsure"
    });
  }

  function summarizeProgress(questions, state) {
    const bankIds = new Set(questions.map((q) => q.id));
    const out = {
      total: questions.length, seen: 0, unseen: 0, marked: 0,
      correct: 0, wrong: 0, unsure: 0, bookmarked: 0, staleQuestions: 0, orphanIds: 0,
    };
    for (const q of questions) {
      if (hasCheck(getCheck(state, q.id))) { out.marked++; out.seen++; } else out.unseen++;
      const last = latestAttempt(q, state);
      if (last === null) {
        if (has(state.attemptsByQuestionId, q.id) && state.attemptsByQuestionId[q.id].length) out.staleQuestions++;
        continue;
      }
      if (last.correct) out.correct++; else out.wrong++;
      if (last.confidence === "unsure") out.unsure++;
    }
    out.bookmarked = state.bookmarks.filter((id) => bankIds.has(id)).length;
    const attemptOrphans = Object.keys(state.attemptsByQuestionId || {}).filter((id) => !bankIds.has(id));
    const markOrphans = Object.keys(state.marksByQuestionId || {}).filter((id) => !bankIds.has(id));
    out.orphanIds = new Set(attemptOrphans.concat(markOrphans)).size;
    return out;
  }

  // ---------- sanitising (shared by storage load and backup parse) ----------
  function sanitizeLastSession(ls) {
    if (!isPlainObject(ls) || !isSafeKey(ls.questionId) || Number.isNaN(toMillis(ls.at))) return null;
    const out = { questionId: ls.questionId, at: ls.at };
    if (typeof ls.topic === "string") out.topic = ls.topic;
    if (typeof ls.filter === "string") out.filter = ls.filter;
    return out;
  }

  function sanitizeAttempt(a) {
    if (!isPlainObject(a)) return null;
    if (!isIdx(a.selected) || !isIdx(a.answer) || typeof a.correct !== "boolean" || !isIdx(a.revision)) return null;
    if (CONFIDENCES.indexOf(a.confidence) < 0 || Number.isNaN(toMillis(a.at))) return null;
    return { at: a.at, selected: a.selected, correct: a.correct, answer: a.answer, confidence: a.confidence, revision: a.revision };
  }

  const attemptKey = (a) => JSON.stringify([a.at, a.selected, a.confidence, a.revision]);

  /**
   * Coerce one check value. Accepts "o"|"x" or legacy boolean[5].
   * Invalid → null and bump invalidDropped when raw was present.
   */
  function sanitizeCheckValue(raw, stats) {
    if (raw === undefined || raw === null) return null;
    if (raw === CHECK_O || raw === CHECK_X) return raw;
    if (Array.isArray(raw) && raw.length === 5) {
      let bad = false;
      let any = false;
      for (let i = 0; i < 5; i++) {
        if (typeof raw[i] !== "boolean") bad = true;
        else if (raw[i]) any = true;
      }
      if (bad) { stats.invalidDropped++; return null; }
      return any ? CHECK_O : null;
    }
    stats.invalidDropped++;
    return null;
  }

  /** @returns {{payload, stats}} ; throws nothing. `bank` (optional) = Map id -> question. */
  function sanitizePayload(raw, bank) {
    const stats = { invalidDropped: 0, duplicatesRemoved: 0, regraded: 0, unsafeKeysSkipped: 0 };
    const attemptsByQuestionId = {};
    const src = isPlainObject(raw.attemptsByQuestionId) ? raw.attemptsByQuestionId : {};
    for (const id of Object.keys(src)) {
      if (!isSafeKey(id)) { stats.unsafeKeysSkipped++; continue; }
      if (!Array.isArray(src[id])) { stats.invalidDropped++; continue; }
      const seen = new Set();
      const list = [];
      const q = bank && bank.get(id);
      for (const item of src[id]) {
        let a = sanitizeAttempt(item);
        if (a && q && a.revision === revisionOf(q)) {
          // Same revision => answer key is the same one we have now; do not trust stored grading.
          if (a.selected >= (Array.isArray(q.choices) ? q.choices.length : Infinity)) a = null;
          else {
            const g = gradeAttempt(q, a.selected);
            if (g.correct !== a.correct || g.answer !== a.answer) stats.regraded++;
            a.correct = g.correct; a.answer = g.answer;
          }
        }
        if (!a) { stats.invalidDropped++; continue; }
        const k = attemptKey(a);
        if (seen.has(k)) { stats.duplicatesRemoved++; continue; }
        seen.add(k);
        list.push(a);
      }
      if (list.length) attemptsByQuestionId[id] = stableSortByTime(list);
    }
    const marksByQuestionId = {};
    const markSrc = isPlainObject(raw.marksByQuestionId) ? raw.marksByQuestionId : {};
    for (const id of Object.keys(markSrc)) {
      if (!isSafeKey(id)) { stats.unsafeKeysSkipped++; continue; }
      const check = sanitizeCheckValue(markSrc[id], stats);
      if (check) marksByQuestionId[id] = check;
    }
    const bookmarks = [];
    for (const b of Array.isArray(raw.bookmarks) ? raw.bookmarks : []) {
      if (!isSafeKey(b)) { if (typeof b === "string") stats.unsafeKeysSkipped++; else stats.invalidDropped++; continue; }
      if (bookmarks.indexOf(b) >= 0) { stats.duplicatesRemoved++; continue; }
      bookmarks.push(b);
    }
    const payload = {
      schemaVersion: SCHEMA_VERSION,
      contentVersion: typeof raw.contentVersion === "string" ? raw.contentVersion : null,
      attemptsByQuestionId,
      marksByQuestionId,
      bookmarks,
      lastSession: sanitizeLastSession(raw.lastSession),
    };
    return { payload, stats };
  }

  function stableSortByTime(list) {
    return list
      .map((a, i) => ({ a, i, t: toMillis(a.at) }))
      .sort((x, y) => x.t - y.t || x.i - y.i)
      .map((x) => x.a);
  }

  function bankMap(questions) {
    const m = new Map();
    for (const q of Array.isArray(questions) ? questions : []) if (q && typeof q.id === "string") m.set(q.id, q);
    return m;
  }

  // ---------- storage adapter ----------
  function defaultStorage() {
    try { return typeof globalThis !== "undefined" && globalThis.localStorage ? globalThis.localStorage : null; }
    catch (e) { return null; }
  }

  function createStore(opts) {
    const o = opts || {};
    const storage = o.storage === undefined ? defaultStorage() : o.storage;
    // Fixed key only: a caller must never be able to point the store at another key
    // (e.g. "pn-study-split-core-pct").
    if (o.key !== undefined && o.key !== null && o.key !== STORAGE_KEY) {
      throw new Error('createStore: only the fixed key "' + STORAGE_KEY + '" is allowed');
    }
    const key = STORAGE_KEY;
    const contentVersion = o.contentVersion === undefined ? null : o.contentVersion;

    function read() {
      if (!storage) return { status: "unavailable", state: createEmptyState(contentVersion) };
      let text;
      try { text = storage.getItem(key); }
      catch (e) { return { status: "unavailable", state: createEmptyState(contentVersion), error: String(e && e.message || e) }; }
      if (text === null || text === undefined) return { status: "empty", state: createEmptyState(contentVersion) };
      let raw;
      try { raw = JSON.parse(text); }
      catch (e) { return { status: "corrupt", state: createEmptyState(contentVersion), error: String(e && e.message || e) }; }
      if (!isPlainObject(raw)) return { status: "corrupt", state: createEmptyState(contentVersion), error: "payload is not an object" };
      if (raw.schemaVersion !== SCHEMA_VERSION) return { status: "unknown-schema", state: createEmptyState(contentVersion), schemaVersion: raw.schemaVersion };
      return { status: "ok", state: sanitizePayload(raw).payload };
    }

    function load() { return read(); }

    function save(state, saveOpts) {
      if (!storage) return { ok: false, reason: "no-storage" };
      // Re-read at save time: another tab may have written unknown-schema/corrupt data since load().
      const check = read();
      const status = check.status; // never clobber data we could not understand
      // If the safety re-read itself failed (getItem threw), we cannot tell what is stored:
      // refuse to write, even with overwrite.
      if (status === "unavailable") {
        return { ok: false, reason: "storage-error", error: check.error || "storage unavailable during pre-save read" };
      }
      if ((status === "corrupt" || status === "unknown-schema") && !(saveOpts && saveOpts.overwrite)) {
        return { ok: false, reason: "blocked-" + status };
      }
      const payload = sanitizePayload(state || {}).payload;
      if (contentVersion !== null) payload.contentVersion = contentVersion;
      try { storage.setItem(key, JSON.stringify(payload)); }
      catch (e) { return { ok: false, reason: "storage-error", error: String(e && e.message || e) }; }
      return { ok: true };
    }

    return { load, save, key };
  }

  // ---------- backup ----------
  function exportBackup(state, opts) {
    const payload = sanitizePayload(state).payload;
    const exportedAt = opts && opts.exportedAt ? opts.exportedAt : new Date().toISOString();
    return JSON.stringify(Object.assign({ kind: BACKUP_KIND, exportedAt }, payload), null, 2);
  }

  function parseBackup(text, questions) {
    const fail = (msg) => ({ ok: false, errors: [msg], warnings: [], payload: null, summary: null });
    if (typeof text !== "string" || text.trim() === "") return fail("invalid-input: backup text is empty");
    let raw;
    try { raw = JSON.parse(text); }
    catch (e) { return fail("invalid-json: " + String(e && e.message || e)); }
    if (!isPlainObject(raw)) return fail("invalid-shape: backup must be a JSON object");
    if (raw.kind !== undefined && raw.kind !== BACKUP_KIND) return fail("invalid-kind: not a PN study progress backup");
    if (raw.schemaVersion !== SCHEMA_VERSION) return fail("unsupported-schema: schemaVersion " + String(raw.schemaVersion) + " (expected " + SCHEMA_VERSION + ")");
    if (!isPlainObject(raw.attemptsByQuestionId)) return fail("invalid-shape: attemptsByQuestionId missing");

    const bank = bankMap(questions);
    const { payload, stats } = sanitizePayload(raw, bank);
    const ids = Object.keys(payload.attemptsByQuestionId);
    const markIds = Object.keys(payload.marksByQuestionId);
    const summary = {
      attempts: ids.reduce((n, id) => n + payload.attemptsByQuestionId[id].length, 0),
      questions: ids.length,
      matchedQuestions: 0,
      staleQuestions: 0,
      orphanIds: 0,
      bookmarks: payload.bookmarks.length,
      markedQuestions: markIds.length,
      duplicatesRemoved: stats.duplicatesRemoved,
      invalidDropped: stats.invalidDropped,
      regraded: stats.regraded,
      contentVersion: payload.contentVersion,
    };
    for (const id of ids) {
      const q = bank.get(id);
      if (!q) summary.orphanIds++;
      else if (payload.attemptsByQuestionId[id].some((a) => a.revision === revisionOf(q))) summary.matchedQuestions++;
      else summary.staleQuestions++;
    }
    const warnings = [];
    if (stats.duplicatesRemoved) warnings.push(stats.duplicatesRemoved + " duplicate entries collapsed");
    if (stats.invalidDropped) warnings.push(stats.invalidDropped + " malformed entries dropped");
    if (stats.unsafeKeysSkipped) warnings.push(stats.unsafeKeysSkipped + " reserved keys skipped");
    if (stats.regraded) warnings.push(stats.regraded + " attempts re-graded against the current answer key");
    if (summary.staleQuestions) warnings.push(summary.staleQuestions + " questions changed revision; their old attempts are kept as history only");
    if (summary.orphanIds) warnings.push(summary.orphanIds + " ids are not in the current question bank; kept but not linked");
    return { ok: true, errors: [], warnings, payload, summary };
  }

  function applyBackup(preview, state, opts) {
    const o = opts || {};
    if (!preview || preview.ok !== true || !preview.payload) throw new Error("applyBackup needs a valid preview from parseBackup");
    if (o.confirmed !== true) throw new Error("applyBackup requires explicit confirmation ({confirmed:true})");
    const mode = o.mode === undefined ? "merge" : o.mode;
    if (mode !== "merge" && mode !== "replace") throw new TypeError('mode must be "merge" or "replace"');
    const cv = o.contentVersion !== undefined ? o.contentVersion : state.contentVersion;
    const inc = preview.payload;
    if (mode === "replace") {
      return Object.assign(createEmptyState(cv), {
        attemptsByQuestionId: JSON.parse(JSON.stringify(inc.attemptsByQuestionId)),
        marksByQuestionId: JSON.parse(JSON.stringify(inc.marksByQuestionId || {})),
        bookmarks: inc.bookmarks.slice(),
        lastSession: inc.lastSession ? Object.assign({}, inc.lastSession) : null,
      });
    }
    const attempts = {};
    const idsAll = Object.keys(state.attemptsByQuestionId).concat(Object.keys(inc.attemptsByQuestionId));
    for (const id of idsAll) {
      if (has(attempts, id)) continue;
      const seen = new Set();
      const list = [];
      for (const src of [state.attemptsByQuestionId, inc.attemptsByQuestionId]) {
        if (!has(src, id)) continue;
        for (const a of src[id]) {
          const k = attemptKey(a);
          if (seen.has(k)) continue;
          seen.add(k);
          list.push(Object.assign({}, a));
        }
      }
      attempts[id] = stableSortByTime(list);
    }
    const marksByQuestionId = {};
    const markIds = Object.keys(state.marksByQuestionId || {}).concat(Object.keys(inc.marksByQuestionId || {}));
    for (const id of markIds) {
      if (has(marksByQuestionId, id)) continue;
      let best = CHECK_NONE;
      for (const src of [state.marksByQuestionId || {}, inc.marksByQuestionId || {}]) {
        if (!has(src, id)) continue;
        const c = coerceCheck(src[id]);
        if ((CHECK_RANK[c] || 0) > (CHECK_RANK[best] || 0)) best = c;
      }
      if (best !== CHECK_NONE) marksByQuestionId[id] = best;
    }
    const bookmarks = state.bookmarks.slice();
    for (const b of inc.bookmarks) if (bookmarks.indexOf(b) < 0) bookmarks.push(b);
    let lastSession = state.lastSession;
    if (inc.lastSession && (!lastSession || toMillis(inc.lastSession.at) > toMillis(lastSession.at))) lastSession = inc.lastSession;
    return {
      schemaVersion: SCHEMA_VERSION,
      contentVersion: cv === undefined ? null : cv,
      attemptsByQuestionId: attempts,
      marksByQuestionId,
      bookmarks,
      lastSession: lastSession ? Object.assign({}, lastSession) : null,
    };
  }

  return {
    STORAGE_KEY, SCHEMA_VERSION, BACKUP_KIND,
    CHECK_NONE, CHECK_O, CHECK_X,
    gradeAttempt, createEmptyState, getCheck, setCheck, cycleCheck, hasCheck,
    recordAttempt, latestAttempt, toggleBookmark, setLastSession,
    normalizeFilter, selectReviewQuestions, summarizeProgress,
    createStore, exportBackup, parseBackup, applyBackup,
  };
});
