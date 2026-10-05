document.querySelectorAll("[data-envio-al-cambiar]").forEach((selector) => {
  selector.addEventListener("change", () => selector.form.requestSubmit());
});
