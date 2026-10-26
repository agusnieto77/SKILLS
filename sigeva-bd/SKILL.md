---
name: sigeva-bd
description: "Trigger: SIGEVA, SIGEVA CONICET, Banco de Datos de Actividades CyT, cargar o corregir publicaciones/artículos/congresos/libros/capítulos/premios/antecedentes en SIGEVA, actualizar SIGEVA desde el CV, CVar, si.conicet.gov.ar, intranet CONICET, informe reglamentario, mapear o verificar cambios en los formularios de SIGEVA."
license: Apache-2.0
compatibility: Python >= 3.10 con Playwright y Chromium. Requiere cuenta propia de la intranet del CONICET con el rol "Usuario banco de datos de actividades de CyT".
metadata:
  author: "agusnieto77"
  version: "1.1.0"
---

## Activation Contract

Activar al pedir cargar, revisar, corregir, inventariar o actualizar antecedentes en el Banco de Datos de Actividades CyT de SIGEVA CONICET (artículos, trabajos en eventos, libros, capítulos, premios, financiamiento, formación de RRHH, etc.), al poner al día el Banco de Datos a partir de un CV o un BibTeX, o al mapear, documentar o vigilar cambios en sus pantallas.

## Hard Rules

- Todo lo que entra al Banco de Datos es una **declaración jurada**. No inventar ni estimar datos: un campo que falta se informa y bloquea ese registro; nunca se completa con algo plausible (mes de publicación, institución, editorial, resumen). Un dato aproximado (p. ej. páginas) solo con autorización explícita y avisando que es aproximado.
- **Buscar antes de pedir.** Antes de pedirle a la persona un PDF, link, ISBN, páginas, compiladores o cualquier dato bibliográfico, buscarlo a fondo en la web (DOI, Crossref/OpenAlex, CONICET Digital y otros repositorios, sitio de la editorial o del evento, JSTOR, buscadores, Wayback para enlaces caídos) según el orden de [flujo-cv](references/flujo-cv.md#2-buscar-el-material-primero-en-la-web-siempre). Pedir solo lo que, tras esa búsqueda, no está en línea, todo junto y diciendo dónde se buscó. Lo que solo la persona puede declarar (área, alcance, referato, rol, aprobación de resúmenes) se pregunta, no se busca.
- `cargar` trabaja **en seco** por defecto. Usar `--guardar` solo con autorización explícita de la persona para esa tanda, después de que revise las capturas en seco.
- Altas con `cargar`; correcciones de registros existentes solo con `modificar` (en seco por defecto, `--guardar` con autorización), que sigue el protocolo anti-duplicados de [trampas](references/trampas.md#modificar-sin-duplicar). Nunca editar desde un id guardado de antes, nunca importar ni apretar "Enviar presentación". Borrar solo el duplicado que deja un `modificar` verificado (`--borrar-duplicado`), nunca otro registro.
- Éxito = el registro **aparece en la lista** y sus fechas releídas coinciden. Sin error visible no alcanza; un error de Hibernate puede haber guardado igual. Nunca reintentar un guardado sin verificar antes la lista.
- Credenciales: la persona las tipea en el navegador, o llegan por `--env-file` o `SIGEVA_USER`/`SIGEVA_PASS` solo para autenticar. Nunca pedirlas en el chat, imprimirlas, ni escribirlas en código, logs, documentación o el repositorio. SIGEVA bloquea la cuenta tras varios ingresos fallidos: ante un rechazo del CAS no se reintenta nunca; si el CAS solo se cuelga, el ingreso espera, recarga y reintenta una única vez. Si vuelve a fallar, parar y pedirle a la persona que pruebe entrar a mano.
- Nunca pedir que la persona confirme un id solo (`persona_id`, institución, revista, área): mostrarlo siempre con su nombre legible, p. ej. "`persona_id` 12345 = GARCÍA, MARÍA, autora declarante en 3 registros". Un número solo es una aprobación a ciegas. Antes de `--guardar`, mostrarle cómo quedaría cada registro (campos, autores con filiación, área con nombre, resumen) y esperar su ok.
- `mapear`, `verificar`, `inventario`, `catalogo`, `inspeccionar` e `institucion` son de solo lectura: no envían formularios ni abren acciones sobre registros. `cv`, `preparar`, `bib` y `pdf` no tocan SIGEVA.
- Tandas cortas (`--limite` 5 por defecto, máximo 20) con pausa entre altas: SIGEVA se traba con el estado acumulado de la sesión.
- Todo trabajo contra SIGEVA empieza con `verificar --auto`: `inventario`, `catalogo`, `inspeccionar` y `cargar` lo corren solos al iniciar la sesión (reutilizan una verificación aprobada de las últimas 6 h; `--vigencia-horas 0` fuerza repetirla). Si hay un cambio crítico o el recorrido queda incompleto, el comando no arranca. No eludirlo: leer el informe, corregir y volver a verificar.
- Además, `cargar` repasa el contrato de pantallas justo antes de la primera alta y se niega si falta algo (código 2).
- Los datos de la persona (listas, inventario, catálogo, capturas, estado) quedan en la carpeta de trabajo local, nunca en el repositorio de la skill.

## Decision Gates

| Necesidad | Acción |
|---|---|
| Primera vez en la máquina | `doctor`; si falla, `pip install -r assets/requirements.txt` y `python -m playwright install chromium` |
| Saber qué ya está cargado | `inventario` (lee las listas y el índice con los conteos) |
| Ids de revistas, instituciones y `persona_id` | `catalogo` (abre registros existentes en modo lectura) |
| Poner al día el Banco de Datos desde un CV | `inventario` → `cv --cv CV.docx --desde AAAA` → por cada `falta`, buscar el material en la web → registros → `preparar` → en seco → mostrar → `--guardar` → `inventario` + `cv` hasta `falta: 0` ([flujo-cv](references/flujo-cv.md)) |
| Artículos y trabajos en eventos desde BibTeX | `bib` → completar a mano lo que falta → `preparar` → `cargar` en seco → `cargar --guardar` |
| Full text: actas/libro completo o PDF de más de 35 MB | `pdf --paginas "2,45-53"` (créditos con ISBN + el trabajo) y/o `pdf --comprimir` |
| Corregir un registro ya cargado (año, estado, ISBN…) | `modificar --tipo … --titulo … --campo nombre=valor`, en seco y después `--guardar --borrar-duplicado` |
| Otro rubro (premios, financiamiento, RRHH, redes…) | `inspeccionar --url <alta>` para relevar los campos, armar un registro `generico` ([formato](references/registros.md)) y seguir igual |
| Institución que no está en el catálogo local | El catálogo local solo junta lo que ya usaste: buscarla en el catálogo oficial con `institucion --texto RAVIGNANI --provincia "Capital Federal"`, mostrar nombre y dependencia a la persona y usar su `institucion_id`. Solo si no existe en SIGEVA: alta a mano una vez y volver a correr `catalogo` |
| Revista que no está en el catálogo | No se inventa id: `issn` o `revista` (la busca `cargar`) o `revista_otra_autorizada` con ISSN |
| Libros y partes de libro (capítulo, introducción, entrada de diccionario…) | Tipos `libro` y `capitulo` ([formato](references/registros.md)). Tesis: `generico` o a mano |
| ¿SIGEVA cambió? | Corre solo al iniciar cada trabajo; a mano: `verificar --auto` ([monitoreo](references/monitoreo.md)) |
| El trabajo no arrancó por un cambio crítico | Mostrar el informe a la persona; corregir `assets/sigeva_bd.py`/`CONTRATO`, probar con el simulador, `verificar --aceptar` |
| Registro bloqueado en `preparar` | Mostrar `errores` a la persona y pedir el dato; no rellenar |

## Execution Steps

1. `doctor`. Copiar `assets/config.ejemplo.json` a la carpeta de trabajo y completar `declarante`, `area_conocimiento` y, tras `catalogo`, `persona_id`: mostrar los `nombres` de cada candidato y que la persona elija el suyo. Si no hay línea base en `references/`, `mapear --aceptar`.
2. `inventario` y `catalogo`. Contrastar los conteos del inventario con el índice del Banco de Datos.
3. Armar `registros.json` (`bib` o a mano según [registros](references/registros.md)). Cada registro necesita `clave` estable y el full text en `archivo`.
4. `preparar`: resuelve ids con coincidencia exacta, valida, descarta lo ya cargado. Resolver con la persona cada registro de `bloqueados`.
5. `cargar` en seco con `--limite` chico; revisar capturas y avisos con la persona.
6. Con su autorización: `cargar --guardar`. Leer el recibo; ante `no-guardado`, `rechazado` o `corte`, mirar la captura y la lista antes de cualquier reintento.
7. Repetir `inventario` al terminar. Cargar el Banco de Datos **antes** de armar una presentación: la solicitud toma los registros de ahí y solo computa los del período de la convocatoria.

## Output Contract

Informar por tanda: modo (`en-seco`/`guardar`), solicitados, resultado por clave (`guardado` con `verificado: true`, `ya-estaba`, `en-seco`, `rechazado`, `no-guardado`, `error`, `corte`), avisos, capturas, `motivo_fin` y ruta del recibo `recibo-cargar-*.json`. `verificar` devuelve el resumen por severidad (`critico`, `alto`, `medio`, `bajo`), cada cambio y si se adoptó la nueva línea base. No presentar una carga en seco ni una prueba contra el simulador como carga real.

## References

- [Del CV al Banco de Datos](references/flujo-cv.md) — flujo completo, orden de búsqueda en la web, qué preguntar y errores ya resueltos.
- [Formato de registros](references/registros.md) — campos de `articulo`, `evento`, `capitulo`, `libro` y `generico`, y qué bloquea cada uno.
- [Trampas de SIGEVA](references/trampas.md) — datepickers, filiaciones, verificación, sesión; por qué el código hace lo que hace.
- [Monitoreo](references/monitoreo.md) — `mapear`, `verificar`, severidades, contrato y programación periódica.
- [Mapa del sitio](references/mapa-sitio.md) — estructura relevada (generado; no editar a mano).
- [Guía de uso](README.md) — instalación, configuración y comandos.
