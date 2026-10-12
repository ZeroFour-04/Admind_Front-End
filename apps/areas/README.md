# areas

Alcance: Núcleo (§3.1).

El catálogo de zonas comunes del conjunto.

## Qué va aquí

- Listado y edición de áreas, identificadas por nombre
- **El modo de uso** se elige al crear (con reserva o con ingreso) y no cambia: al editar se lee, y la API rechaza cambiarlo. Cada modo pide su campo, rotulado en el formulario: la duración de la franja (mínimo 2 horas) solo con reserva, y la permanencia máxima (de 15 a 1 440 minutos) solo con ingreso
- La tabla dice «Con reserva» o «Con ingreso» en su columna «Cómo se usa». El formulario y la tabla también los usa el paso de áreas del asistente
- El aforo máximo de cada área es obligatorio
- Administración puede guardar las reglas de renta de cada zona; se precargan en el formulario al revisar y aceptar una solicitud de reserva
- Administración, Secretaría y Superusuario pueden abrir las solicitudes de cada área
- Plantilla de condiciones del alquiler por área

## Con qué se conecta

- Backend: `Admind_Backend/apps/areas/`
- `apps/conjuntos/`: es un paso del asistente de creación

## Referencias

Maestro §3.1, §5.1
