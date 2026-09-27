/* Solicitud de reserva en trámite (HU-11 y HU-12). Se carga antes que Alpine, los dos con defer.

   El reloj arranca de los segundos que calculó el servidor: el navegador no decide si el
   bloqueo venció, solo lo muestra. Al salir de la pantalla sin enviar, suelta el bloqueo.
   El panel de confirmación vive en el mismo componente: abrirlo o cerrarlo no pide nada al
   servidor y no reinicia ni extiende el reloj. */
document.addEventListener("alpine:init", () => {
  Alpine.data("solicitudDeReserva", (segundos, urlLiberar) => ({
    restantes: segundos,
    // Si el formulario se está enviando (Cancelar o Enviar), salir de la página no suelta nada.
    enviando: false,
    // Panel de confirmación abierto. El formulario solo se oculta: lo escrito sigue ahí al corregir.
    revisando: false,
    asistentes: "",

    init() {
      const campoAsistentes = this.$root.querySelector("[name=asistentes]");
      if (campoAsistentes) {
        this.asistentes = campoAsistentes.value;
        campoAsistentes.addEventListener("input", () => (this.asistentes = campoAsistentes.value));
      }
      const vence = Date.now() + segundos * 1000;
      const reloj = setInterval(() => {
        this.restantes = Math.max(0, Math.round((vence - Date.now()) / 1000));
        if (this.restantes === 0) clearInterval(reloj);
      }, 1000);
      window.addEventListener("pagehide", () => this.soltar(urlLiberar));
    },

    get vencido() {
      return this.restantes === 0;
    },

    get reloj() {
      const minutos = Math.floor(this.restantes / 60);
      const segundosSueltos = String(this.restantes % 60).padStart(2, "0");
      return `${minutos}:${segundosSueltos}`;
    },

    revisar(formulario) {
      if (formulario.reportValidity()) this.revisando = true;
    },

    soltar(url) {
      if (this.enviando || this.vencido) return;
      const datos = new FormData();
      datos.append("csrfmiddlewaretoken", this.$root.querySelector("[name=csrfmiddlewaretoken]").value);
      navigator.sendBeacon(url, datos);
    },
  }));
});
