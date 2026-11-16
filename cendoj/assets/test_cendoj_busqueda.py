# -*- coding: utf-8 -*-
"""Tests offline de cendoj_busqueda (fixtures locales, sesion HTTP falsa)."""
import os
import unittest

import cendoj_busqueda as cb

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "busqueda_huelga_p10.html")


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages):
        self.pages = pages
        self.posts = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.posts.append(dict(data or {}))
        idx = min(len(self.posts) - 1, len(self.pages) - 1)
        return FakeResponse(self.pages[idx])


class TestParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIX, encoding="utf-8") as f:
            cls.html = f.read()
        cls.docs = cb.parse_search_html(cls.html)

    def test_bloques(self):
        self.assertEqual(len(self.docs), 10)

    def test_primer_doc(self):
        d = self.docs[0]
        self.assertEqual(d["reference"], "11923807")
        self.assertTrue(d["documento_data_link"].startswith(
            "https://www.poderjudicial.es/search/AN/openDocument/"))
        self.assertIn("SAP VI 1532/2026", d["titulo"])
        self.assertEqual(d["ECLI"], "ECLI:ES:APVI:2026:1532")
        self.assertEqual(d["ROJ"], "SAP VI 1532/2026")

    def test_todos_con_documento(self):
        sin = [d for d in self.docs if not d["documento_data_link"]]
        self.assertEqual(sin, [])

    def test_resumen_no_html(self):
        con = [d for d in self.docs if d["resumen"]]
        self.assertTrue(con)
        for d in con:
            self.assertNotIn("<", d["resumen"])

    def test_dedup(self):
        dobles = self.docs + self.docs
        self.assertEqual(len(cb.dedup(dobles)), len(self.docs))

    def test_params(self):
        p = cb.build_query_params("huelga", 51, 50)
        self.assertEqual(p, {"action": "query", "TEXT": "huelga",
                             "databasematch": "AN",
                             "sort": "IN_FECHARESOLUCION:decreasing",
                             "recordsPerPage": "50", "start": "51",
                             "page": "1", "maxresults": "200"})

    def test_paginacion_optima(self):
        with open(FIX, encoding="utf-8") as f:
            page = f.read()
        fake = FakeSession([page] * 4)
        docs, snaps = cb.fetch_all("huelga", 50, fake, sleep=0)
        self.assertEqual([p["start"] for p in fake.posts], ["1", "51", "101", "151"])
        self.assertEqual(len(snaps), 4)
        self.assertEqual(len(docs), 10)  # 4 paginas identicas -> dedup a 10


if __name__ == "__main__":
    unittest.main()
