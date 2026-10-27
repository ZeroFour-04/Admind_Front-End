document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.querySelector("#confirmar-eliminar-usuario");
  const abrir = document.querySelector("[data-abrir-confirmacion]");
  if (!(dialog instanceof HTMLDialogElement) || !(abrir instanceof HTMLButtonElement)) return;

  abrir.addEventListener("click", () => dialog.showModal());
  dialog.querySelector("[data-cerrar-confirmacion]")?.addEventListener("click", () => dialog.close());
});
