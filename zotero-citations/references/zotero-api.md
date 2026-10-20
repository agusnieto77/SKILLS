# Zotero API — contrato de integración

Verificado contra la documentación oficial (Web API v3, API local) y contra una biblioteca real (schema 42, Zotero 9). `scripts/zotero_client.py` implementa todo esto; usá esta referencia para entender sus decisiones o para casos que el script no cubre.

## Dos APIs

| | Web API | API local (Zotero desktop) |
|---|---|---|
| Base | `https://api.zotero.org` | `http://127.0.0.1:23119/api` (no `localhost`: en Windows intenta IPv6 primero y pierde ~2 s por request) |
| Lectura | Key (o pública) | Sin auth; hay que habilitar *Settings → Advanced → Allow other applications on this computer to communicate with Zotero* (si no, 403) |
| Escritura | Key con permiso de escritura | Solo Zotero 10+, con key local que el usuario aprueba en un diálogo |
| Límites | `Backoff`, 429 + `Retry-After`; `limit` máx. 100, paginación con `start` | Sin rate limit; sin paginación por default |
| Biblioteca | `/users/{userID}` o `/groups/{groupID}` | Solo el usuario logueado (`/users/0` o su ID; otro ID → 400) y sus grupos |
| Versiones | Las del servidor | En Zotero 10+ son locales y **no** comparables con las de la Web API |

Regla: leer de la local si responde (rápido, sin cuota); escribir siempre por Web API (hasta Zotero 10). Lo creado por Web API aparece en la local tras sincronizar.

## Autenticación

- Headers: `Zotero-API-Version: 3` y `Zotero-API-Key: <key>` (o `Authorization: Bearer <key>`). Nunca la key en la URL.
- `GET /keys/current` devuelve `userID`, `username` y permisos (`access.user.library`, `access.user.write`, `access.groups`). Así se obtiene el `userID` sin pedírselo al usuario.
- Keys en `https://www.zotero.org/settings/keys`. Para esta skill: lectura de biblioteca + escritura.

## Lectura

```
GET {prefix}/items/top?format=json&includeTrashed=1&limit=100&start=0
GET {prefix}/items?itemKey=K1,K2,...        (máx. 50 claves por request)
GET {prefix}/items/{itemKey}                  (data + version)
GET /schema                                   (tipos, campos, creadores; sin auth)
GET /items/new?itemType=book                  (plantilla vacía oficial; sin auth)
```

### Búsqueda: trampas verificadas

- `q` es **búsqueda de frase**, no por campo. `q=DOI:10.x/y` no es una sintaxis válida.
- `qmode=titleCreatorYear` (default) solo mira título, creadores y año: **no encuentra DOI ni ISBN**.
- `qmode=everything` sí encuentra identificadores, pero también texto completo de PDFs y notas: en `/items` devuelve el **adjunto** (PDF) en lugar del ítem. Usá siempre `/items/top` y comprobá el campo exacto (`DOI`, `ISBN`, o `DOI:` dentro de `extra`).
- La búsqueda de la API local usa el motor de quicksearch local: devuelve más ítems (notas, anotaciones). Filtrá `itemType` `attachment`, `note`, `annotation`.
- Para cotejar un manuscrito completo es más preciso bajar un snapshot de `/items/top` (cacheado por `Last-Modified-Version`) y comparar localmente: es lo que hace `match`.
- Filtros: `itemType=book || journalArticle`, `itemType=-attachment`, `tag=foo`, `includeTrashed=1`.

### Formateo APA del lado del servidor

```
GET {prefix}/items?itemKey=K1,K2&format=json&include=data,bib,citation&style=apa&locale=es-ES
GET {prefix}/items?itemKey=K1,K2&format=bib&style=apa&locale=es-ES      (lista ordenada, máx. 150)
```

- `include=bib,citation` devuelve por ítem la referencia y la cita parentética en HTML (`<i>` para itálicas).
- Los sufijos `a`/`b` de mismo autor y año solo aparecen si esos ítems se renderizan **juntos** (`format=bib`).
- El CSL `apa` con `es-ES` produce `En`, `s. f.`, `Recuperado ... de`, `(Eds.)`, pero **mantiene `&`** en citas y deja **guion** en rangos de páginas; Chicago entrega `n.<sup>o</sup>`: `cite_format.py render` corrige todo eso.
- `style` acepta cualquier id del repositorio (`chicago-notes-bibliography`, `iso690-author-date-es`, el de una revista). Verificado: la **Web API devolvió 500** para `chicago-author-date` y `modern-language-association` mientras la API local los renderizaba bien; si la web falla, usá la local. Estilos de notas devuelven en `citation` la nota (completa o abreviada según el CSL).
- Índice completo de estilos (sin auth): `https://www.zotero.org/styles-files/styles.json` (nombre, título, formato `author-date`/`note`/`numeric`, disciplinas).
- El CSL no cambia mayúsculas de los títulos: se imprimen como están guardados. Los títulos en Zotero deben estar en sentence case (salvo revistas).
- La API local y la Web API pueden traer versiones distintas del estilo (p. ej. mayúscula tras dos puntos). Preferí la local si está disponible y mantené la misma fuente en todo el manuscrito.

### Texto completo y anotaciones (para `source_check.py`)

```
GET {prefix}/items/{itemKey}/children?format=json     (adjuntos: contentType application/pdf, epub, text/html)
GET {prefix}/items/{attachmentKey}/fulltext            ({"content", "indexedPages", "totalPages"})
```

- `fulltext` va sobre la **clave del adjunto**, no del ítem padre. 404 = no indexado (en Zotero: clic derecho → *Reindexar ítem*).
- El contenido es el texto que extrajo Zotero: puede traer saltos de página (`\f`), saltos de línea, guiones de corte y ligaduras (`ﬁ`). Algunos PDF no conservan `\f`, y entonces no hay número de página.
- `indexedPages < totalPages` significa índice parcial (límite de páginas en las preferencias de búsqueda de Zotero): una cita "no encontrada" puede estar en las páginas sin indexar.
- Web API y API local devuelven el mismo texto (verificado: 65.766 caracteres en ambas).
- Anotaciones (`itemType: annotation`, hijas del adjunto) traen `annotationText`, `annotationPageLabel` (página impresa) y `annotationPosition.pageIndex` (página del PDF). Comparando ambas se obtiene el desfase entre página del PDF y página impresa. La **API local no las lista como hijas** del adjunto: hay que pedir `/items?itemType=annotation` y filtrar por `parentItem`.
- Escaneos sin OCR no tienen texto: el resultado es `no-fulltext`, no un error del manuscrito.

### `itemKey` en la API local

`/items?itemKey=K1,K2` en la API local devuelve también los hijos (adjuntos, anotaciones) de esos ítems. Filtrá por las claves pedidas o usá `/items/top`.

## Escritura

### Crear (`POST {prefix}/items`)

- Body: array de hasta **50** ítems (más → 413). Partí en lotes.
- Header `Zotero-Write-Token: <32 hex aleatorios>` por lote: si se reintenta el mismo lote, el servidor responde 412 en vez de duplicar (el token vale 12 h). Alternativa: `If-Unmodified-Since-Version: <versión de biblioteca>`.
- Respuesta 200 con éxito **por índice**:

```json
{"success": {"0": "ABCD2345"}, "successful": {"0": {"key": "ABCD2345", "...": "..."}},
 "unchanged": {}, "failed": {"1": {"key": "", "code": 400, "message": "..."}}}
```

  Un 200 no significa que todo se creó: revisá `failed`.
- No mandes `key` ni `version` al crear (Citoid y los exports los traen).
- `collections: ["COLLKEY"]` agrega el ítem a una colección; `tags: [{"tag": "..."}]`.

### Actualizar (`PATCH {prefix}/items/{itemKey}`)

- Body: solo los campos que cambian. Arrays (`creators`, `tags`, `collections`) se reemplazan completos.
- Obligatorio `If-Unmodified-Since-Version: <versión del ítem>` (o `version` en el body). Si alguien lo modificó → 412: releer, volver a mostrar el diff y volver a confirmar.
- 204 = ok; la nueva versión viene en `Last-Modified-Version`.
- `PUT` reemplaza el ítem entero (borra lo que no mandes): evitarlo.

### Papelera, no borrado

- `PATCH` con `{"deleted": 1}` manda el ítem a la papelera (restaurable con `{"deleted": 0}`).
- `DELETE` (requiere `If-Unmodified-Since-Version`, si no 428) es definitivo: esta skill no lo usa.

## Tipos y campos

El schema es la fuente de verdad (`GET /schema`, versión 42 al momento de escribir esto); `check` valida contra él. Errores frecuentes que tenían las plantillas anteriores:

| Incorrecto | Correcto |
|---|---|
| `abstract` | `abstractNote` |
| `page` en artículos | `pages` |
| `publisher` en `report` | `institution` |
| `publisher` en `dataset` | `repository` |
| `publisher` en `thesis` | `university` |
| `itemType: photograph` | `artwork` (creador `artist`) |
| `archiveCollection` | no existe: `archive` + `archiveLocation` (+ `callNumber`) |
| `ISBN` en `manuscript` | no existe en ese tipo |

Creadores: `{"creatorType": "author", "lastName": "...", "firstName": "..."}` o, para instituciones, `{"creatorType": "author", "name": "..."}` (uno u otro, nunca ambos). Los `creatorType` válidos dependen del tipo (`letter` tiene `recipient`; `map`, `cartographer`; `artwork`, `artist`; `bookSection`, `bookAuthor`).

Otros campos útiles: `DOI` sin prefijo URL, `ISBN` puede tener varios separados por espacio, `extra` para datos sin campo propio (`Original Date: 1867`), `date` vacío para obras sin fecha (APA imprime `s. f.`/`n.d.` sola).

## Errores HTTP

| Código | Causa | Acción |
|---|---|---|
| 400 | Campo/tipo inválido, JSON roto; en la API local, biblioteca ajena | Correr `check`; en local, caer a Web API. |
| 403 | Key inválida o sin permiso; API local deshabilitada | `whoami`; habilitar la API local. |
| 409 | Biblioteca bloqueada | Reintentar más tarde. |
| 412 | Versión desactualizada o write token ya usado | Releer; con token, buscar si el lote ya se guardó antes de reintentar. |
| 413 | Más de 50 objetos | Lotes de 50. |
| 428 | Falta `If-Unmodified-Since-Version` | Agregarlo. |
| 429 | Demasiadas requests | Esperar `Retry-After` (o backoff exponencial); respetar `Backoff` en cualquier respuesta. |
