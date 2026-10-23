// Reading and writing datasets: JSON Lines (default), JSON array or CSV.
import fs from 'node:fs';
import path from 'node:path';
import { toMarkdown } from './markdown.mjs';
export { toMarkdown, writeMarkdown } from './markdown.mjs';

// Separator of list columns (hashtags, media...) in CSV cells.
export const LIST_SEP = ' | ';

/** "YYYY_MM_DD_HH_MM_SS" in local time, as TweetScraperR names its files. */
export function stamp(d = new Date()) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}_${p(d.getMonth() + 1)}_${p(d.getDate())}_${p(d.getHours())}_${p(d.getMinutes())}_${p(d.getSeconds())}`;
}

export const slug = (s) => String(s).replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'x';

export function formatOf(file, explicit) {
  if (explicit) return explicit;
  const ext = path.extname(file || '').toLowerCase();
  if (ext === '.csv') return 'csv';
  if (ext === '.json') return 'json';
  if (ext === '.md' || ext === '.markdown') return 'markdown';
  return 'jsonl';
}

/** Output path: the one given, or "<prefix>_<stamp>.jsonl" in the current directory. */
export function outPath(out, prefix) {
  return out || path.resolve(`${prefix}_${stamp()}.jsonl`);
}

function csvCell(v) {
  if (v == null) return '';
  if (Array.isArray(v)) v = v.join(LIST_SEP);
  else if (typeof v === 'object') v = JSON.stringify(v);
  const s = String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

export function toCsv(rows, fields) {
  const cols = fields || [...new Set(rows.flatMap((r) => Object.keys(r)))];
  const lines = [cols.map(csvCell).join(',')];
  for (const r of rows) lines.push(cols.map((c) => csvCell(r[c])).join(','));
  // BOM so Excel opens accented text as UTF-8.
  return '\ufeff' + lines.join('\r\n') + '\r\n';
}

export function serialize(rows, format, fields) {
  if (format === 'csv') return toCsv(rows, fields);
  if (format === 'markdown' || format === 'md') return toMarkdown(rows);
  if (format === 'json') return JSON.stringify(rows, null, 2) + '\n';
  return rows.map((r) => JSON.stringify(r)).join('\n') + (rows.length ? '\n' : '');
}

/** Writes rows to `file` ("-" = stdout). Returns the absolute path (or "-"). */
export function writeRows(file, rows, { format, fields } = {}) {
  const fmt = formatOf(file === '-' ? '' : file, format);
  const text = serialize(rows, fmt, fields);
  if (file === '-') {
    process.stdout.write(text);
    return '-';
  }
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, text, 'utf8');
  return path.resolve(file);
}

/** Appends one record to a JSONL file (incremental output that survives interruptions). */
export function appendJsonl(file, row) {
  fs.appendFileSync(file, JSON.stringify(row) + '\n', 'utf8');
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') {
      row.push(cell);
      cell = '';
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = '';
    } else cell += c;
  }
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}

const CSV_LISTS = new Set(['emoticones', 'hashtags', 'menciones', 'urls_externas', 'media', 'media_tipo']);
const CSV_NUMS = new Set([
  'respuestas', 'retweets', 'citas', 'megustas', 'views', 'guardados',
  'seguidores', 'siguiendo', 'tweets', 'favoritos', 'tweets_media', 'cambios_usuario',
]);
const CSV_BOOLS = new Set([
  'es_retweet', 'es_cita', 'sensible', 'editado', 'verificado', 'protegida',
  'ubicacion_precisa', 'identidad_verificada',
]);

function csvValue(col, s) {
  if (CSV_LISTS.has(col)) return s ? s.split(LIST_SEP) : [];
  if (s === '') return null;
  if (CSV_NUMS.has(col)) return Number(s);
  if (CSV_BOOLS.has(col)) return s === 'true' || s === 'TRUE';
  return s;
}

/** Reads a dataset written by this tool (JSONL, JSON array or CSV). */
export function readRows(file) {
  let text = fs.readFileSync(file, 'utf8').replace(/^\ufeff/, '');
  const fmt = formatOf(file);
  if (fmt === 'csv') {
    const [head, ...body] = parseCsv(text).filter((r) => r.length > 1 || r[0] !== '');
    return body.map((r) => Object.fromEntries(head.map((h, i) => [h, csvValue(h, r[i] ?? '')])));
  }
  text = text.trim();
  if (!text) return [];
  if (text[0] === '[') return JSON.parse(text);
  return text.split(/\r?\n/).filter(Boolean).map((l) => JSON.parse(l));
}
