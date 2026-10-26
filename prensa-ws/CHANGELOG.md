# Changelog

## 1.2.0 — 2026-10-26

Ajustes a partir de un test real completo contra el sitio (33/33 PDF de 1002062, 254,3 MB en 150 s; 3/3 de 1006238 en dos años; reutilización y limpieza verificadas).

- **Segundo diseño del listado**: además del ancla con texto `PDF` (diseño clásico), se reconocen los enlaces de icono (`data-analytics-grouptitle="PDF"`, `title` que empieza con `PDF`) y la fecha en `data-analytics-recordtitle` (`Gazeta de México: Número 36 - 1730 noviembre`). Las copias JPEG que comparten `path` se descartan.
- **Paginación por año**: `numeros_por_mes.do` muestra un año por página y enlaza el resto con `&anyo=YYYY`; se siguen en orden ascendente y solo hasta alcanzar `--n`. Snapshot por año. Un 401/403/429 en una página de año registra `prensa_<pub>_anyo_<YYYY>` y conserva lo recolectado.
- **Manifiesto**: al re-ejecutar una publicación se descartan sus filas de página obsoletas (`prensa_<pub>_preflight|error|anyo_<YYYY>`); antes, un error transitorio quedaba contradiciendo descargas exitosas.
- Motivo de detención informa páginas de año consultadas y páginas restringidas. User-Agent 1.2.
- Tests: 42 (nuevos: diseño con iconos, URLs de año, seguimiento y corte perezoso de años, 429 en página de año, limpieza de filas obsoletas).

## 1.1.1 — 2026-10-26

Mantenimiento posterior al Judgment Day (`validation/2026-10-26-juicio-final.md`); ambos hallazgos confirmados por los dos jueces, ninguno severo.

- README raíz: el comando First run usaba `--modo`, eliminado en 1.1.0; corregido a `--n 1`.
- `validate_pausa` rechaza `nan`/`inf` con `math.isfinite`; antes pasaban y el primer `time.sleep` del bucle lanzaba ValueError/OverflowError tras pedir el listado. Tests: 35 (regresión de pausa no finita y rechazo en CLI antes de cualquier petición).
- Quedan como info para iteración futura: motivo de detención cuando el faltante proviene de errores/omisiones, y neutralización de fórmulas CSV en campos del manifiesto.

## 1.1.0 — 2026-10-26

Sin topes autoimpuestos de cantidad; la gestión de descargas (pausas, lotes) queda como buena práctica operativa, no como límite.

- `--n` acepta cualquier entero ≥ 1 por publicación (antes: `prueba` 1–10 y `muestra` 100–200 frenada).
- Eliminados `--modo`, el bloqueo de `muestra` y `BULK_GATE_MOTIVO`.
- `--pausa SEG` configurable (default 2 s; `0` = sin pausa).
- Multi-publicación por corrida: `--publicacion id1,id2` o `@archivo.txt` (un id por línea, comentarios `#`, dedupe). Un 401/403/429 o error aborta solo esa publicación; las demás continúan sobre el mismo manifiesto.
- Estado de acceso normal: `abierto` (antes `abierto_para_muestra_pequena`). User-Agent a 1.1.
- Las condiciones publicadas por el sitio se mantienen documentadas en `references/fuente.md` como información del operador; el script no las impone.
- Suite: 34 tests (multi-publicación, argumentos sin tope, aislamiento de fallos).

## 1.0.0 — 2026-10-26

Skill inicial.

- `assets/prensa_ws.py`: CLI adaptado de `Scripts/clase1/clase1_scraping.py` (curso web scraping + IA, centra), reducido a la fuente Prensa Histórica.
  - Generaliza el listado con `--publicacion` (default 1002062, la única con cobertura verificada).
  - `--modo prueba` acepta 1–10 ejemplares (la clase 1 fijaba 3); `--modo muestra` (100–200) sigue frenado por el acuerdo institucional pendiente, sin flag de autoautorización.
  - Manifiesto/summary idénticos en columnas a la clase 1 (interopera con carpetas `datos` existentes); I/O CSV con stdlib (sin pandas).
  - Corregido el bloque de funciones duplicadas del original (`extract_prensa_items`, `fetch_listing_snapshot`, descarga de PDF): queda una sola versión, con manejo de 401/403/429 y `Retry-After`.
  - Identidad de reutilización `(fuente, id)` sin la URL de descubrimiento.
  - Salida por defecto `./datos` (directorio de trabajo) en vez de junto al script.
- `assets/test_prensa_ws.py`: 27 pruebas offline (sin red) con sesión falsa y PDFs generados.
- `references/fuente.md`: mapa del sitio, selectores, condiciones de uso y procedimiento de re-diagnóstico.
- Registro en `README.md` raíz del repo y en `.github/workflows/tests.yml`.

Basado en la evidencia de la clase 1: tres PDF reales de *Pluma y Lápiz* descargados y validados; diagnóstico honesto de BNE/Andalucía/ABC (fuera de alcance aquí).
