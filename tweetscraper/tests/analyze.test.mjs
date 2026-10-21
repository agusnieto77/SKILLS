import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { timeCounts, wordCounts, emojiCounts, hashtagCounts, withHashtags, summarize, tokenize } from '../scripts/lib/analyze.mjs';
import { readRows, writeRows } from '../scripts/lib/io.mjs';
import { classify, withCursor, parseProxy, opOf } from '../scripts/lib/engine.mjs';
import { handle, tweetUrl, listId, maxStatusId, searchUrl } from '../scripts/lib/collect.mjs';
import { wordCloud } from '../scripts/lib/charts.mjs';

test('timeCounts buckets in UTC, fills empty buckets and starts weeks on Sunday', () => {
  const rows = [
    { fecha: '2026-06-01T10:15:00Z' },
    { fecha: '2026-06-01T10:59:59Z' },
    { fecha: '2026-06-01T13:00:00Z' },
    { fecha: null },
  ];
  assert.deepEqual(timeCounts(rows, 'hour'), [
    { fecha: '2026-06-01T10:00', n: 2 },
    { fecha: '2026-06-01T11:00', n: 0 },
    { fecha: '2026-06-01T12:00', n: 0 },
    { fecha: '2026-06-01T13:00', n: 1 },
  ]);
  // 2026-06-01 is a Monday -> week of Sunday 2026-05-31; 2026-06-07 is Sunday.
  assert.deepEqual(timeCounts([{ fecha: '2026-06-01T00:00:00Z' }, { fecha: '2026-06-07T00:00:00Z' }], 'week'), [
    { fecha: '2026-05-31', n: 1 },
    { fecha: '2026-06-07', n: 1 },
  ]);
  assert.deepEqual(timeCounts([{ fecha: '2025-12-31T23:00:00Z' }, { fecha: '2026-02-01T00:00:00Z' }], 'month').map((d) => d.fecha), ['2025-12', '2026-01', '2026-02']);
  assert.throws(() => timeCounts(rows, 'minute'), /group must be/);
  assert.throws(() => timeCounts([{ texto: 'x' }], 'day'), /'fecha'/);
});

test('tokenize drops URLs, punctuation, numbers and stopwords but keeps hashtags and mentions', () => {
  const stop = new Set(['de', 'la']);
  assert.deepEqual(tokenize('La NASA lanzó 3 cohetes de #Artemis con @NASA_es https://t.co/abc ¡genial!', stop), [
    'nasa', 'lanzó', 'cohetes', '#artemis', 'con', '@nasa_es', 'genial',
  ]);
});

test('wordCounts applies language stopwords, extra stopwords and min frequency', () => {
  const rows = [{ texto: 'el datos y los datos' }, { texto: 'Datos abiertos para el pueblo' }, { texto: 'pueblo pueblo' }];
  assert.deepEqual(wordCounts(rows, { lang: 'es', minFreq: 2 }), [
    { word: 'datos', freq: 3 },
    { word: 'pueblo', freq: 3 },
  ]);
  assert.deepEqual(wordCounts(rows, { lang: 'es', minFreq: 1, sw: ['pueblo'], maxWords: 2 }).map((w) => w.word), ['datos', 'abiertos']);
  assert.throws(() => wordCounts(rows, { lang: 'zz' }), /No stopword list/);
});

test('emojiCounts uses the emoticones column, or extracts from text', () => {
  assert.deepEqual(emojiCounts([{ emoticones: ['😀', '😀'] }, { emoticones: ['🚀'] }], 1), [{ emoji: '😀', n: 2 }]);
  assert.deepEqual(emojiCounts([{ texto: '🚀 y 🚀 y 👩‍💻' }]), [{ emoji: '🚀', n: 2 }, { emoji: '👩‍💻', n: 1 }]);
});

test('hashtagCounts: entity column by default, text on request, optional case folding', () => {
  const rows = [{ texto: '#rstats', hashtags: ['RStats'] }, { texto: '#RStats #dataviz', hashtags: ['RStats', 'dataviz'] }];
  assert.deepEqual(hashtagCounts(rows), [{ hashtag: 'RStats', n: 2 }, { hashtag: 'dataviz', n: 1 }]);
  assert.deepEqual(hashtagCounts(rows, { fromText: true, ignoreCase: true }), [{ hashtag: 'rstats', n: 2 }, { hashtag: 'dataviz', n: 1 }]);
  assert.deepEqual(withHashtags([{ tweet: 'Un #tweet' }])[0].hashtags, ['tweet']);
  assert.throws(() => withHashtags([{ otro: 1 }]), /'texto' or 'tweet'/);
});

test('summarize recognizes tweets and users datasets', () => {
  const t = summarize([
    { tweet_id: '1', fecha: '2026-01-02T00:00:00Z', user: '@a', megustas: 5, retweets: 1, texto: 'x', hashtags: ['A'] },
    { tweet_id: '2', fecha: '2026-01-01T00:00:00Z', user: '@a', megustas: 9, retweets: 0, texto: 'y', hashtags: ['a'] },
  ]);
  assert.equal(t.kind, 'tweets');
  assert.deepEqual(t.fecha, { from: '2026-01-01T00:00:00Z', to: '2026-01-02T00:00:00Z' });
  assert.equal(t.totals.megustas, 14);
  assert.equal(t.top_by_megustas[0].megustas, 9);
  assert.deepEqual(t.top_hashtags, [{ hashtag: 'a', n: 2 }]);
  assert.equal(summarize([{ user: '@a', seguidores: 3 }]).kind, 'users');
});

test('CSV round trip keeps lists, numbers, booleans, commas, quotes and newlines', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-io-'));
  const rows = [
    { tweet_id: '1', texto: 'hola, "mundo"\nsegunda línea', megustas: 3, es_cita: true, hashtags: ['a', 'b'], lugar: null },
    { tweet_id: '2', texto: 'ñandú 🚀', megustas: 0, es_cita: false, hashtags: [], lugar: 'Mar del Plata' },
  ];
  for (const ext of ['csv', 'jsonl', 'json']) {
    const f = path.join(dir, 'd.' + ext);
    writeRows(f, rows);
    assert.deepEqual(readRows(f), rows, ext);
  }
});

test('classify follows the twscrape rules', () => {
  const h = (rem) => (rem == null ? {} : { 'x-rate-limit-remaining': String(rem) });
  assert.equal(classify(200, h(10), '{"data":{}}'), null);
  assert.equal(classify(429, h(), ''), 'rate_limited');
  assert.equal(classify(200, h(0), '{"data":{}}'), 'rate_limited');
  assert.equal(classify(200, h(5), '{"errors":[{"code":88}]}'), 'banned');
  assert.equal(classify(200, h(), '{"errors":[{"code":326}]}'), 'locked');
  assert.equal(classify(401, h(), ''), 'expired');
  assert.equal(classify(403, h(), ''), 'expired');
  assert.equal(classify(403, { 'content-type': 'text/html' }, '<html>'), 'blocked');
});

test('withCursor replaces only the cursor in the GraphQL variables', () => {
  const u = 'https://x.com/i/api/graphql/abc/SearchTimeline?variables=' + encodeURIComponent('{"rawQuery":"x","count":20}') + '&features=%7B%7D';
  const v = JSON.parse(new URL(withCursor(u, 'CUR')).searchParams.get('variables'));
  assert.deepEqual(v, { rawQuery: 'x', count: 20, cursor: 'CUR' });
  assert.equal(opOf(u), 'SearchTimeline');
});

test('parseProxy splits credentials for Chromium', () => {
  assert.deepEqual(parseProxy('http://u:p@h:1'), { server: 'http://h:1', username: 'u', password: 'p' });
  assert.deepEqual(parseProxy('u:p@w@h:1'), { server: 'h:1', username: 'u', password: 'p@w' });
  assert.deepEqual(parseProxy('http://h:1'), { server: 'http://h:1' });
});

test('input normalizers', () => {
  assert.equal(handle('@NASA'), 'NASA');
  assert.equal(handle('https://twitter.com/NASA/status/1'), 'NASA');
  assert.equal(tweetUrl('https://twitter.com/a/status/123?s=20'), 'https://x.com/a/status/123');
  assert.equal(tweetUrl('123'), 'https://x.com/i/status/123');
  assert.throws(() => tweetUrl('https://x.com/a'), /Unrecognized tweet URL/);
  assert.equal(listId('https://x.com/i/lists/53645372/members'), '53645372');
  assert.equal(maxStatusId([null, '999', '1000', '2111426246517072370', '2111426246517072369']), '2111426246517072370');
  assert.equal(searchUrl('#RStats lang:es', 'live'), 'https://x.com/search?q=%23RStats%20lang%3Aes&src=typed_query&f=live');
});

test('wordCloud is deterministic and accounts for every word', () => {
  const words = Array.from({ length: 60 }, (_, i) => ({ word: 'palabra' + i, freq: 60 - i }));
  const a = wordCloud(words);
  assert.equal(a.svg, wordCloud(words).svg);
  assert.equal(a.placed + a.dropped, 60);
  assert.ok(a.placed > 30);
});
