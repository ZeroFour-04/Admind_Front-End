# reglas

Alcance: Núcleo (§3.1).

Configuración de las reglas de reserva: las del conjunto (alfa) y las de cada área (beta).

## Qué va aquí

- El **tablero** de reglas: una fila por cada regla posible, con su descripción fija y lo que vale hoy o «Sin definir». Arriba las del conjunto; debajo, un bloque por área
- Formularios por tipo de regla (parámetros y vigencia). No hay editor de texto libre: el catálogo es de tipos parametrizados
- Los **días que no abre** de un área se agregan y se quitan de a uno, con su motivo; la lista completa viaja a la API
- El **día límite de pago** (desde el 10/10, HU-35): un número de 1 a 28 entre las reglas del conjunto, con `DiaLimiteDePagoForm`. No restringe por sí sola: *paz y salvo* la usa para calcular la mora
- Los nombres y las descripciones no se escriben aquí: llegan de `GET /reglas/catalogo/`

## Con qué se conecta

- Backend: `Admind_Backend/apps/reglas/`
- `apps/conjuntos/`: el paso de reglas del asistente es este mismo tablero
- `apps/areas/`: de ahí salen las áreas, con su horario y su aforo
- `apps/reservas/`: donde el residente ve el resultado de la validación

## Referencias

Maestro §5.10
