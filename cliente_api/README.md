# cliente_api

El único lugar del frontend que sabe que existe `Admind_Backend`. Ninguna vista arma URLs de la API por su cuenta.

## Qué va aquí

- Las llamadas HTTP a la API, agrupadas por módulo
- La traducción de las respuestas de error a lo que la vista muestra. Un 404 se muestra como "No encontrado", sin más detalle (§5.4)
- La identidad del usuario en cada llamada

## Lo que no va

`conjunto_id` en ninguna petición. El conjunto activo lo resuelve la API desde la sesión (§5.4).

## Con qué se conecta

- `apps/`: todas las vistas piden datos por aquí
- `config/`: de ahí sale la dirección de la API
- Backend: los endpoints de DRF en `Admind_Backend/apps/`

## Pendiente

- Cómo se autentica este servidor ante la API en nombre del usuario, con sesión o con token (§12.7 b). Es la decisión que más afecta a esta carpeta
