# ingresos

Alcance: Núcleo (§3.1). Sin historia todavía.

Las pantallas del ingreso a zonas con aforo: Vigilancia registra a quien entra y Administración consulta el historial. Quién puede entrar, cuántos caben y cuándo se cumple el tiempo lo decide la API; aquí solo se muestra y se pide.

## Qué va aquí

- `lista` (`/ingresos/`), una sola pantalla que decide qué mostrar con el **permiso**, no con el nombre del rol:
  - `ingreso.registrar` → «Ingreso a zonas», en este orden: cupos por zona, registrar una entrada, «Adentro ahora» con «Registrar salida» y «Se les cumplió el tiempo hoy»
  - `ingreso.ver_historico` → «Ingresos»: el historial con filtro por zona y por día, sin formulario
  - Sin ninguno de los dos, vuelve al inicio
- **Registrar es en dos pasos y sin JavaScript** (`registrar`): buscar (zona, documento y acompañantes) y confirmar (nombre y vivienda a la vista; si el residente vive en dos viviendas, el vigilante elige a nombre de cuál entra). Un registro rechazado muestra **todos** los motivos y conserva lo escrito
- `salida`: «Registrar salida» llama a la API y vuelve a la pantalla; un 409 de «ya salió» se muestra con su mensaje
- El **aviso de finalidad** va junto al formulario. Su texto sale de la verificación legal ([abiertas] 12.10 b) y todavía no llega: `AVISO_DE_FINALIDAD` en `views.py` dice que está pendiente y se reemplaza ahí
- El documento viaja por `POST`, nunca en la URL, y el front no lo guarda: sigue en un campo oculto solo mientras dura el segundo paso
- Los cupos se refrescan al recargar, con el enlace «Actualizar»

## Con qué se conecta

- `cliente_api/ingresos.py`: las cinco llamadas
- `apps/reservas/`: la fila de cada zona (`fila_de_zona`) es la misma que usa «Zonas comunes»
- `templates/componentes/lateral.html`: «Ingreso a zonas» o «Ingresos», según el permiso
- Backend: `Admind_Backend/apps/ingresos/`

## Referencias

`05_Modulos/ingresos.md` y `07_Planes/hechos/Plan_Zonas_Con_Ingreso.md` de la documentación.
