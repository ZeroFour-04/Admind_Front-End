/* Vínculos de una vivienda: el buscador para elegir a la persona y el modal de «Crear nuevo residente».
   Se carga después de busqueda.js y antes que Alpine, los tres con defer.

   Nada de esto decide: qué personas hay en el conjunto y con qué rol se crean lo decide el servidor. Aquí
   solo se filtra la lista que la página ya trae y se abre o se cierra el modal. */

// Cuántas personas se listan a la vez: con más, se pide escribir para acotar (igual que en Unidades).
const MAXIMO_DE_PERSONAS_LISTADAS = 50;

document.addEventListener("alpine:init", () => {
  const { indexar, fichasDe, coincide } = window.busquedaDePalabras;

  Alpine.data("selectorDePersona", () => {
    // Fuera del estado de Alpine: pueden ser cientos de filas que no cambian y no hace falta vigilarlas.
    let personas = [];

    return {
      consulta: "",
      // El id de la persona elegida; vacío mientras no se elija a nadie.
      elegida: "",

      init() {
        const datos = JSON.parse(document.getElementById("personas-datos").textContent);
        personas = datos.map((persona) => ({
          ...persona,
          indice: indexar([persona.nombre, persona.correo], [persona.documento]),
        }));
        // Si la página vuelve con alguien elegido (un error del formulario o un residente recién creado).
        this.elegida = this.$el.dataset.elegida || "";
      },

      get persona() {
        return personas.find((persona) => persona.id === this.elegida) ?? null;
      },
      get coinciden() {
        const fichas = fichasDe(this.consulta);
        return fichas.length ? personas.filter((persona) => coincide(persona.indice, fichas)) : personas;
      },
      get visibles() {
        return this.coinciden.slice(0, MAXIMO_DE_PERSONAS_LISTADAS);
      },
      get resumen() {
        const total = this.coinciden.length;
        if (!total) return "No encontramos a nadie con esa búsqueda. Si es un residente nuevo, créalo.";
        if (total > this.visibles.length) {
          return `Mostrando las primeras ${this.visibles.length} de ${total} personas. Escribe más para acotar.`;
        }
        return `${total} ${total === 1 ? "persona" : "personas"}`;
      },

      elegir(id) {
        this.elegida = id;
        this.consulta = "";
      },
      // Con Enter se elige a la primera de la lista, así no se envía el formulario sin nadie elegido.
      elegirPrimera() {
        const [primera] = this.coinciden;
        if (primera) this.elegir(primera.id);
      },
      cambiar() {
        this.elegida = "";
        // Por id y no con $refs: este método lo llama el botón de la persona elegida, que desaparece al cambiar.
        this.$nextTick(() => document.getElementById("buscar-persona")?.focus());
      },
    };
  });
});

// El modal es un <dialog> del navegador: showModal() lo abre sobre la página y Escape lo cierra.
document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("click", (evento) => {
    const abrir = evento.target.closest("[data-abrir-modal]");
    if (abrir) {
      const modal = document.getElementById(abrir.dataset.abrirModal);
      if (modal instanceof HTMLDialogElement) modal.showModal();
      return;
    }
    evento.target.closest("[data-cerrar-modal]")?.closest("dialog")?.close();
  });
  // Si el alta volvió con errores, el modal vuelve abierto para que se vean.
  for (const modal of document.querySelectorAll("dialog[data-abrir]")) modal.showModal();
});
