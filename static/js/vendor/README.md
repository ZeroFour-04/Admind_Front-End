# vendor

Librerías de terceros servidas desde este mismo servidor. Por ahora, solo Alpine.js.

## Por qué no desde un CDN

Por la misma razón que las tipografías (§6.2): cargar un archivo desde un tercero le entrega la IP de cada residente a ese tercero, y ese tratamiento no está en la autorización de la Ley 1581.

## Qué hay aquí

| Archivo | Librería | Versión | Origen | SHA-256 |
|---|---|---|---|---|
| `alpine.min.js` | Alpine.js | 3.17.4 | `alpinejs/dist/cdn.min.js` de npm, descargado el 2026-09-27 | `232519394c6c8fdba6f362b1d9da16106db513cdbf899011f00daab4051df31c` |

## Con qué se conecta

- `templates/base/base.html`: trae el bloque `{% block scripts %}`. Solo las pantallas que usan Alpine lo cargan ahí, con `defer`; las demás no llevan JavaScript
- Hoy lo usa la solicitud de reserva (HU-11 y HU-12): la cuenta regresiva y el panel de confirmación
