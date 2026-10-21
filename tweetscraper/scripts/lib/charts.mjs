// Self-contained SVG charts (no dependencies; they open in any browser and
// embed in reports). Equivalents of plotTime, plotEmojis/plotEmojisPNG and plotWords.

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

const FONT = "font-family='system-ui, -apple-system, Segoe UI, Roboto, sans-serif'";

function niceStep(max, ticks = 5) {
  const raw = max / ticks;
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const f = raw / mag;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * mag;
}

/** Line chart of [{fecha, n}] (output of timeCounts). */
export function lineChart(series, { title = '', color = 'steelblue', width = 900, height = 420 } = {}) {
  const m = { top: 48, right: 24, bottom: 110, left: 56 };
  const w = width - m.left - m.right;
  const h = height - m.top - m.bottom;
  const maxY = Math.max(1, ...series.map((d) => d.n));
  const step = niceStep(maxY);
  const top = Math.ceil(maxY / step) * step;
  const x = (i) => m.left + (series.length > 1 ? (i / (series.length - 1)) * w : w / 2);
  const y = (v) => m.top + h - (v / top) * h;
  const parts = [];
  for (let v = 0; v <= top; v += step) {
    parts.push(`<line x1='${m.left}' x2='${m.left + w}' y1='${y(v)}' y2='${y(v)}' stroke='#e5e5e5'/>`);
    parts.push(`<text x='${m.left - 8}' y='${y(v) + 4}' text-anchor='end' font-size='12' fill='#555'>${v}</text>`);
  }
  // At most ~30 x labels, evenly spaced.
  const every = Math.max(1, Math.ceil(series.length / 30));
  series.forEach((d, i) => {
    if (i % every) return;
    const tx = x(i);
    const ty = m.top + h + 10;
    parts.push(`<text transform='translate(${tx},${ty}) rotate(-90)' text-anchor='end' dominant-baseline='middle' font-size='11' fill='#555'>${esc(d.fecha)}</text>`);
  });
  const pts = series.map((d, i) => `${x(i).toFixed(1)},${y(d.n).toFixed(1)}`).join(' ');
  if (series.length > 1) parts.push(`<polyline points='${pts}' fill='none' stroke='${esc(color)}' stroke-width='2'/>`);
  if (series.length <= 60) series.forEach((d, i) => parts.push(`<circle cx='${x(i)}' cy='${y(d.n)}' r='2.5' fill='${esc(color)}'><title>${esc(d.fecha)}: ${d.n}</title></circle>`));
  return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${width} ${height}' width='${width}' height='${height}' ${FONT}>
<rect width='100%' height='100%' fill='white'/>
<text x='${m.left}' y='28' font-size='18' font-weight='600' fill='#222'>${esc(title)}</text>
<text transform='translate(16,${m.top + h / 2}) rotate(-90)' text-anchor='middle' font-size='12' fill='#555'>Nº de tweets</text>
${parts.join('\n')}
<line x1='${m.left}' x2='${m.left + w}' y1='${m.top + h}' y2='${m.top + h}' stroke='#999'/>
</svg>
`;
}

/** Horizontal bar chart of [{label, n}] — emojis render in color with the viewer's emoji font. */
export function barChart(items, { title = '', fill = 'skyblue', stroke = 'grey', labelSize = 24, width = 700 } = {}) {
  const rowH = Math.max(34, labelSize + 12);
  const m = { top: 52, right: 56, bottom: 24, left: 24 + labelSize * 2.6 };
  const w = width - m.left - m.right;
  const height = m.top + m.bottom + rowH * Math.max(1, items.length);
  const max = Math.max(1, ...items.map((d) => d.n));
  const bars = items.map((d, i) => {
    const y = m.top + i * rowH;
    const bw = (d.n / max) * w;
    return `<text x='${m.left - 10}' y='${y + rowH / 2}' text-anchor='end' dominant-baseline='central' font-size='${labelSize}'>${esc(d.label)}</text>
<rect x='${m.left}' y='${y + 4}' width='${bw.toFixed(1)}' height='${rowH - 8}' fill='${esc(fill)}' stroke='${esc(stroke)}'/>
<text x='${m.left + bw + 6}' y='${y + rowH / 2}' dominant-baseline='central' font-size='13' fill='#333'>${d.n}</text>`;
  });
  return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${width} ${height}' width='${width}' height='${height}' ${FONT}>
<rect width='100%' height='100%' fill='white'/>
<text x='24' y='30' font-size='18' font-weight='600' fill='#222'>${esc(title)}</text>
${bars.join('\n')}
</svg>
`;
}

// Deterministic PRNG so the same data always yields the same cloud.
function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const DARK = ['#1b4f72', '#7b241c', '#145a32', '#4a235a', '#7e5109', '#0e6655', '#943126', '#1a5276', '#6c3483', '#283747'];

// Width estimate of a word in em: wide glyphs (CJK, emoji) count ~1, the rest ~0.6.
const emWidth = (word) => [...word].reduce((a, ch) => a + (/[\u2e80-\uffff]/u.test(ch) || ch.codePointAt(0) > 0xffff ? 1 : 0.6), 0);

function layout(list, size, scale, rotateRatio, seed) {
  const rnd = mulberry32(seed);
  const max = Math.max(1, ...list.map((w) => w.freq));
  const min = Math.min(max, ...list.map((w) => w.freq));
  const fs = (f) => scale * (max === min ? 40 : 12 + ((Math.sqrt(f) - Math.sqrt(min)) / (Math.sqrt(max) - Math.sqrt(min))) * 60);
  const placed = [];
  const c = size / 2;
  for (const w of list) {
    const f = fs(w.freq);
    const rot = rnd() < rotateRatio;
    const color = DARK[Math.floor(rnd() * DARK.length)];
    const bw = emWidth(w.word) * f + 4;
    const bh = f * 1.1;
    const [ww, hh] = rot ? [bh, bw] : [bw, bh];
    // Elliptical Archimedean spiral from the center outwards, ~2 px per step.
    for (let a = 0, r = 0; r < size * 0.75; a += Math.min(0.5, 2 / (r + 1)), r = 1.6 * a) {
      const x = c + r * Math.cos(a) - ww / 2;
      const y = c + r * 0.65 * Math.sin(a) - hh / 2;
      if (x < 0 || y < 0 || x + ww > size || y + hh > size) continue;
      if (placed.some((p) => x < p.x + p.w && x + ww > p.x && y < p.y + p.h && y + hh > p.y)) continue;
      placed.push({ x, y, w: ww, h: hh, f, rot, color, word: w.word, freq: w.freq });
      break;
    }
  }
  return placed;
}

/**
 * Word cloud of [{word, freq}] (most frequent first). Font sizes shrink until
 * at least 95% of the words fit; the ones that still do not fit are left out
 * (`dropped` in the returned object).
 */
export function wordCloud(words, { size = 750, rotateRatio = 0.3, shuffle = false, seed = 42 } = {}) {
  const list = [...words];
  if (shuffle) {
    // Seeded Fisher-Yates: random order, still reproducible.
    const rnd = mulberry32(seed + 1);
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(rnd() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
  }
  let placed = [];
  for (const scale of [1, 0.85, 0.7, 0.6, 0.5, 0.42, 0.35, 0.3]) {
    placed = layout(list, size, scale, rotateRatio, seed);
    if (placed.length >= Math.ceil(list.length * 0.95)) break;
  }
  const out = placed.map((p) => {
    const tx = (p.x + p.w / 2).toFixed(1);
    const ty = (p.y + p.h / 2).toFixed(1);
    return `<text x='${tx}' y='${ty}' font-size='${p.f.toFixed(1)}' font-weight='700' fill='${p.color}' text-anchor='middle' dominant-baseline='central'${p.rot ? ` transform='rotate(-90 ${tx} ${ty})'` : ''}><title>${esc(p.word)}: ${p.freq}</title>${esc(p.word)}</text>`;
  });
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${size} ${size}' width='${size}' height='${size}' font-family='Montserrat, system-ui, sans-serif'>
<rect width='100%' height='100%' fill='white'/>
${out.join('\n')}
</svg>
`;
  return { svg, placed: placed.length, dropped: list.length - placed.length };
}
