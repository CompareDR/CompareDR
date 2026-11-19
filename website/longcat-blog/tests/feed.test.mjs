import test from 'node:test';
import assert from 'node:assert/strict';
import {content} from '../src/content.mjs';
test('both languages report the common-set calibrated macro-F1, not accuracy', () => {
  for (const lang of ['zh','en']) {
    const text = content[lang].validationBody;
    for (const part of ['119', 'macro-F1', '64.2%', '37.8%']) assert.ok(text.includes(part));
    assert.ok(!text.includes('64.7%'));
  }
});
import fs from 'node:fs';
import {validateFeed,fetchFeed,chooseFeed,safeFeedURL,DIMENSIONS} from '../src/feed.mjs';
const original = JSON.parse(fs.readFileSync(new URL('../../dist/leaderboard.json',import.meta.url)));
const base = () => ({...structuredClone(original),schema_version:1,revision:'paper-2026-11-16-main9-v1'});
const source = 'https://raw.githubusercontent.com/CompareDR/CompareDR/main/website/longcat-blog/feed/v1/leaderboard.json';
const origins = ['https://raw.githubusercontent.com'];
const opts = fetchImpl => ({allowedOrigins:origins,fetchImpl,timeoutMs:40});
test('exact nine-system scores and complete cohort survive validation',()=> { const d=validateFeed(base());assert.equal(d.rows.length,9);assert.equal(d.reports,360);assert.equal(d.within_query_pairs,1440);for(let i=0;i<9;i++) for(const k of [...DIMENSIONS,'overall']) assert.equal(d.rows[i][k],original.rows[i][k]); });
test('accept complete expanded cohort, not hard-coded nine',()=>{const d=base(); const r={...d.rows[8],model:'Fixture model',harness:'Fixture harness'};d.rows.push(r);d.systems=10;d.reports=400;d.within_query_pairs=1800;assert.equal(validateFeed(d).rows.length,10);});
for(const [name,change] of Object.entries({schema:d=>d.schema_version=2,weight:d=>d.weights.D1=31,count:d=>d.reports=359,pairs:d=>d.within_query_pairs=1,NaN:d=>d.rows[0].D1=NaN,range:d=>d.rows[0].D1=101,overall:d=>d.rows[0].overall+=1,duplicate:d=>d.rows[1]={...d.rows[0]},html:d=>d.rows[0].harness='<img src=x>',protocol:d=>delete d.protocol.verifier,date:d=>d.snapshot_date='2026-02-30'})) test('reject '+name,()=>{const d=base();change(d);assert.throws(()=>validateFeed(d));});
test('derive ranks and ties from overall instead of input ranks',()=>{const d=base();d.rows[0].rank=99;assert.equal(validateFeed(d).rows[0].rank,1);const b={...d.rows[0],model:'Tie model',harness:'Tie harness'};d.rows[1]=b;assert.deepEqual(validateFeed(d).rows.slice(0,2).map(r=>r.rank),[1,1]);});
test('accept public origin only, no query token, credentials, or non-HTTPS',()=>{assert.equal(safeFeedURL(source,origins),source);for(const url of ['http://raw.githubusercontent.com/x.json','https://evil.example/x.json',source+'?token=secret','https://user:pass@raw.githubusercontent.com/x.json']) assert.throws(()=>safeFeedURL(url,origins));});
test('fetch valid JSON without auth; requests bypass cache and reject redirects',async()=>{let seen; const d=await fetchFeed(source,opts(async(url,options)=>{seen=options;return new Response(JSON.stringify(base()),{headers:{'content-type':'application/json'}})}));assert.equal(d.systems,9);assert.equal(seen.credentials,'omit');assert.equal(seen.cache,'no-store');assert.equal(seen.redirect,'error');});
for(const [name,response] of [['HTTP404',()=>new Response('',{status:404})],['malformed',()=>new Response('{bad',{headers:{'content-type':'application/json'}})],['HTML',()=>new Response('<html>login</html>',{headers:{'content-type':'text/html'}})],['invalid-schema',()=>new Response('{"schema_version":99}',{headers:{'content-type':'application/json'}})],['oversized',()=>new Response('x',{headers:{'content-type':'application/json','content-length':'1000001'}})]]) test('failed update leaves snapshot untouched: '+name,async()=>{const current=validateFeed(base());await assert.rejects(fetchFeed(source,opts(async()=>response())));assert.equal(current.rows[0].overall,original.rows[0].overall);});
test('network/CORS rejection is catchable',async()=>{await assert.rejects(fetchFeed(source,opts(async()=>{throw new TypeError('Failed to fetch')})));});
test('timeout bounds stalled fetch',async()=>{await assert.rejects(fetchFeed(source,opts(()=>new Promise(()=>{}))),/timeout/);});
test('old date and reused version cannot silently replace data',()=>{const current=validateFeed(base());let next=base();next.snapshot_date='2026-11-15';assert.throws(()=>chooseFeed(current,next));next=base();next.protocol.judge='Another judge';assert.throws(()=>chooseFeed(current,next));next.revision='new-version';assert.equal(chooseFeed(current,next).protocol.judge,'Another judge');});
test('both language dictionaries have identical keys',async()=>{const {content}=await import('../src/content.mjs');assert.deepEqual(Object.keys(content.zh).sort(),Object.keys(content.en).sort());});
test('every HTML translation key exists',async()=>{const {content}=await import('../src/content.mjs');const html=fs.readFileSync(new URL('../src/index.html',import.meta.url),'utf8');for(const match of html.matchAll(/data-t="([^"]+)"/g)) assert.ok(content.zh[match[1]],match[1]);});
test('page does not inject remote HTML or silently make authenticated calls',()=>{const js=fs.readFileSync(new URL('../src/app.mjs',import.meta.url),'utf8');assert.ok(!js.includes('innerHTML'));assert.ok(!js.includes('localStorage'));assert.ok(!js.includes('Authorization'));});
