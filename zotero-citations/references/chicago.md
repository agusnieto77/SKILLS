# Chicago 18.ª — reglas y uso con Zotero

Fuente: *The Chicago Manual of Style*, 18.ª ed. (2024), caps. 13–14, y su lista oficial de cambios ("What's New in the 18th Edition"). Zotero implementa ambas variantes en los CSL `chicago-notes-bibliography`, `chicago-shortened-notes-bibliography` y `chicago-author-date` (18.ª ed.); `cite_format.py render --style chicago-notes|chicago-author-date` los usa y agrega lo que Zotero no hace: rayas en rangos, sufijos a/b, localizadores y la forma narrativa.

## Qué variante

| Señal | Variante |
|---|---|
| El usuario dice "Chicago" a secas | La del manuscrito (`cite_audit --style chicago` la detecta); si no se distingue, **notas y bibliografía** (la forma habitual en historia y humanidades). |
| Citas `(Autor Año, página)` en el texto | Autor-fecha. |
| Llamadas de nota con referencias en las notas | Notas y bibliografía. |
| "Chicago 17", "Chicago 16", "Chicago-Deusto" | No es la oficial vigente: buscar el CSL (`cite_format styles --search chicago`) o tratarla como formato a medida (`custom-formats.md`). Chicago-Deusto es la adaptación española de la 16.ª ed. y difiere en detalles. |

## Reglas comunes de la 18.ª edición

1. **Autores en bibliografía o lista de referencias**: hasta 6 se listan todos; con más de 6, los 3 primeros + "et al." (13.23).
2. **Autores en notas y citas en el texto**: 1 o 2 se nombran; con 3 o más, el primero + "et al." (13.23, 13.107).
3. **Primer autor invertido** en la bibliografía (`Acha, Omar`); los siguientes en orden normal (`Nicolás Quiroga`). En notas, ningún nombre se invierte.
4. **Nombres de pila completos** tal como aparecen en la obra (Chicago no reduce a iniciales).
5. **"y" / "and"** entre autores, nunca "&" (salvo dentro del nombre de una editorial).
6. **Autor repetido**: se repite el nombre; Chicago ya no prefiere la raya de 3 em `———.` (13.72).
7. **Lugar de publicación** de libros: ya no es obligatorio (14.30).
8. **Rango de páginas de un capítulo** en la bibliografía: ya no es obligatorio (14.8); en artículos de revista sí.
9. **Mes o estación** de un número de revista: normalmente se puede omitir (13.26).
10. **Títulos**: en inglés, title case (las preposiciones de cinco letras o más van con mayúscula, 8.160); en español y otras lenguas, sentence case. Cursiva para obras independientes; comillas para partes (artículos, capítulos). En español, comillas latinas «» y “ ” dentro.
11. **DOI** como URL `https://doi.org/...`; si no hay DOI, URL o base de datos.
12. **Rangos** con raya (59–81) y **sin "p."** en notas y citas autor-fecha.

## Notas y bibliografía

**Nota completa** (primera cita de una obra cuando no hay bibliografía, o siempre si así lo pide la editorial):

> Omar Acha, «Lucha y organización: repensar en la Argentina la historia de la clase obrera y el primer peronismo», *Cuadernos del Ciesal*, n.º 14 (2015): 61.
>
> Omar Acha y Nicolás Quiroga, *Asociaciones y política en la Argentina del siglo veinte. Entre prácticas y expectativas* (Prometeo, 2015), 12.
>
> Omar Acha, «El sindicato de “canillitas” y el mosaico de lo público en la sociedad política peronista (1945–1955)», en *Asociaciones y política en la Argentina del siglo veinte*, ed. Omar Acha y Nicolás Quiroga (Prometeo, 2015), 85.

**Nota abreviada** (citas siguientes; con bibliografía, también la primera): apellido(s), título corto (hasta cuatro palabras, 13.32), página.

> Acha, «Lucha y organización», 61.
>
> Acha y Quiroga, *Asociaciones y política*, 12.

- El título corto sale del campo **Short Title** de Zotero; si está vacío, Zotero repite el título entero (`render` lo marca en `quality`). Corregilo en Zotero, no en el texto.
- **Ibid.**: Chicago prefiere la nota abreviada (13.37); *ibid.* sigue admitido. Nunca después de una nota con varias fuentes.
- Formas abreviadas válidas (13.37): autor + título (la regular), solo autor (si hay una sola obra de ese autor), solo título (obras sin autor).
- Varias fuentes en una nota: separadas por punto y coma.

**Bibliografía**: orden alfabético por apellido del primer autor; obras del mismo autor, por título (ignorando "A", "An", "The" iniciales, 13.100).

> Acha, Omar. «Lucha y organización: repensar en la Argentina la historia de la clase obrera y el primer peronismo». *Cuadernos del Ciesal*, n.º 14 (2015): 59–81.
>
> Acha, Omar, y Nicolás Quiroga. *Asociaciones y política en la Argentina del siglo veinte. Entre prácticas y expectativas*. Prometeo, 2015.

- La bibliografía puede incluir obras consultadas y no citadas: `C-UNCITED` es solo informativo.
- Sin bibliografía, la primera nota de cada obra debe ser completa (`C-FIRST-NOTE-SHORT`); `cite_audit` arma las referencias a partir de esas notas para poder seguir con Zotero.

## Autor-fecha

**Cita en el texto**: sin coma entre autor y año; página tras coma, sin "p.".

> (Acha y Quiroga 2015, 12) · (Acha 2015b, 61) · Acha y Quiroga (2015, 12) sostienen…

**Lista de referencias**: el año va después del autor, sin paréntesis; sufijos a/b para mismo autor y año.

> Acha, Omar. 2015a. «El sindicato de “canillitas” y el mosaico de lo público en la sociedad política peronista (1945–1955)». En *Asociaciones y política en la Argentina del siglo veinte*, editado por Omar Acha y Nicolás Quiroga. Prometeo.
>
> Acha, Omar. 2015b. «Lucha y organización: repensar en la Argentina la historia de la clase obrera y el primer peronismo». *Cuadernos del Ciesal*, n.º 14: 59–81.

## Diferencias con APA que más se confunden

| | APA 7 | Chicago 18 autor-fecha | Chicago 18 notas |
|---|---|---|---|
| Cita | (Acha, 2015, p. 61) | (Acha 2015, 61) | nota: Acha, «Lucha y organización», 61. |
| Año en la lista | (2015). tras el autor | 2015. tras el autor | al final de los datos de publicación |
| Nombres en la lista | iniciales | completos | completos |
| Conector | & | y / and | y / and |
| Hasta cuántos autores | 20 | 6 (si no, 3 + et al.) | 6 (si no, 3 + et al.) |
| Títulos de libros en inglés | sentence case | title case | title case |

## Reglas del auditor (`cite_audit --style chicago-*`)

| Regla | Severidad | Significado |
|---|---|---|
| `C-COMMA-EXTRA` | error | Autor-fecha con coma de APA: `(Acha, 2015)` → `(Acha 2015)`. |
| `C-LOCATOR-FORMAT` | warning | "p. 61" en autor-fecha: `(Acha 2015, 61)`. |
| `C-AMPERSAND` / `R-AMPERSAND` | warning | "&" entre autores. |
| `C-IBID` | info | Ibid. usado (preferida la nota abreviada). |
| `C-IBID-AMBIGUOUS` | error | Ibid. tras una nota con varias fuentes o como primera nota. |
| `C-TITLE-MISMATCH` | error | El autor está en la bibliografía pero el título corto no coincide con ninguna obra. |
| `C-FIRST-NOTE-SHORT` | error | Sin bibliografía, primera cita de una obra en forma abreviada. |
| `C-REPEATED-FULL` | warning | Nota completa repetida: usar la abreviada. |
| `R-WRONG-SYSTEM` | error | Entrada escrita en otro sistema (APA, o autor-fecha dentro de notas y viceversa). |
| `R-AUTHORS-LIMIT` | error / warning | Más de 6 autores listados, o "et al." sin exactamente 3. |
| `R-3EM-DASH` | warning | Raya de 3 em en vez de repetir el autor. |
| `D-NOTES-UNANCHORED` | info | No se encontraron llamadas de nota en el cuerpo (texto plano sin `[^n]`). |
| `C-OPCIT` | warning | `op. cit.` o `ibídem` con autor (formato hispano): Chicago usa la nota abreviada. |
| `C-OPCIT-AMBIGUOUS` | error | `op. cit.` cuando ya se citaron varias obras del autor: no se sabe cuál (se toma la última). |
| `C-OPCIT-UNRESOLVED` | error | `op. cit.` / `ibídem` con autor sin cita previa de ese autor. |
| `C-NOTE-INVERTED` | warning | Notas "Apellido, Nombre: Título" (formato hispano): Chicago usa orden normal en notas. |
| `C-TITLE-MARKUP` | warning | Título sin cursiva ni comillas; se infirió hasta la primera coma. |

### Notas en formato hispano

Muchas revistas latinoamericanas y españolas usan notas `Apellido, Nombre: *Título*, Ciudad, Editorial, año, p. X`, con `op. cit.`, `ibídem` (solo o con autor) y "Citado en:". El auditor las lee igual (autores invertidos, `op. cit.` resuelto a la última obra citada de ese autor, partes dentro de un libro como «Carta…» en Autor: *Libro*). Si el usuario quiere **conservar** ese formato, es un formato a medida: `--style chicago-notes --no-lint` (cruce sin reglas de Chicago) y plantilla para reescribir. Si quiere pasarlo a Chicago o APA, se audita contra esa norma y se reescribe desde Zotero.

En autor-fecha, un paréntesis de prosa con lugar y año ("(Buenos Aires 1932)") tiene forma de cita y puede salir como `C-ORPHAN`: revisalo antes de reportarlo.
