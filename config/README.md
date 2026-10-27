# config

Proyecto de Django del servidor web. No contiene lógica de negocio ni modelos de dominio.

## Qué va aquí

- Ajustes: apps instaladas, plantillas y archivos estáticos
- La dirección de la API del backend, por variable de entorno
- URLs raíz, que montan las URLs de cada app de `apps/`

## Con qué se conecta

- `apps/`: registra cada app y monta sus rutas
- `templates/` y `static/`: se declaran como carpetas globales
- `design-system/`: se declara como carpeta de estáticos, para servirlo sin moverlo ni copiarlo
- `cliente_api/`: le entrega la dirección de la API

## Lo que no va

Acceso a las tablas de AdMind. Todo dato pasa por la API.

## Pendiente

- Dónde guarda este servidor sus propias sesiones, que depende de §12.7 b
