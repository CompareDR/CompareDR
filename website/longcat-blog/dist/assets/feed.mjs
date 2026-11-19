// Pure data contract shared by the browser, publisher, and offline tests.
export const DIMENSIONS = ['D1', 'D2', 'D3', 'D4', 'D5_D6'];
const fail = message => { throw new Error(message); };
const text = (v, max = 180) => typeof v === 'string' && v.trim().length > 0 && v.length <= max && !/[<>\u0000-\u001f]/.test(v);
const finite = v => typeof v === 'number' && Number.isFinite(v);
const integer = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
export function validateFeed(input) {
  const d = input;
  if (!d || d.schema_version !== 1 || d.benchmark !== 'CompareDR') fail('Unsupported leaderboard schema');
  if (!text(d.revision, 80) || !/^[a-zA-Z0-9._-]+$/.test(d.revision)) fail('Invalid revision');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d.snapshot_date || '') || new Date(d.snapshot_date).toISOString().slice(0, 10) !== d.snapshot_date) fail('Invalid snapshot date');
  if (!text(d.cohort) || !integer(d.systems, 2, 500) || !integer(d.queries, 1, 100000)) fail('Invalid cohort');
  if (d.reports !== d.systems * d.queries || d.within_query_pairs !== d.queries * d.systems * (d.systems - 1) / 2) fail('Inconsistent complete-cohort counts');
  if (JSON.stringify(d.score_scale) !== '[0,100]') fail('Unsupported score scale');
  if (!d.weights || Object.keys(d.weights).sort().join() !== [...DIMENSIONS].sort().join() || DIMENSIONS.some(k => !finite(d.weights[k]) || d.weights[k] < 0) || Math.abs(DIMENSIONS.reduce((s, k) => s + d.weights[k], 0) - 100) > 1e-8) fail('Invalid weights');
  if (!d.protocol || ['judge', 'reasoning', 'verifier', 'verifier_reasoning', 'note'].some(k => !text(d.protocol[k], 500))) fail('Missing judging protocol');
  if (!text(d.comparison_scope, 1000)) fail('Missing comparison scope');
  if (!Array.isArray(d.rows) || d.rows.length !== d.systems) fail('Incorrect system count');
  const keys = new Set();
  for (const r of d.rows) {
    if (!text(r.model) || !text(r.harness)) fail('Invalid system identity');
    const key = JSON.stringify([r.model, r.harness]);
    if (keys.has(key)) fail('Duplicate system');
    keys.add(key);
    if ([...DIMENSIONS, 'overall'].some(k => !finite(r[k]) || r[k] < 0 || r[k] > 100)) fail('Invalid score');
    const weighted = DIMENSIONS.reduce((s, k) => s + r[k] * d.weights[k] / 100, 0);
    if (Math.abs(weighted - r.overall) > 1e-6) fail('Overall does not match full-precision weighted dimensions');
  }
  // Ignore supplied ranks: derive competition rank from full-precision overall.
  const rows = d.rows.map(r => Object.fromEntries(['model', 'harness', ...DIMENSIONS, 'overall'].map(k => [k, r[k]])))
    .sort((a, b) => b.overall - a.overall || a.harness.localeCompare(b.harness));
  rows.forEach((r, i) => { r.rank = i && r.overall === rows[i - 1].overall ? rows[i - 1].rank : i + 1; });
  return {
    schema_version: 1, revision: d.revision, benchmark: d.benchmark,
    snapshot_date: d.snapshot_date, cohort: d.cohort, systems: d.systems,
    queries: d.queries, reports: d.reports, within_query_pairs: d.within_query_pairs,
    score_scale: [0, 100], weights: {...d.weights},
    protocol: Object.fromEntries(['judge', 'reasoning', 'verifier', 'verifier_reasoning', 'note'].map(k => [k, d.protocol[k]])),
    comparison_scope: d.comparison_scope, rows
  };
}
export function safeFeedURL(value, allowedOrigins) {
  const u = new URL(value);
  if (u.protocol !== 'https:' || u.username || u.password || u.hash || u.search || !allowedOrigins.includes(u.origin) || !u.pathname.endsWith('.json')) fail('Unapproved feed URL');
  return u.href;
}
export async function fetchFeed(url, {allowedOrigins, timeoutMs = 6000, fetchImpl = fetch} = {}) {
  const target = safeFeedURL(url, allowedOrigins || []);
  const controller = new AbortController();
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => { controller.abort(); reject(new Error('Feed timeout')); }, timeoutMs);
  });
  try {
    return await Promise.race([timeout, (async () => {
      const response = await fetchImpl(target, {signal: controller.signal, mode: 'cors', credentials: 'omit', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer'});
      if (!response.ok) fail('Feed HTTP ' + response.status);
      if (Number(response.headers.get('content-length')) > 1000000) fail('Feed too large');
      const type = response.headers.get('content-type') || '';
      if (!/application\/json|text\/plain|application\/octet-stream/i.test(type)) fail('Unexpected feed content type');
      let body = '';
      if (response.body?.getReader) {
        const reader = response.body.getReader(); const decoder = new TextDecoder(); let bytes = 0;
        try {
          for (;;) { const {done, value} = await reader.read(); if (done) break; bytes += value.byteLength; if (bytes > 1000000) fail('Feed too large'); body += decoder.decode(value, {stream: true}); }
          body += decoder.decode();
        } catch (error) { await reader.cancel().catch(() => {}); throw error; }
      } else { body = await response.text(); if (body.length > 1000000) fail('Feed too large'); }
      return validateFeed(JSON.parse(body));
    })()]);
  } finally { clearTimeout(timer); controller.abort(); }
}
export function chooseFeed(current, candidate) {
  const next = validateFeed(candidate);
  if (next.snapshot_date < current.snapshot_date) fail('Remote snapshot is older than the displayed snapshot');
  if (next.revision === current.revision && JSON.stringify(next) !== JSON.stringify(validateFeed(current))) fail('Revision reused for different data');
  return next;
}
