/* Mobile navigation drawer for the app shell. */
"use strict";
(function () {
  const toggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!toggle || !sidebar) return;

  function setOpen(open) {
    sidebar.classList.toggle("open", open);
    backdrop.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.classList.toggle("no-scroll", open);
    if (open) { const first = sidebar.querySelector("a"); if (first) first.focus(); } else { toggle.focus(); }
  }
  toggle.addEventListener("click", () => setOpen(!sidebar.classList.contains("open")));
  backdrop.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && sidebar.classList.contains("open")) setOpen(false); });
  window.matchMedia("(min-width: 901px)").addEventListener("change", (m) => { if (m.matches && sidebar.classList.contains("open")) setOpen(false); });
})();
