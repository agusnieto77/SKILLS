// Content is data: escape HTML, Markdown and Obsidian syntax; URLs cannot choose local paths.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

export const escapeMarkdown = (value) => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/([\\`*_{}\[\]()#!|~+-])/g, '\\$1').replace(/^(\s*\d+)\./gm, '$1\\.');

export function safeUrl(value) {
  try {
    const u = new URL(value);
    if (!['http:', 'https:'].includes(u.protocol) || u.username || u.password || /[\u0000-\u0020]/.test(value)) return null;
    return u.href.replace(/[()<>]/g, (c) => '%' + c.charCodeAt(0).toString(16).toUpperCase());
  } catch { return null; }
}
const link = (label, url) => safeUrl(url) ? `[${escapeMarkdown(label)}](${safeUrl(url)})` : escapeMarkdown(label);
const tweetLink = (row) => safeUrl(row.url) ?? (/^\d+$/.test(row.tweet_id ?? '') ? `https://x.com/i/status/${row.tweet_id}` : null);
const mediaOf = (row) => row.article_id
  ? [...(row.portada ? [{ url: row.portada, tipo: 'photo' }] : []), ...(row.media ?? [])]
  : (row.media ?? []).map((url, i) => ({ url, tipo: row.media_tipo?.[i] ?? 'photo' }));

function mediaMarkdown(media, localized) {
  const remote = safeUrl(media.url);
  const target = localized?.has(media.url) ? localized.get(media.url) : remote;
  if (!target) return '';
  return media.tipo === 'photo' ? `![media](${target})` : `[media (${escapeMarkdown(media.tipo)})](${target})`;
}

function inlineBlock(block, entities) {
  const text = String(block.text ?? '');
  const ranges = (block.entityRanges ?? []).filter((r) => Number.isInteger(r.offset) && r.offset >= 0 && r.length > 0 && r.offset + r.length <= text.length);
  const styles = (block.inlineStyleRanges ?? []).filter((r) => Number.isInteger(r.offset) && r.offset >= 0 && r.length > 0 && r.offset + r.length <= text.length);
  const boundaries = [...new Set([0, text.length, ...ranges.flatMap((r) => [r.offset, r.offset + r.length]),
    ...styles.flatMap((r) => [r.offset, r.offset + r.length])])].sort((a, b) => a - b);
  let result = '';
  for (let i = 0; i < boundaries.length - 1; i++) {
    const start = boundaries[i];
    const end = boundaries[i + 1];
    let value = escapeMarkdown(text.slice(start, end));
    for (const r of styles.filter((r) => r.offset <= start && r.offset + r.length >= end)) {
      const marker = { bold: '**', italic: '*', strikethrough: '~~', code: '`' }[String(r.style).toLowerCase()];
      if (marker && String(r.style).toLowerCase() !== 'code') value = marker + value + marker;
    }
    const range = ranges.find((r) => r.offset <= start && r.offset + r.length >= end);
    const entity = range ? entities[String(range.key)] : null;
    if (String(entity?.type).toUpperCase() === 'LINK' && safeUrl(entity.data?.url)) value = `[${value}](${safeUrl(entity.data.url)})`;
    result += value;
  }
  return result;
}

export function articleMarkdown(row, localized) {
  if (row.estado_cuerpo !== 'completo') return `> Solo preview; cuerpo no disponible.\n\n${escapeMarkdown(row.preview)}`;
  if (!row.bloques?.length) return escapeMarkdown(row.texto);
  const entities = row.entidades ?? {};
  const parts = [];
  for (const block of row.bloques) {
    const value = inlineBlock(block, entities);
    const depth = Number.isInteger(block.depth) ? Math.min(6, Math.max(0, block.depth)) : 0;
    if (block.type === 'atomic') {
      const ids = (block.entityRanges ?? []).map((r) => entities[String(r.key)]?.data?.mediaId);
      if (block.data?.mediaId) ids.push(block.data.mediaId);
      for (const id of ids) {
        const media = (row.media ?? []).find((m) => m.id === String(id));
        if (media) parts.push(mediaMarkdown(media, localized));
      }
    } else if (/^header-(one|two|three|four|five|six)$/.test(block.type)) {
      const n = ['one', 'two', 'three', 'four', 'five', 'six'].indexOf(block.type.split('-')[1]) + 1;
      parts.push('#'.repeat(n) + ' ' + value);
    } else if (block.type === 'blockquote') parts.push(value.split('\n').map((s) => '> ' + s).join('\n'));
    else if (block.type === 'code-block') parts.push(String(block.text ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').split('\n').map((s) => '    ' + s).join('\n'));
    else if (block.type === 'unordered-list-item' || block.type === 'ordered-list-item') parts.push('  '.repeat(depth) + (block.type === 'ordered-list-item' ? '1. ' : '- ') + value);
    else parts.push(value);
  }
  return parts.filter(Boolean).join('\n\n');
}

export function toMarkdown(rows, { style = 'full', query = null, capturedAt = new Date().toISOString(), localized } = {}) {
  if (!['compact', 'full'].includes(style)) throw new Error('md-style must be compact or full.');
  const first = rows[0];
  const front = { url: first?.url ?? null, autor: first?.user ?? null, fecha: first?.fecha ?? null, consulta: query,
    capturado_en: capturedAt, formato: style, tweets: rows.length };
  const lines = ['---', ...Object.entries(front).map(([k, v]) => `${k}: ${JSON.stringify(v)}`), '---', ''];
  const byId = new Map(rows.map((r) => [r.tweet_id, r]));
  for (const row of rows) {
    lines.push(`## ${escapeMarkdown(row.article_id ? row.titulo ?? 'Article' : row.user ?? 'Tweet')} · ${escapeMarkdown(row.fecha ?? '')}`, '');
    const url = row.article_id ? row.url : tweetLink(row);
    if (url) lines.push(link('Fuente', url), '');
    if (row.rol) lines.push(`Rol: ${escapeMarkdown(row.rol)}`, '');
    if (row.article_id) {
      if (row.portada) lines.push(mediaMarkdown({ url: row.portada, tipo: 'photo' }, localized), '');
      lines.push(articleMarkdown(row, localized), '');
      if (style === 'full' && row.user) lines.push(`Autor: ${escapeMarkdown(row.user)}`, '');
      continue;
    }
    lines.push(escapeMarkdown(row.texto ?? row.tweet), '');
    if (/^\d+$/.test(row.tweet_citado_id ?? '')) {
      const quote = byId.get(row.tweet_citado_id);
      const quoteUrl = quote ? tweetLink(quote) : 'https://x.com/i/status/' + row.tweet_citado_id;
      lines.push('### Tweet citado', '', '> ' + link(quote?.user ?? 'Fuente de la cita', quoteUrl),
        ...(quote ? ['', ...escapeMarkdown(quote.texto).split('\n').map((s) => '> ' + s)] : ['> Texto no incluido en el dataset.']), '');
    }
    for (const media of mediaOf(row)) { const md = mediaMarkdown(media, localized); if (md) lines.push(md, ''); }
    if (style === 'full') {
      lines.push(`Me gusta: ${row.megustas ?? '—'} · Retweets: ${row.retweets ?? '—'} · Respuestas: ${row.respuestas ?? '—'} · Vistas: ${row.views ?? '—'}`, '');
      if (row.respuesta_a_id && /^\d+$/.test(row.respuesta_a_id)) lines.push(link('En respuesta a', 'https://x.com/i/status/' + row.respuesta_a_id), '');
      for (const external of row.urls_externas ?? []) if (safeUrl(external)) lines.push(link('Enlace externo', external), '');
    }
  }
  return lines.join('\n').trimEnd() + '\n';
}

const MEDIA_TYPES = new Map([['image/jpeg', 'jpg'], ['image/png', 'png'], ['image/gif', 'gif'], ['image/webp', 'webp'], ['video/mp4', 'mp4']]);

export async function writeMarkdown(file, rows, { downloadMedia = false, maxMediaBytes = 25 * 1024 * 1024,
  fetch: request = globalThis.fetch, signal, ...render } = {}) {
  if (downloadMedia && file === '-') throw new Error('La descarga requiere un archivo Markdown, no stdout.');
  if (!Number.isSafeInteger(maxMediaBytes) || maxMediaBytes < 1) throw new Error('max-media-bytes debe ser un entero positivo.');
  // Validate render settings before any downloads or filesystem writes.
  toMarkdown([], render);
  const warnings = [];
  let downloaded = 0;
  const localized = new Map();
  const absolute = path.resolve(file);
  const folder = path.join(path.dirname(absolute), path.parse(absolute).name + '_media');
  if (downloadMedia) {
    for (const media of rows.flatMap(mediaOf)) {
      if (localized.has(media.url)) continue;
      localized.set(media.url, null);
      let response;
      let headerTimer;
      let totalTimer;
      try {
        signal?.throwIfAborted();
        const url = new URL(media.url);
        if (url.protocol !== 'https:' || url.username || url.password || url.port ||
          !['pbs.twimg.com', 'video.twimg.com'].includes(url.hostname)) throw new Error('host de media no permitido');
        const headersTimeout = new AbortController();
        headerTimer = setTimeout(() => headersTimeout.abort(new Error('tiempo de espera de cabeceras agotado')), 30000);
        const totalTimeout = new AbortController();
        totalTimer = setTimeout(() => totalTimeout.abort(new Error('tiempo total de descarga agotado')), 300000);
        const downloadSignal = AbortSignal.any([headersTimeout.signal, totalTimeout.signal, ...(signal ? [signal] : [])]);
        response = await request(url.href, { credentials: 'omit', redirect: 'error',
          signal: downloadSignal });
        clearTimeout(headerTimer);
        downloadSignal.throwIfAborted();
        const type = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase();
        const ext = MEDIA_TYPES.get(type);
        if (!response.ok || !ext || (media.tipo === 'photo' ? !type.startsWith('image/') : !type.startsWith('video/'))) throw new Error('HTTP o content-type no válido');
        const length = response.headers.get('content-length');
        if (length && (!/^\d+$/.test(length) || Number(length) > maxMediaBytes)) throw new Error('tamaño anunciado excede el límite');
        const chunks = [];
        let size = 0;
        if (!response.body) throw new Error('respuesta sin cuerpo');
        for await (const chunk of response.body) {
          downloadSignal.throwIfAborted();
          size += chunk.byteLength;
          if (size > maxMediaBytes) throw new Error('tamaño descargado excede el límite');
          chunks.push(chunk);
        }
        downloadSignal.throwIfAborted();
        if (!size) throw new Error('archivo vacío');
        fs.mkdirSync(folder, { recursive: true });
        if (fs.lstatSync(folder).isSymbolicLink()) throw new Error('carpeta de media no puede ser un enlace simbólico');
        const name = createHash('sha256').update(url.href).digest('hex').slice(0, 24) + '.' + ext;
        const target = path.join(folder, name);
        const content = Buffer.concat(chunks, size);
        try {
          fs.writeFileSync(target, content, { flag: 'wx' });
          downloaded++;
        } catch (e) {
          if (e.code !== 'EEXIST') throw e;
          const existing = fs.lstatSync(target);
          if (!existing.isFile() || existing.size !== size || !fs.readFileSync(target).equals(content)) {
            throw new Error('archivo de media existente no coincide con la descarga verificada');
          }
        }
        localized.set(media.url, path.relative(path.dirname(absolute), target).split(path.sep).map(encodeURIComponent).join('/'));
      } catch (e) {
        signal?.throwIfAborted();
        warnings.push(`Media omitida (${String(media.url)}): ${e.message}`);
      } finally {
        clearTimeout(headerTimer);
        clearTimeout(totalTimer);
        if (response?.body && !response.body.locked) await response.body.cancel().catch(() => {});
      }
    }
  }
  signal?.throwIfAborted();
  const text = toMarkdown(rows, { ...render, localized: downloadMedia ? localized : undefined });
  if (file === '-') process.stdout.write(text);
  else { fs.mkdirSync(path.dirname(absolute), { recursive: true }); fs.writeFileSync(absolute, text, 'utf8'); }
  return { out: file === '-' ? '-' : absolute, warnings, downloaded };
}
