/* Identidad del conjunto (HU-21): el color propio y la foto 1:1. Se carga antes que Alpine, los dos con defer.

   Nada de esto decide: la API valida el color y rechaza la foto que no sea cuadrada. Aquí solo
   se marca "Personalizado" al elegir un color, se advierte si el texto blanco se leería mal, y
   se recorta la foto en el navegador para que llegue cuadrada. */

// El mismo límite de la API (512 KB).
const TAMANO_MAXIMO_FOTO = 512 * 1024;
// Lado en píxeles de la foto que se sube.
const LADO_DE_LA_FOTO = 512;
const CONTRASTE_MINIMO = 4.5;

function luminancia(hex) {
  const [r, g, b] = [1, 3, 5].map((inicio) => {
    const canal = parseInt(hex.slice(inicio, inicio + 2), 16) / 255;
    return canal <= 0.04045 ? canal / 12.92 : ((canal + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function comoBlob(lienzo, tipo, calidad) {
  return new Promise((resolver) => lienzo.toBlob(resolver, tipo, calidad));
}

document.addEventListener("alpine:init", () => {
  Alpine.data("selectorDeColor", () => ({
    color: "",
    personalizado: false,

    init() {
      this.color = this.$refs.color.value;
      this.revisar();
    },

    // Elegir un color en el selector del navegador es elegir el acento personalizado.
    elegir(valor) {
      this.color = valor;
      this.$refs.personalizado.checked = true;
      this.revisar();
    },

    revisar() {
      this.personalizado = this.$refs.personalizado.checked;
    },

    // Contraste del texto blanco de los botones sobre el color: (1 + 0.05) / (L + 0.05).
    get contraste() {
      return (1.05 / (luminancia(this.color) + 0.05)).toFixed(1);
    },

    get pocoLegible() {
      return Number(this.contraste) < CONTRASTE_MINIMO;
    },
  }));

  Alpine.data("recortadorDeFoto", () => ({
    url: null,
    // Hay una imagen cargada y encuadrada: al enviar se sube el recorte, no el archivo original.
    lista: false,
    enviando: false,
    ancho: 0,
    alto: 0,
    // Lado del cuadro en pantalla, en píxeles.
    marco: 0,
    zoom: 1,
    // Esquina superior izquierda de la imagen respecto al cuadro.
    x: 0,
    y: 0,
    arrastre: null,

    cargar(evento) {
      if (this.url) URL.revokeObjectURL(this.url);
      this.url = null;
      this.lista = false;
      const archivo = evento.target.files[0];
      if (!archivo) return;
      const url = URL.createObjectURL(archivo);
      const imagen = new Image();
      imagen.onload = () => {
        this.ancho = imagen.naturalWidth;
        this.alto = imagen.naturalHeight;
        this.zoom = 1;
        this.url = url;
        this.lista = true;
        this.$nextTick(() => {
          this.marco = this.$refs.marco.clientWidth;
          this.x = (this.marco - this.ancho * this.escala) / 2;
          this.y = (this.marco - this.alto * this.escala) / 2;
          this.limitar();
        });
      };
      // Si el navegador no la puede abrir, se sube tal cual y la API dice por qué no sirve.
      imagen.onerror = () => URL.revokeObjectURL(url);
      imagen.src = url;
    },

    // Con zoom 1 el lado corto de la imagen llena el cuadro.
    get escala() {
      return (this.marco / Math.min(this.ancho, this.alto)) * this.zoom;
    },

    get estilo() {
      const escala = this.escala;
      return `width:${this.ancho * escala}px;height:${this.alto * escala}px;transform:translate(${this.x}px,${this.y}px)`;
    },

    // La imagen siempre cubre el cuadro: no se puede arrastrar hasta dejar un borde vacío.
    limitar() {
      this.x = Math.min(0, Math.max(this.marco - this.ancho * this.escala, this.x));
      this.y = Math.min(0, Math.max(this.marco - this.alto * this.escala, this.y));
    },

    // Acercar deja quieto el punto que está en el centro del cuadro.
    acercar(zoom) {
      const antes = this.escala;
      const centroX = (this.marco / 2 - this.x) / antes;
      const centroY = (this.marco / 2 - this.y) / antes;
      this.zoom = zoom;
      this.x = this.marco / 2 - centroX * this.escala;
      this.y = this.marco / 2 - centroY * this.escala;
      this.limitar();
    },

    empezar(evento) {
      this.arrastre = { x: evento.clientX - this.x, y: evento.clientY - this.y };
      evento.currentTarget.setPointerCapture(evento.pointerId);
    },

    arrastrar(evento) {
      if (!this.arrastre) return;
      this.x = evento.clientX - this.arrastre.x;
      this.y = evento.clientY - this.arrastre.y;
      this.limitar();
    },

    soltar() {
      this.arrastre = null;
    },

    mover(dx, dy) {
      this.x += dx;
      this.y += dy;
      this.limitar();
    },

    // Dibuja lo que está dentro del cuadro en un lienzo cuadrado y lo pone en el campo del archivo.
    async enviar(evento) {
      if (!this.lista) return;
      evento.preventDefault();
      this.enviando = true;
      const lienzo = document.createElement("canvas");
      lienzo.width = lienzo.height = LADO_DE_LA_FOTO;
      const contexto = lienzo.getContext("2d");
      const imagen = this.$refs.marco.querySelector("img");
      const escala = this.escala;
      const dibujar = () =>
        contexto.drawImage(imagen, -this.x / escala, -this.y / escala, this.marco / escala, this.marco / escala, 0, 0, LADO_DE_LA_FOTO, LADO_DE_LA_FOTO);
      dibujar();
      // WebP pesa poco y guarda la transparencia. El navegador que no sepa crearlo devuelve PNG;
      // si ese PNG se pasa del límite, JPG sobre fondo blanco.
      let foto = await comoBlob(lienzo, "image/webp", 0.9);
      if (foto.size > TAMANO_MAXIMO_FOTO) {
        contexto.fillStyle = "#ffffff";
        contexto.fillRect(0, 0, LADO_DE_LA_FOTO, LADO_DE_LA_FOTO);
        dibujar();
        foto = await comoBlob(lienzo, "image/jpeg", 0.9);
      }
      const extension = { "image/webp": "webp", "image/png": "png", "image/jpeg": "jpg" }[foto.type];
      const archivos = new DataTransfer();
      archivos.items.add(new File([foto], `foto.${extension}`, { type: foto.type }));
      this.$refs.archivo.files = archivos.files;
      // submit() no vuelve a disparar el evento: el recorte no se repite.
      evento.target.submit();
    },
  }));
});
