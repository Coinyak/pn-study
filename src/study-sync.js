/* study-sync.js — optional Supabase sync layered on StudyState (never replaces it).
 *
 * Merge: bookmarks union; attempts via StudyState.applyBackup(mode:"merge").
 * Push: pull → merge → save local → upsert. Never overwrite newer remote with older payload.
 */
(function (root) {
  "use strict";
  if (!root.StudyState) {
    console.warn("StudySync: StudyState missing; sync disabled");
    return;
  }

  const S = root.StudyState;
  let client = null;
  let sessionUser = null;
  let pushTimer = null;
  let lastKnownRemoteMs = 0;
  let questionBank = [];

  function cfg() { return root.PN_SUPABASE || null; }

  function isConfigured() {
    const c = cfg();
    return !!(c && c.url && c.anonKey && String(c.anonKey).indexOf("YOUR_") < 0);
  }

  function getStore() {
    return S.createStore({
      storage: typeof localStorage !== "undefined" ? localStorage : null,
      contentVersion: typeof root.PN_CONTENT_VERSION === "string" ? root.PN_CONTENT_VERSION : null,
    });
  }

  function stateUpdatedAt(state) {
    let max = 0;
    if (state && state.lastSession) {
      const t = Date.parse(state.lastSession.at) || Number(state.lastSession.at) || 0;
      if (t > max) max = t;
    }
    const attempts = (state && state.attemptsByQuestionId) || {};
    Object.keys(attempts).forEach(function (id) {
      (attempts[id] || []).forEach(function (a) {
        const t = Date.parse(a.at) || Number(a.at) || 0;
        if (t > max) max = t;
      });
    });
    if (state && typeof state.updatedAt === "number" && state.updatedAt > max) max = state.updatedAt;
    return max;
  }

  function stamp(state) {
    return Object.assign({}, state, { updatedAt: Math.max(stateUpdatedAt(state), Date.now()) });
  }

  function mergeRemoteIntoLocal(local, remotePayload, questions) {
    const text = S.exportBackup(remotePayload);
    const preview = S.parseBackup(text, questions || questionBank || []);
    if (!preview.ok) {
      return { state: local, warnings: preview.errors || ["remote-parse-failed"] };
    }
    const merged = S.applyBackup(preview, local, { confirmed: true, mode: "merge" });
    return { state: stamp(merged), warnings: preview.warnings || [] };
  }

  async function ensureClient() {
    if (!isConfigured()) return null;
    if (!root.supabase || !root.supabase.createClient) {
      console.warn("StudySync: supabase-js CDN not loaded");
      return null;
    }
    if (!client) {
      client = root.supabase.createClient(cfg().url, cfg().anonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
      });
      client.auth.onAuthStateChange(function (_ev, session) {
        sessionUser = session && session.user ? session.user : null;
        if (typeof root.PN_STUDY_ON_AUTH === "function") root.PN_STUDY_ON_AUTH(sessionUser);
      });
    }
    const { data } = await client.auth.getSession();
    sessionUser = data.session && data.session.user ? data.session.user : null;
    return client;
  }

  async function pullRemote() {
    const sb = await ensureClient();
    if (!sb || !sessionUser) return null;
    const { data, error } = await sb
      .from("study_progress")
      .select("payload, updated_at")
      .eq("user_id", sessionUser.id)
      .maybeSingle();
    if (error) throw error;
    if (!data) return null;
    const remoteMs = Date.parse(data.updated_at) || 0;
    const payloadAt = (data.payload && Number(data.payload.updatedAt)) || 0;
    const effective = Math.max(remoteMs, payloadAt);
    lastKnownRemoteMs = Math.max(lastKnownRemoteMs, effective);
    return { payload: data.payload, updatedAtMs: effective, rowUpdatedAt: data.updated_at };
  }

  async function upsertMerged(merged, basedOnRemoteMs) {
    const sb = await ensureClient();
    if (!sb || !sessionUser) return { ok: false, reason: "not-signed-in" };

    const again = await pullRemote();
    let toSave = merged;
    if (again && again.updatedAtMs > (basedOnRemoteMs || 0)) {
      const store = getStore();
      const local = store.load().state;
      const remixed = mergeRemoteIntoLocal(local, again.payload, questionBank);
      toSave = remixed.state;
      store.save(toSave);
      basedOnRemoteMs = again.updatedAtMs;
    }

    const localMs = stateUpdatedAt(toSave);
    if (again && again.updatedAtMs > localMs) {
      return { ok: false, reason: "remote-newer", remoteMs: again.updatedAtMs, localMs: localMs };
    }

    const payload = stamp(toSave);
    const { error } = await sb.from("study_progress").upsert({
      user_id: sessionUser.id,
      payload: payload,
      updated_at: new Date(payload.updatedAt).toISOString(),
    });
    if (error) throw error;
    lastKnownRemoteMs = Math.max(lastKnownRemoteMs, payload.updatedAt);
    getStore().save(payload);
    return { ok: true, state: payload };
  }

  async function syncNow(questions) {
    if (questions) questionBank = questions;
    const store = getStore();
    let local = store.load().state;
    if (!sessionUser) await ensureClient();
    if (!sessionUser) return { synced: false, reason: "login-required", state: local };

    const remote = await pullRemote();
    const basedOn = remote ? remote.updatedAtMs : 0;
    if (remote && remote.payload) {
      const { state, warnings } = mergeRemoteIntoLocal(local, remote.payload, questionBank);
      local = state;
      store.save(local);
      const pushed = await upsertMerged(local, basedOn);
      return { synced: !!pushed.ok, state: pushed.state || local, warnings: warnings, push: pushed };
    }
    const pushed = await upsertMerged(stamp(local), 0);
    return { synced: !!pushed.ok, state: pushed.state || local, push: pushed };
  }

  function scheduleSync(questions) {
    if (!isConfigured() || !sessionUser) return;
    if (questions) questionBank = questions;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(function () {
      syncNow(questionBank).catch(function (err) {
        console.warn("StudySync: background sync failed", err);
      });
    }, 700);
  }

  function persistLocal(mutator, questions) {
    const store = getStore();
    const cur = store.load().state;
    const next = stamp(mutator(cur));
    const saved = store.save(next);
    scheduleSync(questions || questionBank);
    return { state: next, save: saved };
  }

  async function signInWithEmail(email) {
    const sb = await ensureClient();
    if (!sb) throw new Error("Supabase 미설정 — content/supabase.json 후 빌드 필요");
    const c = cfg();
    const redirectTo = c.redirectTo || (root.location && root.location.href.split("#")[0]);
    const { error } = await sb.auth.signInWithOtp({
      email: email,
      options: { emailRedirectTo: redirectTo },
    });
    if (error) throw error;
  }

  async function signOut() {
    const sb = await ensureClient();
    if (!sb) return;
    await sb.auth.signOut();
    sessionUser = null;
  }

  async function init(questions) {
    if (questions) questionBank = questions;
    await ensureClient();
    if (sessionUser) {
      try { await syncNow(questionBank); }
      catch (err) { console.warn("StudySync: initial sync failed", err); }
    }
    return { configured: isConfigured(), user: sessionUser };
  }

  root.StudySync = {
    isConfigured: isConfigured,
    init: init,
    syncNow: syncNow,
    scheduleSync: scheduleSync,
    persistLocal: persistLocal,
    signInWithEmail: signInWithEmail,
    signOut: signOut,
    getUser: function () { return sessionUser; },
    getStore: getStore,
    stateUpdatedAt: stateUpdatedAt,
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
