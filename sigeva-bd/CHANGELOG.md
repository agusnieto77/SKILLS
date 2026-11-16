# Changelog

## 1.3.0 — 2026-11-12

- `pip-cargar` ya no da por buenas las secciones en "Ok": las que tienen `campos`, `filas`, `seleccion` o
  `miembros` se reabren y se comparan con lo pedido; solo se guarda lo que difiere y el recibo dice qué.
  Después de cada Guardar se relee el formulario: "Ok" con contenido distinto es `no-guardado`.
- Nuevos tipos en `pip.json`: `filas` (grillas de filas repetidas, como la recusación) y `seleccion`
  (casillas paginadas que guardan al clic, como Otras fuentes de financiamiento: en seco no se hace
  ningún clic y con `--guardar` se valida todo antes del primero).
- `estado-pip.jsonl` guarda la `huella` del contenido: un cambio en los datos vuelve a encolar la sección.
- Grupo: cada integrante declarado se habilita (casilla HAB): quien se incorpora con el código del trámite
  aparece sin rol y sin habilitar. Se avisa si alguien quedaría sin rol.
- Trampas nuevas documentadas: el resumen admite 2500 caracteres y SIGEVA borra sus saltos de línea sin
  dejar espacio (la relectura posterior al guardado lo detectó en el sitio real).
- Corrige la regresión que dejaba de saltear las secciones en "Ok" sin contenido comparable (grillas,
  adjuntos). Simulador: enlaces de la tabla siempre disponibles (como el sitio real), formularios que
  muestran lo cargado, recusación y otras fuentes paginadas.

## 1.2.0 — 2026-11-12

- Módulo de convocatorias (presentación/solicitud, rol 72): nuevos comandos `pip-mapear`, `pip-verificar`,
  `pip-estados`, `pip-preparar`, `pip-cargar` y `pip-enviar`, con la misma disciplina del Banco de Datos
  (solo lectura para el mapeo, en seco por defecto, tandas cortas, verificación previa y éxito por relectura).
  Guía nueva [pip](references/pip.md) y línea base PIP separada (`mapa-pip-base.json`, con `origen`
  real/simulador: una línea base del simulador no habilita trabajos contra el sitio real).
- `pip-cargar` nunca aprieta ENVIAR PRESENTACIÓN: éxito = la sección vuelve a "Ok" en la tabla de estados
  (cantidad de ítems leída de la tabla, nada hardcodeado). `pip-enviar --confirmo-enviar` es la única vía
  asistida de envío, aparte y con todos los estados en "Ok"; la vía preferida sigue siendo el botón a mano.
- `pip-preparar` valida `pip.json` sin red: tramite, secciones con nombre exacto de la tabla, campos
  sin vacíos (no se estiman), adjuntos existentes, PDF y dentro del límite de tamaño (el aval es un PDF
  firmado: solo subida, nunca generación).
- `sigeva_mapa`: excepciones por módulo (`IDS_ESTRUCTURALES_EXTRA`, `ACCIONES_SEGURAS_EXTRA`) para que el
  recorrido del módulo trate `tramiteId` como estructura y siga las acciones de alta propias de convocatorias.
- Simulador con pantallas mock del trámite (tabla de 11 estados, formularios con datepicker, radios y
  adjuntos con límite, Guardar silencioso, botón ENVIAR que exige todo en "Ok") y pruebas unitarias y de
  punta a punta del módulo. `Sesion.iniciar(rol=)` para entrar por presentación; `VERSION` corregida a 1.2.0.

## 1.1.0 — 2026-10-26

- Skill renombrada de `sigeva-banco-datos` a `sigeva-bd`.
- Comandos `cv` (cruza un CV .docx/.pdf/.txt con el inventario: faltantes, no publicados, fuera de período, en otra tabla) y `pdf` (recorte de créditos + trabajo y compresión por debajo de 35 MB). Guía [flujo-cv](references/flujo-cv.md): de CV a Banco de Datos, regla de buscar el material a fondo en la web antes de pedírselo a la persona, qué datos solo declara ella y errores ya resueltos.
- `preparar` exige compiladores en partes de libro e ISBN y páginas en libros y partes; ingreso al CAS que distingue rechazo de cuelgue y reintenta una sola vez solo ante un cuelgue.

## 1.0.0 — 2026-10-25

- Primera versión. CLI `assets/sigeva_bd.py` con `doctor`, `bib`, `inventario`, `catalogo`, `inspeccionar`, `preparar`, `cargar`, `mapear` y `verificar`.
- Carga de artículos, trabajos en eventos, libros y partes de libro con autores, compiladores, filiaciones inyectadas por id de catálogo, rol, referato, área del conocimiento, palabras clave y full text (en libros, por el uploader AJAX y solo al guardar); registros `generico` para cualquier otro rubro relevado con `inspeccionar`. Comando `institucion` para buscar en el catálogo oficial.
- Comando `modificar` para corregir registros existentes sin duplicar: abre el id vigente de la lista, marca al declarante si falta, guarda con Modificar y verifica por diferencia de ids; un duplicado se informa y solo se borra con `--borrar-duplicado` tras verificar el registro nuevo.
- Mapa de solo lectura del Banco de Datos (123 pantallas en SIGEVA 14.11.24.6), línea base saneada y documento generado; detección de cambios por severidad con historial. `verificar --auto` corre al inicio de todo trabajo contra SIGEVA (`inventario`, `catalogo`, `inspeccionar`, `cargar`), reutiliza una verificación aprobada de las últimas 6 h y frena el trabajo ante un cambio crítico; `cargar` repasa además el contrato antes de la primera alta.
- Rutas canónicas: ids de registros generalizados y paginación acumulada descartada. Pantallas de datos personales sin opciones publicadas; barrera que impide escribir la línea base si contiene las credenciales.
- Pruebas sin red: unitarias y de punta a punta contra un SIGEVA simulado con sus trampas (datepicker, AJAX, guardado silencioso, archivo vaciado).
