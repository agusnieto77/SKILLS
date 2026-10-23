// Playwright + stealth engine (ported from TweetScraperR inst/node/tsr-engine.js).
//
// Instead of crafting GraphQL requests (several endpoints, like SearchTimeline
// and TweetDetail, require the x-client-transaction-id header that only the
// web app computes), it navigates x.com with a real session and "rides along":
// it collects the JSON responses the app itself fires, scrolling to trigger
// more pages.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { scanBody, findInstructions, hasThreadCursor } from './parse.mjs';

const require = createRequire(import.meta.url);

let chromiumCache = null;

/** playwright-extra chromium with the stealth plugin (lazy: analysis commands never load it). */
function chromium() {
  if (chromiumCache) return chromiumCache;
  let mod;
  try {
    mod = require('playwright-extra');
  } catch {
    throw new Error('The Playwright engine is not installed. Run: node scripts/tweetscraper.mjs install');
  }
  const stealth = require('puppeteer-extra-plugin-stealth');
  mod.chromium.use(stealth());
  chromiumCache = mod.chromium;
  return chromiumCache;
}

// No fixed userAgent: Chromium's own (with "HeadlessChrome" patched by the
// stealth plugin) matches the real browser version, OS and client hints. A
// hardcoded UA is itself a fingerprint. Each pool account may set its own.
function ctxOpts(extra) {
  return Object.assign(
    { locale: 'es-ES', timezoneId: 'America/Argentina/Buenos_Aires', viewport: { width: 1280, height: 860 } },
    extra || {}
  );
}

/** Accepts "http://host:port", "user:pass@host:port" or {server, username, password}. */
export function parseProxy(proxy) {
  if (!proxy) return null;
  if (typeof proxy === 'object') return proxy;
  let s = String(proxy);
  let creds = null;
  if (s.includes('@')) {
    const scheme = (s.match(/^[a-z0-9]+:\/\//i) || [''])[0];
    const rest = s.slice(scheme.length);
    const at = rest.lastIndexOf('@');
    const userpass = rest.slice(0, at);
    const colon = userpass.indexOf(':');
    creds = {
      username: colon === -1 ? userpass : userpass.slice(0, colon),
      password: colon === -1 ? '' : userpass.slice(colon + 1),
    };
    s = scheme + rest.slice(at + 1);
  }
  return creds ? { server: s, ...creds } : { server: s };
}

async function launch({ proxy, headless = true, args } = {}) {
  const px = parseProxy(proxy);
  const opts = { headless };
  if (px) opts.proxy = px;
  if (args) opts.args = args;
  return chromium().launch(opts);
}

export function isLoginUrl(u) {
  return /\/(i\/flow\/login|login|i\/jf\/onboarding)/.test(u);
}

/** GraphQL operation of an API URL: /i/api/graphql/<hash>/<Operation> */
export function opOf(u) {
  const m = /\/i\/api\/graphql\/[^/]+\/([^/?#]+)/.exec(u);
  return m ? m[1] : null;
}

/**
 * Classifies an API response to decide what to do with the account (rules
 * ported from twscrape, queue_client._check_rep). null = keep going, else:
 *   rate_limited  endpoint quota exhausted until x-rate-limit-reset
 *   banned        "Rate limit exceeded" (88) with quota left: suspended/limited account
 *   locked        account locked by access control (326)
 *   expired       invalid session (expired or revoked cookies: 32, 401, 403)
 *   blocked       HTML error page (Cloudflare or another IP block)
 */
export function classify(status, headers, text) {
  const remaining = parseInt(headers['x-rate-limit-remaining'], 10);
  if (status >= 400 && (headers['content-type'] || '').includes('text/html')) return 'blocked';
  let codes = [];
  try {
    const d = JSON.parse(text);
    if (d && Array.isArray(d.errors)) codes = d.errors.map((e) => e && e.code);
  } catch {
    /* empty body or plain text */
  }
  if (codes.includes(88) && remaining > 0) return 'banned';
  if (status === 429 || remaining === 0 || codes.includes(88) || /^\s*rate limit exceeded/i.test(text)) {
    return 'rate_limited';
  }
  if (codes.includes(326)) return 'locked';
  if (codes.includes(32) || status === 401 || (status === 403 && !codes.length)) return 'expired';
  return null;
}

/** Replaces the cursor in the variables of a GraphQL URL (the transaction id signs only method + path). */
export function withCursor(url, cursor) {
  const u = new URL(url);
  const v = JSON.parse(u.searchParams.get('variables') || '{}');
  v.cursor = cursor;
  u.searchParams.set('variables', JSON.stringify(v));
  return u.toString();
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Harvests the GraphQL responses of `opNames` fired while visiting each URL.
 * One browser/context is reused for every URL.
 *
 * If a response says the account cannot continue (see classify()), it stops at
 * the current URL and returns what it got with `stopped` (reason) and
 * `stoppedAt` (0-based index of the cut URL): the caller rotates to another
 * pool account and resumes from that URL. `cursors[k]` is injected into the
 * first request of the app so pagination resumes where it stopped.
 *
 * Each result has {url, docs, cursor, count, paginationState}: complete, uncertain or truncated.
 * Returns {results, rateLimits, stopped, stoppedOp, stoppedAt, detail}.
 */
export async function harvest(p) {
  const {
    storageStatePath, urls, opNames, maxScrolls = 25, waitMs = 2500, scrollPx = 4000, headless = true,
    dumpDir = null, cursors = [], targets = [], unit = 'tweets', proxy = null, userAgent = null,
    onProgress = () => {}, onLog = () => {}, signal = null,
  } = p;
  if (dumpDir) fs.mkdirSync(dumpDir, { recursive: true });
  onProgress({ stage: 'launch' });
  const browser = await launch({ proxy, headless });
  const abort = () => browser.close().catch(() => {});
  signal?.addEventListener('abort', abort, { once: true });
  const context = await browser.newContext(
    ctxOpts(Object.assign({ storageState: storageStatePath }, userAgent ? { userAgent } : {}))
  );
  const results = [];
  const rateLimits = {};
  const seenTweets = new Set();
  const seenUsers = new Set();
  let last = null;
  let stop = null;
  let dumpSeq = 0;
  const dumpRun = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').slice(0, 15) + '_' + process.pid;

  try {
    for (let k = 0; k < urls.length && !stop; k++) {
      const url = urls[k];
      onProgress({ stage: 'open', i: k + 1, n: urls.length, url });
      const docs = [];
      const target = targets[k] || 0;
      let found = 0;
      let cursor = null;
      let paginationPending = false;
      let stableEnd = false;
      let page;
      try {
        page = await context.newPage();
        if (cursors[k]) {
          let injected = false;
          await page.route('**/i/api/graphql/**', (route) => {
            const req = route.request();
            if (injected || opOf(req.url()) !== opNames[0]) return route.continue();
            injected = true;
            onLog(`resuming ${opNames[0]} from the saved cursor`);
            return route.continue({ url: withCursor(req.url(), cursors[k]) });
          });
        }
        page.on('response', async (resp) => {
          const op = opOf(resp.url());
          if (!op || !opNames.includes(op)) return;
          const h = resp.headers();
          if (h['x-rate-limit-remaining'] != null) {
            rateLimits[op] = {
              remaining: parseInt(h['x-rate-limit-remaining'], 10),
              limit: parseInt(h['x-rate-limit-limit'], 10),
              reset: parseInt(h['x-rate-limit-reset'], 10),
            };
          }
          let t = '';
          try {
            t = await resp.text();
          } catch {
            /* response already consumed, or navigation */
          }
          if (dumpDir) {
            const f = `${dumpRun}_${String(++dumpSeq).padStart(4, '0')}_${op}_${resp.status()}.json`;
            try {
              fs.writeFileSync(path.join(dumpDir, f), t);
            } catch (e) {
              onLog(`could not dump ${f}: ${e.message}`);
            }
          }
          const reason = classify(resp.status(), h, t);
          if (reason && !stop) {
            stop = { reason, op, at: k, detail: t.slice(0, 200) };
            onLog(`stop (${reason}) at ${op}: HTTP ${resp.status()}`);
          }
          // The last response before a quota stop still carries data.
          if (t && t[0] === '{') {
            let doc;
            try {
              doc = JSON.parse(t);
            } catch {
              onLog('skipped a non-JSON response: ' + t.slice(0, 120));
              return;
            }
            docs.push({ op, doc });
            const s = scanBody(doc, seenTweets, seenUsers);
            if (s.last) last = s.last;
            if (op === opNames[0]) {
              found += unit === 'users' ? s.users : s.tweets;
              paginationPending = hasThreadCursor(findInstructions(doc));
              if (s.cursor) cursor = s.cursor;
            }
            onProgress({ stage: 'data', tweets: seenTweets.size, users: seenUsers.size, last });
          }
        });

        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(4500);
        if (!stop && isLoginUrl(page.url())) {
          stop = { reason: 'not_logged_in', op: null, at: k, detail: page.url() };
        }
        // With an invalid session X does not redirect to the login: it deletes
        // the auth_token cookie and serves the page as a guest, so the harvest
        // would come back empty without any error.
        if (!stop) {
          const cookies = await context.cookies('https://x.com');
          if (!cookies.some((c) => c.name === 'auth_token' && c.value)) {
            stop = { reason: 'expired', op: null, at: k, detail: 'X deleted the auth_token cookie' };
          }
        }
        let stable = 0;
        for (let i = 0; i < maxScrolls && !stop && !(target && found >= target); i++) {
          const before = docs.length;
          await page.mouse.wheel(0, scrollPx);
          await page.waitForTimeout(waitMs);
          if (docs.length === before) {
            if (++stable >= 3) { stableEnd = true; break; }
          } else stable = 0;
        }
      } catch (e) {
        if (!signal?.aborted) throw e;
      }
      const paginationState = stop || signal?.aborted ? 'truncated' :
        !paginationPending ? 'complete' : stableEnd ? 'uncertain' : 'truncated';
      results.push({ url, docs, cursor, count: found, paginationState });
      if (signal?.aborted) {
        stop = stop || { reason: 'interrupted', op: null, at: k + 1, detail: null };
        break;
      }
      await page?.close().catch(() => {});
    }
    return {
      results,
      rateLimits,
      stopped: stop ? stop.reason : null,
      stoppedOp: stop ? stop.op : null,
      stoppedAt: stop ? stop.at : null,
      detail: stop ? stop.detail : null,
    };
  } finally {
    signal?.removeEventListener('abort', abort);
    await browser.close().catch(() => {});
  }
}

/**
 * Validates a session: opens x.com/home and returns whether it is still
 * authenticated and the real @handle (from the sidebar "Profile" link).
 * An invalid session loses its auth_token cookie; a locked account is
 * redirected to /account/access.
 */
export async function whoami({ storageStatePath, proxy = null, userAgent = null }) {
  const browser = await launch({ proxy });
  try {
    const context = await browser.newContext(
      ctxOpts(Object.assign({ storageState: storageStatePath }, userAgent ? { userAgent } : {}))
    );
    const page = await context.newPage();
    await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 60000 });
    let screenName = null;
    try {
      const link = page.locator('[data-testid="AppTabBar_Profile_Link"]');
      await link.waitFor({ timeout: 15000 });
      screenName = ((await link.getAttribute('href')) || '').replace(/^\//, '') || null;
    } catch {
      /* no sidebar: invalid or locked session, or an error page */
    }
    const url = page.url();
    const cookies = await context.cookies('https://x.com');
    const hasAuth = cookies.some((c) => c.name === 'auth_token' && c.value);
    let reason = null;
    if (/\/account\/access/.test(url)) reason = 'locked';
    else if (isLoginUrl(url) || !hasAuth) reason = 'expired';
    else if (!screenName) reason = 'unknown';
    return { valid: !reason, reason, screenName, url };
  } finally {
    await browser.close().catch(() => {});
  }
}

const LOGIN_URL = 'https://x.com/i/flow/login';
// Bilingual: X may serve the modal in Spanish or English.
const NEXT_BTNS = ['Continuar', 'Continue', 'Siguiente', 'Next'];
const LOGIN_BTNS = ['Iniciar sesión', 'Log in', 'Sign in', 'Acceder', 'Entrar', 'Continuar', 'Continue'];
const USER_SEL = "input[name='username_or_email'], input[name='text'], input[autocomplete~='username']";
const PASS_SEL = "input[name='password']";

// Types into the first VISIBLE input matching the selector with real
// keystrokes (JS value injection is an automation signature X detects). The
// target is tagged so Playwright can reach it despite the duplicated modal DOM.
async function humanFill(page, selector, value) {
  const marked = await page.evaluate((sel) => {
    const vis = (el) => el && el.offsetParent !== null && el.getClientRects().length > 0 && el.getAttribute('aria-hidden') !== 'true';
    document.querySelectorAll('[data-tsr-target]').forEach((e) => e.removeAttribute('data-tsr-target'));
    const els = Array.from(document.querySelectorAll(sel)).filter(vis);
    if (!els.length) return false;
    els[0].setAttribute('data-tsr-target', '1');
    return true;
  }, selector);
  if (!marked) return 'NO-VISIBLE';
  const loc = page.locator("[data-tsr-target='1']");
  await loc.click({ delay: 40 + Math.floor(Math.random() * 60) });
  await page.waitForTimeout(200 + Math.floor(Math.random() * 300));
  await loc.pressSequentially(String(value), { delay: 80 + Math.floor(Math.random() * 90) });
  await page.evaluate(() => document.querySelector('[data-tsr-target]')?.removeAttribute('data-tsr-target'));
  return 'OK';
}

async function clickVisibleText(page, texts) {
  return page.evaluate((ts) => {
    const vis = (el) => el && el.offsetParent !== null && el.getClientRects().length > 0;
    const c = Array.from(document.querySelectorAll('button,[role=button]')).filter(vis);
    for (const t of ts) {
      const el = c.find((e) => (e.innerText || '').trim().toLowerCase() === t.toLowerCase());
      if (el) {
        el.click();
        return 'CLICK:' + t;
      }
    }
    return 'NO-BTN';
  }, texts);
}

/** Automated login through the current X modal. X often blocks it: prefer cookie import or manual login. */
export async function login({ user, pass, email = '', storageStatePath, headless = true, proxy = null, shotDir = null, onLog = () => {} }) {
  const browser = await launch({ proxy, headless });
  try {
    const context = await browser.newContext(ctxOpts());
    const page = await context.newPage();
    await page.goto(LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(4500);
    let uf = 'NO-VISIBLE';
    for (let i = 0; i < 10 && uf !== 'OK'; i++) {
      uf = await humanFill(page, USER_SEL, user);
      if (uf !== 'OK') await page.waitForTimeout(1500);
    }
    onLog('username: ' + uf);
    await page.waitForTimeout(800 + Math.floor(Math.random() * 600));
    await clickVisibleText(page, NEXT_BTNS);
    await page.waitForTimeout(3500);
    // Optional identity challenge (email/phone) before the password field.
    let pf = await humanFill(page, PASS_SEL, pass);
    if (pf !== 'OK' && email) {
      if ((await humanFill(page, "input[data-testid='ocfEnterTextTextInput'], input[name='text']", email)) === 'OK') {
        onLog('identity challenge: email entered');
        await page.waitForTimeout(700);
        await clickVisibleText(page, NEXT_BTNS);
        await page.waitForTimeout(3500);
      }
    }
    for (let i = 0; i < 8 && pf !== 'OK'; i++) {
      await page.waitForTimeout(1500);
      pf = await humanFill(page, PASS_SEL, pass);
    }
    onLog('password: ' + pf);
    await page.waitForTimeout(800 + Math.floor(Math.random() * 600));
    await clickVisibleText(page, LOGIN_BTNS);
    await page.waitForTimeout(7000);
    const url = page.url();
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    const limited = /limitado temporalmente|temporarily limited|sospechos|unusual/i.test(bodyText);
    if (!isLoginUrl(url)) {
      await context.storageState({ path: storageStatePath });
      return { ok: true, url };
    }
    let screenshot = null;
    if (shotDir) {
      screenshot = path.join(shotDir, 'login-fail.png');
      await page.screenshot({ path: screenshot }).catch(() => {});
    }
    return { ok: false, url, limited, reason: limited ? 'rate_limited' : 'login_failed', hint: bodyText.slice(0, 500), screenshot };
  } finally {
    await browser.close().catch(() => {});
  }
}

/** Opens a visible browser on the X login and waits for the person to log in by hand. */
export async function manualLogin({ storageStatePath, waitSeconds = 420, proxy = null, onLog = () => {} }) {
  const browser = await launch({ proxy, headless: false, args: ['--start-maximized'] });
  try {
    const context = await browser.newContext(ctxOpts({ viewport: null }));
    const page = await context.newPage();
    await page.goto(LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    onLog(`Browser open. Log in to X in that window (waiting up to ${waitSeconds}s)...`);
    const start = Date.now();
    while (Date.now() - start < waitSeconds * 1000) {
      await sleep(2500);
      let u;
      try {
        u = page.url();
      } catch {
        break; // window closed
      }
      if (isLoginUrl(u)) continue;
      const ok = await page
        .evaluate(() => !!document.querySelector('[data-testid="primaryColumn"], [data-testid="AppTabBar_Home_Link"], a[href="/home"], article'))
        .catch(() => false);
      if (ok) {
        await sleep(1500);
        await context.storageState({ path: storageStatePath });
        return { ok: true, url: page.url() };
      }
    }
    return { ok: false, reason: 'timeout_manual' };
  } finally {
    await browser.close().catch(() => {});
  }
}

/** Engine diagnostics: versions and Chromium path. */
export function doctor() {
  const out = { node: process.version, playwright: null, chromium: null, chromiumInstalled: false };
  try {
    out.playwright = require('playwright/package.json').version;
    out.chromium = chromium().executablePath();
    out.chromiumInstalled = fs.existsSync(out.chromium);
  } catch (e) {
    out.error = e.message;
  }
  return out;
}
