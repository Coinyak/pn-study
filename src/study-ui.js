/* study-ui.js — quiz pane UI (answer, grade, review filters, search, resume, backup/restore,
 * practice session) on top of StudyState (src/study-state.js). All progress mutation goes
 * through StudyState; this file never touches localStorage directly.
 *
 * Inlined after the split shell's script, so it can use the shell's globals (QUESTION_BANK,
 * QUESTIONS, activeTopic, TOPIC_LABEL, CORE_SKIP, escapeHtml, setTopic, setPane,
 * highlightFromQuestion, clearCoreHl). It replaces the shell's read-only renderQuiz().
 *
 * Node: require("./study-ui.js") returns the pure helpers only (no DOM).
 */
(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else {
    root.StudyUI = api;
    if (root.document) api.mount();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";

  const FILTERS = [["all", "전체"], ["unseen", "미풀이"], ["wrong", "오답"], ["unsure", "헷갈림"], ["bookmarked", "즐겨찾기"]];
  const REVIEW_FILTERS = ["wrong", "unsure", "bookmarked"];
  const MOCK_PLAN = { common: 20, pn: 80 };
  const COMMON_TOPIC = "common";

  // ---------- pure helpers ----------
  const isKo = (q) => q.language === undefined || q.language === null || q.language === "ko";

  /**
   * Core origin label for display/filter. Hides intermediary tags (OpenExamPrep, QZ, VERIFIED/,
   * "Quizlet indexed") and shows the underlying bank/module (BCNSP, CNSC, ASPEN PN, …).
   */
  function coreSourceLabel(q) {
    const id = String((q && q.id) || "");
    const s = String((q && q.source) || "");
    if (id.indexOf("kshp-") === 0 || /병원약사회/.test(s)) return "병원약사회";
    if (id.indexOf("bcnsp-") === 0 || s === "OE-B" || s === "BCNSP") return "BCNSP";
    if (id.indexOf("cnsc-") === 0 || s === "OE-C" || s === "CNSC") return "CNSC";
    if (id.indexOf("nbnsc-") === 0 || s === "VERIFIED/CNSC" || s === "VERIFIED") return "CNSC 샘플";
    if (id.indexOf("oep-bcscp") === 0 || /BCSCP/i.test(s)) return "BCSCP";
    if (id.indexOf("rxk-") === 0 || id.indexOf("rx-") === 0 || s === "RX") return "RxKinetics";
    if (id.indexOf("allaccess-") === 0 || s === "AllAccess") return "AllAccess";
    if (id.indexOf("medex-") === 0 || s === "MedEx") return "MedEx";
    if (id.indexOf("hoag-") === 0 || s === "HOAG") return "HOAG";
    if (id.indexOf("op-") === 0 || /자체/.test(s)) return "자체 연습";
    if (id.indexOf("quizlet-pn-") === 0) return "ASPEN PN 모듈";
    if (id.indexOf("quizlet-a14pn-") === 0) return "ASPEN '14 PN";
    if (id.indexOf("quizlet-iib-") === 0) return "ASPEN Module IIB";
    if (id.indexOf("quizlet-m2b-") === 0) return "ASPEN Module 2B";
    if (id.indexOf("quizlet-m4-") === 0) return "ASPEN Module 4";
    if (id.indexOf("quizlet-cnsc-practice-") === 0 || /CNSC Practice/i.test(s)) return "CNSC Practice";
    if (id.indexOf("quizlet-ss2-") === 0 || /Self Study Set 2/i.test(s)) return "ASPEN Self-Study 2";
    if (id.indexOf("quizlet-home-") === 0 || /SAP Home/i.test(s)) return "ASPEN Home NS";
    if (id.indexOf("quizlet-ach-") === 0) return "ASPEN ACH";
    if (id.indexOf("quizlet-cna-") === 0) return "ASPEN CNA";
    if (id.indexOf("quizlet-cp-") === 0) return "ASPEN CP";
    if (id.indexOf("aspen-") === 0 || /Self-Study CNSC/i.test(s)) return "ASPEN Self-Study CNSC";
    if (/Nutrition Support Review/i.test(s)) return "Nutrition Support Review";
    let cleaned = s
      .replace(/^VERIFIED\/?/i, "")
      .replace(/\s*\(Quizlet indexed\)/ig, "")
      .replace(/\s*\(Quizlet\)/ig, "")
      .replace(/OpenExamPrep\s*/ig, "")
      .trim();
    if (!cleaned || cleaned === "QZ" || /^OE-/i.test(cleaned)) return "기타";
    return cleaned;
  }

  function sourceToneClass(label) {
    const L = String(label || "");
    if (L === "병원약사회") return "src-kshp";
    if (L === "자체 연습") return "src-practice";
    if (L === "RxKinetics") return "src-rx";
    if (L === "BCNSP" || L === "BCSCP") return "src-bcnsp";
    if (L.indexOf("CNSC") === 0) return "src-cnsc";
    if (L.indexOf("ASPEN") === 0) return "src-aspen";
    if (L === "AllAccess") return "src-allaccess";
    if (L === "MedEx") return "src-medex";
    if (L === "HOAG") return "src-hoag";
    return "src-other";
  }

  /** Questions that may be shown at all (never excluded, Korean only). */
  function isDisplayable(q) {
    return !!q && q.reviewStatus !== "excluded" && isKo(q);
  }

  /** Default pool = includeInBasicSet; pending only when the user opts in. */
  function basePool(bank, includePending) {
    return bank.filter((q) => q.includeInBasicSet === true || (includePending && q.reviewStatus === "pending" && isKo(q)));
  }

  function normSearch(s) {
    return String(s || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function matchesSearch(q, query) {
    const terms = normSearch(query).split(" ").filter(Boolean);
    if (!terms.length) return true;
    const hay = normSearch([q.id, q.source, q.stem].concat(q.choices || [], [q.explain]).join(" "));
    return terms.every((t) => hay.indexOf(t) >= 0);
  }

  /**
   * Questions for the list view.
   * opts: { filter, search, topic, scope: "topic"|"all", includePending }
   * Review filters (wrong/unsure/bookmarked) look at every displayable question, so an answered
   * pending item still shows up in 오답 after the 검토 대기 toggle is turned off again.
   * A non-empty search always spans every topic.
   */
  function buildList(bank, state, opts, SS) {
    const o = opts || {};
    const filter = SS.normalizeFilter(o.filter || "all");
    let pool = REVIEW_FILTERS.indexOf(filter) >= 0 ? bank.filter(isDisplayable) : basePool(bank, !!o.includePending);
    if (normSearch(o.search)) pool = pool.filter((q) => matchesSearch(q, o.search));
    else if (o.scope !== "all" && o.topic) pool = pool.filter((q) => q.topic === o.topic);
    if (o.sourceLabel) pool = pool.filter((q) => coreSourceLabel(q) === o.sourceLabel);
    return SS.selectReviewQuestions(pool, state, filter);
  }

  function shuffled(list, rng) {
    const a = list.slice();
    const r = rng || Math.random;
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(r() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /** Fixed-order session. The id list is frozen at creation; topic changes never alter it. */
  function createSession(questions, opts) {
    const o = opts || {};
    const list = o.shuffle ? shuffled(questions, o.rng) : questions.slice();
    return { id: "s" + (o.now === undefined ? Date.now() : o.now), kind: o.kind || "drill", label: o.label || "", ids: list.map((q) => q.id) };
  }

  /** 20+80 mock exam needs enough verified items in both parts. */
  function mockAvailability(bank) {
    const pool = basePool(bank, false);
    const common = pool.filter((q) => q.topic === COMMON_TOPIC).length;
    const pn = pool.length - common;
    return { ok: common >= MOCK_PLAN.common && pn >= MOCK_PLAN.pn, common, pn, need: MOCK_PLAN };
  }

  function createMockSession(bank, opts) {
    const pool = basePool(bank, false);
    const rng = opts && opts.rng;
    const common = shuffled(pool.filter((q) => q.topic === COMMON_TOPIC), rng).slice(0, MOCK_PLAN.common);
    const pn = shuffled(pool.filter((q) => q.topic !== COMMON_TOPIC), rng).slice(0, MOCK_PLAN.pn);
    return createSession(common.concat(pn), Object.assign({}, opts, { shuffle: false, kind: "mock", label: "모의고사 20+80" }));
  }

  /** Every view except 전체 (all) derives membership from study state (unseen/wrong/unsure/bookmarked). */
  function filterUsesState(filter) {
    return !!filter && filter !== "all";
  }

  /**
   * After a state mutation rebuilt the list: which question gets focus?
   * The mutated card if it is still listed; otherwise the next previously-listed card that
   * survived (then the nearest earlier one); otherwise (e.g. a cleared source chip swapped in cards
   * from other sources, so nothing from the old list survived) the first card of the new list;
   * null only when the list is now empty.
   */
  function focusAfterRebuild(oldIds, mutatedId, newIds) {
    if (newIds.indexOf(mutatedId) >= 0) return mutatedId;
    const at = oldIds.indexOf(mutatedId);
    if (at < 0) return newIds.length ? newIds[0] : null;
    for (let i = at + 1; i < oldIds.length; i++) if (newIds.indexOf(oldIds[i]) >= 0) return oldIds[i];
    for (let i = at - 1; i >= 0; i--) if (newIds.indexOf(oldIds[i]) >= 0) return oldIds[i];
    return newIds.length ? newIds[0] : null;
  }

  const api = {
    FILTERS, MOCK_PLAN, filterUsesState, focusAfterRebuild, isDisplayable, basePool, matchesSearch, buildList, createSession,
    mockAvailability, createMockSession, coreSourceLabel, sourceToneClass, mount,
  };

  // ---------- DOM ----------
  function mount() {
    const doc = root.document;
    const SS = root.StudyState;
    const list = doc.getElementById("quizList");
    const head = doc.getElementById("quizHead");
    if (!SS || !list || !head || typeof QUESTION_BANK === "undefined") return;

    const BANK = QUESTION_BANK;
    const BY_ID = new Map(BANK.map((q) => [q.id, q]));
    const CV = typeof PN_CONTENT_VERSION === "string" ? PN_CONTENT_VERSION : null;
    const esc = typeof escapeHtml === "function" ? escapeHtml
      : (s) => String(s).replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
    const topicNow = () => (typeof activeTopic !== "undefined" ? activeTopic : null);
    const topicLabel = (t) => (typeof TOPIC_LABEL !== "undefined" && TOPIC_LABEL[t]) || t || "";
    const coreLinked = (q) => !(typeof CORE_SKIP !== "undefined" && CORE_SKIP.has(q.id));
    const isMobile = () => root.matchMedia && root.matchMedia("(max-width:899px)").matches;

    const store = SS.createStore({ contentVersion: CV });
    const loaded = store.load();
    let state = loaded.state;
    const loadStatus = loaded.status;

    const ui = {
      mode: "learn", filter: "all", scope: "topic", search: "", includePending: false, sourceLabel: "",
      session: null, sessionCards: new Map(), learnCards: new Map(), listVersion: 0, stateRev: 0, lastKey: null, lastSaveReason: null,
    };

    // ----- toolbar -----
    const bar = doc.createElement("div");
    bar.className = "study-bar";
    bar.id = "studyBar";
    const mock = mockAvailability(BANK);
    bar.innerHTML =
      '<div class="sb-row">' +
        '<label class="sb-field"><span class="sb-lab">모드</span> <select id="sbMode">' +
          '<option value="learn">학습(핵심 연계)</option>' +
          '<option value="drill">연습 세션(순서 고정)</option>' +
          '<option value="mock"' + (mock.ok ? "" : " disabled") + ">모의고사 20+80" + (mock.ok ? "" : " · 검증 문항 부족") + "</option>" +
        "</select></label>" +
        '<label class="sb-field"><span class="sb-lab">보기</span> <select id="sbFilter">' + FILTERS.map((f) => '<option value="' + f[0] + '">' + f[1] + "</option>").join("") + "</select></label>" +
        '<label class="sb-field"><span class="sb-lab">범위</span> <select id="sbScope"><option value="topic">현재 소단원</option><option value="all">전체 단원</option></select></label>' +
        '<input type="search" id="sbSearch" class="sb-search" placeholder="문항 검색" aria-label="문항 검색(전체 단원)" enterkeyhint="search">' +
      "</div>" +
      '<div class="sb-row">' +
        '<label class="sb-chk" title="검토가 끝나지 않은 문항. 정답·해설이 바뀔 수 있습니다."><input type="checkbox" id="sbPending"> 검토 대기 포함</label>' +
        '<button type="button" class="sb-btn" id="sbResume" hidden>이어하기</button>' +
        '<button type="button" class="sb-btn" id="sbExport" title="학습 기록을 JSON 파일로 저장">백업</button>' +
        '<button type="button" class="sb-btn" id="sbImport" title="백업 파일에서 학습 기록 불러오기">복원</button>' +
        '<input type="file" id="sbFile" accept=".json,application/json" hidden>' +
        '<span class="sb-sum" id="sbSum"></span>' +
      "</div>" +
      '<div class="sb-row sb-sources" id="sbSources" aria-label="출처 필터"></div>' +
      '<div class="sb-panel" id="sbSession" hidden></div>' +
      '<div class="sb-panel" id="sbRestore" hidden></div>' +
      '<div class="sb-notice" id="sbNotice" role="status" aria-live="polite" hidden></div>';
    head.insertAdjacentElement("afterend", bar);
    const $ = (id) => doc.getElementById(id);
    const el = {
      mode: $("sbMode"), filter: $("sbFilter"), scope: $("sbScope"), search: $("sbSearch"), pending: $("sbPending"),
      resume: $("sbResume"), exp: $("sbExport"), imp: $("sbImport"), file: $("sbFile"), sum: $("sbSum"),
      session: $("sbSession"), restore: $("sbRestore"), notice: $("sbNotice"), title: $("quizHeadTitle") || head,
      sources: $("sbSources"),
    };

    // ----- notices / persistence -----
    let noticeTimer = null;
    function notice(msg, sticky) {
      clearTimeout(noticeTimer);
      el.notice.textContent = msg;
      el.notice.hidden = !msg;
      if (msg && !sticky) noticeTimer = setTimeout(() => { el.notice.hidden = true; }, 8000);
    }
    const SAVE_MSG = {
      "no-storage": "브라우저 저장소를 쓸 수 없어 이 창에서만 기록됩니다. 계속 풀 수 있습니다.",
      "storage-error": "기록 저장에 실패했습니다(용량·권한). 계속 풀 수 있지만 새로고침하면 사라질 수 있습니다.",
      "blocked-corrupt": "저장된 기록을 읽을 수 없어 덮어쓰지 않았습니다. 이 창에서만 기록됩니다.",
      "blocked-unknown-schema": "다른 버전의 기록이 저장돼 있어 덮어쓰지 않았습니다. 이 창에서만 기록됩니다.",
    };
    function persist(opts) {
      const r = store.save(state, opts);
      if (r.ok) { ui.lastSaveReason = null; return true; }
      if (r.reason !== ui.lastSaveReason) notice(SAVE_MSG[r.reason] || "기록을 저장하지 못했습니다.", false);
      ui.lastSaveReason = r.reason;
      return false;
    }
    if (loadStatus === "unavailable") notice(SAVE_MSG["no-storage"], false);
    else if (loadStatus === "corrupt") notice("저장된 학습 기록이 손상돼 읽지 못했습니다. 기존 데이터는 그대로 두며, 복원(교체)으로 정리할 수 있습니다.", true);
    else if (loadStatus === "unknown-schema") notice("다른 버전의 학습 기록이 있어 읽지 못했습니다. 기존 데이터는 그대로 둡니다.", true);

    // ----- list -----
    function listKey() {
      const s = ui.session;
      // stateRev counts study-state mutations (submit, bookmark, restore); state-derived filters
      // (미풀이/오답/헷갈림/즐겨찾기) must rebuild when it moves. A frozen session never depends on it.
      return JSON.stringify(s ? ["s", s.id, ui.listVersion]
        : [ui.mode, ui.filter, ui.scope, ui.search, ui.includePending, ui.sourceLabel, ui.scope === "all" || ui.search ? "" : topicNow(), ui.listVersion,
          filterUsesState(ui.filter) ? ui.stateRev : 0]);
    }
    function currentItems() {
      if (ui.session) return ui.session.ids.map((id) => BY_ID.get(id)).filter(Boolean);
      return buildList(BANK, state, {
        filter: ui.filter, search: ui.search, topic: topicNow(), scope: ui.scope,
        includePending: ui.includePending, sourceLabel: ui.sourceLabel || "",
      }, SS);
    }
    function poolForSourceChips() {
      // Chips reflect the current view before source filter (so counts stay honest).
      return buildList(BANK, state, {
        filter: ui.filter, search: ui.search, topic: topicNow(), scope: ui.scope,
        includePending: ui.includePending, sourceLabel: "",
      }, SS);
    }
    function renderSourceChips() {
      if (!el.sources || ui.session) {
        if (el.sources) el.sources.innerHTML = "";
        return;
      }
      const pool = poolForSourceChips();
      const counts = new Map();
      pool.forEach((q) => {
        const lab = coreSourceLabel(q);
        counts.set(lab, (counts.get(lab) || 0) + 1);
      });
      if (ui.sourceLabel && !counts.has(ui.sourceLabel)) ui.sourceLabel = "";
      const labels = Array.from(counts.keys()).sort((a, b) => a.localeCompare(b, "ko"));
      el.sources.innerHTML =
        '<button type="button" class="sb-src' + (ui.sourceLabel ? "" : " on") + '" data-src="">전체 (' + pool.length + ")</button>" +
        labels.map((lab) => {
          const on = ui.sourceLabel === lab ? " on" : "";
          return '<button type="button" class="sb-src ' + sourceToneClass(lab) + on + '" data-src="' + esc(lab) + '">' +
            esc(lab) + " (" + counts.get(lab) + ")</button>";
        }).join("");
    }
    const cards = () => (ui.session ? ui.sessionCards : ui.learnCards);
    function cardState(id) {
      const m = cards();
      if (!m.has(id)) m.set(id, { selected: null, unsure: false, result: null, explain: false });
      return m.get(id);
    }

    function statusBadge(q) {
      const last = SS.latestAttempt(q, state);
      if (!last) return "";
      const t = last.correct ? (last.confidence === "unsure" ? "맞음·헷갈림" : "맞음") : "틀림";
      return ' · <span class="q-last ' + (last.correct ? "ok" : "ng") + '">지난 풀이 ' + t + "</span>";
    }

    function cardHtml(q, idx) {
      const cs = cardState(q.id);
      const inSession = !!ui.session;
      const done = !!cs.result;
      const linked = coreLinked(q);
      const bm = state.bookmarks.indexOf(q.id) >= 0;
      const pending = q.reviewStatus === "pending" ? ' · <span class="q-pending">검토 대기</span>' : "";
      const num = inSession ? '<b class="q-no">' + (idx + 1) + ".</b> " : "";
      const name = "ans-" + idx;
      const choices = q.choices.map((c, i) => {
        let cls = "q-choice";
        if (done && i === cs.result.answer) cls += " is-answer";
        if (done && i === cs.result.selected && !cs.result.correct) cls += " is-wrong";
        return '<label class="' + cls + '"><input type="radio" name="' + name + '" value="' + i + '"' +
          (cs.selected === i ? " checked" : "") + (done ? " disabled" : "") + '><span class="q-n">' + (i + 1) + '.</span><span class="q-t">' + esc(c) + "</span></label>";
      }).join("");
      const showCore = linked && (!inSession || done);
      const canExplain = !inSession || done;
      let result = "";
      if (done) {
        const r = cs.result;
        result = r.correct ? '<span class="ok">정답</span>' : '<span class="ng">오답</span> · 정답 ' + (r.answer + 1) + "번";
        if (cs.unsure) result += " · 헷갈림 표시";
      }
      let explain = "";
      if (cs.explain && canExplain) {
        const ce = Array.isArray(q.choiceExplanations) ? q.choiceExplanations : [];
        const sel = done ? cs.result.selected : null;
        explain = '<div class="q-explain"><p><b>정답:</b> ' + (q.answer + 1) + ". " + esc(q.choices[q.answer] || "") + "</p>" +
          (q.explain ? "<p>" + esc(q.explain) + "</p>" : "") +
          (sel !== null && sel !== q.answer && ce[sel] ? '<p class="muted">내 선택 ' + (sel + 1) + "번: " + esc(ce[sel]) + "</p>" : "") +
          "</div>";
      }
      return '<article class="qcard sq" data-qid="' + esc(q.id) + '" data-idx="' + idx + '">' +
        '<div class="q-top"><div class="src">' + num +
          '<span class="src-meta ' + sourceToneClass(coreSourceLabel(q)) + '">' + esc(coreSourceLabel(q)) + "</span>" +
          " · " + esc(q.id) + (linked ? "" : " · 핵심 연결 없음") + pending + statusBadge(q) + "</div>" +
        '<button type="button" class="q-bm" data-act="bookmark" aria-pressed="' + bm + '" aria-label="즐겨찾기" title="즐겨찾기">' + (bm ? "★" : "☆") + "</button></div>" +
        '<div class="stem" id="stem-' + idx + '">' + esc(q.stem) + "</div>" +
        '<fieldset class="q-choices" aria-labelledby="stem-' + idx + '"><legend class="sr-only">선택지</legend>' + choices + "</fieldset>" +
        '<div class="q-actions">' +
          '<label class="q-unsure"><input type="checkbox" data-act="unsure"' + (cs.unsure ? " checked" : "") + (done ? " disabled" : "") + "> 헷갈림</label>" +
          (done
            ? (inSession ? "" : '<button type="button" class="sb-btn" data-act="retry">다시 풀기</button>')
            : '<button type="button" class="sb-btn primary" data-act="submit"' + (cs.selected === null ? " disabled" : "") + ">제출</button>") +
          (canExplain ? '<button type="button" class="sb-btn" data-act="explain" aria-expanded="' + !!cs.explain + '">' + (cs.explain ? "해설 닫기" : "해설 보기") + "</button>" : "") +
          (showCore ? '<button type="button" class="sb-btn" data-act="core" title="왼쪽 핵심본에서 관련 위치 표시">핵심 위치</button>' : "") +
          '<span class="q-result" tabindex="-1">' + result + "</span>" +
        "</div>" + explain + "</article>";
    }

    function headTitle(items) {
      if (ui.session) {
        const m = ui.sessionCards;
        const doneN = ui.session.ids.filter((id) => m.has(id) && m.get(id).result).length;
        const ok = ui.session.ids.filter((id) => m.has(id) && m.get(id).result && m.get(id).result.correct).length;
        return (ui.session.label || "연습 세션") + " · " + doneN + "/" + ui.session.ids.length + " 제출 · 정답 " + ok;
      }
      const f = FILTERS.find((x) => x[0] === ui.filter)[1];
      const where = ui.search ? "검색「" + ui.search + "」" : ui.scope === "all" ? "전체 단원" : topicLabel(topicNow());
      const src = ui.sourceLabel ? " · " + ui.sourceLabel : "";
      return "관련 문제 · " + where + src + (ui.filter === "all" ? "" : " · " + f) + " (" + items.length + ")";
    }

    function emptyText() {
      if (ui.search) return "검색 결과가 없습니다.";
      if (ui.filter !== "all") return "조건에 맞는 문항이 없습니다. 보기·범위를 바꿔 보세요.";
      return "이 소단원에 검증 완료 문항이 아직 없습니다(검토 대기 문항은 기본 세트에서 제외). 왼쪽에서 다른 소단원을 고르거나 범위를 「전체 단원」으로 바꾸세요.";
    }

    function updateSummary() {
      const s = SS.summarizeProgress(basePool(BANK, ui.includePending), state);
      el.sum.textContent = "풀이 " + s.seen + "/" + s.total + " · 오답 " + s.wrong + " · 헷갈림 " + s.unsure + " · ★" + s.bookmarked;
      const ls = state.lastSession;
      const q = ls && BY_ID.get(ls.questionId);
      el.resume.hidden = !q || !isDisplayable(q) || !!ui.session;
      if (q) el.resume.textContent = "이어하기 · " + topicLabel(ls.topic || q.topic);
    }

    function renderQuiz(force) {
      renderSourceChips();
      const key = listKey();
      const items = currentItems();
      el.title.textContent = headTitle(items);
      updateSummary();
      if (!force && key === ui.lastKey) return;
      ui.lastKey = key;
      list.dataset.topic = topicNow() || "";
      list.innerHTML = items.length ? items.map(cardHtml).join("") : '<div class="empty">' + emptyText() + "</div>";
    }

    function rerenderCard(card, focusSel) {
      const q = BY_ID.get(card.dataset.qid);
      const idx = Number(card.dataset.idx);
      card.insertAdjacentHTML("afterend", cardHtml(q, idx));
      const next = card.nextElementSibling;
      card.remove();
      el.title.textContent = headTitle(currentItems());
      updateSummary();
      if (focusSel) {
        const f = next.querySelector(focusSel);
        if (f) f.focus({ preventScroll: false });
      }
      return next;
    }

    function scrollerOf(node) {
      for (let n = node; n && n.nodeType === 1; n = n.parentElement) {
        const oy = root.getComputedStyle ? root.getComputedStyle(n).overflowY : "";
        if ((oy === "auto" || oy === "scroll") && n.scrollHeight > n.clientHeight) return n;
      }
      return list;
    }

    /**
     * A study-state change (submit, bookmark, restore) may change which questions belong to the
     * current filter. Bump stateRev so listKey() moves, rebuild, and keep focus/scroll: the card
     * stays if it still qualifies, otherwise focus goes to the next remaining card.
     */
    function afterStateChange(card, focusSel) {
      ui.stateRev++;
      if (ui.session || !filterUsesState(ui.filter)) {
        const next = rerenderCard(card, focusSel);
        ui.lastKey = listKey();
        return next;
      }
      const id = card.dataset.qid;
      const oldIds = Array.from(list.querySelectorAll(".qcard.sq")).map((c) => c.dataset.qid);
      const sc = scrollerOf(list);
      const top = sc.scrollTop;
      renderQuiz();
      sc.scrollTop = top;
      const newIds = Array.from(list.querySelectorAll(".qcard.sq")).map((c) => c.dataset.qid);
      const target = focusAfterRebuild(oldIds, id, newIds);
      const find = (qid) => list.querySelector('.qcard[data-qid="' + (root.CSS && CSS.escape ? CSS.escape(qid) : qid) + '"]');
      if (target === id) {
        const f = focusSel && find(id).querySelector(focusSel);
        if (f) f.focus({ preventScroll: true });
      } else {
        notice("현재 보기(" + FILTERS.find((x) => x[0] === ui.filter)[1] + ") 조건에서 벗어나 목록에서 제외했습니다.", false);
        const t = target && find(target);
        const f = t ? (t.querySelector('input[type="radio"]:not(:disabled)') || t.querySelector("button:not(:disabled)")) : null;
        if (f) f.focus({ preventScroll: true });
        else {
          // Never leave focus detached: the card itself, then the empty state, then the list.
          const e = t || list.querySelector(".empty") || list;
          e.tabIndex = -1;
          e.focus({ preventScroll: true });
        }
      }
    }

    // ----- answer actions -----
    function submit(card) {
      const q = BY_ID.get(card.dataset.qid);
      if (!q) return;
      const cs = cardState(q.id);
      if (cs.selected === null || cs.result) return;
      const g = SS.gradeAttempt(q, cs.selected);
      cs.result = { correct: g.correct, answer: g.answer, selected: cs.selected };
      state = SS.recordAttempt(state, q, cs.selected, cs.unsure ? "unsure" : "sure");
      const ls = { questionId: q.id, at: state.lastSession.at, topic: q.topic };
      if (!ui.session) ls.filter = ui.filter;
      state = SS.setLastSession(state, ls);
      persist();
      afterStateChange(card, ".q-result");
      if (ui.session && ui.session.ids.every((id) => ui.sessionCards.has(id) && ui.sessionCards.get(id).result)) renderSessionPanel();
    }

    function showCore(card) {
      const q = BY_ID.get(card.dataset.qid);
      if (!q || !coreLinked(q) || typeof highlightFromQuestion !== "function") return;
      list.querySelectorAll(".qcard.hl").forEach((c) => c.classList.toggle("hl", c === card));
      card.classList.add("hl");
      // Outside topic-scoped learn view the list does not depend on activeTopic, so aim at the
      // question's own topic; in topic view they already match.
      if (typeof activeTopic !== "undefined" && (ui.session || ui.scope === "all" || ui.search)) activeTopic = q.topic; // eslint-disable-line no-global-assign
      highlightFromQuestion(q);
      if (!doc.querySelector(".core-hl, .core-hl-exact")) notice("핵심본에서 이 문항의 위치를 찾지 못했습니다.", false);
    }

    list.addEventListener("change", (e) => {
      const card = e.target.closest(".qcard.sq");
      if (!card) return;
      const cs = cardState(card.dataset.qid);
      if (e.target.type === "radio") {
        cs.selected = Number(e.target.value);
        const b = card.querySelector('[data-act="submit"]');
        if (b) b.disabled = false;
      } else if (e.target.dataset.act === "unsure") {
        cs.unsure = e.target.checked;
      }
    });
    list.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" || !e.target.matches('.qcard.sq input[type="radio"]')) return;
      e.preventDefault();
      const card = e.target.closest(".qcard");
      cardState(card.dataset.qid).selected = Number(e.target.value);
      submit(card);
    });
    list.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-act]");
      const card = btn && btn.closest(".qcard.sq");
      if (!card) return;
      const id = card.dataset.qid;
      const cs = cardState(id);
      const act = btn.dataset.act;
      if (act === "submit") submit(card);
      else if (act === "retry") { cs.selected = null; cs.result = null; cs.unsure = false; cs.explain = false; rerenderCard(card, 'input[type="radio"]'); }
      else if (act === "explain") { cs.explain = !cs.explain; rerenderCard(card, '[data-act="explain"]'); }
      else if (act === "core") showCore(card);
      else if (act === "bookmark") {
        state = SS.toggleBookmark(state, id);
        persist();
        afterStateChange(card, '[data-act="bookmark"]');
      }
    });

    // ----- toolbar actions -----
    function readControls() {
      ui.filter = el.filter.value;
      ui.scope = el.scope.value;
      ui.search = el.search.value.trim();
      ui.includePending = el.pending.checked;
    }
    [el.filter, el.scope, el.pending].forEach((c) => c.addEventListener("change", () => { readControls(); renderQuiz(); }));
    el.sources.addEventListener("click", (e) => {
      const b = e.target.closest("button.sb-src");
      if (!b || ui.session) return;
      ui.sourceLabel = b.dataset.src || "";
      ui.listVersion++;
      renderQuiz(true);
    });
    let searchTimer = null;
    el.search.addEventListener("input", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { readControls(); renderQuiz(); }, 200);
    });

    function setControlsLocked(locked) {
      [el.filter, el.scope, el.search, el.pending].forEach((c) => { c.disabled = locked; });
    }

    function renderSessionPanel() {
      const p = el.session;
      if (ui.mode === "learn" && !ui.session) { p.hidden = true; p.innerHTML = ""; return; }
      p.hidden = false;
      if (ui.session) {
        const m = ui.sessionCards;
        const doneN = ui.session.ids.filter((id) => m.has(id) && m.get(id).result).length;
        const ok = ui.session.ids.filter((id) => m.has(id) && m.get(id).result && m.get(id).result.correct).length;
        const finished = doneN === ui.session.ids.length;
        p.innerHTML = "<span>" + esc(ui.session.label || "연습 세션") + " " + ui.session.ids.length + "문항 · 순서 고정(스크롤·소단원 이동과 무관)" +
          (finished ? " · <b>완료: " + ok + "/" + doneN + " 정답</b>" : "") + "</span> " +
          '<button type="button" class="sb-btn" data-sact="end">' + (finished ? "세션 닫기" : "세션 종료") + "</button>";
        return;
      }
      const n = currentItems().length;
      const m = mockAvailability(BANK);
      p.innerHTML = "<span>현재 목록 " + n + "문항으로 세션을 만듭니다. 시작하면 문제 순서가 고정됩니다.</span> " +
        '<label class="sb-chk"><input type="checkbox" id="sbShuffle"> 순서 섞기</label> ' +
        '<button type="button" class="sb-btn primary" data-sact="start"' + (n ? "" : " disabled") + ">시작</button> " +
        '<button type="button" class="sb-btn" data-sact="cancel">취소</button>' +
        (m.ok ? "" : '<div class="muted">모의고사 20+80: 검증 문항 부족(공통 ' + m.common + "/" + m.need.common + " · PN " + m.pn + "/" + m.need.pn + "). 검토가 끝나면 열립니다.</div>");
    }

    function startSession(session) {
      ui.session = session;
      ui.sessionCards = new Map();
      setControlsLocked(true);
      el.mode.value = session.kind;
      renderSessionPanel();
      renderQuiz(true);
      list.scrollTop = 0;
    }
    function endSession() {
      ui.session = null;
      ui.mode = "learn";
      el.mode.value = "learn";
      setControlsLocked(false);
      ui.listVersion++;
      renderSessionPanel();
      renderQuiz(true);
    }

    el.mode.addEventListener("change", () => {
      const v = el.mode.value;
      if (ui.session) {
        el.mode.value = ui.session.kind;
        notice("진행 중인 세션을 먼저 종료하세요.", false);
        return;
      }
      ui.mode = v;
      if (v === "mock") {
        const m = mockAvailability(BANK);
        if (!m.ok) { el.mode.value = ui.mode = "learn"; notice("모의고사 20+80: 검증 문항 부족", false); renderSessionPanel(); return; }
        startSession(createMockSession(BANK));
        return;
      }
      renderSessionPanel();
    });
    el.session.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-sact]");
      if (!b) return;
      const a = b.dataset.sact;
      if (a === "start") {
        const sh = doc.getElementById("sbShuffle");
        startSession(createSession(currentItems(), { shuffle: !!(sh && sh.checked), kind: "drill", label: "연습 세션" }));
      } else if (a === "cancel") {
        ui.mode = "learn"; el.mode.value = "learn"; renderSessionPanel();
      } else if (a === "end") endSession();
    });

    el.resume.addEventListener("click", () => {
      const ls = state.lastSession;
      const q = ls && BY_ID.get(ls.questionId);
      if (!q) return;
      el.search.value = "";
      el.scope.value = "topic";
      el.filter.value = ls.filter && FILTERS.some((f) => f[0] === ls.filter) ? ls.filter : "all";
      if (q.includeInBasicSet !== true) el.pending.checked = true;
      readControls();
      const target = (q.coreSectionIds || []).find((id) => doc.getElementById(id)) || null;
      if (typeof setTopic === "function") setTopic(q.topic, { scroll: true, target });
      renderQuiz(true);
      let card = list.querySelector('.qcard[data-qid="' + (root.CSS && CSS.escape ? CSS.escape(q.id) : q.id) + '"]');
      if (!card && ui.filter !== "all") {
        el.filter.value = "all"; readControls(); renderQuiz(true);
        card = list.querySelector('.qcard[data-qid="' + (root.CSS && CSS.escape ? CSS.escape(q.id) : q.id) + '"]');
      }
      if (isMobile() && typeof setPane === "function") setPane("quiz");
      if (card) {
        list.querySelectorAll(".qcard.hl").forEach((c) => c.classList.remove("hl"));
        card.classList.add("hl");
        card.scrollIntoView({ block: "start" });
        const r = card.querySelector('input[type="radio"]:not(:disabled)') || card.querySelector("button");
        if (r) r.focus({ preventScroll: true });
      }
    });

    // ----- backup / restore -----
    el.exp.addEventListener("click", () => {
      const text = SS.exportBackup(state);
      const blob = new Blob([text], { type: "application/json" });
      const a = doc.createElement("a");
      const d = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      a.download = "pn-study-backup-" + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + ".json";
      a.href = URL.createObjectURL(blob);
      doc.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
      notice("백업 파일을 저장했습니다. 다른 기기에서 「복원」으로 불러올 수 있습니다.", false);
    });
    el.imp.addEventListener("click", () => { el.file.value = ""; el.file.click(); });
    let preview = null;
    function closeRestore() { preview = null; el.restore.hidden = true; el.restore.innerHTML = ""; }
    el.file.addEventListener("change", () => {
      const f = el.file.files && el.file.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => showPreview(SS.parseBackup(String(reader.result || ""), BANK));
      reader.onerror = () => showPreview({ ok: false, errors: ["파일을 읽지 못했습니다."], warnings: [] });
      reader.readAsText(f);
    });
    function showPreview(p) {
      preview = p;
      const box = el.restore;
      box.hidden = false;
      if (!p.ok) {
        box.innerHTML = '<b>복원할 수 없는 파일입니다.</b><ul>' + p.errors.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul>" +
          '<button type="button" class="sb-btn" data-ract="cancel">닫기</button>';
        return;
      }
      const s = p.summary;
      const blocked = loadStatus === "corrupt" || loadStatus === "unknown-schema";
      box.innerHTML = "<b>복원 미리보기</b>" +
        '<table class="jg nest sb-prev"><tr><td class="l1">풀이 기록</td><td class="num">' + s.attempts + "건 · " + s.questions + "문항</td></tr>" +
        '<tr><td class="l1">현재 문항과 일치</td><td class="num">' + s.matchedQuestions + "</td></tr>" +
        '<tr><td class="l1">문항 개정됨(이력만)</td><td class="num">' + s.staleQuestions + "</td></tr>" +
        '<tr><td class="l1">현재 없는 문항</td><td class="num">' + s.orphanIds + "</td></tr>" +
        '<tr><td class="l1">즐겨찾기</td><td class="num">' + s.bookmarks + "</td></tr>" +
        '<tr><td class="l1">중복 제거 · 손상 제외 · 재채점</td><td class="num">' + s.duplicatesRemoved + " · " + s.invalidDropped + " · " + s.regraded + "</td></tr>" +
        '<tr><td class="l1">콘텐츠 버전</td><td>' + esc(s.contentVersion || "—") + (CV && s.contentVersion && s.contentVersion !== CV ? " (현재 " + esc(CV) + ")" : "") + "</td></tr></table>" +
        (p.warnings.length ? '<details><summary>경고 ' + p.warnings.length + "건</summary><ul>" + p.warnings.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul></details>" : "") +
        '<div class="sb-row"><label class="sb-chk"><input type="radio" name="sbRmode" value="merge" checked> 지금 기록과 합치기</label>' +
        '<label class="sb-chk"><input type="radio" name="sbRmode" value="replace"> 지금 기록을 지우고 교체</label></div>' +
        (blocked ? '<div class="ng">이 브라우저에 저장된 읽을 수 없는 기록은 덮어씁니다.</div>' : "") +
        '<div class="sb-row"><button type="button" class="sb-btn primary" data-ract="apply">복원 적용</button> <button type="button" class="sb-btn" data-ract="cancel">취소</button></div>';
      const first = box.querySelector('[data-ract="apply"]') || box.querySelector("button");
      if (first) first.focus();
    }
    el.restore.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-ract]");
      if (!b) return;
      if (b.dataset.ract === "cancel") { closeRestore(); return; }
      if (!preview || !preview.ok) return;
      const modeEl = el.restore.querySelector('input[name="sbRmode"]:checked');
      const mode = modeEl ? modeEl.value : "merge";
      if (mode === "replace" && !root.confirm("지금 브라우저의 학습 기록을 지우고 백업으로 교체합니다. 계속할까요?")) return;
      state = SS.applyBackup(preview, state, { confirmed: true, mode, contentVersion: CV });
      const blocked = loadStatus === "corrupt" || loadStatus === "unknown-schema";
      const saved = persist(blocked ? { overwrite: true } : undefined);
      closeRestore();
      ui.learnCards = new Map();
      ui.listVersion++;
      ui.stateRev++;
      renderQuiz(true);
      if (saved) notice("복원했습니다.", false);
    });

    // ----- mobile: collapsible TOC, wide tables -----
    const tabs = doc.getElementById("tabs");
    const nav = doc.getElementById("nav");
    if (tabs && nav) {
      const t = doc.createElement("button");
      t.type = "button";
      t.className = "toc-toggle";
      t.id = "tocToggle";
      t.setAttribute("aria-controls", "nav");
      t.setAttribute("aria-expanded", "true");
      t.textContent = "목차 접기";
      tabs.insertBefore(t, tabs.firstChild);
      t.addEventListener("click", () => {
        const collapsed = doc.body.classList.toggle("toc-collapsed");
        t.setAttribute("aria-expanded", String(!collapsed));
        t.textContent = collapsed ? "목차 펴기" : "목차 접기";
      });
    }
    doc.querySelectorAll("#core table.jg").forEach((tbl) => {
      if (tbl.parentElement.closest("table")) return;
      let cols = 0;
      for (const row of tbl.rows) {
        let n = 0;
        for (const c of row.cells) n += c.colSpan || 1;
        cols = Math.max(cols, n);
      }
      // Every table gets a local scroll box so a long token never scrolls the whole pane;
      // only wide comparison tables (8+ columns) keep a desktop-like min-width on mobile.
      const wrap = doc.createElement("div");
      wrap.className = cols >= 8 ? "tbl-x wide" : "tbl-x";
      tbl.parentNode.insertBefore(wrap, tbl);
      wrap.appendChild(tbl);
    });

    root.renderQuiz = renderQuiz;
    renderQuiz(true);
  }

  return api;
});
