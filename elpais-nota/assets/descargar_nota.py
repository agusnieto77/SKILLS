# -*- coding: utf-8 -*-
"""
descargar_nota.py
Descarga una nota digital y sus metadatos completos:
  - HTML crudo de respaldo (nota.html)
  - metadatos.json (meta tags, JSON-LD, fechas, autor, canonical, contador
    de comentarios Disqus cuando existe, contadores genericos)
  - nota.txt (texto limpio del cuerpo)
  - links.csv (todos los <a> con su texto y tipo)

Uso:
    python descargar_nota.py "https://elpais.com/ruta/nota.html" --salida salidas
    python descargar_nota.py "URL" --html nota_guardada.html   (modo manual anti-403)

Estrategia de captura del HTML (3 capas):
    1. HTTP directo con cabeceras de navegador.
    2. Wayback Machine (notas archivadas).
    3. Archivo local: guarda la pagina a mano (Ctrl+S o ver codigo fuente)
       y pasala con --html.

Solo libreria estandar de Python 3.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

METAllaves_INTERES = None  # guardamos TODAS las meta; filtrar es trabajo del analisis


def http_get(url, referer=None, timeout=40, retries=3, headers_extra=None):
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    if headers_extra:
        headers.update(headers_extra)
    last = None
    for intento in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1 + intento)
    raise RuntimeError(f"GET fallo: {url} ({last})")


def leer_archivo_texto(path):
    with open(path, "rb") as f:
        data = f.read()
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


class NotaParser(HTMLParser):
    """Extrae meta, title, canonical, h1, JSON-LD, links, objetos y parrafos."""

    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base = base_url
        self._pila = ["body"]
        self._jsonld_buffer = ""
        self._jsonld_on = False
        self.meta = []
        self.title = ""
        self.canonical = ""
        self.h1 = []
        self.jsonld = []
        self.links = []
        self.objetos = []       # (fuente_tag, url_cruda)
        self.parrafos = []      # (ambito, texto)  ambito: article|main|body
        self._en_title = False
        self._link_href = None
        self._link_texto = []
        self._h1_abierto = False
        self._h1_texto = []
        self._p_ambito = None
        self._p_texto = []

    # -- utilidades ---------------------------------------------------------
    def _abs(self, url):
        if not url or url.startswith(("data:", "javascript:", "mailto:", "tel:", "#")):
            return None
        return urllib.parse.urljoin(self.base, url)

    def _ambito_actual(self):
        # aproximacion simple: usamos un contador guardado en self._pila
        return self._pila[-1] if self._pila else "body"

    # -- eventos ------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            clave = a.get("property") or a.get("name") or a.get("itemprop")
            if clave and a.get("content") is not None:
                self.meta.append({"clave": clave, "contenido": a["content"]})
        elif tag == "title":
            self._en_title = True
        elif tag == "link":
            if a.get("rel") == "canonical" and a.get("href"):
                self.canonical = self._abs(a["href"]) or a["href"]
            if a.get("type") in ("application/rss+xml", "application/json"):
                u = self._abs(a.get("href"))
                if u:
                    self.objetos.append(("link-" + a["type"].split("/")[-1], u))
        elif tag == "script" and a.get("type") == "application/ld+json":
            # el contenido llega por handle_data; marcamos colector
            self._jsonld_on = True
        elif tag in ("article", "main"):
            self._pila.append(tag)
        elif tag == "h1":
            self._h1_abierto = True
            self._h1_texto = []
        elif tag == "p":
            self._p_ambito = self._ambito_actual()
            self._p_texto = []
        elif tag == "a":
            href = self._abs(a.get("href"))
            if href:
                self._link_href = href
                self._link_texto = []
        elif tag == "img":
            for fuente in ("src", "data-src"):
                u = self._abs(a.get(fuente))
                if u:
                    self.objetos.append(("img-" + fuente, u))
            srcset = a.get("srcset") or a.get("data-srcset")
            if srcset:
                for parte in srcset.split(","):
                    partes = parte.strip().split()
                    if partes:
                        u = self._abs(partes[0])
                        if u:
                            self.objetos.append(("img-srcset", u))
        elif tag == "source":
            u = self._abs(a.get("src"))
            if u:
                self.objetos.append(("source-src", u))
            srcset = a.get("srcset")
            if srcset:
                for parte in srcset.split(","):
                    partes = parte.strip().split()
                    if partes:
                        u = self._abs(partes[0])
                        if u:
                            self.objetos.append(("source-srcset", u))
        elif tag in ("video", "audio"):
            u = self._abs(a.get("src"))
            if u:
                self.objetos.append((tag + "-src", u))
            if a.get("poster"):
                u = self._abs(a["poster"])
                if u:
                    self.objetos.append((tag + "-poster", u))

    def handle_endtag(self, tag):
        if tag == "title":
            self._en_title = False
        elif tag == "script" and getattr(self, "_jsonld_on", False):
            self._jsonld_on = False
            buffer = getattr(self, "_jsonld_buffer", "")
            if buffer.strip():
                try:
                    self.jsonld.append(json.loads(buffer))
                except Exception:
                    self.jsonld.append({"_crudo": buffer[:2000]})
            self._jsonld_buffer = ""
        elif tag in ("article", "main") and self._pila:
            self._pila.pop()
        elif tag == "h1" and self._h1_abierto:
            texto = " ".join("".join(self._h1_texto).split())
            if texto:
                self.h1.append(texto)
            self._h1_abierto = False
        elif tag == "p":
            texto = " ".join("".join(self._p_texto).split())
            if texto:
                self.parrafos.append((self._p_ambito or "body", texto))
            self._p_ambito = None
        elif tag == "a" and self._link_href is not None:
            texto = " ".join("".join(self._link_texto).split())
            self.links.append({"url": self._link_href, "texto": texto[:200]})
            self._link_href = None

    def handle_data(self, data):
        if self._en_title:
            self.title += data
        elif getattr(self, "_jsonld_on", False):
            self._jsonld_buffer = getattr(self, "_jsonld_buffer", "") + data
        elif self._h1_abierto:
            self._h1_texto.append(data)
        elif self._link_href is not None:
            self._link_texto.append(data)
        elif self._p_ambito is not None:
            self._p_texto.append(data)

    def close(self):
        super().close()
        # vaciar buffer jsonld pendiente (bloque sin </script> procesado)
        if getattr(self, "_jsonld_buffer", ""):
            try:
                self.jsonld.append(json.loads(self._jsonld_buffer))
            except Exception:
                self.jsonld.append({"_crudo": self._jsonld_buffer[:2000]})
            self._jsonld_buffer = ""


def contar_comentarios_disqus(cuerpo_html, url_base):
    """Devuelve (identificador, foro, contador) si la nota usa Disqus."""
    m = re.search(r'data-disqus-identifier="([^"]+)"', cuerpo_html)
    if not m:
        return None, None, None
    ident = m.group(1)
    m2 = re.search(r'([a-z0-9-]+)\.disqus\.com/(?:count-data|count|embed)\.js', cuerpo_html)
    foro = m2.group(1) if m2 else None
    if not foro:
        return ident, None, None
    try:
        u = f"https://{foro}.disqus.com/count-data.js?1={urllib.parse.quote(ident)}"
        _, js = http_get(u, referer=url_base)
        m3 = re.search(r'"comments":\s*(\d+)', js)
        contador = int(m3.group(1)) if m3 else None
        return ident, foro, contador
    except Exception:
        return ident, foro, None


def contadores_genericos(cuerpo_html):
    """Otros contadores de comentarios visibles en el HTML (no Disqus)."""
    hallados = {}
    for patron, clave in [
        (r':num-comments="(\d+)"', "num-comments-atributo"),
        (r'"num_comments"[:\s]+(\d+)', "num_comments-json"),
        (r'data-comments-count="(\d+)"', "data-comments-count"),
    ]:
        m = re.search(patron, cuerpo_html)
        if m:
            hallados[clave] = int(m.group(1))
    return hallados


def conseguir_html(url, html_local=None):
    """Devuelve (html, como_se_obtuvo). 3 capas: local -> directo -> wayback."""
    if html_local:
        return leer_archivo_texto(html_local), "archivo-local"
    try:
        status, cuerpo = http_get(url)
        if status == 200:
            return cuerpo, "http-directo"
        print(f"[i] HTTP directo devolvio {status}. Probando Wayback Machine...")
    except Exception as e:
        print(f"[i] HTTP directo fallo ({e}). Probando Wayback Machine...")
    try:
        _, wb = http_get("http://archive.org/wayback/available?url="
                         + urllib.parse.quote(url, safe=""))
        snap = json.loads(wb).get("archived_snapshots", {}).get("closest", {}).get("url")
        if snap:
            print(f"[i] Snapshot: {snap}")
            status, cuerpo = http_get(snap)
            if status == 200:
                return cuerpo, "wayback"
    except Exception as e:
        print(f"[i] Wayback fallo: {e}")
    return None, None


def slug_de(url, html_texto):
    m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html_texto or "")
    base = m.group(1) if m else url
    path = urllib.parse.urlparse(base).path.rstrip("/")
    nombre = os.path.basename(path)
    nombre = re.sub(r"\.html?$", "", nombre)
    nombre = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)[:80]
    return nombre or "nota"


def main():
    ap = argparse.ArgumentParser(description="Descarga una nota digital con todos sus metadatos")
    ap.add_argument("url", help="URL de la nota")
    ap.add_argument("--salida", default=".", help="Carpeta base de salida")
    ap.add_argument("--html", dest="html_local", help="HTML ya guardado a mano (anti-403)")
    args = ap.parse_args()

    print(f"[1/5] Obteniendo HTML de:\n      {args.url}")
    cuerpo, como = conseguir_html(args.url, args.html_local)
    if cuerpo is None:
        print("[X] No pude obtener el HTML automaticamente.")
        print("    Solucion manual: abri la nota en el navegador -> Ctrl+S (pagina completa)")
        print('    -> repeti el comando con --html "archivo.html"')
        sys.exit(2)
    print(f"      obtenido via: {como}  ({len(cuerpo):,} caracteres)")

    print("[2/5] Parseando (meta, JSON-LD, links, objetos, parrafos)...")
    parser = NotaParser(args.url)
    parser.feed(cuerpo)
    parser.close()

    print("[3/5] Contadores de comentarios...")
    ident_disqus, foro_disqus, contador_disqus = contar_comentarios_disqus(cuerpo, args.url)
    otros = contadores_genericos(cuerpo)

    meta_dict = {}
    for m in parser.meta:
        meta_dict.setdefault(m["clave"], m["contenido"])

    meta_out = {
        "source_url": args.url,
        "como_se_obtuvo": como,
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": " ".join(parser.title.split()),
        "canonical": parser.canonical,
        "h1": parser.h1,
        "meta_tags": meta_dict,
        "json_ld": parser.jsonld,
        "comentarios": {
            "disqus": {
                "identificador": ident_disqus,
                "foro": foro_disqus,
                "contador_actual": contador_disqus,
            } if ident_disqus else None,
            "otros_contadores": otros,
        },
        "totales": {
            "links": len(parser.links),
            "objetos_detectados": len(parser.objetos),
            "parrafos": len(parser.parrafos),
        },
    }

    slug = slug_de(args.url, cuerpo)
    carpeta = os.path.join(args.salida, f"nota_{slug}")
    os.makedirs(carpeta, exist_ok=True)

    print(f"[4/5] Escribiendo en {carpeta} ...")
    with open(os.path.join(carpeta, "nota.html"), "w", encoding="utf-8") as f:
        f.write(cuerpo)
    with open(os.path.join(carpeta, "metadatos.json"), "w", encoding="utf-8") as f:
        json.dump(meta_out, f, ensure_ascii=False, indent=1)

    ambito_preferido = None
    for ambito in ("article", "main", "body"):
        textos = [t for a, t in parser.parrafos if a == ambito]
        if textos:
            ambito_preferido = (ambito, textos)
            break
    with open(os.path.join(carpeta, "nota.txt"), "w", encoding="utf-8") as f:
        if ambito_preferido:
            f.write(f"{meta_out['title']}\n\n")
            f.write("\n\n".join(ambito_preferido[1]))
        else:
            f.write("(no se detectaron parrafos)")

    # links.csv con url absoluta + dedup
    vistos, filas = set(), []
    for l in parser.links:
        if l["url"] in vistos:
            continue
        vistos.add(l["url"])
        externo = urllib.parse.urlparse(l["url"]).netloc != urllib.parse.urlparse(args.url).netloc
        filas.append({"url": l["url"], "texto": l["texto"],
                      "tipo": "externo" if externo else "interno"})
    with open(os.path.join(carpeta, "links.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "texto", "tipo"], delimiter=";")
        w.writeheader()
        w.writerows(filas)

    print("[5/5] LISTO:")
    print(f"  {carpeta}\\nota.html       (respaldo crudo)")
    print(f"  {carpeta}\\metadatos.json  (meta + JSON-LD + comentarios + totales)")
    print(f"  {carpeta}\\nota.txt        ({len(ambito_preferido[1]) if ambito_preferido else 0} parrafos)")
    print(f"  {carpeta}\\links.csv       ({len(filas)} links unicos)")
    if contador_disqus is not None:
        print(f"  comentarios Disqus ahora mismo: {contador_disqus}")


if __name__ == "__main__":
    main()
