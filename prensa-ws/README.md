# prensa-ws

Descarga de ejemplares PDF de la [Biblioteca Virtual de Prensa Histórica](https://prensahistorica.mcu.es) (Ministerio de Cultura de España) **sin tope de cantidad**, con manifiesto auditable, reutilización de lo ya descargado y ritmo configurable.

Adaptada de los scripts de la clase 1 del curso de web scraping con IA (centra): `Scripts/clase1/clase1_scraping.py`. Se conserva la fuente `prensa` con su evidencia verificada; BNE, Biblioteca Digital de Andalucía y Archivo ABC no forman parte de esta skill.

## Qué hace

- Descarga el listado *números por mes* de una o varias publicaciones (`idPublicacion`, lista separada por comas o `@archivo.txt`) y extrae los ejemplares: enlaces `PDF` hacia `catalogo_imagenes/grupo.do?path=...`. Reconoce los **dos diseños reales** del sitio: el clásico (texto visible `PDF`, fecha en el texto anterior) y el de iconos (`data-analytics-grouptitle="PDF"`, fecha en `data-analytics-recordtitle`), descartando las copias JPEG que comparten el mismo `path`.
- Recorre la **paginación por año**: `numeros_por_mes.do` muestra un año por página y enlaza el resto con `&anyo=YYYY`; las páginas se siguen en orden ascendente y solo hasta alcanzar el objetivo, con un snapshot por año.
- `--n` fija el objetivo por publicación: cualquier entero ≥ 1, sin límite superior. Una corrida puede acumular miles de PDF en el mismo manifiesto.
- Valida cada respuesta como PDF real (firma `%PDF-` + apertura con `pypdf`) antes de moverla a disco (escritura atómica); SHA-256 en `manifest.csv`.
- Reutiliza archivos ya descargados (valideza + hash) sin volver a pedirlos; deduplica por `(fuente, id)` y por hash; las re-ejecuciones acumulan y descartan filas de página obsoletas de la publicación re-ejecutada.
- Ritmo configurable con `--pausa` (default 2 s entre peticiones; `0` desactiva). Es gestión operativa, no un límite de cantidad.
- Un bloqueo (401/403/429) o error aborta solo la publicación afectada y queda registrado; las demás continúan.

## Instalación

Python 3.10+:

```bash
python -m pip install -r assets/requirements.txt
```

En Windows, `truststore` hace que `requests` verifique TLS con los certificados del sistema (no se desactiva la verificación).

## Uso

```bash
# 3 ejemplares (default) de Pluma y Lápiz (idPublicacion=1002062) en ./datos
python assets/prensa_ws.py --salida datos

# Los 33 de esa publicación
python assets/prensa_ws.py --n 33 --salida datos

# Publicación multianual (Gazeta de México, 3 ejemplares en 1730 y 1732)
python assets/prensa_ws.py --n 100 --publicacion 1006238 --salida datos

# Miles: lista de publicaciones, una por línea en publicaciones.txt
python assets/prensa_ws.py --n 500 --publicacion @publicaciones.txt --pausa 1 --salida datos

# Dos publicaciones puntuales sin pausa entre peticiones
python assets/prensa_ws.py --n 2000 --publicacion 1002062,1006238 --pausa 0 --salida datos
```

El archivo de lista admite comentarios `#` y líneas vacías; los ids duplicados se ignoran.

| Opción | Valores | Comportamiento |
|---|---|---|
| `--n` | entero ≥ 1 (default 3) | Objetivo de ejemplares **por publicación**; sin tope superior. Si el listado tiene menos, descarga los disponibles y lo registra |
| `--publicacion` | id, `id1,id2`, `@archivo.txt` (default `1002062`) | Listados `numeros_por_mes.do?idPublicacion=` a procesar en la misma corrida |
| `--pausa` | segundos ≥ 0 (default 2) | Pausa entre peticiones HTTP; `0` = sin pausa |
| `--salida` | directorio (default `./datos`) | Estructura abajo |

Argumentos inválidos (`--n 0`, `--pausa -1`, id no numérico, archivo inexistente) abortan con código 2 antes de cualquier petición.

Estructura de salida:

```
datos/
├── manifest.csv                                        # registro por material, identidad (fuente, id)
├── resumen.csv                                         # una fila por publicación y corrida
└── prensa/
    ├── prensa_listado_numeros_por_mes_<id>.html         # snapshot de la página por defecto
    ├── prensa_listado_numeros_por_mes_<id>_<anyo>.html  # snapshot de cada página de año consultada
    └── pdf/
        └── prensa_<path>.pdf                           # ejemplares validados
```

Estados en `manifest.csv`: `descargado_pdf` (motivo `descargado_nuevo` o `reutilizado_existente_valido`), `omitido` (`duplicado_sha256`), `contenido_restringido`, `error`.

## Cobertura y límites técnicos

- **Sin límites autoimpuestos de volumen.** El único tope real es el catálogo: cada publicación expone los ejemplares que tiene.
- Publicaciones verificadas en el test real: *Pluma y Lápiz* (1002062) — 33 PDF de un solo año, 254,3 MB en 150 s con pausa 2 s; *Gazeta de México* (1006238) — 3 PDF en dos años (1730, 1732), diseño con iconos. Otras se marcan `publicacion_no_verificada_previamente` hasta correrlas.
- Planificación con las cifras observadas: ~4,5 s por ejemplar y ~7,7 MB de media con pausa 2 s → **~1000 ejemplares ≈ 1,3 h y ~7,7 GB**. `--pausa 0` elimina la espera, no el tiempo de descarga.
- Para encontrar `idPublicacion`: catálogo `es/publicaciones/listar_numeros.do` → `ficha_pub.do?idPublicacion=N`, o el enlace al listado desde la ficha de un título.
- Los PDF son escaneos: no hay extracción de texto ni OCR.
- Condiciones publicadas por el sitio (información para el operador, el script no las impone): `robots.txt` responde 404; la página de reproducciones permite descargas personales y pide contacto previo con info.bvph@cultura.gob.es para consultas/descargas masivas por carga técnica. User-Agent identificable con ese contacto en cada petición.

## Detalles del sitio y re-diagnóstico

Endpoints, selectores y evidencia: [`references/fuente.md`](references/fuente.md). Si el sitio cambia, la publicación afectada aborta con «el listado no contiene enlaces PDF con el formato esperado» en vez de adivinar; seguir esa guía para re-verificar.

## Tests

```bash
(cd prensa-ws && python -m unittest discover -s assets -p test_prensa_ws.py -v)
```

42 pruebas offline (fixtures HTML/PDF locales, sesión HTTP falsa): extracción en ambos diseños del sitio, paginación por año (seguido y corte perezoso), validación de argumentos, lista/archivo de publicaciones, pausa finita, validación y reutilización de PDF, duplicados, 403/429 en listado y en página de año, multi-publicación con aislamiento de fallos, manifiesto y limpieza de filas de página obsoletas. Sin red ni credenciales.
