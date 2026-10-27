# citas

Alcance: Comprometido (§3.2).

Citas con el administrador.

## Qué va aquí

- Configurar el horario semanal de atención: lunes a viernes, un rango de días o un horario distinto por día
- Marcar un intervalo opcional de almuerzo o descanso, dentro de las horas de atención
- Si ya existe un horario, mostrar su resumen por día y abrir el formulario completo con «Editar horario»
- Residentes consultan el horario semanal, eligen una fecha del calendario mensual y ven franjas consecutivas de dos horas que excluyen el descanso
- Agendar una única cita futura por residente, con confirmación visible del día y la hora antes de enviar; no hay límite adicional de anticipación
- Administración consulta las citas agendadas desde la pestaña Citas de Solicitudes
- Horario de atención del administrador y aviso de las citas que quedan fuera al cambiarlo
- Aceptar una de las tres alternativas, también con confirmación de contenido

## Con qué se conecta

- Backend: `Admind_Backend/apps/citas/`
- API: `/citas/horario/`, `/citas/agenda/` y `/citas/bandeja/`
- La agenda del residente reutiliza el calendario y las pastillas visuales de `apps/reservas/`
- `apps/triage/`: la bandeja donde llegan

## Pendiente

- Cambios del horario que afecten citas ya agendadas, cancelaciones explicadas, alternativas y notificaciones
- Gestión de las citas (aceptar, rechazar, cancelar o reprogramar)

## Referencias

Maestro §5.1, §5.9 · HU-31
