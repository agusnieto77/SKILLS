# Trampas de SIGEVA y cómo las maneja el cargador

SIGEVA es una aplicación Struts que sirve HTML en ISO-8859-1 y no tiene una API de escritura. Todo lo que sigue se verificó contra SIGEVA CONICET 14.11.x. Buena parte se documentó primero en [carga-sigeva](https://github.com/juanfraire/carga-sigeva) (Juan A. Fraire, MIT) y en [SIGEVA-JSON](https://github.com/indirivacua/SIGEVA-JSON). Si algo de esto deja de ser cierto, `verificar` debería detectarlo como cambio en el [mapa](mapa-sitio.md).

## Entrar

| Paso | Detalle |
|---|---|
| Login CAS | `/cas/login`: `input#username`, `input#password`, `button[name=submitBtn]` |
| Roles | `/intranet/index.htm`; cada rol es `redirect(<id>)` dentro de un menú colapsado (esperar `attached`, no `visible`) |
| Banco de Datos | `redirect(96)` → `/eva/indexBancoDatos.do`. Presentación/solicitud es `redirect(72)` |

SIGEVA bloquea la cuenta tras varios ingresos fallidos. El CAS a veces se cuelga después de "INGRESAR" (ni la captura carga) aunque la clave sea correcta, y a la media hora funciona: el ingreso no espera la navegación del click, espera los roles 90 s, distingue un rechazo (corta sin reintentar) de un cuelgue (espera, recarga la intranet por si igual entró y reintenta **una** vez). El servidor también se cuelga por **estado acumulado de sesión**, no por tráfico: cada corrida abre un contexto de navegador nuevo y trabaja en tandas cortas.

## Guardar no significa guardado

- SIGEVA puede volver del *Guardar* a la lista **sin error y sin haber guardado nada** (p. ej. con un PDF de más de 35 MB). Por eso cada alta se confirma buscando el registro en la lista.
- Al revés, una `LockAcquisitionException` puede aparecer **y el registro entrar igual**. Reintentar sin mirar la lista duplica.
- Con PDF grandes la página vuelve a la lista antes de terminar la subida y el registro aparece segundos después: la confirmación reintenta durante un minuto.
- Después de guardar la página sigue navegando y un `evaluate` puede caer con *Execution context was destroyed*: las lecturas esperan y reintentan.
- Los mensajes de validación usan varios verbos (*debe ingresar / seleccionar / adjuntar / especificar…*): filtrar por uno solo lee un rechazo como éxito.
- Si un rechazo vacía el archivo ("seleccione nuevamente el archivo"), se vuelve a adjuntar **una** vez, se reponen las fechas y se reintenta.

## Fechas: el datepicker pisa lo que se escribe

`fechaPublica`, `fechaReunion`, `anioPublica`, `anio`, `anioInicio`, `anioFin` son datepickers de jQuery UI. Al cerrarse escriben la fecha **seleccionada** en el widget, que sin selección es el mes actual. `fill()` cambia el texto pero no la selección: al perder el foco, el campo vuelve a hoy. Así se guardaron decenas de registros con la fecha del día y sin ningún error.

El cargador cierra los pickers, quita el foco, fija cada fecha con `datepicker('setDate', …)`, escribe también el `hidden` del mismo nombre, lo hace **al final** (cada vuelta por un buscador re-renderiza y pisa) y, después de guardar, reabre el registro y compara fecha por fecha.

## Combos y campos

- Asignar `select.value` por JavaScript no sirve: Struts no registra el cambio. Se usa `select_option` (eventos reales).
- `campo_0_0` (subárea) llega por AJAX después de elegir `campo_0`; los valores negativos de `campo_0` son encabezados deshabilitados.
- Muchos campos aparecen dos veces con el mismo `name` (visible + hidden): se escribe el visible y, en fechas, los dos.
- Los checkbox se serializan por `value`, no solo por `checked`.

## Autores y filiaciones

- `preSubmit()` arma `autorJSON` recorriendo `#autorTable>tbody>tr` y, en cada autor, las filas del `<tbody>` de su tabla anidada. Una filiación fuera de ese `<tbody>` se ve en pantalla pero no viaja.
- Las filiaciones se inyectan como inputs ocultos (`autorOrganizacionId`, `autorOrganizacionLabel`, `autorisOtraOrganizacion`…). **Solo** con un id real del catálogo: con id vacío el backend cae con `TransientPropertyValueException`. `autorisOtraOrganizacion` debe ser `true` para las "otra" dadas de alta por usuarios y `false` para las del catálogo oficial.
- El catálogo local (`catalogo`) solo conoce las instituciones de tus registros ya cargados; el oficial de SIGEVA es mucho más grande. Antes de dejar a un autor sin filiación, buscarla con `institucion`: devuelve el id (último tramo de `navegar('02565-23770-24160')`, sin ceros) y de quién depende. Con Argentina, la provincia es obligatoria (CABA figura como "Capital Federal").
- Una institución que no existe en SIGEVA se crea recién cuando se guarda un registro que la usa: hacerlo a mano una vez y volver a correr `catalogo`.
- Desde 14.11.24.5 el declarante es el autor con `autorPersonaId` = id de persona (`persona_id` en `config.json`); antes era el radio `autorSel`. El cargador marca el que exista.
- En artículos la institución es obligatoria para **cada** autor; en eventos no.
- El catálogo resuelve solo por coincidencia exacta: "Nanjing University" y "Nanjing Institute of Geology" comparten palabras y son instituciones distintas. Una filiación falsa en una declaración jurada es peor que una faltante.

## Listas

- Paginación displaytag: `d-<idTabla>-p=N`. Los ids de tabla de publicaciones son `3997137` (artículos) y `8106305` (eventos publicados); el contrato los vigila.
- Con un `d-<id>-p` en la query, SIGEVA lo copia en los enlaces de orden de **todas** las tablas de la página. Una tabla se identifica solo por su propio parámetro de orden, `d-<id>-s=`; tomar el primer `d-<id>-` hace pasar la tabla de Libros por la de Eventos. Control: los conteos del inventario deben coincidir con los del índice del Banco de Datos.
- Los títulos de la lista vienen truncados con `...`: se compara por prefijo normalizado de al menos 25 caracteres.
- En la lista de eventos, la columna *Año* es la del evento, no la de las actas.

## Modificar sin duplicar

"Modificar" no siempre edita: en muchas pantallas crea un registro con otro id y retira el anterior de la lista. El formulario del id viejo se sigue abriendo con los datos viejos, y modificarlo desde ahí deja un **duplicado**. Lo que duplica no es Modificar: es partir de un id viejo. El comando `modificar` sigue este protocolo:

1. Lee la lista **en ese momento** y exige que el título coincida con exactamente un registro.
2. Abre ese id, anota los ids de la tabla, aplica los cambios (fechas con `setDate`) y relee los valores del formulario.
3. Si el declarante no está marcado (registros viejos), marca `autorPersonaId` en la fila de su apellido: SIGEVA lo exige al modificar ("Debe seleccionar su nombre de la lista de autores").
4. Aprieta Modificar y compara los ids de la lista antes y después:
   - un id nuevo y el viejo retirado → *version-nueva*, éxito;
   - mismo id y ninguno nuevo → *edición en el lugar*, éxito;
   - el viejo **y** uno nuevo → **duplicado**: solo con `--borrar-duplicado`, y recién después de releer el nuevo y confirmar los cambios, abre la confirmación de borrado del viejo (justo antes, por el token de Struts) y verifica que desapareció;
   - más de un id nuevo, otro registro desaparecido o el registro desaparecido → corte, sin tocar nada más.
5. Relee el registro final y compara campo por campo con lo que quedó en el formulario.

Al modificar registros viejos SIGEVA también puede pedir cosas que antes no pedía (tipo de versión del adjunto, full text): el formulario vuelve con el error y no guarda nada; `modificar` lo informa como `rechazado`.

## Otras

- Full text obligatorio, hasta 35 MB, y el límite no se valida con un mensaje. Comprimir: `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/printer -o chico.pdf grande.pdf`.
- `tipoAdjunto` solo ofrece *Post print* y *Versión final*: un preprint no se puede declarar.
- Libros y partes de libro: el referato es el radio `referato` (0 no, 2 sí), no `tipoReferato`; el rol de quien declara son las casillas `isAutor`/`isEditor`/`isRevisor`. En partes de libro el ISBN, la cantidad de páginas del libro y las páginas inicial/final (si está publicado) son obligatorios aunque el mapa no los marque: el asterisco está en otra celda.
- Los compiladores de una parte de libro usan los mismos campos ocultos que los autores con prefijo `compilador` y viajan en `compiladorJSON`. Son obligatorios aunque el formulario no tenga asterisco: sin ellos el Guardar vuelve con "Debe ingresar el/los compiladores/es, el/los editor/es, el/los organizadore/es del libro".
- El libro sube el full text por un Fine Uploader (`qqfile`), que manda el archivo al servidor apenas se elige: en seco no se toca.
- Soporte electrónico exige URL o DOI.
- La revista se puede dar de alta como "otra" solo con ISSN, y ese bloque aparece recién en la pantalla de resultados de una búsqueda.
- La precarga por DOI existe pero es intermitente y deja vacíos campos obligatorios: el cargador entra por *Omitir*.
- Una convocatoria solo computa registros del período: un rubro "Con datos" puede valer cero.
