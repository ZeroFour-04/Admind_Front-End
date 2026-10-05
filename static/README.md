# static

Archivos estáticos propios del servidor web. El sistema de diseño **no** se copia aquí: se sirve desde `design-system/`.

## Qué va aquí

- `css/`: estilos propios de las pantallas
- `js/`: comportamiento con Alpine.js
- `img/`: el ícono de AdMind para la pestaña del navegador

`img/`: solo el ícono de la pestaña (`favicon.ico`, `favicon.png`, `apple-touch-icon.png`). El sistema de diseño no usa imágenes ni iconos (README de `design-system/`).

## Con qué se conecta

- `templates/base/`: los enlaza
- `config/`: se declara como carpeta de estáticos
