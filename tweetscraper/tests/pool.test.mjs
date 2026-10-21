import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';

process.env.TWEETSCRAPER_HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'tws-pool-'));
const pool = await import('../scripts/lib/pool.mjs');
const { harvestPool, CollectError } = await import('../scripts/lib/collect.mjs');

const fx = (name) => JSON.parse(fs.readFileSync(new URL('./fixtures/' + name, import.meta.url), 'utf8'));

function reset() {
  for (const a of pool.all()) pool.remove(a.username);
}

const ctx = (harvest, extra = {}) => ({ waitTimeout: 0, harvest, log: () => {}, warn: () => {}, progress: () => {}, ...extra });

test('parseCookies reads the header, a JSON object and the Cookie-Editor array', () => {
  assert.deepEqual(pool.parseCookies('guest_id=1; auth_token=AAA; ct0=BBB'), { authToken: 'AAA', ct0: 'BBB' });
  assert.deepEqual(pool.parseCookies('{"auth_token":"A","ct0":"B"}'), { authToken: 'A', ct0: 'B' });
  assert.deepEqual(
    pool.parseCookies('[{"name":"ct0","value":"B"},{"name":"auth_token","value":"A"},{"name":"x","value":"y"}]'),
    { authToken: 'A', ct0: 'B' }
  );
});

test('checkProxy accepts host:port forms and rejects authenticated SOCKS5', () => {
  assert.equal(pool.checkProxy('http://u:p@host:8080'), 'http://u:p@host:8080');
  assert.equal(pool.checkProxy('u:p@host:8080'), 'u:p@host:8080');
  assert.equal(pool.checkProxy(''), null);
  assert.equal(pool.checkProxy('none'), null);
  assert.throws(() => pool.checkProxy('socks5://u:p@host:1080'), /SOCKS5/);
  assert.throws(() => pool.checkProxy('host-without-port'), /Unrecognized proxy/);
});

test('importSession writes a storageState with both cookies and re-import reactivates', () => {
  reset();
  pool.importSession({ authToken: 'A', ct0: 'B', account: 'uno' });
  const st = JSON.parse(fs.readFileSync(pool.get('uno').state_path, 'utf8'));
  assert.deepEqual(st.cookies.map((c) => [c.name, c.value, c.domain]), [['auth_token', 'A', '.x.com'], ['ct0', 'B', '.x.com']]);
  pool.disable('uno', 'SearchTimeline', 'expired');
  assert.equal(pool.get('uno').active, 0);
  pool.importSession({ authToken: 'A2', ct0: 'B2', account: 'uno' });
  assert.equal(pool.get('uno').active, 1);
  assert.equal(pool.get('uno').error_msg, null);
  assert.throws(() => pool.importSession({ authToken: '', ct0: 'B', account: 'x' }), /auth_token and ct0/);
});

test('locks are per operation and acquisition picks the least recently used account', () => {
  reset();
  pool.importSession({ authToken: 'a', ct0: 'a', account: 'a' });
  pool.importSession({ authToken: 'b', ct0: 'b', account: 'b' });
  const first = pool.acquire('SearchTimeline');
  const second = pool.acquire('SearchTimeline');
  assert.notEqual(first.username, second.username);
  assert.equal(pool.acquire('SearchTimeline'), null); // both held
  assert.ok(pool.acquire('UserOriginalsTimeline')); // other op is free
  pool.release(first.username, 'SearchTimeline', pool.now() + 600, 3);
  pool.release(second.username, 'SearchTimeline');
  assert.equal(pool.acquire('SearchTimeline').username, second.username); // first is paused
  const d = pool.describe().find((r) => r.cuenta === first.username);
  assert.match(d.pausas, /^SearchTimeline until /);
  assert.equal(d.requests, 3);
  pool.resetLocks();
  assert.ok(pool.acquire('SearchTimeline'));
});

test('dedupe keeps the newest entry of the same X account, merging locks (max) and stats (sum)', () => {
  reset();
  pool.importSession({ authToken: 'o', ct0: 'o', account: 'old' });
  pool.release('old', 'Followers', pool.now() + 1000, 5);
  pool.importSession({ authToken: 'n', ct0: 'n', account: 'new' });
  pool.release('new', 'Followers', 0, 2);
  pool.markValid('old', 'same');
  pool.markValid('new', 'same');
  const oldState = pool.get('old').state_path;
  // added_at has 1 s resolution: make "new" strictly newer.
  const raw = new DatabaseSync(path.join(process.env.TWEETSCRAPER_HOME, 'accounts.sqlite'));
  raw.prepare('UPDATE accounts SET added_at = added_at - 10 WHERE username = ?').run('old');
  raw.close();
  assert.deepEqual(pool.dedupe('same'), ['old']);
  const left = pool.describe();
  assert.equal(left.length, 1);
  assert.equal(left[0].cuenta, 'new');
  assert.equal(left[0].requests, 7);
  assert.match(left[0].pausas, /Followers until/);
  assert.equal(fs.existsSync(oldState), false);
});

const page = (fixture) => ({ op: 'UserOriginalsTimeline', doc: fx(fixture) });

test('rotation: a quota stop pauses the account and the next one resumes from the saved cursor', async () => {
  reset();
  pool.importSession({ authToken: 'a', ct0: 'a', account: 'a' });
  pool.importSession({ authToken: 'b', ct0: 'b', account: 'b' });
  const calls = [];
  const reset_at = pool.now() + 800;
  const harvest = async (p) => {
    calls.push(p);
    if (calls.length === 1) {
      return {
        results: [{ url: p.urls[0], docs: [page('user_tweets.json')], cursor: 'CURSOR_ABC', count: 2 }],
        rateLimits: { UserOriginalsTimeline: { remaining: 0, limit: 50, reset: reset_at } },
        stopped: 'rate_limited', stoppedOp: 'UserOriginalsTimeline', stoppedAt: 0,
      };
    }
    return {
      results: [{ url: p.urls[0], docs: [page('search_timeline.json')], cursor: null, count: 1 }],
      rateLimits: {}, stopped: null, stoppedAt: null,
    };
  };
  const [docs] = await harvestPool(ctx(harvest), ['https://x.com/NASA'], ['UserOriginalsTimeline'], { n: 10 });
  assert.equal(docs.length, 2);
  assert.equal(calls.length, 2);
  assert.notEqual(calls[0].storageStatePath, calls[1].storageStatePath);
  assert.deepEqual(calls[1].cursors, ['CURSOR_ABC']);
  assert.deepEqual(calls[1].targets, [8]); // 10 wanted - 2 found
  const paused = pool.describe().find((r) => r.pausas);
  assert.match(paused.pausas, /UserOriginalsTimeline until/);
});

test('rotation: an expired session disables the account; with no data left it raises a clear error', async () => {
  reset();
  pool.importSession({ authToken: 'a', ct0: 'a', account: 'solo' });
  const harvest = async (p) => ({
    results: [{ url: p.urls[0], docs: [], cursor: null, count: 0 }],
    rateLimits: {}, stopped: 'expired', stoppedAt: 0,
  });
  await assert.rejects(harvestPool(ctx(harvest), ['https://x.com/NASA'], ['UserOriginalsTimeline']), (e) => {
    assert.ok(e instanceof CollectError);
    assert.match(e.message, /expired/);
    return true;
  });
  assert.equal(pool.get('solo').active, 0);
});

test('rotation: when every account is out, partial data is returned with a warning', async () => {
  reset();
  pool.importSession({ authToken: 'a', ct0: 'a', account: 'solo' });
  const warnings = [];
  const harvest = async (p) => ({
    results: [{ url: p.urls[0], docs: [page('user_tweets.json')], cursor: 'C', count: 2 }],
    rateLimits: { UserOriginalsTimeline: { remaining: 0, reset: pool.now() + 900 } },
    stopped: 'rate_limited', stoppedAt: 0,
  });
  const [docs] = await harvestPool(ctx(harvest, { warn: (m) => warnings.push(m) }), ['https://x.com/NASA'], ['UserOriginalsTimeline']);
  assert.equal(docs.length, 1);
  assert.match(warnings[0], /paused for UserOriginalsTimeline/);
});

test('rotation: a batch cut in the middle resumes only the pending URLs', async () => {
  reset();
  pool.importSession({ authToken: 'a', ct0: 'a', account: 'a' });
  pool.importSession({ authToken: 'b', ct0: 'b', account: 'b' });
  const calls = [];
  const harvest = async (p) => {
    calls.push(p.urls);
    if (calls.length === 1) {
      return {
        results: [
          { url: p.urls[0], docs: [page('user_tweets.json')], cursor: null, count: 2 },
          { url: p.urls[1], docs: [], cursor: null, count: 0 },
        ],
        rateLimits: {}, stopped: 'blocked', stoppedAt: 1,
      };
    }
    return { results: p.urls.map((u) => ({ url: u, docs: [page('search_timeline.json')], cursor: null, count: 1 })), rateLimits: {}, stopped: null };
  };
  const urls = ['https://x.com/a', 'https://x.com/b', 'https://x.com/c'];
  const groups = await harvestPool(ctx(harvest), urls, ['UserOriginalsTimeline']);
  assert.deepEqual(calls[1], ['https://x.com/b', 'https://x.com/c']);
  assert.deepEqual(groups.map((g) => g.length), [1, 1, 1]);
});

test('no accounts at all -> instructions to import a session', async () => {
  reset();
  await assert.rejects(harvestPool(ctx(async () => assert.fail()), ['https://x.com/a'], ['X']), /no active X session/);
});
