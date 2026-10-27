/* Búsqueda por palabras para las pantallas con buscador. Se carga antes que el script de la pantalla, los
   dos con defer.

   Solo compara el texto escrito con lo que la API ya entregó: qué personas o viviendas existen lo decide
   el servidor. Cada palabra escrita debe empezar una palabra distinta de lo buscado: «torre 2 402» no
   encuentra «Torre 2 – 202», porque el 2 y el 402 no pueden ser la misma palabra. */
(() => {
  // Las cédulas solo coinciden desde esta cantidad de caracteres: con «4» se busca la torre 4, no a quien
  // tiene una cédula que empieza por 4.
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

  // Las palabras por las que se puede encontrar algo, sin repetir. `textos` se buscan por palabra;
  // `documentos`, solo con MINIMO_PARA_DOCUMENTO caracteres o más.
  function indexar(textos, documentos = []) {
    const vistas = new Set();
    const indice = [];
    const agregar = (texto, documento) => {
      for (const palabra of palabrasDe(texto)) {
        const clave = (documento ? "#" : "") + palabra;
        if (vistas.has(clave)) continue;
        vistas.add(clave);
        indice.push({ palabra, documento });
      }
    };
    for (const texto of textos) agregar(texto, false);
    for (const documento of documentos) agregar(documento, true);
    return indice;
  }

  // Las palabras de la consulta, las más largas primero para que ninguna se quede sin su pareja.
  function fichasDe(consulta) {
    return palabrasDe(consulta).sort((a, b) => b.length - a.length);
  }

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

  window.busquedaDePalabras = { palabrasDe, indexar, fichasDe, coincide };
})();
