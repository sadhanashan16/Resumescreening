/* Candidate browser: used by the screening results page and the shortlist page.
   Every score, skill and recommendation shown here comes from /api/candidates (the stored ML pipeline output). */
"use strict";
(function () {
  const root = document.getElementById("cb");
  const cfgEl = document.getElementById("page-config");
  if (!root || !cfgEl) return;
  const cfg = cfgEl.dataset;

  const ICONS = {
    star: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    ban: '<circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/>',
    eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    undo: '<path d="M9 7L4 12l5 5M4 12h11a5 5 0 010 10h-3"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
  };
  function icon(name, size) {
    const s = svg("svg", { width: size || 16, height: size || 16, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
      "stroke-width": "1.9", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", focusable: "false", class: "ico" });
    s.innerHTML = ICONS[name];          // static, trusted constants only (never user data)
    return s;
  }

  const STATUS_LABEL = { pending: "To review", shortlisted: "Shortlisted", rejected: "Rejected" };
  const COMPONENT_LABEL = { text_similarity: "Text similarity", skills: "Skill coverage", role_fit: "Role fit", experience: "Experience", education: "Education" };
  const mobile = window.matchMedia("(max-width: 800px)");
  let savedView = "table";
  try { savedView = localStorage.getItem("cb-view") || "table"; } catch (_) { /* storage unavailable */ }

  const state = {
    q: "", grade: "all", sort: "score", order: "desc", status: cfg.defaultStatus || "all", page: 1, perPage: 50,
    view: savedView, screeningId: cfg.screeningId || "", selected: new Set(), items: [], counts: { all: 0, pending: 0, shortlisted: 0, rejected: 0 },
    total: 0, pages: 1, req: 0, error: null, loaded: false,
  };

  const $ = (id) => document.getElementById(id);
  const listEl = $("cb-list"), tabsEl = $("cb-tabs"), bulkEl = $("cb-bulk"), pagerEl = $("cb-pager");

  // ------------------------------------------------------------------ data
  function filterParams() {
    const p = new URLSearchParams();
    if (state.screeningId) p.set("screening_id", state.screeningId);
    p.set("status", state.status);
    if (state.grade !== "all") p.set("grade", state.grade);
    if (state.q.trim()) p.set("q", state.q.trim());
    p.set("sort", state.sort); p.set("order", state.order);
    return p;
  }
  const filtersActive = () => state.grade !== "all" || !!state.q.trim();

  async function load() {
    const req = ++state.req;
    state.error = null;
    if (!state.loaded) renderSkeleton();
    const p = filterParams();
    p.set("page", state.page); p.set("per_page", state.perPage);
    try {
      const data = await api("GET", "/api/candidates?" + p.toString());
      if (req !== state.req) return;               // a newer request superseded this one
      if (data.page > data.pages && data.pages > 0) { state.page = data.pages; return load(); }
      Object.assign(state, { items: data.items, counts: data.counts, total: data.total, pages: data.pages, loaded: true });
      const ids = new Set(state.items.map((c) => c.id));
      state.selected.forEach((id) => { if (!ids.has(id)) state.selected.delete(id); });
    } catch (err) {
      if (req !== state.req) return;
      state.error = err.message;
    }
    render();
  }

  async function setStatus(ids, status, quiet) {
    try {
      let msg;
      if (ids.length === 1) { await api("PATCH", "/api/candidates/" + ids[0], { status }); msg = `Marked ${STATUS_LABEL[status].toLowerCase()}`; }
      else { const r = await api("POST", "/api/candidates/bulk", { ids, status }); msg = `${r.updated} candidates marked ${STATUS_LABEL[status].toLowerCase()}`; }
      if (!quiet) toast(msg, "success");
      state.selected.clear();
      await load();
      if (drawerId) openDrawer(drawerId, true);
    } catch (err) { toast(err.message, "error"); }
  }

  // ---------------------------------------------------------------- render
  function renderSkeleton() {
    listEl.replaceChildren(...Array.from({ length: 5 }, () => h("div", { class: "skeleton-row" })));
  }

  function render() {
    renderTabs();
    renderBulk();
    renderList();
    renderPager();
    const exp = $("export-link");
    if (exp) { const p = filterParams(); exp.href = "/api/candidates/export.csv?" + p.toString(); }
    const quick = $("shortlist-recommended");
    if (quick) quick.disabled = false;
  }

  function renderTabs() {
    const defs = [["all", "All"], ["pending", "To review"], ["shortlisted", "Shortlisted"], ["rejected", "Rejected"]];
    tabsEl.replaceChildren(...defs.map(([key, label]) => h("button", {
      type: "button", class: "tab" + (state.status === key ? " active" : ""), "aria-pressed": String(state.status === key),
      onclick: () => { state.status = key; state.page = 1; state.selected.clear(); load(); },
    }, label, h("span", { class: "tab-count", text: String(state.counts[key] ?? 0) }))));
  }

  function renderBulk() {
    const n = state.selected.size;
    bulkEl.hidden = n === 0;
    $("cb-bulk-count").textContent = `${n} selected`;
  }

  function renderList() {
    if (state.error) {
      listEl.replaceChildren(h("div", { class: "alert error", role: "alert" }, "Could not load candidates: " + state.error + " ",
        h("button", { type: "button", class: "btn btn-sm", onclick: () => load() }, "Retry")));
      return;
    }
    if (!state.items.length) { listEl.replaceChildren(emptyState()); return; }
    const view = mobile.matches ? "cards" : state.view;
    document.querySelectorAll("#cb-view button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === view)));
    listEl.replaceChildren(view === "table" ? renderTable(state.items) : renderCards(state.items));
  }

  function emptyState() {
    if (filtersActive()) {
      return h("div", { class: "empty" }, h("h3", { text: "No candidates match your filters" }),
        h("p", { class: "muted", text: "Try a different search term or clear the filters." }),
        h("button", { type: "button", class: "btn", onclick: clearFilters }, "Clear filters"));
    }
    if (cfg.shortlistPage && state.status === "shortlisted" && !state.counts.all) {
      return h("div", { class: "empty" }, h("h3", { text: "No shortlisted candidates yet" }),
        h("p", { class: "muted", text: "Open a screening and shortlist the candidates you want to move forward with." }),
        h("a", { class: "btn btn-primary", href: "/screenings" }, "Go to screenings"));
    }
    const msg = { shortlisted: "No one is shortlisted here yet. Use the star button on a candidate to shortlist them.",
      rejected: "No rejected candidates.", pending: "Every candidate here has been reviewed.", all: "No candidates found." }[state.status];
    return h("div", { class: "empty" }, h("h3", { text: "Nothing to show" }), h("p", { class: "muted", text: msg }));
  }

  function clearFilters() {
    state.q = ""; state.grade = "all"; state.page = 1;
    $("cb-q").value = ""; $("cb-grade").value = "all";
    load();
  }

  // table ------------------------------------------------------------------
  function scoreCell(c) {
    const fill = h("div", { class: "fill " + gradeClass(c.grade) });
    requestAnimationFrame(() => { fill.style.width = Math.max(2, Math.min(100, c.score)) + "%"; });
    return h("div", { class: "score-cell", title: c.grade },
      h("b", { text: c.score.toFixed(1) }), h("div", { class: "track" }, fill),
      h("span", { class: "grade " + gradeClass(c.grade), text: c.grade.replace(" match", "") }));
  }

  function skillChips(c, max) {
    const list = c.matched_skills.length ? c.matched_skills : c.skills;
    const shown = list.slice(0, max);
    return h("div", { class: "chips tight" }, shown.map((s) => chip(s, "good")),
      list.length > max ? chip("+" + (list.length - max), "") : null);
  }

  function statusBadge(c) { return h("span", { class: "status-badge s-" + c.status, text: STATUS_LABEL[c.status] }); }

  function actionButtons(c, withText) {
    const short = c.status === "shortlisted", rej = c.status === "rejected";
    return h("div", { class: "row-actions" },
      h("button", { type: "button", class: "icon-btn" + (short ? " on-good" : ""), "aria-pressed": String(short),
        title: short ? "Remove from shortlist" : "Shortlist", "aria-label": (short ? "Remove from shortlist: " : "Shortlist: ") + c.name,
        onclick: (e) => { e.stopPropagation(); setStatus([c.id], short ? "pending" : "shortlisted"); } }, icon("star", 18), withText ? (short ? " Shortlisted" : " Shortlist") : null),
      h("button", { type: "button", class: "icon-btn" + (rej ? " on-bad" : ""), "aria-pressed": String(rej),
        title: rej ? "Undo reject" : "Reject", "aria-label": (rej ? "Undo reject: " : "Reject: ") + c.name,
        onclick: (e) => { e.stopPropagation(); setStatus([c.id], rej ? "pending" : "rejected"); } }, icon(rej ? "undo" : "ban", 18), withText ? (rej ? " Rejected" : " Reject") : null),
      h("button", { type: "button", class: "icon-btn", title: "View details", "aria-label": "View details: " + c.name,
        onclick: (e) => { e.stopPropagation(); openDrawer(c.id); } }, icon("eye", 18), withText ? " Details" : null));
  }

  function selectBox(c) {
    return h("input", { type: "checkbox", class: "sel", "aria-label": "Select " + c.name, checked: state.selected.has(c.id) || null,
      onclick: (e) => e.stopPropagation(),
      onchange: (e) => { e.target.checked ? state.selected.add(c.id) : state.selected.delete(c.id); renderBulk(); syncSelectAll(); } });
  }

  let selectAllEl = null;
  function syncSelectAll() { if (selectAllEl) selectAllEl.checked = state.items.length > 0 && state.items.every((c) => state.selected.has(c.id)); }

  function renderTable(items) {
    selectAllEl = h("input", { type: "checkbox", "aria-label": "Select all candidates on this page",
      onchange: (e) => { state.items.forEach((c) => e.target.checked ? state.selected.add(c.id) : state.selected.delete(c.id)); render(); } });
    const head = h("tr", {}, h("th", { class: "sel-col" }, selectAllEl), h("th", { text: "Rank" }), h("th", { text: "Candidate" }),
      h("th", { text: "Match score" }), h("th", { text: "Experience" }), h("th", { text: "Education" }), h("th", { text: "Key skills" }),
      h("th", { text: "Status" }), h("th", { class: "num", text: "Actions" }));
    const rows = items.map((c) => h("tr", { class: "clickable s-" + c.status, onclick: () => openDrawer(c.id) },
      h("td", { class: "sel-col" }, selectBox(c)),
      h("td", { class: "rank-cell" }, h("b", { text: "#" + c.rank }), c.recommended ? h("span", { class: "ai-badge", title: "Recommended by the AI ranking", text: "AI pick" }) : null),
      h("td", {}, h("button", { type: "button", class: "link-btn", onclick: (e) => { e.stopPropagation(); openDrawer(c.id); } }, c.name),
        h("small", { class: "muted block", text: c.email || c.filename }),
        state.screeningId ? null : h("small", { class: "muted block", text: c.screening_title })),
      h("td", { class: "score-td" }, scoreCell(c)),
      h("td", { text: c.experience_years + " yrs" }),
      h("td", { text: (c.education && c.education.label) || "–" }),
      h("td", {}, skillChips(c, 2)),
      h("td", {}, statusBadge(c)),
      h("td", { class: "num" }, actionButtons(c, false))));
    const t = h("table", { class: "data-table cand-table" }, h("thead", {}, head), h("tbody", {}, rows));
    syncSelectAll();
    return h("div", { class: "table-wrap card flush" }, t);
  }

  // cards ------------------------------------------------------------------
  function ring(score, grade) {
    const r = 26, circ = 2 * Math.PI * r;
    const arc = svg("circle", { cx: 32, cy: 32, r, fill: "none", "stroke-width": 6, "stroke-linecap": "round", class: "ring-arc " + gradeClass(grade),
      "stroke-dasharray": `${(Math.max(0, Math.min(100, score)) / 100) * circ} ${circ}`, transform: "rotate(-90 32 32)" });
    return h("div", { class: "ring", role: "img", "aria-label": `Match score ${score.toFixed(1)} out of 100` },
      svg("svg", { viewBox: "0 0 64 64", width: 64, height: 64 }, svg("circle", { cx: 32, cy: 32, r, fill: "none", "stroke-width": 6, class: "ring-bg" }), arc),
      h("b", { text: Math.round(score) }));
  }

  function renderCards(items) {
    return h("div", { class: "cand-cards" }, items.map((c) => h("article", { class: "cand-card s-" + c.status },
      h("div", { class: "cand-card-top" }, selectBox(c), h("span", { class: "rank-pill", text: "#" + c.rank }),
        c.recommended ? h("span", { class: "ai-badge", text: "AI pick" }) : null, h("span", { class: "grow" }), statusBadge(c)),
      h("div", { class: "cand-card-main" },
        h("div", { class: "grow" },
          h("button", { type: "button", class: "link-btn big", onclick: () => openDrawer(c.id) }, c.name),
          h("small", { class: "muted block", text: c.email || c.filename }),
          h("div", { class: "meta" }, h("span", { text: c.experience_years + " yrs" }), h("span", { text: (c.education && c.education.label) || "–" }),
            c.predicted_role ? h("span", { text: c.predicted_role.title }) : null)),
        h("div", { class: "ring-wrap" }, ring(c.score, c.grade), h("span", { class: "grade " + gradeClass(c.grade), text: c.grade.replace(" match", "") }))),
      skillChips(c, 6),
      c.missing_skills.length ? h("div", { class: "chips tight miss" }, c.missing_skills.slice(0, 3).map((s) => chip("missing: " + s, "bad"))) : null,
      actionButtons(c, true))));
  }

  // pager ------------------------------------------------------------------
  function renderPager() {
    pagerEl.hidden = state.pages <= 1;
    if (state.pages <= 1) return;
    pagerEl.replaceChildren(
      h("button", { type: "button", class: "btn btn-sm", disabled: state.page <= 1 || null, onclick: () => { state.page--; load(); } }, "← Previous"),
      h("span", { class: "muted small", text: `Page ${state.page} of ${state.pages} · ${state.total} candidates` }),
      h("button", { type: "button", class: "btn btn-sm", disabled: state.page >= state.pages || null, onclick: () => { state.page++; load(); } }, "Next →"));
  }

  // ---------------------------------------------------------------- drawer
  let drawer = null, drawerId = null, lastFocus = null;

  function closeDrawer() {
    if (!drawer) return;
    drawer.remove(); drawer = null; drawerId = null;
    document.body.classList.remove("no-scroll");
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  async function openDrawer(id, refreshOnly) {
    let c = state.items.find((x) => x.id === id);
    if (!c) { try { c = await api("GET", "/api/candidates/" + id); } catch (err) { return toast(err.message, "error"); } }
    if (!refreshOnly) lastFocus = document.activeElement;
    const keepNotes = refreshOnly && drawer && drawer.querySelector("textarea") ? drawer.querySelector("textarea").value : null;
    if (drawer) drawer.remove();
    drawerId = id;
    drawer = buildDrawer(c, keepNotes);
    document.body.append(drawer);
    document.body.classList.add("no-scroll");
    if (!refreshOnly) drawer.querySelector(".drawer-close").focus();
  }

  function buildDrawer(c, keepNotes) {
    const comps = Object.keys(COMPONENT_LABEL).filter((k) => c.components && c.components[k] !== null && c.components[k] !== undefined);
    const notes = h("textarea", { class: "input", id: "drawer-notes", rows: 4, maxlength: 5000, placeholder: "Interview impressions, follow-ups, reasons for your decision…" });
    notes.value = keepNotes !== null ? keepNotes : c.notes;
    const saveBtn = h("button", { type: "button", class: "btn btn-sm", onclick: async () => {
      saveBtn.disabled = true;
      try { const u = await api("PATCH", "/api/candidates/" + c.id, { notes: notes.value }); c.notes = u.notes; toast("Notes saved", "success"); }
      catch (err) { toast(err.message, "error"); }
      saveBtn.disabled = false;
    } }, "Save notes");

    const panel = h("div", { class: "drawer-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "drawer-title" },
      h("div", { class: "drawer-head" },
        h("span", { class: "avatar lg", "aria-hidden": "true", text: initials(c.name) }),
        h("div", { class: "grow" }, h("h2", { id: "drawer-title", text: c.name }),
          h("div", { class: "muted small", text: [c.email, c.phone].filter(Boolean).join(" · ") || "No contact details found" })),
        h("button", { type: "button", class: "icon-btn drawer-close", "aria-label": "Close details", onclick: closeDrawer }, icon("x", 22))),
      h("div", { class: "drawer-body" },
        h("div", { class: "score-hero" }, ring(c.score, c.grade),
          h("div", {}, h("span", { class: "grade " + gradeClass(c.grade), text: c.grade }),
            h("div", { class: "muted small", text: `AI rank #${c.rank}` + (c.recommended ? " · recommended by the AI" : "") }),
            h("div", { class: "muted small", text: c.screening_title || "" }))),
        h("div", { class: "decision" }, ...[["shortlisted", "star", "Shortlist"], ["rejected", "ban", "Reject"], ["pending", "undo", "Reset"]].map(([st, ic, label]) =>
          h("button", { type: "button", class: "btn btn-sm" + (c.status === st ? (st === "shortlisted" ? " btn-primary" : " btn-selected") : ""),
            "aria-pressed": String(c.status === st), disabled: c.status === st || null, onclick: () => setStatus([c.id], st) }, icon(ic, 16), " " + label))),
        h("h3", { text: "Why this score" }),
        h("div", { class: "bars" }, comps.map((k) => bar(`${COMPONENT_LABEL[k]} (${Math.round((c.weights_used[k] || 0) * 100)}%)`, c.components[k]))),
        h("div", { class: "kv" },
          h("div", {}, h("b", { text: "Experience" }), c.experience_years + " years"),
          h("div", {}, h("b", { text: "Education" }), ((c.education && c.education.label) || "–") + (c.education && c.education.detail ? " · " + c.education.detail : "")),
          h("div", {}, h("b", { text: "Predicted role" }), c.predicted_role ? `${c.predicted_role.title} (${Math.round(c.predicted_role.confidence * 100)}%)` : "–"),
          h("div", {}, h("b", { text: "Naive Bayes / SVM" }), `${c.naive_bayes_role || "–"} / ${c.svm_role || "–"}`)),
        h("h3", { text: "Skills" }),
        ...skillBlock(c.matched_skills, c.related_skills, c.missing_skills),
        c.extra_skills.length ? [h("div", { class: "label-row", text: "Other technical skills" }), chips(c.extra_skills, "tech")] : null,
        h("h3", { text: "Notes" }), notes, h("div", { class: "notes-actions" }, saveBtn),
        h("div", { class: "drawer-foot" },
          h("a", { class: "btn btn-sm btn-ghost", href: "/screenings/" + c.screening_id }, "Open screening"),
          h("span", { class: "muted small grow", text: "File: " + c.filename }),
          h("button", { type: "button", class: "btn btn-sm btn-danger-ghost", onclick: async () => {
            if (!window.confirm(`Delete ${c.name} from your records? This cannot be undone.`)) return;
            try { await api("DELETE", "/api/candidates/" + c.id); toast("Candidate deleted", "success"); closeDrawer(); load(); }
            catch (err) { toast(err.message, "error"); }
          } }, icon("trash", 16), " Delete"))));
    const wrap = h("div", { class: "drawer" }, h("div", { class: "drawer-backdrop", onclick: closeDrawer }), panel);
    return wrap;
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer) closeDrawer();
    if (e.key === "Tab" && drawer) {                // keep keyboard focus inside the dialog
      const f = drawer.querySelectorAll("button:not([disabled]), a[href], textarea, input, select");
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  // -------------------------------------------------------------- controls
  $("cb-q").addEventListener("input", debounce((e) => { state.q = e.target.value; state.page = 1; load(); }, 250));
  $("cb-grade").addEventListener("change", (e) => { state.grade = e.target.value; state.page = 1; load(); });
  $("cb-sort").addEventListener("change", (e) => { [state.sort, state.order] = e.target.value.split(":"); state.page = 1; load(); });
  document.querySelectorAll("#cb-view button").forEach((b) => b.addEventListener("click", () => {
    state.view = b.dataset.view;
    try { localStorage.setItem("cb-view", state.view); } catch (_) { /* ignore */ }
    renderList();
  }));
  mobile.addEventListener("change", () => { if (state.loaded) renderList(); });
  $("cb-clear-sel").addEventListener("click", () => { state.selected.clear(); render(); });
  bulkEl.querySelectorAll("[data-bulk]").forEach((b) => b.addEventListener("click", () => setStatus([...state.selected], b.dataset.bulk)));

  const runSelect = $("cb-run");
  if (runSelect) runSelect.addEventListener("change", (e) => { state.screeningId = e.target.value; state.page = 1; load(); });

  const quick = $("shortlist-recommended");
  if (quick) quick.addEventListener("click", async () => {
    quick.disabled = true;
    try {
      const r = await api("POST", "/api/candidates/bulk", { screening_id: Number(cfg.screeningId), scope: "recommended", status: "shortlisted" });
      toast(`Shortlisted the AI's top ${r.updated} candidate${r.updated === 1 ? "" : "s"}`, "success");
      await load();
    } catch (err) { toast(err.message, "error"); }
    quick.disabled = false;
  });

  document.querySelectorAll("#cb-view button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
  load();
})();
