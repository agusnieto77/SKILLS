# APA 7 — reglas y payloads Zotero

El formato final lo produce `cite_format.py render --style apa` (CSL `apa` de Zotero, con correcciones encima). Esta referencia sirve para (1) cargar bien los datos en Zotero, porque el CSL imprime lo que está guardado, y (2) revisar o corregir el texto cuando el usuario no usa Zotero para esa entrada. Para Chicago, ver `chicago.md`; para formatos a medida, `custom-formats.md`.

Partí siempre de `zotero_client.py template <itemType>` o de `validate_ref.py payload <ID>`, y pasá el resultado por `zotero_client.py check`.

## Reglas universales

1. **Sangría francesa** de 1,27 cm (0,5 in) e interlineado doble en la lista.
2. **Orden alfabético** por apellido del primer autor, letra por letra; "nada precede a algo" (`Acha, O. (2015)` antes que `Acha, O., & Quiroga, N. (2015)`). Mismo autor: por año ascendente; mismo autor y año: por título, con sufijos `2015a`, `2015b` también en las citas. Obras sin autor: por la primera palabra significativa del título.
3. **Mayúsculas**: sentence case para títulos de artículos, capítulos, **libros** (también el libro editado que contiene un capítulo), tesis, informes y páginas web: mayúscula inicial, tras dos puntos y en nombres propios. Title case **solo** para nombres de revistas, diarios y otras publicaciones periódicas.
4. **Itálicas**: título de la obra independiente (libro, informe, tesis, página web, dataset) y, en artículos, nombre de la revista y volumen (`*Science*, *380*(6650)`). Nunca el título del artículo ni el del capítulo.
5. **DOI** como URL: `https://doi.org/10.xxxx/yyy`, sin "doi:", sin "Recuperado de". Si hay DOI, no se agrega la URL de la base de datos.
6. **Autores**: hasta 20 se listan todos, con `&` antes del último; con 21 o más, los primeros 19, `. . .` y el último. Nunca "et al." en la lista. Iniciales con punto y espacio (`Parker, D. C.`).
7. **Ciudad de la editorial**: APA 7 la omite. Si la editorial es el mismo autor institucional, se omite la editorial.
8. **Páginas**: rangos con raya (`59–81`). `pp.` solo en capítulos (`(pp. 349–390)`), nunca en artículos.
9. **Edición**: `(3rd ed.)` en inglés, `(3.ª ed.)` en español, entre paréntesis y sin itálica, después del título.
10. **Fechas especiales**: sin fecha `n.d.` / `s. f.`; en prensa `in press` / `en prensa`; fecha exacta para diarios, blogs y webs (`2024, March 15` / `2024, 15 de marzo`).
11. **Recuperado de**: solo para contenido que cambia y no está archivado: `Recuperado el 2 de octubre de 2026, de https://...` / `Retrieved October 2, 2026, from https://...`.

## Citas en el texto

| Caso | Parentética | Narrativa |
|---|---|---|
| 1 autor | `(Acha, 2015)` | `Acha (2015)` |
| 2 autores | `(Marx & Engels, 1947)` · es: `(Marx y Engels, 1947)` | `Marx and Engels (1947)` · es: `Marx y Engels (1947)` |
| 3+ autores | `(Grossmann et al., 2023)` desde la primera cita | `Grossmann et al. (2023)` |
| Autor institucional con sigla | 1.ª: `(Organización Internacional del Trabajo [OIT], 2019)`; luego `(OIT, 2019)` | 1.ª: `Organización Internacional del Trabajo (OIT, 2019)` |
| Sin autor | `(*Título del libro*, 2019)` o `("Título del artículo", 2019)` | idem sin paréntesis externos |
| Varias obras | `(Acha, 2015a, 2015b; Camarero, 2007)`: orden alfabético, `;` entre autores | — |
| Cita textual | `(Acha, 2015, p. 61)`, `(pp. 12–14)`, sin páginas: `párr. 3` | `Acha (2015, p. 61)` |
| Cita secundaria | `(Freud, 1900, como se cita en Ricoeur, 1970)`: solo Ricoeur va a la lista | — |
| Mismo apellido, autores distintos | `(L. Caruso, 2016; L. G. Caruso, 2016)` (APA 8.20) | — |

## Variantes por idioma

| Elemento | Inglés (APA 7) | Español (Manual APA, 4.ª ed. en español) |
|---|---|---|
| Conector en citas | `&` parentética, `and` narrativa | `y` en ambas (el CSL de Zotero deja `&`: `cite_format.py render --lang es` lo corrige) |
| Conector en la lista | `&`, con coma serial | `&` aceptado (es lo que genera Zotero); `y` también, **sin** coma antes. Uno solo en todo el documento |
| Sin fecha | `n.d.` | `s. f.` |
| Capítulo | `In A. Editor (Ed.), ...` | `En A. Editor (Ed.), ...` |
| Edición | `(2nd ed.)` | `(2.ª ed.)` |
| Recuperado | `Retrieved Month D, YYYY, from` | `Recuperado el D de mes de AAAA, de` |
| Descripciones | `[Doctoral dissertation, ...]`, `[Data set]` | `[Tesis doctoral, ...]`, `[Conjunto de datos]` |

El idioma lo define el texto del manuscrito, no el de la fuente citada.

## Payloads por tipo

Ejemplos reales validados por DOI/ISBN salvo donde se indica plantilla.

### Artículo de revista (`journalArticle`)

> Messeri, L., & Crockett, M. J. (2024). Artificial intelligence and illusions of understanding in scientific research. *Nature*, *627*(8002), 49–58. https://doi.org/10.1038/s41586-024-07146-0

```json
{
  "itemType": "journalArticle",
  "title": "Artificial intelligence and illusions of understanding in scientific research",
  "creators": [
    {"creatorType": "author", "firstName": "Lisa", "lastName": "Messeri"},
    {"creatorType": "author", "firstName": "M. J.", "lastName": "Crockett"}
  ],
  "publicationTitle": "Nature",
  "volume": "627",
  "issue": "8002",
  "pages": "49-58",
  "date": "2024",
  "DOI": "10.1038/s41586-024-07146-0",
  "ISSN": "0028-0836, 1476-4687",
  "tags": [{"tag": "citation-audited"}]
}
```

Sin volumen (revistas que solo numeran): `issue` sin `volume` → `*Cuadernos del Ciesal*, (14), 59–81.`

### Libro (`book`)

> Knuth, D. E. (1997). *The art of computer programming* (3rd ed., Vol. 1). Addison-Wesley.

```json
{
  "itemType": "book",
  "title": "The art of computer programming",
  "creators": [{"creatorType": "author", "firstName": "Donald E.", "lastName": "Knuth"}],
  "edition": "3",
  "volume": "1",
  "date": "1997",
  "publisher": "Addison-Wesley",
  "ISBN": "9780201896831"
}
```

`place` puede guardarse (otros estilos lo usan); APA lo omite. Obra republicada: `date` de la edición usada y `originalDate` con el año original → `(1867/1990)`.

### Capítulo de libro editado (`bookSection`)

> Korinek, A., & Stiglitz, J. E. (2019). Artificial intelligence and its implications for income distribution and unemployment. En A. Agrawal, J. Gans, & A. Goldfarb (Eds.), *The economics of artificial intelligence: An agenda* (pp. 349–390). University of Chicago Press. https://doi.org/10.7208/chicago/9780226613475.003.0014

```json
{
  "itemType": "bookSection",
  "title": "Artificial intelligence and its implications for income distribution and unemployment",
  "creators": [
    {"creatorType": "author", "firstName": "Anton", "lastName": "Korinek"},
    {"creatorType": "author", "firstName": "Joseph E.", "lastName": "Stiglitz"},
    {"creatorType": "editor", "firstName": "Ajay", "lastName": "Agrawal"},
    {"creatorType": "editor", "firstName": "Joshua", "lastName": "Gans"},
    {"creatorType": "editor", "firstName": "Avi", "lastName": "Goldfarb"}
  ],
  "bookTitle": "The economics of artificial intelligence: An agenda",
  "pages": "349-390",
  "date": "2019",
  "publisher": "University of Chicago Press",
  "DOI": "10.7208/chicago/9780226613475.003.0014"
}
```

Sin `bookTitle` el CSL imprime el capítulo como si fuera un libro (`quality` lo marca). Crossref a menudo **no trae los editores** de un capítulo: tomalos del sitio del editor o del libro.

### Ponencia (`conferencePaper`)

Plantilla:

> Apellido, A. (Año). *Título de la ponencia* [Ponencia]. Nombre del congreso, Ciudad, País. URL
>
> Si se publicó en actas con DOI: Apellido, A. (Año). Título. En E. Editor (Ed.), *Título de las actas* (pp. #–#). Editorial. https://doi.org/...

```json
{
  "itemType": "conferencePaper",
  "title": "Título de la ponencia",
  "creators": [{"creatorType": "author", "firstName": "Nombre", "lastName": "Apellido"}],
  "conferenceName": "Nombre del congreso",
  "proceedingsTitle": "Título de las actas (si existen)",
  "place": "Ciudad, País",
  "date": "AAAA",
  "pages": "#-#",
  "DOI": ""
}
```

### Tesis (`thesis`)

Plantilla:

> Apellido, A. (Año). *Título de la tesis* [Tesis doctoral, Universidad]. Repositorio. URL

```json
{
  "itemType": "thesis",
  "title": "Título de la tesis",
  "creators": [{"creatorType": "author", "firstName": "Nombre", "lastName": "Apellido"}],
  "thesisType": "Tesis doctoral",
  "university": "Universidad",
  "date": "AAAA",
  "url": "https://repositorio..."
}
```

### Informe (`report`)

> Apellido, A. o Institución. (Año). *Título del informe* (Informe N.º 123). Institución. URL

```json
{
  "itemType": "report",
  "title": "Título del informe",
  "creators": [{"creatorType": "author", "name": "Organización Internacional del Trabajo"}],
  "reportNumber": "123",
  "reportType": "Informe",
  "institution": "Organización Internacional del Trabajo",
  "date": "AAAA",
  "url": "https://..."
}
```

`institution` (no `publisher`). Si coincide con el autor, APA la omite en la entrada.

### Página web (`webpage`)

> Institución. (2024, 15 de marzo). *Título de la página*. Nombre del sitio. URL

```json
{
  "itemType": "webpage",
  "title": "Título de la página",
  "creators": [{"creatorType": "author", "name": "Institución"}],
  "websiteTitle": "Nombre del sitio",
  "date": "2024-03-15",
  "url": "https://...",
  "accessDate": "2026-10-02"
}
```

El `title` no debe incluir el nombre del sitio (`"Artículo - REMS - Revista..."` es un error frecuente del conector: va en `websiteTitle`). Un artículo de revista guardado como `webpage` debe pasar a `journalArticle`. `accessDate` solo se imprime en contenido que cambia.

### Dataset (`dataset`)

> Apellido, A. (Año). *Título del dataset* (Versión 1.2) [Conjunto de datos]. Repositorio. https://doi.org/...

```json
{
  "itemType": "dataset",
  "title": "Título del dataset",
  "creators": [{"creatorType": "author", "firstName": "Nombre", "lastName": "Apellido"}],
  "versionNumber": "1.2",
  "repository": "Zenodo",
  "date": "AAAA",
  "DOI": "10.5281/zenodo..."
}
```

`repository` (no `publisher`).

### Artículo de diario (`newspaperArticle`)

> Apellido, A. (2024, 5 de abril). Título de la nota. *La Nación*. URL

Campos: `publicationTitle`, `date` completa, `pages` o `section` si es impreso, `url` si es online.

### Preprint (`preprint`)

> Apellido, A. (Año). *Título* [Preprint]. arXiv. https://doi.org/10.48550/arXiv....

Campos: `repository` (arXiv, SocArXiv, SSRN), `archiveID` (`arXiv:2401.12345`), `DOI`. Si existe la versión publicada, citá esa.
