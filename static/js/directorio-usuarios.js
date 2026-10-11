/* Directorio de Usuarios: agrupa por rol, busca y ordena cada grupo. Se carga después de busqueda.js y antes
   que Alpine, los tres con defer.

   Solo presenta lo que la API ya entregó: quién tiene qué rol y dónde vive lo decide el servidor. Aquí se
   reparten las cuentas en sus grupos, se compara el texto escrito con cada una y se ordena a pedido. */

document.addEventListener("alpine:init", () => {
  const { palabrasDe, indexar, fichasDe, coincide } = window.busquedaDePalabras;
  // Un grupo con más personas que estas arranca recogido: el equipo de la administración se ve de entrada
  // y los residentes, que son muchos, se abren a pedido.
  const MAXIMO_PARA_ABRIR = 10;
  // Para ordenar por vivienda: quien no tiene ninguna va al final, y la vivienda sin agrupación, justo antes.
  const SIN_VIVIENDA = Number.MAX_SAFE_INTEGER;
  const SIN_AGRUPACION = SIN_VIVIENDA - 1;
  // «Torre 2» antes que «Torre 10», y sin que las tildes ni las mayúsculas cambien el orden.
  const comparador = new Intl.Collator("es", { sensitivity: "base", numeric: true });

  // La vivienda por la que se ordena a una persona con varias: la de la agrupación que se creó primero.
  function claveDeVivienda(unidades) {
    const ordenadas = unidades
      .map((unidad) => ({ orden: unidad.orden ?? SIN_AGRUPACION, nombre: unidad.nombre }))
      .sort((a, b) => a.orden - b.orden || comparador.compare(a.nombre, b.nombre));
    return ordenadas[0] ?? { orden: SIN_VIVIENDA, nombre: "" };
  }

  const unicos = (textos) => [...new Set(textos.filter(Boolean))].join(", ");

  const ORDENES = {
    nombre: (a, b) => comparador.compare(a.nombre, b.nombre) || comparador.compare(a.correo, b.correo),
    correo: (a, b) => comparador.compare(a.correo, b.correo) || comparador.compare(a.nombre, b.nombre),
    vivienda: (a, b) =>
      a.clave.orden - b.clave.orden || comparador.compare(a.clave.nombre, b.clave.nombre) || ORDENES.nombre(a, b),
  };
  const OPCIONES_DE_ORDEN = [
    { valor: "nombre", etiqueta: "Nombre (A–Z)" },
    { valor: "vivienda", etiqueta: "Agrupación y vivienda" },
    { valor: "correo", etiqueta: "Correo (A–Z)" },
  ];

  Alpine.data("directorioDeUsuarios", () => {
    // Fuera del estado de Alpine: son cientos de filas que no cambian y no hace falta vigilarlas.
    let todos = [];
    let grupos = [];
    const totales = {};
    const conViviendas = {};

    return {
      consulta: "",
      // Rol → lo que eligió quien usa la página. Sin entrada, vale lo de siempre: «nombre» y, abierto,
      // lo que dice el tamaño del grupo.
      orden: {},
      abiertos: {},

      init() {
        const usuarios = JSON.parse(document.getElementById("usuarios-datos").textContent);
        grupos = JSON.parse(document.getElementById("usuarios-grupos").textContent);
        const titulos = Object.fromEntries(grupos.map((grupo) => [grupo.rol, grupo.titulo]));
        todos = usuarios.map((usuario) => ({
          ...usuario,
          indice: indexar(
            [
              usuario.nombre,
              usuario.correo,
              titulos[usuario.rol],
              ...usuario.unidades.flatMap((unidad) => [unidad.nombre, unidad.agrupacion]),
            ],
            [usuario.documento],
          ),
          clave: claveDeVivienda(usuario.unidades),
          agrupaciones: unicos(usuario.unidades.map((unidad) => unidad.agrupacion)),
          viviendas: unicos(usuario.unidades.map((unidad) => unidad.nombre)),
        }));
        for (const usuario of todos) {
          totales[usuario.rol] = (totales[usuario.rol] ?? 0) + 1;
          if (usuario.unidades.length) conViviendas[usuario.rol] = true;
        }
        // Al buscar se abren los grupos con resultados: quien busca quiere ver lo que encontró.
        this.$watch("consulta", () => {
          if (!this.escribiendo) return;
          for (const grupo of this.grupos) this.abiertos[grupo.rol] = true;
        });
      },

      get escribiendo() {
        return palabrasDe(this.consulta).length > 0;
      },
      // Los grupos con alguien que coincide, cada uno con sus filas ya ordenadas.
      get grupos() {
        const fichas = fichasDe(this.consulta);
        const coinciden = fichas.length ? todos.filter((usuario) => coincide(usuario.indice, fichas)) : todos;
        return grupos
          .map((grupo) => ({
            ...grupo,
            total: totales[grupo.rol] ?? 0,
            conViviendas: Boolean(conViviendas[grupo.rol]),
            filas: coinciden.filter((usuario) => usuario.rol === grupo.rol).sort(ORDENES[this.ordenDe(grupo.rol)]),
          }))
          .filter((grupo) => grupo.filas.length);
      },

      ordenDe(rol) {
        return this.orden[rol] ?? "nombre";
      },
      // «Agrupación y vivienda» solo se ofrece donde alguien tiene vivienda.
      opcionesDe(grupo) {
        return OPCIONES_DE_ORDEN.filter((opcion) => opcion.valor !== "vivienda" || grupo.conViviendas);
      },
      conteoDe(grupo) {
        return grupo.filas.length === grupo.total ? String(grupo.total) : `${grupo.filas.length} de ${grupo.total}`;
      },

      estaAbierto(rol) {
        return this.abiertos[rol] ?? (totales[rol] ?? 0) <= MAXIMO_PARA_ABRIR;
      },
      alternar(rol) {
        this.abiertos[rol] = !this.estaAbierto(rol);
      },
      get todosAbiertos() {
        return this.grupos.every((grupo) => this.estaAbierto(grupo.rol));
      },
      alternarTodos() {
        const abrir = !this.todosAbiertos;
        for (const grupo of this.grupos) this.abiertos[grupo.rol] = abrir;
      },

      get resumen() {
        const mostrados = this.grupos.reduce((suma, grupo) => suma + grupo.filas.length, 0);
        if (!mostrados) return "";
        const palabra = todos.length === 1 ? "usuario" : "usuarios";
        return mostrados === todos.length ? `${todos.length} ${palabra}` : `${mostrados} de ${todos.length} ${palabra}`;
      },
    };
  });
});
