/* Al volver con «atrás», el navegador puede mostrar la página tal como quedó en memoria (bfcache),
   sin preguntarle al servidor, aunque la sesión ya se haya cerrado. Si la página viene de ahí, se
   vuelve a pedir: con la sesión cerrada, el servidor manda al ingreso. */
window.addEventListener("pageshow", function (evento) {
  if (evento.persisted) {
    window.location.reload();
  }
});
