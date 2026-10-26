# Formato de `registros.json`

Una lista JSON. Cada registro tiene `clave` (estable entre corridas: es lo que usa `estado.jsonl` para no repetir) y `tipo`: `articulo`, `evento`, `capitulo`, `libro` o `generico`. `preparar` valida y separa en `listos`, `bloqueados` y `ya_cargados`; `cargar` solo acepta lo que valida.

Texto: SIGEVA trabaja en ISO-8859-1. Lo que no entra (`ş`, `—`, comillas tipográficas) se reemplaza y `preparar` lo avisa.

## Comunes a `articulo`, `evento`, `capitulo` y `libro`

| Campo | Obligatorio | Nota |
|---|---|---|
| `clave` | sí | Identificador propio (p. ej. la clave BibTeX) |
| `titulo` | sí | |
| `autores` | sí | Lista de `{apellido, nombre, declarante?, institucion?, institucion_id?, institucion_otra?}` en orden |
| autor declarante | sí | Exactamente uno: `"declarante": true` o el apellido de `config.declarante` |
| `idioma` | sí | Etiqueta del combo: `Español`, `Inglés`, `Portugués`… |
| `resumen` | sí | SIGEVA lo exige |
| `archivo` | sí | Full text (PDF ≤ 35 MB). Sin archivo SIGEVA no guarda |
| `area_conocimiento` | sí* | `{campo, subcampo}`; *si no está, se usa la de `config.json` |
| `palabras_clave` | no | Se cargan en mayúsculas, hasta los campos disponibles |
| `doi`, `url` | no | Con soporte electrónico hace falta uno de los dos |
| `soporte` | no | `["electronico"]`, `["impreso"]` o ambos. Por defecto electrónico si hay DOI/URL |
| `en_prensa` | no | `true` bloquea: un aceptado no es un publicado |

## `articulo`

| Campo | Obligatorio | Nota |
|---|---|---|
| `publicacion_id` | uno de tres | Id de la revista en SIGEVA (`catalogo`). Es la vía más confiable |
| `issn` / `revista` | uno de tres | Búsqueda en el catálogo de SIGEVA. Si hay varias coincidencias, se bloquea y se pide `publicacion_id` |
| `revista_otra_autorizada` | no | `true` permite dar de alta la revista como "otra" (solo con ISSN) si no está en el catálogo |
| `editorial`, `pais_edicion` | sí | País con la etiqueta de SIGEVA (`Estados Unidos`, `Reino Unido`, `República de China` para Taiwán) |
| `fecha_publicacion` | sí | `mm/aaaa`. El mes no se estima |
| `volumen`, `tomo`, `numero`, `paginas`, `ciudad_edicion` | no | `paginas` como `10-20` |
| `institucion_id` de **cada** autor | sí | SIGEVA exige filiación por autor en artículos |
| `version_adjunto` | no | `postprint` (defecto) o `final`. SIGEVA no acepta preprint |
| `referato` | no | Solo se cubre "con referato"; `false` bloquea |

## `evento` (trabajo en evento C-T publicado)

| Campo | Obligatorio | Nota |
|---|---|---|
| `titulo_publicacion` | sí | Título de las actas / libro / revista |
| `tipo_publicacion` | sí | Etiqueta: `Libro` o `Revista` |
| `reunion`, `tipo_reunion` | sí | Tipo: `Conferencia`, `Simposio`, `Workshop`… |
| `alcance` | sí | `nacional` o `internacional` |
| `pais_evento`, `ciudad_evento`, `fecha_evento` | sí | Fecha `mm/aaaa`. La lista de SIGEVA muestra el año del evento, no el de las actas |
| `pais_edicion`, `editorial`, `anio_publicacion` | sí | |
| `isbn` | no | SIGEVA valida el formato |
| `tipo_trabajo` | no | Por defecto `Artículo Completo` |
| `institucion_organizadora` | no | |

En eventos la filiación no es obligatoria: un autor con `institucion` sin `institucion_id` se carga sin filiación y se avisa.

## `capitulo` (parte de libro) y `libro`

| Campo | Obligatorio | Nota |
|---|---|---|
| `isbn` | sí | SIGEVA lo exige y valida el formato. Usar el de la edición cuyo full text se adjunta |
| `paginas_libro` | sí | Cantidad de páginas del libro completo |
| `editorial`, `pais_edicion`, `anio_publicacion` | sí | `ciudad_edicion` opcional |
| `referato` | sí | `true`/`false`: comité editorial o referato del libro |
| `rol` | no | Lista con `autor`, `editor`, `revisor` (rol de quien declara). Por defecto `["autor"]` |
| `tipo_parte` | sí (capítulo) | Etiqueta: `Capítulo de libro`, `Introducción`, `Prólogo o prefacio`, `Entrada de diccionario, glosario o repertorio biográfico`… |
| `titulo_libro`, `paginas` | sí (capítulo) | `paginas` como `15-69`: SIGEVA exige inicial y final si está publicado |
| `compiladores` | sí (capítulo) | Misma forma que `autores`; se marca a quien declara si figura entre ellos. SIGEVA rechaza la parte de libro sin al menos uno ("Debe ingresar el/los compiladores…"). No inventar la lista si la ficha dice "et al." |

En libros el full text va por un uploader AJAX (`qqfile`) que sube el archivo apenas se elige: `cargar` en seco **no** lo sube; lo sube al guardar. Un PDF de más de 35 MB hay que comprimirlo antes (rebajar imágenes; el texto vectorial no pierde calidad).

## `generico` (cualquier otro rubro)

Para premios, financiamiento, formación de RRHH, redes, cargos, etc. Primero relevar el formulario:

```bash
python assets/sigeva_bd.py inspeccionar --url "eva/bcoPremio.do?accion=nuevo"
```

Eso deja en `sigeva-trabajo/inspecciones/` cada control con su `name`, tipo, etiqueta, opciones y si es datepicker. Las URL de alta y de lista de cada rubro están en el [mapa del sitio](mapa-sitio.md).

```json
{
  "clave": "premio-houssay-2023",
  "tipo": "generico",
  "rubro": "Premios y/o distinciones",
  "url_alta": "eva/bcoPremio.do?accion=nuevo",
  "url_lista": "eva/bcoPremioLista.do?idModulo=7&idGrupo=7&idMenu=1470",
  "buscar_en_lista": "Premio Houssay",
  "campos": {
    "premio": "Premio Houssay",
    "tipoPremio": {"etiqueta": "Nacional"},
    "anio": "2023",
    "institucionOtorgante": "MINCyT"
  }
}
```

| Valor en `campos` | Se usa como |
|---|---|
| texto / número | `fill` del campo |
| `{"etiqueta": "…"}` o `{"valor": "…"}` | opción de un `select` (etiqueta exacta y única) |
| `{"fecha": "mm/aaaa"}` o campo datepicker | fecha fijada con `setDate` |
| valor de radio / lista de valores de checkbox / `true`/`false` | marca de radio o casilla |

`buscar_en_lista` es un texto que identifica al registro en la lista: si ya figura, no se carga. La verificación posterior exige **exactamente un** registro nuevo en la lista y relee sus campos de texto, fechas y `select` con `valor`. Opcionales: `archivo` + `campo_archivo` (por defecto `theFile`) y `boton_guardar` (por defecto `Guardar`; `Modificar`, `Borrar`, `Eliminar` y `Enviar` están prohibidos).

Libros y partes de libro van con sus tipos propios, no con `generico`: la tabla de autores y compiladores se arma por JavaScript.
