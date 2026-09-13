# triage

Alcance: Comprometido (§3.2).

La bandeja de solicitudes. La usa Secretaría y, si no hay secretaría, el administrador.

## Qué va aquí

- Pestañas de Citas, Casos y Eventos, más la vista combinada, con la **antigüedad siempre visible**
- La vista por antigüedad pura, a un clic
- Cambiar prioridad (`URGENTE` pide justificación). En Eventos el control no existe
- Rechazo formal con causal de lista cerrada
- Enlace al detalle de cada solicitud en su módulo, donde decide el administrador

## Lo que no va

Botones de aprobar, responder de fondo, reasignar o exportar.

## Con qué se conecta

- Backend: `Admind_Backend/apps/triage/`
- `apps/citas/`, `apps/casos/`, `apps/reservas/`: el detalle de cada solicitud
- `templates/componentes/`: `Pestanas`, `Tabla`, `Pastilla`, `EstadoVacio`

## Referencias

Maestro §5.7 · HU-22 · R13
