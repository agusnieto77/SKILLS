# Prensa Histórica · mapa del sitio y evidencia verificada

Fuente: <https://prensahistorica.mcu.es> (Biblioteca Virtual de Prensa Histórica, Ministerio de Cultura de España). Lo documentado aquí fue observado en la clase 1 del curso de web scraping y re-verificado contra el sitio en el test real de prensa-ws 1.2 (2026-10-26).

## Endpoints conocidos

| Elemento | URL / patrón | Verificado |
|---|---|---|
| Ficha de título catalográfico | `https://prensahistorica.mcu.es/es/consulta/registro.do?id=<ID_REGISTRO>` | Sí (id=1029158) |
| Ficha de publicación con enlace al listado | `https://prensahistorica.mcu.es/es/publicaciones/ficha_pub.do?idPublicacion=<ID_PUBLICACION>` | Sí (1006238) |
| Catálogo de publicaciones / calendario | `https://prensahistorica.mcu.es/es/publicaciones/listar_numeros.do` (admite `?busq_anyo=YYYY`) | Sí (home → «Calendario») |
| Listado de ejemplares por mes | `.../numeros_por_mes.do?idPublicacion=<ID>` | Sí (1002062, 1006238) |
| Listado de un año concreto | `.../numeros_por_mes.do?idPublicacion=<ID>&anyo=<YYYY>` | Sí (1730, 1732) |
| Archivo PDF de un ejemplar | `https://prensahistorica.mcu.es/es/catalogo_imagenes/grupo.do?path=<ID_EJEMPLAR>` | Sí (2000857258-60, 8476519-21) |
| Condiciones de reproducción | `https://prensahistorica.mcu.es/es/cms/elemento.do?id=estaticos/paginas/REPRODUCCIONES.html` | Sí |

La portada `https://prensahistorica.mcu.es/` redirige a `es/inicio/inicio.do`; de ahí cuelgan los enlaces de navegación anteriores.

## Dos diseños reales del listado

**Clásico** (*Pluma y Lápiz*, 1002062): ancla con texto visible exactamente `PDF`; el nodo de texto anterior aporta `Año I Número 1 - 16 Marzo 1893`. Enlaces «Copia digital», idioma y ficha se descartan.

**Con iconos** (*Gazeta de México*, 1006238): las anclas no tienen texto útil. Marcadores reales:

- `data-analytics-grouptitle="PDF"` (o `title` que empieza con `PDF`) → archivo.
- `data-analytics-recordtitle="Gazeta de México: Número 36 - 1730 noviembre"` → título y fecha.
- `data-analytics-recordid="NUM01001329140"` → id de registro (no usado; el id estable del archivo sigue siendo `path`).
- La copia JPEG comparte el mismo `path` con `data-analytics-grouptitle="Copia en JPEG"` → **excluir**, o se duplicaría cada ejemplar.

`extract_prensa_items` reconoce ambos. `grupo.do?path=...` devuelve el PDF directamente aunque la URL no termine en `.pdf`; no parsear su cuerpo como HTML.

## Paginación por año

`numeros_por_mes.do` muestra **un año por página**. Los demás años aparecen como enlaces `Año YYYY` → `numeros_por_mes.do?idPublicacion=<ID>&anyo=<YYYY>`; el año mostrado figura como texto, no como enlace. Publicaciones de un solo año no tienen enlaces.

Comportamiento implementado: se consulta la página por defecto y luego las páginas de año en orden ascendente, **de forma perezosa**: se detiene al alcanzar `--n` y guarda un snapshot por página (`prensa_listado_numeros_por_mes_<pub>_<anyo>.html`). Un 401/403/429 en una página de año registra `prensa_<pub>_anyo_<YYYY>` como `contenido_restringido`, conserva lo ya recolectado y sigue con la descarga.

## Publicaciones verificadas

| idPublicacion | Título | Cobertura observada | Diseño |
|---|---|---|---|
| 1002062 | *Pluma y Lápiz : periódico ilustrado* (Barcelona, 1893) | **33 PDF**, números 1–34 salvo el 16 | clásico, un año |
| 1006238 | *Gazeta de México* | **3 PDF**: nº 36–37 (nov–dic 1730) y nº 52 (mar 1732) | iconos, dos años |

Otras publicaciones usan el mismo tipo de página y se marcan `publicacion_no_verificada_previamente` hasta correrlas. Para encontrar `idPublicacion`: catálogo `listar_numeros.do` → `ficha_pub.do?idPublicacion=N`, o el enlace al listado desde la ficha de un título.

## Rendimiento y capacidad observados (test real 2026-10-26)

- 33 PDF de 1002062: **254,3 MB en 150 s** con pausa por defecto (2 s) ≈ **4,5 s por ejemplar**, ~7,7 MB de media, 0 errores.
- Re-ejecución sobre lo descargado: 3/3 reutilizados sin peticiones de PDF.
- Estimación para planificar: ~1000 ejemplares ≈ 1,3 h y ~7,7 GB con pausa 2 s (sin contar el tiempo de bajada, que dominó en el test). `--pausa` solo controla la espera entre peticiones.

## Condiciones publicadas por el sitio (información del operador)

- `robots.txt`: respondió **HTTP 404**. No hay protocolo de rastreo que cumplir.
- [Condiciones de reproducción](https://prensahistorica.mcu.es/es/cms/elemento.do?id=estaticos/paginas/REPRODUCCIONES.html): permiten descargas personales; piden contacto previo con **info.bvph@cultura.gob.es** para consultas/descargas masivas por carga técnica.
- Postura de la skill: **sin topes autoimpuestos de cantidad**. Lo anterior queda documentado como información; la decisión de ritmo y volumen es del operador. La gestión interna (pausa entre peticiones, reutilización por hash, reanudable por manifiesto) existe por robustez, no como límite.
- Licencias: la ficha de cada título declara la suya (CC BY 4.0 en 1002062). Comprobar la ficha antes de redistribuir material de otra publicación.

## Parámetros operativos del script

| Parámetro | Valor |
|---|---|
| Pausa entre peticiones | `--pausa`, default 2 s; `0` = sin pausa |
| Timeout | 30 s |
| User-Agent | `PrensaWsSkill/1.2 (contacto: info.bvph@cultura.gob.es)` |
| TLS | Verificado siempre; en Windows usa `truststore` (certificados del sistema). Nunca `verify=False` |
| HTTP 401/403/429 | Aborta esa publicación (o esa página de año) como `contenido_restringido`, registra `Retry-After` y continúa con las demás |

## Validación de archivos y manifiesto

- Firma `%PDF-` + apertura con `pypdf` antes de mover a destino (escritura atómica vía `.part`).
- SHA-256 en `manifest.csv`; reutilización de archivos válidos previos sin nueva descarga; igual hash distinto id → `omitido` (`duplicado_sha256`).
- Identidad `(fuente, id)`; al re-ejecutar una publicación se descartan sus filas de página obsoletas (`prensa_<pub>_preflight|error|anyo_<YYYY>`), para que un fallo transitorio viejo no contradiga descargas exitosas.

## Si el sitio cambia (re-diagnóstico)

1. Pedir el listado con `curl -A "PrensaWsSkill/1.2" "<url numeros_por_mes>"` y guardar el HTML.
2. Confirmar anclas PDF por texto `PDF` **o** por `data-analytics-grouptitle="PDF"`, y que apunten a `grupo.do?path=`.
3. Confirmar que un enlace `grupo.do` devuelve `Content-Type: application/pdf`.
4. Revisar enlaces `Año YYYY` (`&anyo=`) si la publicación abarca varios años.
5. Si algo difiere, actualizar selectores/regex de `extract_prensa_items`/`extract_year_urls` y esta referencia antes de reintentar. La publicación aborta con «el listado no contiene enlaces PDF con el formato esperado» en ese caso.

## Historial de verificación

- Clase 1 (curso web scraping + IA, centra): tres PDF de *Pluma y Lápiz* descargados y validados (números 1–3, 7 páginas cada uno, hashes distintos, portada examinada visualmente). Evidencia original en el material del curso, `Scripts/clase1/RESULTADOS.md` y `diagnostico.md`.
- prensa-ws 1.0 (2026-10-26): adaptación a skill; smoke real de 1 ejemplar.
- prensa-ws 1.1 (2026-10-26): sin topes de cantidad, pausa configurable y multi-publicación.
- prensa-ws 1.2 (2026-10-26): test real completo — 33/33 PDF de 1002062 (254,3 MB, 150 s) y 3/3 de 1006238 en dos años; reutilización verificada; descubiertos y soportados el diseño con iconos y la paginación por año; corregidas las filas de página obsoletas en el manifiesto.
