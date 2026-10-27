document.addEventListener("DOMContentLoaded", () => {
  const formulario = document.querySelector("[data-vehiculo-selector]");
  const camposVehiculo = document.querySelector("[data-vehiculo-campos]");
  if (!formulario || !camposVehiculo) return;

  const selector = formulario.querySelectorAll('input[name="ingresa_con_vehiculo"]');
  const placa = camposVehiculo.querySelector('input[name="placa_vehiculo"]');
  const tipo = camposVehiculo.querySelector('select[name="tipo_vehiculo"]');
  // Puede no estar: sin parqueaderos libres la pantalla muestra un aviso en su lugar.
  const parqueadero = camposVehiculo.querySelector('select[name="parqueadero"]');

  const actualizarCamposVehiculo = () => {
    const ingresaConVehiculo = formulario.querySelector(
      'input[name="ingresa_con_vehiculo"]:checked'
    )?.value === "si";
    camposVehiculo.hidden = !ingresaConVehiculo;
    placa.required = ingresaConVehiculo;
    tipo.required = ingresaConVehiculo;
    placa.disabled = !ingresaConVehiculo;
    tipo.disabled = !ingresaConVehiculo;
    if (parqueadero) parqueadero.disabled = !ingresaConVehiculo;
    if (!ingresaConVehiculo) {
      placa.value = "";
      tipo.value = "";
      if (parqueadero) parqueadero.value = "";
    }
  };

  selector.forEach((opcion) => opcion.addEventListener("change", actualizarCamposVehiculo));
  actualizarCamposVehiculo();
});
