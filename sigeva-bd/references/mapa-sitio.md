# Mapa del Banco de Datos de SIGEVA

> Archivo generado por `sigeva_bd.py mapear --aceptar` / `verificar --aceptar`. No editar a mano.

- Versión de SIGEVA: **14.11.24.6**
- Capturado: 2026-10-25T18:08:46+00:00
- Pantallas: 123 · omitidas por seguridad: 149 · errores: 0
- Recorrido completo: sí

Solo estructura: nombres de campo, tipos, etiquetas y cantidad de opciones. Los valores de la persona no se registran.

## Contrato del cargador

Lo que `cargar` necesita encontrar. `verificar` marca como **crítico** cualquier faltante.

| Uso | Pantalla | Campos | Botones | Tablas |
|---|---|---|---|---|
| inventario y verificacion de altas | `bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica` | 0 |  | articulo, congresoPublicado, capituloLibro, libro |
| alta de articulo: precarga | `bcoPrecargarArticulo.do?action=Nuevo` | 0 | Omitir |  |
| alta de articulo | `bcoPrecargarArticulo.do?action=Nuevo#omitir` | 26 | Buscar por ISSN / e-ISSN, Buscar por Nombre, Guardar, Volver, autorNuevo |  |
| alta de trabajo en evento | `bcoProduccionListaPublicacionCongreso.do?action=Nuevo&publicado=1` | 25 | Guardar, Volver, autorNuevo |  |
| alta de parte de libro | `bcoProduccionListaPublicacionCapituloLibro.do?action=Nuevo` | 26 | Guardar, Volver, autorNuevo, compiladorNuevo |  |
| alta de libro | `bcoProduccionLibroPublicacion.do?action=Nuevo` | 21 | Guardar, Volver, autorNuevo |  |

## Índice de pantallas

| Pantalla | Tipo | Título | Formularios | Campos | Tablas |
|---|---|---|---|---|---|
| [`bcoABMRoles.do?accion=nuevo`](#bcoabmrolesdoaccionnuevo) | formulario | SIGEVA | 1 | 10 | 0 |
| [`bcoActividadAmbitoNoAcademico.do?accion=Nuevo&tipoActividad=5`](#bcoactividadambitonoacademicodoaccionnuevotipoactividad5) | formulario | SIGEVA | 1 | 37 | 1 |
| [`bcoActividadCoordinacion.do?accion=nuevo&tipoActividad=9`](#bcoactividadcoordinaciondoaccionnuevotipoactividad9) | formulario | SIGEVA | 1 | 82 | 3 |
| [`bcoActividadEvaluacionInstitucional.do?accion=Nuevo`](#bcoactividadevaluacioninstitucionaldoaccionnuevo) | formulario | SIGEVA | 1 | 34 | 1 |
| [`bcoActividadEvaluacionLista.do?idGrupo=5&idMenu=1462&idModulo=5`](#bcoactividadevaluacionlistadoidgrupo5idmenu1462idmodulo5) | lista | SIGEVA | 1 | 15 | 5 |
| [`bcoActividadEvaluacionOtroTipo.do?accion=Nuevo`](#bcoactividadevaluacionotrotipodoaccionnuevo) | formulario | SIGEVA | 1 | 26 | 0 |
| [`bcoActividadEvaluacionPersonalCyT.do?accion=Nuevo`](#bcoactividadevaluacionpersonalcytdoaccionnuevo) | formulario | SIGEVA | 1 | 27 | 0 |
| [`bcoActividadEvaluacionProyecto.do?accion=Nuevo`](#bcoactividadevaluacionproyectodoaccionnuevo) | formulario | SIGEVA | 1 | 27 | 1 |
| [`bcoActividadEvaluacionRevista.do?accion=Nuevo&tipoActividadEvaluacionId=3`](#bcoactividadevaluacionrevistadoaccionnuevotipoactividadevaluacionid3) | formulario | SIGEVA | 1 | 30 | 0 |
| [`bcoActividadEvaluacionRevista.do?accion=Nuevo&tipoActividadEvaluacionId=6`](#bcoactividadevaluacionrevistadoaccionnuevotipoactividadevaluacionid6) | formulario | SIGEVA | 1 | 32 | 0 |
| [`bcoActividadMembresias.do?accion=nuevo&tipoActividad=7`](#bcoactividadmembresiasdoaccionnuevotipoactividad7) | formulario | SIGEVA | 1 | 75 | 0 |
| [`bcoActividadNormalizacion.do?accion=Nuevo&tipoActividad=4`](#bcoactividadnormalizaciondoaccionnuevotipoactividad4) | formulario | SIGEVA | 1 | 33 | 1 |
| [`bcoActividadOtraActividadCYT.do?accion=Nuevo&tipoActividad=6`](#bcoactividadotraactividadcytdoaccionnuevotipoactividad6) | formulario | SIGEVA | 1 | 31 | 0 |
| [`bcoActividadProduccion.do?accion=Nuevo&tipoActividad=3`](#bcoactividadproducciondoaccionnuevotipoactividad3) | formulario | SIGEVA | 1 | 57 | 3 |
| [`bcoActividadRedes.do?accion=nuevo&tipoActividad=8`](#bcoactividadredesdoaccionnuevotipoactividad8) | formulario | SIGEVA | 1 | 78 | 1 |
| [`bcoActividadSistemaAltaComplejidad.do?accion=Nuevo&tipoActividad=2`](#bcoactividadsistemaaltacomplejidaddoaccionnuevotipoactividad2) | formulario | SIGEVA | 1 | 49 | 2 |
| [`bcoAjustes.do?idGrupo=2&idMenu=1480&idModulo=2`](#bcoajustesdoidgrupo2idmenu1480idmodulo2) | menu | SIGEVA | 1 | 2 | 0 |
| [`bcoBeca.do?accion=nuevo`](#bcobecadoaccionnuevo) | formulario | SIGEVA | 1 | 31 | 0 |
| [`bcoCArchivosAdjuntos.do?idGrupo=7&idMenu=1476&idModulo=7`](#bcocarchivosadjuntosdoidgrupo7idmenu1476idmodulo7) | menu | SIGEVA | 2 | 2 | 1 |
| [`bcoCargoDocenteLista.do?idGrupo=4&idMenu=1455&idModulo=4`](#bcocargodocentelistadoidgrupo4idmenu1455idmodulo4) | lista | SIGEVA | 1 | 13 | 4 |
| [`bcoCargoDocenteNivelBasicoMedio.do?accion=Nuevo`](#bcocargodocentenivelbasicomediodoaccionnuevo) | formulario | SIGEVA | 1 | 24 | 0 |
| [`bcoCargoDocenteNivelCapacitacion.do?accion=Nuevo`](#bcocargodocentenivelcapacitaciondoaccionnuevo) | formulario | SIGEVA | 1 | 25 | 0 |
| [`bcoCargoDocenteNivelSuperior.do?accion=Nuevo`](#bcocargodocentenivelsuperiordoaccionnuevo) | formulario | SIGEVA | 1 | 33 | 2 |
| [`bcoCargoDocenteNivelTerciario.do?accion=Nuevo`](#bcocargodocentenivelterciariodoaccionnuevo) | formulario | SIGEVA | 1 | 24 | 0 |
| [`bcoCargoGestionAction.do?accion=Nuevo`](#bcocargogestionactiondoaccionnuevo) | formulario | SIGEVA | 1 | 15 | 0 |
| [`bcoCargoGestionLista.do`](#bcocargogestionlistado) | lista | SIGEVA | 1 | 4 | 1 |
| [`bcoCargoGestionLista.do?idGrupo=4&idMenu=1457&idModulo=4`](#bcocargogestionlistadoidgrupo4idmenu1457idmodulo4) | lista | SIGEVA | 1 | 4 | 1 |
| [`bcoCargoIDIncentivos.do?action=Nuevo`](#bcocargoidincentivosdoactionnuevo) | formulario | SIGEVA | 1 | 19 | 0 |
| [`bcoCargoIDLista.do?idGrupo=4&idMenu=1456&idModulo=4`](#bcocargoidlistadoidgrupo4idmenu1456idmodulo4) | lista | SIGEVA | 1 | 10 | 3 |
| [`bcoCargoIDOrganizacionCT.do?action=Nuevo`](#bcocargoidorganizacionctdoactionnuevo) | formulario | SIGEVA | 1 | 23 | 0 |
| [`bcoCargoIDOtraOrganizacion.do?action=Nuevo`](#bcocargoidotraorganizaciondoactionnuevo) | formulario | SIGEVA | 1 | 19 | 0 |
| [`bcoCargoOtroAction.do?accion=Nuevo`](#bcocargootroactiondoaccionnuevo) | formulario | SIGEVA | 1 | 14 | 0 |
| [`bcoCargoOtroLista.do`](#bcocargootrolistado) | lista | SIGEVA | 1 | 4 | 1 |
| [`bcoCargoOtroLista.do?idGrupo=4&idMenu=1458&idModulo=4`](#bcocargootrolistadoidgrupo4idmenu1458idmodulo4) | lista | SIGEVA | 1 | 4 | 1 |
| [`bcoCompartirFormulario.do?idGrupo=0&idMenu=1478&idModulo=1`](#bcocompartirformulariodoidgrupo0idmenu1478idmodulo1) | formulario | SIGEVA | 1 | 7 | 0 |
| [`bcoCompartirFormulario.do?idGrupo=0&idMenu=814&idModulo=1`](#bcocompartirformulariodoidgrupo0idmenu814idmodulo1) | formulario | SIGEVA | 1 | 7 | 0 |
| [`bcoDatoAcademico.do?idGrupo=7&idMenu=1475&idModulo=7`](#bcodatoacademicodoidgrupo7idmenu1475idmodulo7) | menu | Página de Errores | 1 | 3 | 0 |
| [`bcoDatoInvestigacion.do?accion=nuevo`](#bcodatoinvestigaciondoaccionnuevo) | formulario | DATOS DE INVESTIGACIÓN | 1 | 39 | 12 |
| [`bcoDatoPersonalDireccion.do?idGrupo=2&idMenu=1451&idModulo=2&tipoDir=residencial`](#bcodatopersonaldirecciondoidgrupo2idmenu1451idmodulo2tipodirresidencial) | formulario | SIGEVA | 1 | 27 | 0 |
| [`bcoDatoPersonalDireccion.do?idGrupo=2&idMenu=1452&idModulo=2&tipoDir=laboral`](#bcodatopersonaldirecciondoidgrupo2idmenu1452idmodulo2tipodirlaboral) | formulario | SIGEVA | 1 | 29 | 0 |
| [`bcoDatoPersonalIdentificacion.do?idGrupo=2&idMenu=1450&idModulo=2`](#bcodatopersonalidentificaciondoidgrupo2idmenu1450idmodulo2) | formulario | SIGEVA | 1 | 19 | 0 |
| [`bcoDatosInvestigacionLista.do?idGrupo=9&idMenu=2535&idModulo=9`](#bcodatosinvestigacionlistadoidgrupo9idmenu2535idmodulo9) | lista | DATOS DE INVESTIGACIÓN BANCO DE DATOS | 1 | 1 | 1 |
| [`bcoExperticia.do?idGrupo=2&idMenu=1465&idModulo=2`](#bcoexperticiadoidgrupo2idmenu1465idmodulo2) | formulario | SIGEVA | 1 | 20 | 4 |
| [`bcoExtensionDivulgacionArtistica.do?accion=Nuevo&tipoExtension=4`](#bcoextensiondivulgacionartisticadoaccionnuevotipoextension4) | formulario | SIGEVA | 1 | 12 | 0 |
| [`bcoExtensionDivulgacionCyT.do?accion=Nuevo&tipoExtension=1`](#bcoextensiondivulgacioncytdoaccionnuevotipoextension1) | formulario | SIGEVA | 1 | 75 | 3 |
| [`bcoExtensionLista.do?idGrupo=5&idMenu=1463&idModulo=5`](#bcoextensionlistadoidgrupo5idmenu1463idmodulo5) | lista | SIGEVA | 1 | 1 | 15 |
| [`bcoExtensionOtroTipo.do?accion=Nuevo&tipoExtension=5`](#bcoextensionotrotipodoaccionnuevotipoextension5) | formulario | SIGEVA | 1 | 12 | 0 |
| [`bcoExtensionRuralIndustrial.do?accion=Nuevo&tipoExtension=2`](#bcoextensionruralindustrialdoaccionnuevotipoextension2) | formulario | SIGEVA | 1 | 78 | 5 |
| [`bcoExtensionServiciosSociales.do?accion=Nuevo&tipoExtension=3`](#bcoextensionserviciossocialesdoaccionnuevotipoextension3) | formulario | SIGEVA | 1 | 14 | 1 |
| [`bcoFinanciamientoCyTLista.do?idGrupo=5&idMenu=1459&idModulo=5`](#bcofinanciamientocytlistadoidgrupo5idmenu1459idmodulo5) | lista | FINANCIAMIENTOS BANCO DE DATOS | 1 | 1 | 6 |
| [`bcoFormacionAcademica.do?idGrupo=3&idMenu=1453&idModulo=3`](#bcoformacionacademicadoidgrupo3idmenu1453idmodulo3) | lista | SIGEVA | 1 | 25 | 7 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=1`](#bcoformacionacademicadetalledoaccionnuevonivel1) | formulario | SIGEVA | 1 | 54 | 3 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=2`](#bcoformacionacademicadetalledoaccionnuevonivel2) | formulario | SIGEVA | 1 | 54 | 3 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=3`](#bcoformacionacademicadetalledoaccionnuevonivel3) | formulario | SIGEVA | 1 | 54 | 3 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=5`](#bcoformacionacademicadetalledoaccionnuevonivel5) | formulario | SIGEVA | 1 | 45 | 2 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=6`](#bcoformacionacademicadetalledoaccionnuevonivel6) | formulario | SIGEVA | 1 | 42 | 1 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=7`](#bcoformacionacademicadetalledoaccionnuevonivel7) | formulario | SIGEVA | 1 | 39 | 0 |
| [`bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=8`](#bcoformacionacademicadetalledoaccionnuevonivel8) | formulario | SIGEVA | 1 | 37 | 0 |
| [`bcoFormacionBecario.do?accion=nuevo&tipo=2`](#bcoformacionbecariodoaccionnuevotipo2) | formulario | SIGEVA | 1 | 90 | 0 |
| [`bcoFormacionComplementariaCurso.do?action=Nuevo`](#bcoformacioncomplementariacursodoactionnuevo) | formulario | SIGEVA | 1 | 31 | 1 |
| [`bcoFormacionComplementariaIdioma.do?action=Nuevo`](#bcoformacioncomplementariaidiomadoactionnuevo) | formulario | SIGEVA | 1 | 20 | 0 |
| [`bcoFormacionComplementariaLista.do`](#bcoformacioncomplementarialistado) | lista | SIGEVA | 1 | 12 | 5 |
| [`bcoFormacionComplementariaLista.do?idGrupo=3&idMenu=1454&idModulo=3`](#bcoformacioncomplementarialistadoidgrupo3idmenu1454idmodulo3) | lista | SIGEVA | 1 | 12 | 5 |
| [`bcoFormacionComplementariaPosdoctorado.do?action=Nuevo`](#bcoformacioncomplementariaposdoctoradodoactionnuevo) | formulario | SIGEVA | 1 | 47 | 2 |
| [`bcoFormacionComplementariaSalud.do?action=Nuevo`](#bcoformacioncomplementariasaluddoactionnuevo) | formulario | SIGEVA | 1 | 49 | 1 |
| [`bcoFormacionInvestigador.do?accion=nuevo&tipo=3`](#bcoformacioninvestigadordoaccionnuevotipo3) | formulario | SIGEVA | 1 | 86 | 0 |
| [`bcoFormacionPasante.do?accion=nuevo&tipo=4`](#bcoformacionpasantedoaccionnuevotipo4) | formulario | SIGEVA | 1 | 30 | 0 |
| [`bcoFormacionPersonalApoyo.do?accion=nuevo&tipo=5`](#bcoformacionpersonalapoyodoaccionnuevotipo5) | formulario | SIGEVA | 1 | 29 | 0 |
| [`bcoFormacionRRHH.do?idGrupo=5&idMenu=1460&idModulo=5`](#bcoformacionrrhhdoidgrupo5idmenu1460idmodulo5) | lista | SIGEVA | 1 | 15 | 5 |
| [`bcoFormacionTesis.do?accion=nuevo&tipo=1`](#bcoformaciontesisdoaccionnuevotipo1) | formulario | SIGEVA | 1 | 85 | 0 |
| [`bcoIncorporarParticipanteTramite.do?idGrupo=8&idMenu=0&idModulo=8`](#bcoincorporarparticipantetramitedoidgrupo8idmenu0idmodulo8) | menu | SIGEVA | 1 | 2 | 0 |
| [`bcoListaActividadEstanciaPasantia.do?accion=Nuevo&tipoActividad=1`](#bcolistaactividadestanciapasantiadoaccionnuevotipoactividad1) | formulario | SIGEVA | 1 | 64 | 4 |
| [`bcoOtrasActividadesCYTLista.do?idGrupo=5&idMenu=1464&idModulo=5`](#bcootrasactividadescytlistadoidgrupo5idmenu1464idmodulo5) | lista | SIGEVA | 1 | 19 | 4 |
| [`bcoParticipacionEvento.do?accion=nuevo`](#bcoparticipacioneventodoaccionnuevo) | formulario | SIGEVA | 1 | 25 | 2 |
| [`bcoPrecargarArticulo.do?action=Nuevo`](#bcoprecargararticulodoactionnuevo) | menu | SIGEVA | 1 | 2 | 0 |
| [`bcoPrecargarArticulo.do?action=Nuevo#omitir`](#bcoprecargararticulodoactionnuevoomitir) | formulario | SIGEVA | 1 | 111 | 5 |
| [`bcoPremio.do?accion=nuevo`](#bcopremiodoaccionnuevo) | formulario | PREMIOS Y/O DISTINCIONES BANCO DE DATOS | 1 | 20 | 1 |
| [`bcoPremioLista.do?idGrupo=7&idMenu=1470&idModulo=7`](#bcopremiolistadoidgrupo7idmenu1470idmodulo7) | lista | SIGEVA | 1 | 3 | 1 |
| [`bcoProduccionArtisticaAudioVisualMultimedial.do?accion=nuevo&grupoArtistica=3`](#bcoproduccionartisticaaudiovisualmultimedialdoaccionnuevogrupoartistica3) | formulario | SIGEVA | 1 | 77 | 13 |
| [`bcoProduccionArtisticaCorporalTeatral.do?accion=nuevo&grupoArtistica=4`](#bcoproduccionartisticacorporalteatraldoaccionnuevogrupoartistica4) | formulario | SIGEVA | 1 | 75 | 12 |
| [`bcoProduccionArtisticaLista.do?grupoArtistica=1&idGrupo=6&idMenu=1468&idModulo=6`](#bcoproduccionartisticalistadogrupoartistica1idgrupo6idmenu1468idmodulo6) | lista | SIGEVA | 1 | 27 | 9 |
| [`bcoProduccionArtisticaLista.do?idGrupo=6&idMenu=1468&idModulo=6`](#bcoproduccionartisticalistadoidgrupo6idmenu1468idmodulo6) | lista | SIGEVA | 1 | 27 | 9 |
| [`bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=1`](#bcoproduccionartisticaliterariadoaccionnuevogrupoartisticaliteraria1) | formulario | SIGEVA | 1 | 73 | 11 |
| [`bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=2`](#bcoproduccionartisticaliterariadoaccionnuevogrupoartisticaliteraria2) | formulario | SIGEVA | 1 | 72 | 11 |
| [`bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=3`](#bcoproduccionartisticaliterariadoaccionnuevogrupoartisticaliteraria3) | formulario | SIGEVA | 1 | 73 | 11 |
| [`bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=4`](#bcoproduccionartisticaliterariadoaccionnuevogrupoartisticaliteraria4) | formulario | SIGEVA | 1 | 72 | 11 |
| [`bcoProduccionArtisticaMusicalSonora.do?accion=nuevo&grupoArtistica=1`](#bcoproduccionartisticamusicalsonoradoaccionnuevogrupoartistica1) | formulario | SIGEVA | 1 | 79 | 13 |
| [`bcoProduccionArtisticaOtra.do?accion=nuevo&grupoArtistica=6`](#bcoproduccionartisticaotradoaccionnuevogrupoartistica6) | formulario | SIGEVA | 1 | 74 | 12 |
| [`bcoProduccionArtisticaVisual.do?accion=nuevo&grupoArtistica=2`](#bcoproduccionartisticavisualdoaccionnuevogrupoartistica2) | formulario | SIGEVA | 1 | 75 | 13 |
| [`bcoProduccionCongresoRedesLista.do?action=Nuevo&publicado=0`](#bcoproduccioncongresoredeslistadoactionnuevopublicado0) | formulario | SIGEVA | 1 | 97 | 7 |
| [`bcoProduccionConvenio.do?action=Nuevo`](#bcoproduccionconveniodoactionnuevo) | formulario | SIGEVA | 1 | 92 | 10 |
| [`bcoProduccionDesarrollo.do?action=Nuevo&tipo=12`](#bcoproducciondesarrollodoactionnuevotipo12) | formulario | Datos básicos | 1 | 62 | 7 |
| [`bcoProduccionDesarrollo.do?action=Nuevo&tipo=13`](#bcoproducciondesarrollodoactionnuevotipo13) | formulario | Datos básicos | 1 | 62 | 7 |
| [`bcoProduccionDesarrollo.do?action=Nuevo&tipo=14`](#bcoproducciondesarrollodoactionnuevotipo14) | formulario | Datos básicos | 1 | 62 | 7 |
| [`bcoProduccionDesarrollo.do?action=Nuevo&tipo=15`](#bcoproducciondesarrollodoactionnuevotipo15) | formulario | Datos básicos | 1 | 62 | 7 |
| [`bcoProduccionInformeTecnico.do?action=Nuevo`](#bcoproduccioninformetecnicodoactionnuevo) | formulario | SIGEVA | 1 | 98 | 6 |
| [`bcoProduccionLibroPublicacion.do?action=Nuevo`](#bcoproduccionlibropublicaciondoactionnuevo) | formulario | SIGEVA | 1 | 99 | 8 |
| [`bcoProduccionListaBienes.do?idGrupo=5&idMenu=1464&idModulo=5`](#bcoproduccionlistabienesdoidgrupo5idmenu1464idmodulo5) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 1 |
| [`bcoProduccionListaBienes.do?idGrupo=6&idMenu=1482&idModulo=6`](#bcoproduccionlistabienesdoidgrupo6idmenu1482idmodulo6) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 1 |
| [`bcoProduccionListaDesarrollo.do?idGrupo=6&idMenu=1467&idModulo=6`](#bcoproduccionlistadesarrollodoidgrupo6idmenu1467idmodulo6) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 4 |
| [`bcoProduccionListaDesarrollo.do?idGrupo=6&idMenu=1467&idModulo=6&prod=tecnologica`](#bcoproduccionlistadesarrollodoidgrupo6idmenu1467idmodulo6prodtecnologica) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 4 |
| [`bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1466&idModulo=6`](#bcoproduccionlistapublicaciondoidgrupo6idmenu1466idmodulo6) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 7 |
| [`bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1466&idModulo=6&prod=cientifica`](#bcoproduccionlistapublicaciondoidgrupo6idmenu1466idmodulo6prodcientifica) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 7 |
| [`bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1467&idModulo=6&prod=tecnologica`](#bcoproduccionlistapublicaciondoidgrupo6idmenu1467idmodulo6prodtecnologica) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 7 |
| [`bcoProduccionListaPublicacionCapituloLibro.do?action=Nuevo`](#bcoproduccionlistapublicacioncapitulolibrodoactionnuevo) | formulario | SIGEVA | 1 | 112 | 13 |
| [`bcoProduccionListaPublicacionCongreso.do?action=Nuevo&publicado=1`](#bcoproduccionlistapublicacioncongresodoactionnuevopublicado1) | formulario | SIGEVA | 1 | 107 | 8 |
| [`bcoProduccionListaPublicacionTesis.do?action=Nuevo`](#bcoproduccionlistapublicaciontesisdoactionnuevo) | formulario | SIGEVA | 1 | 32 | 5 |
| [`bcoProduccionListaServicios.do?idGrupo=6&idMenu=1481&idModulo=6`](#bcoproduccionlistaserviciosdoidgrupo6idmenu1481idmodulo6) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 1 |
| [`bcoProduccionListaServicios.do?idGrupo=6&idMenu=1481&idModulo=6&prod=tecnologica`](#bcoproduccionlistaserviciosdoidgrupo6idmenu1481idmodulo6prodtecnologica) | lista | PRODUCCIONES Y SERVICIOS BANCO DE DATOS | 1 | 1 | 1 |
| [`bcoProduccionOtra.do?action=Nuevo`](#bcoproduccionotradoactionnuevo) | formulario | SIGEVA | 1 | 35 | 8 |
| [`bcoRedesLista.do?idGrupo=6&idMenu=1466&idModulo=6&prod=cientifica`](#bcoredeslistadoidgrupo6idmenu1466idmodulo6prodcientifica) | lista | REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS | 1 | 1 | 6 |
| [`bcoRedesLista.do?idGrupo=7&idMenu=1469&idModulo=7`](#bcoredeslistadoidgrupo7idmenu1469idmodulo7) | lista | REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS | 1 | 1 | 6 |
| [`bcoRedesLista.do?idGrupo=7&idMenu=1471&idModulo=7`](#bcoredeslistadoidgrupo7idmenu1471idmodulo7) | lista | REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS | 1 | 1 | 6 |
| [`bcoRoles.do?idGrupo=0&idMenu=1479&idModulo=1`](#bcorolesdoidgrupo0idmenu1479idmodulo1) | lista | SIGEVA | 1 | 4 | 1 |
| [`bcofinanciamientoCYTEventoEquipamiento.do?accion=nuevo&grupoFinanciamientoId=3`](#bcofinanciamientocyteventoequipamientodoaccionnuevogrupofinanciamientoid3) | formulario | FINANCIAMIENTO CYT BANCO DE DATOS | 1 | 30 | 1 |
| [`bcofinanciamientoCYTEventoEquipamiento.do?accion=nuevo&grupoFinanciamientoId=4`](#bcofinanciamientocyteventoequipamientodoaccionnuevogrupofinanciamientoid4) | formulario | FINANCIAMIENTO CYT BANCO DE DATOS | 1 | 30 | 1 |
| [`bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=11`](#bcofinanciamientocytproyectodoaccionnuevotipofinanciamientoid11) | formulario | FINANCIAMIENTO CYT BANCO DE DATOS | 1 | 57 | 5 |
| [`bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=12`](#bcofinanciamientocytproyectodoaccionnuevotipofinanciamientoid12) | formulario | FINANCIAMIENTO CYT BANCO DE DATOS | 1 | 57 | 6 |
| [`bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=5`](#bcofinanciamientocytproyectodoaccionnuevotipofinanciamientoid5) | formulario | FINANCIAMIENTO CYT BANCO DE DATOS | 1 | 57 | 5 |
| [`filtroImprimirCurriculum.do`](#filtroimprimircurriculumdo) | formulario | Imprimir los formularios seleccionados | 1 | 4 | 0 |
| [`indexBancoDatos.do?idGrupo=0&idMenu=0&idModulo=1`](#indexbancodatosdoidgrupo0idmenu0idmodulo1) | menu | BANCO DE DATOS DE ACTIVIDADES DE CIENCIA Y TÉCNICA BANCO DE DATOS | 1 | 0 | 0 |
| [`instructivoBancoDeDatoNavOper.do`](#instructivobancodedatonavoperdo) | menu | SIGEVA | 1 | 0 | 0 |
| [`instructivoConvocatoriaGral.do?idGrupo=0&idMenu=1477&idModulo=1`](#instructivoconvocatoriagraldoidgrupo0idmenu1477idmodulo1) | menu | SIGEVA | 1 | 0 | 0 |

## Formularios y pantallas sin módulo

### `bcoABMRoles.do?accion=nuevo`

Formulario — SIGEVA

Formulario `cABMRolesMemoriaActionForm` → `bcoABMRoles.do` (POST); botones: Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoRol` | select/select-one | Tipo de rol |  |  |
| `apellido` | input/text | Apellido o Cuil |  |  |
| `usuarioSeleccionado` | textarea/textarea | Usuario seleccionado |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `fechaInicio`, `fechaFin`, `usrNum`, `d-4563864-p`, `d-4563864-s`, `d-4563864-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadAmbitoNoAcademico.do?accion=Nuevo&tipoActividad=5`

Formulario — SIGEVA
- Tabla `usr.actividad.tablaActividadesLogros` (displaytag `d-`): (2)TAREAS REALIZADAS (ES POSIBLE SELECCIONAR MÁS DE UNA TAREA) · 

Formulario `cActividadAmbitoNoAcademicoActionForm` → `bcoActividadAmbitoNoAcademico.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoAreaEjercicioActividadId` | select/select-one | Área de ejercicio de la profesión |  | 16 opciones |
| `tipoFuncionActividadId` | select/select-one | Función/Cargo |  | 5 opciones |
| `otraFuncionActividad` | input/text | (1) Otra |  |  |
| `actividadLogrosChecked` | input/checkbox |  |  | valores 20, 21, 22, 23; x4 |
| `otroTipoTarea` | input/text | (3) Otras tareas realizadas |  |  |
| `descripcionAcividad` | textarea/textarea | Descripción de la actividad |  |  |
| `tipoAmbitoProfesionId` | select/select-one | Ámbito de desempeño |  | 3 opciones |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `pais` | select/select-one | (4) País |  | 244 opciones |
| `provincia` | select/select-one | (4) Provincia |  | 1 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `btnSubmit`, `action`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadCoordinacion.do?accion=nuevo&tipoActividad=9`

Formulario — SIGEVA
- Tabla `objetivoRed` (displaytag `d-`): TIPO DE ACTIVIDADES (ES POSIBLE SELECCIONAR MÁS DE UN TIPO DE ACTIVIDAD) · SEL.
- Tabla `actividadOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCION · INSTITUCION QUE FINANCIA LA PRODUCCIÓN · % FINANCIA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)

Formulario `cActividadCoordinacionActionForm` → `bcoActividadCoordinacion.do` (POST); botones: Nuevo, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (2) Año de finalización |  | datepicker |
| `evento` | input/text | Denominación del proyecto y/o programa |  |  |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `cidSeleccionar` | input/checkbox |  | sí | valores 1 |
| `tipoTareaActividadChecked` | input/checkbox |  |  | valores 33, 34, 35, 36, 37, 38, 39, 40, 41; x9 |
| `otroTipoTareaActividad` | input/text | (1) Otro tipo de actividades |  |  |
| `infoAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `d-4396209-p`, `d-4396209-s` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionInstitucional.do?accion=Nuevo`

Formulario — SIGEVA
- Tabla `usr.actividadEvaluacion.tablaTipoAmbito` (displaytag `d-`): ÁMBITO DEL PLAN O POLÍTICA EVALUADO ·  · (ES POSIBLE SELECCIONAR MÁS DE UN ÁMBITO) · 

Formulario `cActividadEvaluacionInstitucionalActionForm` → `bcoActividadEvaluacionInstitucional.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoEvaluacionInstitucional` | select/select-one | Tipo de evaluación institucional |  | 5 opciones |
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (1) Fin |  | datepicker |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `tipoRolEvaluador` | select/select-one | (2) Rol evaluador |  | 6 opciones |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `observaciones` | textarea/textarea | Observaciones |  |  |
| `tipoAmbitoId` | input/checkbox |  |  | valores 1, 2, 3, 4, 5, 6, 7, 8, 9, 10; x10 |
| `otroAmbito` | input/text | (3) Otro ámbito |  |  |
| `filtroOrganizacionEvaluadaBuscar` | input/text |  |  |  |
| `filtroOrganizacionEvaluadaLabel` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `organizacionBuscada`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `filtroOrganizacionEvaluadaId`, `filtroOrganizacionEvaluadaIsOtra`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionOtroTipo.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cActividadEvaluacionOtroTipoActionForm` → `bcoActividadEvaluacionOtroTipo.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `otroTipoEvaluacion` | input/text | Tipo evaluación |  |  |
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (1) Fin |  | datepicker |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `observaciones` | textarea/textarea | Observaciones |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionPersonalCyT.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cActividadEvaluacionPersonalCyTActionForm` → `bcoActividadEvaluacionPersonalCyT.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoEvaluacion` | select/select-one | Tipo de personal evaluado |  | 8 opciones |
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (1) Fin |  | datepicker |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `tipoRolEvaluador` | select/select-one | (2) Rol evaluador |  | 6 opciones |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `observaciones` | textarea/textarea | (3) Descripción |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionProyecto.do?accion=Nuevo`

Formulario — SIGEVA
- Tabla `usr.actividadEvaluacion.tablaTipoProyecto` (displaytag `d-`): TIPO DE PROGRAMAS/PROYECTOS EVALUADOS (ES POSIBLE SELECCIONAR MÁS DE UN TIPO). · 

Formulario `cActividadEvaluacionProyectoActionForm` → `bcoActividadEvaluacionProyecto.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (1) Fin |  | datepicker |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `tipoProyectoId` | input/checkbox |  |  | valores 1, 2, 3, 4, 5, 6, 7, 8, 9, 10; x10 |
| `tipoRolEvaluador` | select/select-one | (2) Rol evaluador |  | 6 opciones |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `observaciones` | textarea/textarea | Observaciones |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionRevista.do?accion=Nuevo&tipoActividadEvaluacionId=3`

Formulario — SIGEVA

Formulario `cActividadEvaluacionRevistaActionForm` → `bcoActividadEvaluacionRevista.do` (POST); botones: Buscar por ISSN / e-ISSN, Buscar por Nombre, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `bissn` | input/text | (1) ISSN / e-ISSN |  |  |
| `brevista` | input/text | (2) Nombre |  |  |
| `srevista` | textarea/textarea | Revista seleccionada |  |  |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `sitioWeb` | input/text | URL |  |  |
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (3) Fin |  | datepicker |
| `observaciones` | textarea/textarea | Observaciones |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `publicacionId`, `revista`, `issn`, `eissn`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`, `tipoActividadEvaluacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadEvaluacionRevista.do?accion=Nuevo&tipoActividadEvaluacionId=6`

Formulario — SIGEVA

Formulario `cActividadEvaluacionRevistaActionForm` → `bcoActividadEvaluacionRevista.do` (POST); botones: Buscar por ISSN / e-ISSN, Buscar por Nombre, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `bissn` | input/text | (1) ISSN / e-ISSN |  |  |
| `brevista` | input/text | (2) Nombre |  |  |
| `srevista` | textarea/textarea | Revista seleccionada |  |  |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `sitioWeb` | input/text | URL |  |  |
| `anioInicio` | input/text | Año inicio |  | datepicker |
| `anioFin` | input/text | (3) Fin |  | datepicker |
| `tipoFuncion` | select/select-one | Función desempeñada |  | 6 opciones |
| `dedicHorariaSemanal` | input/text | (4) Dedicación horaria semanal |  |  |
| `observaciones` | textarea/textarea | Observaciones |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `publicacionId`, `revista`, `issn`, `eissn`, `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`, `tipoActividadEvaluacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadMembresias.do?accion=nuevo&tipoActividad=7`

Formulario — SIGEVA

Formulario `cActividadMembresiasActionForm` → `bcoActividadMembresias.do` (POST); botones: Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (2) Año de finalización |  | datepicker |
| `evento` | input/text | Denominación de la asociación científico-tecnológica y/o profesional |  |  |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `tipoModalidadAdmision` | select/select-one | Modalidad de admisión |  | 5 opciones |
| `otroTipoModalidadAdmision` | input/text | (1) Otra modalidad de admisión |  |  |
| `infoAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `d-4396209-p`, `d-4396209-s` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadNormalizacion.do?accion=Nuevo&tipoActividad=4`

Formulario — SIGEVA
- Tabla `usr.actividad.tablaActividadesLogros` (displaytag `d-`): TIPO DE TAREAS REALIZADAS (ES POSIBLE SELECCIONAR MÁS DE UNA ACTIVIDAD O LOGRO) · 

Formulario `cActividadNormalizacionActionForm` → `bcoActividadNormalizacion.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoFuncionActividadId` | select/select-one | Función desempeñada |  | 5 opciones |
| `otraFuncionActividad` | input/text | (1) Otra |  |  |
| `actividadLogrosChecked` | input/checkbox |  |  | valores 15, 16, 17, 18, 19; x5 |
| `otroTipoTarea` | input/text | (2) Otro |  |  |
| `descripcionPrincipalesAcividades` | textarea/textarea | Descripción de las principales actividades |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `btnSubmit`, `action`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadOtraActividadCYT.do?accion=Nuevo&tipoActividad=6`

Formulario — SIGEVA

Formulario `cActividadOtraActividadActionForm` → `bcoActividadOtraActividadCYT.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `otroTipoActividad` | input/text | Tipo de actividad |  |  |
| `funcionDesempeniada` | input/text | Función desempeñada |  |  |
| `descripcionAcividad` | textarea/textarea | Descripción de la actividad |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `btnSubmit`, `action`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadProduccion.do?accion=Nuevo&tipoActividad=3`

Formulario — SIGEVA
- Tabla `actividadOrganizacionFinanciaTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN QUE FINANCIA LA PRODUCCIÓN · % FINANCIA
- Tabla `actividadTipoDestinatarioTable` (displaytag `d-`):  · TIPO DE DESTINATARIO · PAÍS · DESTINATARIO
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)

Formulario `cActividadProduccionActionForm` → `bcoActividadProduccion.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoFuncionActividadId` | select/select-one | Función desempeñada |  | 5 opciones |
| `otraFuncionActividad` | input/text | (1) Otra |  |  |
| `tipoProductoId` | select/select-one | Tipo de producto |  | 9 opciones |
| `otroTipoProducto` | input/text | (2) Otro |  |  |
| `denominacionProducto` | input/text | Denominación del producto |  |  |
| `denominacionActividad` | input/text | Denominación de la actividad |  |  |
| `descripcionPrincipalesTareas` | textarea/textarea | Descripción de las tareas desempeñadas |  |  |
| `actividadOrganizacionFinanciaBuscar` | input/text |  |  | x2 |
| `actividadOrganizacionFinanciaPorcentajeFinancia` | input/text |  |  | x2 |
| `actividadTipoDestinatarioTipoDestinatario` | select/select-one |  |  | 11 opciones |
| `actividadTipoDestinatarioPais` | select/select-one |  |  | 244 opciones |
| `actividadTipoDestinatarioDestinatario` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `actividadOrganizacionFinanciaOrganizacionId`, `actividadOrganizacionFinanciaisOtraOrganizacion`, `actividadOrganizacionFinanciaPaisId`, `actividadOrganizacionFinanciaOrganizacionLabel`, `actividadOrganizacionFinanciaProvinciaId`, `actividadOrganizacionFinanciaRelacionadaId`, `actividadOrganizacionFinanciaNivel`, `actividadOrganizacionFinanciaRuta`, `actividadOrganizacionFinanciaTipoId`, `actividadOrganizacionFinanciaId`, `actividadOrganizacionFinanciaProduccionId`, `actividadTipoDestinatarioId`, `actividadTipoDestinatarioConvenioId`, `action`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `btnSubmit`, `actividadOrganizacionFinanciaJSON`, `actividadTipoDestinatarioJSON`, `campoDisciplinarJSON`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadRedes.do?accion=nuevo&tipoActividad=8`

Formulario — SIGEVA
- Tabla `objetivoRed` (displaytag `d-`): OBJETIVO DE LA RED (ES POSIBLE SELECCIONAR MÁS DE UN OBJETIVO) · SEL.

Formulario `cActividadRedesActionForm` → `bcoActividadRedes.do` (POST); botones: Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (2) Año de finalización |  | datepicker |
| `evento` | input/text | Denominación de la red temática o institucional |  |  |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `cidSeleccionar` | input/checkbox |  | sí | valores 1 |
| `tipoTareaActividadChecked` | input/checkbox |  |  | valores 24, 25, 26, 27, 28, 29, 30, 31, 32; x9 |
| `otroTipoTareaActividad` | input/text | (1) Otro objetivo de la red |  |  |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `infoAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `id`, `d-4396209-p` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoActividadSistemaAltaComplejidad.do?accion=Nuevo&tipoActividad=2`

Formulario — SIGEVA
- Tabla `usr.actividad.tablaTipoSistema` (displaytag `d-`): TIPO DE SISTEMA OPERADO Y/O MANTENIDO (ES POSIBLE SELECCIONAR MÁS DE UN TIPO DE SISTEMA) · 
- Tabla `actividadOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN SELECCIONADA

Formulario `cActividadSistemaAltaComplejidadActionForm` → `bcoActividadSistemaAltaComplejidad.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoFuncionActividadId` | select/select-one | Función desempeñada |  | 5 opciones |
| `otraFuncionActividad` | input/text | (1) Otra |  |  |
| `actividadTipoSistemaChecked` | input/checkbox |  |  | valores 1, 2, 3; x3 |
| `otroTipoSistema` | input/text | (2) Otro |  |  |
| `denominacionActividad` | input/text | Denominación de la actividad |  |  |
| `descripcionPrincipalesTareas` | textarea/textarea | Descripción de las principales tareas |  |  |
| `actividadOrganizacionBuscar` | input/text |  |  | x2 |
| `esActividadVinculada` | input/radio |  |  | valores 1, 0; x2 |
| `denominacionRed` | input/text | (3) Denominación de la red o sistema de información |  |  |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `actividadOrganizacionOrganizacionId`, `actividadOrganizacionisOtraOrganizacion`, `actividadOrganizacionPaisId`, `actividadOrganizacionOrganizacionLabel`, `actividadOrganizacionProvinciaId`, `actividadOrganizacionRelacionadaId`, `actividadOrganizacionNivel`, `actividadOrganizacionRuta`, `actividadOrganizacionTipoId`, `actividadOrganizacionId`, `actividadOrganizacionProduccionId`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `btnSubmit`, `actividadOrganizacionJSON`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoBeca.do?accion=nuevo`

Formulario — SIGEVA

Formulario `cBecaActionForm` → `bcoBeca.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (1) Fin |  | datepicker |
| `tipoBeca` | select/select-one | Tipo de beca |  | 12 opciones |
| `denominacionBeca` | input/text | Denominación de la beca |  |  |
| `tipoTarea` | select/select-one | Tipo de tareas |  | 5 opciones |
| `organizacionDesarrolloBuscar` | input/text |  |  |  |
| `organizacionDesarrolloLabel` | textarea/textarea |  |  |  |
| `organizacionOtorganteBuscar` | input/text |  |  |  |
| `organizacionOtorganteLabel` | textarea/textarea |  |  |  |
| `nombreDirector` | input/text | Nombre del director |  |  |
| `apellidoDirector` | input/text | Apellido del director |  |  |
| `nombreCoDirector` | input/text | Nombre del codirector |  |  |
| `apellidoCoDirector` | input/text | Apellido del codirector |  |  |
| `observaciones` | textarea/textarea | Descripción (tema, plan de trabajo, tareas, etc.) |  |  |
| `financiaPostgrado` | input/radio | ¿Financia o financió un posgrado con esta beca? |  | valores 0, 1; x2 |
| `nivel` | input/radio |  |  | valores 0, 1, 2, 3; x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `organizacionDesarrolloId`, `organizacionDesarrolloIsOtra`, `organizacionOtorganteId`, `organizacionOtorganteIsOtra`, `id`, `btnBuscarOrganizacion`, `becaOrganizacionJSON`, `buscarOrganizacionIndex`, `buscarOrganizacion`, `buscarOrganizacionControl`, `btnSubmit`, `d-1036751-p`, `d-1036751-s`, `d-1036751-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoDocenteNivelBasicoMedio.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cCargoDocenteNivelBasicoMedioActionForm` → `bcoCargoDocenteNivelBasicoMedio.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `cargo` | input/text | Cargo |  |  |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |
| `tipoSistemaEducacionBasicaMediaId` | select/select-one | Tipo de sistema de educación básica/media |  | 6 opciones; x2 |
| `otroTipoSistemaEducacionBasicaMedia` | input/text | (2) Otro tipo de sistema de educación básica/media |  | x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-6314371-p`, `d-6314371-s`, `d-6314371-o`, `d-2137604-p`, `d-2137604-s`, `d-2137604-o`, `d-1335539-p`, `d-1335539-s`, `d-1335539-o`, `d-4077089-p`, `d-4077089-s`, `d-4077089-o`, `cargoId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoDocenteNivelCapacitacion.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cCargoDocenteNivelCapacitacionActionForm` → `bcoCargoDocenteNivelCapacitacion.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x3 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x3 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x3 |
| `cargo` | input/text | Cargo |  | x3 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal del cargo docente |  | 4 opciones; x3 |
| `tematica` | input/text | Nombre o temática del curso |  | x3 |
| `tipoCursoId` | select/select-one | Tipo de curso |  | 5 opciones; x3 |
| `cargaHorariaTotal` | input/text | Carga horaria total del curso |  | x3 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-6314371-p`, `d-6314371-s`, `d-6314371-o`, `d-2137604-p`, `d-2137604-s`, `d-2137604-o`, `d-1335539-p`, `d-1335539-s`, `d-1335539-o`, `d-4077089-p`, `d-4077089-s`, `d-4077089-o`, `cargoId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoDocenteNivelSuperior.do?accion=Nuevo`

Formulario — SIGEVA
- Tabla `niveles` (displaytag `d-`): NIVEL EDUCATIVO DE LAS ACTIVIDADES CURRICULARES DICTADAS · 
- Tabla `actividades` (displaytag `d-`):  · NOMBRE DE LA ACTIVIDAD CURRICULAR · PROFESOR TITULAR O RESPONSABLE

Formulario `cCargoDocenteNivelSuperiorActionForm` → `bcoCargoDocenteNivelSuperior.do` (POST); botones: Buscar, Limpiar, Nuevo, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `claseCargoId` | select/select-one | Cargo |  | 1 opciones; x2 |
| `otroCargo` | input/text | (2) Otro cargo |  | oculto al cargar |
| `tipoHonorariosId` | select/select-one | Tipo de cargo |  | 3 opciones; x2 |
| `tipoDedicacionHorariaDocenteId` | select/select-one | Dedicación |  | 7 opciones; x3 |
| `otraDedicacionHorariaDocente` | input/text | (3) Otra dedicación |  |  |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal del cargo docente |  | 4 opciones; x2 |
| `tipoCondicionDocenteId` | select/select-one | Condición |  | 4 opciones; x2 |
| `esInvestigacionDesarrollo` | input/radio | ¿Realiza actividades de investigación y desarrollo con este cargo docente? |  | valores 1, 0; x3 |
| `nivelEducativoChecked` | input/checkbox |  | sí | valores 5, 1, 2, 3, 9; x6 |
| `nombreActividadCurricular` | input/text |  |  | x2 |
| `profesorActividadCurricular` | input/text |  |  | x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `btnSubmitEx`, `btnSubmitParam`, `cargoId`, `d-6314371-p`, `d-6314371-s`, `d-6314371-o`, `d-2137604-p`, `d-2137604-s`, `d-2137604-o`, `d-1335539-p`, `d-1335539-s`, `d-1335539-o`, `d-4077089-p`, `d-4077089-s`, `d-4077089-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoDocenteNivelTerciario.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cCargoDocenteNivelTerciarioActionForm` → `bcoCargoDocenteNivelTerciario.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `cargo` | input/text | Cargo |  | x2 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |
| `denominacionCarrera` | input/text | Denominación de la carrera/tecnicatura |  | x2 |
| `tipoFormacionAcademicaId` | select/select-one | Tipo de formación |  | 3 opciones; x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `cargoId`, `d-6314371-p`, `d-6314371-s`, `d-6314371-o`, `d-2137604-p`, `d-2137604-s`, `d-2137604-o`, `d-1335539-p`, `d-1335539-s`, `d-1335539-o`, `d-4077089-p`, `d-4077089-s`, `d-4077089-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoGestionAction.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cCargoGestionActionForm` → `bcoCargoGestionAction.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `claseCargoId` | select/select-one | Cargo |  | 39 opciones; x2 |
| `cargo` | input/text | (2) Otro cargo |  | x2 |
| `tipoFuncionId` | select/select-one | Tipo de función desempeñada |  | 6 opciones; x2 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-7297766-p`, `d-7297766-s`, `d-7297766-o`, `cargoId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoGestionLista.do`

Lista — SIGEVA
- Tabla `persona.cargoDocente.cargosGestion` (displaytag `d-7297766`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO

Formulario `cCargoGestionListaActionForm` → `bcoCargoGestionLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7297766-p`, `d-7297766-s`, `d-7297766-o`

Acciones no visitadas: `bcoCargoGestionAction.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoCargoGestionAction.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=51` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoIDIncentivos.do?action=Nuevo`

Formulario — SIGEVA

Formulario `cCargoIDIncentivosActionForm` → `bcoCargoIDIncentivos.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `anioCategorizacion` | input/text | Año de categorización |  | datepicker; x2 |
| `categoria` | select/select-one | Categoría en el Programa de Incentivos |  | 6 opciones; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-94152-p`, `d-94152-s`, `d-94152-o`, `d-472981-p`, `d-472981-s`, `d-472981-o`, `d-5866723-p`, `d-5866723-s`, `d-5866723-o`, `id`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoIDOrganizacionCT.do?action=Nuevo`

Formulario — SIGEVA

Formulario `cCargoIDOrganizacionCTActionForm` → `bcoCargoIDOrganizacionCT.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `tipoInstitucionInvestigacion` | select/select-one | Carrera |  | 4 opciones; x2 |
| `tipoCargoInvestigacion` | select/select-one | Categoria |  | 14 opciones; x2 |
| `cargo` | input/text | Otro cargo/función |  | x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-94152-p`, `d-94152-s`, `d-94152-o`, `d-472981-p`, `d-472981-s`, `d-472981-o`, `d-5866723-p`, `d-5866723-s`, `d-5866723-o`, `id`, `organizacionId`, `otraOrganizacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoIDOtraOrganizacion.do?action=Nuevo`

Formulario — SIGEVA

Formulario `cCargoIDOtraOrganizacionActionForm` → `bcoCargoIDOtraOrganizacion.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  | x2 |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `cargo` | input/text | Cargo para Realizar I+D |  | x2 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-94152-p`, `d-94152-s`, `d-94152-o`, `d-472981-p`, `d-472981-s`, `d-472981-o`, `d-5866723-p`, `d-5866723-s`, `d-5866723-o`, `id`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoOtroAction.do?accion=Nuevo`

Formulario — SIGEVA

Formulario `cCargoOtroActionForm` → `bcoCargoOtroAction.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker; x2 |
| `fechaFin` | input/text | (1) Fecha fin |  | datepicker; x2 |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  | x2 |
| `cargo` | input/text | Cargo |  | x2 |
| `tipoDedicacionHorariaSemanalId` | select/select-one | Dedicación horaria semanal |  | 4 opciones; x2 |
| `categoria` | input/text | Categoría |  | x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `cargoId`, `d-7953626-p`, `d-7953626-s`, `d-7953626-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoOtroLista.do`

Lista — SIGEVA
- Tabla `persona.cargo.otrosCargos` (displaytag `d-7953626`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO

Formulario `cCargoOtroListaActionForm` → `bcoCargoOtroLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7953626-p`, `d-7953626-s`, `d-7953626-o`

Acciones no visitadas: `bcoCargoOtroAction.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoCargoOtroAction.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=16` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoDatoInvestigacion.do?accion=nuevo`

Formulario — DATOS DE INVESTIGACIÓN
- Tabla `autorTable` (displaytag `d-`): Agregar · AUTOR
- Tabla `colaboradorTable` (displaytag `d-`): Agregar · COLABORADOR
- Tabla `produccion` (displaytag `d-`): Agregar · TIPO · AÑO · TITULO
- Tabla `localizaciones` (displaytag `d-`): Agregar · Tipo · Detalle
- Tabla `financiamientos` (displaytag `d-`): Agregar · ORGANISMO · ORGANISMO FINANCIADOR · NOMBRE DEL PROYECTO · CÓDIGO DEL FINANCIAMIENTO
- Tabla `identificadores` (displaytag `d-`): Agregar · TIPO IDENTIFICADOR · IDENTIFICADOR ALTERNATIVO
- Tabla `descripciones` (displaytag `d-`): Agregar · TIPO · DESCRIPCIÓN
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `adjuntos` (displaytag `d-`): Agregar · ARCHIVO ADJUNTO · NOTA DE USO
- Tabla `poligono` (displaytag `d-`): Agregar · Latitud · Longitud
- Tabla `poligonoEdit` (displaytag `d-`): Agregar · Latitud · Longitud

Formulario `cDatoInvestigacionActionForm` → `bcoDatoInvestigacion.do` (POST); botones: Agregar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `titulo` | input/text |  |  |  |
| `tipofecha` | select/select-one |  |  | 3 opciones |
| `fechaDesde` | input/text |  |  |  |
| `fechaHasta` | input/text |  |  |  |
| `idioma` | select/select-one |  |  | 13 opciones |
| `georeferenciable` | select/select-one |  |  | 3 opciones |
| `justificacion` | textarea/textarea |  |  | oculto al cargar |
| `version` | input/text |  |  |  |
| `tipoIdentificador` | select/select-one |  |  | 10 opciones |
| `identificador` | input/text |  |  |  |
| `resumen` | textarea/textarea |  |  |  |
| `tipoDescripcion` | select/select-one |  |  | 6 opciones |
| `descripcion` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `tipoAcceso` | input/radio |  |  | valores 1, 2, 3; x3 |
| `licenciaAbierto` | select/select-one |  |  | 9 opciones; oculto al cargar |
| `motivoExclusion` | select/select-one |  |  | 7 opciones; oculto al cargar |
| `fechaEmbargo` | input/text |  |  | datepicker; oculto al cargar |
| `licenciaEmbargado` | select/select-one |  |  | 9 opciones; oculto al cargar |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `colaboradorJSON`, `produccionRelacionadaJSON`, `referenciasJSON`, `financiamientoJSON`, `identificadoresJSON`, `descripcionesJSON`, `palabraId`, `adjuntosJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `palabraJSON`, `campoDisciplinarJSON`, `actionSesion`, `desactivarPopup`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionDivulgacionArtistica.do?accion=Nuevo&tipoExtension=4`

Formulario — SIGEVA

Formulario `cExtensionActionForm` → `bcoExtensionDivulgacionArtistica.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (2) Fin |  | datepicker |
| `titulo` | input/text | Denominación de la actividad |  |  |
| `tipoFuncionDesempeniadaId` | select/select-one | Función desempeñada |  | 6 opciones |
| `otraFuncionDesempeniada` | input/text | (1) Otra función desempeñada |  |  |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `selMedioDivulgacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionDivulgacionCyT.do?accion=Nuevo&tipoExtension=1`

Formulario — SIGEVA
- Tabla `usr.extension.tablaMedioDivulgacion` (displaytag `d-`):  · TIPO DE MEDIO DE DIVULGACIÓN · NOMBRE DEL MEDIO DE DIVULGACIÓN · LUGAR DE REALIZACIÓN · (3)PART. PERIÓDICA
- Tabla `usr.extension.tablaTipoDestinatario` (displaytag `d-`): TIPO DESTINATARIO (ES POSIBLE SELECCIONAR MÁS DE UN TIPO) ·  ·  · 
- Tabla `usr.extension.tablaFuenteFinanciamiento` (displaytag `d-`): FUENTE DE FINANCIAMIENTO (ES POSIBLE SELECCIONAR MÁS DE UNA FUENTE) · 

Formulario `cExtensionActionForm` → `bcoExtensionDivulgacionCyT.do` (POST); botones: Nuevo, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `titulo` | input/text | Denominación de la actividad |  |  |
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (1) Fin |  | datepicker |
| `tipoFuncionDesempeniadaId` | select/select-one | Función desempeñada |  | 6 opciones |
| `otraFuncionDesempeniada` | input/text | (2) Otra función desempeñada |  |  |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `medioDivulgacionTipo` | select/select-one |  |  | 17 opciones; x3 |
| `medioDivulgacionNombre` | input/text |  |  | x3 |
| `medioDivulgacionLugar` | input/text |  |  | x3 |
| `medioParticipacion` | input/checkbox |  |  | valores -1, -2, -3; x3 |
| `tipoDestinatarioId` | input/checkbox |  |  | valores 1, 2, 3, 4, 5, 6; x6 |
| `tipoFuenteFinanciamientoId` | input/checkbox |  |  | valores 1, 2, 3, 5, 4; x5 |
| `otraFuentefinanciamiento` | input/text | (4) Otra fuente de financiamiento |  |  |
| `archivoFile` | input/file | Adjuntar archivo |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `medioDivulgacionId`, `linkArchivo` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionOtroTipo.do?accion=Nuevo&tipoExtension=5`

Formulario — SIGEVA

Formulario `cExtensionActionForm` → `bcoExtensionOtroTipo.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (2) Fin |  | datepicker |
| `titulo` | input/text | Denominación de la actividad |  |  |
| `tipoFuncionDesempeniadaId` | select/select-one | Función desempeñada |  | 5 opciones |
| `otraFuncionDesempeniada` | input/text | (1) Otra función desempeñada |  |  |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `selMedioDivulgacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionRuralIndustrial.do?accion=Nuevo&tipoExtension=2`

Formulario — SIGEVA
- Tabla `?` (displaytag `d-`): TIPO DE EXTENSIÓN · 
- Tabla `?` (displaytag `d-`): ÁMBITO DE EXTENSIÓN · 
- Tabla `usr.extension.tablaMedioDivulgacion` (displaytag `d-`):  · TIPO DE ACCIONES COMPRENDIDAS · LUGAR DE REALIZACIÓN · (3)PART. PERIÓDICA
- Tabla `usr.extension.tablaTipoDestinatario` (displaytag `d-`): TIPO DESTINATARIO (ES POSIBLE SELECCIONAR MÁS DE UN TIPO) ·  ·  · 
- Tabla `usr.extension.tablaFuenteFinanciamiento` (displaytag `d-`): FUENTE DE FINANCIAMIENTO (ES POSIBLE SELECCIONAR MÁS DE UNA FUENTE) · 

Formulario `cExtensionActionForm` → `bcoExtensionRuralIndustrial.do` (POST); botones: Buscar, Limpiar, Nuevo, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `titulo` | input/text | Denominación del proyecto o actividad |  |  |
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (1) Fin |  | datepicker |
| `tipoActividadExtensionismoId` | input/checkbox |  |  | valores 1, 2; x2 |
| `ambitoExtensionId` | input/checkbox |  |  | valores 1, 2, 3; x3 |
| `tipoFuncionDesempeniadaId` | select/select-one | Función desempeñada |  | 7 opciones |
| `otraFuncionDesempeniada` | input/text | (2) Otra función desempeñada |  |  |
| `descripcion` | textarea/textarea | Descripción del proyecto o actividad |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `medioDivulgacionTipo` | select/select-one |  |  | 12 opciones; x3 |
| `medioDivulgacionLugar` | input/text |  |  | x3 |
| `medioParticipacion` | input/checkbox |  |  | valores -1, -2, -3; x3 |
| `tipoDestinatarioId` | input/checkbox |  |  | valores 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20; x14 |
| `tipoFuenteFinanciamientoId` | input/checkbox |  |  | valores 1, 2, 3, 5, 4; x5 |
| `otraFuentefinanciamiento` | input/text | (4) Otra fuente de financiamiento |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionServiciosSociales.do?accion=Nuevo&tipoExtension=3`

Formulario — SIGEVA
- Tabla `usr.extension.tablaFuenteFinanciamiento` (displaytag `d-`): FUENTE DE FINANCIAMIENTO (ES POSIBLE SELECCIONAR MÁS DE UNA FUENTE) · 

Formulario `cExtensionActionForm` → `bcoExtensionServiciosSociales.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | (2) Fin |  | datepicker |
| `titulo` | input/text | Denominación de la actividad |  |  |
| `tipoFuncionDesempeniadaId` | select/select-one | Función desempeñada |  | 6 opciones |
| `otraFuncionDesempeniada` | input/text | (1) Otra función desempeñada |  |  |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `tipoFuenteFinanciamientoId` | input/checkbox |  |  | valores 1, 2, 3, 5, 4; x5 |
| `otraFuentefinanciamiento` | input/text | (3) Otra fuente de financiamiento |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `selMedioDivulgacionId`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=1`

Formulario — SIGEVA
- Tabla `usr.formacionAcademicaDetalle.organizacionOtorgante` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN OTORGANTE DEL TÍTULO SELECCIONADA
- Tabla `usr.formacionAcademicaDetalle.organizacionFinanciadora` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN FINANCIADORA DE LA BECA SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Nuevo, Limpiar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `denominacionCarrera` | input/text | Denominación de la carrera |  |  |
| `tituloObtenido` | input/text | Título |  |  |
| `numeroResolucion` | input/text | Número de Resolución de Acreditación del Posgrado por CONEAU |  |  |
| `organizacionOtorganteBusquedaArray0` | input/text |  |  |  |
| `tituloTesis` | input/text | Título de la tesis |  |  |
| `avanceTesis` | input/text | (2) Porcentaje de avance de la tesis |  |  |
| `apellidoDirector` | input/text | Apellido del director/tutor |  |  |
| `nombreDirector` | input/text | Nombre del director/tutor |  |  |
| `organizacionDirectorTesisBuscar` | input/text | Institución del director/tutor |  |  |
| `organizacionDirectorTesisLabel` | textarea/textarea | Institución seleccionada del director/tutor |  |  |
| `apellidoCoDirector` | input/text | Apellido del codirector/co-tutor |  |  |
| `nombreCoDirector` | input/text | Nombre del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisBuscar` | input/text | Institución del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisLabel` | textarea/textarea | Institución seleccionada del codirector/co-tutor |  |  |
| `beca` | input/radio | ¿Realizó su posgrado con una beca? |  | valores 1, 0; x2 |
| `organizacionFinanciadoraBusquedaArray0` | input/text |  |  |  |
| `especialidad` | input/text | * Especialidad |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionDirectorTesisId`, `organizacionCoDirectorTesisId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=2`

Formulario — SIGEVA
- Tabla `usr.formacionAcademicaDetalle.organizacionOtorgante` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN OTORGANTE DEL TÍTULO SELECCIONADA
- Tabla `usr.formacionAcademicaDetalle.organizacionFinanciadora` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN FINANCIADORA DE LA BECA SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Nuevo, Limpiar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `denominacionCarrera` | input/text | Denominación de la carrera |  |  |
| `tituloObtenido` | input/text | Título |  |  |
| `numeroResolucion` | input/text | Número de Resolución de Acreditación del Posgrado por CONEAU |  |  |
| `organizacionOtorganteBusquedaArray0` | input/text |  |  |  |
| `tituloTesis` | input/text | Título del trabajo final, obra o tesis |  |  |
| `avanceTesis` | input/text | (2) Porcentaje de avance del trabajo final, obra o tesis |  |  |
| `apellidoDirector` | input/text | Apellido del director/tutor |  |  |
| `nombreDirector` | input/text | Nombre del director/tutor |  |  |
| `organizacionDirectorTesisBuscar` | input/text | Institución del director/tutor |  |  |
| `organizacionDirectorTesisLabel` | textarea/textarea | Institución seleccionada del director/tutor |  |  |
| `apellidoCoDirector` | input/text | Apellido del codirector/co-tutor |  |  |
| `nombreCoDirector` | input/text | Nombre del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisBuscar` | input/text | Institución del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisLabel` | textarea/textarea | Institución seleccionada del codirector/co-tutor |  |  |
| `beca` | input/radio | ¿Realizó su posgrado con una beca? |  | valores 1, 0; x2 |
| `organizacionFinanciadoraBusquedaArray0` | input/text |  |  |  |
| `especialidad` | input/text | * Especialidad |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionDirectorTesisId`, `organizacionCoDirectorTesisId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=3`

Formulario — SIGEVA
- Tabla `usr.formacionAcademicaDetalle.organizacionOtorgante` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN OTORGANTE DEL TÍTULO SELECCIONADA
- Tabla `usr.formacionAcademicaDetalle.organizacionFinanciadora` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN FINANCIADORA DE LA BECA SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Nuevo, Limpiar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `denominacionCarrera` | input/text | Denominación de la carrera |  |  |
| `tituloObtenido` | input/text | Título |  |  |
| `numeroResolucion` | input/text | Número de Resolución de Acreditación del Posgrado por CONEAU |  |  |
| `organizacionOtorganteBusquedaArray0` | input/text |  |  |  |
| `tituloTesis` | input/text | Título del trabajo final |  |  |
| `avanceTesis` | input/text | (2) Porcentaje de avance del trabajo final |  |  |
| `apellidoDirector` | input/text | Apellido del director/tutor |  |  |
| `nombreDirector` | input/text | Nombre del director/tutor |  |  |
| `organizacionDirectorTesisBuscar` | input/text | Institución del director/tutor |  |  |
| `organizacionDirectorTesisLabel` | textarea/textarea | Institución seleccionada del director/tutor |  |  |
| `apellidoCoDirector` | input/text | Apellido del codirector/co-tutor |  |  |
| `nombreCoDirector` | input/text | Nombre del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisBuscar` | input/text | Institución del codirector/co-tutor |  |  |
| `organizacionCoDirectorTesisLabel` | textarea/textarea | Institución seleccionada del codirector/co-tutor |  |  |
| `beca` | input/radio | ¿Realizó su posgrado con una beca? |  | valores 1, 0; x2 |
| `organizacionFinanciadoraBusquedaArray0` | input/text |  |  |  |
| `especialidad` | input/text | * Especialidad |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionDirectorTesisId`, `organizacionCoDirectorTesisId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=5`

Formulario — SIGEVA
- Tabla `usr.formacionAcademicaDetalle.organizacionOtorgante` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN OTORGANTE DEL TÍTULO SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Nuevo, Limpiar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `denominacionCarrera` | input/text | Denominación de la carrera |  |  |
| `tituloIntermedioObtenido` | input/radio | Obtención de título intermedio |  | valores 1, 0; x2 |
| `denominacionTituloIntermedio` | input/text | (2) Denominación del título intermedio |  |  |
| `tituloObtenido` | input/text | Título |  |  |
| `organizacionOtorganteBusquedaArray0` | input/text |  |  |  |
| `tituloTesis` | input/text | Título de la tesina |  |  |
| `avanceTesis` | input/text | (3) Porcentaje de avance de la tesina |  |  |
| `apellidoDirector` | input/text | Apellido del director/tutor |  |  |
| `nombreDirector` | input/text | Nombre del director/tutor |  |  |
| `especialidad` | input/text | * Especialidad |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=6`

Formulario — SIGEVA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `denominacionCarrera` | input/text | Denominación de la carrera |  |  |
| `tituloObtenido` | input/text | Título |  |  |
| `tipoFormacionAcademicaId` | select/select-one | Tipo de formación |  | 3 opciones |
| `organizacionOtorganteBuscar` | input/text | Institución |  |  |
| `organizacionOtorganteLabel` | textarea/textarea | Institución seleccionada |  |  |
| `especialidad` | input/text | * Especialidad |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionOtorganteId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=7`

Formulario — SIGEVA

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `formacionTecnica` | input/radio | Formación técnica |  | valores 1, 0; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `tituloObtenido` | input/text | Título |  |  |
| `organizacionOtorganteBuscar` | input/text | Institución |  |  |
| `organizacionOtorganteLabel` | textarea/textarea | Institución seleccionada |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionOtorganteId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionAcademicaDetalle.do?accion=nuevo&nivel=8`

Formulario — SIGEVA

Formulario `cFormacionAcademicaDetalleActionForm` → `bcoFormacionAcademicaDetalle.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `estadoSituacionId` | input/radio | Situación del nivel |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaEgreso` | input/text |  |  | datepicker |
| `organizacionOtorganteBuscar` | input/text | Institución |  |  |
| `organizacionOtorganteLabel` | textarea/textarea | Institución seleccionada |  |  |
| `observaciones` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `btnSubmitContexto`, `organizacionFila`, `organizacionEnFilaId`, `tipoOrganizacionEnFilaId`, `filtroOrganizacion`, `organizacionOtorganteId`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionBecario.do?accion=nuevo&tipo=2`

Formulario — SIGEVA

Formulario `cFormacionBecarioActionForm` → `bcoFormacionBecario.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (1) Fin |  | datepicker |
| `nombre` | input/text | Nombre becario |  |  |
| `apellido` | input/text | Apellido becario |  |  |
| `organizacionTrabajoBuscar` | input/text |  |  |  |
| `organizacionTrabajoLabel` | textarea/textarea |  |  |  |
| `organizacionFinanciaBuscar` | input/text |  |  |  |
| `organizacionFinanciaLabel` | textarea/textarea |  |  |  |
| `tipoTarea` | select/select-one | Tipo de tareas |  | 5 opciones |
| `tipoBeca` | select/select-one | Tipo de beca |  | 12 opciones |
| `tipoDirector` | select/select-one | Función desempeñada |  | 3 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `id`, `organizacionBuscada` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaCurso.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionComplementariaCursoActionForm` → `bcoFormacionComplementariaCurso.do` (POST); botones: Buscar, Limpiar, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `situacionFormacion` | input/radio | Situación del curso |  | valores 1, 2; x2 |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | (1) Fecha de finalización |  | datepicker |
| `tipoCursoId` | select/select-one | (2) Tipo de curso |  | 5 opciones |
| `otroTipoCurso` | input/text | (3) Otro |  |  |
| `denominacionCurso` | input/text | Denominación del curso |  |  |
| `cargaHorariaId` | select/select-one | Carga horaria |  | 7 opciones |
| `tipoCertificacionFinalId` | select/select-one | (1) Tipo de certificación final |  | 3 opciones |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`, `campoDisciplinarJSON`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaIdioma.do?action=Nuevo`

Formulario — SIGEVA

Formulario `cFormacionComplementariaIdiomaActionForm` → `bcoFormacionComplementariaIdioma.do` (POST); botones: Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `idiomaId` | select/select-one | Idioma |  | 13 opciones |
| `otroIdioma` | input/text | (1) Otro |  |  |
| `nivelDominioIdiomaId` | select/select-one | Nivel de dominio del idioma |  | 4 opciones |
| `certificadosObtenidos` | input/text | Certificado/s obtenido/s |  |  |
| `institucionEmisoraCertificado` | input/text | Institución emisora del certificado |  |  |
| `anioObtencionCertificado` | input/text | Año de obtención del certificado |  | datepicker |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaLista.do`

Lista — SIGEVA
- Tabla `persona.formacionComplementaria.salud` (displaytag `d-5236396`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · ESPECIALIDAD
- Tabla `persona.formacionComplementaria.posdoctorado` (displaytag `d-2007390`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN
- Tabla `persona.formacionComplementaria.curso` (displaytag `d-5235699`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN · DENOMINACIÓN DEL CURSO
- Tabla `persona.formacionComplementaria.idioma` (displaytag `d-7318382`): NUEVO · IDIOMA · DOMINIO · CERTIFICADO · AÑO
- Tabla `usr.actividad.pasantia` (displaytag `d-2879534`): NUEVO · AÑO INICIO · AÑO FIN · TIPO DE TAREAS · DIRECTOR

Formulario `(sin nombre)` → `bcoFormacionComplementariaLista.do` (POST); botones: Importar, Salir

Ocultos: `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`

Acciones no visitadas: `bcoFormacionComplementariaCurso.do?action=Borrar&formacionId=N` (accion sobre registros (borrar)); `bcoFormacionComplementariaCurso.do?action=Editar&formacionId=N` (accion sobre registros (editar)); `bcoFormacionComplementariaIdioma.do?action=Borrar&formacionId=N` (accion sobre registros (borrar)); `bcoFormacionComplementariaIdioma.do?action=Editar&formacionId=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=47` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=48` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=49` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=50` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=54` (ruta prohibida (sesion, importacion o descarga)); `bcoListaActividadEstanciaPasantia.do?accion=borrar&actividadId=N&tipoActividad=1` (accion sobre registros (borrar)); `bcoListaActividadEstanciaPasantia.do?accion=editar&actividadId=N&tipoActividad=1` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaPosdoctorado.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `formacionOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN FINANCIADORA SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cFormacionComplementariaPosdoctoradoActionForm` → `bcoFormacionComplementariaPosdoctorado.do` (POST); botones: Buscar, Limpiar, Nuevo, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text | Fecha de inicio |  | datepicker |
| `fechaFin` | input/text | Fecha de finalización |  | datepicker |
| `tituloTrabajo` | input/text | Título del trabajo o proyecto de investigación |  |  |
| `apellidoAnfitrion` | input/text | Apellido del investigador anfitrión |  |  |
| `nombreAnfitrion` | input/text | Nombre del investigador anfitrión |  |  |
| `apellidoCoAnfitrion` | input/text | Apellido del investigador co-anfitrión |  |  |
| `nombreCoAnfitrion` | input/text | Nombre del investigador co-anfitrión |  |  |
| `filtroOrganizacionEjecucionBuscar` | input/text |  |  |  |
| `filtroOrganizacionEjecucionLabel` | textarea/textarea |  |  |  |
| `tuvoBeca` | input/radio |  |  | valores 1, 2; x2 |
| `formacionOrganizacionBuscar` | input/text |  |  | x2 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionEjecucionId`, `filtroOrganizacionEjecucionIsOtra`, `formacionOrganizacionOrganizacionId`, `formacionOrganizacionisOtraOrganizacion`, `formacionOrganizacionPaisId`, `formacionOrganizacionOrganizacionLabel`, `formacionOrganizacionProvinciaId`, `formacionOrganizacionRelacionadaId`, `formacionOrganizacionNivel`, `formacionOrganizacionRuta`, `formacionOrganizacionTipoId`, `formacionOrganizacionId`, `formacionOrganizacionProduccionId`, `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `formacionOrganizacionJSON`, `campoDisciplinarJSON`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaSalud.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `formacionOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN FINANCIADORA SELECCIONADA

Formulario `cFormacionComplementariaSaludActionForm` → `bcoFormacionComplementariaSalud.do` (POST); botones: Buscar, Limpiar, Nuevo, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `situacionFormacion` | input/radio | Situación de la formación |  | valores 1, 2; x2 |
| `fechaInicio` | input/text | Fecha de inicio |  | datepicker |
| `fechaFin` | input/text | (1) Fecha de finalización |  | datepicker |
| `tipoFormacionSaludId` | select/select-one | Tipo de formación incluida |  | 5 opciones |
| `otroTipoFormacionSalud` | input/text | (2) Otra |  |  |
| `tipoEspecialidadMedicaId` | select/select-one | Especialidad |  | 46 opciones |
| `otroTipoEspecialidadMedica` | input/text | (3) Otra |  |  |
| `tieneCertificadoEspecialidad` | input/radio | (1) Certificado de especialidad |  | valores 1, 0; x2 |
| `filtroOrganizacionOtorganteBuscar` | input/text |  |  |  |
| `filtroOrganizacionOtorganteLabel` | textarea/textarea |  |  |  |
| `anioUltimaCertificacion` | input/text | Año de obtención de la última certificación |  | datepicker |
| `filtroOrganizacionEjecucionBuscar` | input/text |  |  |  |
| `filtroOrganizacionEjecucionLabel` | textarea/textarea |  |  |  |
| `tuvoBecaResidencia` | input/radio |  |  | valores 1, 2; x2 |
| `formacionOrganizacionBuscar` | input/text |  |  | x2 |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionOtorganteId`, `filtroOrganizacionOtorganteIsOtra`, `filtroOrganizacionEjecucionId`, `filtroOrganizacionEjecucionIsOtra`, `formacionOrganizacionOrganizacionId`, `formacionOrganizacionisOtraOrganizacion`, `formacionOrganizacionPaisId`, `formacionOrganizacionOrganizacionLabel`, `formacionOrganizacionProvinciaId`, `formacionOrganizacionRelacionadaId`, `formacionOrganizacionNivel`, `formacionOrganizacionRuta`, `formacionOrganizacionTipoId`, `formacionOrganizacionId`, `formacionOrganizacionProduccionId`, `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `formacionOrganizacionJSON`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionInvestigador.do?accion=nuevo&tipo=3`

Formulario — SIGEVA

Formulario `cFormacionInvestigadorActionForm` → `bcoFormacionInvestigador.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (1) Fin |  | datepicker |
| `nombre` | input/text | Nombre |  |  |
| `apellido` | input/text | Apellido |  |  |
| `organizacionTrabajoBuscar` | input/text |  |  |  |
| `organizacionTrabajoLabel` | textarea/textarea |  |  |  |
| `carrera` | select/select-one | Carrera |  | 4 opciones |
| `categoria` | select/select-one | (2) Categoria |  | 0 opciones |
| `otroCargoInvestigacion` | input/text | Otro cargo/función |  |  |
| `tipoDirector` | select/select-one | Función desempeñada |  | 3 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `id`, `organizacionTrabajoId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionPasante.do?accion=nuevo&tipo=4`

Formulario — SIGEVA

Formulario `cFormacionPasanteActionForm` → `bcoFormacionPasante.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (1)Fin |  | datepicker |
| `organizacionTrabajoBuscar` | input/text |  |  |  |
| `organizacionTrabajoLabel` | textarea/textarea |  |  |  |
| `nombre` | input/text | Nombre de pasante |  |  |
| `apellido` | input/text | Apellido del pasante |  |  |
| `tipoTarea` | select/select-one | Tipo de tareas |  | 5 opciones |
| `tipoAmbitoInstitucional` | select/select-one | (2) Ámbito institucional |  | 11 opciones |
| `temaPlanTrabajo` | input/text | Tema del plan de trabajo |  |  |
| `gradoAcademico` | select/select-one | Nivel educativo del pasante |  | 6 opciones |
| `tipoDirector` | select/select-one | Función desempeñada |  | 3 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `organizacionTrabajoId`, `organizacionTrabajoIsOtra`, `d-5968303-p`, `d-5968303-s`, `d-5968303-o`, `d-5969929-p`, `d-5969929-s`, `d-5969929-o`, `d-3911430-p`, `d-3911430-s`, `d-3911430-o`, `d-1793546-p`, `d-1793546-s`, `d-1793546-o`, `d-626479-p`, `d-626479-s`, `d-626479-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionPersonalApoyo.do?accion=nuevo&tipo=5`

Formulario — SIGEVA

Formulario `cFormacionPersonalApoyoActionForm` → `bcoFormacionPersonalApoyo.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (1) Fin |  | datepicker |
| `organizacionTrabajoBuscar` | input/text |  |  |  |
| `organizacionTrabajoLabel` | textarea/textarea |  |  |  |
| `nombre` | input/text | Nombre del personal de apoyo a la I+D |  |  |
| `apellido` | input/text | Apellido del personal de apoyo a la I+D |  |  |
| `carrera` | select/select-one | Carrera |  | 4 opciones |
| `categoria` | select/select-one | Categoria |  | 0 opciones |
| `otroCargoInvestigacion` | input/text | (2) Otro cargo/función |  |  |
| `tipoDirector` | select/select-one | Función desempeñada |  | 3 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `organizacionTrabajoId`, `organizacionTrabajoIsOtra`, `d-5968303-p`, `d-5968303-s`, `d-5968303-o`, `d-5969929-p`, `d-5969929-s`, `d-5969929-o`, `d-3911430-p`, `d-3911430-s`, `d-3911430-o`, `d-1793546-p`, `d-1793546-s`, `d-1793546-o`, `d-626479-p`, `d-626479-s`, `d-626479-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionTesis.do?accion=nuevo&tipo=1`

Formulario — SIGEVA

Formulario `cFormacionTesisActionForm` → `bcoFormacionTesis.do` (POST); botones: Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `anioDesde` | input/text |  |  | datepicker |
| `anioHasta` | input/text | (1) Año defensa tesis |  | datepicker |
| `nombre` | input/text | Nombre tesista |  |  |
| `apellido` | input/text | Apellido tesista |  |  |
| `organizacionTrabajoBuscar` | input/text |  |  |  |
| `organizacionTrabajoLabel` | textarea/textarea |  |  |  |
| `tipoTesis` | select/select-one | Tipo de trabajo dirigido |  | 5 opciones |
| `calificacionObtenida` | input/text | (1) Calificación obtenida |  |  |
| `tipoDirector` | select/select-one | Función desempeñada |  | 3 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `id`, `organizacionTrabajoId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoListaActividadEstanciaPasantia.do?accion=Nuevo&tipoActividad=1`

Formulario — SIGEVA
- Tabla `usr.actividad.tablaActividadesLogros` (displaytag `d-`): ACTIVIDADES REALIZADAS Y/O LOGROS ALCANZADOS (ES POSIBLE SELECCIONAR MÁS DE UNA ACTIVIDAD O LOGRO) · 
- Tabla `actividadOrganizacionFinanciaTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN SELECCIONADA · EJECUTA · % FINANCIA
- Tabla `actividadOrganizacionDirectorTable` (displaytag `d-`):  · BUSCAR INSTITUCIÓN · INSTITUCIÓN SELECCIONADA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)

Formulario `cActividadEstanciaPasantiaActionForm` → `bcoListaActividadEstanciaPasantia.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoFuncionActividadId` | select/select-one | Tipo de tareas |  | 6 opciones |
| `temaPlanTrabajo` | input/text | (1) Tema del plan de trabajo |  |  |
| `actividadLogrosChecked` | input/checkbox |  |  | valores 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14; x14 |
| `descripcion` | textarea/textarea | Descripción de la actividad |  |  |
| `actividadOrganizacionFinanciaBuscar` | input/text |  |  | x2 |
| `actividadOrganizacionFinanciaEjecuta` | input/checkbox |  |  | valores false; x2 |
| `actividadOrganizacionFinanciaPorcentajeFinancia` | input/text |  |  | x2 |
| `directorNombre` | input/text | Nombre del director/tutor |  |  |
| `directorApellido` | input/text | Apellido del director/tutor |  |  |
| `actividadOrganizacionDirectorBuscar` | input/text |  |  | x2 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `actividadOrganizacionFinanciaOrganizacionId`, `actividadOrganizacionFinanciaisOtraOrganizacion`, `actividadOrganizacionFinanciaPaisId`, `actividadOrganizacionFinanciaOrganizacionLabel`, `actividadOrganizacionFinanciaProvinciaId`, `actividadOrganizacionFinanciaRelacionadaId`, `actividadOrganizacionFinanciaNivel`, `actividadOrganizacionFinanciaRuta`, `actividadOrganizacionFinanciaTipoId`, `actividadOrganizacionFinanciaId`, `actividadOrganizacionFinanciaConvenioId`, `actividadOrganizacionDirectorOrganizacionId`, `actividadOrganizacionDirectorisOtraOrganizacion`, `actividadOrganizacionDirectorPaisId`, `actividadOrganizacionDirectorOrganizacionLabel`, `actividadOrganizacionDirectorProvinciaId`, `actividadOrganizacionDirectorRelacionadaId`, `actividadOrganizacionDirectorNivel`, `actividadOrganizacionDirectorRuta`, `actividadOrganizacionDirectorTipoId`, `actividadOrganizacionDirectorId`, `actividadOrganizacionDirectorProduccionId`, `action`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `btnSubmit`, `actividadOrganizacionFinanciaJSON`, `actividadOrganizacionDirectorJSON`, `campoDisciplinarJSON`, `id`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoParticipacionEvento.do?accion=nuevo`

Formulario — SIGEVA
- Tabla `modosParticipacion` (displaytag `d-`): MODO DE PARTICIPACIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MODO DE PARTICIPACIÓN) · SEL.
- Tabla `participacionEventoOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCION · INSTITUCION SELECCIONADA

Formulario `cParticipacionEventoActionForm` → `bcoParticipacionEvento.do` (POST); botones: Nuevo, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `evento` | input/text | Nombre del evento |  |  |
| `tipoReunion` | select/select-one | Tipo de evento |  | 14 opciones |
| `otroTipoReunion` | input/text | (1) Otro tipo de evento |  |  |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `anio` | input/text | Año |  | datepicker |
| `cidSeleccionar` | input/checkbox |  | sí | valores 1 |
| `modoParticipacionChecked` | input/checkbox |  |  | valores 1, 2, 3, 4, 5, 6, 7, 8, 9, 10; x10 |
| `otroModoParticipacion` | input/text | (2) Otro modo de participación |  |  |
| `infoAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `participacionEventoOrganizacionJSON`, `btnSubmit`, `d-5252578-p`, `d-5252578-s`, `d-5252578-o`, `d-998727-p`, `d-998727-s`, `d-998727-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoPrecargarArticulo.do?action=Nuevo`

Menu — SIGEVA

Formulario `cPrecargarArticuloActionForm` → `bcoPrecargarArticulo.do` (POST); botones: Precargar, Omitir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `identificador` | input/text | DOI / ISSN |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoPrecargarArticulo.do?action=Nuevo#omitir`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · SEL. · AUTORES · INSTITUCIONES ·  · ORDEN · MOVER
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionArticuloActionForm` → `bcoProduccionArticuloPublicacion.do` (POST); botones: Buscar por ISSN / e-ISSN, Buscar por Nombre, Limpiar, Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `bissn` | input/text | (1) ISSN / e-ISSN |  |  |
| `brevista` | input/text | (2) Nombre |  |  |
| `srevista` | textarea/textarea | Revista seleccionada |  |  |
| `editorial` | input/text | Editorial |  | x2 |
| `pais` | select/select-one |  |  | 244 opciones; x2 |
| `lugarEdicion` | input/text | Ciudad de la editorial |  |  |
| `produccion` | input/text | Título del artículo |  | x2 |
| `idioma` | select/select-one | Idioma |  | 13 opciones; x2 |
| `volumen` | input/text |  |  | x2 |
| `tomo` | input/text | Tomo |  |  |
| `numero` | input/text | Número |  | x2 |
| `paginaInicial` | input/text |  |  | x2 |
| `paginaFinal` | input/text | Página final |  | x2 |
| `fechaPublica` | input/text | (3) Fecha de publicación |  | datepicker; x2 |
| `web` | input/text | (4) URL |  | x2 |
| `doi` | input/text | (4) DOI |  | x2 |
| `tipoReferato` | input/radio |  | sí | valores 0, 2; x3 |
| `publicado` | input/radio |  | sí | valores 1, 2; x3 |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `autorSel` | input/radio |  |  | valores 0 |
| `autorParticipacionLabel` | input/text |  |  |  |
| `autorOrganizacionBuscar` | input/text |  |  |  |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `theFile` | input/file | Full text o texto completo | sí |  |
| `tipoAdjunto` | select/select-one | Tipo de archivo |  | 3 opciones |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `publicacionId`, `revista`, `issn`, `eissn`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `palabraId`, `linkFullText`, `actionSesion`, `autorJSON`, `palabraJSON`, `camposImportadosJSON`, `campoDisciplinarJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `fuente`, `autorSeleccionado`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoPremio.do?accion=nuevo`

Formulario — PREMIOS Y/O DISTINCIONES BANCO DE DATOS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO

Formulario `cPremioActionForm` → `bcoPremio.do` (POST); botones: Buscar, Limpiar, Borrar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `nombrePremio` | input/text | Denominación del premio o distinción honorífica |  |  |
| `categoria` | input/text | Categoría |  |  |
| `tipoPremio` | select/select-one | Tipo de premio o distinción |  | 3 opciones |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `anio` | input/text | Año |  | datepicker |
| `organizacionOtorganteBuscar` | input/text |  |  |  |
| `organizacionOtorganteLabel` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `infoAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `organizacionOtorganteId`, `organizacionOtorganteIsOtra`, `campoDisciplinarJSON`, `btnSubmit`, `d-7570473-p`, `d-7570473-s`, `d-7570473-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaAudioVisualMultimedial.do?accion=nuevo&grupoArtistica=3`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `importantePresentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaAudioVisualMultimedialActionForm` → `bcoProduccionArtisticaAudioVisualMultimedial.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaId` | select/select-one | Tipo de producción audiovisual o multimedial |  | 8 opciones |
| `otroTipoProduccion` | input/text | (1) Otro tipo de producción audiovisual o multimedial |  |  |
| `titulo` | input/text | Título de la producción |  |  |
| `anio` | input/text | Año |  | datepicker |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (2) URL |  |  |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoArtisticaCantidadPresentacionId` | select/select-one | Cantidad de presentaciones |  | 3 opciones |
| `presentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `importantePresentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `importantePresentacionPais` | select/select-one |  |  | 244 opciones |
| `importantePresentacionAnio` | input/text |  |  | datepicker |
| `importantePresentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `importantePresentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `importantePresentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `importantePresentacionProduccionId`, `importantePresentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaCorporalTeatral.do?accion=nuevo&grupoArtistica=4`

Formulario — SIGEVA
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `importantePresentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaCorporalTeatralActionForm` → `bcoProduccionArtisticaCorporalTeatral.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaId` | select/select-one | Tipo de producción corporal o teatral |  | 6 opciones |
| `otroTipoArtistica` | input/text | (1) Otro tipo de producción corporal o teatral |  |  |
| `titulo` | input/text | Título de la producción |  |  |
| `anio` | input/text | Año |  | datepicker |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoArtisticaCantidadPresentacionId` | select/select-one | Cantidad de presentaciones |  | 3 opciones |
| `presentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `importantePresentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `importantePresentacionPais` | select/select-one |  |  | 244 opciones |
| `importantePresentacionAnio` | input/text |  |  | datepicker |
| `importantePresentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `importantePresentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `importantePresentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `importantePresentacionProduccionId`, `importantePresentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=1`

Formulario — SIGEVA
- Tabla `cuadroModosDivulgacion` (displaytag `d-`): MODO DE DIVULGACIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): PAIS · CIUDAD · AÑO · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaLiterariaActionForm` → `bcoProduccionArtisticaLiteraria.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaLiterariaId` | select/select-one | Tipo de género narrativo |  | 5 opciones |
| `otroTipoArtisticaLiteraria` | input/text | (1) Otro tipo de género narrativo |  |  |
| `tituloArtisticaLiteraria` | input/text | Título de la producción artística literaria |  |  |
| `anio` | input/text | Año |  | datepicker |
| `modoDivulgacionCkecked` | input/checkbox |  |  | valores 0, 1; x2 |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoPublicacionId` | select/select-one | Tipo de publicación |  | 4 opciones |
| `tituloPublicacion` | input/text | Título de la publicación |  |  |
| `paisPublicacionId` | select/select-one | Pais |  | 244 opciones |
| `isbnIssn` | input/text | ISBN/ISSN |  |  |
| `idiomaPublicacionId` | select/select-one | Idioma |  | 13 opciones |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionCiudad` | input/text |  |  |  |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=2`

Formulario — SIGEVA
- Tabla `cuadroModosDivulgacion` (displaytag `d-`): MODO DE DIVULGACIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): PAIS · CIUDAD · AÑO · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaLiterariaActionForm` → `bcoProduccionArtisticaLiteraria.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaLiterariaId` | select/select-one | Tipo de género literario |  | 4 opciones |
| `tituloArtisticaLiteraria` | input/text | Título de la producción artística literaria |  |  |
| `anio` | input/text | Año |  | datepicker |
| `modoDivulgacionCkecked` | input/checkbox |  |  | valores 0, 1; x2 |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoPublicacionId` | select/select-one | Tipo de publicación |  | 4 opciones |
| `tituloPublicacion` | input/text | Título de la publicación |  |  |
| `paisPublicacionId` | select/select-one | Pais |  | 244 opciones |
| `isbnIssn` | input/text | ISBN/ISSN |  |  |
| `idiomaPublicacionId` | select/select-one | Idioma |  | 13 opciones |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionCiudad` | input/text |  |  |  |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=3`

Formulario — SIGEVA
- Tabla `cuadroModosDivulgacion` (displaytag `d-`): MODO DE DIVULGACIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): PAIS · CIUDAD · AÑO · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaLiterariaActionForm` → `bcoProduccionArtisticaLiteraria.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaLiterariaId` | select/select-one | Tipo de género guión |  | 5 opciones |
| `otroTipoArtisticaLiteraria` | input/text | (1) Otro tipo de género guión |  |  |
| `tituloArtisticaLiteraria` | input/text | Título de la producción artística literaria |  |  |
| `anio` | input/text | Año |  | datepicker |
| `modoDivulgacionCkecked` | input/checkbox |  |  | valores 0, 1; x2 |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoPublicacionId` | select/select-one | Tipo de publicación |  | 4 opciones |
| `tituloPublicacion` | input/text | Título de la publicación |  |  |
| `paisPublicacionId` | select/select-one | Pais |  | 244 opciones |
| `isbnIssn` | input/text | ISBN/ISSN |  |  |
| `idiomaPublicacionId` | select/select-one | Idioma |  | 13 opciones |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionCiudad` | input/text |  |  |  |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaLiteraria.do?accion=nuevo&grupoArtisticaLiteraria=4`

Formulario — SIGEVA
- Tabla `cuadroModosDivulgacion` (displaytag `d-`): MODO DE DIVULGACIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): PAIS · CIUDAD · AÑO · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaLiterariaActionForm` → `bcoProduccionArtisticaLiteraria.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `otroTipoArtisticaLiteraria` | input/text | Tipo de género literario |  |  |
| `tituloArtisticaLiteraria` | input/text | Título de la producción artística literaria |  |  |
| `anio` | input/text | Año |  | datepicker |
| `modoDivulgacionCkecked` | input/checkbox |  |  | valores 0, 1; x2 |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoPublicacionId` | select/select-one | Tipo de publicación |  | 4 opciones |
| `tituloPublicacion` | input/text | Título de la publicación |  |  |
| `paisPublicacionId` | select/select-one | Pais |  | 244 opciones |
| `isbnIssn` | input/text | ISBN/ISSN |  |  |
| `idiomaPublicacionId` | select/select-one | Idioma |  | 13 opciones |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionCiudad` | input/text |  |  |  |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaMusicalSonora.do?accion=nuevo&grupoArtistica=1`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `importantePresentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaMusicalSonoraActionForm` → `bcoProduccionArtisticaMusicalSonora.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtisticaId` | select/select-one | Tipo de producción musical sonora |  | 5 opciones |
| `tipoSonorizacionId` | select/select-one | Tipo de sonorización |  | 9 opciones |
| `otrotipoSonorizacion` | input/text | (1) Otro tipo de sonorización |  |  |
| `tipoArtisticaMedioId` | select/select-one | Medio |  | 5 opciones |
| `titulo` | input/text | Título de la producción |  |  |
| `anio` | input/text | Año |  | datepicker |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (2) URL |  |  |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoArtisticaCantidadPresentacionId` | select/select-one | Cantidad de presentaciones |  | 3 opciones |
| `presentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `importantePresentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `importantePresentacionPais` | select/select-one |  |  | 244 opciones |
| `importantePresentacionAnio` | input/text |  |  | datepicker |
| `importantePresentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `importantePresentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `importantePresentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `importantePresentacionProduccionId`, `importantePresentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaOtra.do?accion=nuevo&grupoArtistica=6`

Formulario — SIGEVA
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `importantePresentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaOtraActionForm` → `bcoProduccionArtisticaOtra.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoArtistica` | input/text | Tipo de producción artística |  |  |
| `titulo` | input/text | Título de la producción |  |  |
| `anio` | input/text | Año |  | datepicker |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoArtisticaCantidadPresentacionId` | select/select-one | Cantidad de presentaciones |  | 3 opciones |
| `presentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `importantePresentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `importantePresentacionPais` | select/select-one |  |  | 244 opciones |
| `importantePresentacionAnio` | input/text |  |  | datepicker |
| `importantePresentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `importantePresentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `importantePresentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `importantePresentacionProduccionId`, `importantePresentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaVisual.do?accion=nuevo&grupoArtistica=2`

Formulario — SIGEVA
- Tabla `artistica.colTiposProduccionVisual` (displaytag `d-`):  ·  ·  · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `presentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `importantePresentacionTable` (displaytag `d-`): TIPO DE EVENTO · PAIS · AÑO · TIPO DE PRESENTACIÓN · INSTITUCIÓN O ESTABLECIMIENTO
- Tabla `?` (displaytag `d-`): 
- Tabla `criticaTable` (displaytag `d-`): MEDIO DE COMUNICACIÓN · AUTOR · AÑO · PAIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cArtisticaVisualActionForm` → `bcoProduccionArtisticaVisual.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoProduccionVisualChecked` | input/checkbox |  |  | valores 5, 10, 6, 11, 7, 12, 8, 13, 9, 14; x10 |
| `otroTipoProduccionVisual` | input/text | (1) Otro tipo de producción visual |  |  |
| `titulo` | input/text | Título de la producción |  |  |
| `anio` | input/text | Año |  | datepicker |
| `tieneCriticasMediosComunicacion` | input/radio | ¿Obtuvo críticas en medios de comunicación? |  | valores 1, 0; x2 |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `tipoArtisticaCantidadPresentacionId` | select/select-one | Cantidad de presentaciones |  | 3 opciones |
| `presentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `presentacionPais` | select/select-one |  |  | 244 opciones |
| `presentacionAnio` | input/text |  |  | datepicker |
| `presentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `presentacionOrganizacionBuscar` | input/text |  |  |  |
| `importantePresentacionTipoEvento` | select/select-one |  |  | 10 opciones |
| `importantePresentacionPais` | select/select-one |  |  | 244 opciones |
| `importantePresentacionAnio` | input/text |  |  | datepicker |
| `importantePresentacionTipoPresentacion` | select/select-one |  |  | 3 opciones |
| `importantePresentacionOrganizacionBuscar` | input/text |  |  |  |
| `criticaMedioComunicacion` | input/text |  |  |  |
| `criticaAutor` | input/text |  |  |  |
| `criticaAnio` | input/text |  |  | datepicker |
| `criticaPais` | select/select-one |  |  | 244 opciones |
| `criticaResumen` | textarea/textarea |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorJSON`, `presentacionJSON`, `importantePresentacionJSON`, `criticaJSON`, `palabraJSON`, `campoDisciplinarJSON`, `accion`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `presentacionProduccionId`, `presentacionId`, `importantePresentacionProduccionId`, `importantePresentacionId`, `criticaProduccionId`, `palabraId`, `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionCongresoRedesLista.do?action=Nuevo&publicado=0`

Formulario — SIGEVA
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionCongresoActionForm` → `bcoProduccionCongresoRedesLista.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `produccion` | input/text | Título de trabajo |  |  |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `reunionCientifica` | input/text | Nombre del evento |  |  |
| `tipoReunion` | select/select-one | Tipo de evento |  | 14 opciones |
| `alcanceNacional` | input/checkbox |  |  | valores 1 |
| `alcanceInternacional` | input/checkbox |  |  | valores 1 |
| `paisEvento` | select/select-one | País del evento |  | 244 opciones |
| `lugarReunion` | input/text | Ciudad del evento |  |  |
| `fechaReunion` | input/text | Fecha del evento |  | datepicker |
| `institucionOrganizadora` | input/text | Institución organizadora |  |  |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `theFile` | input/file | Full text o texto completo |  |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `autorParticipacionProduccionId`, `autorPersonaId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionConvenio.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `convenioOrganizacionTable` (displaytag `d-`):  · ENTIDAD · ENTIDAD SELECCIONADA · EJECUTA · EVALUA · % FINANCIA
- Tabla `autorTable` (displaytag `d-`):  · PRESTADORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `produccionDestinatarioTable` (displaytag `d-`):  · TIPO DE DESTINATARIO · DESTINATARIO DE LA ACTIVIDAD SELECCIONADO
- Tabla `certificadoTable` (displaytag `d-`):  · DENOMINACIÓN DE LA CERTIFICACIÓN · AÑO DE AUTORIZACIÓN U OTORGAMIENTO

Formulario `cProduccionConvenioActionForm` → `bcoProduccionConvenio.do` (POST); botones: Limpiar texto, Nuevo, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `produccion` | input/text | Denominación del servicio |  |  |
| `tipoServicioId` | select/select-one | Tipo de servicio |  | 13 opciones |
| `otroTipoServicio` | input/text | Otro |  |  |
| `tipoFinalidadId` | select/select-one | Finalidad principal del servicio |  | 17 opciones |
| `fechaInicio` | input/text |  |  | datepicker |
| `fechaFin` | input/text | Fin |  | datepicker |
| `tipoModalidadId` | select/select-one | Modalidad del servicio |  | 3 opciones |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `campoAplicacionId` | select/select-one | Campo de aplicación |  | 280 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `financiamiento` | input/radio |  | sí | valores 0, 1; x2 |
| `monedaId` | select/select-one | (1) Moneda |  | 5 opciones |
| `montoPercibidoEntero` | input/text | Monto total |  |  |
| `montoPercibidoDecimal` | input/text | Monto total |  |  |
| `tipoFuncionId` | select/select-one | Función desempeñada en la producción del servicio |  | 6 opciones |
| `porcentajeParticipacionAutoria` | input/text | Porcentaje de participación en el servicio |  |  |
| `tipoConvenioId` | select/select-one | Modalidad de vinculación |  | 7 opciones |
| `theFile` | input/file |  |  |  |
| `exclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 2 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `linkFullText`, `action` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionDesarrollo.do?action=Nuevo&tipo=12`

Formulario — Datos básicos
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `autorTable` (displaytag `d-`):  · SEL. · AUTORES · INSTITUCIONES · ORDEN · MOVER
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `produccionOrganizacionTable` (displaytag `d-`):  · Entidad · Entidad Participante · Ejecuta · Evalua · Adopta · Demanda · Promueve · % Financia
- Tabla `tituloPropIntelectual` (displaytag `d-`):  ·  · Tipo protección · País · Fecha de solicitud · Estado
- Tabla `transferencia` (displaytag `d-`):  ·  · Destinatario · Año inicio · Año fin

Formulario `cProduccionDesarrolloActionForm` → `bcoProduccionDesarrollo.do` (POST); botones: Limpiar la descripción, Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoDesarrollo` | select/select-one |  |  | 5 opciones |
| `produccion` | input/text |  |  |  |
| `hdnresumen` | textarea/textarea |  |  |  |
| `anioReferencia` | input/text |  |  | datepicker |
| `qqfile` | input/file |  |  |  |
| `url` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `campoAplicacion` | select/select-one |  |  | 280 opciones |
| `especialidad` | input/text |  |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `autorSel` | input/radio |  |  | valores 0 |
| `autorParticipacionLabel` | input/text |  |  |  |
| `autorOrganizacionBuscar` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one |  |  | 8 opciones |
| `porcentajeParticipacionServicio` | input/text |  |  |  |
| `desarrolloFinanciamiento` | input/radio |  |  | valores 1, 0; x2 |
| `conTituloPropiedad` | input/radio |  |  | valores 1, 0; x2 |
| `transferenciaProduccion` | input/radio |  |  | valores 1, 0; x2 |
| `moneda` | select/select-one |  |  | 5 opciones; oculto al cargar |
| `montoEntero` | input/text |  |  | oculto al cargar |
| `montoDecimal` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionBuscar` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionEjecuta` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionEvalua` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionAdoptante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionDemandante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPromotora` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPorcentajeFinancia` | input/text |  |  | oculto al cargar |
| `motivoExclusion` | select/select-one |  |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `linkFullText`, `palabraId`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `autorSeleccionado`, `produccionOrganizacionOrganizacionId`, `produccionOrganizacionisOtraOrganizacion`, `produccionOrganizacionPaisId`, `produccionOrganizacionOrganizacionLabel`, `produccionOrganizacionProvinciaId`, `produccionOrganizacionRelacionadaId`, `produccionOrganizacionNivel`, `produccionOrganizacionRuta`, `produccionOrganizacionTipoId`, `produccionOrganizacionId`, `produccionOrganizacionSubsidioId`, `btnSubmit`, `tipoProduccion`, `campoDisciplinarJSON`, `palabraJSON`, `autorJSON`, `paAutorId`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `produccionId`, `produccionOrganizacionJSON`, `subFormSelected`, `subFormEvent`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionDesarrollo.do?action=Nuevo&tipo=13`

Formulario — Datos básicos
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `autorTable` (displaytag `d-`):  · SEL. · AUTORES · INSTITUCIONES · ORDEN · MOVER
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `produccionOrganizacionTable` (displaytag `d-`):  · Entidad · Entidad Participante · Ejecuta · Evalua · Adopta · Demanda · Promueve · % Financia
- Tabla `tituloPropIntelectual` (displaytag `d-`):  ·  · Tipo protección · País · Fecha de solicitud · Estado
- Tabla `transferencia` (displaytag `d-`):  ·  · Destinatario · Año inicio · Año fin

Formulario `cProduccionDesarrolloActionForm` → `bcoProduccionDesarrollo.do` (POST); botones: Limpiar la descripción, Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoDesarrollo` | select/select-one |  |  | 7 opciones |
| `produccion` | input/text |  |  |  |
| `hdnresumen` | textarea/textarea |  |  |  |
| `anioReferencia` | input/text |  |  | datepicker |
| `qqfile` | input/file |  |  |  |
| `url` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `campoAplicacion` | select/select-one |  |  | 280 opciones |
| `especialidad` | input/text |  |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `autorSel` | input/radio |  |  | valores 0 |
| `autorParticipacionLabel` | input/text |  |  |  |
| `autorOrganizacionBuscar` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one |  |  | 8 opciones |
| `porcentajeParticipacionServicio` | input/text |  |  |  |
| `desarrolloFinanciamiento` | input/radio |  |  | valores 1, 0; x2 |
| `conTituloPropiedad` | input/radio |  |  | valores 1, 0; x2 |
| `transferenciaProduccion` | input/radio |  |  | valores 1, 0; x2 |
| `moneda` | select/select-one |  |  | 5 opciones; oculto al cargar |
| `montoEntero` | input/text |  |  | oculto al cargar |
| `montoDecimal` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionBuscar` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionEjecuta` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionEvalua` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionAdoptante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionDemandante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPromotora` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPorcentajeFinancia` | input/text |  |  | oculto al cargar |
| `motivoExclusion` | select/select-one |  |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `linkFullText`, `palabraId`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `autorSeleccionado`, `produccionOrganizacionOrganizacionId`, `produccionOrganizacionisOtraOrganizacion`, `produccionOrganizacionPaisId`, `produccionOrganizacionOrganizacionLabel`, `produccionOrganizacionProvinciaId`, `produccionOrganizacionRelacionadaId`, `produccionOrganizacionNivel`, `produccionOrganizacionRuta`, `produccionOrganizacionTipoId`, `produccionOrganizacionId`, `produccionOrganizacionSubsidioId`, `btnSubmit`, `tipoProduccion`, `campoDisciplinarJSON`, `palabraJSON`, `autorJSON`, `paAutorId`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `produccionId`, `produccionOrganizacionJSON`, `subFormSelected`, `subFormEvent`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionDesarrollo.do?action=Nuevo&tipo=14`

Formulario — Datos básicos
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `autorTable` (displaytag `d-`):  · SEL. · AUTORES · INSTITUCIONES · ORDEN · MOVER
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `produccionOrganizacionTable` (displaytag `d-`):  · Entidad · Entidad Participante · Ejecuta · Evalua · Adopta · Demanda · Promueve · % Financia
- Tabla `tituloPropIntelectual` (displaytag `d-`):  ·  · Tipo protección · País · Fecha de solicitud · Estado
- Tabla `transferencia` (displaytag `d-`):  ·  · Destinatario · Año inicio · Año fin

Formulario `cProduccionDesarrolloActionForm` → `bcoProduccionDesarrollo.do` (POST); botones: Limpiar la descripción, Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoDesarrollo` | select/select-one |  |  | 6 opciones |
| `produccion` | input/text |  |  |  |
| `hdnresumen` | textarea/textarea |  |  |  |
| `anioReferencia` | input/text |  |  | datepicker |
| `qqfile` | input/file |  |  |  |
| `url` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `campoAplicacion` | select/select-one |  |  | 280 opciones |
| `especialidad` | input/text |  |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `autorSel` | input/radio |  |  | valores 0 |
| `autorParticipacionLabel` | input/text |  |  |  |
| `autorOrganizacionBuscar` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one |  |  | 8 opciones |
| `porcentajeParticipacionServicio` | input/text |  |  |  |
| `desarrolloFinanciamiento` | input/radio |  |  | valores 1, 0; x2 |
| `conTituloPropiedad` | input/radio |  |  | valores 1, 0; x2 |
| `transferenciaProduccion` | input/radio |  |  | valores 1, 0; x2 |
| `moneda` | select/select-one |  |  | 5 opciones; oculto al cargar |
| `montoEntero` | input/text |  |  | oculto al cargar |
| `montoDecimal` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionBuscar` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionEjecuta` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionEvalua` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionAdoptante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionDemandante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPromotora` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPorcentajeFinancia` | input/text |  |  | oculto al cargar |
| `motivoExclusion` | select/select-one |  |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `linkFullText`, `palabraId`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `autorSeleccionado`, `produccionOrganizacionOrganizacionId`, `produccionOrganizacionisOtraOrganizacion`, `produccionOrganizacionPaisId`, `produccionOrganizacionOrganizacionLabel`, `produccionOrganizacionProvinciaId`, `produccionOrganizacionRelacionadaId`, `produccionOrganizacionNivel`, `produccionOrganizacionRuta`, `produccionOrganizacionTipoId`, `produccionOrganizacionId`, `produccionOrganizacionSubsidioId`, `btnSubmit`, `tipoProduccion`, `campoDisciplinarJSON`, `palabraJSON`, `autorJSON`, `paAutorId`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `produccionId`, `produccionOrganizacionJSON`, `subFormSelected`, `subFormEvent`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionDesarrollo.do?action=Nuevo&tipo=15`

Formulario — Datos básicos
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `autorTable` (displaytag `d-`):  · SEL. · AUTORES · INSTITUCIONES · ORDEN · MOVER
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `produccionOrganizacionTable` (displaytag `d-`):  · Entidad · Entidad Participante · Ejecuta · Evalua · Adopta · Demanda · Promueve · % Financia
- Tabla `tituloPropIntelectual` (displaytag `d-`):  ·  · Tipo protección · País · Fecha de solicitud · Estado
- Tabla `transferencia` (displaytag `d-`):  ·  · Destinatario · Año inicio · Año fin

Formulario `cProduccionDesarrolloActionForm` → `bcoProduccionDesarrollo.do` (POST); botones: Limpiar la descripción, Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoDesarrollo` | select/select-one |  |  | 5 opciones |
| `produccion` | input/text |  |  |  |
| `hdnresumen` | textarea/textarea |  |  |  |
| `anioReferencia` | input/text |  |  | datepicker |
| `qqfile` | input/file |  |  |  |
| `url` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `campoAplicacion` | select/select-one |  |  | 280 opciones |
| `especialidad` | input/text |  |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `autorSel` | input/radio |  |  | valores 0 |
| `autorParticipacionLabel` | input/text |  |  |  |
| `autorOrganizacionBuscar` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one |  |  | 8 opciones |
| `porcentajeParticipacionServicio` | input/text |  |  |  |
| `desarrolloFinanciamiento` | input/radio |  |  | valores 1, 0; x2 |
| `conTituloPropiedad` | input/radio |  |  | valores 1, 0; x2 |
| `transferenciaProduccion` | input/radio |  |  | valores 1, 0; x2 |
| `moneda` | select/select-one |  |  | 5 opciones; oculto al cargar |
| `montoEntero` | input/text |  |  | oculto al cargar |
| `montoDecimal` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionBuscar` | input/text |  |  | oculto al cargar |
| `produccionOrganizacionEjecuta` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionEvalua` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionAdoptante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionDemandante` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPromotora` | input/checkbox |  |  | valores false; oculto al cargar |
| `produccionOrganizacionPorcentajeFinancia` | input/text |  |  | oculto al cargar |
| `motivoExclusion` | select/select-one |  |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `linkFullText`, `palabraId`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `autorSeleccionado`, `produccionOrganizacionOrganizacionId`, `produccionOrganizacionisOtraOrganizacion`, `produccionOrganizacionPaisId`, `produccionOrganizacionOrganizacionLabel`, `produccionOrganizacionProvinciaId`, `produccionOrganizacionRelacionadaId`, `produccionOrganizacionNivel`, `produccionOrganizacionRuta`, `produccionOrganizacionTipoId`, `produccionOrganizacionId`, `produccionOrganizacionSubsidioId`, `btnSubmit`, `tipoProduccion`, `campoDisciplinarJSON`, `palabraJSON`, `autorJSON`, `paAutorId`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `produccionId`, `produccionOrganizacionJSON`, `subFormSelected`, `subFormEvent`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionInformeTecnico.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 

Formulario `cProduccionInformeTecnicoActionForm` → `bcoProduccionInformeTecnico.do` (POST); botones: Limpiar texto, Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `produccion` | input/text | Tipo del informe o memoria |  |  |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `tipoProduccionTecnologica` | select/select-one | Tipo producción tecnológica |  | 7 opciones |
| `otroTipoProduccionTecnologica` | input/text | (1) Otro |  |  |
| `tipoNaturalezaProduccionTecnologica` | select/select-one | Naturaleza de la producción tecnológica |  | 11 opciones |
| `otroTipoNaturalezaProduccionTecnologica` | input/text | (2) Otra |  |  |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (3) URL |  |  |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `disciplina` | select/select-one | Disciplina |  | 22 opciones |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `porcentajeParticipacionAutoria` | input/text | Porcentaje de participación en la autoría |  |  |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoPercibidoEntero` | input/text | Monto percibido |  |  |
| `montoPercibidoDecimal` | input/text | Monto percibido |  |  |
| `fechaInicio` | input/text | Fecha inicio |  | datepicker |
| `fechaFin` | input/text | Fecha finalización |  | datepicker |
| `trabajoConfidencial` | input/text | En caso de tratarse de un trabajo confidencial, citar persona y/o contacto |  |  |
| `destinatario` | input/text | Destinatario |  |  |
| `tipoOrganizacion` | select/select-one | Tipo institución financiadora de la producción tecnológica |  | 10 opciones |
| `porcentajeParticipacionFinanciera` | input/text | Porcentaje de participación de la institución en el financiamiento |  |  |
| `campoAplicacion` | select/select-one | Campo de aplicación |  | 280 opciones |
| `theFile` | input/file |  |  |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `autorParticipacionProduccionId`, `autorPersonaId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionLibroPublicacion.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionLibroActionForm` → `bcoProduccionLibroPublicacion.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `produccion` | input/text | Título del libro |  |  |
| `isbn` | input/text | ISBN |  |  |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `totalVolumenesLibro` | input/text | Cantidad de volúmenes o tomos |  |  |
| `totalPaginasLibro` | input/text | Cantidad de páginas |  |  |
| `publicado` | input/radio |  | sí | valores 1, 2; x2 |
| `referato` | input/radio |  | sí | valores 0, 2; x2 |
| `pais` | select/select-one | País de edición |  | 244 opciones |
| `lugarEdicion` | input/text | Ciudad de la editorial |  |  |
| `editorial` | input/text | Editorial |  |  |
| `anioPublica` | input/text | (1) Año de publicación |  | datepicker |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (2) URL |  |  |
| `isAutor` | input/checkbox |  |  | valores on |
| `isEditor` | input/checkbox |  | sí | valores on |
| `isRevisor` | input/checkbox |  |  | valores on |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `qqfile` | input/file | Full text o texto completo |  |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `autorParticipacionProduccionId`, `autorPersonaId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaPublicacionCapituloLibro.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `compiladorTable` (displaytag `d-`):  · COMPILADORES, EDITORES U ORGANIZADORES DEL LIBRO · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionCapituloLibroActionForm` → `bcoProduccionListaPublicacionCapituloLibro.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoParteLibro` | select/select-one | Tipo de parte de libro |  | 9 opciones |
| `tituloLibro` | input/text | Título del libro |  |  |
| `produccion` | input/text | Título de la parte |  |  |
| `isbn` | input/text | ISBN |  |  |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `volumen` | input/text |  |  |  |
| `tomo` | input/text | Tomo |  |  |
| `numero` | input/text | Número |  |  |
| `totalPaginasLibro` | input/text | Cantidad de páginas de libro |  |  |
| `paginaInicial` | input/text |  |  |  |
| `paginaFinal` | input/text | Página final |  |  |
| `publicado` | input/radio |  | sí | valores 1, 2; x2 |
| `referato` | input/radio |  | sí | valores 0, 2; x2 |
| `pais` | select/select-one | País de edición |  | 244 opciones |
| `lugarEdicion` | input/text | Ciudad de la editorial |  |  |
| `editorial` | input/text | Editorial |  |  |
| `anioPublica` | input/text | (1) Año de publicación |  | datepicker |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (2) URL |  |  |
| `isAutor` | input/checkbox |  |  | valores on |
| `isEditor` | input/checkbox |  | sí | valores on |
| `isRevisor` | input/checkbox |  |  | valores on |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `compiladorParticipacionLabel` | input/text |  |  | x4 |
| `compiladorOrganizacionBuscar` | input/text |  |  | x4 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `theFile` | input/file | Full text o texto completo | sí |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `autorParticipacionProduccionId`, `autorPersonaId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaPublicacionCongreso.do?action=Nuevo&publicado=1`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionCongresoActionForm` → `bcoProduccionListaPublicacionCongreso.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoTrabajo` | select/select-one | Tipo de trabajo |  | 5 opciones |
| `produccion` | input/text | Título de trabajo |  |  |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `tipoPublicacion` | select/select-one | Tipo de publicación |  | 3 opciones |
| `tituloPublicacion` | input/text | Título de la/el revista/libro |  |  |
| `issnIsbn` | input/text | ISSN/ISBN |  |  |
| `paisEdicion` | select/select-one | País de edición |  | 244 opciones |
| `lugarPublicacion` | input/text | Ciudad de la editorial |  |  |
| `editorial` | input/text | Editorial |  |  |
| `anioPublica` | input/text | Año de publicación |  | datepicker |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (1) URL |  |  |
| `reunionCientifica` | input/text | Nombre del evento |  |  |
| `tipoReunion` | select/select-one | Tipo de evento |  | 14 opciones |
| `alcanceNacional` | input/checkbox |  | sí | valores 1 |
| `alcanceInternacional` | input/checkbox |  | sí | valores 1 |
| `paisEvento` | select/select-one | País del evento |  | 244 opciones |
| `lugarReunion` | input/text | Ciudad del evento |  |  |
| `fechaReunion` | input/text | Fecha del evento |  | datepicker |
| `institucionOrganizadora` | input/text | Institución organizadora |  |  |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `theFile` | input/file | Full text o texto completo | sí |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7774741-p`, `d-7774741-s`, `d-7774741-o`, `d-8150921-p`, `d-8150921-s`, `d-8150921-o`, `d-1531180-p`, `d-1531180-s`, `d-1531180-o`, `d-7775590-p`, `d-7775590-s`, `d-7775590-o`, `d-3912456-p`, `d-3912456-s`, `d-3912456-o`, `d-7776505-p`, `d-7776505-s`, `d-7776505-o`, `d-5834887-p`, `d-5834887-s`, `d-5834887-o`, `d-2967023-p`, `d-2967023-s`, `d-2967023-o`, `d-245505-p`, `d-245505-s`, `d-245505-o`, `d-5383825-p`, `d-5383825-s`, `d-5383825-o`, `d-6586321-p`, `d-6586321-s`, `d-6586321-o`, `d-2944114-p`, `d-2944114-s`, `d-2944114-o`, `d-4461471-p`, `d-4461471-s`, `d-4461471-o`, `d-3429963-p`, `d-3429963-s`, `d-3429963-o`, `d-1839375-p`, `d-1839375-s`, `d-1839375-o`, `d-4665157-p`, `d-4665157-s`, `d-4665157-o`, `d-4543575-p`, `d-4543575-s`, `d-4543575-o`, `d-7812730-p`, `d-7812730-s`, `d-7812730-o`, `d-1531850-p`, `d-1531850-s`, `d-1531850-o`, `autorParticipacionProduccionId`, `autorPersonaId` …

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaPublicacionTesis.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `directorTable` (displaytag `d-`): DIRECTOR DE TESIS
- Tabla `codirectorTable` (displaytag `d-`): CO-DIRECTOR DE TESIS
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionTesisActionForm` → `bcoProduccionListaPublicacionTesis.do` (POST); botones: Buscar, Limpiar, Nuevo, Borrar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `produccion` | input/text | Título de la tesis |  |  |
| `gradoAcademico` | select/select-one | Nivel educativo al que corresponde |  | 6 opciones |
| `filtroOrganizacionBuscar` | input/text |  |  |  |
| `filtroOrganizacionLabel` | textarea/textarea |  |  |  |
| `tituloObtenido` | input/text | Título obtenido |  |  |
| `fechaDefensa` | input/text | Fecha de defensa/aprobación |  | datepicker |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (1) URL |  |  |
| `apellidoDirector` | input/text |  |  |  |
| `nombreDirector` | input/text |  |  |  |
| `cuilDirector` | input/text |  |  |  |
| `apellidoCodirector` | input/text |  |  |  |
| `nombreCodirector` | input/text |  |  |  |
| `cuilCodirector` | input/text |  |  |  |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `qqfile` | input/file | Full text o texto completo | sí |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `filtroOrganizacionId`, `filtroOrganizacionIsOtra`, `idPersonaDirector`, `idPersonaCodirector`, `palabraId`, `linkFullText`, `actionSesion`, `palabraJSON`, `campoDisciplinarJSON`, `btnSubmit`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionOtra.do?action=Nuevo`

Formulario — SIGEVA
- Tabla `tiposSoporte` (displaytag `d-`): SOPORTE Y/O MEDIO DE DIFUSIÓN (ES POSIBLE SELECCIONAR MÁS DE UN MEDIO) · 
- Tabla `autorTable` (displaytag `d-`):  · AUTORES · INSTITUCIONES ·  · ORDEN
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `?` (displaytag `d-`):  ·  · 
- Tabla `campoDisciplinarTable` (displaytag `d-`):  · ÁREA DEL CONOCIMIENTO (MÁXIMO TRES)
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE

Formulario `cProduccionOtraActionForm` → `bcoProduccionOtra.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar resumen o abstract, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoOtraProduccionId` | select/select-one | Tipo de producción |  | 7 opciones |
| `otroTipoOtraProduccion` | input/text | (1)Otro tipo de producción |  |  |
| `produccion` | input/text | Título de la producción científico-tecnológica publicada |  |  |
| `idioma` | select/select-one | Idioma |  | 13 opciones |
| `anioPublicacion` | input/text | Año de publicación |  | datepicker |
| `isbn` | input/text | ISBN |  |  |
| `issn` | input/text | ISSN |  |  |
| `pais` | select/select-one | País |  | 244 opciones |
| `ciudad` | input/text | Ciudad |  |  |
| `cantPaginas` | input/text | Cantidad de páginas |  |  |
| `tipoSoporteChecked` | input/checkbox |  |  | valores 1, 2; x2 |
| `web` | input/text | (2) URL |  |  |
| `autorParticipacionLabel` | input/text |  |  | x4 |
| `autorOrganizacionBuscar` | input/text |  |  | x4 |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `palabraLabel` | input/text |  |  | x4 |
| `hdnresumen` | textarea/textarea |  | sí |  |
| `theFile` | input/file | Full text o texto completo | sí |  |
| `tipoAdjuntoMotivoExclusion` | select/select-one | Motivos de exclusión (OPT-OUT) |  | 4 opciones |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `autorParticipacionProduccionId`, `autorPersonaId`, `autorProduccionId`, `autorTipoProduccionId`, `palabraId`, `linkFullText`, `actionSesion`, `palabraJSON`, `campoDisciplinarJSON`, `btnSubmit`, `autorJSON`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcofinanciamientoCYTEventoEquipamiento.do?accion=nuevo&grupoFinanciamientoId=3`

Formulario — FINANCIAMIENTO CYT BANCO DE DATOS
- Tabla `subsidioOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCION · INSTITUCION SELECCIONADA · EJECUTA · EVALUA · % FINANCIA

Formulario `cFinanciamientoCYTEventoEquipamientoActionForm` → `bcofinanciamientoCYTEventoEquipamiento.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoFinanciamiento` | select/select-one | Tipo de subsidio |  | 3 opciones; x2 |
| `titulo` | input/text | Actividad objeto del financiamiento |  |  |
| `fechaDesde` | input/text |  |  | datepicker |
| `fechaHasta` | input/text | Hasta |  | datepicker |
| `descripcion` | textarea/textarea | Breve descripción del proyecto o actividad objeto de financiamiento |  |  |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoEntero` | input/text | Monto total |  |  |
| `montoDecimal` | input/text | Monto total |  |  |
| `subsidioOrganizacionBuscar` | input/text |  |  |  |
| `subsidioOrganizacionEjecuta` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionEvalua` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPorcentajeFinancia` | input/text |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `subsidioOrganizacionOrganizacionId`, `subsidioOrganizacionisOtraOrganizacion`, `subsidioOrganizacionPaisId`, `subsidioOrganizacionOrganizacionLabel`, `subsidioOrganizacionProvinciaId`, `subsidioOrganizacionRelacionadaId`, `subsidioOrganizacionNivel`, `subsidioOrganizacionRuta`, `subsidioOrganizacionTipoId`, `subsidioOrganizacionId`, `subsidioOrganizacionSubsidioId`, `id`, `subsidioOrganizacionJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcofinanciamientoCYTEventoEquipamiento.do?accion=nuevo&grupoFinanciamientoId=4`

Formulario — FINANCIAMIENTO CYT BANCO DE DATOS
- Tabla `subsidioOrganizacionTable` (displaytag `d-`):  · BUSCAR INSTITUCION · INSTITUCION SELECCIONADA · EJECUTA · EVALUA · % FINANCIA

Formulario `cFinanciamientoCYTEventoEquipamientoActionForm` → `bcofinanciamientoCYTEventoEquipamiento.do` (POST); botones: Nuevo, Borrar, Buscar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `titulo` | input/text | Actividad objeto del financiamiento |  |  |
| `fechaDesde` | input/text |  |  | datepicker |
| `fechaHasta` | input/text | Hasta |  | datepicker |
| `descripcion` | textarea/textarea | Breve descripción del proyecto o actividad objeto de financiamiento |  |  |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoEntero` | input/text | Monto total |  |  |
| `montoDecimal` | input/text | Monto total |  |  |
| `subsidioOrganizacionBuscar` | input/text |  |  |  |
| `subsidioOrganizacionEjecuta` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionEvalua` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPorcentajeFinancia` | input/text |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `subsidioOrganizacionOrganizacionId`, `subsidioOrganizacionisOtraOrganizacion`, `subsidioOrganizacionPaisId`, `subsidioOrganizacionOrganizacionLabel`, `subsidioOrganizacionProvinciaId`, `subsidioOrganizacionRelacionadaId`, `subsidioOrganizacionNivel`, `subsidioOrganizacionRuta`, `subsidioOrganizacionTipoId`, `subsidioOrganizacionId`, `subsidioOrganizacionSubsidioId`, `id`, `tipoFinanciamiento`, `subsidioOrganizacionJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=11`

Formulario — FINANCIAMIENTO CYT BANCO DE DATOS
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `subsidioOrganizacionTable` (displaytag `d-`):  · ENTIDAD · ENTIDAD PARTICIPANTE · EJECUTA · EVALUA · ADOPTA · DEMANDA · PROMUEVE · % FINANCIA
- Tabla `directorTable` (displaytag `d-`): DIRECTOR DEL PROYECTO
- Tabla `codirectorTable` (displaytag `d-`): CO-DIRECTOR DEL PROYECTO

Formulario `cFinanciamientoCYTProyectoActionForm` → `bcofinanciamientoCYTProyecto.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoActividadSubsidio` | select/select-one | Tipo de actividad |  | 4 opciones |
| `titulo` | input/text | Denominación del proyecto |  |  |
| `tipoProyecto` | input/text | Tipo de proyecto |  |  |
| `codigoProyecto` | input/text | (1) Código de identificación |  |  |
| `fechaDesde` | input/text |  |  | datepicker |
| `fechaHasta` | input/text | Hasta |  | datepicker |
| `descripcion` | textarea/textarea | Breve descripción del proyecto o actividad objeto de financiamiento |  |  |
| `campoAplicacion` | select/select-one | Campo aplicación |  | 280 opciones |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoEntero` | input/text | Monto total |  |  |
| `montoDecimal` | input/text | Monto total |  |  |
| `subsidioOrganizacionBuscar` | input/text |  |  |  |
| `subsidioOrganizacionEjecuta` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionEvalua` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionAdoptante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionDemandante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPromotora` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPorcentajeFinancia` | input/text |  |  |  |
| `apellidoDirector` | input/text |  |  |  |
| `nombreDirector` | input/text |  |  |  |
| `cuilDirector` | input/text |  |  |  |
| `apellidoCodirector` | input/text |  |  |  |
| `nombreCodirector` | input/text |  |  |  |
| `cuilCodirector` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one | Función desempeñada |  | 8 opciones; x2 |
| `fechaInicioParticipacion` | input/text |  |  | datepicker |
| `fechaFinParticipacion` | input/text | Fin |  | datepicker |
| `qqfile` | input/file | Documentación de otorgamiento del proyecto |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `palabraId`, `subsidioOrganizacionOrganizacionId`, `subsidioOrganizacionisOtraOrganizacion`, `subsidioOrganizacionPaisId`, `subsidioOrganizacionOrganizacionLabel`, `subsidioOrganizacionProvinciaId`, `subsidioOrganizacionRelacionadaId`, `subsidioOrganizacionNivel`, `subsidioOrganizacionRuta`, `subsidioOrganizacionTipoId`, `subsidioOrganizacionId`, `subsidioOrganizacionSubsidioId`, `idPersonaDirector`, `idPersonaCodirector`, `linkArchivo`, `id`, `tipoFinanciamiento`, `subsidioOrganizacionJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `palabraJSON`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=12`

Formulario — FINANCIAMIENTO CYT BANCO DE DATOS
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `subsidioTipoMedioDivulgacionTable` (displaytag `d-`):  · TIPO DE MEDIO DE DIVULGACIÓN
- Tabla `subsidioOrganizacionTable` (displaytag `d-`):  · ENTIDAD · ENTIDAD PARTICIPANTE · EJECUTA · EVALUA · ADOPTA · DEMANDA · PROMUEVE · % FINANCIA
- Tabla `directorTable` (displaytag `d-`): DIRECTOR DEL PROYECTO
- Tabla `codirectorTable` (displaytag `d-`): CO-DIRECTOR DEL PROYECTO

Formulario `cFinanciamientoCYTProyectoActionForm` → `bcofinanciamientoCYTProyecto.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `titulo` | input/text | Denominación del proyecto |  |  |
| `tipoProyecto` | input/text | Tipo de proyecto |  |  |
| `codigoProyecto` | input/text | (1) Código de identificación |  |  |
| `fechaDesde` | input/text |  |  | datepicker |
| `fechaHasta` | input/text | Hasta |  | datepicker |
| `descripcion` | textarea/textarea | Breve descripción del proyecto o actividad objeto de financiamiento |  |  |
| `campoAplicacion` | select/select-one | Campo aplicación |  | 280 opciones |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoEntero` | input/text | Monto total |  |  |
| `montoDecimal` | input/text | Monto total |  |  |
| `tipoMedioDivulgacionId` | select/select-one |  |  | 17 opciones; x3 |
| `subsidioOrganizacionBuscar` | input/text |  |  |  |
| `subsidioOrganizacionEjecuta` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionEvalua` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionAdoptante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionDemandante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPromotora` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPorcentajeFinancia` | input/text |  |  |  |
| `apellidoDirector` | input/text |  |  |  |
| `nombreDirector` | input/text |  |  |  |
| `cuilDirector` | input/text |  |  |  |
| `apellidoCodirector` | input/text |  |  |  |
| `nombreCodirector` | input/text |  |  |  |
| `cuilCodirector` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one | Función desempeñada |  | 7 opciones; x2 |
| `fechaInicioParticipacion` | input/text |  |  | datepicker |
| `fechaFinParticipacion` | input/text | Fin |  | datepicker |
| `qqfile` | input/file | Documentación de otorgamiento del proyecto |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `palabraId`, `subsidioOrganizacionOrganizacionId`, `subsidioOrganizacionisOtraOrganizacion`, `subsidioOrganizacionPaisId`, `subsidioOrganizacionOrganizacionLabel`, `subsidioOrganizacionProvinciaId`, `subsidioOrganizacionRelacionadaId`, `subsidioOrganizacionNivel`, `subsidioOrganizacionRuta`, `subsidioOrganizacionTipoId`, `subsidioOrganizacionId`, `subsidioOrganizacionSubsidioId`, `idPersonaDirector`, `idPersonaCodirector`, `linkArchivo`, `id`, `tipoFinanciamiento`, `subsidioOrganizacionJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `palabraJSON`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcofinanciamientoCYTProyecto.do?accion=nuevo&tipoFinanciamientoId=5`

Formulario — FINANCIAMIENTO CYT BANCO DE DATOS
- Tabla `campoDisciplinarTable` (displaytag `d-`): ÁREA DEL CONOCIMIENTO
- Tabla `palabraTable` (displaytag `d-`):  · PALABRA CLAVE
- Tabla `subsidioOrganizacionTable` (displaytag `d-`):  · ENTIDAD · ENTIDAD PARTICIPANTE · EJECUTA · EVALUA · ADOPTA · DEMANDA · PROMUEVE · % FINANCIA
- Tabla `directorTable` (displaytag `d-`): DIRECTOR DEL PROYECTO
- Tabla `codirectorTable` (displaytag `d-`): CO-DIRECTOR DEL PROYECTO

Formulario `cFinanciamientoCYTProyectoActionForm` → `bcofinanciamientoCYTProyecto.do` (POST); botones: Nuevo, Borrar, Buscar, Limpiar, Guardar, Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `tipoActividad` | select/select-one | Tipo de actividad de I+D |  | 4 opciones |
| `titulo` | input/text | Denominación del proyecto |  |  |
| `tipoProyecto` | input/text | Tipo de proyecto |  |  |
| `codigoProyecto` | input/text | (1) Código de identificación |  |  |
| `fechaDesde` | input/text |  |  | datepicker |
| `fechaHasta` | input/text | Hasta |  | datepicker |
| `descripcion` | textarea/textarea | Breve descripción del proyecto o actividad objeto de financiamiento |  |  |
| `campoAplicacion` | select/select-one | Campo aplicación |  | 280 opciones |
| `campo_0` | select/select-one |  |  | 49 opciones |
| `campo_0_0` | select/select-one |  |  | 1 opciones |
| `especialidad` | input/text | Especialidad |  |  |
| `palabraLabel` | input/text |  |  | x4 |
| `moneda` | select/select-one | Moneda |  | 5 opciones |
| `montoEntero` | input/text | Monto total |  |  |
| `montoDecimal` | input/text | Monto total |  |  |
| `subsidioOrganizacionBuscar` | input/text |  |  |  |
| `subsidioOrganizacionEjecuta` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionEvalua` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionAdoptante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionDemandante` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPromotora` | input/checkbox |  |  | valores false |
| `subsidioOrganizacionPorcentajeFinancia` | input/text |  |  |  |
| `apellidoDirector` | input/text |  |  |  |
| `nombreDirector` | input/text |  |  |  |
| `cuilDirector` | input/text |  |  |  |
| `apellidoCodirector` | input/text |  |  |  |
| `nombreCodirector` | input/text |  |  |  |
| `cuilCodirector` | input/text |  |  |  |
| `funcionDesempeniada` | select/select-one | Función desempeñada |  | 7 opciones; x2 |
| `fechaInicioParticipacion` | input/text |  |  | datepicker |
| `fechaFinParticipacion` | input/text | Fin |  | datepicker |
| `qqfile` | input/file | Documentación de otorgamiento del proyecto |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `palabraId`, `subsidioOrganizacionOrganizacionId`, `subsidioOrganizacionisOtraOrganizacion`, `subsidioOrganizacionPaisId`, `subsidioOrganizacionOrganizacionLabel`, `subsidioOrganizacionProvinciaId`, `subsidioOrganizacionRelacionadaId`, `subsidioOrganizacionNivel`, `subsidioOrganizacionRuta`, `subsidioOrganizacionTipoId`, `subsidioOrganizacionId`, `subsidioOrganizacionSubsidioId`, `idPersonaDirector`, `idPersonaCodirector`, `linkArchivo`, `id`, `tipoFinanciamiento`, `subsidioOrganizacionJSON`, `btnSubmit`, `buscarOrganizacion`, `buscarOrganizacionControl`, `buscarOrganizacionIndex`, `palabraJSON`, `campoDisciplinarJSON`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `filtroImprimirCurriculum.do`

Formulario — Imprimir los formularios seleccionados

Formulario `cFiltroImprimirCurriculumActionForm` → `filtroImprimirCurriculum.do` (POST); botones: Imprimir CV (pdf), Imprimir CV (doc), Volver

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `fechaDesde` | input/text | Fecha desde |  | datepicker |
| `fechaHasta` | input/text | Fecha hasta |  | datepicker |
| `formulariosImprimir` | input/checkbox |  |  | valores datosPerIndentificacion, datosPerDirResidencial, datosPerLugarTrabajo, datosPersExperticia, formAcademicaUnivDoc, formAcademicaUnivMae, formAcademicaUnivEspe, formAcademicaGrado, formAcademicaNoUniv, formAcademicaMedio, formAcademicaBasico, formComplementariaSalud, formComplementariaPosDoc, formComplementariaPosGrado, formComplementariaIdiomas, formComplementariaEstancia, docenciaNivelSuperior, docenciaNivelTerciario, docenciaNivelBasico, docenciaCursos, cargosGestionInsti, cargosIDCyT, cargosIDProgIncent, cargosIDOtroTipoInst, otrosCargos, antFormBecarios, antFormTesistas, antFormInv, antFormPasantes, antFormApoyo, antFinanciamientoProyID, antFinanciamientoProyExt, antFinanciamientoProyComu, antFinanciamientoSubEvent, antFinanciamientoSubInfra, antFinanciamientoBecaRec, extActDivulgacion, extRural, extServSociales, extDivulgacionCientifica, extOtro, evalPersonal, evalProgramas, evalRevistas, evalInstitucional, evalOtros, otrasActOperSistemas, otrasActNormalizacion, otrasActEjercicioProf, otrasActCyT, prodCArticulos, prodCLibros, prodCParteLibro, prodCEventosPublic, prodCEventosNoPublic, prodCTesis, prodCDemasProd, prodTInformeTecnico, prodTServicio, prodMusicalSonora, prodVisual, prodAudiovisual, prodCorporal, prodNarrativo, prodDramatico, prodGuion, prodLiterario, prodOtraArtistica, OtrosAntParticipacionEventos, premiosDist, prodBienes, desaProd, desaProcSocio, desaProcGestEmp, desaProcGestPub, participacionEvent, trabajosCTNoPub, partipacionRedes, membresiasAsoc, coordinacionProy, gestionEdit, datosInvestigacion; x82; oculto al cargar |

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `instructivoBancoDeDatoNavOper.do`

Menu — SIGEVA

Formulario `(sin nombre)` → `indexBancoDatos.do` (POST); botones: Volver a Instructivos

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 1

### `bcoCompartirFormulario.do?idGrupo=0&idMenu=1478&idModulo=1`

Formulario — SIGEVA

Formulario `cCompartirFormularioActionForm` → `bcoCompartirFormulario.do` (POST); botones: Compartir, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `organizacion` | select/select-one | Institución |  |  |
| `contrasenia` | input/password | Contraseña |  |  |
| `confirmaContrasenia` | input/password | Confirmar contraseña |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `usrAlta`, `usrModif`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCompartirFormulario.do?idGrupo=0&idMenu=814&idModulo=1`

Formulario — SIGEVA

Formulario `cCompartirFormularioActionForm` → `bcoCompartirFormulario.do` (POST); botones: Compartir, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `organizacion` | select/select-one | Institución |  |  |
| `contrasenia` | input/password | Contraseña |  |  |
| `confirmaContrasenia` | input/password | Confirmar contraseña |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `id`, `usrAlta`, `usrModif`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoRoles.do?idGrupo=0&idMenu=1479&idModulo=1`

Lista — SIGEVA
- Tabla `tRoles` (displaytag `d-445999`): NUEVO · ROL · APELLIDO Y NOMBRE · CUIL · FECHA ALTA

Formulario `cRolesActionForm` → `bcoRoles.do` (POST); botones: Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-4563864-p`, `d-4563864-s`, `d-4563864-o`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `indexBancoDatos.do?idGrupo=0&idMenu=0&idModulo=1`

Menu — BANCO DE DATOS DE ACTIVIDADES DE CIENCIA Y TÉCNICA BANCO DE DATOS

Formulario `cIndexBancoDatosActionForm` → `indexBancoDatos.do` (POST)

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `instructivoConvocatoriaGral.do?idGrupo=0&idMenu=1477&idModulo=1`

Menu — SIGEVA

Formulario `(sin nombre)` → `indexBancoDatos.do` (POST); botones: Salir

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 2

### `bcoAjustes.do?idGrupo=2&idMenu=1480&idModulo=2`

Menu — SIGEVA

Formulario `cDatoPersonalAjustesActionForm` → `bcoAjustes.do` (POST); botones: Guardar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `recibirInformacion` | input/radio |  | sí | valores 1, 0; x2 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoDatoPersonalDireccion.do?idGrupo=2&idMenu=1451&idModulo=2&tipoDir=residencial`

Formulario — SIGEVA

Formulario `cDatoPersonalDireccionActionForm` → `bcoDatoPersonalDireccion.do` (POST); botones: Guardar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `pais` | select/select-one | País |  | x2 |
| `provincia` | select/select-one | Provincia |  | x2 |
| `partido` | select/select-one | (1) Partido/Departamento |  | x2 |
| `localidad` | select/select-one | Localidad |  | x2 |
| `casillaPostal` | input/text | Casilla postal |  | x2 |
| `telefonoPais` | input/text |  |  | x2 |
| `telefonoArea` | input/text |  | sí | x2 |
| `telefonoCaracteristica` | input/text |  | sí | x2 |
| `telefonoNumero` | input/text |  | sí | x2 |
| `telefonoInterno` | input/text |  |  | x2 |
| `celular` | input/text | Teléfono celular |  | x2 |
| `fax` | input/text | Fax |  | x2 |
| `mail` | input/text | E-mail |  | x2 |
| `sitioWeb` | input/text | URL |  | x2 |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `calle`, `numero`, `piso`, `dpto`, `otroPartido`, `otraLocalidad`, `codigoPostal`, `estado`, `tramite`, `usrAlta`, `fechaAlta`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoDatoPersonalDireccion.do?idGrupo=2&idMenu=1452&idModulo=2&tipoDir=laboral`

Formulario — SIGEVA

Formulario `cDatoPersonalDireccionActionForm` → `bcoDatoPersonalDireccion.do` (POST); botones: Guardar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `organizacionLaboralLabel` | textarea/textarea |  |  | x2 |
| `calle` | input/text | Calle |  | x2 |
| `numero` | input/text | Número |  | x2 |
| `piso` | input/text | Piso |  | x2 |
| `dpto` | input/text | Oficina/Departamento |  | x2 |
| `pais` | select/select-one | País |  |  |
| `provincia` | select/select-one | Provincia |  |  |
| `partido` | select/select-one | (1) Partido/Departamento |  |  |
| `otroPartido` | input/text | (2) Otro |  | x2 |
| `localidad` | select/select-one | Localidad |  |  |
| `otraLocalidad` | input/text | (3) Otro |  | x2 |
| `codigoPostal` | input/text | Código postal |  | x2 |
| `casillaPostal` | input/text | Casilla postal |  | x2 |
| `telefonoPais` | input/text |  |  | x2 |
| `telefonoArea` | input/text |  | sí | x2 |
| `telefonoCaracteristica` | input/text |  | sí | x2 |
| `telefonoNumero` | input/text |  | sí | x2 |
| `telefonoInterno` | input/text |  |  | x2 |
| `celular` | input/text | Teléfono celular |  | x2 |
| `fax` | input/text | Fax |  | x2 |
| `mail` | input/text | E-mail |  | x2 |
| `sitioWeb` | input/text | URL |  | x2 |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `organizacionLaboralId`, `estado`, `tramite`, `usrAlta`, `fechaAlta`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoDatoPersonalIdentificacion.do?idGrupo=2&idMenu=1450&idModulo=2`

Formulario — SIGEVA

Formulario `cDatoPersonalIdentificacionActionForm` → `bcoDatoPersonalIdentificacion.do` (POST); botones: Guardar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `nombre` | input/text | Nombre/s |  | x2 |
| `apellido` | input/text | Apellido/s |  | x2 |
| `apellidoCasada` | input/text | Apellido/s de casada |  |  |
| `sexoId` | input/radio | Sexo |  | valores 1, 0, 2; x4 |
| `estadoCivilId` | select/select-one | Estado civil |  |  |
| `cantidadHijos` | input/text | Cantidad hijos |  |  |
| `paisNacionalidadId` | select/select-one | Nacionalidad |  |  |
| `condicionNacionalidadId` | select/select-one | (1) Condición nacionalidad |  |  |
| `tipoDocumentoId` | select/select-one | Tipo de documento |  |  |
| `paisEmisionPasaporteId` | select/select-one | (2) País emisión pasaporte |  |  |
| `numeroDocumento` | input/text | Número de documento |  |  |
| `cuitCuil` | input/text | (3) (4) C.U.I.T./C.U.I.L. |  | x2 |
| `paisNacimientoId` | select/select-one | País |  |  |
| `provinciaNacimientoId` | select/select-one | Provincia |  |  |
| `partidoNacimientoId` | select/select-one | Partido/Departamento |  |  |
| `otroPartidoNacimiento` | input/text | (5) Otro |  |  |
| `fechaNacimiento` | input/text |  |  | x2 |
| `informacionAdicional` | textarea/textarea | Informaciones adicionales |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExperticia.do?idGrupo=2&idMenu=1465&idModulo=2`

Formulario — SIGEVA
- Tabla `lineaInvestigacionTable` (displaytag `d-`):  · ÁREA DE ACTUACIÓN Y LÍNEAS DE INVESTIGACIÓN
- Tabla `palabraCastellanoTable` (displaytag `d-`):  · PALABRA CLAVE EN ESPAÑOL
- Tabla `palabraInglesTable` (displaytag `d-`):  · PALABRA CLAVE EN INGLÉS
- Tabla `persona.experticia.capacidadTecnologica` (displaytag `d-`):  · CÓDIGO · DESCRIPCIÓN · DESCRIPTION

Formulario `cExperticiaActionForm` → `bcoExperticia.do` (POST); botones: Nuevo, Borrar, Guardar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `hdnresumen` | textarea/textarea |  | sí |  |
| `campo_0` | select/select-one |  |  |  |
| `campo_0_0` | select/select-one |  |  |  |
| `linea_0` | input/text |  |  |  |
| `campo_1` | select/select-one |  |  |  |
| `campo_1_1` | select/select-one |  |  |  |
| `linea_1` | input/text |  |  |  |
| `palabraCastellanoLabel` | input/text |  |  | x4 |
| `palabraInglesLabel` | input/text |  |  | x4 |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `regId_0`, `regId_1`, `palabraCastellanoId`, `palabraInglesId`, `colCapacidadTecnologicaId`, `palabraCastellanoJSON`, `palabraInglesJSON`, `lineaInvestigacionJSON`, `btnSubmit`, `btnIdCT`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 3

### `bcoFormacionAcademica.do?idGrupo=3&idMenu=1453&idModulo=3`

Lista — SIGEVA
- Tabla `usr.formacionAcademica.doctorado` (displaytag `d-3305891`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · CARRERA
- Tabla `usr.formacionAcademica.maestria` (displaytag `d-6704370`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · CARRERA
- Tabla `usr.formacionAcademica.especializacion` (displaytag `d-267567`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · CARRERA
- Tabla `usr.formacionAcademica.grado` (displaytag `d-7393995`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · CARRERA
- Tabla `usr.formacionAcademica.terciarioNoUniversitario` (displaytag `d-725065`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · CARRERA
- Tabla `usr.formacionAcademica.nivelMedio` (displaytag `d-1713622`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN
- Tabla `usr.formacionAcademica.nivelBasico` (displaytag `d-5138349`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN

Formulario `cFormacionAcademicaActionForm` → `bcoFormacionAcademica.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-3305891-p`, `d-3305891-s`, `d-3305891-o`, `d-6704370-p`, `d-6704370-s`, `d-6704370-o`, `d-267567-p`, `d-267567-s`, `d-267567-o`, `d-7393995-p`, `d-7393995-s`, `d-7393995-o`, `d-725065-p`, `d-725065-s`, `d-725065-o`, `d-1713622-p`, `d-1713622-s`, `d-1713622-o`, `d-5138349-p`, `d-5138349-s`, `d-5138349-o`, `d-3399291-p`, `d-3399291-s`, `d-3399291-o`

Acciones no visitadas: `bcoFormacionAcademicaDetalle.do?accion=borrar&id=N&nivel=1` (accion sobre registros (borrar)); `bcoFormacionAcademicaDetalle.do?accion=borrar&id=N&nivel=5` (accion sobre registros (borrar)); `bcoFormacionAcademicaDetalle.do?accion=editar&id=N&nivel=1` (accion sobre registros (editar)); `bcoFormacionAcademicaDetalle.do?accion=editar&id=N&nivel=5` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=21` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFormacionComplementariaLista.do?idGrupo=3&idMenu=1454&idModulo=3`

Lista — SIGEVA
- Tabla `persona.formacionComplementaria.salud` (displaytag `d-5236396`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN · ESPECIALIDAD
- Tabla `persona.formacionComplementaria.posdoctorado` (displaytag `d-2007390`): NUEVO · FECHA INGRESO · FECHA EGRESO · INSTITUCIÓN
- Tabla `persona.formacionComplementaria.curso` (displaytag `d-5235699`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN · DENOMINACIÓN DEL CURSO
- Tabla `persona.formacionComplementaria.idioma` (displaytag `d-7318382`): NUEVO · IDIOMA · DOMINIO · CERTIFICADO · AÑO
- Tabla `usr.actividad.pasantia` (displaytag `d-2879534`): NUEVO · AÑO INICIO · AÑO FIN · TIPO DE TAREAS · DIRECTOR

Formulario `(sin nombre)` → `bcoFormacionComplementariaLista.do` (POST); botones: Importar, Salir

Ocultos: `d-5236396-p`, `d-5236396-s`, `d-5236396-o`, `d-2007390-p`, `d-2007390-s`, `d-2007390-o`, `d-5235699-p`, `d-5235699-s`, `d-5235699-o`, `d-7318382-p`, `d-7318382-s`, `d-7318382-o`

Acciones no visitadas: `bcoFormacionComplementariaCurso.do?action=Borrar&formacionId=N` (accion sobre registros (borrar)); `bcoFormacionComplementariaCurso.do?action=Editar&formacionId=N` (accion sobre registros (editar)); `bcoFormacionComplementariaIdioma.do?action=Borrar&formacionId=N` (accion sobre registros (borrar)); `bcoFormacionComplementariaIdioma.do?action=Editar&formacionId=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=47` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=48` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=49` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=50` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=54` (ruta prohibida (sesion, importacion o descarga)); `bcoListaActividadEstanciaPasantia.do?accion=borrar&actividadId=N&tipoActividad=1` (accion sobre registros (borrar)); `bcoListaActividadEstanciaPasantia.do?accion=editar&actividadId=N&tipoActividad=1` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 4

### `bcoCargoDocenteLista.do?idGrupo=4&idMenu=1455&idModulo=4`

Lista — SIGEVA
- Tabla `persona.cargoDocente.nivelSuperior` (displaytag `d-6314371`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN
- Tabla `persona.cargoDocente.nivelTerciario` (displaytag `d-2137604`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN
- Tabla `persona.cargoDocente.nivelBasicoMedio` (displaytag `d-1335539`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN
- Tabla `persona.cargoDocente.nivelCapacitacion` (displaytag `d-4077089`): NUEVO · FECHA INICIO · FECHA FIN · INSTITUCIÓN

Formulario `cCargoDocenteListaActionForm` → `bcoCargoDocenteLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-6314371-p`, `d-6314371-s`, `d-6314371-o`, `d-2137604-p`, `d-2137604-s`, `d-2137604-o`, `d-1335539-p`, `d-1335539-s`, `d-1335539-o`, `d-4077089-p`, `d-4077089-s`, `d-4077089-o`

Acciones no visitadas: `bcoCargoDocenteNivelBasicoMedio.do?accion=Borrar&cargoId=N` (accion sobre registros (borrar)); `bcoCargoDocenteNivelBasicoMedio.do?accion=Editar&cargoId=N` (accion sobre registros (editar)); `bcoCargoDocenteNivelCapacitacion.do?accion=Borrar&cargoId=N` (accion sobre registros (borrar)); `bcoCargoDocenteNivelCapacitacion.do?accion=Editar&cargoId=N` (accion sobre registros (editar)); `bcoCargoDocenteNivelSuperior.do?accion=Borrar&cargoId=N` (accion sobre registros (borrar)); `bcoCargoDocenteNivelSuperior.do?accion=Editar&cargoId=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=39` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=40` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=41` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=42` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoGestionLista.do?idGrupo=4&idMenu=1457&idModulo=4`

Lista — SIGEVA
- Tabla `persona.cargoDocente.cargosGestion` (displaytag `d-7297766`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO

Formulario `cCargoGestionListaActionForm` → `bcoCargoGestionLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7297766-p`, `d-7297766-s`, `d-7297766-o`

Acciones no visitadas: `bcoCargoGestionAction.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoCargoGestionAction.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=51` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoIDLista.do?idGrupo=4&idMenu=1456&idModulo=4`

Lista — SIGEVA
- Tabla `persona.cargoID.OrganizacionCT` (displaytag `d-94152`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO
- Tabla `persona.cargoID.Incentivos` (displaytag `d-472981`): NUEVO · FECHA INICIO · FECHA FIN · AÑO CATEGORIZACIÓN · CATEGORIA INCENTIVOS · INSTITUCIÓN DE TRABAJO
- Tabla `persona.cargoID.OtraOrganizacion` (displaytag `d-5866723`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO

Formulario `cCargoIDListaActionForm` → `bcoCargoIDLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-94152-p`, `d-94152-s`, `d-94152-o`, `d-472981-p`, `d-472981-s`, `d-472981-o`, `d-5866723-p`, `d-5866723-s`, `d-5866723-o`

Acciones no visitadas: `bcoCargoIDIncentivos.do?action=Borrar&cargoIdId=N` (accion sobre registros (borrar)); `bcoCargoIDIncentivos.do?action=Editar&cargoIdId=N` (accion sobre registros (editar)); `bcoCargoIDOrganizacionCT.do?action=Borrar&cargoIdId=N` (accion sobre registros (borrar)); `bcoCargoIDOrganizacionCT.do?action=Editar&cargoIdId=N` (accion sobre registros (editar)); `bcoCargoIDOtraOrganizacion.do?action=Borrar&cargoIdId=N` (accion sobre registros (borrar)); `bcoCargoIDOtraOrganizacion.do?action=Editar&cargoIdId=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=31` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=32` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=33` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoCargoOtroLista.do?idGrupo=4&idMenu=1458&idModulo=4`

Lista — SIGEVA
- Tabla `persona.cargo.otrosCargos` (displaytag `d-7953626`): NUEVO · FECHA INICIO · FECHA FIN · CARGO · INSTITUCIÓN DE TRABAJO

Formulario `cCargoOtroListaActionForm` → `bcoCargoOtroLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-7953626-p`, `d-7953626-s`, `d-7953626-o`

Acciones no visitadas: `bcoCargoOtroAction.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoCargoOtroAction.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=16` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 5

### `bcoActividadEvaluacionLista.do?idGrupo=5&idMenu=1462&idModulo=5`

Lista — SIGEVA
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo1` (displaytag `d-4114002`): NUEVO · AÑO INICIO · AÑO FIN · TIPO EVALUACIÓN · INSTITUCIÓN CONVOCANTE
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo2` (displaytag `d-4114003`): NUEVO · AÑO INICIO · AÑO FIN · INSTITUCIÓN CONVOCANTE
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo3` (displaytag `d-4114004`): NUEVO · AÑO INICIO · AÑO FIN · TÍTULO DE LA REVISTA
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo4` (displaytag `d-4114005`): NUEVO · AÑO INICIO · AÑO FIN · TIPO DE EVALUACIÓN INSTITUCIONAL · INSTITUCIÓN CONVOCANTE
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo5` (displaytag `d-4114006`): NUEVO · AÑO INICIO · AÑO FIN · TIPO EVALUACIÓN · INSTITUCIÓN CONVOCANTE

Formulario `(sin nombre)` → `bcoActividadEvaluacionLista.do` (POST); botones: Importar, Salir

Ocultos: `d-4114002-p`, `d-4114002-s`, `d-4114002-o`, `d-4114003-p`, `d-4114003-s`, `d-4114003-o`, `d-4114004-p`, `d-4114004-s`, `d-4114004-o`, `d-4114005-p`, `d-4114005-s`, `d-4114005-o`, `d-4114006-p`, `d-4114006-s`, `d-4114006-o`

Acciones no visitadas: `bcoActividadEvaluacionOtroTipo.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoActividadEvaluacionOtroTipo.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoActividadEvaluacionPersonalCyT.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoActividadEvaluacionPersonalCyT.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoActividadEvaluacionProyecto.do?accion=Borrar&id=N` (accion sobre registros (borrar)); `bcoActividadEvaluacionProyecto.do?accion=Editar&id=N` (accion sobre registros (editar)); `bcoActividadEvaluacionRevista.do?accion=Borrar&id=N&tipoActividadEvaluacionId=3` (accion sobre registros (borrar)); `bcoActividadEvaluacionRevista.do?accion=Editar&id=N&tipoActividadEvaluacionId=3` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=26` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoExtensionLista.do?idGrupo=5&idMenu=1463&idModulo=5`

Lista — SIGEVA
- Tabla `usr_extensionLista_tablaExtensionDivulgacionCyT` (displaytag `d-1264550`): NUEVO · AÑO INICIO · AÑO FIN · TÍTULO · MEDIO DE DIVULGACIÓN
- Tabla `usr_extensionLista_tablaMedio1` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio2` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio3` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio4` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio5` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio6` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio7` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio8` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio9` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaMedio10` (displaytag `d-`): TIPO DE MEDIO · NOMBRE DEL MEDIO
- Tabla `usr_extensionLista_tablaExtensionRuralIndustrial` (displaytag `d-8229384`): NUEVO · AÑO INICIO · AÑO FIN · ACTIVIDAD · FUNCIÓN DESEMPEÑADA · INSTITUCIÓN
- Tabla `usr_extensionLista_tablaExtensionServiciosSociales` (displaytag `d-7738317`): NUEVO · AÑO INICIO · AÑO FIN · ACTIVIDAD · FUNCIÓN DESEMPEÑADA · INSTITUCIÓN
- Tabla `usr_extensionLista_tablaExtensionDivulgacionArtistica` (displaytag `d-7532876`): NUEVO · AÑO INICIO · AÑO FIN · ACTIVIDAD · FUNCIÓN DESEMPEÑADA · INSTITUCIÓN
- Tabla `usr_extensionLista_tablaExtensionOtroTipo` (displaytag `d-7097029`): NUEVO · AÑO INICIO · AÑO FIN · ACTIVIDAD · FUNCIÓN DESEMPEÑADA · INSTITUCIÓN

Formulario `cExtensionListaActionForm` → `bcoExtensionLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoExtensionDivulgacionCyT.do?accion=Borrar&extensionId=N` (accion sobre registros (borrar)); `bcoExtensionDivulgacionCyT.do?accion=Editar&extensionId=N` (accion sobre registros (editar)); `bcoExtensionOtroTipo.do?accion=Borrar&extensionId=N` (accion sobre registros (borrar)); `bcoExtensionOtroTipo.do?accion=Editar&extensionId=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=17` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=34` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=44` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=45` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=46` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoFinanciamientoCyTLista.do?idGrupo=5&idMenu=1459&idModulo=5`

Lista — FINANCIAMIENTOS BANCO DE DATOS
- Tabla `persona.subsidio.proyectosID` (displaytag `d-513259`): NUEVO · TÍTULO · FECHA DESDE · FECHA HASTA · MONTO
- Tabla `persona.subsidio.proyectosID` (displaytag `d-513259`): NUEVO · TÍTULO · FECHA DESDE · FECHA HASTA · MONTO
- Tabla `persona.subsidio.proyectosID` (displaytag `d-513259`): NUEVO · TÍTULO · FECHA DESDE · FECHA HASTA · MONTO
- Tabla `persona.subsidio.proyectosID` (displaytag `d-513259`): NUEVO · TÍTULO · FECHA DESDE · FECHA HASTA · MONTO
- Tabla `persona.subsidio.proyectosID` (displaytag `d-513259`): NUEVO · TÍTULO · FECHA DESDE · FECHA HASTA · MONTO
- Tabla `bco.antecedentes.becas` (displaytag `d-1036751`): NUEVO · AÑO INICIO · AÑO FIN · TIPO DE BECA · INSTITUCIÓN

Formulario `cFinanciamientoCyTListaActionForm` → `bcoFinanciamientoCyTLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoBeca.do?accion=borrar&id=N` (accion sobre registros (borrar)); `bcoBeca.do?accion=editar&id=N` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=1` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=25` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=76` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=77` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=78` (ruta prohibida (sesion, importacion o descarga)); `bcofinanciamientoCYTEventoEquipamiento.do?accion=borrar&grupoFinanciamientoId=3&id=N` (accion sobre registros (borrar)); `bcofinanciamientoCYTEventoEquipamiento.do?accion=borrar&grupoFinanciamientoId=4&id=N` (accion sobre registros (borrar)); `bcofinanciamientoCYTEventoEquipamiento.do?accion=editar&grupoFinanciamientoId=3&id=N` (accion sobre registros (editar)); `bcofinanciamientoCYTEventoEquipamiento.do?accion=editar&grupoFinanciamientoId=4&id=N` (accion sobre registros (editar)); `bcofinanciamientoCYTProyecto.do?accion=borrar&id=N&tipoFinanciamientoId=11` (accion sobre registros (borrar))

### `bcoFormacionRRHH.do?idGrupo=5&idMenu=1460&idModulo=5`

Lista — SIGEVA
- Tabla `persona.formacionRRHH.lista.becas` (displaytag `d-5968303`): NUEVO · AÑO INICIO · AÑO FIN · APELLIDO Y NOMBRE · TIPO DE BECA · INSTITUCIÓN DEL DIRIGIDO · FUNCIÓN
- Tabla `persona.formacionRRHH.lista.tesis` (displaytag `d-5969929`): NUEVO · AÑO INICIO · AÑO FIN · APELLIDO Y NOMBRE · TIPO DE TESIS · INSTITUCIÓN DEL DIRIGIDO · FUNCIÓN
- Tabla `persona.formacionRRHH.lista.investigadores` (displaytag `d-3911430`): NUEVO · AÑO INICIO · AÑO FIN · APELLIDO Y NOMBRE · CARRERA · INSTITUCIÓN DEL DIRIGIDO · FUNCIÓN
- Tabla `persona.formacionRRHH.lista.pasantes` (displaytag `d-1793546`): NUEVO · AÑO INICIO · AÑO FIN · APELLIDO Y NOMBRE · AMBITO INSTITUCIONAL · INSTITUCIÓN · FUNCIÓN
- Tabla `persona.formacionRRHH.lista.personalApoyo` (displaytag `d-626479`): NUEVO · AÑO INICIO · AÑO FIN · APELLIDO Y NOMBRE · CARRERA · INSTITUCIÓN DEL DIRIGIDO · FUNCIÓN

Formulario `(sin nombre)` → `bcoFormacionRRHH.do` (POST); botones: Importar, Salir

Ocultos: `d-5968303-p`, `d-5968303-s`, `d-5968303-o`, `d-5969929-p`, `d-5969929-s`, `d-5969929-o`, `d-3911430-p`, `d-3911430-s`, `d-3911430-o`, `d-1793546-p`, `d-1793546-s`, `d-1793546-o`, `d-626479-p`, `d-626479-s`, `d-626479-o`

Acciones no visitadas: `bcoFormacionBecario.do?accion=borrar&formacionId=N&tipo=2` (accion sobre registros (borrar)); `bcoFormacionBecario.do?accion=editar&formacionId=N&tipo=2` (accion sobre registros (editar)); `bcoFormacionTesis.do?accion=borrar&formacionId=N&tipo=1` (accion sobre registros (borrar)); `bcoFormacionTesis.do?accion=editar&formacionId=N&tipo=1` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=14` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=2` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=3` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=52` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=53` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoOtrasActividadesCYTLista.do?idGrupo=5&idMenu=1464&idModulo=5`

Lista — SIGEVA
- Tabla `usr.actividad.complejidad` (displaytag `d-1747795`): NUEVO · AÑO INICIO · AÑO FIN · FUNCIÓN
- Tabla `usr.actividad.normalizacion` (displaytag `d-4981825`): NUEVO · AÑO INICIO · AÑO FIN · FUNCIÓN
- Tabla `usr.actividad.ambitoNoAcademico` (displaytag `d-967784`): NUEVO · AÑO INICIO · AÑO FIN · AREA · FUNCIÓN
- Tabla `usr.actividad.otra` (displaytag `d-4799537`): NUEVO · AÑO INICIO · AÑO FIN · TIPO ACTIVIDAD · FUNCIÓN

Formulario `cOtrasActividadesCYTListaActionForm` → `bcoOtrasActividadesCYTLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `d-2879534-p`, `d-2879534-s`, `d-2879534-o`, `d-4981825-p`, `d-4981825-s`, `d-4981825-o`, `d-4799537-p`, `d-4799537-s`, `d-4799537-o`, `d-855635-p`, `d-855635-s`, `d-855635-o`, `d-1747795-p`, `d-1747795-s`, `d-1747795-o`, `d-967784-p`, `d-967784-s`, `d-967784-o`

Acciones no visitadas: `bcoActividadOtraActividadCYT.do?accion=borrar&actividadId=N&tipoActividad=6` (accion sobre registros (borrar)); `bcoActividadOtraActividadCYT.do?accion=editar&actividadId=N&tipoActividad=6` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=55` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=57` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=58` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=59` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaBienes.do?idGrupo=5&idMenu=1464&idModulo=5`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `usr.actividad.otra` (displaytag `d-4799537`): NUEVO · AÑO INICIO · AÑO FIN · TIPO ACTIVIDAD · FUNCIÓN

Formulario `cProduccionListaActionForm` → `bcoProduccionListaBienes.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=56` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 6

### `bcoProduccionArtisticaLista.do?grupoArtistica=1&idGrupo=6&idMenu=1468&idModulo=6`

Lista — SIGEVA
- Tabla `usr_artistica_musical_sonora_lista` (displaytag `d-1235083`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN MUSICAL-SONORA · AÑO
- Tabla `usr_artistica_visual_lista` (displaytag `d-1034952`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN VISUAL · AÑO
- Tabla `usr_artistica_audiovisual_multimedial_lista` (displaytag `d-6866496`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN AUDIOVISUAL O MULTIMEDIAL · AÑO
- Tabla `usr_corporal_teatral_lista` (displaytag `d-3516235`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN CORPORAL O TEATRAL · AÑO
- Tabla `usr_artistica_literaria_narrativo_lista` (displaytag `d-4940154`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_dramatico_lista` (displaytag `d-7806602`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_guion_lista` (displaytag `d-4536772`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_otro_lista` (displaytag `d-1680212`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_otra_lista` (displaytag `d-4692768`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN ARTÍSTICA · AÑO

Formulario `(sin nombre)` → `bcoProduccionArtisticaLista.do` (POST); botones: Importar, Salir

Ocultos: `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=70` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=71` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=72` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=73` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=74` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=75` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionArtisticaLista.do?idGrupo=6&idMenu=1468&idModulo=6`

Lista — SIGEVA
- Tabla `usr_artistica_musical_sonora_lista` (displaytag `d-1235083`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN MUSICAL-SONORA · AÑO
- Tabla `usr_artistica_visual_lista` (displaytag `d-1034952`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN VISUAL · AÑO
- Tabla `usr_artistica_audiovisual_multimedial_lista` (displaytag `d-6866496`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN AUDIOVISUAL O MULTIMEDIAL · AÑO
- Tabla `usr_corporal_teatral_lista` (displaytag `d-3516235`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN CORPORAL O TEATRAL · AÑO
- Tabla `usr_artistica_literaria_narrativo_lista` (displaytag `d-4940154`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_dramatico_lista` (displaytag `d-7806602`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_guion_lista` (displaytag `d-4536772`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_literaria_otro_lista` (displaytag `d-1680212`): NUEVO · TÍTULO DE LA PRODUCCIÓN ARTÍSTICA LITERARIA · AÑO · PAÍS
- Tabla `usr_artistica_otra_lista` (displaytag `d-4692768`): NUEVO · TÍTULO DE LA PRODUCCIÓN · TIPO DE PRODUCCIÓN ARTÍSTICA · AÑO

Formulario `(sin nombre)` → `bcoProduccionArtisticaLista.do` (POST); botones: Importar, Salir

Ocultos: `d-1235083-p`, `d-1235083-s`, `d-1235083-o`, `d-1034952-p`, `d-1034952-s`, `d-1034952-o`, `d-6866496-p`, `d-6866496-s`, `d-6866496-o`, `d-3516235-p`, `d-3516235-s`, `d-3516235-o`, `d-4940154-p`, `d-4940154-s`, `d-4940154-o`, `d-7806602-p`, `d-7806602-s`, `d-7806602-o`, `d-4536772-p`, `d-4536772-s`, `d-4536772-o`, `d-1680212-p`, `d-1680212-s`, `d-1680212-o`, `d-4692768-p`, `d-4692768-s`, `d-4692768-o`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=70` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=71` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=72` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=73` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=74` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=75` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaBienes.do?idGrupo=6&idMenu=1482&idModulo=6`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `usr.actividad.otra` (displaytag `d-4799537`): NUEVO · AÑO INICIO · AÑO FIN · TIPO ACTIVIDAD · FUNCIÓN

Formulario `cProduccionListaActionForm` → `bcoProduccionListaBienes.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=56` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaDesarrollo.do?idGrupo=6&idMenu=1467&idModulo=6`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `colDesarrolloProdProsSist` (displaytag `d-4224505`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloSocioCom` (displaytag `d-6164601`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloEmpresarial` (displaytag `d-6304318`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloPublica` (displaytag `d-7646535`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO

Formulario `cProduccionListaActionForm` → `bcoProduccionListaDesarrollo.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=80` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionDesarrollo.do?action=Borrar&produccionId=N&tipo=12` (accion sobre registros (borrar)); `bcoProduccionDesarrollo.do?action=Editar&produccionId=N&tipo=12` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaDesarrollo.do?idGrupo=6&idMenu=1467&idModulo=6&prod=tecnologica`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `colDesarrolloProdProsSist` (displaytag `d-4224505`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloSocioCom` (displaytag `d-6164601`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloEmpresarial` (displaytag `d-6304318`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO
- Tabla `colDesarrolloPublica` (displaytag `d-7646535`): NUEVO · AÑO · TÍTULO · TIPO DESARROLLO

Formulario `cProduccionListaActionForm` → `bcoProduccionListaDesarrollo.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=80` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionDesarrollo.do?action=Borrar&produccionId=N&tipo=12` (accion sobre registros (borrar)); `bcoProduccionDesarrollo.do?action=Editar&produccionId=N&tipo=12` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1466&idModulo=6`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `articulo` (displaytag `d-3997137`): NUEVO · AÑO · TÍTULO · REVISTA · EDITORIAL · PRECARGA
- Tabla `libro` (displaytag `d-148512`): NUEVO · AÑO · TÍTULO · ISBN · EDITORIAL
- Tabla `capituloLibro` (displaytag `d-4551421`): NUEVO · AÑO · TÍTULO · LIBRO · TIPO DE PARTE
- Tabla `congresoPublicado` (displaytag `d-8106305`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `tesis` (displaytag `d-149182`): NUEVO · FECHA DEFENSA / APROBACIÓN · TESIS · TÍTULO · INSTITUCIÓN
- Tabla `otras` (displaytag `d-149149`): NUEVO · AÑO · TÍTULO · ISBN · ISSN
- Tabla `informeTecnico` (displaytag `d-3424995`): NUEVO · FECHA INICIO · FECHA FIN · TÍTULO · DISCIPLINA

Formulario `cProduccionListaActionForm` → `bcoProduccionListaPublicacion.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=13` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=37&tipoProduccionCientifica=7` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=38&tipoProduccionCientifica=8` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=5&tipoProduccionCientifica=1` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=6&tipoProduccionCientifica=2` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=7&tipoProduccionCientifica=3` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=8&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionArticuloPublicacion.do?action=Borrar&produccionId=N&tipo=1` (accion sobre registros (borrar)); `bcoProduccionArticuloPublicacion.do?action=Editar&produccionId=N&tipo=1` (accion sobre registros (editar)); `bcoProduccionInformeTecnico.do?action=Borrar&produccionId=N&tipo=9` (accion sobre registros (borrar)); `bcoProduccionInformeTecnico.do?action=Editar&produccionId=N&tipo=9` (accion sobre registros (editar)); `bcoProduccionLibroPublicacion.do?action=Borrar&produccionId=N&tipo=3` (accion sobre registros (borrar))

### `bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1466&idModulo=6&prod=cientifica`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `articulo` (displaytag `d-3997137`): NUEVO · AÑO · TÍTULO · REVISTA · EDITORIAL · PRECARGA
- Tabla `libro` (displaytag `d-148512`): NUEVO · AÑO · TÍTULO · ISBN · EDITORIAL
- Tabla `capituloLibro` (displaytag `d-4551421`): NUEVO · AÑO · TÍTULO · LIBRO · TIPO DE PARTE
- Tabla `congresoPublicado` (displaytag `d-8106305`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `tesis` (displaytag `d-149182`): NUEVO · FECHA DEFENSA / APROBACIÓN · TESIS · TÍTULO · INSTITUCIÓN
- Tabla `otras` (displaytag `d-149149`): NUEVO · AÑO · TÍTULO · ISBN · ISSN
- Tabla `informeTecnico` (displaytag `d-3424995`): NUEVO · FECHA INICIO · FECHA FIN · TÍTULO · DISCIPLINA

Formulario `cProduccionListaActionForm` → `bcoProduccionListaPublicacion.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=13` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=37&tipoProduccionCientifica=7` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=38&tipoProduccionCientifica=8` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=5&tipoProduccionCientifica=1` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=6&tipoProduccionCientifica=2` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=7&tipoProduccionCientifica=3` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=8&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionArticuloPublicacion.do?action=Borrar&produccionId=N&tipo=1` (accion sobre registros (borrar)); `bcoProduccionArticuloPublicacion.do?action=Editar&produccionId=N&tipo=1` (accion sobre registros (editar)); `bcoProduccionInformeTecnico.do?action=Borrar&produccionId=N&tipo=9` (accion sobre registros (borrar)); `bcoProduccionInformeTecnico.do?action=Editar&produccionId=N&tipo=9` (accion sobre registros (editar)); `bcoProduccionLibroPublicacion.do?action=Borrar&produccionId=N&tipo=3` (accion sobre registros (borrar))

### `bcoProduccionListaPublicacion.do?idGrupo=6&idMenu=1467&idModulo=6&prod=tecnologica`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `articulo` (displaytag `d-3997137`): NUEVO · AÑO · TÍTULO · REVISTA · EDITORIAL · PRECARGA
- Tabla `libro` (displaytag `d-148512`): NUEVO · AÑO · TÍTULO · ISBN · EDITORIAL
- Tabla `capituloLibro` (displaytag `d-4551421`): NUEVO · AÑO · TÍTULO · LIBRO · TIPO DE PARTE
- Tabla `congresoPublicado` (displaytag `d-8106305`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `tesis` (displaytag `d-149182`): NUEVO · FECHA DEFENSA / APROBACIÓN · TESIS · TÍTULO · INSTITUCIÓN
- Tabla `otras` (displaytag `d-149149`): NUEVO · AÑO · TÍTULO · ISBN · ISSN
- Tabla `informeTecnico` (displaytag `d-3424995`): NUEVO · FECHA INICIO · FECHA FIN · TÍTULO · DISCIPLINA

Formulario `cProduccionListaActionForm` → `bcoProduccionListaPublicacion.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=13` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=37&tipoProduccionCientifica=7` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=38&tipoProduccionCientifica=8` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=5&tipoProduccionCientifica=1` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=6&tipoProduccionCientifica=2` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=7&tipoProduccionCientifica=3` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=8&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionArticuloPublicacion.do?action=Borrar&produccionId=N&tipo=1` (accion sobre registros (borrar)); `bcoProduccionArticuloPublicacion.do?action=Editar&produccionId=N&tipo=1` (accion sobre registros (editar)); `bcoProduccionInformeTecnico.do?action=Borrar&produccionId=N&tipo=9` (accion sobre registros (borrar)); `bcoProduccionInformeTecnico.do?action=Editar&produccionId=N&tipo=9` (accion sobre registros (editar)); `bcoProduccionLibroPublicacion.do?action=Borrar&produccionId=N&tipo=3` (accion sobre registros (borrar))

### `bcoProduccionListaServicios.do?idGrupo=6&idMenu=1481&idModulo=6`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `convenio` (displaytag `d-3998901`): NUEVO · TÍTULO O DENOMINACIÓN · FUNCIÓN · FECHA INICIO · FECHA FIN · MOD. DE VINC.

Formulario `cProduccionListaActionForm` → `bcoProduccionListaServicios.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=9` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionConvenio.do?action=Borrar&produccionId=N&tipo=5` (accion sobre registros (borrar)); `bcoProduccionConvenio.do?action=Editar&produccionId=N&tipo=5` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoProduccionListaServicios.do?idGrupo=6&idMenu=1481&idModulo=6&prod=tecnologica`

Lista — PRODUCCIONES Y SERVICIOS BANCO DE DATOS
- Tabla `convenio` (displaytag `d-3998901`): NUEVO · TÍTULO O DENOMINACIÓN · FUNCIÓN · FECHA INICIO · FECHA FIN · MOD. DE VINC.

Formulario `cProduccionListaActionForm` → `bcoProduccionListaServicios.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=9` (ruta prohibida (sesion, importacion o descarga)); `bcoProduccionConvenio.do?action=Borrar&produccionId=N&tipo=5` (accion sobre registros (borrar)); `bcoProduccionConvenio.do?action=Editar&produccionId=N&tipo=5` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoRedesLista.do?idGrupo=6&idMenu=1466&idModulo=6&prod=cientifica`

Lista — REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS
- Tabla `bco.otroAntecedentes.participacionEvento` (displaytag `d-5252578`): NUEVO · AÑO · EVENTO · TIPO DE EVENTO · PAÍS
- Tabla `congresoNoPublicado` (displaytag `d-5511260`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `persona.membresias.lista.redes` (displaytag `d-7751082`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · RED
- Tabla `persona.membresias.lista.membresias` (displaytag `d-4396209`): NUEVO · AÑO INICIO · AÑO FIN · ASOCIACIÓN
- Tabla `persona.membresias.lista.coordinacion` (displaytag `d-4945653`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · PROYECTO
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo6` (displaytag `d-4114007`): NUEVO · AÑO INICIO · AÑO FIN · TÍTULO DE LA REVISTA

Formulario `cRedesListaActionForm` → `bcoRedesLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoActividadCoordinacion.do?accion=borrar&actividadId=N&tipoActividad=9` (accion sobre registros (borrar)); `bcoActividadCoordinacion.do?accion=editar&actividadId=N&tipoActividad=9` (accion sobre registros (editar)); `bcoActividadEvaluacionRevista.do?accion=Borrar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (borrar)); `bcoActividadEvaluacionRevista.do?accion=Editar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (editar)); `bcoActividadMembresias.do?accion=borrar&actividadId=N&tipoActividad=7` (accion sobre registros (borrar)); `bcoActividadMembresias.do?accion=editar&actividadId=N&tipoActividad=7` (accion sobre registros (editar)); `bcoActividadRedes.do?accion=borrar&actividadId=N&tipoActividad=8` (accion sobre registros (borrar)); `bcoActividadRedes.do?accion=editar&actividadId=N&tipoActividad=8` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=26` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=29&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=35` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=66` (ruta prohibida (sesion, importacion o descarga))

## Módulo 7

### `bcoCArchivosAdjuntos.do?idGrupo=7&idMenu=1476&idModulo=7`

Menu — SIGEVA
- Tabla `?` (displaytag `d-`): TIPOS DE ARCHIVOS A ADJUNTAR · ARCHIVO ADJUNTO · FECHA DE ALTA · 

Formulario `(sin nombre)` → `bcoCArchivosAdjuntos.do` (POST); botones: Limpiar

Ocultos: `archivoId`

Formulario `cArchivosAdjuntosActionForm` → `bcoCArchivosAdjuntos.do` (POST); botones: Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `archivoDinamico.do?arch=1615797&archivo=archivosConv` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=4` (ruta prohibida (sesion, importacion o descarga)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoDatoAcademico.do?idGrupo=7&idMenu=1475&idModulo=7`

Menu — Página de Errores

Formulario `cErrorHandlerActionForm` → `errorHandlerAction.do` (POST); botones: Ver Detalles

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `areaError` | textarea/textarea |  |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`, `exception`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoPremioLista.do?idGrupo=7&idMenu=1470&idModulo=7`

Lista — SIGEVA
- Tabla `bco.otrosAntecedentes.premios` (displaytag `d-7570473`): NUEVO · AÑO · PREMIO · TIPO DE PREMIO · INSTITUCIÓN OTORGANTE

Formulario `(sin nombre)` → `bcoPremioLista.do` (POST); botones: Importar, Salir

Ocultos: `d-7570473-p`, `d-7570473-s`, `d-7570473-o`

Acciones no visitadas: `bcoImportarFormulario.do?sincronizarformId=30` (ruta prohibida (sesion, importacion o descarga)); `bcoPremio.do?accion=borrar&id=N` (accion sobre registros (borrar)); `bcoPremio.do?accion=editar&id=N` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

### `bcoRedesLista.do?idGrupo=7&idMenu=1469&idModulo=7`

Lista — REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS
- Tabla `bco.otroAntecedentes.participacionEvento` (displaytag `d-5252578`): NUEVO · AÑO · EVENTO · TIPO DE EVENTO · PAÍS
- Tabla `congresoNoPublicado` (displaytag `d-5511260`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `persona.membresias.lista.redes` (displaytag `d-7751082`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · RED
- Tabla `persona.membresias.lista.membresias` (displaytag `d-4396209`): NUEVO · AÑO INICIO · AÑO FIN · ASOCIACIÓN
- Tabla `persona.membresias.lista.coordinacion` (displaytag `d-4945653`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · PROYECTO
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo6` (displaytag `d-4114007`): NUEVO · AÑO INICIO · AÑO FIN · TÍTULO DE LA REVISTA

Formulario `cRedesListaActionForm` → `bcoRedesLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoActividadCoordinacion.do?accion=borrar&actividadId=N&tipoActividad=9` (accion sobre registros (borrar)); `bcoActividadCoordinacion.do?accion=editar&actividadId=N&tipoActividad=9` (accion sobre registros (editar)); `bcoActividadEvaluacionRevista.do?accion=Borrar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (borrar)); `bcoActividadEvaluacionRevista.do?accion=Editar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (editar)); `bcoActividadMembresias.do?accion=borrar&actividadId=N&tipoActividad=7` (accion sobre registros (borrar)); `bcoActividadMembresias.do?accion=editar&actividadId=N&tipoActividad=7` (accion sobre registros (editar)); `bcoActividadRedes.do?accion=borrar&actividadId=N&tipoActividad=8` (accion sobre registros (borrar)); `bcoActividadRedes.do?accion=editar&actividadId=N&tipoActividad=8` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=26` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=29&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=35` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=66` (ruta prohibida (sesion, importacion o descarga))

### `bcoRedesLista.do?idGrupo=7&idMenu=1471&idModulo=7`

Lista — REDES, GESTIÓN EDITORIAL Y PARTICIPACIÓN EN EVENTOS BANCO DE DATOS
- Tabla `bco.otroAntecedentes.participacionEvento` (displaytag `d-5252578`): NUEVO · AÑO · EVENTO · TIPO DE EVENTO · PAÍS
- Tabla `congresoNoPublicado` (displaytag `d-5511260`): NUEVO · AÑO · TÍTULO · TIPO EVENTO · EVENTO CIENTÍFICO
- Tabla `persona.membresias.lista.redes` (displaytag `d-7751082`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · RED
- Tabla `persona.membresias.lista.membresias` (displaytag `d-4396209`): NUEVO · AÑO INICIO · AÑO FIN · ASOCIACIÓN
- Tabla `persona.membresias.lista.coordinacion` (displaytag `d-4945653`): NUEVO · AÑO INICIO · AÑO FIN · ALCANCE GEOGRÁFICO · PROYECTO
- Tabla `usr.actividadEvaluacionLista.actividadesEvaluacionTipo6` (displaytag `d-4114007`): NUEVO · AÑO INICIO · AÑO FIN · TÍTULO DE LA REVISTA

Formulario `cRedesListaActionForm` → `bcoRedesLista.do` (POST); botones: Importar, Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoActividadCoordinacion.do?accion=borrar&actividadId=N&tipoActividad=9` (accion sobre registros (borrar)); `bcoActividadCoordinacion.do?accion=editar&actividadId=N&tipoActividad=9` (accion sobre registros (editar)); `bcoActividadEvaluacionRevista.do?accion=Borrar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (borrar)); `bcoActividadEvaluacionRevista.do?accion=Editar&id=N&tipoActividadEvaluacionId=6` (accion sobre registros (editar)); `bcoActividadMembresias.do?accion=borrar&actividadId=N&tipoActividad=7` (accion sobre registros (borrar)); `bcoActividadMembresias.do?accion=editar&actividadId=N&tipoActividad=7` (accion sobre registros (editar)); `bcoActividadRedes.do?accion=borrar&actividadId=N&tipoActividad=8` (accion sobre registros (borrar)); `bcoActividadRedes.do?accion=editar&actividadId=N&tipoActividad=8` (accion sobre registros (editar)); `bcoImportarFormulario.do?sincronizarformId=26` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=29&tipoProduccionCientifica=4` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=35` (ruta prohibida (sesion, importacion o descarga)); `bcoImportarFormulario.do?sincronizarformId=66` (ruta prohibida (sesion, importacion o descarga))

## Módulo 8

### `bcoIncorporarParticipanteTramite.do?idGrupo=8&idMenu=0&idModulo=8`

Menu — SIGEVA

Formulario `cIncorporarParticipanteTramiteActionForm` → `bcoIncorporarParticipanteTramite.do` (POST); botones: Aceptar, Salir

| Campo | Tipo | Etiqueta | Oblig. | Notas |
|---|---|---|---|---|
| `codigoTramite` | input/text | Código del trámite |  |  |

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `salir.jsp` (ruta prohibida (sesion, importacion o descarga))

## Módulo 9

### `bcoDatosInvestigacionLista.do?idGrupo=9&idMenu=2535&idModulo=9`

Lista — DATOS DE INVESTIGACIÓN BANCO DE DATOS
- Tabla `bco.otroAntecedentes.participacionEvento` (displaytag `d-5252578`): NUEVO · AÑO · TITULO

Formulario `cDatoInvestigacionListaActionForm` → `bcoDatosInvestigacionLista.do` (POST); botones: Salir

Ocultos: `org.apache.struts.taglib.html.TOKEN`

Acciones no visitadas: `bcoDatoInvestigacion.do?accion=editar&datoInvestigacionId=N` (accion sobre registros (editar)); `salir.jsp` (ruta prohibida (sesion, importacion o descarga))
