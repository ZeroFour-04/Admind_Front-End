# infracciones

Alcance: Comprometido (§3.2).

Registro, consulta y cierre de infracciones.

## Qué hay hoy

**Construido el 2026-10-25 (HU-30, rama `feat/infracciones-registro`, sin commit):** `/infracciones/` (lista: los anulados tachados y con su motivo), `/infracciones/nueva/[?caso=<id>]` (formulario: vivienda, fecha y hecho; desde un caso sugiere las viviendas del autor, pero se elige a mano) y `/infracciones/<id>/` (detalle, «Cerrar registro» con `infraccion.cerrar` y «Anular» solo con `infraccion.anular`). El aviso de R11 va en un recuadro fijo en las tres pantallas (`textos.py`). El ítem «Infracciones» del lateral lo ve quien tenga `infraccion.ver`. En el detalle de un caso, con `infraccion.registrar`, «Registrar infracción».

## Qué va aquí

- Registrar una infracción, con la fecha de notificación obligatoria
- Consultar y cerrar
- El aviso, en el propio registro, de que no es prueba de debido proceso (R11)

## Lo que no va

Campos de sanción, multa o restricción (§4.2).

## Con qué se conecta

- Backend: `Admind_Backend/apps/infracciones/`

## Referencias

Maestro §4.2, §5.8 · R11
