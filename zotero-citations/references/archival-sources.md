# Fuentes históricas y documentales — protocolo

## Definición

Fuentes que NO tienen DOI ni ISBN moderno, y a veces tampoco editorial, autor identificable o año preciso:

- Manuscritos antiguos o incunables.
- Documentos de archivo (cartas, decretos, actas, partidas, escrituras notariales, expedientes).
- Fuentes éditas antiguas con impresores históricos ("Imprenta de...", "En la oficina de...", "Establecimiento Tipográfico...").
- Prensa histórica (periódicos y gacetas del siglo XIX o anteriores, prensa obrera, boletines sindicales).
- Documentos oficiales de baja accesibilidad digital.
- Mapas, planos y material cartográfico antiguo.
- Fotografías, postales o grabaciones con metadatos mínimos.

## Principio rector

**No inventar metadatos que faltan.** La cita debe permitir que un lector encuentre el documento original. La estructura depende de la norma del manuscrito: APA (guía *Archival documents and collections* de APA Style) o Chicago (CMOS 18, fuentes manuscritas y colecciones, cap. 14). Las reglas específicas y las reglas duras de abajo valen para las dos.

## Estructura APA 7

```
Autor, A. A. (Año, día de mes). Título del material [Descripción]. Nombre de la colección (Signatura, Caja, Carpeta). Repositorio, Ciudad, País. URL
```

| Campo | Cuándo | Cómo |
|---|---|---|
| Autor | Si se conoce | Patrón APA (`Apellido, I.`); institución tal como aparece en el documento. |
| Fecha | Del documento, no de la consulta | Exacta: `1876, 15 de marzo` (en inglés `1876, March 15`). Solo año: `1876`. Aproximada con respaldo: `[ca. 1876]` o `[1876?]`. Desconocida: `s. f.` / `n.d.`. Rango: `[1860–1870]`. |
| Título | Siempre | En cursiva si la obra tiene título propio; si es un documento sin título, descripción entre corchetes sin cursiva: `[Carta a Alberto Girri]`. |
| Descripción | Siempre | Entre corchetes: `[Carta]`, `[Manuscrito]`, `[Mapa]`, `[Fotografía]`, `[Partida de bautismo]`, `[Decreto]`, `[Acta]`. |
| Colección y localización | Recomendado | Entre paréntesis: `(Caja 3, Carpeta 12, f. 5)`. Solo con datos verificados. |
| Repositorio | Siempre | Institución que custodia, en su idioma original: `Archivo General de la Nación`, no "General Archive of the Nation". |
| Ciudad, país | Si aplica | Donde está el repositorio. |
| URL | Solo si hay copia digital del documento | URL directa al documento, nunca la home del catálogo. |

## Ejemplos de estructura

Ilustrativos: muestran el orden de los elementos, no documentos verificados.

- Carta: `Apellido, N. (1953, 12 de agosto). [Carta a Destinatario]. Fondo Apellido (Caja 4, Carpeta 12). Repositorio, Buenos Aires, Argentina.`
- Decreto: `Gobierno de la Provincia de Buenos Aires. (1853, 11 de noviembre). [Decreto sobre organización de la justicia]. Archivo Histórico de la Provincia de Buenos Aires, La Plata, Argentina.`
- Prensa histórica con título: `Título de la nota. (1870, 5 de abril). *La Prensa*, 2.` Sin título: `[Nota editorial sobre la cuestión capital]. (1870, 5 de abril). *La Prensa*, 2.`
- Fotografía: `[Fotografía de la Plaza de Mayo]. (1910). Archivo General de la Nación (Documentos Fotográficos, Caja N). Buenos Aires, Argentina.`
- Mapa: `[Mapa de la Ciudad de Buenos Aires]. (1870). Archivo General de la Nación (Cartoteca, Caja 2). Buenos Aires, Argentina.`

Fuente édita antigua (ejemplo real): `Sarmiento, D. F. (1845). *Civilización i barbarie: Vida de Juan Facundo Quiroga*. Imprenta del Progreso.` — se conserva la grafía original del título y el impresor histórico.

## Estructura Chicago 18.ª

En Chicago, el material de archivo se cita sobre todo **en notas**, de lo particular a lo general: documento → fecha → localización (caja, carpeta, folio) → colección → repositorio, ciudad. La bibliografía suele listar **la colección**, no cada documento (salvo que se cite uno solo de esa colección).

Ilustrativos (estructura, no documentos verificados):

- Nota, carta: `Julio Cortázar a Alberto Girri, 12 de agosto de 1953, caja 4, carpeta 12, Fondo Cortázar, Repositorio, Buenos Aires.`
- Nota abreviada siguiente: `Cortázar a Girri, 12 de agosto de 1953.`
- Nota, documento sin autor: `Decreto sobre organización de la justicia, 11 de noviembre de 1853, Archivo Histórico de la Provincia de Buenos Aires, La Plata.`
- Bibliografía, colección: `Fondo Cortázar. Repositorio, Buenos Aires.`
- Prensa histórica (nota): `«Nota editorial sobre la cuestión capital», *La Prensa* (Buenos Aires), 5 de abril de 1870, 2.` Los artículos de diario suelen citarse solo en notas.
- En autor-fecha, el documento va en la lista como en APA pero con el año tras el autor: `Gobierno de la Provincia de Buenos Aires. 1853. «Decreto sobre organización de la justicia», 11 de noviembre. Archivo Histórico de la Provincia de Buenos Aires, La Plata.`

Descripciones genéricas (carta, decreto, acta) van sin comillas ni cursiva; los títulos propios, como cualquier título (comillas para partes, cursiva para obras).

## Reglas específicas

1. **Fechas aproximadas** (`[ca. 1890]`, `[1890?]`) solo con una fuente que las respalde; si no, `s. f.`.
2. **Fecha dudosa pero legible**: la fecha presumida entre corchetes: `[1856?]`.
3. **Autores institucionales antiguos**: nombre histórico (`Gazeta de Madrid`), no una "Editorial X" moderna. Si se conoce el impresor y no el autor, el impresor va después del título.
4. **Sin autor**: el título pasa al primer lugar. En el texto, las primeras palabras del título: `("Nota editorial", 1870)` o `(*Civilización i barbarie*, 1845)`.
5. **Agregados del archivero**: lo que no está en el documento original va entre corchetes. Le indica al lector qué es del documento y qué del registro archivístico.
6. **Copia vs original**: si la fecha de la copia difiere de la del contenido: `(Original 1530; copia ca. 1870)`.
7. **Obras republicadas**: `(1845/2018)` en la cita y `(Obra original publicada en 1845)` al final de la referencia.

## Payload Zotero

| Fuente | `itemType` | Creadores útiles |
|---|---|---|
| Carta | `letter` (`letterType`: "Carta manuscrita") | `author`, `recipient` |
| Manuscrito, expediente, documento sin publicar | `manuscript` (`manuscriptType`) | `author` |
| Decreto, acta, documento oficial | `document` (`type`) | `author` (institución con `name`) |
| Nota de prensa histórica | `newspaperArticle` | `author` |
| Libro antiguo édito | `book` (sin `ISBN`) | `author` |
| Mapa | `map` (`mapType`, `scale`) | `cartographer` |
| Fotografía, grabado, obra visual | `artwork` (`artworkMedium`: "Fotografía") | `artist` |
| Audio / video / film | `audioRecording`, `videoRecording`, `film` | según tipo |

`photograph` no existe en Zotero. Ver la lista completa con `zotero_client.py template <tipo>`.

```json
{
  "itemType": "letter",
  "title": "[Carta a Destinatario]",
  "letterType": "Carta manuscrita",
  "creators": [
    {"creatorType": "author", "firstName": "Nombre", "lastName": "Apellido"},
    {"creatorType": "recipient", "firstName": "Nombre", "lastName": "Destinatario"}
  ],
  "date": "1953-08-12",
  "archive": "Repositorio",
  "archiveLocation": "Fondo Apellido, Caja 4, Carpeta 12",
  "callNumber": "Signatura si existe",
  "url": "",
  "tags": [{"tag": "citation-audited"}, {"tag": "archival-source"}]
}
```

Campos archivísticos reales del schema:
- `archive` — institución que custodia.
- `archiveLocation` — fondo/colección, caja, carpeta, folio.
- `callNumber` — signatura topográfica.
- `place` — ciudad (en `manuscript`, `document`, `map`, `book`; `letter` y `artwork` no lo tienen: usar `archive`).
- `date` — fecha del documento; vacía si no hay (nunca `s. f.` como texto).
- `extra` — datos sin campo propio, una línea por dato (`Original Date: 1530`).

`archiveCollection` no existe: la colección va en `archiveLocation`.

## Validación — caso archivístico

**No se buscan DOI ni ISBN para fuentes de archivo.** El protocolo:

1. **Verificar** que el documento está catalogado en el repositorio mencionado (catálogo en línea del archivo, guía de fondos).
2. **Confirmar** la signatura (caja, carpeta, folio) en ese catálogo.
3. **Si el archivo digitalizó el documento**, usar la URL directa al documento digital.
4. **Si no hay forma de verificar** su existencia, marcarlo `[revisión manual obligatoria]` y **no** crear el registro en Zotero.

En el reporte, sección "Fuentes archivísticas":

```
| # | Referencia | Repositorio | Signatura | URL | Estado |
```

Estado: `verificada`, `signatura pendiente` o `revisión manual obligatoria`.

## Reglas duras

- **Nunca inventar signatura, caja, carpeta o folio.** Si el usuario no la dio y no está en el catálogo: `[signatura: verificar]`.
- **Nunca traducir el nombre del repositorio.**
- **Fuentes éditas anteriores a 1900**: editorial = lo que figura en el documento ("Imprenta de...", "Por...", "En casa de..."). Nunca una editorial actual.
- **Sin ISBN moderno** para ediciones antiguas: el campo queda vacío. Si se cita una edición moderna, se cita esa edición con su ISBN y el año original va en `originalDate`.
