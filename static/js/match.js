"use strict";
(function () {
  const form = document.getElementById("match-form");
  const results = document.getElementById("results");
  const errBox = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  const sampleSel = document.getElementById("sample");
  const text = document.getElementById("resume_text");
  const dz = setupDropzone({
    zone: document.getElementById("dropzone"), input: document.getElementById("file"),
    list: document.getElementById("file-list"), multiple: false,
  });

  fetch("/api/samples").then((r) => r.json()).then((list) => {
    list.forEach((s) => sampleSel.append(h("option", { value: s.filename }, s.filename)));
  }).catch(() => {});

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(errBox, "");
    const fd = new FormData();
    if (dz.files().length) fd.append("resume", dz.files()[0], dz.files()[0].name);
    else if (text.value.trim()) fd.set("resume_text", text.value);
    else if (sampleSel.value) fd.set("sample", sampleSel.value);
    else return showError(errBox, "Upload a resume, paste its text, or choose a sample.");
    setBusy(btn, true);
    try { render(await postForm("/api/match", fd)); }
    catch (err) { showError(errBox, err.message); }
    finally { setBusy(btn, false, "Find matching roles"); }
  });

  function roleCard(r, i) {
    return h("article", { class: "cand" + (i === 0 ? " shortlisted" : "") },
      h("div", { class: "rank" }, "#" + (i + 1)),
      h("div", {},
        h("h3", {}, r.title, i === 0 ? h("span", { class: "badge" }, "BEST FIT") : null),
        h("p", { class: "muted small", text: r.description }),
        ...skillBlock(r.matched_skills, r.related_skills, []),
        r.skills_to_learn.length ? [h("div", { class: "label-row", text: "Skills to learn for this role" }), chips(r.skills_to_learn, "bad")] : null,
        h("details", { class: "more" }, h("summary", { text: "Score breakdown" }),
          h("div", { class: "bars" },
            bar("Text similarity", r.components.text_similarity),
            bar("Skill fit", r.components.skills),
            bar("Classifier probability", r.components.classifier)),
          h("p", { class: "muted small", text: "Typically asks for " + r.typical_min_years + "+ years of experience." }))),
      h("div", { class: "score" },
        h("div", { class: "num", text: r.score.toFixed(1) }), h("div", { class: "muted small", text: "/ 100" }),
        h("span", { class: "grade " + gradeClass(r.grade), text: r.grade })));
  }

  function render(d) {
    const c = d.candidate;
    results.replaceChildren(
      h("h2", { text: "Best matching roles" }),
      h("div", { class: "card" },
        h("h3", { text: c.name }),
        h("div", { class: "meta" },
          h("span", { text: "🕒 " + c.experience_years + " yrs experience" }),
          h("span", { text: "🎓 " + c.education.label }),
          c.email ? h("span", { text: "✉ " + c.email }) : null),
        h("div", { class: "kv" },
          h("div", {}, h("b", { text: "Naive Bayes classifies as" }), d.naive_bayes_role),
          h("div", {}, h("b", { text: "SVM classifies as" }), d.svm_role)),
        c.skills.length ? [h("div", { class: "label-row", text: "Skills detected (" + c.skills.length + ")" }), chips(c.skills, "tech")] :
          h("div", { class: "alert warn", text: "No known skills were detected in this resume." })),
      ...d.roles.map(roleCard));
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth" });
  }
})();
