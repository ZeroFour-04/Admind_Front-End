# apps

Una app de Django por módulo. Cada una tiene su pareja con el mismo nombre en `Admind_Backend/apps/`.

## Forma de cada app, cuando haya código

Vistas, URLs y sus plantillas en `templates/<app>/`. Sin modelos de dominio: los datos llegan de la API.

## Con qué se conecta

- `cliente_api/`: la única vía hacia el backend
- `templates/base/` y `templates/componentes/`: toda pantalla extiende una base y usa los componentes compartidos
- `static/`: el CSS y el comportamiento propios del módulo
- `config/`: registra la app

## Diferencias con el backend

- `paneles` existe solo aquí: los inicios por rol juntan datos de varios módulos
- `permisos` no tiene app propia: la asignación de roles se hace desde `personas`
- `comun` no tiene pantalla
