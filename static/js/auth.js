/* Sign up / log in helpers: password reveal, strength meter, instant client-side checks.
   The server validates everything again; this only improves feedback. */
"use strict";
(function () {
  document.querySelectorAll("[data-pw-toggle]").forEach((btn) => {
    const input = document.getElementById(btn.dataset.pwToggle);
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  });

  const form = document.querySelector("[data-auth-form]");
  if (!form) return;

  function setMsg(input, message) {
    const wrap = input.closest(".field");
    const msg = document.getElementById(input.id + "-msg");
    wrap.classList.toggle("has-error", !!message);
    input.setAttribute("aria-invalid", message ? "true" : "false");
    if (message) { msg.textContent = message; msg.classList.add("error"); }
  }

  // strength meter (register page)
  const pw = document.getElementById("password");
  const meter = document.getElementById("pw-strength");
  if (pw && meter) {
    const label = document.getElementById("pw-strength-label");
    const names = ["", "Weak", "Fair", "Good", "Strong"];
    pw.addEventListener("input", () => {
      const v = pw.value;
      let score = 0;
      if (v.length >= 8) score++;
      if (/[A-Za-z]/.test(v) && /\d/.test(v)) score++;
      if (v.length >= 12) score++;
      if (/[^A-Za-z0-9]/.test(v) && /[a-z]/.test(v) && /[A-Z]/.test(v)) score++;
      if (!v) score = 0;
      meter.dataset.level = String(score);
      label.textContent = names[score];
    });
  }

  form.addEventListener("submit", (e) => {
    let firstBad = null;
    const check = (id, test, message) => {
      const el = document.getElementById(id);
      if (!el) return;
      const bad = test(el.value);
      if (bad) { setMsg(el, message); firstBad = firstBad || el; }
    };
    const emailOk = (v) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.trim());
    check("email", (v) => !emailOk(v), "Enter a valid email address.");
    if (form.hasAttribute("data-register")) {
      check("name", (v) => v.trim().length < 2, "Enter your name.");
      check("password", (v) => v.length < 8 || !/[A-Za-z]/.test(v) || !/\d/.test(v), "Use at least 8 characters with a letter and a number.");
      check("confirm", (v) => v !== document.getElementById("password").value, "Passwords do not match.");
    } else {
      check("password", (v) => !v, "Enter your password.");
    }
    if (firstBad) { e.preventDefault(); firstBad.focus(); }
  });
})();
