// Pool of X accounts (SQLite through node:sqlite).
//
// Model ported from TweetScraperR (R/accounts-pool.R), which in turn ports
// twscrape (accounts_pool.py, MIT): each account stores its session
// (Playwright storageState), an optional proxy and, per GraphQL operation, a
// lock (unix ts until which it is not used) and a request counter. Locks are
// per (account, operation): an account out of quota for SearchTimeline still
// serves UserTweets. Acquisition is one atomic UPDATE ... RETURNING, so
// several processes never take the same account.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';

// Covers the harvest timeout plus a margin: if the process dies mid-run the
// account frees itself when the hold expires.
const HOLD_SECS = 960;

export const now = () => Math.floor(Date.now() / 1000);

export const hms = (ts) => new Date(ts * 1000).toTimeString().slice(0, 8);

export function dataDir() {
  const d = process.env.TWEETSCRAPER_HOME || path.join(os.homedir(), '.tweetscraper');
  fs.mkdirSync(d, { recursive: true });
  return d;
}

export function sessionPath(account) {
  const d = path.join(dataDir(), 'sessions');
  fs.mkdirSync(d, { recursive: true });
  return path.join(d, account.replace(/[^A-Za-z0-9_.-]/g, '_') + '.json');
}

let db = null;

function open() {
  if (db) return db;
  db = new DatabaseSync(path.join(dataDir(), 'accounts.sqlite'));
  // Another process writing: wait instead of failing with "database is locked".
  db.exec('PRAGMA busy_timeout = 10000');
  const uv = db.prepare('PRAGMA user_version').get().user_version;
  if (uv < 1) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS accounts (
        username    TEXT PRIMARY KEY NOT NULL COLLATE NOCASE,
        state_path  TEXT NOT NULL,
        proxy       TEXT,
        user_agent  TEXT,
        active      INTEGER NOT NULL DEFAULT 1,
        locks       TEXT NOT NULL DEFAULT '{}',
        stats       TEXT NOT NULL DEFAULT '{}',
        last_used   INTEGER,
        error_msg   TEXT,
        added_at    INTEGER NOT NULL,
        screen_name TEXT
      );
      PRAGMA user_version = 2;`);
  }
  return db;
}

function opPath(op) {
  if (!/^[A-Za-z0-9_]+$/.test(op)) throw new Error('Invalid operation name: ' + op);
  return `$."${op}"`;
}

/** Adds or updates an account. Re-importing reactivates it and clears its error; proxy/UA only change if given. */
export function upsert(account, statePath, { proxy = null, userAgent = null } = {}) {
  open()
    .prepare(`
      INSERT INTO accounts (username, state_path, proxy, user_agent, added_at)
      VALUES (:u, :s, :p, :ua, :now)
      ON CONFLICT(username) DO UPDATE SET
        state_path = excluded.state_path,
        proxy      = COALESCE(excluded.proxy, proxy),
        user_agent = COALESCE(excluded.user_agent, user_agent),
        active     = 1,
        error_msg  = NULL`)
    .run({ u: account, s: statePath, p: proxy || null, ua: userAgent || null, now: now() });
  return account;
}

export function get(account) {
  return open().prepare('SELECT * FROM accounts WHERE username = ?').get(account) ?? null;
}

export function all() {
  return open().prepare('SELECT * FROM accounts ORDER BY active DESC, username').all();
}

/** Takes the least recently used active account that is free for `op` and holds it. */
export function acquire(op) {
  const t = now();
  return (
    open()
      .prepare(`
        UPDATE accounts SET locks = json_set(locks, :path, :hold), last_used = :now
        WHERE username = (
          SELECT username FROM accounts
          WHERE active = 1 AND COALESCE(json_extract(locks, :path), 0) <= :now
          ORDER BY COALESCE(last_used, 0), username
          LIMIT 1
        )
        RETURNING *`)
      .get({ path: opPath(op), hold: t + HOLD_SECS, now: t }) ?? null
  );
}

/** Frees an account after using it for `op`; `until` > now keeps it paused for `op` (quota exhausted). */
export function release(account, op, until = 0, n = 0) {
  open()
    .prepare(`
      UPDATE accounts SET
        locks = CASE WHEN :until > :now THEN json_set(locks, :path, :until) ELSE json_remove(locks, :path) END,
        stats = json_set(stats, :path, COALESCE(json_extract(stats, :path), 0) + :n),
        last_used = :now
      WHERE username = :u`)
    .run({ path: opPath(op), until: Math.trunc(until), now: now(), n: Math.trunc(n), u: account });
}

/** Deactivates an account (expired session, suspended or locked by X). */
export function disable(account, op, msg, n = 0) {
  open()
    .prepare(`
      UPDATE accounts SET active = 0, error_msg = :msg,
        locks = json_remove(locks, :path),
        stats = json_set(stats, :path, COALESCE(json_extract(stats, :path), 0) + :n)
      WHERE username = :u`)
    .run({ msg, path: opPath(op), n: Math.trunc(n), u: account });
}

function status(op) {
  const r = open()
    .prepare(`
      SELECT COUNT(*) AS n_active, MIN(COALESCE(json_extract(locks, :path), 0)) AS next_at
      FROM accounts WHERE active = 1`)
    .get({ path: opPath(op) });
  return { nActive: r.n_active, nextAt: r.next_at };
}

/**
 * Takes an account for `op`, waiting up to `waitTimeout` seconds if all are
 * paused. Returns the account, or {account: null, reason: "none"|"busy", nextAt}.
 */
export async function acquireWait(op, waitTimeout, log) {
  const deadline = now() + waitTimeout;
  let announced = false;
  for (;;) {
    const acc = acquire(op);
    if (acc) return { account: acc };
    const st = status(op);
    if (st.nActive === 0) return { account: null, reason: 'none' };
    if (st.nextAt > deadline) return { account: null, reason: 'busy', nextAt: st.nextAt };
    if (!announced) {
      log(`All accounts are paused for ${op}; one frees up at ${hms(st.nextAt)}. Waiting...`);
      announced = true;
    }
    await new Promise((r) => setTimeout(r, Math.min(Math.max(st.nextAt - now(), 1), 5) * 1000));
  }
}

/** Effective proxy of an account: its own, or the global one. */
export function effectiveProxy(acc, globalProxy) {
  return acc.proxy || globalProxy || process.env.TWEETSCRAPER_PROXY || null;
}

export function remove(account) {
  const acc = get(account);
  if (!acc) return false;
  open().prepare('DELETE FROM accounts WHERE username = ?').run(account);
  fs.rmSync(acc.state_path, { force: true });
  return true;
}

export function reactivate(account) {
  return open().prepare('UPDATE accounts SET active = 1, error_msg = NULL WHERE username = ?').run(account).changes;
}

export function resetLocks() {
  return open().prepare("UPDATE accounts SET locks = '{}'").run().changes;
}

export function setProxy(account, proxy) {
  return open().prepare('UPDATE accounts SET proxy = ? WHERE username = ?').run(proxy, account).changes;
}

export function markValid(account, screenName) {
  open()
    .prepare('UPDATE accounts SET active = 1, error_msg = NULL, screen_name = ? WHERE username = ?')
    .run(screenName, account);
}

export function markInvalid(account, msg) {
  open().prepare('UPDATE accounts SET active = 0, error_msg = ? WHERE username = ?').run(msg, account);
}

/**
 * Keeps one entry per real X account. The most recently added (freshest
 * session) wins and inherits locks (longest wins: same account, same quota)
 * and stats (summed). Returns the removed names.
 */
export function dedupe(screenName) {
  const d = open();
  const rows = d
    .prepare('SELECT * FROM accounts WHERE screen_name = ? COLLATE NOCASE ORDER BY added_at DESC, username')
    .all(screenName);
  if (rows.length < 2) return [];
  const merge = (key, f) => {
    const acc = {};
    for (const r of rows) for (const [k, v] of Object.entries(JSON.parse(r[key]))) acc[k] = k in acc ? f(acc[k], v) : v;
    return JSON.stringify(acc);
  };
  const [keep, ...drop] = rows;
  d.exec('BEGIN');
  try {
    d.prepare('UPDATE accounts SET locks = ?, stats = ? WHERE username = ?').run(
      merge('locks', Math.max),
      merge('stats', (a, b) => a + b),
      keep.username
    );
    for (const r of drop) d.prepare('DELETE FROM accounts WHERE username = ?').run(r.username);
    d.exec('COMMIT');
  } catch (e) {
    d.exec('ROLLBACK');
    throw e;
  }
  for (const r of drop) fs.rmSync(r.state_path, { force: true });
  return drop.map((r) => r.username);
}

/** Readable pool state (one record per account). */
export function describe() {
  const t = now();
  return all().map((r) => {
    const locks = Object.entries(JSON.parse(r.locks)).filter(([, v]) => v > t);
    const stats = JSON.parse(r.stats);
    return {
      cuenta: r.username,
      usuario_x: r.screen_name,
      activa: r.active === 1,
      pausas: locks.length ? locks.map(([k, v]) => `${k} until ${hms(v)}`).join('; ') : null,
      requests: Object.values(stats).reduce((a, b) => a + b, 0),
      requests_por_endpoint: Object.keys(stats).length
        ? Object.entries(stats).map(([k, v]) => `${k}: ${v}`).join('; ')
        : null,
      ultimo_uso: r.last_used ? new Date(r.last_used * 1000).toISOString() : null,
      proxy: r.proxy ? r.proxy.replace(/\/\/([^:@/]+):[^@/]*@/, '//$1:***@').replace(/^([^:@/]+):[^@/]*@/, '$1:***@') : null,
      error: r.error_msg,
    };
  });
}

/**
 * auth_token and ct0 from a cookie export: the header "auth_token=...; ct0=...",
 * a JSON object {"auth_token": ..., "ct0": ...} or the JSON array of
 * extensions like Cookie-Editor ([{"name": ..., "value": ...}, ...]).
 */
export function parseCookies(x) {
  x = String(x).trim();
  const vals = {};
  if (x.startsWith('{') || x.startsWith('[')) {
    const j = JSON.parse(x);
    if (Array.isArray(j)) for (const c of j) vals[c?.name ?? ''] = c?.value;
    else Object.assign(vals, j);
  } else {
    for (const kv of x.split(';')) {
      const s = kv.trim();
      const eq = s.indexOf('=');
      if (eq > 0) vals[s.slice(0, eq)] = s.slice(eq + 1);
    }
  }
  return { authToken: vals.auth_token || null, ct0: vals.ct0 || null };
}

/** Writes a Playwright storageState holding the X session cookies. */
export function writeSession(authToken, ct0, file) {
  const mk = (name, value, httpOnly) => ({
    name, value, domain: '.x.com', path: '/', expires: -1, httpOnly, secure: true, sameSite: 'Lax',
  });
  const st = { cookies: [mk('auth_token', authToken, true), mk('ct0', ct0, false)], origins: [] };
  fs.writeFileSync(file, JSON.stringify(st), { encoding: 'utf8', mode: 0o600 });
  return file;
}

/** Validates and normalizes a proxy address (null = no proxy). */
export function checkProxy(proxy) {
  const p = proxy == null ? '' : String(proxy).trim();
  if (!p || p === 'none') return null;
  if (/^socks5?:\/\/[^/]*@/i.test(p)) {
    throw new Error(
      'Chromium does not support SOCKS5 proxies with user and password. ' +
        "Use your provider's HTTP address (http://user:pass@host:port)."
    );
  }
  if (!/^((https?|socks[45]?):\/\/)?([^@/]+@)?[^:@/]+:[0-9]+\/?$/i.test(p)) {
    throw new Error(`Unrecognized proxy "${p}". Format: http://user:pass@host:port`);
  }
  return p;
}

/** Imports an X session (cookies) as a pool account. */
export function importSession({ authToken, ct0, account = 'default', proxy = null }) {
  if (!authToken || !ct0) throw new Error('Both values are needed: auth_token and ct0 (x.com cookies).');
  if (!account) throw new Error('An account name is needed.');
  const state = get(account)?.state_path || sessionPath(account);
  const px = checkProxy(proxy);
  writeSession(authToken, ct0, state);
  upsert(account, state, { proxy: px });
  return account;
}
