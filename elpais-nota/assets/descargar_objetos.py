# -*- coding: utf-8 -*-
"""
descargar_objetos.py
Descarga todos los objetos digitales de una nota digital (imagenes, audio,
video directo, PDF) con un manifiesto de metadatos por archivo.

Entrada:
    - El nota.html que produjo descargar_nota.py, o
    - La URL de la nota (usa la misma cadena directo -> Wayback -> error).

Uso:
    python descargar_objetos.py carpeta\\nota.html
    python descargar_objetos.py "https://..." --salida carpeta

Salida:
    objetos/objetos.csv    (manifiesto ; separado, utf-8-sig)
    objetos/objetos.json   (mismo manifiesto + resumen)
    objetos/NNN_sha8.ext   (archivos con nombre estable por hash)

Reglas honestas:
    - Solo archivos directos (image/*, video/*, audio/*, application/pdf).
    - Streams HLS/DASH (.m3u8/.mpd) se registran como 'stream-no-descargable'
      porque no son un archivo unico (requieren ffmpeg).
    - Tamano maximo por archivo: --tamano-max MB (default 60).

Solo libreria estandar de Python 3.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from descargar_nota import NotaParser, conseguir_html

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

TIPOS_MEDIA = ("image/", "video/", "audio/", "application/pdf")

EXT_POR_TIPO = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/avif": ".avif", "image/svg+xml": ".svg",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
    "audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/ogg": ".ogg",
    "audio/wav": ".wav", "application/pdf": ".pdf",
}


def descargar_objeto(url, referer, tope_bytes):
    """Descarga un objeto. Devuelve (item, data) donde data son los bytes
    si estado == 'ok', o None en cualquier otro caso."""
    item = {"url": url, "archivo": None, "sha256": None, "bytes": None,
            "content_type": None, "last_modified": None, "estado": None}
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Referer": referer, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            item["content_type"] = ctype
            item["last_modified"] = resp.headers.get("Last-Modified")

            path_limpio = urllib.parse.urlparse(url).path.lower()
            if (ctype == "application/vnd.apple.mpegurl"
                    or path_limpio.endswith((".m3u8", ".mpd"))):
                item["estado"] = "stream-no-descargable"
                return item, None
            if not ctype.startswith(TIPOS_MEDIA) and ctype != "application/octet-stream":
                item["estado"] = f"no-es-media ({ctype or 'sin-tipo'})"
                return item, None

            data = b""
            while True:
                bloque = resp.read(1 << 16)
                if not bloque:
                    break
                data += bloque
                if len(data) > tope_bytes:
                    item["estado"] = "supera-tamano-max"
                    return item, None

        item["bytes"] = len(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
        item["estado"] = "ok"
        return item, data
    except Exception as e:
        item["estado"] = f"error: {str(e)[:80]}"
        return item, None


def extension_para(url, ctype):
    ext = EXT_POR_TIPO.get(ctype)
    if ext:
        return ext
    path_ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if re.fullmatch(r"\.[a-z0-9]{1,5}", path_ext):
        return path_ext
    return ".bin" if ctype == "application/octet-stream" else ""


def main():
    ap = argparse.ArgumentParser(description="Descarga objetos digitales de una nota")
    ap.add_argument("entrada", help="nota.html local o URL de la nota")
    ap.add_argument("--salida", default=None,
                    help="Carpeta base (default: la del nota.html cuando es archivo local)")
    ap.add_argument("--tamano-max", type=float, default=60, help="MB maximo por archivo (default 60)")
    args = ap.parse_args()

    # 1. HTML
    es_url = args.entrada.startswith("http")
    if es_url:
        print(f"[1/4] Obteniendo HTML de {args.entrada}")
        cuerpo, como = conseguir_html(args.entrada)
        if cuerpo is None:
            print("[X] No pude obtener el HTML. Guarda la nota a mano y usa su ruta.")
            sys.exit(2)
        referencia_pagina = args.entrada
        carpeta_base = args.salida or "."
    else:
        print(f"[1/4] Leyendo {args.entrada}")
        with open(args.entrada, "rb") as f:
            cuerpo = f.read().decode("utf-8", errors="replace")
        referencia_pagina = "file://" + args.entrada.replace("\\", "/")
        carpeta_base = args.salida or os.path.dirname(os.path.abspath(args.entrada))

    # URL base para resolver rutas relativas: canonical si existe
    m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', cuerpo)
    url_base = m.group(1) if m else (args.entrada if es_url else "file:///")
    if not es_url and not m:
        print("[i] Aviso: nota local sin canonical; las rutas relativas no se podran resolver.")

    # 2. detectar objetos
    print("[2/4] Detectando objetos en el HTML...")
    parser = NotaParser(url_base)
    parser.feed(cuerpo)
    parser.close()
    urls_unicas, fuentes = [], {}
    for fuente, u in parser.objetos:
        if u not in fuentes:
            urls_unicas.append(u)
            fuentes[u] = fuente
    print(f"      {len(urls_unicas)} URLs unicas ({len(parser.objetos)} referencias)")

    # 3. descargar
    carpeta_obj = os.path.join(carpeta_base, "objetos")
    os.makedirs(carpeta_obj, exist_ok=True)
    tope = int(args.tamano_max * 1024 * 1024)

    print(f"[3/4] Descargando a {carpeta_obj} ...")
    manifiesto, n_ok = [], 0
    for i, u in enumerate(urls_unicas):
        item, data = descargar_objeto(u, referencia_pagina, tope)
        item["url"] = u
        item["fuente_tag"] = fuentes[u]
        if item["estado"] == "ok":
            nombre = f"{i:03d}_{item['sha256'][:8]}{extension_para(u, item['content_type'])}"
            with open(os.path.join(carpeta_obj, nombre), "wb") as f:
                f.write(data)
            item["archivo"] = nombre
            n_ok += 1
        manifiesto.append(item)
        marca = "OK " if item["estado"] == "ok" else "-- "
        print(f"      {marca}{i + 1:3d}/{len(urls_unicas)}  {item['estado']:<30} {u[:70]}")
        time.sleep(0.3)

    # 4. manifiestos
    print("[4/4] Escribiendo manifiestos...")
    resumen = {}
    for it in manifiesto:
        clave = it.get("content_type") or it["estado"].split(" ")[0]
        resumen[clave] = resumen.get(clave, 0) + 1

    campos = ["archivo", "url", "fuente_tag", "content_type", "bytes",
              "sha256", "last_modified", "estado"]
    with open(os.path.join(carpeta_obj, "objetos.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for it in manifiesto:
            w.writerow({k: (it.get(k, "") or "") for k in campos})
    with open(os.path.join(carpeta_obj, "objetos.json"), "w", encoding="utf-8") as f:
        json.dump({"carpeta": carpeta_obj, "total_urls": len(urls_unicas),
                   "descargados": n_ok, "resumen_por_tipo": resumen,
                   "objetos": manifiesto}, f, ensure_ascii=False, indent=1)

    print(f"\nLISTO: {n_ok}/{len(urls_unicas)} objetos descargados -> {carpeta_obj}")
    for t, c in sorted(resumen.items(), key=lambda x: -x[1]):
        print(f"  {c:4d}  {t}")


if __name__ == "__main__":
    main()
