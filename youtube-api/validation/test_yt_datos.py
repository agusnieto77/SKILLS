"""Pruebas del cliente de YouTube sin red: funciones puras y cliente con sesion falsa.

Ejecutar:  python youtube-api/validation/test_yt_datos.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
import contextlib
import io
import json
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "assets"))

import yt_datos as Y  # noqa: E402

VIDEO_ID = "j3ZIM9UaXlE"

TIMEDTEXT_V3 = """<?xml version="1.0" encoding="utf-8" ?>
<timedtext format="3">
<head><ws id="0"/></head>
<body>
<p t="0" d="4841"><s ac="0">Hola</s><s t="321" ac="0"> mundo</s></p>
<p t="5000" d="2000"><s ac="0">Segundo</s></p>
</body>
</timedtext>"""

TIMEDTEXT_V1 = """<?xml version="1.0" encoding="utf-8" ?>
<timedtext format="1">
<body>
<text start="0" dur="2000">Hola mundo</text>
<text start="2500" dur="1500">Segundo</text>
</body>
</timedtext>"""


class TestExtraerIdVideo(unittest.TestCase):
    def test_desde_url_watch(self):
        self.assertEqual(
            Y.extraer_id_video(f"https://www.youtube.com/watch?v={VIDEO_ID}"), VIDEO_ID
        )

    def test_desde_url_watch_con_parametros(self):
        url = f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42s&list=PL123"
        self.assertEqual(Y.extraer_id_video(url), VIDEO_ID)

    def test_desde_url_short(self):
        self.assertEqual(Y.extraer_id_video(f"https://youtu.be/{VIDEO_ID}"), VIDEO_ID)

    def test_desde_url_shorts(self):
        self.assertEqual(Y.extraer_id_video(f"https://www.youtube.com/shorts/{VIDEO_ID}"), VIDEO_ID)

    def test_id_suelto(self):
        self.assertEqual(Y.extraer_id_video(VIDEO_ID), VIDEO_ID)

    def test_url_invalida(self):
        with self.assertRaises(Y.YouTubeError):
            Y.extraer_id_video("https://www.youtube.com/feed/trending")


class TestSegmentos(unittest.TestCase):
    def test_formato_3(self):
        segmentos = Y.segmentos_desde_timedtext(TIMEDTEXT_V3)
        self.assertEqual(len(segmentos), 2)
        self.assertAlmostEqual(segmentos[0]["inicio"], 0.0)
        self.assertAlmostEqual(segmentos[0]["duracion"], 4.841)
        self.assertEqual(segmentos[0]["texto"], "Hola mundo")
        self.assertAlmostEqual(segmentos[1]["inicio"], 5.0)

    def test_formato_1(self):
        segmentos = Y.segmentos_desde_timedtext(TIMEDTEXT_V1)
        self.assertEqual(len(segmentos), 2)
        self.assertAlmostEqual(segmentos[0]["inicio"], 0.0)
        self.assertEqual(segmentos[1]["texto"], "Segundo")

    def test_xml_corrupto(self):
        with self.assertRaises(Y.YouTubeError):
            Y.segmentos_desde_timedtext("<timedtext><p t='0'>sin cerrar")

    def test_xml_vacio_no_devuelve_segmentos(self):
        self.assertEqual(Y.segmentos_desde_timedtext("<timedtext format='3'></timedtext>"), [])


class TestComentarios(unittest.TestCase):
    def test_entidad_se_localiza_por_prefijo(self):
        entities = {"clave-corta": {"commentEntityPayload": {"properties": {"commentId": "x"}}}}
        self.assertIsNotNone(Y._coincidir_entidad(entities, "clave-corta-sufijo-largo"))
        self.assertIsNone(Y._coincidir_entidad(entities, "otra-clave"))

    def test_view_model_de_hilo_y_de_item(self):
        hilo = {"commentThreadRenderer": {"commentViewModel": {"commentViewModel": {"commentKey": "k1"}}}}
        item = {"commentViewModel": {"commentKey": "k2"}}
        self.assertEqual(Y._view_model(hilo)["commentKey"], "k1")
        self.assertEqual(Y._view_model(item)["commentKey"], "k2")
        self.assertIsNone(Y._view_model({"otro": 1}))

    def test_conteo_de_comentarios_desde_runs(self):
        cabecera = {"commentsCount": {"runs": [{"text": "229"}]}}
        self.assertEqual(Y._contar_comentarios(cabecera), 229)

    def test_conteo_de_comentarios_desde_texto(self):
        cabecera = {"countText": {"runs": [{"text": "1.234"}, {"text": " comentarios"}]}}
        self.assertEqual(Y._contar_comentarios(cabecera), 1234)

    def test_conteo_ausente(self):
        self.assertIsNone(Y._contar_comentarios({}))

    def test_conteo_prefiere_total_exacto_sobre_abreviado(self):
        cabecera = {
            "commentsCount": {"runs": [{"text": "2,4 M"}]},
            "countText": {"runs": [{"text": "2.460.280"}, {"text": " comentarios"}]},
        }
        self.assertEqual(Y._contar_comentarios(cabecera), 2460280)

    def test_conteo_abreviado_sin_total_exacto(self):
        for texto, esperado in (("2,4 M", 2_400_000), ("15 mil", 15_000), ("3.1K", 3_100), ("1,2 mill.", 1_200_000)):
            with self.subTest(texto=texto):
                self.assertEqual(Y._contar_comentarios({"commentsCount": {"simpleText": texto}}), esperado)

    def test_token_de_orden_por_indice(self):
        cabecera = {
            "sortMenu": {
                "sortFilterSubMenuRenderer": {
                    "subMenuItems": [
                        {"title": "Destacados", "serviceEndpoint": {"continuationCommand": {"token": "t-top"}}},
                        {"title": "Mas recientes", "serviceEndpoint": {"continuationCommand": {"token": "t-new"}}},
                    ]
                }
            }
        }
        self.assertEqual(Y._token_de_orden(cabecera, "top")["continuation"], "t-top")
        self.assertEqual(Y._token_de_orden(cabecera, "newest")["continuation"], "t-new")
        self.assertIsNone(Y._token_de_orden({}, "top"))

    def test_siguiente_consulta_desde_endpoint_directo(self):
        items = [
            {
                "continuationItemRenderer": {
                    "continuationEndpoint": {
                        "clickTrackingParams": "ctp",
                        "continuationCommand": {"token": "siguiente"},
                    }
                }
            }
        ]
        consulta = Y._siguiente_consulta(items)
        self.assertEqual(consulta["continuation"], "siguiente")
        self.assertEqual(consulta["clickTracking"]["clickTrackingParams"], "ctp")

    def test_siguiente_consulta_desde_boton_de_respuestas(self):
        items = [
            {
                "continuationItemRenderer": {
                    "button": {
                        "buttonRenderer": {
                            "command": {
                                "clickTrackingParams": "ctp2",
                                "continuationCommand": {"token": "mas-respuestas"},
                            }
                        }
                    }
                }
            }
        ]
        self.assertEqual(Y._siguiente_consulta(items)["continuation"], "mas-respuestas")

    def test_sin_continuacion_devuelve_none(self):
        self.assertIsNone(Y._siguiente_consulta([{"commentThreadRenderer": {}}]))


class TestPistasSubtitulo(unittest.TestCase):
    def test_prefiere_subtitulo_manual(self):
        lista = [
            {"languageCode": "es", "kind": "asr"},
            {"languageCode": "es", "kind": None},
        ]
        self.assertEqual(Y._elegir_pista(lista)["kind"], None)

    def test_prefiere_el_idioma_del_cliente_entre_automaticas(self):
        lista = [
            {"languageCode": "ar", "kind": "asr"},
            {"languageCode": "es", "kind": "asr"},
            {"languageCode": "en", "kind": "asr"},
        ]
        self.assertEqual(Y._elegir_pista(lista)["languageCode"], "es")

    def test_primera_pista_si_no_hay_preferencia(self):
        lista = [{"languageCode": "ar", "kind": "asr"}]
        self.assertEqual(Y._elegir_pista(lista)["languageCode"], "ar")


class TestMetadatos(unittest.TestCase):
    def test_normalizacion_desde_player(self):
        player = {
            "videoDetails": {
                "videoId": VIDEO_ID,
                "title": "Titulo",
                "author": "Canal",
                "channelId": "UC1",
                "viewCount": "100",
                "lengthSeconds": "604",
                "shortDescription": "Descripcion",
                "keywords": ["a", "b"],
            },
            "microformat": {
                "playerMicroformatRenderer": {
                    "category": "Tech",
                    "likeCount": "12",
                    "publishDate": "2026-10-21T07:02:25-07:00",
                }
            },
            "playabilityStatus": {"status": "OK"},
        }
        datos = Y.metadatos_desde_player(player)
        self.assertEqual(datos["titulo"], "Titulo")
        self.assertEqual(datos["vistas"], 100)
        self.assertEqual(datos["likes"], 12)
        self.assertEqual(datos["duracion_s"], 604)
        self.assertEqual(datos["categoria"], "Tech")
        self.assertEqual(datos["keywords"], ["a", "b"])
        self.assertFalse(datos["es_en_vivo"])
        self.assertEqual(datos["disponibilidad"], "OK")


class TestJsonEmpotrado(unittest.TestCase):
    def test_no_corta_en_llave_y_punto_y_coma_dentro_de_un_string(self):
        html = (
            '<script>var ytInitialPlayerResponse = {"videoDetails": {"title": "a};b", '
            '"videoId": "x"}};var otra = 1;</script>'
        )
        datos = Y.extraer_respuesta_player(html)
        self.assertEqual(datos["videoDetails"]["title"], "a};b")

    def test_asignacion_por_corchetes(self):
        html = '<script>window["ytInitialData"] = {"a": 1};</script>'
        self.assertEqual(Y.extraer_datos_iniciales(html), {"a": 1})

    def test_ausente_devuelve_none(self):
        self.assertIsNone(Y.extraer_respuesta_player("<html>sin datos</html>"))


class FakeRespuesta:
    def __init__(self, status=200, texto="", cuerpo=None, headers=None):
        self.status_code = status
        self.text = texto
        self.content = texto.encode("utf-8")
        self._cuerpo = cuerpo
        self.headers = headers or {}

    def json(self):
        return self._cuerpo


class FakeSesion:
    def __init__(self, gets=None, posts=None):
        self.headers = {}
        self.gets = list(gets or [])
        self.posts = list(posts or [])
        self.llamadas = []

    def get(self, url, timeout=None, **kwargs):
        self.llamadas.append(("GET", url))
        return self.gets.pop(0)

    def post(self, url, json=None, timeout=None):
        self.llamadas.append(("POST", url))
        return self.posts.pop(0)


class TestCliente(unittest.TestCase):
    def test_retry_after_con_fecha_http_no_rompe(self):
        respuesta = FakeRespuesta(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
        self.assertEqual(Y.ClienteYouTube._espera_429(respuesta), 10.0)
        self.assertEqual(Y.ClienteYouTube._espera_429(FakeRespuesta(429, headers={"Retry-After": "600"})), 30.0)

    def test_ficha_y_reproductor_se_piden_una_vez_por_video(self):
        html = (
            '"INNERTUBE_API_KEY":"clave123"'
            'var ytInitialPlayerResponse = {"videoDetails": {"videoId": "%s", "title": "T"}, '
            '"playabilityStatus": {"status": "OK"}};' % VIDEO_ID
        )
        player = {
            "playabilityStatus": {"status": "OK"},
            "captions": {"playerCaptionsTracklistRenderer": {"captionTracks": [
                {"languageCode": "es", "kind": "asr", "baseUrl": "https://www.youtube.com/api/timedtext?x=1"}
            ]}},
        }
        sesion = FakeSesion(
            gets=[FakeRespuesta(200, html), FakeRespuesta(200, TIMEDTEXT_V3), FakeRespuesta(200, TIMEDTEXT_V3)],
            posts=[FakeRespuesta(200, cuerpo=player)],
        )
        cliente = Y.ClienteYouTube(sesion=sesion, pausar=0)
        self.assertEqual(cliente.metadatos(VIDEO_ID)["titulo"], "T")
        self.assertEqual(len(cliente.transcripcion(VIDEO_ID)["segmentos"]), 2)
        self.assertEqual(len(cliente.pistas_subtitulo(VIDEO_ID)), 1)
        self.assertEqual(len(cliente.transcripcion(VIDEO_ID, "es")["segmentos"]), 2)
        fichas = [u for m, u in sesion.llamadas if m == "GET" and "/watch?" in u]
        reproductor = [u for m, u in sesion.llamadas if m == "POST" and "/player" in u]
        self.assertEqual(len(fichas), 1)
        self.assertEqual(len(reproductor), 1)


def pagina_comentarios(ids=(), siguiente=None, respuestas=None, cabecera=None):
    items = []
    mutaciones = []
    for cid in ids:
        vm = {"commentId": cid, "commentKey": cid}
        hilo = {"commentViewModel": {"commentViewModel": vm}}
        if respuestas and cid in respuestas:
            hilo["replies"] = {"commentRepliesRenderer": {"contents": [
                {"continuationItemRenderer": {"continuationEndpoint": {
                    "continuationCommand": {"token": respuestas[cid]}
                }}}
            ]}}
        items.append({"commentThreadRenderer": hilo})
        mutaciones.append({"entityKey": cid, "payload": {"commentEntityPayload": {
            "properties": {"commentId": cid, "content": {"content": f"Texto {cid}"}},
            "toolbar": {"replyCount": 2 if respuestas and cid in respuestas else 0},
        }}})
    if cabecera:
        items.insert(0, {"commentsHeaderRenderer": cabecera})
    if siguiente:
        items.append({"continuationItemRenderer": {"continuationEndpoint": {
            "continuationCommand": {"token": siguiente}
        }}})
    return {
        "onResponseReceivedEndpoints": [{"appendContinuationItemsAction": {"continuationItems": items}}],
        "frameworkUpdates": {"entityBatchUpdate": {"mutations": mutaciones}},
    }


def cliente_comentarios(posts):
    html = '"INNERTUBE_API_KEY":"clave" var ytInitialData = ' + json.dumps({
        "sectionIdentifier": "comment-item-section",
        "continuationCommand": {"token": "inicio"},
    }) + ";"
    sesion = FakeSesion(gets=[FakeRespuesta(texto=html)], posts=posts)
    return Y.ClienteYouTube(sesion=sesion, pausar=0), sesion


class TestCobertura(unittest.TestCase):
    def test_limite_filas_evitar_descarga_respuestas(self):
        cliente, sesion = cliente_comentarios([FakeRespuesta(cuerpo=pagina_comentarios(
            ["a", "b"], siguiente="otra", respuestas={"a": "ra", "b": "rb"}
        ))])
        datos = cliente.comentarios(VIDEO_ID, maximo=1, con_respuestas=True)
        self.assertEqual(datos["obtenidos"], 1)
        self.assertTrue(datos["parcial"])
        self.assertEqual(datos["motivo_fin"], "max_filas")
        self.assertEqual({h["comment_id"] for h in datos["hilos_no_expandidos"]}, {"a", "b"})
        self.assertEqual(len(sesion.llamadas), 2)

    def test_error_hilo_conserva_filas_y_continua_otro(self):
        cliente, _ = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a", "b"], respuestas={"a": "ra", "b": "rb"})),
            FakeRespuesta(503),
            FakeRespuesta(cuerpo=pagina_comentarios(["r1", "r2"])),
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(datos["obtenidos"], 4)
        self.assertTrue(datos["parcial"])
        self.assertEqual(datos["hilos_no_expandidos"][0]["comment_id"], "a")
        self.assertIn("503", datos["hilos_no_expandidos"][0]["error"])
        self.assertEqual(datos["presupuesto"]["peticiones_consumidas"], 3)

    def test_limite_paginas_incluye_cambio_orden(self):
        cabecera = {"sortMenu": {"sortFilterSubMenuRenderer": {"subMenuItems": [
            {}, {"continuationCommand": {"token": "newest"}}
        ]}}}
        cliente, _ = cliente_comentarios([FakeRespuesta(cuerpo=pagina_comentarios(cabecera=cabecera))])
        datos = cliente.comentarios(VIDEO_ID, max_paginas=1)
        self.assertEqual(datos["motivo_fin"], "max_paginas")
        self.assertEqual(datos["presupuesto"]["paginas_consumidas"], 1)

    def test_retry_cuenta_y_no_supera_presupuesto(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(429)])
        with patch.object(Y.time, "sleep"):
            datos = cliente.comentarios(VIDEO_ID, max_peticiones=1)
        self.assertEqual(datos["motivo_fin"], "max_peticiones")
        self.assertEqual(datos["presupuesto"]["peticiones_consumidas"], 1)

    def test_token_repetido_no_equivale_a_fin_normal(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(cuerpo=pagina_comentarios(["a"], siguiente="inicio"))])
        self.assertEqual(cliente.comentarios(VIDEO_ID)["motivo_fin"], "token_repetido")

    def test_fin_natural_no_promete_total_declarado(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(cuerpo=pagina_comentarios(
            ["a"], cabecera={"countText": {"simpleText": "5 comentarios"}}
        ))])
        datos = cliente.comentarios(VIDEO_ID)
        self.assertEqual(datos["motivo_fin"], "sin_continuacion")
        self.assertTrue(datos["parcial"])

    def test_error_pagina_conserva_resultado_parcial(self):
        cliente, _ = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], siguiente="otra")), FakeRespuesta(500)
        ])
        datos = cliente.comentarios(VIDEO_ID)
        self.assertEqual(datos["obtenidos"], 1)
        self.assertEqual(datos["motivo_fin"], "error_pagina")
        self.assertIn("500", datos["errores"][0])

    def test_respuestas_se_truncan_dentro_de_pagina(self):
        cliente, sesion = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], respuestas={"a": "ra"})),
            FakeRespuesta(cuerpo=pagina_comentarios(["r1", "r2", "r3"], siguiente="mas")),
        ])
        datos = cliente.comentarios(VIDEO_ID, maximo=2, con_respuestas=True)
        self.assertEqual(datos["obtenidos"], 2)
        self.assertEqual(datos["hilos_no_expandidos"][0]["motivo"], "max_filas")
        self.assertEqual(len(sesion.llamadas), 3)

    def test_limites_no_validos_no_hacen_red(self):
        for kwargs in ({"maximo": 0}, {"max_paginas": 61}, {"max_peticiones": 121}):
            with self.subTest(kwargs=kwargs), self.assertRaises(Y.YouTubeError):
                Y.ClienteYouTube(sesion=FakeSesion()).comentarios(VIDEO_ID, **kwargs)


    def test_tope_predeterminado_60_paginas(self):
        paginas = [FakeRespuesta(cuerpo=pagina_comentarios([f"c{i}"], siguiente=f"t{i}")) for i in range(60)]
        cliente, sesion = cliente_comentarios(paginas)
        datos = cliente.comentarios(VIDEO_ID)
        self.assertEqual(datos["motivo_fin"], "max_paginas")
        self.assertEqual(datos["presupuesto"]["paginas_consumidas"], 60)
        self.assertEqual(len(sesion.llamadas), 61)

    def test_presupuesto_compartido_con_respuestas(self):
        cliente, sesion = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], respuestas={"a": "ra"})),
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True, max_paginas=1)
        self.assertEqual(datos["hilos_no_expandidos"][0]["motivo"], "max_paginas")
        self.assertEqual(len(sesion.llamadas), 2)

    def test_respuesta_parcial_y_error_en_segunda_pagina(self):
        cliente, _ = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], respuestas={"a": "ra"})),
            FakeRespuesta(cuerpo=pagina_comentarios(["r1"], siguiente="otra")),
            FakeRespuesta(500),
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(datos["obtenidos"], 2)
        hilo = datos["hilos_no_expandidos"][0]
        self.assertEqual(hilo["respuestas_obtenidas"], 1)
        self.assertEqual(hilo["motivo"], "error_hilo")

    def test_respuestas_deduplicadas_y_token_repetido(self):
        cliente, _ = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], respuestas={"a": "ra"})),
            FakeRespuesta(cuerpo=pagina_comentarios(["r1", "r1"], siguiente="ra")),
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(datos["obtenidos"], 2)
        self.assertEqual(datos["hilos_no_expandidos"][0]["motivo"], "token_repetido")

    def test_retry_exitoso_cuenta_dos_intentos_y_una_pagina(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(429), FakeRespuesta(cuerpo=pagina_comentarios(["a"]))])
        with patch.object(Y.time, "sleep"):
            datos = cliente.comentarios(VIDEO_ID)
        self.assertEqual(datos["presupuesto"]["peticiones_consumidas"], 2)
        self.assertEqual(datos["presupuesto"]["paginas_consumidas"], 1)
        self.assertFalse(datos["parcial"])

    def test_hilos_no_solicitados_y_respuestas_menores_declaradas(self):
        pagina = pagina_comentarios(["a"], respuestas={"a": "ra"})
        cliente, _ = cliente_comentarios([FakeRespuesta(cuerpo=pagina)])
        self.assertEqual(cliente.comentarios(VIDEO_ID)["hilos_no_expandidos"][0]["motivo"], "no_solicitadas")
        cliente, _ = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina), FakeRespuesta(cuerpo=pagina_comentarios(["r1"]))
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(datos["hilos_no_expandidos"][0]["motivo"], "menos_respuestas_declaradas")

    def test_bloqueo_pagina_no_expande_hilos(self):
        cliente, sesion = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], siguiente="otra", respuestas={"a": "ra"})),
            FakeRespuesta(429), FakeRespuesta(429),
        ])
        with patch.object(Y.time, "sleep"):
            datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(len(sesion.llamadas), 4)
        self.assertEqual(datos["bloqueo"], "http_429")
        self.assertEqual(datos["hilos_no_expandidos"][0]["motivo"], "bloqueo")

    def test_bloqueo_hilo_no_intenta_otro(self):
        cliente, sesion = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a", "b"], respuestas={"a": "ra", "b": "rb"})),
            FakeRespuesta(429), FakeRespuesta(429),
        ])
        with patch.object(Y.time, "sleep"):
            datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(len(sesion.llamadas), 4)
        self.assertEqual(datos["bloqueo"], "http_429")
        self.assertEqual(datos["hilos_no_expandidos"][1]["motivo"], "bloqueo")

    def test_pagina_invalida_consume_peticion_no_pagina(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(cuerpo={"error": {"code": 500}})])
        datos = cliente.comentarios(VIDEO_ID)
        self.assertEqual(datos["presupuesto"]["peticiones_consumidas"], 1)
        self.assertEqual(datos["presupuesto"]["paginas_consumidas"], 0)

    def test_429_sin_presupuesto_de_reintento_detiene_cliente(self):
        cliente, _ = cliente_comentarios([FakeRespuesta(429)])
        datos = cliente.comentarios(VIDEO_ID, max_peticiones=1)
        self.assertEqual(datos["motivo_fin"], "max_peticiones")
        self.assertEqual(datos["bloqueo"], "http_429")
        self.assertTrue(datos["errores"])

    def test_login_required_en_next_no_expande_hilos(self):
        cliente, sesion = cliente_comentarios([
            FakeRespuesta(cuerpo=pagina_comentarios(["a"], siguiente="otra", respuestas={"a": "ra"})),
            FakeRespuesta(cuerpo={"playabilityStatus": {"status": "LOGIN_REQUIRED"}}),
        ])
        datos = cliente.comentarios(VIDEO_ID, con_respuestas=True)
        self.assertEqual(len(sesion.llamadas), 3)
        self.assertEqual(datos["bloqueo"], "login_required")


class TestIdiomasNuevos(unittest.TestCase):
    def test_preferencias_ordenadas_y_tipo(self):
        pistas = [
            {"languageCode": "en", "kind": None},
            {"languageCode": "es", "kind": "asr"},
            {"languageCode": "es", "kind": None},
        ]
        self.assertEqual(Y._elegir_pista(pistas, ["fr", "es", "en"], "asr"), pistas[1])
        self.assertEqual(Y._elegir_pista(pistas, ["es", "en"]), pistas[2])
        with self.assertRaises(Y.YouTubeError):
            Y._elegir_pista(pistas, ["fr"], "manual")

    def cliente(self, traducible=True):
        base = "https://www.youtube.com/api/timedtext?lang=en&sig=a%2Bb&tlang=fr"
        pista = {"languageCode": "en", "baseUrl": base, "isTranslatable": traducible}
        cliente = Y.ClienteYouTube(sesion=FakeSesion(gets=[FakeRespuesta(texto=TIMEDTEXT_V3)]), pausar=0)
        cliente._html[VIDEO_ID] = '"INNERTUBE_API_KEY":"clave"'
        cliente._player[VIDEO_ID] = {"captions": {"playerCaptionsTracklistRenderer": {"captionTracks": [pista]}}}
        return cliente

    def test_traduccion_conserva_firma_y_declara_metodo(self):
        cliente = self.cliente()
        datos = cliente.transcripcion(VIDEO_ID, ["en"], tlang="es")
        self.assertEqual(cliente.sesion.llamadas[0][1],
                         "https://www.youtube.com/api/timedtext?lang=en&sig=a%2Bb&tlang=es")
        self.assertTrue(datos["traducida"])
        self.assertEqual((datos["idioma_fuente"], datos["idioma_destino"]), ("en", "es"))
        self.assertEqual(datos["metodo_traduccion"], "traduccion_automatica_youtube_tlang")
        self.assertFalse(datos["traduccion_verificada"])
        self.assertEqual(datos["idioma"], "en")

    def test_pista_no_traducible_no_hace_red(self):
        cliente = self.cliente(False)
        with self.assertRaises(Y.YouTubeError):
            cliente.transcripcion(VIDEO_ID, tlang="es")
        self.assertEqual(cliente.sesion.llamadas, [])

    def test_original_declarada_sin_traduccion(self):
        datos = self.cliente().transcripcion(VIDEO_ID)
        self.assertFalse(datos["traducida"])
        self.assertEqual(datos["idioma_fuente"], "en")


    def test_traduccion_vacia_o_http_error_no_devuelve_original(self):
        for respuesta in (FakeRespuesta(texto=""), FakeRespuesta(403), FakeRespuesta(texto="<timedtext/>")):
            cliente = self.cliente()
            cliente.sesion.gets = [respuesta]
            with self.subTest(status=respuesta.status_code), self.assertRaises(Y.YouTubeError):
                cliente.transcripcion(VIDEO_ID, tlang="es")
            self.assertEqual(len(cliente.sesion.llamadas), 1)

    def test_tlang_no_valido_antes_de_red(self):
        cliente = self.cliente()
        with self.assertRaises(Y.YouTubeError):
            cliente.transcripcion(VIDEO_ID, tlang="es&sig=otro")
        self.assertEqual(cliente.sesion.llamadas, [])


class TestLotesCLI(unittest.TestCase):
    def ejecutar(self, argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return Y.main(argv)

    def test_archivo_y_urls_con_error_independiente(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ids = Path(carpeta) / "ids.txt"
            ids.write_text("# inventario\nno-valido\nabcdefghijk\n", encoding="utf-8")
            with patch.object(Y.ClienteYouTube, "metadatos", return_value={"titulo": "T"}) as meta:
                codigo = self.ejecutar(["metadatos", "--url", VIDEO_ID, "--archivo-ids", str(ids), "--out", carpeta])
            datos = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
            self.assertEqual(codigo, 1)
            self.assertEqual(meta.call_count, 2)
            self.assertEqual([r["ok"] for r in datos["resultados"]], [True, False, True])
            self.assertIn("resultado", datos["resultados"][0])
            self.assertIn("error", datos["resultados"][1])

    def test_error_red_no_aborta_lote(self):
        with tempfile.TemporaryDirectory() as carpeta, patch.object(
            Y.ClienteYouTube, "metadatos",
            side_effect=[Y.requests.ConnectionError("sin red"), {"titulo": "T"}]
        ):
            codigo = self.ejecutar(["metadatos", "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])
            datos = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
            self.assertEqual(codigo, 1)
            self.assertEqual([r["ok"] for r in datos["resultados"]], [False, True])

    def test_lote_superior_a_50_se_rechaza_antes_de_red(self):
        with patch.object(Y.ClienteYouTube, "metadatos") as meta:
            self.assertEqual(self.ejecutar(["metadatos", "--url", *([VIDEO_ID] * 51)]), 2)
            meta.assert_not_called()

    def test_cli_pistas_y_opciones_idioma(self):
        with tempfile.TemporaryDirectory() as carpeta, patch.object(
            Y.ClienteYouTube, "pistas_subtitulo", return_value=[{"idioma": "es", "automatica": True}]
        ):
            self.assertEqual(self.ejecutar(["pistas", "--url", VIDEO_ID, "--out", carpeta]), 0)
            self.assertTrue((Path(carpeta) / f"{VIDEO_ID}_pistas.json").exists())
        with tempfile.TemporaryDirectory() as carpeta, patch.object(
            Y.ClienteYouTube, "transcripcion", return_value={"segmentos": [], "idioma": "es", "automatica": False}
        ) as tr:
            self.assertEqual(self.ejecutar([
                "transcripcion", "--url", VIDEO_ID, "--lang", "en,fr", "--lang", "es",
                "--tipo-subtitulo", "manual", "--tlang", "es", "--out", carpeta,
            ]), 0)
            tr.assert_called_once_with(VIDEO_ID, ["en", "fr", "es"], tipo="manual", tlang="es")


    def test_archivo_solo_y_limite_exacto_50(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "ids.txt"
            archivo.write_text("\n".join([VIDEO_ID] * 50), encoding="utf-8-sig")
            with patch.object(Y.ClienteYouTube, "metadatos", return_value={"titulo": "T"}) as meta, patch.object(Y.time, "sleep"):
                codigo = self.ejecutar(["metadatos", "--archivo-ids", str(archivo), "--out", carpeta])
            recibo = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
            self.assertEqual(codigo, 0)
            self.assertEqual(meta.call_count, 50)
            self.assertEqual(recibo["total"], 50)

    def test_todo_aisla_error_de_cada_operacion(self):
        with tempfile.TemporaryDirectory() as carpeta, patch.object(
            Y.ClienteYouTube, "metadatos", side_effect=Y.YouTubeError("no metadatos")
        ), patch.object(
            Y.ClienteYouTube, "transcripcion", side_effect=Y.requests.ConnectionError("sin red")
        ), patch.object(Y.ClienteYouTube, "comentarios", return_value={"comentarios": [], "obtenidos": 0}) as com:
            codigo = self.ejecutar(["todo", "--url", VIDEO_ID, "--max-paginas", "2", "--out", carpeta])
            self.assertEqual(codigo, 1)
            self.assertTrue((Path(carpeta) / f"{VIDEO_ID}_comentarios.json").exists())
            com.assert_called_once_with(
                VIDEO_ID, maximo=200, con_respuestas=False, orden="newest", max_paginas=2, max_peticiones=120
            )

    def test_archivo_inexistente_y_limites_invalidos_no_hacen_red(self):
        with patch.object(Y.ClienteYouTube, "pagina_watch") as ficha:
            self.assertEqual(self.ejecutar(["metadatos", "--archivo-ids", "no-existe/ids.txt"]), 2)
            self.assertEqual(self.ejecutar(["comentarios", "--url", VIDEO_ID, "--max", "0"]), 2)
            ficha.assert_not_called()

    def test_429_agotado_detiene_lote_y_todo(self):
        for comando in ("metadatos", "todo"):
            with self.subTest(comando=comando), tempfile.TemporaryDirectory() as carpeta:
                sesion = FakeSesion(gets=[FakeRespuesta(429), FakeRespuesta(429)])
                cliente = Y.ClienteYouTube(sesion=sesion, pausar=0)
                with patch.object(Y, "ClienteYouTube", return_value=cliente), patch.object(Y.time, "sleep"):
                    codigo = self.ejecutar([comando, "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])
                recibo = json.loads((Path(carpeta) / f"lote_{comando}.json").read_text(encoding="utf-8"))
                self.assertEqual(codigo, 1)
                self.assertEqual(len(sesion.llamadas), 2)
                pendiente = recibo["resultados"][1]
                self.assertEqual((pendiente["estado"], pendiente["motivo"]), ("no_procesado", "http_429"))
                self.assertEqual(recibo["resultados"][0]["estado"], "procesado")
                if comando == "todo":
                    self.assertEqual(recibo["resultados"][0]["resultado"]["transcripcion"]["estado"], "no_procesado")

    def test_login_required_detiene_desde_watch_y_player(self):
        bloqueado = {"playabilityStatus": {"status": "LOGIN_REQUIRED", "reason": "Sign in to confirm you're not a bot"}}
        for comando in ("metadatos", "pistas"):
            with self.subTest(comando=comando), tempfile.TemporaryDirectory() as carpeta:
                html = '"INNERTUBE_API_KEY":"clave"'
                if comando == "metadatos":
                    html += " var ytInitialPlayerResponse = " + json.dumps(bloqueado) + ";"
                sesion = FakeSesion(gets=[FakeRespuesta(texto=html)], posts=[FakeRespuesta(cuerpo=bloqueado)])
                cliente = Y.ClienteYouTube(sesion=sesion, pausar=0)
                with patch.object(Y, "ClienteYouTube", return_value=cliente), patch.object(Y.time, "sleep"):
                    codigo = self.ejecutar([comando, "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])
                recibo = json.loads((Path(carpeta) / f"lote_{comando}.json").read_text(encoding="utf-8"))
                self.assertEqual(codigo, 1)
                self.assertEqual(len(sesion.llamadas), 1 if comando == "metadatos" else 2)
                self.assertEqual(recibo["resultados"][1]["motivo"], "login_required")

    def test_429_comentarios_detiene_siguiente_video(self):
        cliente, sesion = cliente_comentarios([FakeRespuesta(429), FakeRespuesta(429)])
        with tempfile.TemporaryDirectory() as carpeta, patch.object(
            Y, "ClienteYouTube", return_value=cliente
        ), patch.object(Y.time, "sleep"):
            codigo = self.ejecutar(["comentarios", "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])
            recibo = json.loads((Path(carpeta) / "lote_comentarios.json").read_text(encoding="utf-8"))
        self.assertEqual(codigo, 1)
        self.assertEqual(len(sesion.llamadas), 3)
        self.assertEqual(recibo["resultados"][1]["motivo"], "http_429")

    def test_recibo_conserva_entrada_antes_de_interrupcion(self):
        for fallo in (KeyboardInterrupt(), TypeError("forma inesperada")):
            with self.subTest(fallo=type(fallo).__name__), tempfile.TemporaryDirectory() as carpeta:
                with patch.object(Y.ClienteYouTube, "metadatos", side_effect=fallo), patch.object(Y.time, "sleep"):
                    with self.assertRaises(type(fallo)):
                        self.ejecutar(["metadatos", "--url", "invalido", VIDEO_ID, "--out", carpeta])
                recibo = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
                self.assertEqual(recibo["resultados"][0]["estado"], "procesado")
                self.assertIn("error", recibo["resultados"][0])
                self.assertEqual(recibo["resultados"][1]["estado"], "no_procesado")

    def test_recibo_actualizado_antes_de_siguiente_video(self):
        with tempfile.TemporaryDirectory() as carpeta:
            def metadatos(video_id):
                if video_id != VIDEO_ID:
                    recibo = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
                    self.assertEqual(recibo["exitosos"], 1)
                    self.assertEqual(recibo["resultados"][0]["resultado"]["titulo"], "T")
                    raise KeyboardInterrupt()
                return {"titulo": "T"}
            with patch.object(Y.ClienteYouTube, "metadatos", side_effect=metadatos), patch.object(Y.time, "sleep"):
                with self.assertRaises(KeyboardInterrupt):
                    self.ejecutar(["metadatos", "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])

    def test_error_red_paginacion_salida_3_con_parcial(self):
        for en_hilo in (False, True):
            pagina = pagina_comentarios(
                ["a"], siguiente=None if en_hilo else "otra", respuestas={"a": "ra"} if en_hilo else None
            )
            cliente, sesion = cliente_comentarios([FakeRespuesta(cuerpo=pagina)])
            post = sesion.post
            def solicitar(*args, sesion=sesion, post=post, **kwargs):
                if sesion.posts:
                    return post(*args, **kwargs)
                raise Y.requests.ConnectionError("sin red")
            with self.subTest(en_hilo=en_hilo), tempfile.TemporaryDirectory() as carpeta, patch.object(
                Y, "ClienteYouTube", return_value=cliente
            ), patch.object(sesion, "post", side_effect=solicitar):
                codigo = self.ejecutar(["comentarios", "--url", VIDEO_ID, "--con-respuestas", "--out", carpeta])
                datos = json.loads((Path(carpeta) / f"{VIDEO_ID}_comentarios.json").read_text(encoding="utf-8"))
                self.assertEqual(codigo, 3)
                self.assertEqual(datos["obtenidos"], 1)
                self.assertTrue(datos["error_red"])

    def test_error_red_watch_salida_3(self):
        with patch.object(Y.ClienteYouTube, "pagina_watch", side_effect=Y.requests.ConnectionError("sin red")):
            self.assertEqual(self.ejecutar(["metadatos", "--url", VIDEO_ID]), 3)

    def test_todo_aisla_oserror_y_fallo_del_json_de_error(self):
        for formato in ("json", "csv"):
            with self.subTest(formato=formato), tempfile.TemporaryDirectory() as carpeta:
                escribir_json = Y._escribir_json
                def escribir(ruta, datos, formato=formato, escribir_json=escribir_json):
                    if formato == "json" and ruta.name.endswith("_transcripcion.json"):
                        raise OSError("sin permiso")
                    escribir_json(ruta, datos)
                with patch.object(Y, "_escribir_json", side_effect=escribir), patch.object(
                    Y, "_escribir_csv", side_effect=OSError("disco lleno") if formato == "csv" else None
                ), patch.object(Y.ClienteYouTube, "metadatos", return_value={"titulo": "T"}), patch.object(
                    Y.ClienteYouTube, "transcripcion", return_value={"segmentos": []}
                ), patch.object(Y.ClienteYouTube, "comentarios", return_value={"comentarios": []}):
                    codigo = self.ejecutar(["todo", "--url", VIDEO_ID, "abcdefghijk", "--out", carpeta])
                recibo = json.loads((Path(carpeta) / "lote_todo.json").read_text(encoding="utf-8"))
                resultado = recibo["resultados"][0]["resultado"]
                self.assertEqual(codigo, 1)
                self.assertEqual(resultado["metadatos"]["titulo"], "T")
                self.assertIn("error", resultado["transcripcion"])
                self.assertIn("comentarios", resultado)
                if formato == "json":
                    self.assertIn("error_escritura", resultado["transcripcion"])

    def test_recibo_previo_sobrevive_interrupcion_al_reemplazar(self):
        with tempfile.TemporaryDirectory() as carpeta:
            reemplazar = Path.replace
            llamadas = 0
            def interrumpir(ruta, destino):
                nonlocal llamadas
                llamadas += 1
                if llamadas == 3:
                    raise KeyboardInterrupt()
                return reemplazar(ruta, destino)
            with patch.object(Path, "replace", autospec=True, side_effect=interrumpir), patch.object(
                Y.ClienteYouTube, "metadatos", return_value={"titulo": "T"}
            ), patch.object(Y.time, "sleep"):
                with self.assertRaises(KeyboardInterrupt):
                    self.ejecutar(["metadatos", "--url", "invalido", VIDEO_ID, "--out", carpeta])
            recibo = json.loads((Path(carpeta) / "lote_metadatos.json").read_text(encoding="utf-8"))
            self.assertEqual(recibo["resultados"][0]["estado"], "procesado")
            self.assertEqual(recibo["resultados"][1]["estado"], "no_procesado")


if __name__ == "__main__":
    unittest.main(verbosity=2)
