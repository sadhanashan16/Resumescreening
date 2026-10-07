/* Shared helpers. All dynamic content is built with textContent / DOM nodes (never innerHTML). */
"use strict";

function h(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return node;
}

function svg(tag, attrs, ...children) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs || {})) if (v !== null && v !== undefined) node.setAttribute(k, v);
  for (const c of children.flat()) if (c) node.append(c);
  return node;
}

function chip(text, cls) { return h("span", { class: "chip " + (cls || "") }, text); }
function chips(items, cls) { return h("div", { class: "chips" }, items.map((t) => chip(t, cls))); }

function bar(label, value) {
  const fill = h("div", { class: "fill" });
  requestAnimationFrame(() => { fill.style.width = Math.max(0, Math.min(100, value)) + "%"; });
  return h("div", { class: "bar" }, h("span", { text: label }), h("div", { class: "track" }, fill),
    h("span", { class: "val", text: Math.round(value) + "%" }));
}

function gradeClass(grade) {
  return { "Strong match": "g-strong", "Good match": "g-good", "Partial match": "g-partial" }[grade] || "g-weak";
}

function formatBytes(n) { return n < 1024 * 1024 ? Math.max(1, Math.round(n / 1024)) + " KB" : (n / 1048576).toFixed(1) + " MB"; }

function fmtDate(iso, withTime) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) +
    (withTime ? " · " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) : "");
}

function initials(name) {
  const parts = String(name || "?").trim().split(/\s+/).filter(Boolean);
  return (parts.slice(0, 2).map((p) => p[0]).join("") || "?").toUpperCase();
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

/* ---- network: every state-changing request carries the CSRF token ---- */
function csrfToken() {
  const m = document.querySelector('meta[name="csrf-token"]');
  return m ? m.content : "";
}

async function readJson(resp) {
  let data = null;
  try { data = await resp.json(); } catch (_) { /* non-JSON body */ }
  if (resp.status === 401) {                       // session expired: go back to the login page
    const here = location.pathname + location.search;
    location.assign("/login?next=" + encodeURIComponent(here));
    throw new Error("Your session has expired. Please log in again.");
  }
  if (!resp.ok) throw new Error((data && data.error) || `Request failed (${resp.status}).`);
  return data;
}

async function postForm(url, formData) {
  return readJson(await fetch(url, { method: "POST", body: formData, headers: { "X-CSRFToken": csrfToken() },
                                     credentials: "same-origin" }));
}

async function api(method, url, body) {
  const opts = { method, credentials: "same-origin", headers: { "X-CSRFToken": csrfToken() } };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  return readJson(await fetch(url, opts));
}

function showError(box, message) { box.textContent = message; box.hidden = !message; }

function setBusy(btn, busy, idleText) {
  btn.disabled = busy;
  btn.textContent = "";
  if (busy) btn.append(h("span", { class: "spinner", "aria-hidden": "true" }), " Analysing…");
  else btn.textContent = idleText;
}

function toast(message, kind) {
  let box = document.getElementById("toasts");
  if (!box) { box = h("div", { id: "toasts", class: "toasts", "aria-live": "polite" }); document.body.append(box); }
  const t = h("div", { class: "toast " + (kind || "info"), role: kind === "error" ? "alert" : "status" }, message);
  box.append(t);
  setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 300); }, kind === "error" ? 6000 : 3200);
}

/* Drag-and-drop zone that fills a file list. Returns {files(), clear()}. */
function setupDropzone({ zone, input, list, multiple, maxFiles, onChange }) {
  let files = [];
  const render = () => {
    list.replaceChildren(...files.map((f, i) => h("li", {},
      h("span", { text: f.name + " · " + formatBytes(f.size) }),
      h("button", { type: "button", "aria-label": "Remove " + f.name, onclick: () => { files.splice(i, 1); render(); } }, "✕"))));
    if (onChange) onChange(files);
  };
  const add = (incoming) => {
    const arr = Array.from(incoming);
    files = multiple ? files.concat(arr).slice(0, maxFiles || 1000) : arr.slice(0, 1);
    render();
  };
  zone.addEventListener("click", () => input.click());
  zone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
  input.addEventListener("change", () => { add(input.files); input.value = ""; });
  ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove("drag"); }));
  zone.addEventListener("drop", (e) => add(e.dataTransfer.files));
  return { files: () => files, clear: () => { files = []; render(); } };
}

function skillBlock(matched, related, missing) {
  const out = [];
  if (matched && matched.length) out.push(h("div", { class: "label-row", text: "Matched skills" }), chips(matched, "good"));
  if (related && related.length) out.push(h("div", { class: "label-row", text: "Related skills (partial credit)" }),
    chips(related.map((r) => `${r.has} ≈ ${r.required}`), "warn"));
  if (missing && missing.length) out.push(h("div", { class: "label-row", text: "Missing skills" }), chips(missing, "bad"));
  return out;
}

/* Forms with data-confirm="message" ask before submitting (delete buttons). */
document.addEventListener("submit", (e) => {
  const msg = e.target.dataset && e.target.dataset.confirm;
  if (msg && !window.confirm(msg)) e.preventDefault();
});
