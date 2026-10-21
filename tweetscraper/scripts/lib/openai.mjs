// Sentiment and image analysis through the OpenAI chat completions API
// (getTweetsSentiments, getTweetsImagesAnalysis). Same prompts, models and
// response schemas as TweetScraperR, so results are comparable.
import fs from 'node:fs';
import path from 'node:path';
import { SENTIMENT_PROMPT, IMAGE_PROMPT } from './prompts.mjs';

// OPENAI_BASE_URL points to any OpenAI-compatible endpoint (Azure gateway, local proxy...).
const api = () => (process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/+$/, '') + '/chat/completions';

export function apiKey(explicit) {
  const k = explicit || process.env.OPENAI_API_KEY;
  if (!k) throw new Error('An OpenAI API key is required: set OPENAI_API_KEY in the environment.');
  return k;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** POST to chat completions; returns the first choice content. Retries 429/5xx (Retry-After honored). */
export async function chat(body, key, { timeout = 300, retries = 3 } = {}) {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(api(), {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeout * 1000),
    });
    if (res.ok) {
      const j = await res.json();
      return j.choices?.[0]?.message?.content ?? null;
    }
    const text = await res.text().catch(() => '');
    if ((res.status === 429 || res.status >= 500) && attempt < retries) {
      const ra = Number(res.headers.get('retry-after'));
      await sleep((Number.isFinite(ra) && ra > 0 ? ra : 2 ** attempt * 2) * 1000);
      continue;
    }
    throw new Error(`OpenAI HTTP ${res.status}: ${text.slice(0, 200)}`);
  }
}

/** Runs `fn` over `items` with at most `concurrency` in flight; `onResult(i, value)` as each finishes. */
export async function mapLimit(items, concurrency, fn, onResult = () => {}) {
  const out = new Array(items.length);
  let next = 0;
  const worker = async () => {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i], i);
      onResult(i, out[i]);
    }
  };
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, worker));
  return out;
}

const SENTIMENT_FIELDS = ['tono', 'sentimiento', 'expresiones_de_odio', 'direccionado', 'llama_a_accion', 'explicacion'];

/** Classifies one tweet. `item` = {tweet, tweet_id?, url?}. Failures keep the row with nulls and `error`. */
export async function analyzeTweet(item, { key, model = 'gpt-4o-mini' }) {
  const base = { ...(item.tweet_id ? { tweet_id: item.tweet_id } : {}), ...(item.url ? { url: item.url } : {}), tweet: item.tweet };
  try {
    const content = await chat(
      {
        model,
        messages: [
          { role: 'system', content: SENTIMENT_PROMPT },
          { role: 'user', content: item.tweet },
        ],
        response_format: { type: 'json_object' },
      },
      key
    );
    const j = JSON.parse(content);
    return { ...base, ...Object.fromEntries(SENTIMENT_FIELDS.map((f) => [f, j[f] ?? null])) };
  } catch (e) {
    return { ...base, ...Object.fromEntries(SENTIMENT_FIELDS.map((f) => [f, null])), error: e.message };
  }
}

const IMAGE_SCHEMA = {
  type: 'object',
  properties: {
    clasificacion: { type: 'string' },
    contiene_texto: { type: 'boolean' },
    texto_contenido: { type: 'string' },
    contenido_discriminatorio: { type: 'boolean' },
    contenido_violento: { type: 'boolean' },
    contenido_pornografico: { type: 'boolean' },
    contenido_inapropiado: { type: 'boolean' },
    descripcion: { type: 'string' },
    palabras_clave: { type: 'string' },
  },
  required: [
    'clasificacion', 'contiene_texto', 'texto_contenido', 'contenido_discriminatorio', 'contenido_violento',
    'contenido_pornografico', 'contenido_inapropiado', 'descripcion', 'palabras_clave',
  ],
  additionalProperties: false,
};

const MIME = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp' };

/** Local file -> data URL; remote URL -> itself if it answers 200. Returns {data, img} or throws. */
export async function imageSource(src) {
  if (fs.existsSync(src)) {
    const mime = MIME[path.extname(src).toLowerCase()] || 'image/jpeg';
    return { data: `data:${mime};base64,${fs.readFileSync(src).toString('base64')}`, img: path.resolve(src) };
  }
  if (!/^https?:\/\//i.test(src)) throw new Error('file not found');
  const res = await fetch(src, { method: 'HEAD', signal: AbortSignal.timeout(60000) });
  // Some servers reject HEAD (405) yet serve the image.
  if (!res.ok && res.status !== 405) throw new Error(`URL answered HTTP ${res.status}`);
  return { data: src, img: src };
}

/** Classifies one image. `item` = {src, tweet_url?}. Failures keep the row with nulls and `error`. */
export async function analyzeImage(item, { key, model = 'gpt-4o-mini' }) {
  const empty = Object.fromEntries(Object.keys(IMAGE_SCHEMA.properties).map((k) => [k, null]));
  const extra = item.tweet_url ? { tweet_url: item.tweet_url } : {};
  let source;
  try {
    source = await imageSource(item.src);
  } catch (e) {
    return { ...empty, img: item.src, ...extra, error: 'invalid image source: ' + e.message };
  }
  try {
    const content = await chat(
      {
        model,
        messages: [
          { role: 'system', content: IMAGE_PROMPT },
          { role: 'user', content: [{ type: 'image_url', image_url: { url: source.data } }] },
        ],
        response_format: { type: 'json_schema', json_schema: { name: 'tweet_images_analysis', strict: true, schema: IMAGE_SCHEMA } },
        temperature: 0,
        max_tokens: 2048,
        top_p: 0,
        frequency_penalty: 0,
        presence_penalty: 0,
      },
      key
    );
    return { ...empty, ...JSON.parse(content), img: source.img, ...extra };
  } catch (e) {
    return { ...empty, img: source.img, ...extra, error: e.message };
  }
}

/** Photos of a tweets dataset (videos and gifs excluded: the vision API takes still images), deduplicated. */
export function photosOf(rows) {
  const seen = new Set();
  const out = [];
  for (const r of rows) {
    (r.media || []).forEach((u, i) => {
      if (u && (r.media_tipo?.[i] ?? 'photo') === 'photo' && !seen.has(u)) {
        seen.add(u);
        out.push({ src: u, tweet_url: r.url ?? null });
      }
    });
  }
  return out;
}
