# reservas

Alcance: Núcleo (§3.1).

Las pantallas del flujo de reserva. Es la parte de la interfaz que más se sustenta.

## Qué va aquí

- **«Zonas comunes» abre con una tabla de todas las zonas**: nombre, cómo se usa, horario y cupos de este momento (`GET /ingresos/zonas/`). La pastilla dice el estado: «Abierta», «Cerrada», «Sin cupo» o «En mantenimiento». Una zona con ingreso no ofrece «Reservar». Si la API de ingresos no responde, la tabla sale sin cupos y con su aviso, y reservar sigue funcionando
- Calendario con franjas libres y ocupadas. El selector lista solo las áreas con reserva
- Las franjas apartadas y reservadas se distinguen en rojo en el calendario
- `Reservar`: toma el bloqueo y muestra la **cuenta regresiva de 3 minutos**. Salir del formulario libera la franja de inmediato
- Formulario y **confirmación de contenido**, con el día de la semana en letras
- Aviso de última oportunidad cuando el residente ya dejó vencer esa franja una vez (R9)
- Mis reservas: ver y cancelar
- Bandeja de solicitudes por zona común para administración, secretaría y superusuario; permite aceptar o rechazar con motivo
- Suscripción a la campana de una franja ocupada
- Detalle para el administrador: aprobar escribiendo las condiciones, que llegan precargadas desde el área, o rechazar con categoría
- La frase de que el dinero lo valida una persona, visible en la interfaz (§5.1)

## Estados como pastillas

En trámite → `tramite` · Confirmada → `ok` · Rechazada → `error` · Expirada y Anulada → `neutro` (§6.2).

## Con qué se conecta

- Backend: `Admind_Backend/apps/reservas/`
- `static/js/`: la cuenta regresiva y la liberación al salir
- `templates/componentes/`: `Modal` (confirmación), `Pastilla`, `Boton`
- `apps/triage/`: la bandeja donde llegan las solicitudes

## Referencias

Maestro §5.1, §6.2 · HU-11 · R9
