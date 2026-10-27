document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.querySelector("#confirmar-eliminar-conjunto");
  const abrir = document.querySelector("[data-abrir-eliminar-conjunto]");
  if (!(dialog instanceof HTMLDialogElement) || !(abrir instanceof HTMLButtonElement)) return;

  abrir.addEventListener("click", () => dialog.showModal());
  dialog.querySelector("[data-cerrar-eliminar-conjunto]")?.addEventListener("click", () => dialog.close());
});
