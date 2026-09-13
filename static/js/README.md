# js

Comportamiento en el navegador con Alpine.js. Solo lo que no se resuelve con HTML y una recarga.

## Qué va aquí

- La **cuenta regresiva** del bloqueo de 3 minutos, en cifras tabulares (§5.1)
- La liberación del bloqueo al salir del formulario
- Abrir y cerrar el modal de confirmación
- `vendor/`: Alpine.js autoalojado

## Lo que no va

Decidir si una franja está libre o si un bloqueo venció. Eso lo decide la API; la cuenta regresiva solo lo muestra.

## Con qué se conecta

- `templates/componentes/`: los componentes con comportamiento
- `apps/reservas/` y `apps/citas/`: las pantallas con bloqueo y confirmación
