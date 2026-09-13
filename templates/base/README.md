# base

La estructura común de las páginas: `<head>`, estilos, Alpine, barra superior, navegación lateral y zona de contenido.

## Qué va aquí

- La plantilla raíz, que enlaza `design-system/styles.css` y los scripts de `static/js/`
- La estructura sin sesión, para el ingreso
- Las páginas de error

## Con qué se conecta

- `templates/componentes/`: `BarraSuperior` y `Lateral`
- `apps/`: todas las pantallas la extienden
- `static/`

## Reglas

- Contenido a máximo 1100px (§6.2)
- Usable a 200 % de zoom y a 360px de ancho (§6.6)
- El acento aparece en cuatro sitios y en ninguno más: botón primario, ítem activo de navegación, anillo de foco y franja del conjunto activo (§6.1)
