# Admind_Front-End

Servidor web de AdMind: plantillas de Django, CSS propio sobre las variables del sistema de diseño y Alpine.js para lo interactivo. Sin Tailwind, sin Bootstrap, sin framework de componentes (maestro §12.1, Definición visual v1).

> [!NOTE]
> Por ahora este repositorio solo tiene el sistema de diseño y carpetas con un `README.md` en cada una, que dice qué va a vivir ahí y con qué se conecta. Todavía no hay código.

> [!WARNING]
> Esta estructura supone **plantillas de Django + Alpine**. Se armó así el 2026-09-13, pero en el maestro la §12.1 sigue abierta. Si el equipo cierra por otro camino, esta estructura se rehace.

## Cómo se conecta con el backend

Son dos servidores Python. Este renderiza HTML; `Admind_Backend` es la API y el único que toca PostgreSQL. Las vistas de aquí piden los datos por HTTP, siempre a través de `cliente_api/`.

## Mapa

| Carpeta | Qué va |
|---|---|
| `design-system/` | Sistema de diseño importado de Claude Design. **Ya existe; no se mueve ni se edita a mano** |
| `config/` | Proyecto Django del servidor web |
| `cliente_api/` | El único punto que habla con la API del backend |
| `apps/` | Una app por módulo: vistas y plantillas de cada pantalla |
| `templates/` | Plantillas compartidas: estructura base y componentes |
| `static/` | CSS propio y JavaScript con Alpine |
| `tests/` | Pruebas de vistas y Definition of Done visual |

## Reglas que aplican a todas las carpetas

- Ningún hex fuera de `design-system/tokens/paleta.css` (§6.6)
- Un solo acento por ahora; no hay `data-acento` (§6.3)
- Tipografías y librerías autoalojadas, nunca desde un CDN (§6.2)
- La interfaz nunca envía `conjunto_id` (§5.4)
- Textos en español de Colombia, con la voz de §6.5 y del README de `design-system/`

## Pendiente

- Cómo viaja la sesión del usuario desde este servidor hasta la API (§12.7 b)
- ¿Manda `design-system/` o el §6 del maestro? Fuentes, radios y ruta de los tokens (§6.3)
