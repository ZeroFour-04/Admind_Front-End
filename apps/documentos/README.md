# documentos

Alcance: Comprometido (§3.2).

El repositorio de documentos del conjunto.

## Qué va aquí

- **Construido el 2026-10-25 (HU-33, rama `feat/documentos-por-tipo`, sin commit):** `/documentos/` con una tarjeta por tipo (reglamento y manual de convivencia): nombre, peso, quién lo subió y «Descargar», o «Sin cargar». Con `documento.subir`, «Subir versión nueva» en cada tarjeta; con `documento.descargar`, «Versiones» (`/documentos/<tipo>/versiones/`, con la vigente y las archivadas). El ítem «Documentos» del lateral lo ve todo rol con `documento.ver`
- El PDF pasa por este servidor: el navegador pide `/documentos/<tipo>/archivo/` y el front lo trae de la API con el token. Un tipo desconocido es 404
- El asistente de creación sigue subiendo el reglamento con `subir_reglamento` (`apps/conjuntos/`)

## Con qué se conecta

- Backend: `Admind_Backend/apps/documentos/`. La descarga pasa por su endpoint validado; aquí nunca hay un enlace directo al archivo

## Referencias

Maestro §5.4
