// Avisa en rojo, debajo del campo y mientras se escribe, qué caracteres acepta. Lee `data-solo`, `minlength`
// y `maxlength`, que pone apps/usuarios/validacion.py. Es solo una ayuda: el formulario de Django y la API
// repiten la misma regla al enviar.
(function () {
  "use strict";

  var REGLAS = {
    digitos: { patron: /^[0-9]*$/, mensaje: "En este campo solo se aceptan números, sin puntos ni espacios.", unidad: "dígitos" },
    alfanumerico: { patron: /^[A-Za-z0-9]*$/, mensaje: "En este campo solo se aceptan letras y números, sin espacios ni símbolos.", unidad: "caracteres" },
    letras: { patron: /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]*$/, mensaje: "En este campo solo se aceptan letras y espacios.", unidad: "letras" },
    telefono: { patron: /^\+?[0-9]*$/, mensaje: "En este campo solo se aceptan números; puede iniciar con +.", unidad: "caracteres" },
  };

  // El documento acepta letras solo si es pasaporte; el tipo sale del select del mismo formulario.
  function reglaDe(campo) {
    var solo = campo.dataset.solo;
    if (solo !== "documento") return REGLAS[solo];
    var tipo = campo.form && campo.form.querySelector('select[name$="tipo_documento"]');
    return tipo && tipo.value === "PAS" ? REGLAS.alfanumerico : REGLAS.digitos;
  }

  function problema(campo, alEnviar) {
    var regla = reglaDe(campo);
    var valor = campo.value;
    if (!regla || valor === "") return "";
    if (!regla.patron.test(valor)) return regla.mensaje;
    var minimo = parseInt(campo.getAttribute("minlength"), 10);
    var maximo = parseInt(campo.getAttribute("maxlength"), 10);
    // El largo mínimo se avisa al salir del campo o al enviar, no con la primera tecla.
    if (alEnviar && minimo && valor.length < minimo) {
      return maximo
        ? "Debe tener entre " + minimo + " y " + maximo + " " + regla.unidad + "."
        : "Debe tener al menos " + minimo + " " + regla.unidad + ".";
    }
    return "";
  }

  function pintar(campo, mensaje) {
    var contenedor = campo.closest(".am-campo") || campo.parentNode;
    var aviso = contenedor.querySelector(".am-campo__error[data-validacion]");
    // El error que trajo el servidor se cambia por el aviso en vivo apenas la persona corrige.
    contenedor.querySelectorAll(".am-campo__error:not([data-validacion])").forEach(function (viejo) {
      viejo.remove();
    });
    if (!mensaje) {
      if (aviso) aviso.remove();
      campo.removeAttribute("aria-invalid");
      return;
    }
    if (!aviso) {
      aviso = document.createElement("span");
      aviso.className = "am-campo__error";
      aviso.dataset.validacion = "";
      aviso.id = (campo.id || campo.name) + "-aviso";
      aviso.setAttribute("aria-live", "polite");
      campo.insertAdjacentElement("afterend", aviso);
      var descritos = (campo.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
      if (descritos.indexOf(aviso.id) === -1) descritos.push(aviso.id);
      campo.setAttribute("aria-describedby", descritos.join(" "));
    }
    aviso.textContent = mensaje;
    campo.setAttribute("aria-invalid", "true");
  }

  function revisar(campo, alEnviar) {
    var mensaje = problema(campo, alEnviar);
    pintar(campo, mensaje);
    return !mensaje;
  }

  document.addEventListener("input", function (evento) {
    if (evento.target.matches && evento.target.matches("[data-solo]")) revisar(evento.target, false);
  });

  document.addEventListener("focusout", function (evento) {
    if (evento.target.matches && evento.target.matches("[data-solo]")) revisar(evento.target, true);
  });

  // Cambiar el tipo de documento cambia lo que el número acepta.
  document.addEventListener("change", function (evento) {
    var tipo = evento.target;
    if (!tipo.matches || !tipo.matches('select[name$="tipo_documento"]') || !tipo.form) return;
    tipo.form.querySelectorAll('[data-solo="documento"]').forEach(function (campo) {
      if (campo.value) revisar(campo, true);
    });
  });

  document.addEventListener(
    "submit",
    function (evento) {
      var primero = null;
      evento.target.querySelectorAll("[data-solo]").forEach(function (campo) {
        if (!campo.disabled && !revisar(campo, true) && !primero) primero = campo;
      });
      if (primero) {
        evento.preventDefault();
        evento.stopImmediatePropagation();
        primero.focus();
      }
    },
    true
  );
})();
