# anuncios

Alcance: Comprometido (§3.2).

El tablón del conjunto.

## Qué va aquí

- Ver anuncios, con sus fotos como miniaturas (`_fotos.html`); cada una abre la foto completa en otra pestaña
- Publicar con alcance de todo el conjunto o de una vivienda, con el aviso en pantalla que separa el uso correcto del atajo (R14)
- Publicar con hasta 4 fotos PNG, JPG o WebP de hasta 5 MB. El formulario revisa el número y el peso; si de verdad son imágenes lo decide la API. Junto al campo va la advertencia de datos personales (Ley 1581)
- Solo se ofrecen los alcances que la persona puede usar: `anuncio.publicar` para el conjunto, `anuncio.dirigir` para una vivienda. La API los vuelve a exigir
- Editar el texto de un anuncio propio, sin volver a avisar (HU-25). El alcance y las fotos no se cambian
- La imagen de cada foto (`views.foto`): este servidor se la pide a la API con el token y se la pasa al navegador, que nunca habla con la API

## Con qué se conecta

- Backend: `Admind_Backend/apps/anuncios/`

## Referencias

Maestro §5.7 · R14
