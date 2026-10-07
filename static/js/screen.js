/* New screening: send job description + resumes to /api/screen (existing ML pipeline), then open the saved results. */
"use strict";
(function () {
  const form = document.getElementById("screen-form");
  const errBox = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  const jd = document.getElementById("job_description");
  const busy = document.getElementById("busy");
  const maxFiles = Number(document.getElementById("top_n").max) || 30;
  const dz = setupDropzone({
    zone: document.getElementById("dropzone"), input: document.getElementById("files"),
    list: document.getElementById("file-list"), multiple: true, maxFiles,
  });
  const rolesReady = fetch("/api/roles", { credentials: "same-origin" }).then((r) => r.ok ? r.json() : []).catch(() => []);
  document.getElementById("example").addEventListener("change", async (e) => {
    const roles = await rolesReady;             // safe even if chosen before the list has finished loading
    const role = roles.find((r) => r.id === e.target.value);
    if (role) { jd.value = role.example_job_description; document.getElementById("job_title").value = role.title; }
  });

  const example = document.getElementById("example");
  if (example.value) example.dispatchEvent(new Event("change"));   // chosen before this script finished loading

  const samplesBox = document.getElementById("samples");
  document.getElementById("samples-link").addEventListener("click", (e) => {
    e.preventDefault();
    samplesBox.hidden = false;
    fetch("/api/samples", { credentials: "same-origin" }).then((r) => r.json()).then((list) => {
      samplesBox.querySelector("#sample-links").replaceChildren(
        ...list.map((s) => h("a", { class: "chip", href: s.url, download: s.filename }, "⬇ " + s.filename)));
    });
    samplesBox.scrollIntoView({ behavior: "smooth" });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(errBox, "");
    const useSamples = document.getElementById("use_samples").checked;
    if (jd.value.trim().length < 30) { jd.focus(); return showError(errBox, "Please paste a job description (at least a couple of sentences)."); }
    if (!dz.files().length && !useSamples) return showError(errBox, "Add at least one resume or tick the sample resumes option.");
    const fd = new FormData();
    fd.set("job_description", jd.value);
    fd.set("job_title", document.getElementById("job_title").value);
    fd.set("top_n", document.getElementById("top_n").value || "5");
    if (useSamples) fd.set("use_samples", "1");
    dz.files().forEach((f) => fd.append("resumes", f, f.name));
    setBusy(btn, true);
    busy.hidden = false;
    try {
      const result = await postForm("/api/screen", fd);
      location.assign(result.url);                  // saved: show the ranked results
    } catch (err) {
      busy.hidden = true;
      setBusy(btn, false, "Analyse resumes");
      showError(errBox, err.message);
    }
  });
})();
