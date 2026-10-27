(() => {
  const formulario = document.querySelector(".citas-formulario");
  if (!formulario) return;

  const modo = formulario.querySelector('input[name="modo"]:checked');
  const opciones = formulario.querySelectorAll('input[name="modo"]');
  const comun = formulario.querySelector('[data-configuracion="comun"]');
  const porDia = formulario.querySelector('[data-configuracion="por_dia"]');
  const rango = formulario.querySelector("[data-rango-dias]");

  const actualizar = (seleccionado) => {
    const usaHorarioComun = seleccionado !== "por_dia";
    comun.hidden = !usaHorarioComun;
    porDia.hidden = usaHorarioComun;
    rango.hidden = seleccionado !== "rango";
  };

  if (modo) actualizar(modo.value);
  opciones.forEach((opcion) => {
    opcion.addEventListener("change", () => actualizar(opcion.value));
  });
})();
