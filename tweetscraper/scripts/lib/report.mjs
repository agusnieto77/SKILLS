// Self-contained HTML report of an image analysis (HTMLImgReport).
// UI copy stays in Spanish to match TweetScraperR's report and its labels.
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const TAGS = [
  ['contenido_discriminatorio', 'Discriminatorio', '#c0392b'],
  ['contenido_violento', 'Violento', '#8e44ad'],
  ['contenido_pornografico', 'Pornográfico', '#d35400'],
  ['contenido_inapropiado', 'Inapropiado', '#7f8c8d'],
];

/** Image src as seen from the report: remote URLs as-is, local files relative to the report. */
function srcFor(img, reportDir) {
  if (/^(https?:|data:)/i.test(img)) return img;
  const rel = path.relative(reportDir, img);
  return rel && !path.isAbsolute(rel) ? rel.split(path.sep).map(encodeURIComponent).join('/') : pathToFileURL(img).href;
}

export function imageReport(rows, outFile) {
  if (!rows.length) throw new Error('The results have no rows.');
  const dir = path.dirname(path.resolve(outFile));
  const cards = rows
    .map((r) => {
      const tags = TAGS.filter(([k]) => r[k] === true)
        .map(([, label, color]) => `<span class="tag" style="background:${color}">${label}</span>`)
        .join('');
      const link = r.tweet_url ? `<a href="${esc(r.tweet_url)}" target="_blank" rel="noopener">Ver tweet</a>` : '';
      return `<article class="card">
  <div class="img"><img loading="lazy" src="${esc(srcFor(r.img, dir))}" alt="${esc(r.clasificacion)}"></div>
  <div class="body">
    <h2>${esc(r.clasificacion ?? 'Sin clasificar')}</h2>
    <p class="desc">${esc(r.descripcion ?? r.error ?? '')}</p>
    <p><strong>Palabras clave:</strong> ${esc(r.palabras_clave)}</p>
    <p><strong>Texto en la imagen:</strong> ${r.contiene_texto === true ? esc(r.texto_contenido) : 'No contiene texto'}</p>
  </div>
  <footer>${tags}${link}</footer>
</article>`;
    })
    .join('\n');
  const counts = {};
  for (const r of rows) counts[r.clasificacion ?? 'Sin clasificar'] = (counts[r.clasificacion ?? 'Sin clasificar'] || 0) + 1;
  const chips = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<span class="chip">${esc(k)}: ${v}</span>`)
    .join('');
  return `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análisis de imágenes</title>
<style>
  :root { --bg:#f5f6f8; --card:#fff; --fg:#1f2933; --muted:#52606d; --accent:#1d4ed8; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; background:var(--bg); color:var(--fg); }
  header { padding:2rem 1.5rem 1rem; background:linear-gradient(135deg,#1e3a8a,#2563eb); color:#fff; }
  header h1 { margin:0 0 .5rem; font-size:1.6rem; }
  .chips { display:flex; flex-wrap:wrap; gap:.4rem; }
  .chip { background:rgba(255,255,255,.18); padding:.2rem .6rem; border-radius:999px; font-size:.85rem; }
  main { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:1.2rem; padding:1.5rem; }
  .card { background:var(--card); border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.12); display:flex; flex-direction:column; }
  .img { aspect-ratio: 4/3; background:#e4e7eb; display:flex; align-items:center; justify-content:center; }
  .img img { max-width:100%; max-height:100%; object-fit:contain; }
  .body { padding:1rem; flex:1; }
  .body h2 { margin:0 0 .5rem; font-size:1.1rem; color:var(--accent); }
  .body p { margin:.4rem 0; font-size:.9rem; line-height:1.4; }
  .desc { color:var(--muted); max-height:9.5em; overflow:auto; }
  footer { padding:.6rem 1rem; border-top:1px solid #e4e7eb; display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; min-height:2.6rem; }
  .tag { color:#fff; font-size:.75rem; padding:.15rem .5rem; border-radius:4px; }
  footer a { margin-left:auto; font-size:.85rem; color:var(--accent); }
</style>
</head>
<body>
<header>
  <h1>Análisis de imágenes (${rows.length})</h1>
  <div class="chips">${chips}</div>
</header>
<main>
${cards}
</main>
</body>
</html>
`;
}
