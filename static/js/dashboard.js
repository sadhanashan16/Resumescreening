/* Dashboard: animate bars (widths come from data-w, no inline styles) and localise dates. */
"use strict";
(function () {
  document.querySelectorAll("[data-w]").forEach((el) => {
    requestAnimationFrame(() => { el.style.width = el.dataset.w + "%"; });
  });
  document.querySelectorAll(".js-date").forEach((el) => {
    const d = fmtDate(el.dataset.iso, true);
    if (d) el.textContent = d;
  });
})();
