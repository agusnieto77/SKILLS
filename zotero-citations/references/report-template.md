# Reporte de auditoría — estructura obligatoria

Llená cada sección con los JSON de los scripts; no recalcules a mano. Secciones sin filas: escribí "Sin casos". En entregables `.docx`, usá estilos Word reales (títulos, tablas), no Markdown literal.

```
# Reporte de auditoría bibliográfica
- Manuscrito: <título>
- Norma aplicada: <APA 7 | Chicago 18.ª notas | Chicago 18.ª autor-fecha | CSL <id> | plantilla a medida> · Cómo se eligió: <pedida | detectada (confianza) | por defecto | ejemplo del usuario> · Idioma: <es | en>
- Formato a medida (si aplica): estilo base o plantilla, preguntas hechas al usuario y sus respuestas
- Fecha: <YYYY-MM-DD>
- Biblioteca Zotero: <user|group> <ID> · Lectura: <local | web>
- Manuscrito entregado: <archivo> · Control de cambios: activado · Autor de las revisiones: <--author>

## Vigencia y trazabilidad de evidencia
- Fecha de comprobación (UTC): <evidence.checked_at>
- SHA-256 del manuscrito original: <evidence.binding.manuscript_sha256>
- Bibliografías `.bib`: <archivo y SHA-256 de cada entrada de evidence.binding.bibliographies>
- SHA-256 de audit.json / match.json: <hashes de bytes registrados por source_check>
- Cobertura de parseo: <completa | incompleta, con cada advertencia y ubicación; no afirmar auditoría completa si hubo omisiones>
- Resultados reutilizados: <current / stale y changed_inputs; un juicio stale debe revisarse de nuevo>

| Ocurrencia (id) | Ubicación (archivo, párrafo/span o línea/columna, nota) | itemKey / versión | attachmentKey / versión | SHA-256 texto fuente | SHA-256 contexto | Comprobado UTC | Vigencia |
|-----------------|------------------------------------------------------|-------------------|-------------------------|----------------------|------------------|----------------|----------|
(Copiar de `results[].evidence.binding` y `checked_at`; valores ausentes = no disponibles, no inferirlos. Cada juicio queda ligado a esa ocurrencia exacta: no trasladarlo a otra oración ni a otro uso del mismo ítem.)

## Control de cambios
- Inserciones I · Eliminaciones D · Cambios de cursiva F · Párrafos insertados / eliminados P / Q · Comentarios C (de `docx_revise.py summary`)
- Ninguna revisión está aceptada: el autor revisa cada una en Word (Revisar → Aceptar / Rechazar). Rechazar todo devuelve el original.
- Párrafos que no se pudieron revisar (revisiones pendientes, campos vivos de Zotero): <lista o "Sin casos">

## ⛔ Integridad de las fuentes
| # | Referencia | DOI | Estado | Aviso (tipo, fecha, DOI del aviso) | Decisión del autor |
|---|------------|-----|--------|------------------------------------|--------------------|
(Solo `retracted`, `expression-of-concern`, `corrected`, `new-version`. Va primero. Indicar cuántas obras no se pudieron revisar por no tener DOI.)

## Resumen
- Referencias totales: N
- Citas en el texto: C (en notas al pie: F)
- Encontradas en Zotero sin cambios: X
- Encontradas con diferencias (resueltas / pendientes): D / P
- Creadas en Zotero tras validación externa: Y
- Corregidas en Zotero (update): U
- Marcadas para revisión manual: Z
- Citas huérfanas (en texto, sin entrada): H
- Entradas no citadas (en lista, sin uso): K
- Fuentes retractadas / con aviso de preocupación: R / E
- Citas cotejadas con texto completo: T de C (sin texto completo: S)
- Citas textuales con problemas: Q · Copia sin comillas: V

## Ajustes de formato aplicados
| # | Entrada | Cambio | Regla |
|---|---------|--------|-------|
(Regla = id del finding: R-DOI-FORMAT, C-ETAL-REQUIRED, ...)

## Coincidencias con Zotero
| # | Entrada | itemKey | Estado de match | Diferencias y decisión |
|---|---------|---------|-----------------|------------------------|

## Nuevas fuentes agregadas a Zotero
| # | itemKey | Apellido, año | Título | Fuentes de validación |
|---|---------|---------------|--------|-----------------------|
(Fuentes = las que dieron `validated`, p. ej. "Crossref + OpenAlex"; o la URL de la segunda fuente manual)

## Correcciones de datos en Zotero
| # | itemKey | Campo | Antes | Después | Motivo |
|---|---------|-------|-------|---------|--------|

## Calidad de datos en Zotero (sin corregir)
| # | itemKey | Problema (`quality` / `warnings` de render) | Acción sugerida |
|---|---------|---------------------------------------------|-----------------|

## Citas que requieren revisión manual
| # | Cita en texto | Problema detectado | Sugerencia |
|---|---------------|--------------------|------------|

## Fidelidad: citas textuales
| # | Cita | Estado | Manuscrito vs fuente | Página (localizador / fuente) | Corrección propuesta |
|---|------|--------|----------------------|-------------------------------|----------------------|
(Solo las que no son `exact`/`exact-with-edits` o tienen página `inconsistent`.)

## Fidelidad: copia sin comillas
| # | Cita | Frase copiada (palabras) | Pasaje de la fuente, página | Corrección propuesta |
|---|------|--------------------------|-----------------------------|----------------------|

## Fidelidad: respaldo de afirmaciones
| # | Cita | Afirmación | Veredicto | Pasaje de la fuente, página | Sugerencia |
|---|------|------------|-----------|-----------------------------|------------|
(Veredicto: fiel / exagerada / parcial / sin respaldo / no verificable. Solo si el usuario pidió verificar fidelidad. Listar aparte las citas `no-fulltext`.)
(Si se conserva un juicio del agente, agregarlo como `results[].judgement` con veredicto, pasaje y página, sin modificar su binding. `--previous` solo lo recupera con inputs idénticos y versiones conocidas; `previous_judgement` es histórico obsoleto, nunca un veredicto vigente.)

## Metadatos faltantes / [verificar]
| # | Referencia | Campo faltante | Acción sugerida |
|---|------------|----------------|-----------------|
(En `.docx` van además como comentario de Word sobre la entrada.)

## Fuentes archivísticas
| # | Referencia | Repositorio | Signatura | URL | Estado |
|---|------------|-------------|-----------|-----|--------|

## Log de operaciones Zotero
| Timestamp (UTC) | Método | Endpoint | itemKey(s) | Resultado |
|-----------------|--------|----------|------------|-----------|
(Copiar del campo `log` de create/update/trash; las lecturas se resumen en una fila por comando: match, render)
```
