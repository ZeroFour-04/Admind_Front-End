# visitantes

Alcance: Comprometido (§3.2).

La minuta de portería. La usa Vigilancia en turnos largos, de noche y en equipos viejos: pocos campos y un solo botón.

## Qué va aquí

- Registrar entrada de un visitante, con el parqueadero de visitantes si entra con vehículo (HU-28): el selector ofrece solo los que la API dice libres ahora, y si no hay, la pantalla lo dice y la visita se registra sin parqueadero. Si el puesto se ocupó mientras tanto, el formulario lo explica y conserva lo escrito
- Registrar la salida: en cada visita sin salida, «Registrar salida» abre, sin JavaScript, la confirmación con el nombre, la placa y el parqueadero que se libera. Solo Vigilancia la ve
- La tabla trae las columnas «Parqueadero» y «Salida». `static/js/visitantes.js` oculta, desactiva y limpia el selector de parqueadero junto con la placa y el tipo cuando no hay vehículo
- Pendiente: listado de ocupaciones abiertas de más de N horas

## Con qué se conecta

- Backend: `Admind_Backend/apps/visitantes/`
- `apps/paneles/`: el panel de Vigilancia enlaza aquí

## Referencias

Maestro §5.6, §11.6 · README de `design-system/` (quién la usa)
