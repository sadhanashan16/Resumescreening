/* Shared helpers. All dynamic content is built with textContent (never innerHTML). */
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

async function postForm(url, formData) {
  const resp = await fetch(url, { method: "POST", body: formData });
  let data = null;
  try { data = await resp.json(); } catch (_) { /* non-JSON error body */ }
  if (!resp.ok) throw new Error((data && data.error) || `Request failed (${resp.status}).`);
  return data;
}

function showError(box, message) { box.textContent = message; box.hidden = !message; }

function setBusy(btn, busy, idleText) {
  btn.disabled = busy;
  btn.textContent = "";
  if (busy) btn.append(h("span", { class: "spinner", "aria-hidden": "true" }), " Analysing…");
  else btn.textContent = idleText;
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

function csvCell(v) {
  let s = v === null || v === undefined ? "" : String(v);
  // neutralise spreadsheet formula injection (but keep phone numbers like +44 7... intact)
  if (/^[=@\t\r]|^[+\-][^\d\s(]/.test(s)) s = "'" + s;
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function downloadCsv(filename, rows) {
  const blob = new Blob([rows.map((r) => r.map(csvCell).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const a = h("a", { href: URL.createObjectURL(blob), download: filename });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function skillBlock(matched, related, missing) {
  const out = [];
  if (matched && matched.length) out.push(h("div", { class: "label-row", text: "Matched skills" }), chips(matched, "good"));
  if (related && related.length) out.push(h("div", { class: "label-row", text: "Related skills (partial credit)" }),
    chips(related.map((r) => `${r.has} ≈ ${r.required}`), "warn"));
  if (missing && missing.length) out.push(h("div", { class: "label-row", text: "Missing skills" }), chips(missing, "bad"));
  return out;
}
