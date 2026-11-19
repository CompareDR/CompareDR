import {content} from './content.mjs';
import {DIMENSIONS, validateFeed, fetchFeed, chooseFeed} from './feed.mjs';
const config = window.BLOG_CONFIG;
let data = validateFeed(window.BUNDLED_LEADERBOARD);
let lang = new URL(location.href).searchParams.get('lang') === 'en' ? 'en' : 'zh';
let tab = location.hash === '#benchmark' || location.hash === '#leaderboard' ? 'benchmark' : 'technical';
let sortKey = 'overall', descending = true, status = config.feedUrl ? 'snapshot' : 'noSource', busy = false;
let hadRemote = false;
const $ = id => document.getElementById(id);
const t = key => content[lang][key];
const node = (tag, text, className) => { const n = document.createElement(tag); if (text != null) n.textContent = text; if (className) n.className = className; return n; };
function publicLink(url, label) {
  if (typeof url !== 'string') return null;
  try { const u = new URL(url); if (u.protocol !== 'https:' || u.username || u.password) return null; } catch { return null; }
  const a = node('a', label); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;
}
function links(container, entries) {
  container.replaceChildren();
  for (const [key, label, required] of entries) {
    const a = publicLink(config.links[key], t(label));
    if (a) container.append(a);
    else if (required) { const s = node('span', t(label), 'unavailable'); s.append(node('small', t('pending'))); container.append(s); }
  }
}
function updateURL() { const u = new URL(location.href); u.searchParams.set('lang', lang); u.hash = tab; history.replaceState(null, '', u); }
function switchTab(next, focus = false) {
  tab = next;
  for (const name of ['technical', 'benchmark']) { $('panel-' + name).hidden = name !== tab; $('tab-' + name).setAttribute('aria-selected', String(name === tab)); $('tab-' + name).tabIndex = name === tab ? 0 : -1; }
  updateURL(); if (focus) $('tab-' + tab).focus();
}
function renderAuthors() {
  const root = $('authors'); root.replaceChildren(); const list = node('div', null, 'author-list');
  for (const a of window.BLOG_AUTHORS.authors) { const s = node('span', a.name); s.append(node('sup', a.affiliations.join(',') + (a.equal ? ',*' : '') + (a.corresponding ? ',†' : ''))); list.append(s); }
  root.append(list); const affs = node('div', null, 'affiliations'); window.BLOG_AUTHORS.affiliations.forEach((a, i) => affs.append(node('p', `${i + 1}. ${a}`))); root.append(affs, node('p', `* ${t('equal')} · † ${t('corresponding')}`));
}
function renderTable() {
  const tr = node('tr'); tr.append(node('th', t('rank')), node('th', t('system')));
  for (const k of [...DIMENSIONS, 'overall']) { const th = node('th', t(k)); if (k !== 'overall') th.append(node('small', `${data.weights[k]}%`)); th.setAttribute('scope', 'col'); tr.append(th); }
  $('score-head').replaceChildren(tr);
  const rows = [...data.rows].sort((a, b) => (descending ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]) || a.rank - b.rank || a.harness.localeCompare(b.harness));
  const body = document.createDocumentFragment();
  for (const r of rows) { const row = node('tr'); if (r.harness === 'LongCat-DeepResearch') row.classList.add('highlight'); row.append(node('td', r.rank)); const identity = node('td', r.harness); identity.append(node('span', r.model === '—' ? t('unknownModel') : r.model)); row.append(identity); for (const k of [...DIMENSIONS, 'overall']) row.append(node('td', r[k].toFixed(2))); body.append(row); }
  $('score-body').replaceChildren(body);
  $('cohort-meta').textContent = `${data.queries} ${t('queries')} · ${data.systems} ${t('systems')} · ${data.reports} ${t('reportsCount')} · ${data.within_query_pairs} ${t('pairs')} · ${data.cohort}`;
  const p = data.protocol; $('protocol').textContent = `${t('judge')}: ${p.judge} (${p.reasoning}); ${t('verification')}: ${p.verifier} (${p.verifier_reasoning}).`;
  $('weight-note').textContent = `${t('weights')}: ` + DIMENSIONS.map(k => `${t(k)} ${data.weights[k]}%`).join(' · ');
  $('sort-direction').textContent = t(descending ? 'descending' : 'ascending');
  $('sort-direction').setAttribute('aria-label', (lang === 'zh' ? '切换排序方向：' : 'Toggle sort direction: ') + t(descending ? 'descending' : 'ascending'));
  $('feed-status').textContent = `${t(status)} · ${t('date')}: ${data.snapshot_date} · ${t('revision')}: ${data.revision}`;
}
function render() {
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en'; document.title = t('title') + ' | LongCat';
  document.querySelectorAll('[data-t]').forEach(el => { el.textContent = t(el.dataset.t); });
  $('language').textContent = lang === 'zh' ? 'English' : '中文'; $('language').setAttribute('aria-label', lang === 'zh' ? 'Switch to English' : '切换到中文');
  links($('technical-links'), [['technicalCode','code',true],['technicalPaper','paper',true],['technicalProject','project',false]]);
  links($('benchmark-links'), [['benchmarkCode','code',true],['benchmarkPaper','paper',true],['benchmarkData','dataset',true],['benchmarkExplorer','explorer',false]]);
  $('submission-link').replaceChildren(publicLink(config.links.benchmarkSubmission, t('submit')) || node('span', t('submitPending')));
  renderAuthors(); renderTable(); switchTab(tab);
}
async function refresh() {
  if (busy) return;
  if (!config.feedUrl) { status = 'noSource'; renderTable(); return; }
  busy = true; $('refresh').disabled = true; status = 'checking'; renderTable();
  try { const remote = await fetchFeed(config.feedUrl, {allowedOrigins: config.allowedFeedOrigins, timeoutMs: config.timeoutMs}); data = chooseFeed(data, remote); hadRemote = true; status = 'live'; }
  catch { status = hadRemote ? 'retained' : 'fallback'; }
  finally { busy = false; $('refresh').disabled = false; renderTable(); }
}
function download(text, type, filename) { const url = URL.createObjectURL(new Blob([text], {type})); const a = node('a'); a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 30000); }
$('download-json').addEventListener('click', () => download(JSON.stringify(data, null, 2) + '\n', 'application/json', `comparedr-${data.revision}.json`));
$('download-csv').addEventListener('click', () => { const fields = ['rank','model','harness',...DIMENSIONS,'overall']; const cell = value => '"' + String(value).replace(/^[=+@-]/, "'$&").replaceAll('"', '""') + '"'; download([fields.join(','), ...data.rows.map(r => fields.map(k => cell(r[k])).join(','))].join('\r\n'), 'text/csv;charset=utf-8', `comparedr-${data.revision}.csv`); });
$('language').addEventListener('click', () => { lang = lang === 'zh' ? 'en' : 'zh'; render(); });
document.querySelectorAll('[data-tab]').forEach(el => { el.addEventListener('click', () => switchTab(el.dataset.tab)); el.addEventListener('keydown', e => { if (['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) { e.preventDefault(); switchTab(e.key === 'Home' ? 'technical' : e.key === 'End' ? 'benchmark' : tab === 'technical' ? 'benchmark' : 'technical', true); } }); });
document.querySelectorAll('[data-switch]').forEach(el => el.addEventListener('click', () => { switchTab(el.dataset.switch, true); document.querySelector('.tabs').scrollIntoView({block:'start'}); }));
window.addEventListener('hashchange', () => switchTab(location.hash === '#benchmark' || location.hash === '#leaderboard' ? 'benchmark' : 'technical'));
$('sort-key').addEventListener('change', e => { sortKey = e.target.value; renderTable(); });
$('sort-direction').addEventListener('click', () => { descending = !descending; renderTable(); });
$('refresh').addEventListener('click', refresh);
render(); refresh();
