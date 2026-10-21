// Collectors: one function per TweetScraperR *API() function.
//
// harvestPool() is the port of .pw_harvest_raw(): it takes an account from the
// pool, harvests, and if X cuts (endpoint quota exhausted, expired session,
// suspended account) pauses or disables that account and resumes the cut URL
// with the next available one, injecting the last pagination cursor so it
// continues where it stopped instead of starting over.
import * as pool from './pool.mjs';
import { harvest } from './engine.mjs';
import { parseTimelineTweets, parseUsers, userRow, aboutRow } from './parse.mjs';

const DISABLE_MSGS = {
  expired: 'session expired or revoked',
  not_logged_in: 'not logged in',
  banned: 'X limited or suspended the account (error 88 with quota left)',
  locked: 'account locked by X (error 326)',
};

export class CollectError extends Error {}

/** Scroll ceiling for `n` items (the engine stops earlier when it reaches n or data stops coming). */
export const scrollsFor = (n) => Math.max(5, Math.ceil(n / 10) + 5);

/** "NASA", "@NASA" or "https://x.com/NASA/..." -> "NASA" */
export function handle(x) {
  return String(x).trim().replace(/^@|^https?:\/\/(www\.)?(x|twitter)\.com\//i, '').replace(/[/?#].*$/, '');
}

/** Numeric list id or https://x.com/i/lists/<id> -> id */
export function listId(x) {
  const id = String(x).trim().replace(/^.*\/lists\/([0-9]+).*$/, '$1');
  if (!/^[0-9]+$/.test(id)) throw new CollectError('Unrecognized list id: ' + x);
  return id;
}

/** Tweet URL (x.com or twitter.com, with or without query) or bare id -> canonical x.com URL. */
export function tweetUrl(x) {
  const s = String(x).trim();
  if (/^[0-9]+$/.test(s)) return 'https://x.com/i/status/' + s;
  const m = /^https?:\/\/(?:www\.|mobile\.)?(?:x|twitter)\.com\/([^/]+)\/status\/([0-9]+)/i.exec(s);
  if (!m) throw new CollectError('Unrecognized tweet URL: ' + x);
  return `https://x.com/${m[1]}/status/${m[2]}`;
}

export const statusId = (url) => /\/status\/([0-9]+)/.exec(url)?.[1] ?? null;

export function searchUrl(q, f) {
  return `https://x.com/search?q=${encodeURIComponent(q)}&src=typed_query&f=${f}`;
}

/**
 * Harvests `urls` rotating pool accounts. Returns one array of GraphQL docs
 * per URL. Throws CollectError if nothing could be collected; with partial
 * data it records a warning and returns it. `ctx.harvest` replaces the engine
 * (tests drive the rotation with scripted responses).
 */
export async function harvestPool(ctx, urls, opNames, { maxScrolls = 25, n = null, unit = 'tweets' } = {}) {
  const run = ctx.harvest ?? harvest;
  const op = opNames[0];
  const docs = urls.map(() => []);
  const cursors = urls.map(() => null);
  const found = urls.map(() => 0);
  let pending = urls.map((_, i) => i);
  let lastDisabled = null;
  while (pending.length) {
    if (ctx.signal?.aborted) break;
    const got = await pool.acquireWait(op, ctx.waitTimeout, ctx.log);
    const acc = got.account;
    if (!acc) {
      const msg =
        got.reason === 'busy'
          ? `All accounts are paused for ${op} until ${pool.hms(got.nextAt)}.`
          : lastDisabled === 'expired'
            ? 'Your X session seems to have expired. Re-import it (session import) with fresh cookies.'
            : 'There is no active X session. Import one with: session import (or login --manual).';
      if (docs.some((d) => d.length)) {
        ctx.warn(msg + ' Returning the data collected until the cut.');
        break;
      }
      throw new CollectError(msg);
    }
    const sent = pending;
    let res;
    try {
      res = await run({
        storageStatePath: acc.state_path,
        urls: sent.map((i) => urls[i]),
        opNames,
        maxScrolls,
        targets: n ? sent.map((i) => Math.max(n - found[i], 1)) : [],
        unit,
        cursors: sent.map((i) => cursors[i]),
        proxy: pool.effectiveProxy(acc, ctx.proxy),
        userAgent: acc.user_agent,
        dumpDir: ctx.dumpDir,
        headless: ctx.headless,
        onProgress: ctx.progress,
        onLog: ctx.log,
        signal: ctx.signal,
      });
    } catch (e) {
      pool.release(acc.username, op);
      throw new CollectError('The harvest failed: ' + e.message);
    }
    let nResp = 0;
    res.results.forEach((r, i) => {
      const j = sent[i];
      for (const d of r.docs) docs[j].push(d.doc);
      nResp += r.docs.length;
      found[j] += r.count;
      if (r.cursor) cursors[j] = r.cursor;
    });
    const rl = res.rateLimits[op];
    const stopped = res.stopped;
    if (!stopped || stopped === 'interrupted') {
      pool.release(acc.username, op, rl?.remaining === 0 ? rl.reset : 0, nResp);
      break;
    }
    pending = sent.slice(res.stoppedAt);
    if (stopped === 'rate_limited' || stopped === 'blocked') {
      const t = pool.now();
      const until = stopped === 'rate_limited' && rl?.reset > t ? rl.reset : t + 900;
      pool.release(acc.username, op, until, nResp);
      ctx.log(
        `Account "${acc.username}": ${stopped === 'blocked' ? 'X returned a block page' : `${op} quota exhausted`}; ` +
          `paused until ${pool.hms(until)}. Continuing with the next available account.`
      );
    } else {
      const msg = DISABLE_MSGS[stopped] || stopped;
      pool.disable(acc.username, op, msg, nResp);
      lastDisabled = stopped;
      ctx.warn(`Account "${acc.username}" disabled: ${msg}.`);
    }
  }
  return docs;
}

function uniqueBy(rows, key) {
  const seen = new Set();
  return rows.filter((r) => {
    const k = r[key];
    if (k == null) return true;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

const tweetsOf = (docs) => uniqueBy(docs.flatMap((d) => parseTimelineTweets(d).tweets), 'tweet_id');
const usersOf = (docs) => uniqueBy(docs.flatMap((d) => parseUsers(d).users), 'user_id');

async function timelineTweets(ctx, url, op, n) {
  const [docs] = await harvestPool(ctx, [url], [op], { maxScrolls: scrollsFor(n), n });
  return tweetsOf(docs).slice(0, n);
}

async function collectUsers(ctx, url, op, n) {
  const [docs] = await harvestPool(ctx, [url], [op], { maxScrolls: scrollsFor(n), n, unit: 'users' });
  return usersOf(docs).slice(0, n);
}

// ---- tweets ---------------------------------------------------------------

export async function userTweets(ctx, username, n = 40) {
  const u = handle(username);
  if (!u) throw new CollectError('A username is needed.');
  return { rows: await timelineTweets(ctx, 'https://x.com/' + u, 'UserOriginalsTimeline', n), prefix: 'api_timeline_' + u };
}

export async function userMedia(ctx, username, n = 40) {
  const u = handle(username);
  if (!u) throw new CollectError('A username is needed.');
  return { rows: await timelineTweets(ctx, `https://x.com/${u}/media`, 'UserVideoTimeline', n), prefix: 'api_media_' + u };
}

/** Combined timeline of several accounts in one browser; n is per account. Newest first. */
export async function timelines(ctx, usernames, n = 40) {
  const us = usernames.map(handle).filter(Boolean);
  if (!us.length) throw new CollectError('At least one username is needed.');
  const groups = await harvestPool(ctx, us.map((u) => 'https://x.com/' + u), ['UserOriginalsTimeline'], {
    maxScrolls: scrollsFor(n),
    n,
  });
  const perAccount = {};
  const rows = [];
  groups.forEach((docs, k) => {
    const tw = tweetsOf(docs).slice(0, n);
    perAccount['@' + us[k]] = tw.length;
    if (!tw.length) ctx.warn(`No tweets for @${us[k]} (protected or nonexistent?).`);
    rows.push(...tw);
  });
  const out = uniqueBy(rows, 'tweet_id').sort((a, b) => (b.fecha ?? '').localeCompare(a.fecha ?? ''));
  return { rows: out, prefix: 'api_timelines', meta: { per_account: perAccount } };
}

const PRODUCTS = { Latest: 'live', Top: 'top', Media: 'media' };

/** since/until: "YYYY-MM-DD" or X's "YYYY-MM-DD_HH:MM:SS" (an "_UTC" suffix from old exports is dropped). */
function dateOp(name, v) {
  if (!v) return '';
  return ` ${name}:${String(v).replace(/_UTC$/, '').trim().replace(/\s+/g, '_')}`;
}

export async function search(ctx, query, n = 40, { product = 'Latest', since = null, until = null } = {}) {
  if (!query) throw new CollectError('A search query is needed.');
  const f = PRODUCTS[product];
  if (!f) throw new CollectError('product must be Latest, Top or Media.');
  const q = query + dateOp('since', since) + dateOp('until', until);
  const rows = await timelineTweets(ctx, searchUrl(q, f), 'SearchTimeline', n);
  return { rows, prefix: 'api_search_' + q.replace(/[^A-Za-z0-9]+/g, '_'), meta: { query: q, product } };
}

/** Largest tweet id (ids exceed double precision: compared as BigInt). */
export function maxStatusId(ids) {
  let best = null;
  for (const id of ids) if (id && /^[0-9]+$/.test(id) && (best === null || BigInt(id) > BigInt(best))) best = id;
  return best;
}

const abortableSleep = (ms, signal) =>
  new Promise((resolve) => {
    if (signal?.aborted) return resolve();
    const t = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => (clearTimeout(t), resolve()), { once: true });
  });

/**
 * Follows a search forward: repeats the "Latest" search every `interval`
 * seconds during `duration`, adding `since_id:<newest seen>` from the second
 * round so X returns only newer tweets. `onRound(rows, info)` runs after each
 * round with the accumulated rows (newest first).
 */
export async function live(ctx, query, { interval = 300, duration = 3600, n = 100, maxTweets = Infinity, onRound = () => {} } = {}) {
  if (!(interval >= 60)) throw new CollectError('interval must be >= 60 seconds.');
  if (!(duration > 0)) throw new CollectError('duration must be > 0 seconds.');
  const end = Date.now() + duration * 1000;
  let rows = [];
  let lastId = null;
  let round = 0;
  while (!ctx.signal?.aborted) {
    round++;
    const q = lastId ? `${query} since_id:${lastId}` : query;
    let fresh = [];
    try {
      fresh = (await search(ctx, q, n, { product: 'Latest' })).rows;
    } catch (e) {
      ctx.warn(`Round ${round} failed (retrying next round): ${e.message}`);
    }
    if (lastId && fresh.length >= n) {
      ctx.warn(`Round ${round}: reached the cap of ${n} tweets; some tweets may be missing. Lower interval or raise n.`);
    }
    lastId = maxStatusId([lastId, ...fresh.map((r) => r.tweet_id)]);
    const have = new Set(rows.map((r) => r.tweet_id));
    const added = fresh.filter((r) => !have.has(r.tweet_id));
    rows = [...added, ...rows];
    onRound(rows, { round, added: added.length, total: rows.length });
    if (rows.length >= maxTweets) break;
    const wait = Math.min(interval * 1000, end - Date.now());
    if (wait <= 0) break;
    await abortableSleep(wait, ctx.signal);
    if (Date.now() >= end) break;
  }
  return { rows, prefix: 'api_live_' + query.replace(/[^A-Za-z0-9]+/g, '_'), meta: { rounds: round } };
}

export async function replies(ctx, url, n = 40) {
  const u = tweetUrl(url);
  const rows = await timelineTweets(ctx, u, 'TweetDetail', n);
  return { rows, prefix: 'api_replies_' + u.replace(/^https:\/\/x\.com\/(.*)\/status\/(.*)$/, '$1_$2') };
}

/** Focal tweet of each URL (the one whose id matches), thread replies discarded. */
export async function tweetsData(ctx, urls) {
  const us = urls.map(tweetUrl);
  if (!us.length) throw new CollectError('At least one tweet URL is needed.');
  const groups = await harvestPool(ctx, us, ['TweetDetail'], { maxScrolls: 1, n: 1 });
  const rows = [];
  groups.forEach((docs, k) => {
    const id = statusId(us[k]);
    const hit = docs.flatMap((d) => parseTimelineTweets(d).tweets).find((t) => t.tweet_id === id);
    if (hit) rows.push(hit);
    else ctx.warn('Could not retrieve the tweet: ' + urls[k]);
  });
  return { rows, prefix: 'api_tweets_data' };
}

export async function listTweets(ctx, list, n = 40) {
  const id = listId(list);
  return { rows: await timelineTweets(ctx, 'https://x.com/i/lists/' + id, 'ListLatestTweetsTimeline', n), prefix: 'api_list_' + id };
}

// ---- users ----------------------------------------------------------------

export async function usersData(ctx, usernames) {
  const us = usernames.map(handle).filter(Boolean);
  if (!us.length) throw new CollectError('At least one username is needed.');
  const groups = await harvestPool(ctx, us.map((u) => 'https://x.com/' + u), ['UserByScreenName'], {
    maxScrolls: 2,
    n: 1,
    unit: 'users',
  });
  const rows = [];
  groups.forEach((docs, k) => {
    const row = docs.map((d) => userRow(d?.data?.user?.result)).find(Boolean);
    if (row) rows.push(row);
    else ctx.warn('Not found: @' + us[k]);
  });
  return { rows, prefix: 'api_users' };
}

export async function usersAbout(ctx, usernames) {
  const us = usernames.map(handle).filter(Boolean);
  if (!us.length) throw new CollectError('At least one username is needed.');
  const groups = await harvestPool(ctx, us.map((u) => `https://x.com/${u}/about`), ['AboutAccountQuery'], {
    maxScrolls: 1,
    n: 1,
    unit: 'users',
  });
  const rows = [];
  groups.forEach((docs, k) => {
    const row = docs.map((d) => aboutRow(d?.data?.user_result_by_screen_name?.result)).find(Boolean);
    if (row) rows.push(row);
    else ctx.warn('Not found: @' + us[k]);
  });
  return { rows, prefix: 'api_about' };
}

export async function usersSearch(ctx, query, n = 40) {
  if (!query) throw new CollectError('A search query is needed.');
  return { rows: await collectUsers(ctx, searchUrl(query, 'user'), 'SearchTimeline', n), prefix: 'api_users_search_' + query.replace(/[^A-Za-z0-9]+/g, '_') };
}

export async function followers(ctx, username, n = 100) {
  const u = handle(username);
  if (!u) throw new CollectError('A username is needed.');
  return { rows: await collectUsers(ctx, `https://x.com/${u}/followers`, 'Followers', n), prefix: 'api_followers_' + u };
}

export async function following(ctx, username, n = 100) {
  const u = handle(username);
  if (!u) throw new CollectError('A username is needed.');
  return { rows: await collectUsers(ctx, `https://x.com/${u}/following`, 'Following', n), prefix: 'api_following_' + u };
}

export async function retweeters(ctx, url, n = 100) {
  const u = tweetUrl(url);
  const prefix = 'api_rt_' + u.replace(/^https:\/\/x\.com\/(.*)\/status\/(.*)$/, '$1_$2');
  return { rows: await collectUsers(ctx, u + '/retweets', 'Retweeters', n), prefix };
}

export async function listMembers(ctx, list, n = 100) {
  const id = listId(list);
  return { rows: await collectUsers(ctx, `https://x.com/i/lists/${id}/members`, 'ListMembers', n), prefix: 'api_list_members_' + id };
}
