# css

Estilos propios de las pantallas, para lo que `design-system/` no cubre.

## Qué va aquí

- Hojas por módulo, escritas **solo con variables** del sistema de diseño

- `usuarios.css`: la lista de Usuarios (desplegable por rol, buscador y «Ordenar por»)
- `unidades.css`: los recuadros por agrupación y, en el detalle de una vivienda, el buscador de personas y el modal de residente

## Lo que no va

- Hex, colores sueltos o tokens nuevos. Los tokens viven en `design-system/tokens/`
- `--acento-*` en reglas que comunican estado (§6.1)
- Tailwind, Bootstrap o cualquier framework de CSS (§12.1)

## Con qué se conecta

- `design-system/styles.css`: el punto de entrada de los tokens, que se enlaza antes que estas hojas
- `templates/base/`

## Pendiente

El maestro (§6.2) pone los tokens en `static/css/tokens.css`; `design-system/` los tiene en `tokens/*.css`. Mientras el equipo no decida, **no se duplican aquí** (§6.3).
