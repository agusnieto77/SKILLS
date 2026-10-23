import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import * as parse from '../scripts/lib/parse.mjs';
import * as io from '../scripts/lib/io.mjs';

process.env.TWEETSCRAPER_HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-reading-'));
const collect = await import('../scripts/lib/collect.mjs');
const pool = await import('../scripts/lib/pool.mjs');
const fixture = JSON.parse(fs.readFileSync(new URL('./fixtures/public_article.json', import.meta.url), 'utf8'));
const context = (fetch) => {
  const warnings = [];
  return { fetch, warnings, warn: (m) => warnings.push(m), log: () => {}, progress: () => {}, waitTimeout: 0 };
};
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
const rawTweet = (id, parent = null, author = 'ana') => ({ rest_id: id,
  core: { user_results: { result: { rest_id: author, core: { screen_name: author } } } },
  legacy: { full_text: 'Tweet ' + id, created_at: 'Fri Jun 12 21:22:33 +0000 2026', conversation_id_str: '1',
    in_reply_to_status_id_str: parent, in_reply_to_screen_name: parent ? 'ana' : null } });
const doc = (tweets, cursor = null) => ({ data: { instructions: [{ entries: [
  ...tweets.map((t) => ({ entryId: 'tweet-' + t.rest_id, content: { itemContent: { tweet_results: { result: t } } } })),
  ...(cursor ? [{ entryId: 'cursor-bottom-1', content: { value: cursor } }] : []),
] }] } });
function harvested(ctx, pages) {
  pool.importSession({ authToken: 'offline', ct0: 'offline', account: 'offline' });
  const calls = [];
  ctx.harvest = async (p) => {
    calls.push(p);
    const id = collect.statusId(p.urls[0]) ?? '800';
    const page = pages[id] ?? doc([]);
    return { results: [{ docs: [{ doc: page }], count: 1 }], rateLimits: {}, stopped: null };
  };
  return calls;
}

test('public tweet uses FxTwitter without session headers and preserves the 31 columns', async () => {
  const calls = [];
  const ctx = context(async (url, options) => { calls.push([url, options]); return json(fixture.fx); });
  ctx.cookies = 'never send this';
  const result = await collect.publicTweet(ctx, fixture.fx.tweet.id);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 'https://api.fxtwitter.com/status/' + fixture.fx.tweet.id);
  assert.equal(calls[0][1].credentials, 'omit');
  assert.equal(new Headers(calls[0][1].headers).has('cookie'), false);
  assert.equal(new Headers(calls[0][1].headers).has('authorization'), false);
  assert.deepEqual(Object.keys(result.rows[0]), parse.TWEET_FIELDS);
  assert.equal(result.rows[0].user, '@ana');
  assert.equal(result.rows[0].tweet_citado_id, '99');
  assert.equal(result.rows[0].guardados, null);
  assert.equal(result.meta.provider, 'fxtwitter');
  assert.ok(ctx.warnings.some((m) => /complet/i.test(m)));
});

test('public tweet computes a nonzero syndication token and reports fallback degradation', async () => {
  const calls = [];
  const ctx = context(async (url) => { calls.push(url); return calls.length === 1 ? json({}, 503) : json(fixture.syndication); });
  const result = await collect.publicTweet(ctx, fixture.fx.tweet.id);
  const url = new URL(calls[1]);
  assert.equal(url.hostname, 'cdn.syndication.twimg.com');
  assert.equal(url.searchParams.get('id'), fixture.fx.tweet.id);
  assert.match(url.searchParams.get('token'), /^[a-z0-9]+$/);
  assert.notEqual(url.searchParams.get('token'), '0');
  assert.equal(result.meta.provider, 'syndication');
  assert.equal(result.meta.degraded, true);
  assert.equal(result.rows[0].retweets, null);
  assert.equal(result.rows[0].fecha, '2026-06-12T21:22:33Z');
  assert.equal(result.rows[0].tweet_citado_id, '99');
  assert.ok(ctx.warnings.length >= 2);
});

for (const [status, body] of [[403, { message: 'Protected tweet' }], [404, { code: 404 }],
  [200, { code: 401, message: 'Private tweet' }], [200, { code: 200, tweet: { ...fixture.fx.tweet, author: { protected: true } } }]]) {
  test('public read stops on inaccessible content: ' + JSON.stringify(body), async () => {
    let count = 0;
    const ctx = context(async () => { count++; return json(body, status); });
    await assert.rejects(collect.publicTweet(ctx, '123'), /privad|proteg|elimin|acces/i);
    assert.equal(count, 1);
  });
}

test('public read rejects mismatched or malformed payloads and never falls back after cancellation', async () => {
  const ctx = context(async () => json({ tweet: { id: 'wrong', text: 'x' } }));
  await assert.rejects(collect.publicTweet(ctx, '123'), /proveedor|provider/i);
  const controller = new AbortController();
  controller.abort();
  ctx.signal = controller.signal;
  ctx.fetch = () => assert.fail('cancelled fetch');
  await assert.rejects(collect.publicTweet(ctx, '123'), /abort|cancel/i);
});

test('thread reconstructs missing ancestors and author continuation, deduplicates and sorts', async () => {
  const ctx = context();
  const calls = harvested(ctx, {
    3: doc([rawTweet('3', '2'), rawTweet('4', '3'), rawTweet('6', '3', 'beto'), rawTweet('4', '3')]),
    2: doc([rawTweet('2', '1')]), 1: doc([rawTweet('1')]),
    4: doc([rawTweet('4', '3'), rawTweet('5', '4')]), 5: doc([rawTweet('5', '4')]),
  });
  const result = await collect.thread(ctx, '3', 20, { maxDetails: 10 });
  assert.deepEqual(result.rows.map((r) => [r.tweet_id, r.rol]), [
    ['1', 'antecedente'], ['2', 'antecedente'], ['3', 'focal'], ['4', 'continuacion'], ['5', 'continuacion'], ['6', 'respuesta'],
  ]);
  assert.equal(result.meta.root_id, '1');
  assert.equal(result.meta.requested_id, '3');
  assert.equal(result.meta.truncated, false);
  assert.equal(calls.length, 5);
});

test('thread limits detail pages and output, keeps focal and warns on truncation and missing parent', async () => {
  const ctx = context();
  harvested(ctx, { 3: doc([rawTweet('3', '2'), rawTweet('4', '3'), rawTweet('5', '4')], 'MORE') });
  const result = await collect.thread(ctx, '3', 2, { maxDetails: 1 });
  assert.ok(result.rows.some((r) => r.rol === 'focal'));
  assert.equal(result.rows.length, 2);
  assert.equal(result.meta.truncated, true);
  assert.ok(ctx.warnings.length);
  await assert.rejects(collect.thread(ctx, '3', 0), /positive|positivo/);
});

test('thread returns partial data on subsequent failure and rejects absent focal', async () => {
  const ctx = context();
  harvested(ctx, { 3: doc([rawTweet('3', '2')]) });
  const original = ctx.harvest;
  ctx.harvest = (p) => p.urls[0].endsWith('/2') ? Promise.reject(new Error('offline interruption')) : original(p);
  const result = await collect.thread(ctx, '3', 10);
  assert.equal(result.meta.truncated, true);
  assert.equal(result.rows[0].tweet_id, '3');
  await assert.rejects(collect.thread(ctx, '999', 10), /focal/i);
});

test('Markdown export escapes hostile content, adds front matter, URLs, citations and full/compact formats', () => {
  const rows = [{ tweet_id: '3', user: '@ana', fecha: '2026-06-12T21:22:33Z', texto: '<script> [[destino]] ![x](file:///secret)',
    url: 'https://x.com/ana/status/3', tweet_citado_id: '2', megustas: 12, rol: 'focal' },
  { tweet_id: '2', user: '@beto', texto: 'Cita real', url: 'https://x.com/beto/status/2' }];
  const full = io.toMarkdown(rows, { query: 'a\n---\nmalicia', capturedAt: '2026-10-22T00:00:00Z' });
  assert.ok(full.startsWith('---\n'));
  assert.match(full, /capturado_en: "2026-10-22T00:00:00Z"/);
  assert.match(full, /https:\/\/x.com\/ana\/status\/3/);
  assert.match(full, /> Cita real/);
  assert.match(full, /Me gusta: 12/);
  assert.doesNotMatch(full, /<script>|\[\[destino\]\]/);
  assert.doesNotMatch(io.toMarkdown(rows, { style: 'compact' }), /Me gusta:/);
  assert.throws(() => io.toMarkdown(rows, { style: 'bad' }), /compact|full/);
  assert.equal(io.formatOf('note.md'), 'markdown');
});

test('media downloads are opt-in, bounded, type checked, relative and fail independently', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-md-'));
  const output = path.join(tmp, 'nota.md');
  const media = ['https://pbs.twimg.com/ok', 'https://pbs.twimg.com/html', 'https://pbs.twimg.com/large', 'https://evil.test/file'];
  const rows = [{ tweet_id: '1', texto: 'hola', media, media_tipo: ['photo', 'photo', 'photo', 'photo'] }];
  let calls = 0;
  const fetch = async (url, options) => {
    calls++;
    assert.equal(options.credentials, 'omit');
    if (url.endsWith('html')) return new Response('html', { headers: { 'content-type': 'text/html' } });
    return new Response(new Uint8Array(url.endsWith('large') ? 5 : 3), { headers: { 'content-type': 'image/jpeg' } });
  };
  await io.writeMarkdown(output, rows, { fetch });
  assert.equal(calls, 0);
  const result = await io.writeMarkdown(output, rows, { fetch, downloadMedia: true, maxMediaBytes: 4 });
  assert.equal(result.downloaded, 1);
  assert.equal(result.warnings.length, 3);
  assert.equal(calls, 3);
  assert.match(fs.readFileSync(output, 'utf8'), /!\[media\]\(nota_media\//);
  assert.equal(fs.readdirSync(path.join(tmp, 'nota_media')).length, 1);
  await assert.rejects(io.writeMarkdown('-', rows, { downloadMedia: true }), /archivo|file/i);
});

test('Articles preserve title, cover, blocks, links and media without confusing note_tweet or preview', () => {
  const tr = rawTweet('10');
  tr.article = { article_results: { result: fixture.article } };
  const result = parse.parseArticles(doc([tr]));
  assert.equal(result.length, 1);
  const a = result[0];
  assert.equal(a.article_id, '800');
  assert.equal(a.estado_cuerpo, 'completo');
  assert.equal(a.bloques.length, 4);
  assert.deepEqual(a.enlaces, ['https://example.org/datos']);
  assert.equal(a.media.length, 1);
  assert.match(io.toMarkdown(result), /## Sección/);
  assert.match(io.toMarkdown(result), /\[\*\*datos\*\*\]\(https:\/\/example.org\/datos\)/);
  assert.doesNotMatch(io.toMarkdown(result), /<script>/);
  const arr = structuredClone(tr);
  arr.article.article_results.result.content_state.entityMap = Object.values(fixture.article.content_state.entityMap);
  assert.deepEqual(parse.parseArticles(doc([arr]))[0].enlaces, a.enlaces);
  delete arr.article.article_results.result.content_state;
  const preview = parse.parseArticles(doc([arr]))[0];
  assert.equal(preview.estado_cuerpo, 'preview');
  assert.equal(preview.texto, null);
  assert.match(io.toMarkdown([preview]), /preview/i);
  delete tr.article;
  tr.note_tweet = { note_tweet_results: { result: { text: 'Esto es un tweet largo' } } };
  assert.deepEqual(parse.parseArticles(doc([tr])), []);
});

test('article collector harvests actual Article and linked Article pages, reporting previews', async () => {
  const ctx = context();
  const tr = rawTweet('10');
  tr.article = { article_results: { result: { rest_id: '800', title: 'Adelanto', preview_text: 'preview' } } };
  const calls = harvested(ctx, { 10: doc([tr]), 800: { data: { article: { article_results: { result: fixture.article } } } } });
  const result = await collect.article(ctx, 'https://x.com/ana/status/10');
  assert.equal(result.rows[0].estado_cuerpo, 'completo');
  assert.equal(calls.length, 2);
  assert.ok(calls[1].opNames.includes('TweetResultByRestId'));
  assert.ok(calls[1].opNames.includes('ArticleEntityResultByRestId'));
});

test('Article preview remains partial and note_tweet alone never becomes an Article', async () => {
  const ctx = context();
  harvested(ctx, { 800: { result: { rest_id: '800', title: 'Adelanto', preview_text: 'No es el cuerpo' } } });
  const result = await collect.article(ctx, 'https://x.com/i/article/800');
  assert.equal(result.meta.partial, true);
  assert.equal(result.rows[0].texto, null);
  assert.ok(ctx.warnings.some((w) => /preview/.test(w)));
  await assert.rejects(collect.article(ctx, 'https://x.com/i/article/999'), /Article/);
});

test('Article entityMap key/value lists, overlapping ranges and invalid URLs remain safe', () => {
  const article = structuredClone(fixture.article);
  article.content_state.entityMap = Object.entries(article.content_state.entityMap).map(([key, value]) => ({ key, value }));
  article.content_state.blocks.push({ type: 'unstyled', text: 'No ejecutar', entityRanges: [{ offset: 0, length: 11, key: 2 }] });
  article.content_state.entityMap.push({ key: 2, value: { type: 'LINK', data: { url: 'javascript:alert(1)' } } });
  const row = parse.parseArticles({ article })[0];
  const markdown = io.toMarkdown([row]);
  assert.match(markdown, /https:\/\/example.org\/datos/);
  assert.doesNotMatch(markdown, /javascript:/);
});

test('media rejects announced sizes, empty payloads, redirects and fetch errors independently', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-media-'));
  const rows = [{ media: ['size', 'empty', 'redirect', 'network'].map((s) => 'https://pbs.twimg.com/' + s) }];
  const result = await io.writeMarkdown(path.join(tmp, 'note.md'), rows, { downloadMedia: true, maxMediaBytes: 4,
    fetch: async (url) => {
      if (url.endsWith('network')) throw new Error('offline');
      if (url.endsWith('redirect')) return new Response(null, { status: 302, headers: { location: 'https://evil.test/' } });
      return new Response(url.endsWith('empty') ? null : 'abc', { headers: {
        'content-type': 'image/jpeg', ...(url.endsWith('size') ? { 'content-length': '5' } : {}),
      } });
    } });
  assert.equal(result.downloaded, 0);
  assert.equal(result.warnings.length, 4);
  assert.equal(fs.existsSync(path.join(tmp, 'note_media')), false);
});

test('convert CLI writes Markdown and rejects download flags for JSON', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-cli-'));
  const input = path.join(tmp, 'in.json');
  fs.writeFileSync(input, JSON.stringify([{ tweet_id: '1', texto: 'hola' }]));
  const cli = new URL('../scripts/tweetscraper.mjs', import.meta.url);
  const run = (...args) => spawnSync(process.execPath, [cli.pathname.replace(/^\/(\w:)/, '$1'), 'convert', '-i', input, ...args], { encoding: 'utf8' });
  const success = run('-o', path.join(tmp, 'note.md'), '--md-style', 'compact', '--query', 'ciencia');
  assert.equal(success.status, 0, success.stderr + success.stdout);
  assert.equal(JSON.parse(success.stdout).warnings.length, 0);
  const invalid = run('-o', path.join(tmp, 'out.json'), '--download-media');
  assert.equal(invalid.status, 1);
});
