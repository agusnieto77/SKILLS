import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  parseTwitterDate, parseMsec, findInstructions, parseTimelineTweets, tweetRow, parseUsers, userRow,
  aboutRow, extractEmojis, extractHashtags, scanBody, TWEET_FIELDS, USER_FIELDS,
} from '../scripts/lib/parse.mjs';

const fx = (name) => JSON.parse(fs.readFileSync(new URL('./fixtures/' + name, import.meta.url), 'utf8'));

test('parseTwitterDate reads the Twitter format as UTC, null on bad input', () => {
  assert.equal(parseTwitterDate('Fri Jun 12 21:22:33 +0000 2026'), '2026-06-12T21:22:33Z');
  assert.equal(parseTwitterDate(null), null);
  assert.equal(parseTwitterDate('basura'), null);
});

test('parseMsec hides the negative dates X uses to mask values', () => {
  assert.equal(parseMsec('1700000000000'), '2023-11-14T22:13:20Z');
  assert.equal(parseMsec('-95617584000000'), null);
  assert.equal(parseMsec(null), null);
});

test('timeline parser: tweets, metrics, entities, media and cursor (UserTweets)', () => {
  const { tweets, cursor } = parseTimelineTweets(fx('user_tweets.json'));
  assert.equal(tweets.length, 2);
  assert.equal(cursor, 'CURSOR_ABC');
  assert.deepEqual(Object.keys(tweets[0]), TWEET_FIELDS);
  assert.equal(TWEET_FIELDS.length, 31);
  const [t1, t2] = tweets;
  assert.equal(t1.user, '@NASA');
  assert.equal(t1.texto, 'Texto rico uno #RStats');
  assert.equal(t1.megustas, 7203);
  assert.equal(t1.views, 470857);
  assert.equal(t1.es_cita, false);
  assert.equal(t1.url, 'https://x.com/NASA/status/1001');
  assert.equal(t1.fecha, '2026-06-12T21:22:33Z');
  assert.equal(t1.idioma, 'es');
  assert.deepEqual(t1.hashtags, ['RStats']);
  assert.deepEqual(t1.menciones, ['NASA']);
  assert.deepEqual(t1.urls_externas, ['https://example.com/a']);
  assert.deepEqual(t1.media, ['https://pbs.twimg.com/media/x.jpg']);
  assert.deepEqual(t1.media_tipo, ['photo']);
  assert.equal(t1.conversation_id, '1001');
  // legacy screen_name fallback + TweetWithVisibilityResults unwrapped
  assert.equal(t2.user, '@NASA');
  assert.equal(t2.es_cita, true);
  assert.equal(t2.tweet_id, '1002');
  assert.equal(t2.tweet_citado_id, '999');
});

test('tweetRow uses the full text of long tweets (note_tweet) and its entities', () => {
  const largo = 'palabra '.repeat(60);
  const row = tweetRow({
    rest_id: '7001',
    source: '<a href="http://twitter.com/download/iphone" rel="nofollow">Twitter for iPhone</a>',
    core: { user_results: { result: { rest_id: '42', core: { screen_name: 'ana' } } } },
    edit_control: { edit_tweet_ids: ['7000', '7001'] },
    note_tweet: {
      note_tweet_results: {
        result: {
          text: largo + ' #RStats @NASA',
          entity_set: { hashtags: [{ text: 'RStats' }], user_mentions: [{ screen_name: 'NASA' }] },
        },
      },
    },
    legacy: {
      full_text: 'palabra palabra palabra …',
      created_at: 'Fri Jun 12 21:22:33 +0000 2026',
      entities: { hashtags: [], user_mentions: [] },
      bookmark_count: 5,
      in_reply_to_status_id_str: '6999',
      in_reply_to_screen_name: 'beto',
      place: { full_name: 'Mar del Plata, Argentina', country: 'Argentina' },
    },
  });
  assert.equal(row.texto, largo + ' #RStats @NASA');
  assert.deepEqual(row.hashtags, ['RStats']);
  assert.deepEqual(row.menciones, ['NASA']);
  assert.equal(row.user_id, '42');
  assert.equal(row.respuesta_a_id, '6999');
  assert.equal(row.respuesta_a_user, '@beto');
  assert.equal(row.guardados, 5);
  assert.equal(row.fuente, 'Twitter for iPhone');
  assert.equal(row.editado, true);
  assert.equal(row.lugar, 'Mar del Plata, Argentina');
  assert.equal(row.pais, 'Argentina');
  assert.equal(row.retweet_id, null);
});

test('videos keep the highest-bitrate mp4; retweets point to the original', () => {
  const row = tweetRow({
    rest_id: '1',
    core: { user_results: { result: { core: { screen_name: 'a' } } } },
    legacy: {
      full_text: 'RT',
      retweeted_status_result: { result: { rest_id: '900' } },
      extended_entities: {
        media: [{
          type: 'video',
          media_url_https: 'https://pbs.twimg.com/thumb.jpg',
          video_info: {
            variants: [
              { content_type: 'application/x-mpegURL', url: 'https://v/x.m3u8' },
              { content_type: 'video/mp4', bitrate: 256000, url: 'https://v/low.mp4' },
              { content_type: 'video/mp4', bitrate: 2176000, url: 'https://v/high.mp4' },
            ],
          },
        }],
      },
    },
  });
  assert.deepEqual(row.media, ['https://v/high.mp4']);
  assert.deepEqual(row.media_tipo, ['video']);
  assert.equal(row.es_retweet, true);
  assert.equal(row.retweet_id, '900');
});

test('empty timelines yield no tweets; findInstructions handles both paths', () => {
  const vacio = { data: { user: { result: { timeline: { timeline: { instructions: [{ type: 'TimelineAddEntries', entries: [] }] } } } } } };
  assert.deepEqual(parseTimelineTweets(vacio).tweets, []);
  assert.ok(Array.isArray(findInstructions(fx('user_tweets.json'))));
  assert.ok(Array.isArray(findInstructions(fx('search_timeline.json'))));
  assert.equal(findInstructions({ a: 1, b: 'x' }), null);
});

test('SearchTimeline path', () => {
  const { tweets, cursor } = parseTimelineTweets(fx('search_timeline.json'));
  assert.equal(tweets.length, 1);
  assert.equal(tweets[0].user, '@RosanaFerrero');
  assert.equal(tweets[0].url, 'https://x.com/RosanaFerrero/status/3001');
  assert.equal(tweets[0].views, 1234);
  assert.equal(cursor, 'SEARCH_CURSOR');
});

test('TweetDetail: conversationthread modules are unpacked (tweet + replies)', () => {
  const { tweets, cursor } = parseTimelineTweets(fx('tweet_detail.json'));
  assert.deepEqual(tweets.map((t) => t.tweet_id).sort(), ['5000', '5001', '5002']);
  assert.equal(cursor, 'TDCURSOR');
});

test('user parser: schema, legacy fallbacks and profile fields', () => {
  const { users, cursor } = parseUsers(fx('users_list.json'));
  assert.equal(users.length, 2);
  assert.equal(cursor, 'UCURSOR');
  assert.deepEqual(Object.keys(users[0]), USER_FIELDS);
  assert.equal(USER_FIELDS.length, 18);
  const u = users[0];
  assert.equal(u.user, '@RosanaFerrero');
  assert.equal(u.nombre, 'Rosana');
  assert.equal(u.seguidores, 1200);
  assert.equal(u.verificado, true);
  assert.equal(u.ubicacion, 'Buenos Aires');
  assert.equal(u.url, 'https://x.com/RosanaFerrero');
  assert.equal(u.fecha_creacion, '2026-06-13T06:00:23Z');
  assert.equal(u.sitio_web, 'https://RosanaFerrero.org');
  assert.match(u.imagen_perfil, /^https:\/\/pbs\.twimg\.com\/profile_images\//);
  assert.match(u.banner, /^https:\/\/pbs\.twimg\.com\/profile_banners\//);
});

test('2026-10 user schema without legacy', () => {
  const u = userRow({
    rest_id: '5',
    core: { screen_name: 'x', name: 'X', created_at: 'Fri Jun 13 06:00:23 +0000 2026' },
    relationship_counts: { followers: 10, following: 3 },
    tweet_counts: { tweets: 99, media_tweets: 4 },
    action_counts: { favorites_count: 7 },
    profile_bio: { description: 'bio' },
    privacy: { protected: true },
    verification: { verified_type: 'Business' },
  });
  assert.deepEqual(
    [u.seguidores, u.siguiendo, u.tweets, u.tweets_media, u.favoritos, u.descripcion, u.protegida, u.verificado, u.tipo_verificacion],
    [10, 3, 99, 4, 7, 'bio', true, true, 'Business']
  );
  assert.equal(userRow(null), null);
  assert.equal(userRow({ legacy: { name: 'x' } }), null);
});

test('aboutRow maps the "About this account" card', () => {
  const r = aboutRow({
    rest_id: '1',
    core: { screen_name: 'NASA', name: 'NASA', created_at: 'Fri Jun 13 06:00:23 +0000 2026' },
    about_profile: {
      account_based_in: 'United States', location_accurate: true, source: 'United States App Store',
      username_changes: { count: '2', last_changed_at_msec: '1700000000000' },
    },
    verification_info: { is_identity_verified: false, reason: { verified_since_msec: '-1' } },
  });
  assert.equal(r.pais_cuenta, 'United States');
  assert.equal(r.ubicacion_precisa, true);
  assert.equal(r.cambios_usuario, 2);
  assert.equal(r.ultimo_cambio_usuario, '2023-11-14T22:13:20Z');
  assert.equal(r.identidad_verificada, false);
  assert.equal(r.verificada_desde, null);
});

test('extractEmojis keeps whole grapheme clusters (ZWJ, skin tones, flags)', () => {
  assert.deepEqual(extractEmojis('hola 🔬🧠 mundo'), ['🔬', '🧠']);
  assert.deepEqual(extractEmojis('👩‍💻 y 👍🏽 en 🇦🇷'), ['👩‍💻', '👍🏽', '🇦🇷']);
  assert.deepEqual(extractEmojis('sin emojis © 2026'), []);
  assert.deepEqual(extractEmojis(null), []);
});

test('extractHashtags is Unicode-aware and drops the #', () => {
  assert.deepEqual(extractHashtags('Un #tweet con #Educación y #año2026!'), ['tweet', 'Educación', 'año2026']);
  assert.deepEqual(extractHashtags('sin hashtags'), []);
});

test('scanBody counts new tweets once and ignores quoted tweets', () => {
  const seenT = new Set();
  const seenU = new Set();
  const first = scanBody(fx('user_tweets.json'), seenT, seenU);
  assert.equal(first.tweets, 2); // 999 (quoted) not counted
  assert.equal(first.cursor, 'CURSOR_ABC');
  assert.equal(scanBody(fx('user_tweets.json'), seenT, seenU).tweets, 0);
  assert.equal(scanBody(fx('users_list.json'), seenT, seenU).users, 2);
});
