# pagos

Alcance: Comprometido (§3.2).

Reporte y confirmación del pago de administración.

## Qué va aquí

- **Construido el 2026-10-10 (HU-35):** `/pagos/administracion/`, una sola ruta que decide la pantalla por los permisos de la sesión (la API es la que niega). Con `pago.ver`: la tabla del mes en letras, con buscador (un formulario `GET`, filtra el servidor), el estado en una pastilla con texto, el enlace al comprobante y, con `pago.confirmar`, el check de cada vivienda. Con solo `pago.reportar`: «Mis pagos», con los últimos 6 meses de cada vivienda y el formulario para subir el comprobante
- El aviso «AdMind no verifica el dinero: el pago lo confirma una persona de la administración» está escrito una sola vez, en `views.py` (`AVISO_DEL_DINERO`), y las dos pantallas lo reciben por contexto
- El check envía su formulario al cambiar (Alpine, cargado solo si hay `pago.confirmar`); sin JavaScript hay un botón «Guardar»
- La página nunca imprime una cédula. `/pagos/administracion/comprobantes/<id>/` entrega el archivo que pide a la API: el front no lo guarda

## Con qué se conecta

- Backend: `Admind_Backend/apps/pagos/`
- `cliente_api/pagos.py`: una función por endpoint
- `apps/reglas/`: el formulario del *día límite de pago* es del tablero de reglas, no de esta app

## Referencias

Maestro §3.2, §3.4
