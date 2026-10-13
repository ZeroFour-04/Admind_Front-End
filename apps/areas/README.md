# areas

Alcance: Núcleo (§3.1).

El catálogo de zonas comunes del conjunto.

## Qué va aquí

- Listado y edición de áreas, identificadas por nombre
- **El modo de uso** se elige al crear (con reserva o con ingreso) y se puede cambiar al editar. Cada modo pide su campo, rotulado en el formulario: la duración de la franja (mínimo 2 horas) solo con reserva, y la permanencia máxima (de 15 a 1 440 minutos) solo con ingreso. El formulario manda solo el campo del modo elegido
- **Al cambiar el modo**, la lista muestra una vez lo que quedó del anterior, según lo que responde la API en `cambio_de_modo`: las reservas apartadas o reservadas que siguen válidas (al pasar a ingreso), quién sigue adentro (al pasar a reserva) y las reglas del área que se retiraron. Viaja en la sesión con `CLAVE_CAMBIO_DE_MODO`
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
