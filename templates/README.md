# templates

Plantillas de Django compartidas por todas las apps. Las plantillas de cada pantalla viven dentro de su app.

## Qué va aquí

- `base/`: la estructura de cada página
- `componentes/`: fragmentos reutilizables con las clases del sistema de diseño

## Con qué se conecta

- `apps/`: toda plantilla de pantalla extiende una base de aquí
- `design-system/` y `static/css/`: las clases que usan
- `config/`: se declara como carpeta global de plantillas
