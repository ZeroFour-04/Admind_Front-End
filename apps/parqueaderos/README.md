# parqueaderos

Alcance: Comprometido (§3.2).

Parqueaderos del conjunto y su asignación a apartamentos.

## Qué va aquí

- **Construido el 2026-10-10 (HU-28):** la pantalla `/parqueaderos/` con la tabla (código, tipo, accesible, notas y una pastilla con texto: «Libre», «Ocupado» o, en los de residentes, «Sin asignar») y, con `parqueadero.gestionar`, el formulario para crear y «Retirar» con la confirmación que nombra el código, sin JavaScript. Con solo `parqueadero.ver` se ve la tabla sin formulario ni botones; sin ninguno de los dos, vuelve al inicio. El ítem «Parqueaderos» del lateral está en `_enlaces_gestion.html`
- El 409 de «ocupado» llega de la API y se muestra arriba de la tabla
- **Construido el 2026-10-25 (HU-34, rama `feat/parqueaderos-asignacion`, sin commit):** en las filas de residentes, y solo con `parqueadero.asignar`, «Asignar» o «Reasignar» (`/parqueaderos/<id>/asignar/`, con el selector de viviendas), «Historial» (`…/historial/`) y «Liberar» (con confirmación); la pastilla dice «Asignado a …» o «Sin asignar». Encima de la tabla, el tope de la regla `PARQUEADEROS_POR_VIVIENDA` o que no hay. Las filas de visitantes no tienen ningún botón de asignar. El formulario de crear pide el vehículo
- «Mi parqueadero» (`/parqueaderos/mios/`): los puestos vigentes de la vivienda del residente, sin botones; está en su lateral y a ella llega el residente que abre `/parqueaderos/`
- No hay ninguna pantalla que quite un puesto por mora ni como sanción

## Con qué se conecta

- Backend: `Admind_Backend/apps/parqueaderos/`
- `apps/visitantes/`: los de visitantes se manejan desde la minuta

## Referencias

Maestro §5.6
