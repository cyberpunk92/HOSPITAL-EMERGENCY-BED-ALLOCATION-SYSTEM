/* HEBAS client-side validation — mirrors config/validation.py.
   Opt in by adding `novalidate data-validate` to a <form> and `data-rule="..."`
   to inputs (space-separated: required alpha numeric email bed date-not-future). */
(function () {
  "use strict";

  const RE = {
    alpha: /^[A-Za-z][A-Za-z .'-]*$/,
    numeric: /^[0-9]+$/,
    email: /^[^@\s]+@[^@\s]+\.[^@\s]+$/,
    bed: /^[A-Za-z]{2,4}-\d{2,3}$/,
    cnic: /^\d{13}$/,
  };
  const MSG = {
    required: "This field is required.",
    alpha: "Letters only.",
    name: "Letters only, at least 2 characters.",
    numeric: "Digits only.",
    cnic: "CNIC must be exactly 13 digits.",
    phone: "Digits only, max 11.",
    email: "Enter a valid email.",
    bed: "Format like ER-01.",
    positive_int: "Enter a positive whole number.",
    non_negative: "Cannot be negative.",
    "date-not-future": "Date cannot be in the future.",
  };

  function fieldError(input) {
    const rules = (input.dataset.rule || "").split(/\s+/).filter(Boolean);
    const v = (input.value || "").trim();
    for (const r of rules) {
      if (r === "required" && v === "") return MSG.required;
      if (v === "") continue;
      if (r === "alpha" && !RE.alpha.test(v)) return MSG.alpha;
      if (r === "name" && (!RE.alpha.test(v) || v.length < 2)) return MSG.name;
      if (r === "numeric" && !RE.numeric.test(v)) return MSG.numeric;
      if (r === "cnic" && !RE.cnic.test(v)) return MSG.cnic;
      if (r === "phone" && (!RE.numeric.test(v) || v.length > 11)) return MSG.phone;
      if (r === "email" && !RE.email.test(v)) return MSG.email;
      if (r === "bed" && !RE.bed.test(v)) return MSG.bed;
      if (r === "positive_int" && !(RE.numeric.test(v) && +v > 0)) return MSG.positive_int;
      if (r === "non_negative" && !(RE.numeric.test(v) && +v >= 0)) return MSG.non_negative;
      if (r === "date-not-future" && v && new Date(v) > new Date(new Date().toDateString()))
        return MSG["date-not-future"];
    }
    return null;
  }

  function applyFeedback(input, err) {
    input.classList.toggle("is-invalid", !!err);
    let fb = input.parentNode.querySelector(".invalid-feedback");
    if (err) {
      if (!fb) {
        fb = document.createElement("div");
        fb.className = "invalid-feedback";
        input.parentNode.appendChild(fb);
      }
      fb.textContent = err;
    }
  }

  function validateForm(form) {
    let ok = true;
    form.querySelectorAll("[data-rule]").forEach((input) => {
      const err = fieldError(input);
      applyFeedback(input, err);
      if (err) ok = false;
    });
    return ok;
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-validate]").forEach((form) => {
      form.addEventListener("submit", function (e) {
        if (!validateForm(form)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
      // Live de-error on input.
      form.querySelectorAll("[data-rule]").forEach((input) => {
        input.addEventListener("input", () => applyFeedback(input, fieldError(input)));
      });
      // Block invalid characters while typing.
      const mask = (sel, fn) => form.querySelectorAll(sel).forEach((i) =>
        i.addEventListener("input", () => { i.value = fn(i.value); }));
      mask('[data-rule~="numeric"]', (s) => s.replace(/[^0-9]/g, ""));
      mask('[data-rule~="positive_int"]', (s) => s.replace(/[^0-9]/g, ""));
      mask('[data-rule~="non_negative"]', (s) => s.replace(/[^0-9]/g, ""));
      mask('[data-rule~="cnic"]', (s) => s.replace(/[^0-9]/g, "").slice(0, 13));
      mask('[data-rule~="phone"]', (s) => s.replace(/[^0-9]/g, "").slice(0, 11));
      mask('[data-rule~="alpha"]', (s) => s.replace(/[^A-Za-z .'-]/g, ""));
      mask('[data-rule~="name"]', (s) => s.replace(/[^A-Za-z .'-]/g, ""));
    });
  });

  window.HEBAS_validateForm = validateForm;
})();
