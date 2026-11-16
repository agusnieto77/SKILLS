# -*- coding: utf-8 -*-
"""Busqueda en el CENDOJ (poderjudicial.es/search) con el enfoque optimo.

Recupera hasta el tope del visor (200 documentos) con paginas de 50
(start=1,51,101,151) en vez de 20x10, y guarda metadatos + data-link.
Requiere: pip install -r requirements.txt (curl_cffi con TLS tipo Chrome;
urllib directo devuelve 403).
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import html as ihtml

BASE = "https://www.poderjudicial.es/search/"
TOTAL_CAP = 200
PAGE_SIZES = (10, 20, 30, 50)


def build_query_params(texto, start, records):
    """Parametros del POST a search.action (form frmBusquedajurisprudencia)."""
    return {
        "action": "query",
        "TEXT": texto,
        "databasematch": "AN",
        "sort": "IN_FECHARESOLUCION:decreasing",
        "recordsPerPage": str(records),
        "start": str(start),
        "page": "1",
        "maxresults": str(TOTAL_CAP),
    }


def clean(t):
    """Quita tags HTML y colapsa espacios."""
    return re.sub(r"\s+", " ", ihtml.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def parse_search_html(html):
    """Extrae un doc por cada bloque div.searchresult.doc.

    documento = atributo data-link (URL openDocument), no el titulo.
    """
    docs = []
    for b in re.split(r'<div class="row searchresult doc"', html)[1:]:
        b = '<div class="row searchresult doc' + b
        ref = re.search(r'data-ref="(\d+)"', b)
        dl = re.search(r'data-link="(https://[^"]+)"', b)
        tit = re.search(r'id="ref-\d+"[^>]*>([^<]+)</a>', b)
        ecli = re.search(r"(ECLI:[^<\s]+)", b)
        meta = re.search(r'<div class="metadatos">(.*?)</div>', b, re.S)
        summ = re.search(r'<div class="summary".*?>(.*?)</div>', b, re.S)
        titulo = ihtml.unescape(tit.group(1).strip()) if tit else ""
        roj = ""
        mroj = re.search(r"ROJ:\s*(.+)$", titulo)
        if mroj:
            roj = clean(mroj.group(1))
        fields = {"municipio": "", "ponente": "", "resolucion": "", "recurso": ""}
        if meta:
            for li in re.findall(r"<li>(.*?)</li>", meta.group(1), re.S):
                txt = clean(li)
                if ":" in txt:
                    k, v = txt.split(":", 1)
                    v = v.strip()
                    if "Municipio" in k:
                        fields["municipio"] = v
                    elif "Ponente" in k:
                        fields["ponente"] = v
                    elif "Resoluci" in k:
                        fields["resolucion"] = v
                    elif "Recurso" in k:
                        fields["recurso"] = v
        docs.append({
            "reference": ref.group(1) if ref else "",
            "documento_data_link": dl.group(1) if dl else "",
            "titulo": titulo,
            "ROJ": roj,
            "ECLI": ecli.group(1) if ecli else "",
            "metadatos": clean(meta.group(1)) if meta else "",
            "resumen": clean(summ.group(1)) if summ else "",
            **fields,
        })
    return docs


def dedup(docs):
    """Dedup por reference manteniendo el orden."""
    seen, uniq = set(), []
    for d in docs:
        if d["reference"] not in seen:
            seen.add(d["reference"])
            uniq.append(d)
    return uniq


def fetch_all(texto, records, session, sleep=0.5):
    """4 paginas (1, 1+R, 1+2R, 1+3R). Devuelve (docs, snapshots_html)."""
    docs, snapshots = [], []
    for start in (1, 1 + records, 1 + 2 * records, 1 + 3 * records):
        params = build_query_params(texto, start, records)
        resp = session.post(BASE + "search.action", data=params, headers={
            "Referer": BASE + "indexAN.jsp",
            "Origin": "https://www.poderjudicial.es",
            "X-Requested-With": "XMLHttpRequest"}, timeout=30)
        resp.raise_for_status()
        snapshots.append(resp.text)
        docs.extend(parse_search_html(resp.text))
        time.sleep(sleep)
    return dedup(docs), snapshots


def main(argv=None):
    ap = argparse.ArgumentParser(description="Busca en el CENDOJ y guarda metadatos + data-link.")
    ap.add_argument("--texto", required=True, help="Texto libre (input frmBusquedajurisprudencia_TEXT)")
    ap.add_argument("--salida", default="./datos", help="Carpeta de salida")
    ap.add_argument("--registros", type=int, choices=PAGE_SIZES, default=50,
                    help="Resultados por pagina (50 = tope 200 en 4 peticiones)")
    args = ap.parse_args(argv)

    from curl_cffi import requests as cr
    session = cr.Session(impersonate="chrome131")
    session.get(BASE + "indexAN.jsp", timeout=30)

    docs, snapshots = fetch_all(args.texto, args.registros, session)
    os.makedirs(args.salida, exist_ok=True)
    for i, snap in enumerate(snapshots, 1):
        with open(os.path.join(args.salida, f"snapshot_pag_{i}.html"), "w", encoding="utf-8") as f:
            f.write(snap)
    cols = ["reference", "documento_data_link", "titulo", "ROJ", "ECLI",
            "municipio", "ponente", "resolucion", "recurso", "resumen"]
    with open(os.path.join(args.salida, "cendoj_resultados.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows([{k: d.get(k, "") for k in cols} for d in docs])
    with open(os.path.join(args.salida, "cendoj_resultados.json"), "w", encoding="utf-8") as f:
        json.dump({"texto": args.texto, "recuperados": len(docs),
                   "tope_visor": TOTAL_CAP, "docs": docs}, f, ensure_ascii=False, indent=1)
    print(f"recuperados: {len(docs)} -> {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
