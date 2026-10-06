// Menú de secciones en pantallas angostas: el lateral se abre como panel desde la izquierda.
// El ancho de corte es el mismo de static/css/estructura.css (900px).
document.addEventListener("DOMContentLoaded", () => {
  const lateral = document.querySelector("#menu-lateral");
  const abrir = document.querySelector("[data-abrir-menu]");
  if (!lateral || !(abrir instanceof HTMLButtonElement)) return;

  // Con el menú abierto, lo de atrás no recibe foco ni toques.
  const fondo = document.querySelectorAll(".am-barra, .vista");

  const poner = (abierto) => {
    lateral.classList.toggle("am-es-abierto", abierto);
    abrir.setAttribute("aria-expanded", String(abierto));
    fondo.forEach((parte) => parte.toggleAttribute("inert", abierto));
  };
  const cerrar = () => {
    if (!lateral.classList.contains("am-es-abierto")) return;
    poner(false);
    abrir.focus();
  };

  abrir.addEventListener("click", () => {
    poner(true);
    lateral.querySelector("[data-cerrar-menu]")?.focus();
  });
  document.querySelectorAll("[data-cerrar-menu]").forEach((pieza) => pieza.addEventListener("click", cerrar));
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") cerrar();
  });
  // Si la pantalla se ensancha con el menú abierto, el lateral vuelve a su sitio de siempre.
  window.matchMedia("(max-width:900px)").addEventListener("change", (corte) => {
    if (!corte.matches) poner(false);
  });
});
