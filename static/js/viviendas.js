/* Paso «Viviendas» del asistente (HU-39). Se carga antes que Alpine, los dos con defer.

   Nada de esto decide: el navegador solo arma la descripción del conjunto y la frase que la
   resume. Qué viviendas salen de ella, cómo se llaman y cuáles ya existen lo calcula la API. */

// Las palabras más comunes. El conjunto puede escribir otra.
const ETIQUETAS = {
  apartamento: ["Torre", "Bloque", "Edificio", "Interior", "Etapa"],
  casa: ["Manzana", "Bloque", "Etapa", "Sector"],
};
const LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
// El mismo tope de la API.
const MAXIMO_DE_AGRUPACIONES = 60;
const CAMPOS_DEL_ESTADO = ["tipo", "mixto", "agrupa", "etiqueta", "otra", "modo", "cuantas", "nombres",
  "iguales", "pisos", "porPiso", "primerPiso", "cantidad", "filas", "patron", "desde"];

function enLineas(texto) {
  return texto.split("\n").map((linea) => linea.trim()).filter(Boolean);
}

document.addEventListener("alpine:init", () => {
  Alpine.data("asistenteDeViviendas", () => ({
    tipo: "",
    mixto: false,
    agrupa: true,
    etiqueta: "",
    otra: "",
    modo: "numeros",
    cuantas: 1,
    nombres: "",
    iguales: true,
    pisos: 5,
    porPiso: 4,
    primerPiso: 1,
    cantidad: 10,
    filas: [],
    patron: "",
    desde: 1,

    // Después de la vista previa el servidor devuelve las respuestas tal como se enviaron.
    init() {
      const guardado = JSON.parse(document.getElementById("estado-inicial").textContent);
      if (guardado) Object.assign(this, guardado);
      if (this.tipo && !this.patron) this.elegirTipo(this.tipo, this.mixto);
      this.alinear();
    },

    elegirTipo(tipo, mixto) {
      this.tipo = tipo;
      this.mixto = mixto;
      this.agrupa = true;
      this.etiqueta = "";
      this.patron = tipo === "apartamento" ? "piso_consecutivo" : "consecutivo";
    },

    plural(palabra) {
      if (/[aeiouáéíóú]$/i.test(palabra)) return palabra + "s";
      if (/z$/i.test(palabra)) return palabra.slice(0, -1) + "ces";
      if (/ón$/i.test(palabra)) return palabra.slice(0, -2) + "ones";
      return palabra + "es";
    },

    get palabra() {
      return this.tipo === "casa" ? "casa" : "apartamento";
    },
    get etiquetas() {
      return ETIQUETAS[this.tipo] || [];
    },
    get palabraDeAgrupacion() {
      if (!this.agrupa) return "";
      return this.etiqueta === "otra" ? this.otra.trim() : this.etiqueta;
    },
    get nombresDeAgrupaciones() {
      if (!this.agrupa) return [""];
      if (this.modo === "nombres") return enLineas(this.nombres).slice(0, MAXIMO_DE_AGRUPACIONES);
      const tope = this.modo === "letras" ? LETRAS.length : MAXIMO_DE_AGRUPACIONES;
      const cuantas = Math.max(0, Math.min(Number(this.cuantas) || 0, tope));
      return Array.from({ length: cuantas }, (_, i) => (this.modo === "letras" ? LETRAS[i] : String(i + 1)));
    },
    get porPisos() {
      return this.patron === "piso_consecutivo";
    },

    // Una fila por agrupación, para cuando no todas son iguales. Conserva lo ya escrito.
    alinear() {
      const nombres = this.nombresDeAgrupaciones;
      const igual = nombres.length === this.filas.length && nombres.every((nombre, i) => this.filas[i].nombre === nombre);
      if (igual) return;
      this.filas = nombres.map((nombre, i) => ({
        nombre,
        pisos: this.filas[i]?.pisos ?? this.pisos,
        porPiso: this.filas[i]?.porPiso ?? this.porPiso,
        cantidad: this.filas[i]?.cantidad ?? this.cantidad,
      }));
    },
    distintas(si) {
      this.iguales = !si;
      this.filas = [];
      this.alinear();
    },

    // Las agrupaciones como las espera la API. Con «todas iguales» se repiten los mismos números.
    get agrupaciones() {
      return this.nombresDeAgrupaciones.map((nombre, i) => {
        const fila = this.iguales ? this : this.filas[i] || this;
        if (this.porPisos) return { nombre, pisos: Number(fila.pisos) || 0, por_piso: Number(fila.porPiso) || 0 };
        return { nombre, cantidad: Number(fila.cantidad) || 0 };
      });
    },
    get total() {
      return this.agrupaciones.reduce((suma, a) => suma + (this.porPisos ? a.pisos * a.por_piso : a.cantidad), 0);
    },
    get especificacion() {
      const datos = {
        tipo_vivienda: this.tipo,
        etiqueta: this.palabraDeAgrupacion,
        patron: this.patron,
        agrupaciones: this.agrupaciones,
      };
      if (this.porPisos) datos.primer_piso = Number(this.primerPiso) || 1;
      if (this.patron === "corrido") datos.desde = Number(this.desde) || 1;
      return datos;
    },
    get estado() {
      return Object.fromEntries(CAMPOS_DEL_ESTADO.map((campo) => [campo, this[campo]]));
    },
    get listo() {
      const conAgrupacion = !this.agrupa || (this.palabraDeAgrupacion !== "" && this.agrupaciones.length > 0);
      return Boolean(this.tipo && this.patron && conAgrupacion && this.total > 0);
    },
    get frase() {
      if (!this.listo) return "";
      const viviendas = `${this.total} ${this.palabra}${this.total === 1 ? "" : "s"}`;
      if (!this.agrupa) return viviendas;
      const cuantas = this.agrupaciones.length;
      const palabra = cuantas === 1 ? this.palabraDeAgrupacion : this.plural(this.palabraDeAgrupacion);
      const grupos = `${cuantas} ${palabra.toLowerCase()}`;
      if (!this.iguales) return `${grupos}: ${viviendas}`;
      if (this.porPisos) return `${grupos} de ${this.pisos} pisos con ${this.porPiso} ${this.palabra}s por piso: ${viviendas}`;
      return `${grupos} de ${this.cantidad} ${this.palabra}s: ${viviendas}`;
    },
  }));
});
