"""Pruebas sin red ni credenciales.

- Unitarias: BibTeX, validacion, comparacion con la lista, catalogo, mapa y deteccion de cambios.
- De punta a punta contra un SIGEVA simulado (validation/sigeva_simulado.py) con Chromium headless.
  Se saltean si Playwright o Chromium no estan instalados.

Ejecutar:  python sigeva-bd/validation/test_sigeva_bd.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "assets"))
sys.path.insert(0, str(AQUI))

import sigeva_bd as B  # noqa: E402
import sigeva_mapa as M  # noqa: E402
import sigeva_cv as CV  # noqa: E402
import sigeva_pip as PIP  # noqa: E402

BIB = r"""
@article{perez2024,
  author = {P{\'e}rez, Ana and Smith, John and others},
  title = {Redes {\'o}pticas: un {$\mu$}-estudio},
  journal = {Revista de Pruebas},
  year = 2024, month = sep, volume = {12}, pages = {10--20},
  doi = {10.1000/xyz}, langid = {spanish}, abstract = {Resumen},
}
@inproceedings{gomez2023,
  author = "G{\'o}mez, Luis", title = "Workshop paper", booktitle = "Proc. of WS 2023", year = "2023",
  note = {To appear},
}
@book{libro2020, title = {Un libro}, year = 2020}
@article{sinmes, title = {Sin mes}, author = {Ruiz, Eva}, journal = {J}, year = {2022}}
"""


def articulo(**extra) -> dict:
    reg = {"clave": "a1", "tipo": "articulo", "titulo": "Un titulo de prueba suficientemente largo para la lista",
           "autores": [{"apellido": "Perez", "nombre": "Ana", "declarante": True, "institucion_id": "8434", "institucion": "UPC"}],
           "idioma": "Inglés", "resumen": "Resumen", "editorial": "IEEE", "pais_edicion": "Estados Unidos",
           "publicacion_id": "77", "revista": "Revista", "fecha_publicacion": "09/2024", "doi": "10.1/x",
           "palabras_clave": ["redes"]}
    reg.update(extra)
    return reg


CONFIG = {"persona_id": "555", "area_conocimiento": {"campo": "60", "subcampo": "605"}}


class TestBibtex(unittest.TestCase):
    def setUp(self):
        self.registros, self.descartes = B.bib_a_registros(B.parsear_bibtex(BIB))
        self.por_clave = {r["clave"]: r for r in self.registros}

    def test_articulo_limpia_latex_y_arma_fecha(self):
        r = self.por_clave["perez2024"]
        self.assertEqual(r["titulo"], "Redes ópticas: un mu-estudio")
        self.assertEqual(r["fecha_publicacion"], "09/2024")
        self.assertEqual(r["idioma"], "Español")
        self.assertEqual([a["apellido"] for a in r["autores"]], ["Pérez", "Smith"])
        self.assertEqual(r["paginas"], "10-20")

    def test_sin_mes_no_se_estima(self):
        self.assertNotIn("fecha_publicacion", self.por_clave["sinmes"])

    def test_to_appear_queda_en_prensa_y_tipos_sin_conversor_se_informan(self):
        self.assertTrue(self.por_clave["gomez2023"]["en_prensa"])
        self.assertEqual(self.por_clave["gomez2023"]["tipo"], "evento")
        self.assertEqual([d["clave"] for d in self.descartes], ["libro2020"])


class TestValidacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pdf = Path(self.tmp.name) / "a.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 prueba")

    def tearDown(self):
        self.tmp.cleanup()

    def errores(self, reg):
        return B.validar_registro(reg, B.cargar_config(None) | CONFIG)[0]

    def test_registro_completo_pasa(self):
        self.assertEqual(self.errores(articulo(archivo=str(self.pdf))), [])

    def test_sin_full_text_bloquea(self):
        self.assertTrue(any("archivo" in e for e in self.errores(articulo())))

    def test_electronico_sin_url_ni_doi_bloquea(self):
        errores = self.errores(articulo(archivo=str(self.pdf), doi=None, soporte=["electronico"]))
        self.assertTrue(any("URL ni DOI" in e for e in errores))

    def test_coautor_sin_institucion_bloquea_en_articulos(self):
        reg = articulo(archivo=str(self.pdf))
        reg["autores"].append({"apellido": "Smith", "nombre": "J"})
        self.assertTrue(any("Smith" in e for e in self.errores(reg)))

    def test_exactamente_un_declarante(self):
        reg = articulo(archivo=str(self.pdf))
        reg["autores"][0]["declarante"] = False
        self.assertTrue(any("declarante" in e for e in self.errores(reg)))

    def test_en_prensa_y_preprint_bloquean(self):
        self.assertTrue(any("prensa" in e for e in self.errores(articulo(archivo=str(self.pdf), en_prensa=True))))
        self.assertTrue(any("preprint" in e for e in self.errores(articulo(archivo=str(self.pdf), version_adjunto="preprint"))))

    def test_pdf_de_mas_de_35_mb_bloquea(self):
        grande = Path(self.tmp.name) / "g.pdf"
        with grande.open("wb") as f:
            f.truncate(36 * 2**20)
        self.assertTrue(any("35" in e for e in self.errores(articulo(archivo=str(grande)))))

    def test_generico_no_acepta_botones_que_modifican(self):
        reg = {"clave": "g", "tipo": "generico", "rubro": "Premio", "url_alta": "eva/x.do", "url_lista": "eva/l.do",
               "campos": {"a": "b"}, "buscar_en_lista": "b", "boton_guardar": "Modificar"}
        self.assertTrue(any("Modificar" in e for e in self.errores(reg)))

    def test_fuera_de_latin1_se_avisa(self):
        texto, cambiados = B.a_latin1("Güneş – “x”")
        self.assertEqual(texto, 'Günes - "x"')
        self.assertEqual(cambiados, ["ş"])


class TestListaYCatalogo(unittest.TestCase):
    HTML = """<table id="articulo"><thead><tr><th><a href="n.do?action=Nuevo">NUEVO</a></th>
      <th><a href="l.do?d-3997137-s=1">AÑO</a></th><th>TÍTULO</th></tr></thead><tbody>
      <tr><td colspan="3">No hay registros cargados.</td></tr>
      <tr><td><a href="e.do?action=Editar&produccionId=9">EDITAR</a></td><td>2024</td>
      <td>Un titulo de prueba suficientemente largo para...</td></tr></tbody></table>"""

    def test_titulo_truncado_coincide_por_prefijo(self):
        tabla = B.parsear_tablas(self.HTML)[0]
        self.assertEqual(tabla["id"], "3997137")
        fila = B.buscar_en_tabla(tabla, "Un título de prueba suficientemente largo para la lista")
        self.assertEqual((fila["anio"], fila["editar"]), (2024, "e.do?action=Editar&produccionId=9"))

    def test_prefijo_corto_no_alcanza(self):
        self.assertFalse(B.fila_coincide("Redes...", "Redes neuronales profundas"))

    def test_html_sin_columna_titulo_corta_la_tanda(self):
        tabla = {"cabecera": ["NUEVO", "AÑO"], "filas": []}
        with self.assertRaises(B.CorteTanda):
            B.buscar_en_tabla(tabla, "x")

    def test_catalogo_solo_coincidencia_exacta(self):
        cat = {"instituciones": {"nanjing university": {"id": "1", "label": "NANJING UNIVERSITY"}}}
        reg = {"tipo": "evento", "autores": [{"apellido": "A", "institucion": "Nanjing Institute of Geology"},
                                              {"apellido": "B", "institucion": "Nanjing University"}]}
        avisos = B.resolver_con_catalogo(reg, cat)
        self.assertNotIn("institucion_id", reg["autores"][0])
        self.assertEqual(reg["autores"][1]["institucion_id"], "1")
        self.assertEqual(len(avisos), 1)

    def test_tabla_se_identifica_por_su_parametro_de_orden(self):
        # SIGEVA copia la query (con el -p de otras tablas) en los enlaces de orden de todas las tablas.
        html = """<table id="libro"><thead><tr><th>NUEVO</th>
          <th><a href="l.do?d-8106305-p=1&d-148512-o=2&d-148512-s=1">AÑO</a></th><th>TÍTULO</th></tr></thead><tbody></tbody></table>
          <table id="congresoPublicado"><thead><tr><th>NUEVO</th>
          <th><a href="l.do?d-8106305-p=1&d-8106305-o=2&d-8106305-s=1">AÑO</a></th><th>TÍTULO</th></tr></thead><tbody></tbody></table>"""
        self.assertEqual([t["id"] for t in B.parsear_tablas(html)], ["148512", "8106305"])

    def test_preparar_descarta_lo_ya_cargado(self):
        inventario = {"tablas": {"articulo": B.parsear_tablas(self.HTML)[0]}}
        r = B.preparar([articulo()], B.cargar_config(None) | CONFIG, {}, inventario)
        self.assertEqual((len(r["listos"]), len(r["ya_cargados"])), (0, 1))


class TestMapa(unittest.TestCase):
    BASE = "https://si.conicet.gov.ar/"
    ACTUAL = "https://si.conicet.gov.ar/eva/indexBancoDatos.do"

    def clasificar(self, href):
        return M.clasificar_url(href, self.ACTUAL, self.BASE)

    def test_solo_se_visitan_listas_y_altas_vacias(self):
        self.assertTrue(self.clasificar("bcoPremio.do?accion=nuevo")["visitar"])
        for href in ("bcoPremio.do?accion=borrar&id=5", "bcoPremio.do?accion=editar&id=5", "salir.jsp",
                     "bcoImportarFormulario.do?sincronizarformId=30", "/intranet/index.htm", "https://otro.org/x"):
            self.assertFalse(self.clasificar(href)["visitar"], href)

    def test_ruta_canonica_sin_ids_de_registros_ni_paginacion_acumulada(self):
        a = self.clasificar("bcoRoles.do?idMenu=1479&buttonSubmit=paginar&buttonSubmit=paginar&idModulo=1")["ruta"]
        b = self.clasificar("bcoRoles.do?idModulo=1&idMenu=1479")["ruta"]
        self.assertEqual(a, b)
        borrar = self.clasificar("bcoFormacionTesis.do?accion=borrar&formacionId=1167646&tipo=1")["ruta"]
        self.assertNotIn("1167646", borrar)
        self.assertIn("tipoFinanciamientoId=5", self.clasificar("bcofinanciamientoCYTProyecto.do?tipoFinanciamientoId=5&accion=nuevo")["ruta"])

    def pantalla(self, campos, tablas=None):
        return {"titulo": "t", "tipo": "formulario", "navegacion": [], "acciones": {}, "tablas": tablas or [],
                "formularios": [{"name": "f", "action": "x.do", "metodo": "post", "botones": ["Guardar"], "botones_name": [],
                                 "campos": campos}]}

    @staticmethod
    def campo(nombre, **extra):
        return {"name": nombre, "tag": "input", "tipo": "text", "etiqueta": nombre, "obligatorio": False,
                "visible": True, "datepicker": False, "cantidad": 1, "valores_opcion": [], "opciones": None} | extra

    def test_detecta_campos_nuevos_eliminados_y_cambios_de_tipo(self):
        base = {"version_sigeva": "1", "pantallas": {"p": self.pantalla([self.campo("a"), self.campo("b")])}}
        actual = {"version_sigeva": "2", "pantallas": {"p": self.pantalla([
            self.campo("a", tag="select", tipo="select-one", opciones=[["1", "x"]]), self.campo("c", obligatorio=True)])}}
        tipos = {(c["tipo"], c["severidad"]) for c in M.comparar_mapas(base, actual)}
        self.assertTrue({("campo-eliminado", "alto"), ("campo-nuevo", "alto"), ("campo-tipo", "alto"), ("version", "medio")} <= tipos)

    def test_pantallas_personales_no_publican_opciones(self):
        mapa = {"pantallas": {
            "bcoDatoPersonalIdentificacion.do?idModulo=2": self.pantalla([self.campo("partidoNacimientoId", tag="select", opciones=[["7", "Tandil"]])]),
            "bcoPremio.do?accion=nuevo": self.pantalla([self.campo("tipoPremio", tag="select", opciones=[["1", "Nacional"]])])}}
        saneado = M.sanear(mapa)
        personal = saneado["pantallas"]["bcoDatoPersonalIdentificacion.do?idModulo=2"]["formularios"][0]["campos"][0]
        self.assertNotIn("opciones_hash", personal)
        self.assertNotIn("Tandil", json.dumps(saneado))
        self.assertEqual(saneado["pantallas"]["bcoPremio.do?accion=nuevo"]["formularios"][0]["campos"][0]["opciones_n"], 1)

    def test_cambio_de_opciones_se_detecta_tambien_contra_mapa_saneado(self):
        base = M.sanear({"pantallas": {"p": self.pantalla([self.campo("s", tag="select", opciones=[["1", "a"]])])}})
        actual = {"pantallas": {"p": self.pantalla([self.campo("s", tag="select", opciones=[["1", "a"], ["2", "b"]])])}}
        self.assertEqual([c["tipo"] for c in M.comparar_mapas(base, actual)], ["campo-opciones"])
        self.assertNotIn("opciones", json.dumps(base["pantallas"]["p"]["formularios"][0]["campos"][0]).replace("opciones_", ""))

    def test_contrato_roto_es_critico(self):
        mapa = {"pantallas": {"x.do?a=1": self.pantalla([self.campo("fecha")],
                                                       [{"id": "t", "orden": "1", "cabecera": ["AÑO"]}])}}
        contrato = [{"uso": "u", "pantalla": "x.do?a=1", "campos": {"fecha": {"datepicker": True}, "falta": {}},
                     "botones": ["Guardar", "Omitir"], "tablas": {"t": {"orden": "2", "columnas": ["TÍTULO"]}}}]
        cambios = M.verificar_contrato(mapa, contrato)
        self.assertEqual({c["tipo"] for c in cambios},
                         {"contrato-campo", "contrato-boton", "contrato-tabla", "contrato-datepicker"})
        self.assertIn("critico", {c["severidad"] for c in cambios})

    def test_historial_mas_reciente_arriba(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "h.md"
            for n in ("1", "2"):
                informe = {"verificado_en_utc": f"2026-10-0{n}", "version_base": "a", "version_actual": "b",
                           "resumen": {"critico": 0}, "cambios": [{"severidad": "bajo", "pantalla": "p", "tipo": "t", "detalle": n}]}
                M.registrar_historial(ruta, informe, adoptado=True)
            texto = ruta.read_text(encoding="utf-8")
            self.assertLess(texto.index("2026-10-02"), texto.index("2026-10-01"))
            self.assertEqual(texto.count("# Historial"), 1)


class TestCruceCV(unittest.TestCase):
    CV_TEXTO = [
        "Artículos en publicaciones científicas con referato",
        "GARCIA, Maria “Un artículo ya cargado en SIGEVA con título largo”, en Revista, 2021, ISSN 2014-6590.",
        "GARCIA, Maria “Un artículo nuevo que todavía no figura en ninguna lista”, en Revista, 2024.",
        "GARCIA, Maria “Un artículo viejo de antes del período pedido”, en Revista, 2010.",
        "Libros",
        "GARCIA, Maria y LOPEZ, Juan (compiladores) La organización de los trabajadores rurales. Balances, métodos, Edisur, 2026.",
        "GARCIA, Maria El libro todavía no publicado, Edisur, [en prensa].",
        "Artículos de divulgación",
        "GARCIA, Maria “Una nota de divulgación que no va al banco”, El Diario, 2023.",
    ]
    INVENTARIO = {"tablas": {
        "articulo": {"cabecera": ["Nuevo", "Año", "Título"], "filas": [{"celdas": ["E", "2021", "Un artículo ya cargado en SIGEVA con..."], "editar": "e"}]},
        "libro": {"cabecera": ["Nuevo", "Año", "Título"], "filas": [{"celdas": ["E", "2026", "La organización de los trabajadores rurales. Balances, m..."], "editar": "e"}]}}}

    def test_secciones_titulos_y_anios(self):
        items = CV.parsear_cv(self.CV_TEXTO)
        self.assertEqual([i["tipo"] for i in items], ["articulo"] * 3 + ["libro"] * 2)
        self.assertEqual(items[0]["anio"], 2021)  # el ISSN 2014-6590 no es un año
        self.assertEqual(items[3]["titulo"], "La organización de los trabajadores rurales. Balances, métodos")
        self.assertFalse(items[4]["publicado"])

    def test_cruce_separa_cargado_faltante_rango_y_no_publicado(self):
        r = CV.cruzar(CV.parsear_cv(self.CV_TEXTO), self.INVENTARIO, desde=2020)
        self.assertEqual([e["titulo"] for e in r["falta"]], ["Un artículo nuevo que todavía no figura en ninguna lista"])
        self.assertEqual((r["resumen"]["ya_cargado"], r["resumen"]["fuera_de_rango"], r["resumen"]["no_publicado"]), (2, 1, 1))

    def test_recorte_de_pdf(self):
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.skipTest("pypdf no instalado")
        with tempfile.TemporaryDirectory() as tmp:
            origen, salida = Path(tmp) / "a.pdf", Path(tmp) / "b.pdf"
            w = PdfWriter()
            for _ in range(5):
                w.add_blank_page(100, 100)
            w.write(str(origen))
            self.assertEqual(CV.recortar_pdf(origen, salida, "1,3-4"), 3)
            self.assertEqual(len(PdfReader(str(salida)).pages), 3)
            with self.assertRaises(ValueError):
                CV.recortar_pdf(origen, salida, "4-9")


class TestCredenciales(unittest.TestCase):
    def test_env_incompleto_falla_sin_mostrar_valores(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / ".env"
            ruta.write_text("USER=secreto-usuario\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                B.cargar_env(str(ruta))
            self.assertNotIn("secreto-usuario", str(ctx.exception))


def _chromium_disponible() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            pw.chromium.launch(headless=True).close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_chromium_disponible(), "Playwright/Chromium no instalados")
class TestSimulado(unittest.TestCase):
    def setUp(self):
        import sigeva_simulado as S

        self.servidor = S.Servidor().__enter__()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pdf = self.dir / "full.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 prueba")
        self.config = self.dir / "config.json"
        self.config.write_text(json.dumps({"base": self.servidor.base, **CONFIG}), encoding="utf-8")
        for clave in ("SIGEVA_USER", "SIGEVA_PASS"):
            os.environ.pop(clave, None)
        # Linea base del simulador: todo trabajo contra SIGEVA empieza con verificar --auto contra ella.
        self.refs = self.dir / "refs"
        self.correr("mapear", "--headless", "--referencias", str(self.refs), "--aceptar", "--pausa-ms", "0")
        self.servidor.estado.peticiones.clear()

    def tearDown(self):
        self.servidor.__exit__(None, None, None)
        self.tmp.cleanup()

    def correr(self, *argv) -> tuple[int, dict]:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(io.StringIO()):
            codigo = B.main([argv[0], "--config", str(self.config), "--dir", str(self.dir), *argv[1:]])
        return codigo, json.loads(salida.getvalue())

    def cargar(self, registros, *flags):
        ruta = self.dir / "registros.json"
        ruta.write_text(json.dumps(registros), encoding="utf-8")
        return self.correr("cargar", "--registros", str(ruta), "--headless", "--referencias", str(self.refs),
                           "--pausa-ms", "0", *flags)

    def recorridos(self) -> int:
        """Cuantas veces se recorrio el sitio: el mapeo arranca siempre por el indice con idMenu=0."""
        return sum(1 for _, p in self.servidor.estado.peticiones if "indexBancoDatos.do?" in p and "idMenu=0" in p)

    def posts(self):
        return [p for m, p in self.servidor.estado.peticiones if m == "POST"]

    def test_en_seco_no_guarda(self):
        codigo, recibo = self.cargar([articulo(archivo=str(self.pdf))])
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "en-seco"))
        self.assertEqual(self.servidor.estado.registros["articulo"], [])

    def test_articulo_guardado_y_verificado_con_fecha_real(self):
        codigo, recibo = self.cargar([articulo(archivo=str(self.pdf))], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        r = self.servidor.estado.registros["articulo"][0]
        # El datepicker simulado pisa con el mes actual si no se usa setDate: 09/2024 prueba que no paso.
        self.assertEqual(r["fechas"]["fechaPublica"], ["09/2024", "09/2024"])
        self.assertEqual((r["orgs"], r["personas"][0], r["area"], r["idioma"]), (["8434"], "555", ["605"], ["2"]))
        self.assertEqual(r["palabras"], ["REDES"])
        # Segunda corrida: estado.jsonl lo da por hecho y no se vuelve a cargar.
        _, recibo2 = self.cargar([articulo(archivo=str(self.pdf))], "--guardar")
        self.assertEqual(recibo2["solicitados"], 0)
        self.assertEqual(len(self.servidor.estado.registros["articulo"]), 1)

    def test_lo_que_ya_esta_en_la_lista_no_se_duplica(self):
        self.servidor.estado.alta("articulo", {"titulo": articulo()["titulo"], "anio": "2024", "fechas": {}})
        _, recibo = self.cargar([articulo(archivo=str(self.pdf))], "--guardar")
        self.assertEqual(recibo["resultados"][0]["resultado"], "ya-estaba")
        self.assertEqual(len(self.servidor.estado.registros["articulo"]), 1)

    def test_guardar_silencioso_se_informa_como_no_guardado(self):
        B.INTENTOS_CONFIRMACION, previo = 1, B.INTENTOS_CONFIRMACION
        try:
            codigo, recibo = self.cargar([articulo(archivo=str(self.pdf), titulo="SILENCIO titulo largo de prueba para la lista")], "--guardar")
        finally:
            B.INTENTOS_CONFIRMACION = previo
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (1, "no-guardado"))

    def test_error_que_vacia_el_archivo_se_reintenta_una_vez(self):
        reg = articulo(archivo=str(self.pdf), titulo="REINTENTO titulo largo de prueba para la lista")
        codigo, recibo = self.cargar([reg], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.registros["articulo"][0]["fechas"]["fechaPublica"][0], "09/2024")

    def test_evento_con_fechas_de_reunion_y_actas(self):
        reg = {"clave": "e1", "tipo": "evento", "titulo": "Trabajo en evento con titulo de prueba largo",
               "autores": [{"apellido": "Perez", "nombre": "Ana", "declarante": True}], "idioma": "Español",
               "resumen": "R", "archivo": str(self.pdf), "titulo_publicacion": "Actas", "tipo_publicacion": "Libro",
               "reunion": "WS", "tipo_reunion": "Workshop", "pais_evento": "Argentina", "ciudad_evento": "Mar del Plata",
               "pais_edicion": "Argentina", "editorial": "Ed", "anio_publicacion": 2025, "fecha_evento": "12/2024",
               "alcance": "internacional", "url": "https://x.org"}
        codigo, recibo = self.cargar([reg], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.registros["evento"][0]["fechas"],
                         {"fechaReunion": ["12/2024"], "anioPublica": ["2025"]})

    def libro_base(self, **extra) -> dict:
        reg = {"clave": "l1", "tipo": "libro", "titulo": "Un libro de prueba con titulo suficientemente largo",
               "autores": [{"apellido": "Perez", "nombre": "Ana", "declarante": True, "institucion_id": "4455", "institucion": "Instituto de Estudios Sociales"},
                           {"apellido": "Gomez", "nombre": "Luis"}],
               "idioma": "Español", "resumen": "R", "archivo": str(self.pdf), "isbn": "978-987-811-173-5",
               "pais_edicion": "Argentina", "ciudad_edicion": "La Plata", "editorial": "Editorial Universitaria", "anio_publicacion": 2024,
               "referato": False, "rol": ["autor"], "url": "https://x.org", "paginas_libro": "110"}
        return reg | extra

    def test_capitulo_con_compiladores_rol_y_referato(self):
        reg = self.libro_base(clave="c1", tipo="capitulo", titulo="Un capitulo de prueba con titulo suficientemente largo",
                              tipo_parte="Introducción", titulo_libro="Libro compilado", paginas="15-69", referato=True,
                              rol=["autor", "editor"],
                              compiladores=[{"apellido": "Lopez", "nombre": "J", "institucion_id": "4455", "institucion": "Instituto de Estudios Sociales"},
                                            {"apellido": "Perez", "nombre": "Ana", "declarante": True}])
        codigo, recibo = self.cargar([reg], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        r = self.servidor.estado.registros["capitulo"][0]
        self.assertEqual((r["compiladores"], r["orgs_compiladores"]), (["Lopez, J", "Perez, Ana"], ["4455"]))
        self.assertEqual((r["personas"][0], r["personas_compiladores"][1]), ("555", "555"))
        self.assertEqual((r["roles"], r["referato"], r["tipoParte"]), (["isAutor", "isEditor"], ["2"], ["5"]))
        self.assertEqual(r["fechas"]["anioPublica"], ["2024"])

    def test_libro_en_seco_no_sube_y_al_guardar_sube_por_el_uploader(self):
        _, recibo = self.cargar([self.libro_base()])
        self.assertEqual(recibo["resultados"][0]["resultado"], "en-seco")
        self.assertEqual(self.servidor.estado.subidas, [])
        codigo, recibo = self.cargar([self.libro_base()], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.subidas, ["full.pdf"])
        r = self.servidor.estado.registros["libro"][0]
        self.assertEqual((r["autores"][:2], r["orgs"], r["referato"], r["roles"]),
                         (["Perez, Ana", "Gomez, Luis"], ["4455"], ["0"], ["isAutor"]))

    def preparar_modificacion(self, modo: str) -> int:
        self.config.write_text(json.dumps({"base": self.servidor.base, **CONFIG, "declarante": {"apellido": "Garcia"}}),
                               encoding="utf-8")
        self.servidor.estado.modo_modificar = modo
        return self.servidor.estado.alta("capitulo", {
            "titulo": "Historia del trabajo en el puerto", "anio": "2015", "fechas": {"anioPublica": ["2015"]},
            "publicado": "2", "autores": ["Maria Garcia"], "personas": [""], "editable": True})

    def modificar(self, *flags):
        return self.correr("modificar", "--tipo", "capitulo", "--titulo", "Historia del trabajo en el puerto",
                           "--campo", "anioPublica=2022", "--campo", "publicado=1", "--headless",
                           "--referencias", str(self.refs), "--pausa-ms", "0", *flags)

    def test_modificar_en_seco_no_cambia_nada(self):
        viejo = self.preparar_modificacion("version-nueva")
        codigo, r = self.modificar()
        self.assertEqual((codigo, r["resultado"]), (0, "en-seco"), r)
        self.assertEqual(r["cambios"]["anioPublica"], {"antes": ["2015"], "despues": ["2022"]})
        self.assertEqual(r["declarante"]["estado"], "marcado")
        self.assertEqual([(x["id"], x["anio"]) for x in self.servidor.estado.registros["capitulo"]], [(viejo, "2015")])

    def test_modificar_con_version_nueva_deja_un_solo_registro(self):
        viejo = self.preparar_modificacion("version-nueva")
        codigo, r = self.modificar("--guardar")
        self.assertEqual((codigo, r["resultado"], r["modo_sigeva"]), (0, "modificado", "version-nueva"), r)
        [registro] = self.servidor.estado.registros["capitulo"]
        self.assertNotEqual(registro["id"], viejo)
        self.assertEqual((registro["anio"], registro["publicado"], registro["personas"]), ("2022", "1", ["555"]))

    def test_modificar_en_el_lugar_conserva_el_id(self):
        viejo = self.preparar_modificacion("en-el-lugar")
        codigo, r = self.modificar("--guardar")
        self.assertEqual((codigo, r["resultado"], r["id_despues"]), (0, "modificado", str(viejo)), r)
        self.assertEqual(len(self.servidor.estado.registros["capitulo"]), 1)

    def test_duplicado_se_informa_y_solo_se_borra_con_permiso(self):
        self.preparar_modificacion("duplicar")
        codigo, r = self.modificar("--guardar")
        self.assertEqual((codigo, r["resultado"]), (1, "duplicado"), r)
        self.assertEqual(len(self.servidor.estado.registros["capitulo"]), 2)
        # Con permiso: se repite desde el registro que muestra la lista ahora... pero hay dos con ese titulo.
        codigo, r = self.modificar("--guardar", "--borrar-duplicado")
        self.assertEqual((codigo, r["resultado"]), (1, "error"), r)
        self.assertIn("2 registros", r["detalle"])

    def test_duplicado_con_permiso_borra_el_viejo_tras_verificar_el_nuevo(self):
        viejo = self.preparar_modificacion("duplicar")
        codigo, r = self.modificar("--guardar", "--borrar-duplicado")
        self.assertEqual((codigo, r["resultado"], r["duplicado_borrado"]), (0, "modificado", str(viejo)), r)
        [registro] = self.servidor.estado.registros["capitulo"]
        self.assertEqual(registro["anio"], "2022")
        self.assertFalse(any(m == "GET" and "action=Borrar" in p and str(viejo) not in p for m, p in self.servidor.estado.peticiones))

    def test_rubro_generico_se_verifica_por_id_nuevo(self):
        reg = {"clave": "p1", "tipo": "generico", "rubro": "Premio", "url_alta": "eva/bcoPremio.do?accion=nuevo",
               "url_lista": "eva/bcoPremioLista.do?idModulo=7&idGrupo=7&idMenu=1470", "buscar_en_lista": "Premio Houssay",
               "campos": {"premio": "Premio Houssay", "tipoPremio": {"etiqueta": "Nacional"}, "anio": "2023",
                          "institucionOtorgante": "MINCyT"}}
        codigo, recibo = self.cargar([reg], "--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.registros["premio"][0]["tipoPremio"], "1")

    def test_el_trabajo_no_empieza_si_sigeva_cambio(self):
        base_antes = (self.refs / "mapa-base.json").read_text(encoding="utf-8")
        self.servidor.estado.quitar_campo = "fechaPublica"
        with self.assertRaises(SystemExit) as ctx:
            self.cargar([articulo(archivo=str(self.pdf))], "--guardar")
        self.assertIn("fechaPublica", str(ctx.exception))
        self.assertEqual(self.servidor.estado.registros["articulo"], [])
        self.assertEqual(self.posts(), ["/eva/bcoPrecargarArticulo.do"])  # solo el paso Omitir del recorrido
        self.assertEqual((self.refs / "mapa-base.json").read_text(encoding="utf-8"), base_antes)
        self.assertIn("SIN actualizar", (self.refs / "historial-cambios.md").read_text(encoding="utf-8"))

    def test_verificacion_previa_vigente_se_reusa(self):
        self.cargar([articulo(archivo=str(self.pdf))])
        self.assertEqual(self.recorridos(), 1)
        self.cargar([articulo(archivo=str(self.pdf))])
        self.assertEqual(self.recorridos(), 1)
        self.cargar([articulo(archivo=str(self.pdf))], "--vigencia-horas", "0")
        self.assertEqual(self.recorridos(), 2)

    def test_mapear_es_solo_lectura_y_verificar_detecta_cambios(self):
        refs = self.dir / "refs"
        codigo, mapa = self.correr("mapear", "--headless", "--referencias", str(refs), "--aceptar", "--pausa-ms", "0")
        self.assertEqual((codigo, mapa["contrato"], mapa["completo"]), (0, [], True), mapa)
        # Solo el paso seguro "Omitir" envia algo; nunca Guardar, Borrar, Importar ni salir.
        self.assertTrue(self.posts() and all(p.startswith("/eva/bcoPrecargarArticulo.do") for p in self.posts()))
        visitadas = " ".join(p for _, p in self.servidor.estado.peticiones).lower()
        for prohibido in ("borrar", "importar", "salir.jsp"):
            self.assertNotIn(prohibido, visitadas)
        self.assertTrue((refs / "mapa-sitio.md").exists())

        codigo, informe = self.correr("verificar", "--headless", "--referencias", str(refs), "--auto", "--pausa-ms", "0")
        self.assertEqual((codigo, informe["cambios"]), (0, []))

        base_antes = (refs / "mapa-base.json").read_text(encoding="utf-8")
        self.servidor.estado.quitar_campo = "fechaPublica"
        codigo, informe = self.correr("verificar", "--headless", "--referencias", str(refs), "--auto", "--pausa-ms", "0")
        self.assertEqual(codigo, 2)
        self.assertGreater(informe["resumen"]["critico"], 0)
        self.assertEqual((refs / "mapa-base.json").read_text(encoding="utf-8"), base_antes)
        self.assertIn("SIN actualizar", (refs / "historial-cambios.md").read_text(encoding="utf-8"))


class TestPipRelleno(unittest.TestCase):
    """Lógica pura de grillas (sin navegador): emparejado contra la grilla real."""

    def test_planificar_grilla_mapea_por_rubro_y_anio(self):
        mapa = [{"indice": 0, "etiqueta": "Equipamiento (1)", "rubro": "1", "anio": "2026"},
                {"indice": 1, "etiqueta": "Equipamiento (1)", "rubro": "1", "anio": "2027"},
                {"indice": 3, "etiqueta": "Licencias (2)", "rubro": "2", "anio": "2026"}]
        plan = PIP.planificar_grilla(mapa, {"1": {"2027": "2000000,00"}, "2": {"2026": "0,00"}})
        self.assertEqual(plan, [(1, "2000000,00"), (3, "0,00")])

    def test_planificar_grilla_rechaza_celda_inexistente_o_ambigua(self):
        mapa = [{"indice": 0, "etiqueta": "Equipamiento (1)", "rubro": "1", "anio": "2026"}]
        with self.assertRaises(PIP.ErrorPip):
            PIP.planificar_grilla(mapa, {"9": {"2026": "1,00"}})
        with self.assertRaises(PIP.ErrorPip):
            PIP.planificar_grilla(
                [{"indice": 0, "etiqueta": "Equipamiento (1)", "rubro": "1", "anio": "2026"},
                 {"indice": 1, "etiqueta": "Otro (1)", "rubro": "1", "anio": "2027"}],
                {"1": {"2026": "1,00"}})
        with self.assertRaises(PIP.ErrorPip):
            PIP.planificar_grilla([], {"1": {"2026": "1,00"}})

    def test_planificar_grilla_acepta_codigo_distinto_del_numero_visible(self):
        # Financiamiento adicional: ubicaciones 4/5/7/8 con etiquetas (2)/(3)/(4)/(5).
        mapa = [{"indice": 3, "etiqueta": "Bienes de consumo (2)", "rubro": "4", "anio": "2026"},
                {"indice": 4, "etiqueta": "Bienes de consumo (2)", "rubro": "4", "anio": "2027"}]
        plan = PIP.planificar_grilla(mapa, {"4": {"2026": "150000,00"}})
        self.assertEqual(plan, [(3, "150000,00")])

    def test_planificar_grupo_empareja_por_nombre_y_avisa_faltantes(self):
        filas = [{"indice": 0, "texto": "NIETO, ALEJANDRO AGUSTÍN | INV INDEPENDIENTE", "pid": "420837", "ded": "100"},
                 {"indice": 1, "texto": "PIVA, ADRIÁN | INV PRINCIPAL", "pid": "422703", "ded": "100"}]
        plan, avisos = PIP.planificar_grupo(
            filas, [{"nombre": "Nieto, Alejandro Agustin", "dedicacion": "100"},
                    {"nombre": "Piva, Adrián", "dedicacion": "50", "rol": "Investigador"},
                    {"nombre": "Román, Maximiliano", "dedicacion": "50"}])
        self.assertEqual(avisos, ["no encontrado (o ambiguo) en la grilla: Román, Maximiliano"])
        self.assertEqual(plan[0], {"indice": 0, "pid": "420837", "valor_rol": None, "dedicacion": "100"})
    def test_grupo_al_dia_detecta_diferencias(self):
        filas = [{"indice": 0, "texto": "NIETO, ... | INV INDEPENDIENTE", "pid": "1",
                  "ded": "100", "rol": "1-0"},
                 {"indice": 1, "texto": "PIVA, ... | INV PRINCIPAL", "pid": "2",
                  "ded": "50", "rol": "2-3"}]
        ok, _ = PIP.grupo_al_dia(filas, [{"nombre": "Nieto", "dedicacion": "100"},
                                          {"nombre": "Piva", "dedicacion": "50"}])
        # "Nieto" está contenido en "NIETO, ..." y "Piva" en "PIVA, ...": coinciden.
        self.assertTrue(ok)
        ok2, _ = PIP.grupo_al_dia(filas, [{"nombre": "Nieto", "dedicacion": "100"}])
        self.assertTrue(ok2)
        ok3, _ = PIP.grupo_al_dia([dict(filas[0], ded="50")],
                                   [{"nombre": "Nieto", "dedicacion": "100"}])
        self.assertFalse(ok3)
        # Figura con la dedicación pedida pero sin la casilla HAB: no integra el proyecto.
        ok4, _ = PIP.grupo_al_dia([dict(filas[0], hab=False)], [{"nombre": "Nieto", "dedicacion": "100"}])
        self.assertFalse(ok4)

    def test_diferencias_campos_normaliza_espacios_y_detecta_cambios(self):
        actual = {"titulo": {"valor": "Enfoques  computacionales\r\npara la protesta "},
                  "area": {"valor": "KS", "texto": "KS - Ciencias Sociales"},
                  "comite": {"valor": "2"}, "fecha": {"valor": "09/2027"}}
        iguales = {"titulo": "Enfoques computacionales para la protesta", "area": {"valor": "KS"},
                   "comite": "2", "fecha": {"fecha": "09/2027"}}
        self.assertEqual(PIP.diferencias_campos(actual, iguales), [])
        self.assertEqual(PIP.diferencias_campos(actual, {"titulo": "Otro título", "area": {"etiqueta": "KS - Ciencias Sociales"},
                                                         "falta": "x"}), ["titulo", "falta"])

    def test_filas_al_dia_ignora_vacias_y_respeta_orden(self):
        pedidas = [{"apellido": "PACHECO", "nombre": "Diego", "observacion": "Coautor"},
                   {"apellido": "SANTELLA", "nombre": "Agustín", "observacion": "Coautor"}]
        cargadas = [["PACHECO", "Diego", "Coautor "], ["SANTELLA", "Agustín", "Coautor"], ["", "", ""]]
        self.assertTrue(PIP.filas_al_dia(cargadas, pedidas))
        self.assertFalse(PIP.filas_al_dia(list(reversed(cargadas[:2])), pedidas))
        self.assertFalse(PIP.filas_al_dia(cargadas[:1], pedidas))

    def test_huella_cambia_con_el_contenido_y_no_con_los_avisos(self):
        item = {"clave": "datos", "seccion": "Datos del proyecto", "campos": {"t": "A"}, "avisos": []}
        self.assertEqual(PIP.huella(item), PIP.huella({**item, "avisos": ["otro aviso"]}))
        self.assertNotEqual(PIP.huella(item), PIP.huella({**item, "campos": {"t": "B"}}))


class TestPipPreparar(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pdf = self.dir / "plan.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 plan")
        self.config = {"limite_adjunto_mb": 35}

    def datos(self, **extra) -> dict:
        base = {"tramite": "11220260100119CO", "secciones": [
            {"clave": "datos-proyecto", "seccion": "Datos del proyecto",
             "campos": {"tituloProyecto": "Título", "resumenProyecto": "R", "fechaInicio": "09/2027"}},
            {"clave": "plan", "seccion": "Plan de trabajo (PDF)", "archivo": {"ruta": str(self.pdf), "tipo": "1"}},
        ]}
        base.update(extra)
        return base

    def test_valido_pasa_sin_errores(self):
        salida = PIP.validar_pip(self.datos(), self.config)
        self.assertEqual(salida["errores"], [])
        self.assertEqual([i["clave"] for i in salida["items"]], ["datos-proyecto", "plan"])
        self.assertEqual(salida["items"][1]["archivo"]["campo"], "theFile")

    def test_sin_tramite_o_sin_secciones_bloquea(self):
        self.assertTrue(PIP.validar_pip({}, self.config)["errores"])
        self.assertTrue(PIP.validar_pip({"tramite": "x"}, self.config)["errores"])
        self.assertTrue(PIP.validar_pip(self.datos(tramite="abc"), self.config)["errores"])

    def test_campos_vacios_no_se_estiman(self):
        datos = self.datos()
        datos["secciones"][0]["campos"]["resumenProyecto"] = ""
        salida = PIP.validar_pip(datos, self.config)
        self.assertTrue(any("no se estiman" in e for e in salida["errores"]))

    def test_adjunto_inexistente_o_no_pdf_o_grande_bloquea(self):
        datos = self.datos()
        datos["secciones"][1]["archivo"]["ruta"] = str(self.dir / "falta.pdf")
        self.assertTrue(any("no existe" in e for e in PIP.validar_pip(datos, self.config)["errores"]))
        otro = self.dir / "otro.txt"
        otro.write_text("no es pdf")
        datos["secciones"][1]["archivo"]["ruta"] = str(otro)
        self.assertTrue(any("no es un PDF" in e for e in PIP.validar_pip(datos, self.config)["errores"]))
        grande = self.dir / "grande.pdf"
        grande.write_bytes(b"%PDF-1.4 " + b"x" * 4096)
        datos["secciones"][1]["archivo"]["ruta"] = str(grande)
        salida = PIP.validar_pip(datos, {"limite_adjunto_mb": 0.001})
        self.assertTrue(any("límite" in e for e in salida["errores"]))

    def test_clave_duplicada_y_seccion_sin_contenido_bloquean(self):
        datos = self.datos()
        datos["secciones"].append({"clave": "plan", "seccion": "Plan de trabajo (PDF)"})
        salida = PIP.validar_pip(datos, self.config)
        self.assertTrue(any("duplicada" in e for e in salida["errores"]))
        salida = PIP.validar_pip(self.datos(secciones=[{"clave": "x", "seccion": "Seguridad"}]), self.config)
        self.assertTrue(any("nada para completar" in e for e in salida["errores"]))

    def test_filas_y_seleccion_se_validan_como_declaracion(self):
        filas = [{"apellido": "PACHECO", "nombre": "Diego", "observacion": "Coautor"}]
        ok = self.datos(secciones=[{"clave": "rec", "seccion": "Recusación", "filas": filas},
                                   {"clave": "fin", "seccion": "Otras Fuentes de Financiamiento",
                                    "seleccion": {"campo": "otrosFinanciamientos", "valores": ["1", "2"]}}])
        self.assertEqual(PIP.validar_pip(ok, self.config)["errores"], [])
        vacia = self.datos(secciones=[{"clave": "rec", "seccion": "Recusación",
                                       "filas": [{"apellido": "PACHECO", "nombre": "", "observacion": "x"}]}])
        self.assertTrue(any("no se estiman" in e for e in PIP.validar_pip(vacia, self.config)["errores"]))
        sin_campo = self.datos(secciones=[{"clave": "fin", "seccion": "Otras Fuentes de Financiamiento",
                                           "seleccion": {"valores": ["1", "1"]}}])
        self.assertTrue(any("'seleccion'" in e for e in PIP.validar_pip(sin_campo, self.config)["errores"]))

    def test_linea_base_del_simulador_no_habilita_el_sitio_real(self):
        with self.assertRaises(SystemExit):
            PIP._chequear_origen({"origen": "simulador"}, {"base": "https://si.conicet.gov.ar/"})
        PIP._chequear_origen({"origen": "real"}, {"base": "https://si.conicet.gov.ar/"})  # no explota
        PIP._chequear_origen({"origen": "simulador"}, {"base": "http://127.0.0.1:1/"})


@unittest.skipUnless(_chromium_disponible(), "Playwright/Chromium no instalados")
class TestPipSimulado(unittest.TestCase):
    """Punta a punta del modulo de convocatorias contra el simulador."""

    def setUp(self):
        import sigeva_simulado as S
        import sigeva_pip as PIP_MOD

        self.S = S
        self.PIP = PIP_MOD
        self.previo_intentos = PIP_MOD.INTENTOS_ESTADO
        PIP_MOD.INTENTOS_ESTADO = 1  # en tests no esperar 10 s entre relecturas
        self.servidor = S.Servidor().__enter__()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.plan = self.dir / "plan.pdf"
        self.plan.write_bytes(b"%PDF-1.4 plan de trabajo")
        self.config = self.dir / "config.json"
        self.config.write_text(json.dumps({"base": self.servidor.base, **CONFIG}), encoding="utf-8")
        for clave in ("SIGEVA_USER", "SIGEVA_PASS"):
            os.environ.pop(clave, None)
        # Linea base PIP del simulador: todo trabajo contra el modulo empieza con pip-verificar --auto.
        self.refs = self.dir / "refs"
        codigo, mapa = self.correr("pip-mapear", "--headless", "--referencias", str(self.refs),
                                   "--aceptar", "--pausa-ms", "0")
        assert codigo == 0, mapa
        self.servidor.estado.peticiones.clear()

    def tearDown(self):
        self.PIP.INTENTOS_ESTADO = self.previo_intentos
        self.servidor.__exit__(None, None, None)
        self.tmp.cleanup()

    def correr(self, *argv):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(io.StringIO()):
            codigo = B.main([argv[0], "--config", str(self.config), "--dir", str(self.dir), *argv[1:]])
        try:
            return codigo, json.loads(salida.getvalue())
        except json.JSONDecodeError:
            return codigo, {}

    def datos(self, **extra) -> dict:
        base = {"tramite": self.S.CODIGO_TRAMITE, "secciones": [
            {"clave": "datos-proyecto", "seccion": "Datos del proyecto",
             "campos": {"tituloProyecto": "Conflictividad y herramientas digitales",
                        "resumenProyecto": "Resumen", "fechaInicio": "09/2027"}},
            {"clave": "aspectos", "seccion": "Aspectos éticos",
             "campos": {"usaComiteEtica": "2", "fundamentacionEtica": "No involucra"}},
            {"clave": "plan", "seccion": "Plan de trabajo (PDF)", "archivo": {"ruta": str(self.plan), "tipo": "1"}},
        ]}
        base.update(extra)
        return base

    def pip_preparar(self, datos):
        ruta = self.dir / "pip.json"
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        return self.correr("pip-preparar", "--datos", str(ruta), "--salida", str(self.dir / "pip-listos.json"))

    def pip_cargar(self, *flags):
        return self.correr("pip-cargar", "--datos", str(self.dir / "pip-listos.json"),
                           "--headless", "--referencias", str(self.refs), "--pausa-ms", "0", *flags)

    def posts(self):
        return [p for m, p in self.servidor.estado.peticiones if m == "POST"]

    def test_pip_mapear_es_solo_lectura_y_arma_linea_base(self):
        refs = self.dir / "refs-pip"
        posts_antes = len(self.posts())
        codigo, mapa = self.correr("pip-mapear", "--headless", "--referencias", str(refs),
                                   "--aceptar", "--pausa-ms", "0")
        self.assertEqual((codigo, mapa["contrato"], mapa["completo"]), (0, [], True), mapa)
        self.assertEqual(mapa["origen"], "simulador")
        self.assertEqual(mapa["tramite_pantalla"], "index.do?tramiteid=7")
        self.assertEqual(self.posts()[posts_antes:], [])  # el recorrido del modulo no envia nada
        self.assertTrue((refs / PIP.BASE_PIP).exists() and (refs / PIP.DOC_PIP).exists())
        base = json.loads((refs / PIP.BASE_PIP).read_text(encoding="utf-8"))
        self.assertEqual(base["modulo"], "pip")
        self.assertEqual(base["estados_tabla_id"], "bcoSolicitudEstados")

    def test_pip_estados_ignora_filas_sin_estado(self):
        codigo, r = self.correr("pip-estados", "--headless", "--referencias", str(self.refs),
                                "--pausa-ms", "0")
        self.assertEqual(codigo, 0, r)
        self.assertNotIn("Presentación electrónica", r["estados"])
        self.assertEqual(len(r["estados"]), len(self.S.ESTADOS_PIP))

    def test_pip_cargar_en_seco_no_guarda_nada(self):
        codigo, salida = self.pip_preparar(self.datos())
        self.assertEqual(codigo, 0, salida)
        codigo, recibo = self.pip_cargar()
        self.assertEqual(codigo, 0, recibo)
        self.assertEqual([r["resultado"] for r in recibo["resultados"]], ["en-seco"] * 3)
        self.assertEqual(self.servidor.estado.tramite["estados"], {})
        # En seco el adjunto navega a la pagina de subida (Adjuntar), pero nunca Guarda:
        # todos los POST son a la lista de adjuntos y nada queda cargado.
        self.assertTrue(all(p == "/eva/cArchivosAdjuntos.do" for p in self.posts()))
        self.assertNotIn("Plan de trabajo (PDF)", self.servidor.estado.tramite.get("cargado", {}))

    def test_pip_cargar_guarda_relee_estados_y_no_aprieta_enviar(self):
        self.pip_preparar(self.datos())
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual(codigo, 0, recibo)
        self.assertEqual([r["resultado"] for r in recibo["resultados"]], ["guardado"] * 3)
        estados = recibo["estados"]
        self.assertEqual(estados["Datos del proyecto"], "Ok")
        self.assertEqual(estados["Aspectos éticos"], "Ok")
        self.assertEqual(estados["Plan de trabajo (PDF)"], "Ok")
        self.assertEqual(self.servidor.estado.tramite["enviado"], False)
        self.assertFalse(any("solicitudEnviar" in p for p in self.posts()))
        # El datepicker simulado pisa con el mes actual si no se uso setDate.
        cargado = self.servidor.estado.tramite["cargado"]["Datos del proyecto"]
        self.assertEqual(cargado["fechaInicio"], ["09/2027", "09/2027"])
        self.assertEqual(self.servidor.estado.tramite["cargado"]["Plan de trabajo (PDF)"]["archivo"], "plan.pdf")
        # Segunda corrida: estado-pip.jsonl lo da por hecho (ya-estaba en el tramite).
        _, recibo2 = self.pip_cargar("--guardar")

    def test_pip_adjunta_segundo_slot_y_lo_marca_ok(self):
        aval = self.dir / "aval.pdf"
        aval.write_bytes(b"%PDF-1.4 aval")
        datos = self.datos()
        datos["secciones"] = [{"clave": "aval", "seccion": "Aval de la autoridad máxima (PDF firmado)",
                               "archivo": {"ruta": str(aval), "tipo": "105"}}]
        self.pip_preparar(datos)
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(recibo["estados"]["Aval de la autoridad máxima (PDF firmado)"], "Ok")

    def test_pip_seccion_en_ok_con_datos_viejos_se_actualiza_y_la_igual_no_se_toca(self):
        datos = self.datos()
        datos["secciones"] = [datos["secciones"][0]]
        self.pip_preparar(datos)
        self.assertEqual(self.pip_cargar("--guardar")[1]["resultados"][0]["resultado"], "guardado")
        # El plan cambió el título: la sección sigue en "Ok", pero con el título viejo.
        datos["secciones"][0]["campos"]["tituloProyecto"] = "Título nuevo del plan"
        self.pip_preparar(datos)
        codigo, recibo = self.pip_cargar("--guardar")
        r = recibo["resultados"][0]
        self.assertEqual((codigo, r["resultado"], r["difiere"]), (0, "guardado", ["campo tituloProyecto"]), recibo)
        cargado = self.servidor.estado.tramite["cargado"]["Datos del proyecto"]
        self.assertEqual(cargado["tituloProyecto"], ["Título nuevo del plan"])
        # Mismo contenido: la huella del log lo da por hecho.
        self.assertEqual(self.pip_cargar("--guardar")[1]["solicitados"], 0)
        # Sin log (otra carpeta de trabajo): se compara contra el sitio y no se guarda nada.
        (self.dir / "estado-pip.jsonl").unlink()
        posts_antes = len(self.posts())
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual(recibo["resultados"][0]["resultado"], "ya-estaba", recibo)
        self.assertNotIn("/eva/solicitudDatosProyecto.do", self.posts()[posts_antes:])

    def test_pip_recusacion_por_filas(self):
        filas = [{"apellido": "PACHECO", "nombre": "Diego", "observacion": "Coautor (2026)"},
                 {"apellido": "SANTELLA", "nombre": "Agustín", "observacion": "Coautor (2026)"}]
        self.pip_preparar(self.datos(secciones=[{"clave": "rec", "seccion": "Recusación", "filas": filas}]))
        codigo, recibo = self.pip_cargar()
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "en-seco"), recibo)
        self.assertNotIn("/eva/solicitudRecusacion.do", self.posts())
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.tramite["cargado"]["Recusación"],
                         [["PACHECO", "Diego", "Coautor (2026)"], ["SANTELLA", "Agustín", "Coautor (2026)"]])

    def test_pip_seleccion_paginada_en_seco_no_hace_clic_y_al_guardar_tilda_todo(self):
        pedidos = ["9003", "9015", "9024"]  # uno por página
        sel = {"clave": "fin", "seccion": "Otras Fuentes de Financiamiento",
               "seleccion": {"campo": "otrosFinanciamientos", "valores": pedidos}}
        self.pip_preparar(self.datos(secciones=[sel]))
        codigo, recibo = self.pip_cargar()
        r = recibo["resultados"][0]
        self.assertEqual((codigo, r["resultado"]), (0, "en-seco"), recibo)
        self.assertIn("3 por tildar", " ".join(r["avisos"]))
        self.assertNotIn("/eva/solicitudOtrasFuentes.do", self.posts())  # cada clic guarda: en seco, ninguno
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (0, "guardado"), recibo)
        self.assertEqual(self.servidor.estado.tramite["financiamientos"], set(pedidos))

    def test_pip_seleccion_con_valor_inexistente_es_error(self):
        sel = {"clave": "fin", "seccion": "Otras Fuentes de Financiamiento",
               "seleccion": {"campo": "otrosFinanciamientos", "valores": ["9003", "1234"]}}
        self.pip_preparar(self.datos(secciones=[sel]))
        codigo, recibo = self.pip_cargar("--guardar")
        r = recibo["resultados"][0]
        self.assertEqual((codigo, r["resultado"]), (1, "error"), recibo)
        self.assertIn("1234", r["detalle"])
        # Se valida todo antes del primer clic: no queda nada guardado a medias.
        self.assertEqual(self.servidor.estado.tramite.get("financiamientos", set()), set())

    def test_pip_guardado_silencioso_se_informa_como_no_guardado(self):
        datos = self.datos()
        datos["secciones"] = [datos["secciones"][0]]
        datos["secciones"][0]["campos"]["tituloProyecto"] = "SILENCIO proyecto de prueba"
        self.pip_preparar(datos)
        codigo, recibo = self.pip_cargar("--guardar")
        self.assertEqual((codigo, recibo["resultados"][0]["resultado"]), (1, "no-guardado"), recibo)
        self.assertEqual(self.servidor.estado.tramite["estados"], {})

    def test_pip_seccion_sin_enlace_se_informa_y_no_corta_la_tanda(self):
        datos = self.datos()
        datos["secciones"].append({"clave": "investigadores", "seccion": "Investigadores declarados",
                                   "campos": {"x": "1"}})
        self.pip_preparar(datos)
        codigo, recibo = self.pip_cargar("--guardar")
        resultados = {r["clave"]: r["resultado"] for r in recibo["resultados"]}
        self.assertEqual(resultados["investigadores"], "error")
        self.assertIn("no ofrece enlace", recibo["resultados"][-1]["detalle"])
        self.assertEqual([r["resultado"] for r in recibo["resultados"]][:3], ["guardado"] * 3)

    def test_pip_enviar_exige_ok_y_confirmacion_explicita(self):
        self.pip_preparar(self.datos())
        self.pip_cargar("--guardar")
        # Sin confirmacion explicita: se niega aunque falten secciones.
        with self.assertRaises(SystemExit):
            self.correr("pip-enviar", "--headless", "--referencias", str(self.refs), "--pausa-ms", "0")
        # Con confirmacion pero con estados pendientes: no envia.
        codigo, r = self.correr("pip-enviar", "--confirmo-enviar", "--headless", "--referencias",
                                str(self.refs), "--pausa-ms", "0")
        self.assertEqual((codigo, r["enviado"]), (2, False), r)
        # Todo en Ok (como lo dejaria el equipo al completar el resto): recien ahi envia.
        for seccion in self.S.ESTADOS_PIP:
            self.servidor.estado.tramite["estados"].setdefault(seccion, "Ok")
        posts_antes = len(self.posts())
        codigo, r = self.correr("pip-enviar", "--confirmo-enviar", "--headless", "--referencias",
                                str(self.refs), "--pausa-ms", "0")
        self.assertEqual((codigo, r["enviado"], r["recibido"]), (0, True, True), r)
        self.assertTrue(any("solicitudEnviar" in p for p in self.posts()[posts_antes:]))

    def test_pip_verificar_detecta_cambios_del_modulo(self):
        codigo, informe = self.correr("pip-verificar", "--headless", "--referencias", str(self.refs),
                                      "--auto", "--pausa-ms", "0")
        self.assertEqual((codigo, informe["cambios"]), (0, []))
        base_antes = (self.refs / PIP.BASE_PIP).read_text(encoding="utf-8")
        self.servidor.estado.quitar_campo = "tituloProyecto"
        # Sin --auto: los cambios se informan y el codigo es 2 (el contrato del cargador, que no usa ese campo, sigue ok).
        codigo, informe = self.correr("pip-verificar", "--headless", "--referencias", str(self.refs),
                                      "--pausa-ms", "0")
        self.assertEqual(codigo, 2)
        self.assertGreater(informe["resumen"]["alto"], 0)
        self.assertEqual((self.refs / PIP.BASE_PIP).read_text(encoding="utf-8"), base_antes)
        # Con --auto: un cambio no critico se adopta (codigo 0) y la linea base se regenera.
        codigo, informe = self.correr("pip-verificar", "--headless", "--referencias", str(self.refs),
                                      "--auto", "--pausa-ms", "0")
        self.assertEqual(codigo, 0)
        self.assertGreater(informe["resumen"]["alto"], 0)
        self.assertNotEqual((self.refs / PIP.BASE_PIP).read_text(encoding="utf-8"), base_antes)
        self.assertIn("actualizada", (self.refs / "historial-cambios.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
