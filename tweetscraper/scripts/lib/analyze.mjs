// Local analysis of collected datasets (no network): the equivalents of
// plotTime, plotWords, plotEmojis/plotEmojisPNG and getTweetsHashtags.
import { createRequire } from 'node:module';
import { extractEmojis, extractHashtags } from './parse.mjs';

const require = createRequire(import.meta.url);

export const textOf = (r) => r.texto ?? r.tweet ?? null;

function requireText(rows) {
  if (rows.length && !rows.some((r) => 'texto' in r || 'tweet' in r)) {
    throw new Error("The dataset needs a 'texto' or 'tweet' column.");
  }
}

/** Sorted [{key, n}] (desc by n, then key) from an iterable of keys. */
function tally(keys, top = Infinity) {
  const m = new Map();
  for (const k of keys) m.set(k, (m.get(k) || 0) + 1);
  return [...m.entries()]
    .map(([key, n]) => ({ key, n }))
    .sort((a, b) => b.n - a.n || a.key.localeCompare(b.key))
    .slice(0, top);
}

// ---- hashtags -------------------------------------------------------------

/** Hashtags per tweet: the `hashtags` column (X entities) or, with fromText, extracted from the text. */
export function hashtagsOf(r, fromText = false) {
  if (!fromText && Array.isArray(r.hashtags)) return r.hashtags;
  return extractHashtags(textOf(r));
}

export function hashtagCounts(rows, { top = Infinity, ignoreCase = false, fromText = false } = {}) {
  if (fromText || !rows.some((r) => Array.isArray(r.hashtags))) requireText(rows);
  const keys = rows.flatMap((r) => hashtagsOf(r, fromText)).map((h) => (ignoreCase ? h.toLowerCase() : h));
  return tally(keys, top).map(({ key, n }) => ({ hashtag: key, n }));
}

/** Adds/replaces the `hashtags` column extracted from the text (getTweetsHashtags). */
export function withHashtags(rows) {
  requireText(rows);
  return rows.map((r) => ({ ...r, hashtags: extractHashtags(textOf(r)) }));
}

// ---- time -----------------------------------------------------------------

export const GROUPS = ['hour', 'day', 'week', 'month', 'year'];

const iso = (d) => d.toISOString();

/** Start of the UTC bucket containing `d`. Weeks start on Sunday (lubridate's default). */
function floorUtc(d, group) {
  const y = d.getUTCFullYear();
  const mo = d.getUTCMonth();
  const day = d.getUTCDate();
  if (group === 'hour') return new Date(Date.UTC(y, mo, day, d.getUTCHours()));
  if (group === 'day') return new Date(Date.UTC(y, mo, day));
  if (group === 'week') return new Date(Date.UTC(y, mo, day - d.getUTCDay()));
  if (group === 'month') return new Date(Date.UTC(y, mo, 1));
  return new Date(Date.UTC(y, 0, 1));
}

function nextBucket(d, group) {
  const n = new Date(d);
  if (group === 'hour') n.setUTCHours(n.getUTCHours() + 1);
  else if (group === 'day') n.setUTCDate(n.getUTCDate() + 1);
  else if (group === 'week') n.setUTCDate(n.getUTCDate() + 7);
  else if (group === 'month') n.setUTCMonth(n.getUTCMonth() + 1);
  else n.setUTCFullYear(n.getUTCFullYear() + 1);
  return n;
}

export function bucketLabel(d, group) {
  const s = iso(d);
  if (group === 'hour') return s.slice(0, 13) + ':00';
  if (group === 'day' || group === 'week') return s.slice(0, 10);
  if (group === 'month') return s.slice(0, 7);
  return s.slice(0, 4);
}

/**
 * Tweet counts per UTC time bucket, oldest first. Empty buckets between the
 * first and last tweet are included with n = 0 so the series is continuous.
 */
export function timeCounts(rows, group = 'hour') {
  if (!GROUPS.includes(group)) throw new Error('group must be one of: ' + GROUPS.join(', '));
  if (rows.length && !rows.some((r) => 'fecha' in r)) throw new Error("The dataset needs a 'fecha' column.");
  const counts = new Map();
  for (const r of rows) {
    if (!r.fecha) continue;
    const d = new Date(r.fecha);
    if (Number.isNaN(+d)) continue;
    const k = +floorUtc(d, group);
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  if (!counts.size) return [];
  const keys = [...counts.keys()];
  const out = [];
  for (let d = new Date(Math.min(...keys)); +d <= Math.max(...keys); d = nextBucket(d, group)) {
    out.push({ fecha: bucketLabel(d, group), n: counts.get(+d) || 0 });
  }
  return out;
}

// ---- words ----------------------------------------------------------------

let stopwordsIso = null;

export function stopwords(lang) {
  stopwordsIso ??= require('stopwords-iso');
  const list = stopwordsIso[lang];
  if (!list) throw new Error(`No stopword list for language "${lang}".`);
  return list;
}

const URL_RE = /\bhttps?:\/\/\S+|\bwww\.\S+/giu;
const TOKEN_RE = /[#@]?[\p{L}\p{M}\p{N}_]+(?:['’-][\p{L}\p{M}\p{N}_]+)*/gu;

/**
 * Lowercased tokens of a text without URLs, punctuation, symbols, pure
 * numbers or stopwords. Hashtags and mentions stay as tokens (#rstats, @nasa).
 */
export function tokenize(text, stop) {
  if (typeof text !== 'string') return [];
  const out = [];
  for (const m of text.replace(URL_RE, ' ').matchAll(TOKEN_RE)) {
    const t = m[0].toLowerCase();
    if (/^[#@]?[\p{N}_]+$/u.test(t) || stop.has(t)) continue;
    out.push(t);
  }
  return out;
}

export function wordCounts(rows, { lang = 'es', sw = [], minFreq = 3, maxWords = 100 } = {}) {
  requireText(rows);
  const stop = new Set([...stopwords(lang), ...sw].map((w) => w.toLowerCase()));
  return tally(rows.flatMap((r) => tokenize(textOf(r), stop)))
    .filter((w) => w.n >= minFreq)
    .slice(0, maxWords)
    .map(({ key, n }) => ({ word: key, freq: n }));
}

// ---- emojis ---------------------------------------------------------------

export function emojiCounts(rows, top = 10) {
  const hasCol = rows.some((r) => Array.isArray(r.emoticones));
  if (!hasCol) requireText(rows);
  const keys = rows.flatMap((r) => (hasCol ? r.emoticones || [] : extractEmojis(textOf(r)))).filter(Boolean);
  return tally(keys, top).map(({ key, n }) => ({ emoji: key, n }));
}

// ---- summary --------------------------------------------------------------

const clip = (s, n = 140) => (typeof s === 'string' && s.length > n ? s.slice(0, n - 1) + '…' : s);

function range(rows, col) {
  const v = rows.map((r) => r[col]).filter(Boolean).sort();
  return v.length ? { from: v[0], to: v[v.length - 1] } : null;
}

const sum = (rows, col) => rows.reduce((a, r) => a + (Number(r[col]) || 0), 0);

/** Compact overview of a dataset, so the agent never needs to read the whole file. */
export function summarize(rows, top = 5) {
  const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))];
  const out = { rows: rows.length };
  // Analysis outputs first: sentiment rows also carry tweet_id/url.
  if (cols.includes('sentimiento')) {
    out.kind = 'sentiment';
    out.sentimiento = tally(rows.map((r) => r.sentimiento ?? 'NA')).map(({ key, n }) => ({ sentimiento: key, n }));
    out.tono = tally(rows.map((r) => r.tono ?? 'NA')).map(({ key, n }) => ({ tono: key, n }));
    out.expresiones_de_odio = rows.filter((r) => r.expresiones_de_odio === true).length;
    out.failed = rows.filter((r) => r.error).length;
  } else if (cols.includes('clasificacion')) {
    out.kind = 'images';
    out.clasificacion = tally(rows.map((r) => r.clasificacion ?? 'NA')).map(({ key, n }) => ({ clasificacion: key, n }));
    out.failed = rows.filter((r) => r.error).length;
  } else if (cols.includes('tweet_id')) {
    out.kind = 'tweets';
    out.fecha = range(rows, 'fecha');
    out.unique_users = new Set(rows.map((r) => r.user)).size;
    out.top_users = tally(rows.map((r) => r.user).filter(Boolean), top).map(({ key, n }) => ({ user: key, n }));
    out.totals = Object.fromEntries(['respuestas', 'retweets', 'citas', 'megustas', 'views'].map((c) => [c, sum(rows, c)]));
    out.retweets_share = rows.length ? rows.filter((r) => r.es_retweet).length / rows.length : 0;
    out.languages = tally(rows.map((r) => r.idioma).filter(Boolean), top).map(({ key, n }) => ({ idioma: key, n }));
    out.top_hashtags = hashtagCounts(rows, { top, ignoreCase: true });
    out.top_by_megustas = [...rows]
      .sort((a, b) => (b.megustas || 0) - (a.megustas || 0))
      .slice(0, top)
      .map((r) => ({ fecha: r.fecha, user: r.user, megustas: r.megustas, retweets: r.retweets, url: r.url, texto: clip(r.texto) }));
  } else if (cols.includes('seguidores')) {
    out.kind = 'users';
    out.fecha_creacion = range(rows, 'fecha_creacion');
    out.verified = rows.filter((r) => r.verificado).length;
    out.protected = rows.filter((r) => r.protegida).length;
    out.top_by_seguidores = [...rows]
      .sort((a, b) => (b.seguidores || 0) - (a.seguidores || 0))
      .slice(0, top)
      .map((r) => ({ user: r.user, nombre: r.nombre, seguidores: r.seguidores, descripcion: clip(r.descripcion, 100) }));
  } else if (cols.includes('pais_cuenta')) {
    out.kind = 'about';
    out.pais_cuenta = tally(rows.map((r) => r.pais_cuenta ?? 'NA'), top).map(({ key, n }) => ({ pais_cuenta: key, n }));
  }
  // Known kinds have a documented schema (references/schema.md); list columns only otherwise.
  if (!out.kind) out.columns = cols;
  return out;
}
