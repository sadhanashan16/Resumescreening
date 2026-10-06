"use strict";
(function () {
  const m = JSON.parse(document.getElementById("metrics-data").textContent);

  document.getElementById("per-role").replaceChildren(h("div", { class: "bars" },
    m.per_role.map((r) => bar(r.title + " (n=" + r.support + ")", r.f1 * 100))),
    h("p", { class: "muted small", text: "Bars show F1 score per role." }));

  const { labels, matrix } = m.confusion_matrix;
  const max = Math.max(1, ...matrix.flat());
  const table = document.getElementById("cm");
  table.replaceChildren(
    h("thead", {}, h("tr", {}, h("th", { text: "" }), labels.map((l) => h("th", { class: "rot", text: l })))),
    h("tbody", {}, matrix.map((row, i) => h("tr", {}, h("th", { text: labels[i] }),
      row.map((v, j) => {
        const td = h("td", { text: v || "" });
        const a = v / max;
        td.style.background = v ? `color-mix(in srgb, ${i === j ? "var(--accent)" : "var(--bad)"} ${Math.round(15 + a * 80)}%, transparent)` : "transparent";
        if (a > 0.55) td.style.color = "#fff";
        return td;
      })))));

  document.getElementById("features").replaceChildren(...Object.entries(m.top_features).map(([role, terms]) =>
    h("div", { class: "card" }, h("h3", { text: role }), chips(terms, "tech"))));
})();
