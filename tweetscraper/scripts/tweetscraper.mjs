#!/usr/bin/env node
// tweetscraper — collect and analyze X/Twitter data (Node.js port of TweetScraperR).
//
// stdout carries exactly one JSON document per run (the result or {ok:false, error});
// progress and logs go to stderr. Datasets are written to files (JSONL by default).

// node:sqlite prints an ExperimentalWarning on Node 22; it is noise for this CLI.
process.removeAllListeners('warning');
process.on('warning', (w) => {
  if (w.name !== 'ExperimentalWarning') process.stderr.write(`${w.name}: ${w.message}\n`);
});

const { main } = await import('./lib/cli.mjs');
await main(process.argv.slice(2));
