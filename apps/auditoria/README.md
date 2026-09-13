# auditoria

Alcance: Núcleo (§3.1).

Consulta del registro de auditoría. Solo lectura: desde la interfaz no hay forma de cambiarlo.

## Qué va aquí

- Consulta con `auditoria.ver` (Administración, Consejo)
- Auditoría técnica con `auditoria_tecnica.ver` (Superusuario)
- Los registros anulados se ven tachados, con su motivo a la vista

## Con qué se conecta

- Backend: `Admind_Backend/apps/auditoria/`
- `templates/componentes/`: `Tabla`, `Pestanas`

## Referencias

Maestro §5.3, §5.11

## Condicional

El Registro de actividades (§3.3) sería otra vista sobre los mismos datos.
