/* HEBAS shared UI behaviours: dark mode, toasts, confirm dialogs, submit spinners. */

// ---- Dark mode (persisted in localStorage; applied before paint) ----
(function () {
  try {
    if (localStorage.getItem("hebas-theme") === "dark")
      document.documentElement.classList.add("dark");
  } catch (e) {}
})();
function hebasToggleTheme() {
  var dark = document.documentElement.classList.toggle("dark");
  try { localStorage.setItem("hebas-theme", dark ? "dark" : "light"); } catch (e) {}
  var icon = document.getElementById("themeIcon");
  if (icon) icon.className = dark ? "bi bi-sun" : "bi bi-moon-stars";
}

(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var icon = document.getElementById("themeIcon");
    if (icon && document.documentElement.classList.contains("dark")) icon.className = "bi bi-sun";
  });

  // ---- Toasts ----------------------------------------------------------
  function toastContainer() {
    let c = document.getElementById("hebas-toasts");
    if (!c) {
      c = document.createElement("div");
      c.id = "hebas-toasts";
      c.className = "toast-container position-fixed top-0 end-0 p-3";
      c.style.zIndex = "1200";
      document.body.appendChild(c);
    }
    return c;
  }

  const ICONS = {
    success: "bi-check-circle-fill",
    danger: "bi-x-circle-fill",
    warning: "bi-exclamation-triangle-fill",
    info: "bi-info-circle-fill",
  };

  function showToast(message, category) {
    category = category || "info";
    const el = document.createElement("div");
    el.className = "toast hebas-toast border-0 toast-" + category;
    el.setAttribute("role", "alert");
    el.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body"><i class="bi ' + (ICONS[category] || ICONS.info) +
      ' me-2"></i>' + message + "</div>" +
      '<button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>' +
      "</div>";
    toastContainer().appendChild(el);
    const t = new bootstrap.Toast(el, { delay: 4000 });
    t.show();
    el.addEventListener("hidden.bs.toast", () => el.remove());
  }
  window.hebasToast = showToast;

  document.addEventListener("DOMContentLoaded", function () {
    // Render server-flashed messages (data-flash) as toasts.
    document.querySelectorAll("#hebas-flash-data [data-msg]").forEach((n) => {
      showToast(n.getAttribute("data-msg"), n.getAttribute("data-cat") || "info");
    });

    // ---- Confirmation dialogs ----------------------------------------
    document.body.addEventListener("submit", function (e) {
      if (e.defaultPrevented) return; // validation already blocked it
      const form = e.target;
      const msg = form.getAttribute("data-confirm");
      if (msg && !form.dataset._confirmed) {
        e.preventDefault();
        if (window.confirm(msg)) {
          form.dataset._confirmed = "1";
          form.submit();
        }
      }
    });

    // ---- Submit spinners (loading indicator) -------------------------
    document.body.addEventListener("submit", function (e) {
      if (e.defaultPrevented) return; // blocked by validation or a cancelled confirm
      const form = e.target;
      const btn = form.querySelector('button[type="submit"], button:not([type])');
      if (btn && !btn.disabled) {
        setTimeout(() => {
          btn.disabled = true;
          btn.dataset._html = btn.innerHTML;
          btn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-1"></span>' +
            (btn.dataset.loading || "Working...");
        }, 0);
      }
    });
  });
})();
