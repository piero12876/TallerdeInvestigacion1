document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.querySelector(".menu-btn");
  const side = document.querySelector(".side");
  if (menuBtn && side) {
    menuBtn.addEventListener("click", () => {
      const open = side.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    side.querySelectorAll(".nav a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.matchMedia("(max-width: 860px)").matches) {
          side.classList.remove("is-open");
          menuBtn.setAttribute("aria-expanded", "false");
        }
      });
    });
  }

  const path = location.pathname;
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.getAttribute("href") === path || (path !== "/" && a.getAttribute("href") !== "/" && path.startsWith(a.getAttribute("href")))) {
      a.classList.add("active");
    }
  });

  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (ev) => {
      if (!window.confirm(el.getAttribute("data-confirm"))) {
        ev.preventDefault();
      }
    });
  });

  document.querySelectorAll("[data-row-filter]").forEach((input) => {
    const table = document.querySelector(input.getAttribute("data-row-filter"));
    if (!table) return;
    input.addEventListener("input", () => {
      const q = input.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach((tr) => {
        tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
      });
    });
  });

  document.querySelectorAll("[data-digits]").forEach((input) => {
    const limit = Number(input.getAttribute("maxlength") || 32);
    const apply = () => {
      input.value = input.value.replace(/\D/g, "").slice(0, limit);
    };
    input.addEventListener("input", apply);
    input.addEventListener("paste", () => setTimeout(apply, 0));
  });

  document.querySelectorAll("[data-letters]").forEach((input) => {
    const apply = () => {
      input.value = input.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ' . -]/g, "");
    };
    input.addEventListener("input", apply);
    input.addEventListener("paste", () => setTimeout(apply, 0));
  });

  document.querySelectorAll("[data-username]").forEach((input) => {
    const apply = () => {
      input.value = input.value.toLowerCase().replace(/[^a-z0-9._-]/g, "");
    };
    input.addEventListener("input", apply);
    input.addEventListener("paste", () => setTimeout(apply, 0));
  });

  document.querySelectorAll("[data-grade]").forEach((input) => {
    input.addEventListener("keydown", (ev) => {
      if (["e", "E", "+", "-"].includes(ev.key)) ev.preventDefault();
    });
  });

  const spanishInvalid = (input) => {
    if (input.validity.valueMissing) return "Este campo es obligatorio.";
    if (input.validity.tooShort) return `Mínimo ${input.minLength} caracteres.`;
    if (input.validity.tooLong) return `Máximo ${input.maxLength} caracteres.`;
    if (input.validity.rangeOverflow) return `El valor no puede ser mayor que ${input.max}.`;
    if (input.validity.rangeUnderflow) return `El valor no puede ser menor que ${input.min}.`;
    if (input.validity.stepMismatch) return "Use un decimal de un dígito (ejemplo: 15.5).";
    if (input.validity.typeMismatch) return "El valor no tiene el formato correcto.";
    if (input.validity.patternMismatch) return input.title || "El formato no es válido.";
    return input.title || "Revise este dato.";
  };

  document.querySelectorAll("input, textarea, select").forEach((input) => {
    input.addEventListener("invalid", () => {
      input.setCustomValidity(spanishInvalid(input));
    });
    input.addEventListener("input", () => input.setCustomValidity(""));
    input.addEventListener("change", () => input.setCustomValidity(""));
  });

  document.querySelectorAll("form[method='post']").forEach((form) => {
    form.addEventListener("submit", (ev) => {
      if (!form.checkValidity()) {
        ev.preventDefault();
        form.reportValidity();
        return;
      }
      const btn = form.querySelector("button[type=submit]");
      if (btn && btn.dataset.busy === "1") {
        ev.preventDefault();
        return;
      }
      if (btn) {
        btn.dataset.busy = "1";
        const label = btn.textContent;
        setTimeout(() => {
          btn.disabled = true;
          btn.textContent = "Guardando…";
          btn.dataset.label = label;
        }, 0);
      }
    });
  });
});
