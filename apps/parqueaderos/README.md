# parqueaderos

Alcance: Comprometido (§3.2).

Parqueaderos del conjunto y su asignación a apartamentos.

## Qué va aquí

- **Construido el 2026-10-10 (HU-28):** la pantalla `/parqueaderos/` con la tabla (código, tipo, accesible, notas y una pastilla con texto: «Libre», «Ocupado» o, en los de residentes, «Sin asignar») y, con `parqueadero.gestionar`, el formulario para crear y «Retirar» con la confirmación que nombra el código, sin JavaScript. Con solo `parqueadero.ver` se ve la tabla sin formulario ni botones; sin ninguno de los dos, vuelve al inicio. El ítem «Parqueaderos» del lateral está en `_enlaces_gestion.html`
- El 409 de «ocupado» llega de la API y se muestra arriba de la tabla
- Pendiente de HU-34: asignar y cerrar la asignación a una unidad. En el selector solo aparecerán los de tipo `residentes`

## Con qué se conecta

- Backend: `Admind_Backend/apps/parqueaderos/`
- `apps/visitantes/`: los de visitantes se manejan desde la minuta

## Referencias

Maestro §5.6
