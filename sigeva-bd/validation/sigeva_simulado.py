"""SIGEVA simulado para las pruebas: mismas rutas, nombres de campo y trampas que el real.

Reproduce lo que hace fallar a un cargador ingenuo:
- datepicker que, al perder el foco, pisa la fecha con el mes actual si no se uso setDate;
- subcampo del area del conocimiento que llega por AJAX despues de elegir el campo;
- HTML en ISO-8859-1 y paginacion displaytag (d-<id>-p);
- Guardar que vuelve a la lista sin guardar nada (titulos con "SILENCIO");
- error que vacia el archivo y pide adjuntarlo de nuevo (titulos con "REINTENTO").
Registra cada peticion para comprobar que `mapear` nunca envia formularios ni borra.
"""

from __future__ import annotations

import html
import threading
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

VERSION = "14.11.24.6"
TABLAS = {"articulo": ("articulo", "3997137"), "evento": ("congresoPublicado", "8106305"),
          "capitulo": ("capituloLibro", "4551421"), "libro": ("libro", "148512")}
NUEVO = {"articulo": "bcoPrecargarArticulo.do?action=Nuevo",
         "evento": "bcoProduccionListaPublicacionCongreso.do?action=Nuevo&amp;publicado=1",
         "capitulo": "bcoProduccionListaPublicacionCapituloLibro.do?action=Nuevo",
         "libro": "bcoProduccionLibroPublicacion.do?action=Nuevo"}
EDITOR = {"articulo": "/eva/bcoProduccionArticuloPublicacion.do", "evento": "/eva/bcoProduccionListaPublicacionCongreso.do",
          "capitulo": "/eva/bcoProduccionListaPublicacionCapituloLibro.do", "libro": "/eva/bcoProduccionLibroPublicacion.do"}
TIPO_POR_RUTA = {v: k for k, v in EDITOR.items()}

JQUERY_FALSO = """<script>
(function () {
  function mesAnio(d) { return String(d.getMonth() + 1).padStart(2, '0') + '/' + d.getFullYear(); }
  function J(sel) {
    var els = typeof sel === 'string' ? Array.prototype.slice.call(document.querySelectorAll(sel)) : [sel];
    return {
      each: function (fn) { els.forEach(function (e) { fn.call(e); }); return this; },
      hasClass: function (c) { return !!els[0] && els[0].classList.contains(c); },
      datepicker: function (cmd, d) {
        els.forEach(function (e) {
          if (cmd === 'setDate') {
            e.dataset.sel = e.classList.contains('calendar-year') ? String(d.getFullYear()) : mesAnio(d);
            e.value = e.dataset.sel;
          }
        });
        return this;
      }
    };
  }
  window.jQuery = window.$ = J;
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.hasDatepicker').forEach(function (e) {
      // Como jQuery UI: al cerrarse escribe la fecha SELECCIONADA (hoy, si nadie llamo setDate).
      e.addEventListener('blur', function () {
        var hoy = new Date();
        e.value = e.dataset.sel || (e.classList.contains('calendar-year') ? String(hoy.getFullYear()) : mesAnio(hoy));
      });
    });
    var c0 = document.querySelector('select[name=campo_0]');
    if (c0) c0.addEventListener('change', function () {
      setTimeout(function () {
        document.querySelector('select[name=campo_0_0]').innerHTML =
          '<option value="-1">Seleccionar</option><option value="605">2.2.5 Telecomunicaciones</option>';
      }, 300);
    });
  });
  window.agregarPersona = function (p) {
    var cuerpo = document.querySelector('#' + p + 'Table > tbody');
    var tr = document.createElement('tr');
    tr.innerHTML = '<td><table><thead><tr><th>' + p + ':* <input name="' + p + 'ParticipacionLabel">'
      + '<input type="hidden" name="' + p + 'PersonaId" value=""></th></tr></thead><tbody></tbody></table></td>';
    cuerpo.appendChild(tr);
  };
  // Fine Uploader: sube el archivo apenas se elige y deja el nombre en un hidden.
  window.subirArchivo = function (input) {
    var nombre = input.files[0].name;
    fetch('/eva/subirFullText', {method: 'POST', body: nombre}).then(function () {
      document.querySelector('input[name=linkFullText]').value = nombre;
      var li = document.createElement('li');
      li.className = 'qq-upload-success';
      li.textContent = nombre;
      document.getElementById('divFullText').appendChild(li);
    });
  };
})();
</script>"""


def _fila(etiqueta: str, control: str) -> str:
    return f"<tr><td>{etiqueta}</td><td>{control}</td></tr>"


def _pagina(cuerpo: str, titulo: str = "SIGEVA") -> bytes:
    doc = (f"<html><head><meta charset='ISO-8859-1'><title>{titulo}</title>{JQUERY_FALSO}</head>"
           f"<body><div class='titulo'>{titulo}</div>{cuerpo}<div class='version'>{VERSION}</div></body></html>")
    return doc.encode("iso-8859-1", "xmlcharrefreplace")


def _select(nombre: str, opciones: list[tuple[str, str]], elegido: str = "") -> str:
    ops = "".join(f"<option value='{v}'{' selected' if v == elegido else ''}{' disabled' if v.startswith('-') and v != '-1' else ''}>"
                  f"{html.escape(t)}</option>" for v, t in opciones)
    return f"<select name='{nombre}'>{ops}</select>"


def _tabla_personas(p: str) -> str:
    return (f"<table id='{p}Table'><tbody><tr><td><table><thead><tr><th>{p}:* "
            f"<input name='{p}ParticipacionLabel'><input type='hidden' name='{p}PersonaId' value=''>"
            f"</th></tr></thead><tbody></tbody></table></td></tr></tbody></table>"
            f"<input type='button' name='{p}Nuevo' value='Nuevo' onclick=\"agregarPersona('{p}')\">")


def _comunes(valores: dict | None = None, archivo: str = "theFile", compiladores: bool = False) -> str:
    v = valores or {}
    if archivo == "qqfile":
        adjunto = ("<div id='divFullText'><input type='file' name='qqfile' onchange='subirArchivo(this)'></div>"
                   "<input type='hidden' name='linkFullText' value=''>")
    else:
        adjunto = "<input type='file' name='theFile'>"
    return "".join([
        _fila("Título:*", f"<input name='produccion' value='{html.escape(v.get('produccion', ''))}'>"),
        _fila("Idioma:*", _select("idioma", [("-1", "Seleccionar"), ("1", "Español"), ("2", "Inglés")])),
        _fila("Autores:*", _tabla_personas("autor")),
        _fila("Compiladores:", _tabla_personas("compilador")) if compiladores else "",
        _fila("Resumen:*", "<textarea name='hdnresumen'></textarea>"),
        _fila("Área:*", _select("campo_0", [("-1", "Seleccionar"), ("-3", "2 INGENIERÍAS Y TECNOLOGÍAS"),
                                           ("60", "2.2 Ingeniería Eléctrica, Electrónica e Información")])),
        _fila("Subárea:*", "<select name='campo_0_0'><option value='-1'>Seleccionar</option></select>"),
        _fila("Palabras clave:", "".join("<input name='palabraLabel'>" for _ in range(4))),
        _fila("Editorial:*", "<input name='editorial'>"),
        _fila("Soporte:*", "<input type='checkbox' name='tipoSoporteChecked' value='1'>Impreso "
                           "<input type='checkbox' name='tipoSoporteChecked' value='2'>Electrónico"),
        _fila("URL:", "<input name='web'>"),
        _fila("Full text:*", adjunto),
    ])


def _datos_libro() -> str:
    return "".join([
        _fila("ISBN:", "<input name='isbn'>"),
        _fila("Cantidad de páginas:", "<input name='totalPaginasLibro'>"),
        _fila("Estado:*", "<input type='radio' name='publicado' value='1'>Publicado <input type='radio' name='publicado' value='2'>En prensa"),
        _fila("Referato:*", "<input type='radio' name='referato' value='0'>No <input type='radio' name='referato' value='2'>Si"),
        _fila("País de edición:", _select("pais", [("-1", "Seleccionar"), ("10", "Argentina"), ("21", "Estados Unidos")])),
        _fila("Ciudad de la editorial:", "<input name='lugarEdicion'>"),
        _fila("Año de publicación:*", "<input name='anioPublica' class='calendar-year hasDatepicker'>"),
        _fila("Rol:*", "<input type='checkbox' name='isAutor' value='on'>Autor <input type='checkbox' name='isEditor' value='on'>Editor "
                       "<input type='checkbox' name='isRevisor' value='on'>Revisor"),
    ])


def form_capitulo() -> bytes:
    campos = "".join([
        _fila("Tipo de parte de libro:*", _select("tipoParteLibro", [("-1", "Seleccionar"), ("1", "Capítulo de libro"),
                                                                     ("5", "Introducción")])),
        _fila("Título del libro:*", "<input name='tituloLibro'>"),
        _fila("Página inicial:", "<input name='paginaInicial'>"), _fila("Página final:", "<input name='paginaFinal'>"),
        _datos_libro(), _comunes(compiladores=True),
    ])
    return _pagina("<form name='cProduccionCapituloLibroActionForm' method='post' enctype='multipart/form-data' "
                   f"action='/eva/bcoProduccionListaPublicacionCapituloLibro.do'><table>{campos}</table>"
                   "<input type='submit' name='btnSubmit' value='Guardar'><input type='submit' name='btnSubmit' value='Volver'></form>",
                   "Parte de libro")


def form_libro() -> bytes:
    campos = _datos_libro() + _comunes(archivo="qqfile")
    return _pagina("<form name='cProduccionLibroActionForm' method='post' enctype='multipart/form-data' "
                   f"action='/eva/bcoProduccionLibroPublicacion.do'><table>{campos}</table>"
                   "<input type='submit' name='btnSubmit' value='Guardar'><input type='submit' name='btnSubmit' value='Volver'></form>",
                   "Libro")


def form_editar_capitulo(r: dict) -> bytes:
    """Edicion de una parte de libro guardada: valores cargados, boton Modificar (no Guardar)."""
    publicado = r.get("publicado", "1")
    radios = "".join(f"<input type='radio' name='publicado' value='{v}'{' checked' if v == publicado else ''}>{t} "
                     for v, t in (("1", "Publicado"), ("2", "En prensa")))
    autores = "".join(f"<tr><td><table><thead><tr><th><input name='autorParticipacionLabel' value='{html.escape(a)}'>"
                      f"<input type='hidden' name='autorPersonaId' value='{html.escape(p)}'></th></tr></thead><tbody></tbody></table></td></tr>"
                      for a, p in zip(r["autores"], r.get("personas") or [""] * len(r["autores"]), strict=False))
    campos = "".join([
        _fila("Título de la parte:*", f"<input name='produccion' value='{html.escape(r['titulo'])}'>"),
        _fila("Estado:*", radios),
        _fila("Año de publicación:*", f"<input name='anioPublica' class='calendar-year hasDatepicker' value='{r['anio']}'>"),
        _fila("Autores:*", f"<table id='autorTable'><tbody>{autores}</tbody></table>"),
    ])
    return _pagina(f"<form method='post' action='{EDITOR['capitulo']}'><input type='hidden' name='produccionId' value='{r['id']}'>"
                   f"<table>{campos}</table><input type='submit' name='btnSubmit' value='Modificar'>"
                   "<input type='submit' name='btnSubmit' value='Volver'></form>", "Parte de libro")


def form_articulo(error: str = "") -> bytes:
    campos = "".join([
        _fila("ISSN:", "<input name='bissn'><input type='submit' name='btnSubmit' value='Buscar por ISSN / e-ISSN'>"),
        _fila("Revista:", "<input name='brevista'><input type='submit' name='btnSubmit' value='Buscar por Nombre'>"),
        _fila("Revista seleccionada:*", "<textarea name='srevista'></textarea><input type='hidden' name='publicacionId' value=''>"),
        _fila("País:*", _select("pais", [("-1", "Seleccionar"), ("10", "Argentina"), ("21", "Estados Unidos")])),
        _fila("Ciudad:", "<input name='lugarEdicion'>"),
        _fila("Volumen:", "<input name='volumen'>"), _fila("Tomo:", "<input name='tomo'>"),
        _fila("Número:", "<input name='numero'>"),
        _fila("Página inicial:", "<input name='paginaInicial'>"), _fila("Página final:", "<input name='paginaFinal'>"),
        _fila("Fecha de publicación:*", "<input name='fechaPublica' class='calendar-year-month hasDatepicker'>"
                                        "<input type='hidden' name='fechaPublica' value=''>"),
        _fila("DOI:", "<input name='doi'>"),
        _fila("Referato:*", "<input type='radio' name='tipoReferato' value='2'>Con <input type='radio' name='tipoReferato' value='1'>Sin"),
        _fila("Estado:*", "<input type='radio' name='publicado' value='1'>Publicado <input type='radio' name='publicado' value='0'>En prensa"),
        _comunes(),
        _fila("Versión del archivo:*", _select("tipoAdjunto", [("-1", "Seleccionar"), ("1", "Post print"), ("2", "Versión final")])),
    ])
    aviso = f"<div class='error'>{html.escape(error)}</div>" if error else ""
    return _pagina(f"{aviso}<form name='cProduccionArticuloActionForm' method='post' enctype='multipart/form-data' "
                   f"action='/eva/bcoProduccionArticuloPublicacion.do'>"
                   f"<input type='hidden' name='org.apache.struts.taglib.html.TOKEN' value='t'><table>{campos}</table>"
                   f"<input type='submit' name='btnSubmit' value='Guardar'><input type='submit' name='btnSubmit' value='Volver'></form>",
                   "Artículo")


def form_evento() -> bytes:
    campos = "".join([
        _fila("Tipo de trabajo:*", _select("tipoTrabajo", [("-1", "Seleccionar"), ("1", "Artículo Completo"), ("2", "Resumen")])),
        _fila("Tipo de publicación:*", _select("tipoPublicacion", [("-1", "Seleccionar"), ("5", "Libro"), ("6", "Revista")])),
        _fila("Título de la publicación:*", "<input name='tituloPublicacion'>"),
        _fila("ISSN/ISBN:", "<input name='issnIsbn'>"),
        _fila("País de edición:*", _select("paisEdicion", [("-1", "Seleccionar"), ("10", "Argentina"), ("21", "Estados Unidos")])),
        _fila("Ciudad de edición:", "<input name='lugarPublicacion'>"),
        _fila("Año de publicación:*", "<input name='anioPublica' class='calendar-year hasDatepicker'>"),
        _fila("Evento:*", "<input name='reunionCientifica'>"),
        _fila("Tipo de evento:*", _select("tipoReunion", [("-1", "Seleccionar"), ("1", "Conferencia"), ("3", "Simposio"), ("4", "Workshop")])),
        _fila("Alcance:*", "<input type='checkbox' name='alcanceNacional' value='true'>Nacional "
                           "<input type='checkbox' name='alcanceInternacional' value='true'>Internacional"),
        _fila("País del evento:*", _select("paisEvento", [("-1", "Seleccionar"), ("10", "Argentina"), ("21", "Estados Unidos")])),
        _fila("Ciudad del evento:*", "<input name='lugarReunion'>"),
        _fila("Fecha del evento:*", "<input name='fechaReunion' class='calendar-year-month hasDatepicker'>"),
        _fila("Institución organizadora:", "<input name='institucionOrganizadora'>"),
        _comunes(),
    ])
    return _pagina("<form name='cProduccionCongresoActionForm' method='post' enctype='multipart/form-data' "
                   f"action='/eva/bcoProduccionListaPublicacionCongreso.do'><table>{campos}</table>"
                   "<input type='submit' name='btnSubmit' value='Guardar'><input type='submit' name='btnSubmit' value='Volver'></form>",
                   "Trabajo en evento")


def form_premio(valores: dict | None = None) -> bytes:
    v = valores or {}
    campos = "".join([
        _fila("Premio:*", f"<input name='premio' value='{html.escape(v.get('premio', ''))}'>"),
        _fila("Tipo de premio:*", _select("tipoPremio", [("-1", "Seleccionar"), ("1", "Nacional"), ("2", "Internacional")], v.get("tipoPremio", ""))),
        _fila("Año:*", f"<input name='anio' class='calendar-year hasDatepicker' value='{html.escape(v.get('anio', ''))}'>"),
        _fila("Institución otorgante:*", f"<input name='institucionOtorgante' value='{html.escape(v.get('institucionOtorgante', ''))}'>"),
    ])
    return _pagina(f"<form name='cPremioActionForm' method='post' action='/eva/bcoPremio.do'><table>{campos}</table>"
                   "<input type='submit' name='btnSubmit' value='Guardar'><input type='submit' name='btnSubmit' value='Volver'></form>",
                   "Premio")


class Estado:
    def __init__(self) -> None:
        self.registros: dict[str, list[dict]] = {"articulo": [], "evento": [], "capitulo": [], "libro": [], "premio": []}
        self.subidas: list[str] = []  # archivos recibidos por el uploader AJAX de libros
        self.peticiones: list[tuple[str, str]] = []
        self.reintentos_hechos: set[str] = set()
        # SIGEVA conserva lo cargado al re-renderizar con error, salvo el archivo.
        # El simulador lo guarda aparte y lo repone en el siguiente Guardar.
        self.borrador: dict[str, list] = {}
        self.quitar_campo: str | None = None  # para simular un cambio del sitio
        # Que hace "Modificar": "version-nueva" (id nuevo, retira el viejo), "duplicar" (deja los dos)
        # o "en-el-lugar" (mismo id). Los tres se vieron en SIGEVA segun pantalla y version.
        self.modo_modificar = "version-nueva"
        self.lock = threading.Lock()
        self.proximo_id = 100  # como SIGEVA: un id borrado nunca se reutiliza

    def alta(self, tipo: str, datos: dict) -> int:
        with self.lock:
            nuevo = {"id": self.proximo_id, **datos}
            self.proximo_id += 1
            self.registros[tipo].append(nuevo)
            return nuevo["id"]


def _lista_publicaciones(estado: Estado, query: dict, query_cruda: str = "") -> bytes:
    # Como SIGEVA: los enlaces de orden de TODAS las tablas copian la query recibida, con los
    # d-<id>-p de las otras tablas. Solo el d-<id>-s= identifica a cada tabla.
    previa = (html.escape(query_cruda) + "&amp;") if query_cruda else ""
    partes = []
    for tipo, (html_id, orden) in TABLAS.items():
        pagina = int(query.get(f"d-{orden}-p", ["1"])[0])
        registros = estado.registros[tipo]
        tramo = registros[(pagina - 1) * 10: pagina * 10]
        nuevo, editor = NUEVO[tipo], EDITOR[tipo].removeprefix("/eva/")
        filas = "".join(
            f"<tr><td><a href='{editor}?action=Editar&produccionId={r['id']}&tipo=1'>EDITAR</a> "
            f"<a href='{editor}?action=Borrar&produccionId={r['id']}&tipo=1'>BORRAR</a></td>"
            f"<td>{r['anio']}</td><td>{html.escape(r['titulo'] if len(r['titulo']) <= 50 else r['titulo'][:50] + '...')}</td>"
            f"<td>x</td><td>y</td></tr>" for r in tramo) or "<tr><td colspan='5'>No hay registros cargados.</td></tr>"
        partes.append(f"<input type='button' value='Importar' onclick=\"location.href='bcoImportarFormulario.do?sincronizarformId=5'\">"
                      f"<table id='{html_id}'><thead><tr><th><a href='{nuevo}'>NUEVO</a></th>"
                      f"<th><a href='bcoProduccionListaPublicacion.do?{previa}d-{orden}-o=2&amp;d-{orden}-s=1'>AÑO</a></th><th>TÍTULO</th><th>REVISTA</th>"
                      f"<th>EDITORIAL</th></tr></thead><tbody>{filas}</tbody></table>")
    return _pagina("<form name='cProduccionListaActionForm' method='post' action='/eva/bcoProduccionListaPublicacion.do?paginar=true'>"
                   + "".join(partes) + "<input type='submit' value='Salir'></form>", "Publicaciones")


def _lista_premios(estado: Estado) -> bytes:
    filas = "".join(f"<tr><td><a href='bcoPremio.do?accion=editar&id={r['id']}'>EDITAR</a> "
                    f"<a href='bcoPremio.do?accion=borrar&id={r['id']}'>BORRAR</a></td><td>{r['anio']}</td>"
                    f"<td>{html.escape(r['premio'])}</td><td>{r['tipoPremio']}</td><td>{html.escape(r['institucionOtorgante'])}</td></tr>"
                    for r in estado.registros["premio"]) or "<tr><td colspan='5'>No hay registros cargados.</td></tr>"
    return _pagina("<form method='post' action='bcoPremioLista.do'><table id='bco.otrosAntecedentes.premios'><thead><tr>"
                   "<th><a href='bcoPremio.do?accion=nuevo'>NUEVO</a></th><th><a href='bcoPremioLista.do?d-7570473-s=1'>AÑO</a></th>"
                   f"<th>PREMIO</th><th>TIPO DE PREMIO</th><th>INSTITUCIÓN OTORGANTE</th></tr></thead><tbody>{filas}</tbody></table>"
                   "<input type='submit' value='Salir'></form>", "Premios")


def crear_manejador(estado: Estado):
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silencio en las pruebas
            pass

        def _responder(self, cuerpo: bytes, codigo: int = 200) -> None:
            if estado.quitar_campo:
                cuerpo = cuerpo.replace(f"name='{estado.quitar_campo}'".encode(), b"name='renombrado'")
            self.send_response(codigo)
            self.send_header("Content-Type", "text/html; charset=ISO-8859-1")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def _redirigir(self, destino: str) -> None:
            self.send_response(302)
            self.send_header("Location", destino)
            self.end_headers()

        def do_GET(self):
            partes = urlsplit(self.path)
            q = parse_qs(partes.query)
            estado.peticiones.append(("GET", self.path))
            ruta = partes.path
            if ruta == "/intranet/index.htm":
                return self._responder(_pagina(
                    "<script>function redirect(id){ if (id === 96) location.href = '/eva/indexBancoDatos.do'; }</script>"
                    "<div style='display:none'><a href='#' onclick='redirect(96)'>Usuario banco de datos de actividades de CyT</a>"
                    "<a href='#' onclick='redirect(72)'>Usuario presentación/solicitud</a></div>", "Intranet"))
            if ruta == "/eva/indexBancoDatos.do":
                return self._responder(_pagina(
                    "<a href='bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica'>Artículos</a> "
                    "<a href='bcoPremioLista.do?idModulo=7&idGrupo=7&idMenu=1470'>Premios</a> <a href='salir.jsp'>Salir</a> "
                    "<a href='indexBancoDatos.do?idModulo=1&idGrupo=0&idMenu=0'>PRINCIPAL</a>", "Principal"))
            if ruta == "/eva/bcoProduccionListaPublicacion.do":
                return self._responder(_lista_publicaciones(estado, q, partes.query))
            if ruta == "/eva/bcoPremioLista.do":
                return self._responder(_lista_premios(estado))
            if ruta == "/eva/bcoPrecargarArticulo.do":
                return self._responder(_pagina(
                    "<form method='post' action='/eva/bcoPrecargarArticulo.do'>DOI: <input name='identificador'>"
                    "<input type='submit' name='btnSubmit' value='Precargar'><input type='submit' name='btnSubmit' value='Omitir'></form>",
                    "Precarga"))
            if ruta == "/eva/bcoProduccionListaPublicacionCongreso.do" and q.get("action") == ["Nuevo"]:
                return self._responder(form_evento())
            if ruta == EDITOR["capitulo"] and q.get("action") == ["Nuevo"]:
                return self._responder(form_capitulo())
            if ruta == EDITOR["libro"] and q.get("action") == ["Nuevo"]:
                return self._responder(form_libro())
            if ruta in TIPO_POR_RUTA and q.get("action") == ["Borrar"]:
                # Solo muestra la confirmacion: un GET nunca borra.
                return self._responder(_pagina(f"<form method='post' action='{ruta}'><input type='hidden' name='produccionId' "
                                               f"value='{q['produccionId'][0]}'>¿Eliminar?<input type='submit' name='btnSubmit' "
                                               "value='Eliminar'><input type='submit' name='btnSubmit' value='Volver'></form>"))
            if ruta in TIPO_POR_RUTA and q.get("action") == ["Editar"]:
                tipo = TIPO_POR_RUTA[ruta]
                r = next(x for x in estado.registros[tipo] if str(x["id"]) == q["produccionId"][0])
                if tipo == "capitulo" and r.get("editable"):
                    return self._responder(form_editar_capitulo(r))
                campos = "".join(f"<input name='{n}' value='{html.escape(v)}'>" for n, valores in r["fechas"].items() for v in valores)
                return self._responder(_pagina(f"<form>{campos}<input name='produccion' value='{html.escape(r['titulo'])}'></form>"))
            if ruta == "/eva/bcoPremio.do":
                if q.get("accion") == ["nuevo"]:
                    return self._responder(form_premio())
                if q.get("accion") == ["editar"]:
                    r = next(x for x in estado.registros["premio"] if str(x["id"]) == q["id"][0])
                    return self._responder(form_premio(r))
            return self._responder(_pagina("No encontrado"), 404)

        def _formulario(self) -> dict[str, list]:
            largo = int(self.headers.get("Content-Length", 0))
            cuerpo = self.rfile.read(largo)
            tipo = self.headers.get("Content-Type", "")
            if tipo.startswith("multipart/form-data"):
                msg = BytesParser(policy=HTTP).parsebytes(f"Content-Type: {tipo}\r\n\r\n".encode() + cuerpo)
                datos: dict[str, list] = {}
                for parte in msg.iter_parts():
                    nombre = parte.get_param("name", header="content-disposition")
                    archivo = parte.get_filename()
                    carga = parte.get_payload(decode=True) or b""
                    datos.setdefault(nombre, []).append({"archivo": archivo, "bytes": len(carga)} if archivo is not None
                                                        else carga.decode("iso-8859-1"))
                return datos
            return {k: v for k, v in parse_qs(cuerpo.decode("iso-8859-1"), keep_blank_values=True).items()}

        def do_POST(self):
            estado.peticiones.append(("POST", self.path))
            ruta = urlsplit(self.path).path
            if ruta == "/eva/subirFullText":
                largo = int(self.headers.get("Content-Length", 0))
                estado.subidas.append(self.rfile.read(largo).decode("utf-8", "replace"))
                return self._responder(b'{"success": true}')
            f = self._formulario()
            boton = (f.get("btnSubmit") or [""])[0]
            if ruta == "/eva/bcoPrecargarArticulo.do" and boton == "Omitir":
                return self._responder(form_articulo())
            if boton == "Volver":
                return self._redirigir("/eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica")
            if ruta in ("/eva/bcoProduccionArticuloPublicacion.do", "/eva/bcoProduccionListaPublicacionCongreso.do") and boton == "Guardar":
                tipo = "articulo" if "Articulo" in ruta else "evento"
                if estado.borrador:
                    f = {k: (f[k] if any(x for x in f.get(k, []) if x) else v) for k, v in estado.borrador.items()} | \
                        {k: v for k, v in f.items() if k not in estado.borrador}
                    estado.borrador = {}
                titulo = f["produccion"][0]
                archivo = (f.get("theFile") or [{}])[0]
                if "REINTENTO" in titulo and titulo not in estado.reintentos_hechos:
                    estado.reintentos_hechos.add(titulo)
                    estado.borrador = {k: v for k, v in f.items() if k != "theFile"}
                    return self._responder(form_articulo("Debe especificar el tipo de version. Seleccione nuevamente el archivo."))
                if not isinstance(archivo, dict) or not archivo.get("archivo"):
                    return self._responder(form_articulo("Debe adjuntar el archivo con el full text"))
                if "SILENCIO" not in titulo:
                    nombres = ("fechaPublica",) if tipo == "articulo" else ("fechaReunion", "anioPublica")
                    fechas = {n: f.get(n, []) for n in nombres}
                    anio = (fechas.get("fechaPublica") or fechas.get("fechaReunion"))[0].split("/")[-1]
                    estado.alta(tipo, {"titulo": titulo, "anio": anio, "fechas": fechas,
                                       "autores": f.get("autorParticipacionLabel", []), "orgs": f.get("autorOrganizacionId", []),
                                       "personas": f.get("autorPersonaId", []), "otras": f.get("autorisOtraOrganizacion", []),
                                       "area": f.get("campo_0_0", []), "idioma": f.get("idioma", []),
                                       "palabras": [p for p in f.get("palabraLabel", []) if p]})
                return self._redirigir("/eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica")
            if ruta in TIPO_POR_RUTA and boton == "Eliminar":
                tipo = TIPO_POR_RUTA[ruta]
                estado.registros[tipo] = [x for x in estado.registros[tipo] if str(x["id"]) != f["produccionId"][0]]
                return self._redirigir("/eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica")
            if ruta == EDITOR["capitulo"] and boton == "Modificar":
                viejo = next(x for x in estado.registros["capitulo"] if str(x["id"]) == f["produccionId"][0])
                nuevo = {**viejo, "titulo": f["produccion"][0], "anio": f["anioPublica"][0], "fechas": {"anioPublica": f["anioPublica"]},
                         "publicado": f["publicado"][0], "autores": f["autorParticipacionLabel"], "personas": f["autorPersonaId"]}
                if estado.modo_modificar == "en-el-lugar":
                    viejo.update(nuevo)
                else:
                    if estado.modo_modificar == "version-nueva":
                        estado.registros["capitulo"].remove(viejo)
                    nuevo.pop("id")
                    estado.alta("capitulo", nuevo)
                return self._redirigir("/eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica")
            if ruta in (EDITOR["capitulo"], EDITOR["libro"]) and boton == "Guardar":
                tipo = TIPO_POR_RUTA[ruta]
                archivo = (f.get("theFile") or [{}])[0] if tipo == "capitulo" else (f.get("linkFullText") or [""])[0]
                if not (archivo.get("archivo") if isinstance(archivo, dict) else archivo):
                    return self._responder(form_capitulo() if tipo == "capitulo" else form_libro())
                fechas = {"anioPublica": f.get("anioPublica", [])}
                estado.alta(tipo, {"titulo": f["produccion"][0], "anio": fechas["anioPublica"][0], "fechas": fechas,
                                   "autores": f.get("autorParticipacionLabel", []), "orgs": f.get("autorOrganizacionId", []),
                                   "personas": f.get("autorPersonaId", []),
                                   "compiladores": f.get("compiladorParticipacionLabel", []),
                                   "orgs_compiladores": f.get("compiladorOrganizacionId", []),
                                   "personas_compiladores": f.get("compiladorPersonaId", []),
                                   "roles": [r for r in ("isAutor", "isEditor", "isRevisor") if f.get(r)],
                                   "referato": f.get("referato", []), "tipoParte": f.get("tipoParteLibro", []),
                                   "isbn": f.get("isbn", [])})
                return self._redirigir("/eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica")
            if ruta == "/eva/bcoPremio.do" and boton == "Guardar":
                estado.alta("premio", {k: f[k][0] for k in ("premio", "tipoPremio", "anio", "institucionOtorgante")})
                return self._redirigir("/eva/bcoPremioLista.do?idModulo=7&idGrupo=7&idMenu=1470")
            return self._responder(_pagina("Accion desconocida"), 400)

    return Manejador


class Servidor:
    def __init__(self) -> None:
        self.estado = Estado()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), crear_manejador(self.estado))
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> "Servidor":
        self.hilo.start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
