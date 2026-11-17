/* Fondo de la interfaz: «liso», «color» o «cristal». Lo elige cada persona en el botón de la
   barra superior y se guarda solo en su navegador: el servidor no sabe nada de esto.

   Se carga en el <head>, sin defer, para poner data-fondo en <html> antes de que se pinte la
   página y que no haya un parpadeo. Sin JavaScript la página queda lisa, como antes. */
(function () {
  var CLAVE = "admind.fondo";
  var FONDOS = ["liso", "color", "cristal"];
  var PREDETERMINADO = "cristal";

  function leer() {
    try {
      var guardado = window.localStorage.getItem(CLAVE);
      return FONDOS.indexOf(guardado) >= 0 ? guardado : PREDETERMINADO;
    } catch (error) {
      return PREDETERMINADO;
    }
  }

  function guardar(fondo) {
    try {
      window.localStorage.setItem(CLAVE, fondo);
    } catch (error) {
      /* Navegación privada o almacenamiento bloqueado: el fondo vale solo para esta página. */
    }
  }

  function aplicar(fondo) {
    document.documentElement.setAttribute("data-fondo", fondo);
  }

  aplicar(leer());

  document.addEventListener("DOMContentLoaded", function () {
    var selectores = document.querySelectorAll("[data-apariencia]");
    selectores.forEach(function (selector) {
      var actual = document.documentElement.getAttribute("data-fondo");
      selector.querySelectorAll("input[name='fondo']").forEach(function (opcion) {
        opcion.checked = opcion.value === actual;
        opcion.addEventListener("change", function () {
          aplicar(opcion.value);
          guardar(opcion.value);
        });
      });
      // Se cierra al tocar fuera o con Escape.
      document.addEventListener("click", function (evento) {
        if (selector.open && !selector.contains(evento.target)) selector.open = false;
      });
      selector.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape" && selector.open) {
          selector.open = false;
          selector.querySelector("summary").focus();
        }
      });
    });
  });
})();
