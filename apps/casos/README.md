# casos

Alcance: Comprometido (§3.2).

Los casos de los residentes.

## Qué va aquí

- Abrir un caso, casi siempre desde el celular
- Ver los propios y su estado
- Crear un caso con título o motivo, descripción y una imagen opcional
- Responder un caso (Administración)

El residente crea el caso desde la sección **Casos** (`/casos/`) y ahí lo consulta: su estado, la respuesta de la administración o la razón del rechazo. No hace ninguna otra operación sobre él.

Gestión entra por la pestaña **Casos** del dashboard (`apps/triage`); `/casos/` la redirige allá. Cada fila abre el detalle (`/casos/<id>/`), que muestra el caso y, según el estado y los permisos de la sesión, sus acciones:

| Acción | Quién la ve | Ruta del front |
|---|---|---|
| Tomar el caso | `caso.gestionar` o `caso.responder`, si está «Por revisar» | `/casos/<id>/tomar/` |
| Cambiar la prioridad | `solicitud.priorizar`, si está abierto | `/casos/<id>/prioridad/` |
| Redirigir al administrador, Descartar | `caso.gestionar` (Secretaría), antes de redirigirlo | `/casos/<id>/redirigir/`, `/descartar/` |
| Responder y resolver, Rechazar | `caso.responder` (Administración), si está abierto | `/casos/<id>/responder/`, `/rechazar/` |

Las seis pasan por una sola vista (`views.gestionar`), que manda los campos a la API y vuelve al detalle. Ocultar un botón no es lo que impide la acción: lo impide la API. Si la API la rechaza, la pantalla dice por qué y conserva lo escrito. Los nombres de estados y prioridades están en `presentacion.py`.

## Con qué se conecta

- Backend: `Admind_Backend/apps/casos/`
- `apps/triage/`: la bandeja donde llegan

## Referencias

Maestro §5.7 · HU-29
