# tests

Pruebas del servidor web. Se llama `tests` y no `pruebas` para no confundirla con la rama `pruebas`.

## Qué va aquí

- Pruebas de vistas con `pytest` + `pytest-django`: sin sesión redirige al ingreso, la vista muestra lo que la API devuelve, un 404 se muestra como "No encontrado"
- La **Definition of Done visual** (§6.6) como revisión por pantalla: contraste 4.5:1, foco visible con `Tab`, áreas de 44×44px, 200 % de zoom y 360px de ancho, `label` en todo campo

## Con qué se conecta

- `apps/` y `cliente_api/`. Para probar una vista sin el backend corriendo, la respuesta de la API se simula

## Cómo se corren

Desde la carpeta del proyecto, con el entorno activado y el `.env` en su sitio:

```bash
python -m pytest -q
```

No hace falta que la API esté encendida: cada prueba simula la respuesta que necesita. `test_acentos.py` lee `design-system/tokens/` y comprueba el contraste de los ocho acentos (HU-21).
