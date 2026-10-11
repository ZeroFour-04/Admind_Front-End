/* Buscador de Unidades. Se carga antes que Alpine, los dos con defer.

   Solo filtra lo que la API ya entregó: qué viviendas existen y quién tiene vínculo con ellas lo decide
   el servidor. Aquí se compara el texto escrito con cada vivienda y se oculta lo que no coincide. */

// Las cédulas solo coinciden desde esta cantidad de caracteres: con «5» se busca la etapa 5, no a quien
// tiene una cédula que empieza por 5.
const MINIMO_PARA_DOCUMENTO = 5;

function palabrasDe(texto) {
  return String(texto ?? "")
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/(\d)[.,](?=\d)/g, "$1") // 1.000.000.001 → 1000000001
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

// Las palabras por las que se puede encontrar una vivienda, sin repetir.
function indexar(unidad) {
  const vistas = new Set();
  const indice = [];
  const agregar = (texto, documento = false) => {
    for (const palabra of palabrasDe(texto)) {
      const clave = (documento ? "#" : "") + palabra;
      if (vistas.has(clave)) continue;
      vistas.add(clave);
      indice.push({ palabra, documento });
    }
  };
  agregar(unidad.nombre);
  agregar(unidad.agrupacion);
  agregar(unidad.tipo);
  if (unidad.tipo === "apartamento") agregar("apto");
  agregar(unidad.numero);
  for (const persona of unidad.personas) {
    agregar(persona.nombre);
    agregar(persona.documento, true);
  }
  return indice;
}

// Cada palabra escrita debe empezar una palabra distinta de la vivienda: «etapa 5 apartamento 501» no
// encuentra «Etapa 1 – Apto 501», porque el 5 y el 501 no pueden ser la misma palabra. Las más largas
// primero, para que ninguna se quede sin su pareja.
function coincide(indice, fichas) {
  const usadas = new Set();
  for (const ficha of fichas) {
    const posicion = indice.findIndex(
      (entrada, i) =>
        !usadas.has(i) &&
        entrada.palabra.startsWith(ficha) &&
        (!entrada.documento || ficha.length >= MINIMO_PARA_DOCUMENTO),
    );
    if (posicion === -1) return false;
    usadas.add(posicion);
  }
  return true;
}

function nombresDe(unidad, tipo) {
  return unidad.personas.filter((p) => p.tipo === tipo).map((p) => p.nombre).join(", ");
}

document.addEventListener("alpine:init", () => {
  Alpine.data("directorioDeUnidades", ({ limite, hayAgrupaciones }) => {
    // Fuera del estado de Alpine: son cientos de filas que no cambian y no hace falta vigilarlas.
    let todas = [];

    return {
      consulta: "",

      init() {
        const datos = JSON.parse(document.getElementById("unidades-datos").textContent);
        todas = datos.map((unidad) => ({
          ...unidad,
          indice: indexar(unidad),
          propietarios: nombresDe(unidad, "propietario"),
          arrendatarios: nombresDe(unidad, "arrendatario"),
        }));
      },

      get escribiendo() {
        return palabrasDe(this.consulta).length > 0;
      },
      // Con agrupaciones, mientras no se busca nada se ven los recuadros.
      get mostrarRecuadros() {
        return hayAgrupaciones && !this.escribiendo;
      },
      get verResultados() {
        return !this.mostrarRecuadros;
      },
      get coinciden() {
        const fichas = palabrasDe(this.consulta).sort((a, b) => b.length - a.length);
        return fichas.length ? todas.filter((unidad) => coincide(unidad.indice, fichas)) : todas;
      },
      get visibles() {
        // Bajo los recuadros no hay tabla: no se pintan filas que nadie ve.
        if (this.mostrarRecuadros) return [];
        const encontradas = this.coinciden;
        return limite && encontradas.length > limite ? encontradas.slice(0, limite) : encontradas;
      },
      get resumen() {
        const total = this.coinciden.length;
        if (!total) return "";
        if (this.visibles.length < total) {
          return `Mostrando las primeras ${this.visibles.length} de ${total} viviendas. Escribe más para acotar.`;
        }
        return `${total} ${total === 1 ? "vivienda" : "viviendas"}`;
      },
    };
  });
});
