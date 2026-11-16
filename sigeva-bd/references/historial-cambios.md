# Historial de cambios detectados en SIGEVA

> Lo agrega `sigeva_bd.py verificar`. Cada entrada compara el sitio real con la linea base
> anterior. Lo **critico** rompe el cargador: no se adopta solo y hay que corregir el codigo.

## 2026-11-12T21:53:11+00:00 — 14.11.24.12 → 14.11.24.12

Resumen: critico 0, alto 4, medio 2, bajo 0. Linea base actualizada.

- **alto** `fuentesFinanciamientoAction.do` campo-valores: otrosFinanciamientos: ['1255716', '739940', '199709', '1255719', '824791', '1255725', '1255717', '1326174', '493898', '1538942'] -> ['127412', '1255716', '739940', '199709', '1255719', '824791', '1255725', '1255717', '1326174', '493898']
- **alto** `fuentesFinanciamientoAction.do?idGrupo=1&idMenu=2709&idModulo=3` campo-valores: otrosFinanciamientos: ['1255716', '739940', '199709', '1255719', '824791', '1255725', '1255717', '1326174', '493898', '1538942'] -> ['127412', '1255716', '739940', '199709', '1255719', '824791', '1255725', '1255717', '1326174', '493898']
- **alto** `grupoInvestigacion.do` campo-valores: seleccionadas: ['422795', '431105', '422703', '422761', '422763', '431401', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707'] -> ['422795', '422703', '422761', '422763', '431401', '423121', '432394', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707']
- **alto** `grupoInvestigacion.do?idGrupo=1&idMenu=2707&idModulo=3` campo-valores: seleccionadas: ['422795', '431105', '422703', '422761', '422763', '431401', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707'] -> ['422795', '422703', '422761', '422763', '431401', '423121', '432394', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707']
- **medio** `fuentesFinanciamientoAction.do` accion-eliminada: financiamientoCYTProyectoFuente.do?accion=ver&id=N&tipoFinanciamientoId=11
- **medio** `fuentesFinanciamientoAction.do?idGrupo=1&idMenu=2709&idModulo=3` accion-eliminada: financiamientoCYTProyectoFuente.do?accion=ver&id=N&tipoFinanciamientoId=11

## 2026-11-12T13:19:53+00:00 — 14.11.24.12 → 14.11.24.12

Resumen: critico 0, alto 2, medio 0, bajo 0. Linea base actualizada.

- **alto** `grupoInvestigacion.do` campo-valores: seleccionadas: ['422795', '431105', '422703', '422761', '422763', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707'] -> ['422795', '431105', '422703', '422761', '422763', '431401', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707']
- **alto** `grupoInvestigacion.do?idGrupo=1&idMenu=2707&idModulo=3` campo-valores: seleccionadas: ['422795', '431105', '422703', '422761', '422763', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707'] -> ['422795', '431105', '422703', '422761', '422763', '431401', '423121', '431343', '420837', '422657', '422729', '423434', '426964', '431150', '422707']

## 2026-11-12T05:23:20+00:00 — 14.11.24.6 → 14.11.24.12

Resumen: critico 0, alto 0, medio 1, bajo 0. Linea base actualizada.

- **medio** `-` version: 14.11.24.6 -> 14.11.24.12
