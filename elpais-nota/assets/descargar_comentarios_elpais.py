# -*- coding: utf-8 -*-
"""
descargar_comentarios_elpais.py
Descarga TODOS los comentarios Disqus de una nota de El Pais y los guarda
en JSON (fidelidad completa) y CSV (; separado, utf-8-sig para Excel).

Uso:
    python descargar_comentarios_elpais.py "https://elpais.com/ruta/nota.html"
    python descargar_comentarios_elpais.py "URL" --identificador JSFQ6OCCYFBNRDTCAGYOJSSJWI
    python descargar_comentarios_elpais.py "URL" --foro mi-foro --salida mi_carpeta

Como funciona (comentarios de El Pais = Disqus, foro "el-pais-1"):
    1. Consigue el identificador Disqus de la nota (data-disqus-identifier en el HTML).
       - Si el diario bloquea el HTTP directo (Datadome 403), intenta Wayback Machine.
       - Si tampoco hay, pide pasarlo a mano con --identificador:
         abri la nota en el navegador -> ver codigo fuente -> Ctrl+F "disqus-identifier".
    2. Extrae la API key publica de Disqus desde el bundle embedv2.js.
    3. Resuelve el identificador al ID numerico del thread (threads/details.json).
    4. Pagina todos los posts (threads/listPosts.json, 100 por pagina, orden ascendente).
    5. Escribe comentarios_elpais_{thread_id}.json y .csv en la carpeta de salida.

Solo usa la libreria estandar de Python 3.
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
API_BASE = "https://disqus.com/api/3.0"
EMBED_BUNDLE = "https://c.disquscdn.com/embedv2/latest/embedv2.js"
DISQUS_HEADERS = {
    "User-Agent": UA,
    "Referer": "https://disqus.com/embed/comments/",
    "Origin": "https://disqus.com",
    "Accept": "application/json",
}


def http_get(url, referer=None, timeout=30, retries=3):
    """GET con cabeceras de navegador. Devuelve (status, body)."""
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"GET fallo para {url}: {last_err}")


def disqus_api(endpoint, params):
    """Llama a la API publica de Disqus y devuelve el envelope completo.
    La key es de dominio disqus.com: exige Referer/Origin de disqus.com."""
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{API_BASE}/{endpoint}?{qs}", headers=DISQUS_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        envelope = json.loads(resp.read().decode("utf-8"))
    if envelope.get("code") != 0:
        raise RuntimeError(f"Disqus API {endpoint} -> code {envelope.get('code')}: {envelope.get('response')}")
    return envelope


def extraer_identificador(url_articulo, manual=None):
    """Devuelve (identificador, foro)."""
    if manual:
        return manual, None  # foro None -> usar default

    cuerpo = None
    # Intento 1: HTTP directo
    try:
        status, cuerpo = http_get(url_articulo)
        if status != 200:
            cuerpo = None
    except Exception:
        cuerpo = None

    # Intento 2: Wayback Machine (funciona para notas con tiempo en el archivo)
    if cuerpo is None:
        print("[i] El diario bloqueo el acceso directo (403). Probando Wayback Machine...")
        try:
            _, wb = http_get("http://archive.org/wayback/available?url="
                             + urllib.parse.quote(url_articulo, safe=""))
            snapshot = json.loads(wb).get("archived_snapshots", {}).get("closest", {})
            snap_url = snapshot.get("url")
            if snap_url:
                print(f"[i] Snapshot: {snap_url}")
                status, cuerpo = http_get(snap_url)
                if status != 200:
                    cuerpo = None
        except Exception:
            pass

    if cuerpo is None:
        return None, None

    ident = None
    m = re.search(r'data-disqus-identifier="([^"]+)"', cuerpo)
    if m:
        ident = m.group(1)
    foro = None
    m2 = re.search(r'([a-z0-9-]+)\.disqus\.com/(?:count-data|count|embed)\.js', cuerpo)
    if m2:
        foro = m2.group(1)
    return ident, foro


def extraer_api_key():
    """La key publica vive dentro del bundle del embed de Disqus."""
    _, js = http_get(EMBED_BUNDLE, referer="https://disqus.com/")
    m = re.search(r'API_KEY:"([A-Za-z0-9]+)"', js)
    if not m:
        raise RuntimeError("No encontre API_KEY en embedv2.js (cambio el formato del bundle?)")
    return m.group(1)


def limpiar_html(texto):
    if not texto:
        return ""
    t = re.sub(r"<br\s*/?>|</p>", "\n", texto)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).strip()


def main():
    ap = argparse.ArgumentParser(description="Descarga comentarios Disqus de una nota de El Pais")
    ap.add_argument("url", help="URL de la nota")
    ap.add_argument("--identificador", help="data-disqus-identifier a mano (si el diario bloquea el HTML)")
    ap.add_argument("--foro", default=None, help="Foro Disqus (default: el-pais-1, el de El Pais)")
    ap.add_argument("--salida", default=".", help="Carpeta de salida (default: .)")
    args = ap.parse_args()

    print(f"[1/5] Identificador Disqus para:\n      {args.url}")
    ident, foro_detectado = extraer_identificador(args.url, manual=args.identificador)
    foro = args.foro or foro_detectado or "el-pais-1"
    if not ident:
        print("[X] No pude obtener el identificador Disqus de la nota.")
        print("    Solucion: abri la nota en el navegador -> ver codigo fuente ->")
        print('    buscar "disqus-identifier" -> repeti el comando con:')
        print("    --identificador <valor>")
        sys.exit(2)
    print(f"      identificador = {ident}   foro = {foro}")

    print("[2/5] API key publica de Disqus...")
    api_key = extraer_api_key()
    print(f"      key = {api_key[:12]}...")

    print("[3/5] Resolviendo thread...")
    thread = disqus_api("threads/details.json", {
        "forum": foro, "thread": f"ident:{ident}", "api_key": api_key})["response"]
    thread_id = thread["id"]
    print(f"      thread_id = {thread_id}   titulo = {thread.get('clean_title', '')[:70]}")

    print("[4/5] Descargando comentarios (100 por pagina)...")
    comentarios, cursor, has_next = [], None, True
    while has_next:
        params = {"forum": foro, "thread": thread_id, "api_key": api_key,
                  "limit": 100, "order": "asc"}
        if cursor:
            params["cursor"] = cursor
        envelope = disqus_api("threads/listPosts.json", params)
        comentarios.extend(envelope["response"])
        cursor = envelope["cursor"].get("next")
        has_next = envelope["cursor"].get("hasNext", False)
        print(f"      ... {len(comentarios)} comentarios")
        if has_next:
            time.sleep(0.4)

    os.makedirs(args.salida, exist_ok=True)
    base = os.path.join(args.salida, f"comentarios_elpais_{thread_id}")

    print("[5/5] Escribiendo archivos...")
    meta = {"source_url": args.url, "forum": foro, "thread_id": thread_id,
            "thread_ident": ident, "comment_count": len(comentarios),
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "comments": comentarios}, f, ensure_ascii=False, indent=1)

    with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "fecha", "autor", "usuario", "anonimo", "likes", "dislikes",
                    "en_respuesta_a", "destacado", "borrado", "texto"])
        for c in comentarios:
            parent = c.get("parent")
            parent_id = parent.get("id") if isinstance(parent, dict) else (parent or "")
            a = c.get("author") or {}
            w.writerow([
                c.get("id"), c.get("createdAt"), a.get("name", ""), a.get("username", ""),
                bool(a.get("isAnonymous")), c.get("likes", 0), c.get("dislikes", 0),
                parent_id, c.get("isHighlighted", False), c.get("isDeleted", False),
                limpiar_html(c.get("message")),
            ])

    respuestas = sum(1 for c in comentarios if c.get("parent"))
    print("\nLISTO:")
    print(f"  {base}.json  ({os.path.getsize(base + '.json'):,} bytes)")
    print(f"  {base}.csv   ({os.path.getsize(base + '.csv'):,} bytes)")
    print(f"  {len(comentarios)} comentarios | {len(comentarios) - respuestas} raiz | {respuestas} respuestas")


if __name__ == "__main__":
    main()
