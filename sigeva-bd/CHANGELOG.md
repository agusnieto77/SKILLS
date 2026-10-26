# Changelog

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
