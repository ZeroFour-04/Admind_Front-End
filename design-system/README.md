# AdMind · Sistema de diseño

> **Nota de importación.** Este directorio se importó desde el proyecto de Claude Design
> «AdMind Design System» conservando su estructura original, para que una
> re-sincronización futura calce sin mover rutas.
>
> **Importado:** `styles.css`, `tokens/` completo, `assets/fonts/` y `guidelines/muestrario.html`.
> **Todavía en Claude Design:** los diez componentes en React (`components/`), el kit de
> aplicación navegable (`ui_kits/admind/`), las demás tarjetas de `guidelines/`, las
> exploraciones de rampa y `SKILL.md`. Se dejaron fuera a propósito mientras el front no
> tenga framework definido. El índice de más abajo los menciona porque es el documento
> original del sistema.

AdMind es una aplicación web para administrar conjuntos residenciales en Colombia bajo el régimen de propiedad horizontal (Ley 675 de 2001). No es un producto de consumo ni una landing: es una herramienta de trabajo que se usa todos los días, en español de Colombia, implementada con HTML y CSS propios más variables CSS — sin Tailwind, sin Bootstrap, sin librería de componentes.

## Quién la usa

- **Administrador y consejo de administración.** Pasan el día en tablas densas y en la bandeja de solicitudes. Rango de edad amplio, muchos de más de 50 años, casi siempre en computador de escritorio. Es la razón por la que ningún tamaño de texto baja de 13px y por la que los ítems de navegación miden 44px de alto aunque sea escritorio.
- **Residentes.** Entran poco y desde el celular: una reserva del salón comunal, un caso nuevo, el estado de algo. Alfabetización digital muy variable. Es la razón por la que el flujo de reserva tiene un resumen permanente y un modal que repite en palabras lo que va a pasar.
- **Vigilantes de portería.** Registran visitantes en turnos de doce horas, incluidas las nocturnas, en un equipo viejo. Es la razón por la que la minuta tiene tres campos y un solo botón.

## Fuentes de esta entrega

- **Tipografías provistas por el cliente** (archivos originales en `uploads/`): Archivo y Inter, variables, con sus itálicas. Copiadas a `assets/fonts/` y autoalojadas.
- **Brief escrito del cliente**, entregado en el chat: restricciones de color, tipografía, las dos capas, la regla de forma entre acción y estado, accesibilidad, voz de los textos y formato de entrega.
- **No hubo** repositorio de código, archivo de Figma, deck ni logotipo. No hay marca gráfica: donde iría un logo va el nombre en Archivo 700. Nada en este sistema fue reconstruido de memoria ni inventado como relleno.

## Índice

| Archivo | Qué es |
|---|---|
| `styles.css` | Punto de entrada. Solo `@import`: es el único archivo que enlaza un proyecto consumidor |
| `tokens/paleta.css` | Paleta cruda. La única capa donde vive un hex |
| `tokens/colores.css` | Color semántico con el ratio de contraste anotado par por par |
| `tokens/tipografia.css` | Familias, la frontera entre ellas, cuatro pesos, seis tamaños |
| `tokens/espaciado.css` | Escala de 4px, tres radios, la única sombra, transición |
| `tokens/fuentes.css` | `@font-face` de Archivo e Inter autoalojadas |
| `tokens/base.css` | Reset corto y valores por defecto del documento |
| `tokens/componentes.css` | CSS plano de los componentes, sobre variables. Transplantable tal cual |
| `guidelines/muestrario.html` | Muestrario con todos los estados visibles a la vez |
| `guidelines/*.html` | Tarjetas de fundamentos: color, tipo, espacio, marca |
| `components/` | Los diez componentes en React |
| `ui_kits/admind/` | Aplicación de administración navegable, cuatro vistas |
| `SKILL.md` | Envoltura para usar este sistema como skill descargable |

## Componentes

Ninguna fuente externa definía un inventario, así que el inventario es exactamente el que pide el brief — ni un componente más:

| Componente | Grupo | Para qué |
|---|---|---|
| `Boton` | `components/acciones/` | Acción: primario, secundario, peligro, texto |
| `Campo` | `components/formularios/` | Entrada con etiqueta asociada: input, select, textarea |
| `Pastilla` | `components/estado/` | Estado en fondo suave y radio total, cinco tonos fijos |
| `EstadoVacio` | `components/estado/` | Lista sin filas todavía, con la acción que corresponde |
| `Modal` | `components/estado/` | Confirmación. Lo único que flota y lo único con sombra |
| `Tabla` | `components/datos/` | Listado denso con encabezado, hover y columnas numéricas |
| `Tesela` | `components/datos/` | Cifra grande de panel |
| `BarraSuperior` | `components/navegacion/` | Barra con la franja identificadora del conjunto activo |
| `Lateral` | `components/navegacion/` | Navegación de escritorio con ítem activo |
| `Pestanas` | `components/navegacion/` | Filtro de una misma lista por estado |

### Adiciones intencionales

- **`Lateral` y `Pestanas`** no están enumerados como componentes en el brief, pero el brief sí exige que el acento aparezca en «el ítem activo de la navegación lateral y la pestaña seleccionada». Sin estos dos componentes ese sitio del acento no tendría dónde existir y la pantalla de validación no se podría armar.
- No hay `Icono`, `Avatar`, `Toast`, `Tooltip` ni `Switch`. Ninguno hace falta todavía y un componente que nadie pidió es un componente en el que alguien va a confiar.

## Las dos decisiones que hay que poder defender

### El verde

Se propusieron dos rampas (`explorations/rampa-a-pino.html` y `explorations/rampa-b-laurel.html`) y el cliente eligió la A.

- **A · Pino institucional** — `#0E7C66` de referencia, bajado de saturación y de luminosidad hasta `#0E6B5A`. Tiene un punto de azul, que es justo lo que lo aleja del verde de producto orgánico y lo acerca a servicio público. Conserva el punto de partida del cliente, así que no obliga a rehacer nada de lo que ya existiera.
- **B · Laurel** — verde de hoja sin azul, más notarial y patrimonial, más lejos del verde-agua de bancos y fintech. Se descartó por dos razones: al bajarle saturación tiende a lo militar, y al ser un verde más literal pelea de frente con el verde del estado «Confirmada».

La rampa elegida son cuatro pasos y nada más: `--acento-50`, `--acento-600`, `--acento-700`, `--acento-900`.

### La frontera tipográfica

Se acepta la frontera propuesta por el cliente, con la cifra grande en Archivo confirmada por él después de plantearle la duda: Archivo variable no trae figuras tabulares reales, así que la cifra usa `font-variant-numeric: tabular-nums` y el motor sintetiza el ancho fijo. Se ve bien en las teselas de dos y tres dígitos; si aparece una tesela de siete dígitos que cambie mucho (por ejemplo un contador de pesos en vivo), es el punto donde habría que revisar.

---

# CONTENT FUNDAMENTALS

Los textos son parte del diseño, no un relleno posterior.

**Idioma y tratamiento.** Español de Colombia, siempre. Segunda persona del singular sin voseo: «Corrígelo y vuelve a guardar», «Cambia la prioridad». La aplicación nunca habla de sí misma en primera persona y nunca dice «nosotros».

**Casing.** Mayúscula inicial de frase en absolutamente todo: botones, etiquetas, encabezados de tabla, títulos de grupo del lateral, pastillas. No hay versalitas ni mayúscula sostenida en ninguna parte del sistema, ni siquiera en las etiquetas de 13px.

**Botones.** Verbo activo y concreto: `Confirmar reserva`, `Guardar cambios`, `Registrar entrada`, `Quitar filtros`. Nunca `Enviar`, `Aceptar` ni `Continuar`. Sin flechas `→` pegadas al texto.

**Continuidad de la acción.** La acción conserva su nombre en todo el flujo. El botón dice `Confirmar reserva`, el modal se titula «¿Confirmar la reserva del salón comunal?» y el resultado dice «Reserva confirmada». El participio es la señal de que ya pasó.

**Errores.** No se disculpan y no son vagos: dicen qué pasó y qué hacer. «El documento debe tener entre 6 y 12 dígitos. Corrígelo y vuelve a guardar.» Nunca «Lo sentimos, algo salió mal».

**Estados vacíos.** Son una invitación, no un aviso. Enuncian la ausencia y explican de dónde va a venir el contenido: «Todavía no hay solicitudes en la bandeja. Cuando un residente abra un caso desde su celular, aparece aquí con su antigüedad y su prioridad.»

**Fechas y horas.** Día de la semana en letras: «Sábado 12 de septiembre, de 2:00 p. m. a 8:00 p. m.», «Al viernes 5 de septiembre». La hora de 24 horas solo se usa en la minuta de portería, donde el turno cruza la medianoche y es lo que el vigilante escribe a mano en el libro.

**Datos del dominio.** El contenido de ejemplo es real: `Torre 3 – 402`, `Salón comunal`, `En trámite · 2:41`, `Antigüedad: 6 días`, `SOL-2026-0418`, `NIT 901.245.877-3`, pesos colombianos con punto de miles y coma decimal (`$ 12.480.000`, `0,00412 %`). No hay «Lorem», ni «Usuario 1», ni cifras redondas de relleno.

**Sin emoji.** Ninguno, en ningún lugar del sistema. Tampoco caracteres unicode haciendo de icono.

**Sin decoración tipográfica.** No hay cadenas unidas con puntos medios como adorno. El punto medio aparece solo cuando une dos datos de la misma línea que se leen juntos: «Marta Ospina · propietaria», «En trámite · 2:41».

---

# VISUAL FOUNDATIONS

## Las dos capas

La interfaz tiene una **capa base fija** —el 85% de lo que se ve: fondo, tarjetas, bordes, texto— y una **capa de acento** que es el verde. El acento aparece en cuatro sitios y en ninguno más:

1. Botón de acción primaria.
2. Ítem activo de la navegación lateral y pestaña seleccionada.
3. Anillo de foco de los formularios.
4. Franja identificadora del conjunto activo.

Sobre el sitio 3: el anillo de foco es el mismo en todo elemento interactivo, también en botones y en el lateral. No es un quinto sitio, es el mismo trabajo — decir dónde está el teclado — y tener dos anillos distintos obligaría a aprender dos.

Sobre el sitio 4: la franja es **siempre** `--acento-600`, no un color por conjunto. Si cambiara de color, el verde dejaría de ser identidad y pasaría a ser dato, y el administrador que maneja seis conjuntos tendría que memorizar un código de colores. El conjunto se identifica por su nombre, que es lo que la gente lee.

## El acento nunca comunica significado

El verde de marca y el verde de «Confirmada» son colores distintos con trabajos distintos, y la colisión no se resuelve con dos verdes: se resuelve con la forma.

| | Forma | Ejemplo |
|---|---|---|
| **Acción** | Relleno sólido, radio de 4px, texto blanco, verbo activo | `Confirmar reserva` |
| **Estado** | Fondo suave, radio total, texto oscuro del mismo tono, participio | `Confirmada` |

Nunca existe un botón de fondo suave ni una pastilla de relleno sólido. Esa es la regla que le permite a alguien distinguir de un vistazo lo que puede hacer de lo que ya pasó.

## Color

Rampa de marca de cuatro pasos, escala neutra de tres superficies, dos bordes y tres niveles de texto, y cinco colores de estado fijos con fondo y texto. Todos los pares están anotados con su ratio en `tokens/colores.css`; el más bajo del sistema es `--texto-suave` sobre `--superficie-pagina`, en 4.8:1. Los cinco estados van entre 7.0:1 y 8.5:1.

Ningún componente escribe un hex: todo sale de una variable, y la única capa con hex es `tokens/paleta.css`. Los estados son ajenos a la marca a propósito — si mañana el verde cambia, la lista de estados no se toca.

Solo modo claro en esta entrega. Las variables están estructuradas en dos capas (paleta cruda y alias semántico) para que agregar modo oscuro sea duplicar el bloque de `colores.css` bajo un selector de tema y reapuntar los alias, no una reescritura.

## Tipografía

Archivo titula, Inter hace todo lo demás, y la frontera es exacta: Archivo en el título de la vista, en los títulos de tarjeta y tesela y en la cifra grande; Inter en cuerpo, tablas, botones, etiquetas, navegación, formularios y pastillas. Archivo va en ancho normal (`font-stretch: normal`): ni Narrow ni Expanded.

Cuatro pesos en total. **Archivo 700** para el título de la vista y la cifra, porque tienen que ganarle a una tabla de cuarenta filas y a 30px un 600 se lee indeciso. **Archivo 500** para títulos de tarjeta y tesela, que marcan jerarquía sin subir al nivel del título. **Inter 400** para cuerpo y celdas, la única forma de que cuarenta filas no se vean sucias. **Inter 500** para etiquetas, encabezados de tabla, botones y navegación, porque a 13px en un monitor viejo un 600 se empasta. No hay Inter 600 ni 700: el énfasis lo carga Archivo.

Seis tamaños: 40 / 30 / 20 / 16 / 14 / 13px. Ninguno baja de 13px. Texto corrido a máximo 68 caracteres por línea (`--medida-texto`), contenido a máximo 1100px.

Ambas familias van autoalojadas desde `assets/fonts/`, no desde el CDN de Google Fonts: servir una tipografía desde un tercero le entrega la IP de cada residente a ese tercero, y eso es tratamiento de datos personales que no está en la autorización de la Ley 1581. La consecuencia práctica es que se usan las variables completas con rango `100 900`, lo que además abre la puerta a afinar pesos intermedios sin pedir archivos nuevos.

Toda columna de números lleva `font-variant-numeric: tabular-nums` — unidades, documentos, horas, cantidades, antigüedad, valores en pesos — vía la clase `.am-num` o `numerica: true` en `Tabla`.

## Espaciado, radios, elevación

Escala de 4px con nueve pasos (`--e-1` a `--e-9`). Los saltos son perceptibles a propósito: la densidad de una tabla y el aire de un formulario no se calibran a ojo.

Tres radios, cada uno con su trabajo, porque el mismo radio en todo aplana la jerarquía: `--radio-control` 4px para botón, campo y casilla; `--radio-caja` 8px para tarjeta, tesela, tabla y modal; `--radio-pastilla` 999px para la pastilla de estado y nada más. El control siempre es más cerrado que el contenedor que lo aloja.

**Una sola sombra en todo el sistema.** `--sombra-flotante` existe únicamente para lo que flota sobre el contenido: modal, menú desplegable, popover. Las tarjetas, las teselas y las tablas se separan con `--borde`. Si algo lleva sombra y no flota, está mal.

## Fondos, imágenes, transparencia

Sin gradientes, sin glassmorphism, sin texturas, sin patrones repetidos, sin ilustraciones y sin imágenes: el fondo es un color plano (`--superficie-pagina`) y las superficies son planas. No hay imagen ninguna en el sistema, así que no hay «vibe» de imagen que calibrar; si algún día entran fotos —una zona común, un daño reportado— van dentro de una tarjeta con borde y `--radio-caja`, sin filtro y sin gradiente de protección.

La única transparencia del sistema son dos alfas derivadas de la tinta y del acento: el velo del modal (`--tinta-a28`) y el halo del anillo de foco (`--acento-anillo`, 32%). No hay blur en ninguna parte.

## Estados de interacción

- **Hover.** Se oscurece: el primario pasa de `--acento-600` a `--acento-700`, el peligro de su relleno a su tono más oscuro, el secundario y las filas de tabla toman `--superficie-hundida`. Nunca opacidad, nunca aclarar, nunca escalar.
- **Foco de teclado.** Visible en todo elemento interactivo. Contorno de 2px en `--acento-600` con 2px de separación; en los campos, además, borde de acento y halo de 3px.
- **Presionado.** El mismo color del hover; no hay hundimiento ni cambio de tamaño. Un botón que se encoge es un botón que se mueve debajo del dedo.
- **Deshabilitado.** Superficie hundida y texto suave, con `cursor: not-allowed`. Nunca opacidad global, que arrastra el contraste del texto por debajo del piso.
- **Fila activa de tabla.** Fondo `--superficie-hundida` en la fila completa, no solo en la celda.

## Movimiento

Solo hay movimiento que responde a una acción: abrir, cerrar, confirmar. No hay animación de entrada al cargar ni al hacer scroll, y no hay nada que se mueva por su cuenta. Una sola transición en el sistema, `--transicion` = 120ms `cubic-bezier(.2,0,.3,1)`, y se aplica a color, fondo y borde. Nada de bounce. `prefers-reduced-motion` la anula.

La cuenta regresiva de la reserva es la única excepción: cambia de valor cada segundo porque el dato cambia cada segundo. Va en cifras tabulares para que no salte de ancho.

## Accesibilidad, como piso

Texto normal a 4.5:1 mínimo y texto grande a 3:1, con el ratio anotado en el token. Ningún estado se comunica solo con color: la pastilla siempre lleva palabra y el ítem activo del lateral lleva además barra a la izquierda y `aria-current`. Área táctil mínima de 44×44px en botones, ítems de navegación, pestañas y campos. Todo campo con `label` asociado por `for`/`id`, el error asociado por `aria-describedby`, y el `placeholder` nunca hace de etiqueta. Usable a 200% de zoom y a 360px de ancho: los formularios son de una columna, las mallas colapsan a una sola y el pie del modal se apila.

---

# ICONOGRAPHY

**No hay iconografía en este sistema, y es una decisión, no una omisión.**

Las fuentes recibidas no traen ningún icono, ninguna fuente de iconos, ningún sprite y ningún SVG. No se dibujó ninguno: un icono inventado es un icono que el equipo de AdMind no reconoce y que un residente tendría que interpretar. El brief además excluye explícitamente los iconos decorativos, los emoji como iconos y las ilustraciones.

Lo que ocupa el lugar de los iconos:

- **Palabras.** El lateral lista «Solicitudes», «Minuta de portería», «Cartera» sin glifo al lado. Para una herramienta que se usa todos los días, el texto es más rápido de aprender y no se confunde entre dos íconos parecidos.
- **La pastilla de estado.** Lleva la palabra del estado, no un símbolo de check o de alerta.
- **Cantidades.** La cuenta de pendientes del lateral va como número alineado a la derecha, no como punto de color.
- **El nombre de la marca.** No hay logotipo en las fuentes recibidas, así que donde iría un logo va «AdMind» en Archivo 700. Está así en `BarraSuperior`, en `thumbnail.html` y en la tarjeta `guidelines/marca-nombre.html`.

**Si hace falta iconografía**, esta es la recomendación y la razón: un set de trazo, monocromático, de 1.5px a 20px, tomado de una librería abierta y copiado como SVG al repositorio —nunca desde un CDN de terceros, por el mismo argumento de la Ley 1581 que aplica a las tipografías—. Los iconos irían solo en tres sitios: la acción repetida de una fila de tabla, el cierre del modal y el desplegable de un menú. Nunca al lado del texto de un botón y nunca como decoración de un estado vacío. Antes de agregarlos hace falta una decisión del cliente, así que quedan fuera de esta entrega.

---

## Caveats

- **Las tipografías son las del cliente**, sin sustituciones. No hizo falta buscar equivalentes en Google Fonts.
- **No hay logo.** Si existe una marca gráfica, hace falta el archivo: el nombre en tipografía plana es un sustituto honesto, no una solución.
- **Sin modo oscuro** por decisión del brief. Las variables ya están en dos capas para agregarlo como bloque de sobrescrituras.
- **Sin vista de residente en celular.** El flujo de reserva funciona y reflowea a 360px, pero no se diseñó la navegación del residente en móvil.
