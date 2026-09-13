# componentes

Los componentes del sistema de diseño como fragmentos de plantilla de Django. En Claude Design están escritos en React; aquí se reescriben sobre las mismas clases de `design-system/tokens/componentes.css`.

## Qué va aquí

El inventario del sistema de diseño, ni uno más: `Boton`, `Campo`, `Pastilla`, `EstadoVacio`, `Modal`, `Tabla`, `Tesela`, `BarraSuperior`, `Lateral` y `Pestanas`.

La **confirmación de contenido** del maestro (§5.1) no es un componente nuevo: es un uso de `Modal`. Un componente, tres usos: solicitud de reserva, agendamiento de cita y aceptación de alternativa.

## Con qué se conecta

- `design-system/`: las clases, los estados y la voz
- `static/js/`: los que tienen comportamiento, como el modal
- `apps/`: todas las pantallas los usan

## Reglas

- Acción y estado no comparten forma: nunca un botón de fondo suave, nunca una pastilla de relleno sólido (§6.1)
- Ningún estado se comunica solo con color: siempre hay texto (§6.6)
- Toda área táctil mide al menos 44×44px (§6.6)
- Todo campo con `label` asociado; el `placeholder` no hace de etiqueta (§6.6)

## Pendiente

- Los componentes en React y los `ui_kits/` siguen en Claude Design, sin importar (README de `design-system/`)
