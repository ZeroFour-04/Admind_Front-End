# triage

Alcance: Comprometido (§3.2).

El dashboard de gestión («Dashboard de Gestión de Reservas»). Lo usan Administración y Secretaría: entra quien tiene `solicitud.bandeja_ver`.

## Pantalla actual

`/solicitudes/` muestra a gestión tres pestañas, cada una con su tabla (`?pestana=reservas`, `casos` o `citas`). No hay vista combinada: las tres solicitudes no son una sola cosa y cada pestaña le pide las filas a su módulo.

| Pestaña | De dónde salen las filas | Columnas | A dónde lleva la fila |
|---|---|---|---|
| **Reservas** | `cliente_api.reservas.solicitudes_para_bandeja` | ID, zona, día y franja, estado, residente, vivienda, solicitada, pago | A la tarjeta de la solicitud en la pantalla de su zona (`#solicitud-<id>`), donde se aprueba, rechaza o descarta |
| **Casos** | `cliente_api.casos.listar` | ID, asunto, estado, prioridad, residente, vivienda, creado | Al detalle del caso (`casos:detalle`) |
| **Citas** | Nada: el módulo no existe (HU-31) | — | Estado vacío que lo dice |

- Cada pestaña muestra cuántas tiene pendientes. Los filtros rápidos (`?ver=`) y el orden de los casos (`?orden=`) son enlaces, y cada pestaña tiene un formulario `GET` de filtros (`estado`, `prioridad` o `area` y `vivienda`, residente y fechas) que viaja en la URL y valida la API: la pantalla no carga JavaScript. Con un estado elegido, «Pendientes / Todas» desaparece. Las zonas y viviendas del selector salen de las filas sin filtrar.
- Reservas no tiene prioridad: va primero la que más lleva esperando. Casos va por prioridad y luego antigüedad, con la vista «Por antigüedad» a un clic.
- El ID es un prefijo y los seis primeros caracteres del identificador (`RES-3C4D5E`); no es un consecutivo.
- Los nombres de los estados y sus pastillas están en `views.py` (reservas) y en `apps/casos/presentacion.py` (casos).

Quien no tiene `solicitud.bandeja_ver` no ve el dashboard. Un residente ve su historial de reservas, con el estado junto a cada solicitud (**Aceptado**, **Rechazado**, **En progreso**), la categoría del rechazo y el comentario; sus casos están en la sección **Casos**.

## Qué va aquí

- La pestaña Citas con sus filas, cuando exista el módulo (HU-31)
- La vista combinada de los tres tipos (HU-22), si el equipo la quiere
- Orden por columna

## Lo que no va

Botones de aprobar, responder de fondo, reasignar o exportar.

## Con qué se conecta

- Backend: `Admind_Backend/apps/triage/`
- `apps/citas/`, `apps/casos/`, `apps/reservas/`: el detalle de cada solicitud
- Las clases `am-pestanas`, `am-tabla`, `am-pastilla` y `am-vacio` del sistema de diseño, y `static/css/solicitudes.css`

## Referencias

Maestro §5.7 · HU-22 · R13
