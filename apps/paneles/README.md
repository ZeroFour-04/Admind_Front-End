# paneles

Alcance: transversal. Existe solo en el frontend, y sus teselas dependen de los módulos que ya estén construidos.

Las pantallas de inicio por rol, en bento grid (§6.4).

## Qué va aquí

- Inicio de Administración
- Inicio de Residente
- Panel de Vigilancia

## Reglas del bento

Rejilla de 12 columnas y cuatro tamaños de tesela, ni uno más: `4x1`, `6x1`, `6x2`, `12x1`. Máximo 6 teselas por vista. Bajo 900px colapsan a ancho completo. Lo que no cabe en una tesela es una vista propia con enlace desde el panel.

## Lo que no va

El bento fuera de estas tres vistas: no se usa en listados, bandejas, formularios ni detalles (§6.4).

## Con qué se conecta

- Backend: varias apps a la vez, según las teselas (`reservas`, `triage`, `visitantes`, `anuncios`, `notificaciones`)
- `templates/componentes/`: `Tesela`

## Pendiente

- Qué teselas lleva cada panel
