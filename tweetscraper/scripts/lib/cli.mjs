// Command dispatch of the tweetscraper CLI.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import * as pool from './pool.mjs';
import * as engine from './engine.mjs';
import * as collect from './collect.mjs';
import * as an from './analyze.mjs';
import { lineChart, barChart, wordCloud } from './charts.mjs';
import { readRows, writeRows, writeMarkdown, appendJsonl, outPath, formatOf } from './io.mjs';
import { TWEET_FIELDS, USER_FIELDS, ABOUT_FIELDS } from './parse.mjs';
import { apiKey, analyzeTweet, analyzeImage, mapLimit, photosOf } from './openai.mjs';
import { imageReport } from './report.mjs';

const SKILL_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const OPTIONS = {
  out: { type: 'string', short: 'o' },
  format: { type: 'string' },
  n: { type: 'string', short: 'n' },
  in: { type: 'string', short: 'i' },
  account: { type: 'string' },
  proxy: { type: 'string' },
  'wait-timeout': { type: 'string' },
  'debug-dir': { type: 'string' },
  headed: { type: 'boolean' },
  // session / login
  'from-env': { type: 'string' },
  'cookies-file': { type: 'string' },
  'auth-token': { type: 'string' },
  ct0: { type: 'string' },
  manual: { type: 'boolean' },
  wait: { type: 'string' },
  'no-validate': { type: 'boolean' },
  // search / live
  product: { type: 'string' },
  since: { type: 'string' },
  until: { type: 'string' },
  interval: { type: 'string' },
  duration: { type: 'string' },
  'max-tweets': { type: 'string' },
  'urls-file': { type: 'string' },
  'users-file': { type: 'string' },
  'max-details': { type: 'string' },
  // Markdown / Obsidian (media downloads are opt-in)
  'md-style': { type: 'string' },
  query: { type: 'string' },
  'captured-at': { type: 'string' },
  'download-media': { type: 'boolean' },
  'max-media-bytes': { type: 'string' },
  // analysis
  top: { type: 'string' },
  group: { type: 'string' },
  chart: { type: 'string' },
  color: { type: 'string' },
  fill: { type: 'string' },
  lang: { type: 'string' },
  sw: { type: 'string' },
  'min-freq': { type: 'string' },
  'max-words': { type: 'string' },
  'random-order': { type: 'boolean' },
  'ignore-case': { type: 'boolean' },
  'from-text': { type: 'boolean' },
  'per-tweet': { type: 'boolean' },
  text: { type: 'string', multiple: true },
  img: { type: 'string', multiple: true },
  limit: { type: 'string' },
  model: { type: 'string' },
  concurrency: { type: 'string' },
  report: { type: 'string' },
  help: { type: 'boolean', short: 'h' },
};

class UsageError extends Error {}

const num = (v, def, name) => {
  if (v == null) return def;
  const n = Number(v);
  if (!Number.isFinite(n) || n < 0) throw new UsageError(`--${name} must be a non-negative number.`);
  return n;
};

const linesOf = (file) =>
  fs.readFileSync(file, 'utf8').split(/\r?\n/).map((s) => s.trim()).filter((s) => s && !s.startsWith('#'));

const log = (msg) => process.stderr.write(msg + '\n');

// ---- progress on stderr ----------------------------------------------------

function progressReporter() {
  const tty = process.stderr.isTTY;
  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  const t0 = Date.now();
  let i = 0;
  let lastLog = 0;
  let line = '';
  const elapsed = () => {
    const s = Math.round((Date.now() - t0) / 1000);
    return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`;
  };
  const draw = (force) => {
    if (tty) {
      const w = (process.stderr.columns || 80) - 1;
      process.stderr.write('\r' + `${frames[i++ % frames.length]} ${line}`.slice(0, w).padEnd(w));
    } else if (force || Date.now() - lastLog > 10000) {
      lastLog = Date.now();
      log(`[progress ${elapsed()}] ${line}`);
    }
  };
  const timer = tty ? setInterval(() => draw(), 120) : null;
  return {
    update(ev) {
      if (ev.stage === 'launch') line = 'starting browser...';
      else if (ev.stage === 'open') {
        line = `loading ${ev.n > 1 ? `${ev.i}/${ev.n}: ` : ''}${ev.url.replace(/^https?:\/\/(www\.)?/, '')}`;
        draw(true);
        return;
      } else if (ev.stage === 'data') {
        const count = ev.tweets ? `${ev.tweets} tweets` : ev.users ? `${ev.users} users` : '';
        line = `${count}  ${elapsed()}  ${(ev.last || '').replace(/\s+/g, ' ')}`;
      }
      draw();
    },
    clear() {
      if (timer) clearInterval(timer);
      if (tty) process.stderr.write('\r' + ' '.repeat((process.stderr.columns || 80) - 1) + '\r');
    },
  };
}

// ---- context shared by collectors ------------------------------------------

function makeCtx(v, signal) {
  const warnings = [];
  const prog = progressReporter();
  const ctx = {
    waitTimeout: num(v['wait-timeout'] ?? process.env.TWEETSCRAPER_WAIT_TIMEOUT, 900, 'wait-timeout'),
    proxy: v.proxy ? pool.checkProxy(v.proxy) : null,
    dumpDir: v['debug-dir'] || process.env.TWEETSCRAPER_DEBUG_DIR || null,
    headless: !v.headed,
    signal,
    log: (m) => {
      prog.clear();
      log(m);
    },
    warn: (m) => {
      warnings.push(m);
      prog.clear();
      log('warning: ' + m);
    },
    progress: (ev) => prog.update(ev),
  };
  return { ctx, warnings, done: () => prog.clear() };
}

const FIELDS_BY_KIND = { tweets: TWEET_FIELDS, thread: [...TWEET_FIELDS, 'rol'], users: USER_FIELDS, about: ABOUT_FIELDS };

async function saveDataset(v, res, kind, signal) {
  const file = v.out === '-' ? '-' : outPath(v.out, res.prefix);
  const format = formatOf(file, v.format);
  if (format === 'markdown' || format === 'md') {
    return writeMarkdown(file, res.rows, { style: v['md-style'] || 'full', query: v.query ?? res.meta?.query ?? null,
      ...(v['captured-at'] ? { capturedAt: v['captured-at'] } : {}), downloadMedia: !!v['download-media'],
      maxMediaBytes: num(v['max-media-bytes'], 25 * 1024 * 1024, 'max-media-bytes'), signal });
  }
  if (v['download-media'] || v['md-style'] || v['max-media-bytes'] || v['captured-at']) {
    throw new UsageError('Las opciones Markdown requieren --format markdown o un archivo .md.');
  }
  return { out: writeRows(file, res.rows, { format: v.format, fields: FIELDS_BY_KIND[kind] }), warnings: [] };
}

// ---- commands --------------------------------------------------------------

const COLLECTORS = {
  'user-tweets': { kind: 'tweets', args: 1, run: (c, a, v) => collect.userTweets(c, a[0], num(v.n, 40, 'n')) },
  media: { kind: 'tweets', args: 1, run: (c, a, v) => collect.userMedia(c, a[0], num(v.n, 40, 'n')) },
  timelines: { kind: 'tweets', list: 'users-file', run: (c, a, v) => collect.timelines(c, a, num(v.n, 40, 'n')) },
  search: {
    kind: 'tweets',
    args: 1,
    run: (c, a, v) =>
      collect.search(c, a[0], num(v.n, 40, 'n'), { product: v.product || 'Latest', since: v.since, until: v.until }),
  },
  replies: { kind: 'tweets', args: 1, run: (c, a, v) => collect.replies(c, a[0], num(v.n, 40, 'n')) },
  tweets: { kind: 'tweets', list: 'urls-file', run: (c, a) => collect.tweetsData(c, a) },
  'public-tweet': { kind: 'tweets', args: 1, run: (c, a) => collect.publicTweet(c, a[0]) },
  thread: { kind: 'thread', args: 1, run: (c, a, v) => collect.thread(c, a[0], num(v.n, 40, 'n'),
    { maxDetails: num(v['max-details'], 10, 'max-details') }) },
  article: { kind: 'article', args: 1, run: (c, a) => collect.article(c, a[0]) },
  'list-tweets': { kind: 'tweets', args: 1, run: (c, a, v) => collect.listTweets(c, a[0], num(v.n, 40, 'n')) },
  users: { kind: 'users', list: 'users-file', run: (c, a) => collect.usersData(c, a) },
  about: { kind: 'about', list: 'users-file', run: (c, a) => collect.usersAbout(c, a) },
  'users-search': { kind: 'users', args: 1, run: (c, a, v) => collect.usersSearch(c, a[0], num(v.n, 40, 'n')) },
  followers: { kind: 'users', args: 1, run: (c, a, v) => collect.followers(c, a[0], num(v.n, 100, 'n')) },
  following: { kind: 'users', args: 1, run: (c, a, v) => collect.following(c, a[0], num(v.n, 100, 'n')) },
  retweeters: { kind: 'users', args: 1, run: (c, a, v) => collect.retweeters(c, a[0], num(v.n, 100, 'n')) },
  'list-members': { kind: 'users', args: 1, run: (c, a, v) => collect.listMembers(c, a[0], num(v.n, 100, 'n')) },
};

async function runCollector(name, spec, pos, v, signal) {
  let args = pos;
  if (spec.list && v[spec.list]) args = [...args, ...linesOf(v[spec.list])];
  if (spec.args === 1 && args.length !== 1) throw new UsageError(`${name} takes exactly one argument (quote queries with spaces).`);
  if (!args.length) throw new UsageError(`${name} needs at least one argument.`);
  const { ctx, warnings, done } = makeCtx(v, signal);
  let res;
  try {
    res = await spec.run(ctx, args, v);
  } finally {
    done();
  }
  const saved = await saveDataset(v, res, spec.kind, signal);
  return {
    ok: true,
    command: name,
    ...saved,
    ...(signal.aborted ? { interrupted: true } : {}),
    ...(res.meta || {}),
    warnings: [...warnings, ...saved.warnings],
    summary: an.summarize(res.rows, 3),
  };
}

async function runLive(pos, v, signal) {
  if (pos.length !== 1) throw new UsageError('live takes exactly one search query (quote it).');
  const interval = num(v.interval, 300, 'interval');
  const duration = num(v.duration, 3600, 'duration');
  if (interval < 60) throw new UsageError('--interval must be >= 60 seconds.');
  if (!(duration > 0)) throw new UsageError('--duration must be > 0 seconds.');
  const { ctx, warnings, done } = makeCtx(v, signal);
  const file = outPath(v.out, 'api_live_' + pos[0].replace(/[^A-Za-z0-9]+/g, '_'));
  let saved = false;
  log(`Live capture of: ${pos[0]} (every ${interval} s for ${duration} s) -> ${file}`);
  let res;
  try {
    res = await collect.live(ctx, pos[0], {
      interval,
      duration,
      n: num(v.n, 100, 'n'),
      maxTweets: num(v['max-tweets'], Infinity, 'max-tweets'),
      onRound: (rows, info) => {
        if (info.added) {
          writeRows(file, rows, { format: v.format, fields: TWEET_FIELDS });
          saved = true;
        }
        ctx.log(`${new Date().toTimeString().slice(0, 8)} | round ${info.round}: ${info.added} new | total: ${info.total}`);
      },
    });
  } finally {
    done();
  }
  return {
    ok: true,
    command: 'live',
    out: saved ? path.resolve(file) : null,
    ...(signal.aborted ? { interrupted: true } : {}),
    ...res.meta,
    warnings,
    summary: an.summarize(res.rows, 3),
  };
}

function readInput(v) {
  if (!v.in) throw new UsageError('--in <dataset file> is required.');
  return readRows(v.in);
}

function writeChart(file, svg) {
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, svg, 'utf8');
  return path.resolve(file);
}

/** Writes the full table with --out; returns it inline only if short. */
function tableResult(command, rows, v, extra = {}) {
  const out = v.out ? writeRows(v.out, rows, { format: v.format }) : null;
  return { ok: true, command, rows: rows.length, ...(out ? { out } : {}), ...extra, ...(out && rows.length > 50 ? {} : { result: rows.slice(0, 200) }) };
}

const ANALYSIS = {
  summary: (pos, v) => ({ ok: true, command: 'summary', in: path.resolve(v.in ?? ''), ...an.summarize(readInput(v), num(v.top, 5, 'top')) }),

  convert: async (pos, v) => {
    if (!v.out) throw new UsageError('convert needs --out (extension sets the format: .jsonl, .json, .csv, .md).');
    const rows = readInput(v);
    return { ok: true, command: 'convert', rows: rows.length,
      ...await saveDataset(v, { rows, prefix: 'converted' }, null) };
  },

  hashtags: (pos, v) => {
    const rows = readInput(v);
    if (v['per-tweet']) {
      if (!v.out) throw new UsageError('--per-tweet needs --out.');
      return { ok: true, command: 'hashtags', rows: rows.length, out: writeRows(v.out, an.withHashtags(rows), { format: v.format }) };
    }
    const t = an.hashtagCounts(rows, { top: num(v.top, 20, 'top'), ignoreCase: !!v['ignore-case'], fromText: !!v['from-text'] });
    return tableResult('hashtags', t, v);
  },

  time: (pos, v) => {
    const group = v.group || 'hour';
    const series = an.timeCounts(readInput(v), group);
    const extra = {};
    if (v.chart) extra.chart = writeChart(v.chart, lineChart(series, { title: `Frecuencia de tweets por '${group}'`, color: v.color || 'steelblue' }));
    return tableResult('time', series, v, extra);
  },

  words: (pos, v) => {
    const words = an.wordCounts(readInput(v), {
      lang: v.lang || 'es',
      sw: v.sw ? v.sw.split(',').map((s) => s.trim()).filter(Boolean) : [],
      minFreq: num(v['min-freq'], 3, 'min-freq'),
      maxWords: num(v['max-words'], 100, 'max-words'),
    });
    const extra = {};
    if (v.chart) {
      const wc = wordCloud(words, { shuffle: !!v['random-order'] });
      extra.chart = writeChart(v.chart, wc.svg);
      if (wc.dropped) extra.chart_dropped_words = wc.dropped;
    }
    return tableResult('words', words, v, extra);
  },

  emojis: (pos, v) => {
    const top = num(v.top, 10, 'top');
    const t = an.emojiCounts(readInput(v), top);
    const extra = {};
    if (v.chart) {
      const svg = barChart(t.map((d) => ({ label: d.emoji, n: d.n })), { title: `Top ${t.length} emojis más usados`, fill: v.fill || 'skyblue', stroke: v.color || 'grey' });
      extra.chart = writeChart(v.chart, svg);
    }
    return tableResult('emojis', t, v, extra);
  },

  'img-report': (pos, v) => {
    if (!v.out) throw new UsageError('img-report needs --out <report.html>.');
    const rows = readInput(v);
    fs.writeFileSync(v.out, imageReport(rows, v.out), 'utf8');
    return { ok: true, command: 'img-report', images: rows.length, out: path.resolve(v.out) };
  },
};

/** Runs an OpenAI analysis writing results incrementally (JSONL) so an interruption keeps what was done. */
async function runOpenAI(command, items, worker, v, signal) {
  const key = apiKey();
  const opts = { key, model: v.model || 'gpt-4o-mini' };
  const file = outPath(v.out, command === 'sentiment' ? 'results_tweets_analyze' : 'results_images_analyze');
  const incremental = formatOf(file, v.format) === 'jsonl';
  if (incremental) fs.writeFileSync(file, '');
  let doneN = 0;
  let failed = 0;
  const results = await mapLimit(
    items,
    num(v.concurrency, 4, 'concurrency') || 1,
    (it) => (signal.aborted ? null : worker(it, opts)),
    (i, r) => {
      if (!r) return;
      doneN++;
      if (r.error) failed++;
      if (incremental) appendJsonl(file, r);
      if (process.stderr.isTTY || doneN % 25 === 0 || doneN === items.length) log(`[${command}] ${doneN}/${items.length}`);
    }
  );
  const rows = results.filter(Boolean);
  writeRows(file, rows, { format: v.format }); // final file in input order
  return { rows, out: path.resolve(file), failed };
}

async function runSentiment(pos, v, signal) {
  let items;
  if (v.text?.length) items = v.text.map((t) => ({ tweet: t }));
  else items = readInput(v).filter((r) => an.textOf(r)).map((r) => ({ tweet: an.textOf(r), tweet_id: r.tweet_id, url: r.url }));
  if (v.limit) items = items.slice(0, num(v.limit, 0, 'limit'));
  if (!items.length) throw new UsageError('No texts to analyze (use --in <dataset> or --text "...").');
  const res = await runOpenAI('sentiment', items, analyzeTweet, v, signal);
  return { ok: true, command: 'sentiment', analyzed: res.rows.length, failed: res.failed, out: res.out, summary: an.summarize(res.rows) };
}

async function runImages(pos, v, signal) {
  let items = v.img?.length ? v.img.map((src) => ({ src })) : photosOf(readInput(v));
  if (v.limit) items = items.slice(0, num(v.limit, 0, 'limit'));
  if (!items.length) throw new UsageError('No images to analyze (use --in <tweets dataset> or --img <url|path>).');
  const res = await runOpenAI('images', items, analyzeImage, v, signal);
  const out = { ok: true, command: 'images', analyzed: res.rows.length, failed: res.failed, out: res.out, summary: an.summarize(res.rows) };
  if (v.report) {
    fs.writeFileSync(v.report, imageReport(res.rows, v.report), 'utf8');
    out.report = path.resolve(v.report);
  }
  return out;
}

// ---- setup, session and accounts -------------------------------------------

function runInstall() {
  const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  log(`Installing the engine in ${SKILL_DIR} (Playwright + Chromium; this may take a while)...`);
  const r = spawnSync(npm, ['install', '--no-fund', '--no-audit'], { cwd: SKILL_DIR, stdio: ['ignore', 'inherit', 'inherit'], shell: process.platform === 'win32' });
  if (r.status !== 0) throw new Error(`npm install failed (exit ${r.status}).`);
  return { ok: true, command: 'install', ...engine.doctor() };
}

function runDoctor() {
  const d = engine.doctor();
  const accounts = fs.existsSync(path.join(pool.dataDir(), 'accounts.sqlite')) ? pool.describe() : [];
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  return {
    ok: !!d.playwright && d.chromiumInstalled,
    command: 'doctor',
    ...d,
    node_ok: nodeMajor >= 22,
    data_dir: pool.dataDir(),
    accounts_total: accounts.length,
    accounts_active: accounts.filter((a) => a.activa).length,
    ...(d.playwright ? {} : { hint: 'Run: node scripts/tweetscraper.mjs install' }),
  };
}

function cookiesFrom(v) {
  if (v['cookies-file']) return pool.parseCookies(fs.readFileSync(v['cookies-file'], 'utf8'));
  if (v['from-env'] != null) {
    const p = v['from-env'] || 'X';
    if (process.env[p + '_COOKIES']) return pool.parseCookies(process.env[p + '_COOKIES']);
    return { authToken: process.env[p + '_AUTH_TOKEN'] || null, ct0: process.env[p + '_CT0'] || null };
  }
  return { authToken: v['auth-token'] || null, ct0: v.ct0 || null };
}

async function validate(names) {
  const rows = pool.all().filter((r) => !names.length || names.some((n) => n.toLowerCase() === r.username.toLowerCase()));
  if (!rows.length) throw new Error('There are no accounts to validate. Import one with: session import');
  const out = [];
  for (const acc of rows) {
    const proxy = pool.effectiveProxy(acc, null);
    log(`Validating "${acc.username}"...`);
    let valida = null;
    let usuario = null;
    let motivo = null;
    try {
      const r = await engine.whoami({ storageStatePath: acc.state_path, proxy, userAgent: acc.user_agent });
      valida = r.valid;
      usuario = r.screenName;
      if (!valida) {
        motivo = {
          expired: 'session expired or revoked',
          locked: 'account locked by X (unlock it at x.com/account/access)',
        }[r.reason] || 'X does not load the account (error or pending check on x.com)';
        if (r.reason === 'expired' || r.reason === 'locked') pool.markInvalid(acc.username, motivo);
      } else pool.markValid(acc.username, usuario);
    } catch (e) {
      const code = /net::ERR_[A-Z_]+/.exec(e.message)?.[0];
      motivo = proxy && code
        ? `could not connect through the proxy (${code.slice(5)}): check address, user and password, or remove it`
        : 'engine error: ' + e.message;
    }
    out.push({ cuenta: acc.username, valida, usuario_x: usuario, motivo });
  }
  const merged = [];
  for (const u of new Set(out.filter((r) => r.valida && r.usuario_x).map((r) => r.usuario_x))) {
    const dropped = pool.dedupe(u);
    if (dropped.length) merged.push({ usuario_x: u, removed: dropped });
  }
  return { accounts: out, ...(merged.length ? { merged_duplicates: merged } : {}) };
}

/** Hidden terminal input (nothing echoed). */
function askSecret(prompt) {
  return new Promise((resolve) => {
    process.stderr.write(prompt);
    const stdin = process.stdin;
    let buf = '';
    stdin.setRawMode(true);
    stdin.resume();
    stdin.setEncoding('utf8');
    const onData = (ch) => {
      for (const c of ch) {
        if (c === '\r' || c === '\n') {
          stdin.setRawMode(false);
          stdin.pause();
          stdin.off('data', onData);
          process.stderr.write('\n');
          return resolve(buf);
        }
        if (c === '\u0003') process.exit(130);
        if (c === '\u007f' || c === '\b') buf = buf.slice(0, -1);
        else buf += c;
      }
    };
    stdin.on('data', onData);
  });
}

function askLine(prompt) {
  return new Promise((resolve) => {
    process.stderr.write(prompt);
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    process.stdin.once('data', (d) => {
      process.stdin.pause();
      resolve(String(d).trim());
    });
  });
}

async function runSetup(v) {
  if (!process.stdin.isTTY) {
    throw new Error('accounts setup is interactive: run it in your own terminal. In scripts use: session import --from-env / --cookies-file');
  }
  log('Load X accounts. For each one copy the auth_token and ct0 cookies of x.com (F12 -> Application -> Cookies).\nLeave the name empty to finish.\n');
  for (;;) {
    const account = await askLine('Account name (Enter to finish): ');
    if (!account) break;
    let auth = (await askSecret(`auth_token of "${account}" (or the cookie header): `)).trim();
    let ct0;
    if (auth.includes('auth_token')) ({ authToken: auth, ct0 } = pool.parseCookies(auth));
    else ct0 = (await askSecret(`ct0 of "${account}": `)).trim();
    if (!auth || !ct0) {
      log(`Missing auth_token or ct0; skipping "${account}".\n`);
      continue;
    }
    let proxy;
    for (;;) {
      try {
        proxy = pool.checkProxy(await askLine('Proxy (optional, Enter for none): '));
        break;
      } catch (e) {
        log(e.message);
      }
    }
    pool.importSession({ authToken: auth, ct0, account, proxy });
    if (!v['no-validate']) {
      const r = (await validate([account])).accounts[0];
      log(r.valida ? `OK: "${account}" is @${r.usuario_x}.\n` : `"${account}" does not work: ${r.motivo}. Load it again with the same name.\n`);
    }
  }
  return { ok: true, command: 'accounts setup', accounts: pool.describe() };
}

async function runSession(pos, v) {
  if (pos[0] !== 'import') throw new UsageError('Usage: session import [--account NAME] (--from-env [PREFIX] | --cookies-file FILE | --auth-token T --ct0 C)');
  const { authToken, ct0 } = cookiesFrom(v);
  const account = v.account || 'default';
  pool.importSession({ authToken, ct0, account, proxy: v.proxy });
  const res = { ok: true, command: 'session import', account };
  if (!v['no-validate']) Object.assign(res, await validate([account]));
  return res;
}

async function runLogin(v) {
  const account = v.account || 'default';
  const state = pool.get(account)?.state_path || pool.sessionPath(account);
  const proxy = v.proxy ? pool.checkProxy(v.proxy) : null;
  let r;
  if (v.manual) {
    r = await engine.manualLogin({ storageStatePath: state, waitSeconds: num(v.wait, 420, 'wait'), proxy, onLog: log });
  } else {
    const user = process.env.TWITTER_USER;
    const pass = process.env.TWITTER_PASS;
    if (!user || !pass) throw new UsageError('Automated login reads TWITTER_USER and TWITTER_PASS (and optional TWITTER_EMAIL) from the environment.');
    r = await engine.login({ user, pass, email: process.env.TWITTER_EMAIL || '', storageStatePath: state, headless: !v.headed, proxy, shotDir: pool.dataDir(), onLog: log });
  }
  if (!r.ok) {
    if (r.limited) throw new Error('X temporarily limited the login (rate limit). Wait a while and retry.');
    throw new Error(`Login failed (${r.reason}). ${(r.hint || '').slice(0, 200)}`);
  }
  pool.upsert(account, state, { proxy });
  return { ok: true, command: 'login', account };
}

async function runAccounts(pos, v) {
  const [sub, ...names] = pos;
  switch (sub ?? 'list') {
    case 'list':
      return { ok: true, command: 'accounts list', accounts: pool.describe() };
    case 'check':
      return { ok: true, command: 'accounts check', ...(await validate(names)) };
    case 'add': {
      if (names.length !== 1) throw new UsageError('Usage: accounts add <accounts.csv> (columns account, auth_token, ct0, proxy)');
      const text = fs.readFileSync(names[0], 'utf8').replace(/^\ufeff/, '');
      const [head, ...lines] = text.split(/\r?\n/).filter((l) => l.trim());
      const seps = [',', ';', '\t'];
      const sep = seps.reduce((a, s) => (head.split(s).length > head.split(a).length ? s : a));
      const cols = head.split(sep).map((c) => c.trim().toLowerCase());
      const missing = ['account', 'auth_token', 'ct0'].filter((c) => !cols.includes(c));
      if (missing.length) throw new Error('Missing columns: ' + missing.join(', '));
      const added = [];
      for (const l of lines) {
        const r = Object.fromEntries(l.split(sep).map((x, i) => [cols[i], x.trim()]));
        pool.importSession({ authToken: r.auth_token, ct0: r.ct0, account: r.account, proxy: r.proxy || null });
        added.push(r.account);
      }
      const res = { ok: true, command: 'accounts add', added };
      if (!v['no-validate'] && added.length) Object.assign(res, await validate(added));
      return res;
    }
    case 'remove':
      if (!names.length) throw new UsageError('Usage: accounts remove <name...>');
      return { ok: true, command: 'accounts remove', removed: names.filter((n) => pool.remove(n)) };
    case 'reactivate':
      if (!names.length) throw new UsageError('Usage: accounts reactivate <name...>');
      return { ok: true, command: 'accounts reactivate', reactivated: names.filter((n) => pool.reactivate(n)) };
    case 'reset-locks':
      return { ok: true, command: 'accounts reset-locks', accounts: pool.resetLocks() };
    case 'proxy': {
      if (!names.length || v.proxy == null) throw new UsageError('Usage: accounts proxy <name...> --proxy <http://user:pass@host:port | none>');
      const px = pool.checkProxy(v.proxy);
      const missing = names.filter((n) => !pool.get(n));
      if (missing.length) throw new Error('Not in the pool: ' + missing.join(', '));
      for (const n of names) pool.setProxy(n, px);
      const res = { ok: true, command: 'accounts proxy', accounts: names, proxy: px ? 'set' : 'removed' };
      if (!v['no-validate']) Object.assign(res, await validate(names));
      return res;
    }
    case 'setup':
      return runSetup(v);
    default:
      throw new UsageError(`Unknown accounts subcommand "${sub}". Use: list, check, add, remove, reactivate, reset-locks, proxy, setup.`);
  }
}

const HELP = `tweetscraper — collect and analyze X/Twitter data (port of TweetScraperR)

Setup:     install | doctor
Session:   session import [--account A] (--from-env [PREFIX] | --cookies-file F | --auth-token T --ct0 C)
           login --manual [--account A] | login [--headed]   (env TWITTER_USER, TWITTER_PASS)
Accounts:  accounts list|check [A...]|add <csv>|remove A...|reactivate A...|reset-locks|proxy A... --proxy P|setup
Tweets:    user-tweets <user> | media <user> | timelines <user...> | search <query> [--product Latest|Top|Media]
           [--since D --until D] | live <query> [--interval 300 --duration 3600] | replies <url>
           tweets <url...> | public-tweet <url> (no login) | thread <url> [--max-details 10] | article <url> | list-tweets <list>
Users:     users <user...> | about <user...> | users-search <query> | followers <user> | following <user>
           retweeters <url> | list-members <list>
Analysis:  summary | convert | hashtags | time [--group hour|day|week|month|year] [--chart f.svg]
           words [--lang es --chart f.svg] | emojis [--chart f.svg]  (all with --in <dataset>)
           convert -i F -o note.md [--md-style compact|full --query Q --captured-at ISO --download-media --max-media-bytes N]
OpenAI:    sentiment (--in F | --text T...) | images (--in F | --img X...) [--report r.html] | img-report --in F --out r.html
Common:    -n N  -o/--out FILE(.jsonl|.json|.csv|-)  --wait-timeout S  --proxy P  --debug-dir D  --headed

See references/commands.md for every option and references/schema.md for the columns.`;

export async function main(argv) {
  const controller = new AbortController();
  let interrupts = 0;
  process.on('SIGINT', () => {
    if (++interrupts > 1) process.exit(130);
    log('\nInterrupted: finishing with what was collected (Ctrl+C again to quit now)...');
    controller.abort();
  });
  let result;
  try {
    const { values: v, positionals } = parseArgs({ args: argv, options: OPTIONS, allowPositionals: true, strict: true });
    const [cmd, ...pos] = positionals;
    if (!cmd || v.help || cmd === 'help') {
      process.stderr.write(HELP + '\n');
      return;
    }
    const signal = controller.signal;
    if (COLLECTORS[cmd]) result = await runCollector(cmd, COLLECTORS[cmd], pos, v, signal);
    else if (cmd === 'live') result = await runLive(pos, v, signal);
    else if (ANALYSIS[cmd]) result = await ANALYSIS[cmd](pos, v);
    else if (cmd === 'sentiment') result = await runSentiment(pos, v, signal);
    else if (cmd === 'images') result = await runImages(pos, v, signal);
    else if (cmd === 'install') result = runInstall();
    else if (cmd === 'doctor') result = runDoctor();
    else if (cmd === 'session') result = await runSession(pos, v);
    else if (cmd === 'login') result = await runLogin(v);
    else if (cmd === 'accounts') result = await runAccounts(pos, v);
    else throw new UsageError(`Unknown command "${cmd}". Run with --help.`);
  } catch (e) {
    result = { ok: false, error: e.message, ...(e instanceof UsageError || e.code === 'ERR_PARSE_ARGS_UNKNOWN_OPTION' ? { usage: true } : {}) };
    process.exitCode = 1;
  }
  if (result.out === '-') return; // dataset already went to stdout
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  if (result.ok === false) process.exitCode = 1;
}
