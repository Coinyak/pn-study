/* study-ui.js — learn quiz pane (marks, favorites, filters, search, backup/restore)
 * on top of StudyState. Card click → core jump. Compact one-line toolbar.
 *
 * Inlined after the split shell's script. Replaces the shell's read-only renderQuiz().
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

  const FILTERS = [["all", "전체"], ["unseen", "미표시"], ["marked", "표시 있음"], ["bookmarked", "즐겨찾기"]];
  const REVIEW_FILTERS = ["marked", "bookmarked"];

  const isKo = (q) => q.language === undefined || q.language === null || q.language === "ko";

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

  function isDisplayable(q) {
    return !!q && q.reviewStatus !== "excluded" && isKo(q);
  }

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

  function buildList(bank, state, opts, SS) {
    const o = opts || {};
    const filter = SS.normalizeFilter(o.filter || "all");
    let pool = REVIEW_FILTERS.indexOf(filter) >= 0 ? bank.filter(isDisplayable) : basePool(bank, !!o.includePending);
    if (normSearch(o.search)) pool = pool.filter((q) => matchesSearch(q, o.search));
    else if (o.scope !== "all" && o.topic) pool = pool.filter((q) => q.topic === o.topic);
    if (o.sourceLabel) pool = pool.filter((q) => coreSourceLabel(q) === o.sourceLabel);
    return SS.selectReviewQuestions(pool, state, filter);
  }

  function filterUsesState(filter) {
    return !!filter && filter !== "all";
  }

  function focusAfterRebuild(oldIds, mutatedId, newIds) {
    if (newIds.indexOf(mutatedId) >= 0) return mutatedId;
    const at = oldIds.indexOf(mutatedId);
    if (at < 0) return newIds.length ? newIds[0] : null;
    for (let i = at + 1; i < oldIds.length; i++) if (newIds.indexOf(oldIds[i]) >= 0) return oldIds[i];
    for (let i = at - 1; i >= 0; i--) if (newIds.indexOf(oldIds[i]) >= 0) return oldIds[i];
    return newIds.length ? newIds[0] : null;
  }

  const api = {
    FILTERS, filterUsesState, focusAfterRebuild, isDisplayable, basePool, matchesSearch, buildList,
    coreSourceLabel, sourceToneClass, mount,
  };

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

    const store = SS.createStore({ contentVersion: CV });
    const loaded = store.load();
    let state = loaded.state;
    const loadStatus = loaded.status;

    const ui = {
      filter: "all", scope: "all", search: "", includePending: false, sourceLabel: "",
      listVersion: 0, stateRev: 0, lastKey: null, lastSaveReason: null,
    };

    const bar = doc.createElement("div");
    bar.className = "study-bar";
    bar.id = "studyBar";
    bar.innerHTML =
      '<div class="sb-row sb-one">' +
        '<select id="sbFilter" aria-label="보기">' + FILTERS.map((f) => '<option value="' + f[0] + '">' + f[1] + "</option>").join("") + "</select>" +
        '<select id="sbScope" aria-label="범위"><option value="all">전체</option><option value="topic">소단원</option></select>' +
        '<select id="sbSource" aria-label="출처"><option value="">출처 전체</option></select>' +
        '<input type="search" id="sbSearch" class="sb-search" placeholder="검색" aria-label="문항 검색" enterkeyhint="search">' +
        '<label class="sb-chk" title="검토 대기 문항 포함"><input type="checkbox" id="sbPending"> 대기</label>' +
        '<button type="button" class="sb-btn" id="sbExport" title="학습 기록 파일로 저장">저장</button>' +
        '<button type="button" class="sb-btn" id="sbImport" title="학습 기록 파일 불러오기">불러오기</button>' +
        '<input type="file" id="sbFile" accept=".json,application/json" hidden>' +
        '<span class="sb-sum" id="sbSum"></span>' +
      "</div>" +
      '<div class="sb-notice" id="sbNotice" role="status" aria-live="polite" hidden></div>';
    head.insertAdjacentElement("afterend", bar);
    const $ = (id) => doc.getElementById(id);
    const el = {
      filter: $("sbFilter"), scope: $("sbScope"), source: $("sbSource"), search: $("sbSearch"), pending: $("sbPending"),
      exp: $("sbExport"), imp: $("sbImport"), file: $("sbFile"), sum: $("sbSum"),
      notice: $("sbNotice"), title: $("quizHeadTitle") || head,
    };

    let noticeTimer = null;
    function notice(msg, sticky) {
      clearTimeout(noticeTimer);
      el.notice.textContent = msg;
      el.notice.hidden = !msg;
      if (msg && !sticky) noticeTimer = setTimeout(() => { el.notice.hidden = true; }, 8000);
    }
    const SAVE_MSG = {
      "no-storage": "브라우저 저장소를 쓸 수 없어 이 창에서만 기록됩니다.",
      "storage-error": "기록 저장에 실패했습니다. 새로고침하면 사라질 수 있습니다.",
      "blocked-corrupt": "저장된 기록을 읽을 수 없어 덮어쓰지 않았습니다.",
      "blocked-unknown-schema": "다른 버전의 기록이 있어 덮어쓰지 않았습니다.",
    };
    function persist(opts) {
      const r = store.save(state, opts);
      if (r.ok) { ui.lastSaveReason = null; return true; }
      if (r.reason !== ui.lastSaveReason) notice(SAVE_MSG[r.reason] || "기록을 저장하지 못했습니다.", false);
      ui.lastSaveReason = r.reason;
      return false;
    }
    if (loadStatus === "unavailable") notice(SAVE_MSG["no-storage"], false);
    else if (loadStatus === "corrupt") notice("저장된 기록이 손상돼 읽지 못했습니다. 「불러오기」로 교체할 수 있습니다.", true);
    else if (loadStatus === "unknown-schema") notice("다른 버전의 기록이 있어 읽지 못했습니다.", true);

    function listKey() {
      return JSON.stringify([
        ui.filter, ui.scope, ui.search, ui.includePending, ui.sourceLabel,
        ui.scope === "all" || ui.search ? "" : topicNow(), ui.listVersion,
        filterUsesState(ui.filter) ? ui.stateRev : 0,
      ]);
    }
    function currentItems() {
      return buildList(BANK, state, {
        filter: ui.filter, search: ui.search, topic: topicNow(), scope: ui.scope,
        includePending: ui.includePending, sourceLabel: ui.sourceLabel || "",
      }, SS);
    }
    function poolForSources() {
      return buildList(BANK, state, {
        filter: ui.filter, search: ui.search, topic: topicNow(), scope: ui.scope,
        includePending: ui.includePending, sourceLabel: "",
      }, SS);
    }
    function renderSourceOptions() {
      const pool = poolForSources();
      const counts = new Map();
      pool.forEach((q) => {
        const lab = coreSourceLabel(q);
        counts.set(lab, (counts.get(lab) || 0) + 1);
      });
      if (ui.sourceLabel && !counts.has(ui.sourceLabel)) ui.sourceLabel = "";
      const labels = Array.from(counts.keys()).sort((a, b) => a.localeCompare(b, "ko"));
      const cur = ui.sourceLabel || "";
      el.source.innerHTML =
        '<option value="">출처 전체 (' + pool.length + ")</option>" +
        labels.map((lab) =>
          '<option value="' + esc(lab) + '"' + (lab === cur ? " selected" : "") + ">" +
          esc(lab) + " (" + counts.get(lab) + ")</option>"
        ).join("");
      el.source.value = cur;
    }

    function learnCardHtml(q, idx) {
      const linked = coreLinked(q);
      const bm = state.bookmarks.indexOf(q.id) >= 0;
      const pending = q.reviewStatus === "pending" ? ' · <span class="q-pending">검토 대기</span>' : "";
      const marks = SS.getMarks(state, q.id);
      const markBoxes = marks.map((on, i) =>
        '<label class="q-mark" title="풀이 표시 ' + (i + 1) + '"><input type="checkbox" data-act="mark" data-mi="' + i + '"' +
          (on ? " checked" : "") + '><span class="sr-only">풀이 표시 ' + (i + 1) + "</span></label>"
      ).join("");
      const choices = '<ol class="q-ol">' + (q.choices || []).map((c) => "<li>" + esc(c) + "</li>").join("") + "</ol>";
      const ans = (q.choices && q.choices[q.answer]) || "";
      const explain =
        '<details class="q-details"><summary>정답·해설 보기</summary>' +
        "<p><b>정답:</b> " + (q.answer + 1) + ". " + esc(ans) + "</p>" +
        (q.explain ? "<p>" + esc(q.explain) + "</p>" : "") +
        "</details>";
      return '<article class="qcard sq' + (linked ? " q-linked" : "") + '" data-qid="' + esc(q.id) + '" data-idx="' + idx + '"' +
        (linked ? ' title="클릭하면 핵심본 위치로 이동합니다"' : "") + ">" +
        '<div class="q-top">' +
          '<div class="src"><span class="src-meta ' + sourceToneClass(coreSourceLabel(q)) + '">' + esc(coreSourceLabel(q)) + "</span>" +
          " · " + esc(q.id) + (linked ? "" : " · 핵심 연결 없음") + pending + "</div>" +
          '<span class="q-tools">' +
            '<span class="q-marks" role="group" aria-label="풀이 횟수 표시">' + markBoxes + "</span>" +
            '<button type="button" class="q-bm" data-act="bookmark" aria-pressed="' + bm + '" aria-label="즐겨찾기" title="즐겨찾기">' + (bm ? "★" : "☆") + "</button>" +
          "</span>" +
        "</div>" +
        '<div class="stem" id="stem-' + idx + '">' + esc(q.stem) + "</div>" +
        choices + explain + "</article>";
    }

    function headTitle(items) {
      const f = FILTERS.find((x) => x[0] === ui.filter)[1];
      const where = ui.search ? "검색「" + ui.search + "」" : ui.scope === "all" ? "전체 단원" : topicLabel(topicNow());
      const src = ui.sourceLabel ? " · " + ui.sourceLabel : "";
      return "관련 문제 · " + where + src + (ui.filter === "all" ? "" : " · " + f) + " (" + items.length + ")";
    }

    function emptyText() {
      if (ui.search) return "검색 결과가 없습니다.";
      if (ui.filter !== "all") return "조건에 맞는 문항이 없습니다.";
      return "이 소단원에 검증 완료 문항이 아직 없습니다. 범위를 「전체」로 바꿔 보세요.";
    }

    function updateSummary() {
      const s = SS.summarizeProgress(basePool(BANK, ui.includePending), state);
      el.sum.textContent = "표시 " + s.marked + "/" + s.total + " · ★" + s.bookmarked;
    }

    function renderQuiz(force) {
      renderSourceOptions();
      const key = listKey();
      const items = currentItems();
      el.title.textContent = headTitle(items);
      updateSummary();
      if (!force && key === ui.lastKey) return;
      ui.lastKey = key;
      list.dataset.topic = topicNow() || "";
      list.innerHTML = items.length ? items.map(learnCardHtml).join("") : '<div class="empty">' + emptyText() + "</div>";
    }

    function rerenderCard(card, focusSel) {
      const q = BY_ID.get(card.dataset.qid);
      const idx = Number(card.dataset.idx);
      card.insertAdjacentHTML("afterend", learnCardHtml(q, idx));
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

    function afterStateChange(card, focusSel) {
      ui.stateRev++;
      if (!filterUsesState(ui.filter)) {
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
        const node = find(id);
        const f = focusSel && node && node.querySelector(focusSel);
        if (f) f.focus({ preventScroll: true });
      } else {
        notice("현재 보기에서 제외했습니다.", false);
        const t = target && find(target);
        const f = t ? (t.querySelector('input[data-act="mark"]') || t.querySelector("button")) : null;
        if (f) f.focus({ preventScroll: true });
        else {
          const e = t || list.querySelector(".empty") || list;
          e.tabIndex = -1;
          e.focus({ preventScroll: true });
        }
      }
    }

    function showCore(card) {
      const q = BY_ID.get(card.dataset.qid);
      if (!q || !coreLinked(q) || typeof highlightFromQuestion !== "function") return;
      list.querySelectorAll(".qcard.hl").forEach((c) => c.classList.toggle("hl", c === card));
      card.classList.add("hl");
      if (typeof activeTopic !== "undefined" && (ui.scope === "all" || ui.search)) activeTopic = q.topic; // eslint-disable-line no-global-assign
      highlightFromQuestion(q);
      if (!doc.querySelector(".core-hl, .core-hl-exact")) notice("핵심본에서 이 문항의 위치를 찾지 못했습니다.", false);
    }

    list.addEventListener("change", (e) => {
      const card = e.target.closest(".qcard.sq");
      if (!card || e.target.dataset.act !== "mark") return;
      const mi = Number(e.target.dataset.mi);
      if (!Number.isInteger(mi)) return;
      state = SS.setMark(state, card.dataset.qid, mi, e.target.checked);
      persist();
      afterStateChange(card, 'input[data-act="mark"][data-mi="' + mi + '"]');
    });
    list.addEventListener("click", (e) => {
      const bm = e.target.closest('button[data-act="bookmark"]');
      if (bm) {
        const card = bm.closest(".qcard.sq");
        if (!card) return;
        e.preventDefault();
        e.stopPropagation();
        state = SS.toggleBookmark(state, card.dataset.qid);
        persist();
        afterStateChange(card, '[data-act="bookmark"]');
        return;
      }
      // Interactive controls: do not jump to core.
      if (e.target.closest("input, button, label, summary, details, a, select, textarea")) return;
      const card = e.target.closest(".qcard.sq");
      if (card) showCore(card);
    });

    function readControls() {
      ui.filter = el.filter.value;
      ui.scope = el.scope.value;
      ui.search = el.search.value.trim();
      ui.includePending = el.pending.checked;
      ui.sourceLabel = el.source.value || "";
    }
    [el.filter, el.scope, el.pending, el.source].forEach((c) => c.addEventListener("change", () => {
      readControls();
      ui.listVersion++;
      renderQuiz(true);
    }));
    let searchTimer = null;
    el.search.addEventListener("input", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { readControls(); renderQuiz(); }, 200);
    });

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
      notice("저장했습니다.", false);
    });
    el.imp.addEventListener("click", () => { el.file.value = ""; el.file.click(); });
    el.file.addEventListener("change", () => {
      const f = el.file.files && el.file.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        const p = SS.parseBackup(String(reader.result || ""), BANK);
        if (!p.ok) {
          notice("불러올 수 없는 파일입니다" + (p.errors && p.errors[0] ? ": " + p.errors[0] : "."), false);
          return;
        }
        const s = p.summary || {};
        const msg = "기록을 합칠까요?\n표시 " + (s.markedQuestions || 0) + " · ★" + (s.bookmarks || 0) +
          "\n확인=합치기 / 취소=덮어쓰기";
        const merge = root.confirm(msg);
        if (!merge && !root.confirm("지금 기록을 지우고 파일로 덮어쓸까요?")) return;
        const mode = merge ? "merge" : "replace";
        state = SS.applyBackup(p, state, { confirmed: true, mode, contentVersion: CV });
        const blocked = loadStatus === "corrupt" || loadStatus === "unknown-schema";
        const saved = persist(blocked || mode === "replace" ? { overwrite: true } : undefined);
        ui.listVersion++;
        ui.stateRev++;
        renderQuiz(true);
        if (saved) notice(mode === "merge" ? "합쳤습니다." : "덮어썼습니다.", false);
      };
      reader.onerror = () => notice("파일을 읽지 못했습니다.", false);
      reader.readAsText(f);
    });

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
