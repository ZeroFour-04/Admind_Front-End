# conjuntos

Alcance: Núcleo (§3.1).

Las pantallas del conjunto y del conjunto activo.

## Qué va aquí

- **Asistente de creación** (solo Superusuario), paso a paso hasta que el conjunto queda operativo
- **Selector de conjunto activo** (HU-26), para quien pertenece a varios
- Datos básicos del conjunto
- En el bloque «Datos básicos» del resumen, el Superusuario ve «Eliminar conjunto»; al pulsarlo, un diálogo muestra el nombre y ofrece «Sí, eliminar» o «No». Al confirmar, vuelve al selector y el conjunto deja de aparecer para los demás
- **Color y logo** (HU-21), en `/conjuntos/identidad/`. El logo se ve en la barra, en el selector y en el resumen; sin logo, solo el nombre
- `/conjuntos/logo/<huella>/`: este servidor pide la imagen a la API con el token de la sesión y se la pasa al navegador. Como la URL lleva la huella, la imagen de una URL nunca cambia y el navegador la guarda

## Con qué se conecta

- Backend: `Admind_Backend/apps/conjuntos/`
- `templates/componentes/`: la barra superior muestra el conjunto activo por su nombre
- `apps/areas/` y `apps/reglas/`: pasos del asistente

## Referencias

Maestro §3.1, §6.3 · HU-03, HU-21, HU-26

## Pendiente

- El maestro todavía tiene el logo como Condicional (§3.3) y el acento por conjunto como aplazado (§6.3). Desde el 2026-09-22 los dos están construidos, con los ocho acentos del catálogo
