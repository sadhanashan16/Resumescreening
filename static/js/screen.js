"use strict";
(function () {
  const form = document.getElementById("screen-form");
  const results = document.getElementById("results");
  const errBox = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  const jd = document.getElementById("job_description");
  const maxFiles = Number(document.getElementById("top_n").max) || 30;
  const dz = setupDropzone({
    zone: document.getElementById("dropzone"), input: document.getElementById("files"),
    list: document.getElementById("file-list"), multiple: true, maxFiles,
  });
  let roles = [];

  fetch("/api/roles").then((r) => r.json()).then((d) => { roles = d; }).catch(() => {});
  document.getElementById("example").addEventListener("change", (e) => {
    const role = roles.find((r) => r.id === e.target.value);
    if (role) { jd.value = role.example_job_description; document.getElementById("job_title").value = role.title; }
  });

  const samplesBox = document.getElementById("samples");
  document.getElementById("samples-link").addEventListener("click", (e) => {
    e.preventDefault();
    samplesBox.hidden = false;
    fetch("/api/samples").then((r) => r.json()).then((list) => {
      samplesBox.querySelector("#sample-links").replaceChildren(
        ...list.map((s) => h("a", { class: "chip", href: s.url, download: s.filename }, "⬇ " + s.filename)));
    });
    samplesBox.scrollIntoView({ behavior: "smooth" });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(errBox, "");
    const useSamples = document.getElementById("use_samples").checked;
    if (jd.value.trim().length < 30) return showError(errBox, "Please paste a job description (at least a couple of sentences).");
    if (!dz.files().length && !useSamples) return showError(errBox, "Add at least one resume or tick the sample resumes option.");
    const fd = new FormData();
    fd.set("job_description", jd.value);
    fd.set("job_title", document.getElementById("job_title").value);
    fd.set("top_n", document.getElementById("top_n").value || "5");
    if (useSamples) fd.set("use_samples", "1");
    dz.files().forEach((f) => fd.append("resumes", f, f.name));
    setBusy(btn, true);
    try {
      render(await postForm("/api/screen", fd));
    } catch (err) {
      showError(errBox, err.message);
    } finally {
      setBusy(btn, false, "Analyse resumes");
    }
  });

  function candidateCard(c) {
    const comp = c.components;
    const labels = { text_similarity: "Text similarity", skills: "Skill coverage", role_fit: "Role fit", experience: "Experience", education: "Education" };
    return h("article", { class: "cand" + (c.shortlisted ? " shortlisted" : "") },
      h("div", { class: "rank", "aria-label": "Rank " + c.rank }, "#" + c.rank),
      h("div", {},
        h("h3", {}, c.name, c.shortlisted ? h("span", { class: "badge" }, "SHORTLISTED") : null),
        h("div", { class: "meta" },
          h("span", { text: "📁 " + c.filename }),
          c.email ? h("span", { text: "✉ " + c.email }) : null,
          c.phone ? h("span", { text: "☎ " + c.phone }) : null),
        h("div", { class: "meta" },
          h("span", { text: "🕒 " + c.experience_years + " yrs experience" }),
          h("span", { text: "🎓 " + c.education.label }),
          h("span", { text: "🧭 Predicted role: " + c.predicted_role.title + " (" + Math.round(c.predicted_role.confidence * 100) + "%)" })),
        ...skillBlock(c.matched_skills, c.related_skills, c.missing_skills),
        h("details", { class: "more" }, h("summary", { text: "Score breakdown & details" }),
          h("div", { class: "bars" }, Object.keys(labels).map((k) => comp[k] === null ? null : bar(labels[k] + " (" + Math.round(c.weights_used[k] * 100) + "% weight)", comp[k]))),
          h("div", { class: "kv" },
            h("div", {}, h("b", { text: "Naive Bayes says" }), c.naive_bayes_role),
            h("div", {}, h("b", { text: "SVM says" }), c.svm_role),
            h("div", {}, h("b", { text: "Education detail" }), c.education.detail || "–"),
            h("div", {}, h("b", { text: "Top role probabilities" }), c.top_roles.map((r) => r.title + " " + Math.round(r.probability * 100) + "%").join(" · "))),
          c.extra_skills.length ? [h("div", { class: "label-row", text: "Other technical skills" }), chips(c.extra_skills, "tech")] : null)),
      h("div", { class: "score" },
        h("div", { class: "num", text: c.score.toFixed(1) }),
        h("div", { class: "muted small", text: "/ 100" }),
        h("span", { class: "grade " + gradeClass(c.grade), text: c.grade })));
  }

  function render(data) {
    const j = data.job;
    const reqs = [
      j.min_years ? j.min_years + "+ yrs experience" : "no experience requirement found",
      j.education_level ? ["", "High school", "Diploma", "Bachelor's", "Master's", "Doctorate"][j.education_level] + " required" : "no education requirement found",
    ];
    const nodes = [
      h("h2", { text: "Results" }),
      h("div", { class: "card" },
        h("div", { class: "job-banner" }, h("strong", { text: j.title }),
          h("span", { class: "chip", text: "Job type detected: " + j.predicted_role.title + " (" + Math.round(j.predicted_role.confidence * 100) + "%)" }),
          h("span", { class: "muted small", text: reqs.join(" · ") })),
        j.skills.length ? [h("div", { class: "label-row", text: "Skills extracted from the job description" }), chips(j.skills, "tech")] :
          h("div", { class: "alert warn", text: "No known skills were found in the job description, so ranking relies on text similarity only. Try listing specific skills." })),
      h("div", { class: "stats", style: null },
        h("div", { class: "stat" }, h("b", { text: data.summary.total }), "resumes analysed"),
        h("div", { class: "stat" }, h("b", { text: data.shortlist_size }), "shortlisted"),
        h("div", { class: "stat" }, h("b", { text: data.summary.strong_matches }), "strong matches (70+)"),
        h("div", { class: "stat" }, h("b", { text: data.summary.average_score }), "average score")),
      h("div", { class: "toolbar no-print" },
        h("button", { class: "btn btn-sm", type: "button", onclick: () => exportCsv(data, true) }, "⬇ Download shortlist (CSV)"),
        h("button", { class: "btn btn-sm", type: "button", onclick: () => exportCsv(data, false) }, "⬇ Download all (CSV)"),
        h("button", { class: "btn btn-sm", type: "button", onclick: () => window.print() }, "🖨 Print"),
        h("span", { class: "spacer" })),
    ];
    if (data.errors && data.errors.length) {
      nodes.push(h("div", { class: "alert warn" }, h("strong", { text: data.errors.length + " file(s) could not be read:" }),
        h("ul", {}, data.errors.map((x) => h("li", { text: x.filename + " - " + x.error })))));
    }
    data.candidates.forEach((c) => nodes.push(candidateCard(c)));
    results.replaceChildren(...nodes);
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth" });
  }

  function exportCsv(data, onlyShortlist) {
    const rows = [["Rank", "Name", "File", "Email", "Phone", "Score", "Grade", "Shortlisted", "Experience (yrs)", "Education",
      "Predicted role", "Matched skills", "Related skills", "Missing skills"]];
    data.candidates.filter((c) => !onlyShortlist || c.shortlisted).forEach((c) => rows.push([
      c.rank, c.name, c.filename, c.email, c.phone, c.score, c.grade, c.shortlisted ? "yes" : "no", c.experience_years,
      c.education.label, c.predicted_role.title, c.matched_skills.join("; "),
      c.related_skills.map((r) => r.has + "~" + r.required).join("; "), c.missing_skills.join("; ")]));
    downloadCsv(onlyShortlist ? "shortlist.csv" : "all-candidates.csv", rows);
  }
})();
