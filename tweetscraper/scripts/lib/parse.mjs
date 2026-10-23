// Parsers for the GraphQL JSON that x.com's web app receives.
//
// Ported from TweetScraperR (R/getUserTweetsAPI.R, R/api-users.R). Field names
// are kept identical to the R package so data stays interchangeable between
// both tools (a JSONL written here reads into R with the same columns).

const MONTHS = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };

const pad = (n) => String(n).padStart(2, '0');

/** "Wdy Mon DD HH:MM:SS +0000 YYYY" -> "YYYY-MM-DDTHH:MM:SSZ" (UTC), or null. */
export function parseTwitterDate(x) {
  if (typeof x !== 'string' || !x) return null;
  const m = /^\w+ (\w+) (\d+) (\d+):(\d+):(\d+) [+-]\d+ (\d+)$/.exec(x);
  if (!m || !MONTHS[m[1]]) return null;
  return `${m[6]}-${pad(MONTHS[m[1]])}-${pad(+m[2])}T${m[3]}:${m[4]}:${m[5]}Z`;
}

/** Unix milliseconds (as X sends them, often a string) -> ISO UTC. Negative = hidden by X -> null. */
export function parseMsec(x) {
  const ms = Number(x);
  if (x == null || x === '' || !Number.isFinite(ms) || ms < 0) return null;
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

/** Depth-first search for the first `instructions` array (its path differs per endpoint). */
export function findInstructions(x) {
  if (!x || typeof x !== 'object') return null;
  if (Array.isArray(x.instructions)) return x.instructions;
  for (const v of Object.values(x)) {
    const r = findInstructions(v);
    if (r) return r;
  }
  return null;
}

const int = (x) => {
  if (x == null || x === '') return null;
  const n = Number(x);
  return Number.isFinite(n) ? Math.trunc(n) : null;
};

const entityVec = (items, field) =>
  Array.isArray(items) ? items.map((e) => e && e[field]).filter((v) => typeof v === 'string') : [];

const unwrap = (t) => (t && t.__typename === 'TweetWithVisibilityResults' ? t.tweet : t);

/** Media URLs and types; for videos/gifs the highest-bitrate mp4. */
export function extractMedia(lg) {
  const media = lg?.extended_entities?.media ?? lg?.entities?.media;
  const urls = [];
  const tipos = [];
  for (const m of Array.isArray(media) ? media : []) {
    const tipo = m.type || 'photo';
    let url = m.media_url_https ?? null;
    if ((tipo === 'video' || tipo === 'animated_gif') && m.video_info?.variants?.length) {
      const mp4 = m.video_info.variants.filter((v) => v.content_type === 'video/mp4');
      if (mp4.length) url = mp4.reduce((a, b) => ((b.bitrate || 0) > (a.bitrate || 0) ? b : a)).url;
    }
    urls.push(url);
    tipos.push(tipo);
  }
  return { urls, tipos };
}

const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' });
const RGI_EMOJI = /^\p{RGI_Emoji}$/v;

/**
 * Emojis of a text, one entry per occurrence. Works on grapheme clusters, so
 * ZWJ sequences, skin tones, flags and keycaps count as a single emoji.
 */
export function extractEmojis(text) {
  if (typeof text !== 'string' || !text) return [];
  const out = [];
  for (const { segment } of segmenter.segment(text)) if (RGI_EMOJI.test(segment)) out.push(segment);
  return out;
}

/** Hashtags written in a text, without the leading "#" (same form as the entities column). */
export function extractHashtags(text) {
  if (typeof text !== 'string' || !text) return [];
  return [...text.matchAll(/#([\p{L}\p{N}_]+)/gu)].map((m) => m[1]);
}

/** Readable label of `source` ('<a href="...">Twitter for iPhone</a>'). */
export function sourceLabel(src) {
  if (typeof src !== 'string' || !src) return null;
  const m = /^.*>([^<]*)<.*$/s.exec(src);
  return m ? m[1] : src;
}

/**
 * One tweet record from a `tweet_results.result` object, or null.
 * Long tweets (> 280 chars) carry only the beginning in legacy.full_text: the
 * full text and its entities live in note_tweet.
 */
export function tweetRow(tr) {
  tr = unwrap(tr);
  const lg = tr?.legacy;
  if (!lg || typeof lg.full_text !== 'string') return null;
  const core = tr.core?.user_results?.result;
  const handle = core?.core?.screen_name ?? core?.legacy?.screen_name ?? null;
  const tid = tr.rest_id ?? lg.id_str ?? null;
  const note = tr.note_tweet?.note_tweet_results?.result;
  const texto = note?.text ?? lg.full_text;
  const ent = note?.entity_set ?? lg.entities;
  const med = extractMedia(lg);
  const qr = unwrap(tr.quoted_status_result?.result);
  const rt = unwrap(lg.retweeted_status_result?.result);
  const replyTo = lg.in_reply_to_screen_name;
  return {
    fecha: parseTwitterDate(lg.created_at),
    user: handle ? '@' + handle : null,
    texto,
    idioma: lg.lang ?? null,
    respuestas: int(lg.reply_count),
    retweets: int(lg.retweet_count),
    citas: int(lg.quote_count),
    megustas: int(lg.favorite_count),
    views: int(tr.views?.count),
    emoticones: extractEmojis(texto),
    hashtags: entityVec(ent?.hashtags, 'text'),
    menciones: entityVec(ent?.user_mentions, 'screen_name'),
    urls_externas: entityVec(ent?.urls, 'expanded_url'),
    media: med.urls,
    media_tipo: med.tipos,
    es_retweet: lg.retweeted_status_result != null,
    es_cita: lg.is_quote_status === true,
    tweet_citado_id: qr?.rest_id ?? null,
    conversation_id: lg.conversation_id_str ?? null,
    url: handle ? `https://x.com/${handle}/status/${tid}` : null,
    tweet_id: tid,
    user_id: core?.rest_id ?? lg.user_id_str ?? null,
    respuesta_a_id: lg.in_reply_to_status_id_str ?? null,
    respuesta_a_user: replyTo ? '@' + replyTo : null,
    retweet_id: rt?.rest_id ?? null,
    guardados: int(lg.bookmark_count),
    fuente: sourceLabel(tr.source),
    sensible: lg.possibly_sensitive === true,
    editado: (tr.edit_control?.edit_tweet_ids?.length ?? 0) > 1,
    lugar: lg.place?.full_name ?? null,
    pais: lg.place?.country ?? null,
  };
}

export const TWEET_FIELDS = Object.keys(tweetRow({ legacy: { full_text: '' } }));

/** tweet_results of an entry: direct, or nested in a conversationthread module. */
function entryTweetResults(e) {
  const out = [];
  const tr = e?.content?.itemContent?.tweet_results?.result;
  if (tr) out.push(tr);
  for (const it of e?.content?.items ?? []) {
    const tr2 = it?.item?.itemContent?.tweet_results?.result;
    if (tr2) out.push(tr2);
  }
  return out;
}

/** Tweets and bottom cursor of a timeline response (UserTweets, SearchTimeline, TweetDetail...). */
export function parseTimelineTweets(doc) {
  const insts = findInstructions(doc);
  const tweets = [];
  let cursor = null;
  for (const ins of insts ?? []) {
    for (const e of ins.entries ?? []) {
      if (/^cursor-bottom/.test(e?.entryId ?? '')) {
        cursor = e.content?.value ?? cursor;
        continue;
      }
      for (const tr of entryTweetResults(e)) {
        const row = tweetRow(tr);
        if (row) tweets.push(row);
      }
    }
  }
  return { tweets, cursor };
}

/** Thread roles are independent of timeline ordering and never include quoted tweets. */
export function reconstructThread(tweets, requestedId) {
  const byId = new Map(tweets.filter((t) => t.tweet_id).map((t) => [t.tweet_id, t]));
  const focal = byId.get(requestedId);
  if (!focal) throw new Error('No se pudo recuperar el tweet focal.');
  const ancestors = new Set();
  let parent = focal.respuesta_a_id;
  while (parent && byId.has(parent) && parent !== requestedId && !ancestors.has(parent)) {
    ancestors.add(parent);
    parent = byId.get(parent).respuesta_a_id;
  }
  const continuation = new Set([requestedId]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const t of byId.values()) {
      const sameAuthor = focal.user_id && t.user_id ? focal.user_id === t.user_id : focal.user && focal.user === t.user;
      if (sameAuthor && continuation.has(t.respuesta_a_id) && !continuation.has(t.tweet_id)) {
        continuation.add(t.tweet_id);
        changed = true;
      }
    }
  }
  const rows = [...byId.values()].map((t) => ({ ...t, rol: t.tweet_id === requestedId ? 'focal' :
    ancestors.has(t.tweet_id) ? 'antecedente' : continuation.has(t.tweet_id) ? 'continuacion' : 'respuesta' }));
  rows.sort((a, b) => (a.fecha ?? '').localeCompare(b.fecha ?? '') ||
    (BigInt(a.tweet_id) < BigInt(b.tweet_id) ? -1 : BigInt(a.tweet_id) > BigInt(b.tweet_id) ? 1 : 0));
  const rootId = focal.conversation_id ?? (parent || [...ancestors].at(-1)) ?? requestedId;
  return { rows, rootId, missingParent: parent, continuation };
}

/** Articles have their own schema: a preview is never passed off as a full body. */
export function parseArticles(doc) {
  const out = new Map();
  function walk(value, author = null, tweetId = null) {
    if (!value || typeof value !== 'object') return;
    if (value.legacy?.full_text != null) {
      const user = value.core?.user_results?.result;
      author = user?.core?.screen_name ?? user?.legacy?.screen_name ?? author;
      tweetId = value.rest_id ?? tweetId;
    }
    const state = value.content_state;
    const isArticle = typeof value.title === 'string' || state?.blocks || typeof value.preview_text === 'string';
    if (isArticle && value.rest_id) {
      const blocks = Array.isArray(state?.blocks) ? state.blocks : [];
      const entityMap = Array.isArray(state?.entityMap)
        ? Object.fromEntries(state.entityMap.map((e, i) => [String(e?.key ?? i), e?.value ?? e]))
        : state?.entityMap ?? {};
      const body = blocks.length ? blocks.map((b) => b.text ?? '').join('\n\n') : value.plain_text || null;
      const media = (value.media_entities ?? []).map((m) => {
        const info = m.media_info ?? {};
        const variants = info.variants ?? info.video_info?.variants ?? [];
        const video = variants.filter((v) => v.content_type === 'video/mp4')
          .sort((a, b) => (b.bitrate ?? 0) - (a.bitrate ?? 0))[0];
        return { id: String(m.media_id ?? m.id ?? ''), url: video?.url ?? info.original_img_url ?? info.url ?? null,
          tipo: video ? 'video' : 'photo' };
      }).filter((m) => m.url);
      const row = {
        article_id: String(value.rest_id), tweet_id: tweetId, user: author ? '@' + author : null,
        url: `https://x.com/i/article/${value.rest_id}`, fecha: parseMsec(value.created_at_secs == null ? null : value.created_at_secs * 1000),
        titulo: value.title ?? null, portada: value.cover_media?.media_info?.original_img_url ?? null,
        texto: body, preview: value.preview_text ?? null, estado_cuerpo: body ? 'completo' : 'preview',
        bloques: blocks, entidades: entityMap,
        enlaces: Object.values(entityMap).filter((e) => String(e?.type).toUpperCase() === 'LINK')
          .map((e) => e.data?.url).filter((u) => typeof u === 'string'),
        media,
      };
      if (!out.has(row.article_id) || row.estado_cuerpo === 'completo') out.set(row.article_id, row);
      return;
    }
    for (const [key, child] of Object.entries(value)) {
      if (key !== 'note_tweet' && key !== 'quoted_status_result' && key !== 'retweeted_status_result') walk(child, author, tweetId);
    }
  }
  walk(doc);
  return [...out.values()];
}

/**
 * One user record from a `user_results.result` object, or null.
 * Since 2026-10 X dropped the user `legacy` block: counts live in
 * relationship_counts / tweet_counts / action_counts, bio in profile_bio.
 * legacy fallbacks stay in case both schemas coexist during the rollout.
 */
export function userRow(ur) {
  if (!ur) return null;
  const rc = ur.relationship_counts;
  const tc = ur.tweet_counts;
  const ac = ur.action_counts;
  const pb = ur.profile_bio;
  const lg = ur.legacy;
  const cr = ur.core;
  const handle = cr?.screen_name ?? lg?.screen_name;
  if (!handle) return null;
  const web = entityVec(pb?.entities?.url?.urls ?? lg?.entities?.url?.urls, 'expanded_url');
  const vtype = ur.verification?.verified_type;
  return {
    user: '@' + handle,
    nombre: cr?.name ?? lg?.name ?? null,
    user_id: ur.rest_id ?? null,
    descripcion: pb?.description ?? lg?.description ?? null,
    seguidores: int(rc?.followers ?? lg?.followers_count),
    siguiendo: int(rc?.following ?? lg?.friends_count),
    tweets: int(tc?.tweets ?? lg?.statuses_count),
    favoritos: int(ac?.favorites_count ?? lg?.favourites_count),
    verificado: ur.is_blue_verified === true || !!vtype || lg?.verified === true,
    ubicacion: ur.location?.location ?? lg?.location ?? null,
    sitio_web: web[0] ?? ur.website?.url ?? null,
    imagen_perfil: ur.avatar?.image_url ?? lg?.profile_image_url_https ?? null,
    banner: ur.banner?.image_url ?? lg?.profile_banner_url ?? null,
    fecha_creacion: parseTwitterDate(cr?.created_at ?? lg?.created_at),
    url: 'https://x.com/' + handle,
    tweets_media: int(tc?.media_tweets ?? lg?.media_count),
    protegida: (ur.privacy?.protected ?? lg?.protected) === true,
    tipo_verificacion: vtype || null,
  };
}

export const USER_FIELDS = Object.keys(userRow({ core: { screen_name: 'x' } }));

/** Users and bottom cursor of a user-timeline response (Followers, Following, Retweeters...). */
export function parseUsers(doc) {
  const insts = findInstructions(doc);
  const users = [];
  let cursor = null;
  for (const ins of insts ?? []) {
    for (const e of ins.entries ?? []) {
      if (/^cursor-bottom/.test(e?.entryId ?? '')) {
        cursor = e.content?.value ?? cursor;
        continue;
      }
      const row = userRow(e?.content?.itemContent?.user_results?.result);
      if (row) users.push(row);
    }
  }
  return { users, cursor };
}

const bool = (x) => (x == null ? null : x === true || x === 'true');

/** "About this account" record (AboutAccountQuery), or null. */
export function aboutRow(ur) {
  const handle = ur?.core?.screen_name;
  if (!handle) return null;
  const ab = ur.about_profile;
  const vi = ur.verification_info;
  return {
    user: '@' + handle,
    nombre: ur.core.name ?? null,
    user_id: ur.rest_id ?? null,
    pais_cuenta: ab?.account_based_in ?? null,
    ubicacion_precisa: bool(ab?.location_accurate),
    cambios_usuario: int(ab?.username_changes?.count),
    ultimo_cambio_usuario: parseMsec(ab?.username_changes?.last_changed_at_msec),
    afiliada_a: ab?.affiliate_username ?? null,
    origen_cuenta: ab?.source ?? null,
    identidad_verificada: bool(vi?.is_identity_verified),
    verificada_desde: parseMsec(vi?.reason?.verified_since_msec),
    fecha_creacion: parseTwitterDate(ur.core.created_at),
    url: 'https://x.com/' + handle,
  };
}

export const ABOUT_FIELDS = Object.keys(aboutRow({ core: { screen_name: 'x' } }));

/**
 * Cheap scan used while harvesting (progress + stop target): counts new tweets
 * and users by rest_id and keeps the last bottom cursor. It does not descend
 * into quoted tweets or retweet originals, so they never count as results.
 */
export function scanBody(doc, seenTweets, seenUsers) {
  const out = { last: null, tweets: 0, users: 0, cursor: null };
  const walk = (o) => {
    if (!o || typeof o !== 'object') return;
    if (Array.isArray(o)) {
      for (const x of o) walk(x);
      return;
    }
    if (o.cursorType === 'Bottom' && typeof o.value === 'string') out.cursor = o.value;
    if (o.rest_id && typeof o.legacy?.full_text === 'string') {
      if (!seenTweets.has(o.rest_id)) {
        seenTweets.add(o.rest_id);
        out.tweets++;
        const u = o.core?.user_results?.result;
        const sn = u?.core?.screen_name ?? u?.legacy?.screen_name;
        out.last = (sn ? '@' + sn + ': ' : '') + o.legacy.full_text;
      }
    } else if (o.__typename === 'User' && o.rest_id && !seenUsers.has(o.rest_id)) {
      seenUsers.add(o.rest_id);
      out.users++;
    }
    for (const k in o) if (k !== 'quoted_status_result' && k !== 'retweeted_status_result') walk(o[k]);
  };
  walk(doc);
  return out;
}
