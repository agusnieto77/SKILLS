// Public providers never receive browser state, cookies, pool accounts or proxy credentials.
import { tweetRow, parseTwitterDate, extractHashtags } from './parse.mjs';

export const syndicationToken = (id) => ((Number(id) / 1e15) * Math.PI).toString(36).replace(/(?:0+|\.)/g, '');
const number = (x) => x == null || !Number.isFinite(Number(x)) ? null : Math.trunc(Number(x));
const idOf = (x) => typeof x === 'string' && /^\d+$/.test(x) ? x : null;
const date = (x) => {
  if (typeof x !== 'string') return null;
  const ms = Date.parse(x);
  return parseTwitterDate(x) ?? (Number.isFinite(ms) ? new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z') : null);
};

export function publicTweetRow(t, provider, requestedId) {
  const fx = provider === 'fxtwitter';
  const id = idOf(fx ? t?.id : t?.id_str);
  if (id !== requestedId || typeof t?.text !== 'string') return null;
  const author = fx ? t.author : t.user;
  const handle = /^[A-Za-z0-9_]+$/.test(author?.screen_name ?? '') ? author.screen_name : null;
  if (!handle) return null;
  const row = tweetRow({ legacy: { full_text: t.text } });
  const quoteId = idOf(fx ? t.quote?.id : t.quoted_tweet?.id_str);
  const candidates = fx ? t.media?.all : t.mediaDetails ?? t.photos?.map((m) => ({ ...m, type: 'photo' }));
  const media = Array.isArray(candidates) ? candidates : [];
  const urls = [];
  const types = [];
  for (const m of media) {
    let url = fx ? m.url : m.media_url_https ?? m.url;
    const variants = m.video_info?.variants ?? m.video?.variants ?? [];
    const best = (Array.isArray(variants) ? variants : []).filter((v) => (v.content_type ?? v.type) === 'video/mp4')
      .sort((a, b) => (b.bitrate ?? 0) - (a.bitrate ?? 0))[0];
    if (best) url = best.url ?? best.src;
    if (typeof url === 'string') { urls.push(url); types.push(m.type ?? 'photo'); }
  }
  Object.assign(row, {
    fecha: date(t.created_at), user: '@' + handle, idioma: t.lang ?? null,
    respuestas: number(fx ? t.replies : t.conversation_count), retweets: number(fx ? t.retweets : t.retweet_count),
    citas: number(fx ? t.quotes : t.quote_count), megustas: number(fx ? t.likes : t.favorite_count), views: number(t.views),
    hashtags: extractHashtags(t.text), menciones: [...t.text.matchAll(/@([A-Za-z0-9_]+)/g)].map((m) => m[1]),
    urls_externas: (t.entities?.urls ?? []).map((u) => u.expanded_url).filter((u) => typeof u === 'string'),
    media: urls, media_tipo: types, es_retweet: t.is_retweet ?? null, es_cita: !!quoteId,
    tweet_citado_id: quoteId, conversation_id: idOf(t.conversation_id ?? t.conversation_id_str),
    url: `https://x.com/${handle}/status/${id}`, tweet_id: id, user_id: idOf(author?.id ?? author?.id_str),
    respuesta_a_id: idOf(fx ? t.replying_to_status : t.in_reply_to_status_id_str),
    respuesta_a_user: typeof t.replying_to === 'string' ? '@' + t.replying_to.replace(/^@/, '') : null,
    sensible: t.possibly_sensitive ?? null, editado: null,
  });
  return row;
}

function inaccessible(response, body) {
  return [401, 403, 404, 410].includes(response.status) || [401, 403, 404, 410].includes(Number(body?.code)) ||
    body?.tweet?.author?.protected === true || body?.user?.protected === true ||
    body?.__typename === 'TweetTombstone' ||
    /\b(private|protected|deleted|not found|unavailable|suspended|tombstone)\b/i.test(String(body?.message ?? body?.error ?? body?.__typename ?? ''));
}

export async function fetchPublicTweet(id, { fetch: request = globalThis.fetch, signal, warn = () => {} } = {}) {
  const endpoints = [
    ['fxtwitter', `https://api.fxtwitter.com/status/${id}`],
    ['syndication', `https://cdn.syndication.twimg.com/tweet-result?id=${id}&token=${syndicationToken(id)}`],
  ];
  for (const [provider, url] of endpoints) {
    signal?.throwIfAborted();
    let response;
    let body;
    try {
      response = await request(url, { headers: { accept: 'application/json' }, credentials: 'omit', redirect: 'error',
        signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(20000)]) : AbortSignal.timeout(20000) });
      try { body = await response.json(); } catch { body = null; }
    } catch (e) {
      if (signal?.aborted) throw e;
      warn(`${provider}: fallo de red; se intentará el siguiente proveedor si existe.`);
      continue;
    }
    if (inaccessible(response, body)) throw new Error('Tweet privado, protegido, eliminado o inaccesible; no se intentarán otros proveedores.');
    const row = response.ok ? publicTweetRow(provider === 'fxtwitter' ? body?.tweet : body, provider, id) : null;
    if (!row) { warn(`${provider}: respuesta no utilizable (${response.status}); se intentará el siguiente proveedor si existe.`); continue; }
    warn(`${provider}: lectura pública degradada; métricas, contexto, hilo y Articles pueden estar incompletos o desactualizados.`);
    return { row, provider };
  }
  throw new Error('Ningún proveedor público pudo devolver el tweet solicitado.');
}
