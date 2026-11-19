// Lightweight unit fixtures, not a replacement for browser visual/keyboard QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'dist/data.json'),'utf8'));
let focused;
class Element{
 constructor(dataset={},label=''){this.dataset=dataset;this.innerHTML=label;this.attrs={};this.events={};this.value='';this.hidden=false;this.tabIndex=0;}
 setAttribute(k,v){this.attrs[k]=v;} getAttribute(k){return this.attrs[k];}
 addEventListener(k,v){this.events[k]=v;} closest(){return this.header??=new Element();}
 focus(){focused=this;} fire(type,key){this.events[type]?.({key,preventDefault(){}});}
}
const sorts=['D1','D2','D3','D4','D5_D6','overall'].map(k=>new Element({sort:k},k+' ↕'));
const tabs=['human','controlled','ablation','judge','efficiency'].map(k=>new Element({tab:k}));tabs[0].attrs['aria-selected']='true';
const elements=new Map();const element=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
element('#language-filter').value='all';
element('#query-card').dataset.repositoryTree='https://github.com/wolf0171/CompareDR/tree/main';
element('#query-card').dataset.repositoryBlob='https://github.com/wolf0171/CompareDR/blob/main';
const document={querySelector:element,querySelectorAll:s=>s==='[data-tab]'?tabs:s==='[data-sort]'?sorts:[]};
const context=vm.createContext({document,window:{BENCH_DATA:data}});
vm.runInContext(fs.readFileSync(path.join(__dirname,'dist/assets/leaderboard.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'dist/assets/app.js'),'utf8'),context);
for(const button of sorts){
 for(let i=0;i<2;i++){
  button.fire('click');const direction=button.closest().attrs['aria-sort'];
  assert.equal(button.innerHTML.endsWith(direction==='ascending'?'↑':'↓'),true);
  assert.equal(sorts.filter(b=>b.closest().attrs['aria-sort']!=='none').length,1);
  for(const inactive of sorts.filter(b=>b!==button))assert.equal(inactive.innerHTML.endsWith('↕'),true);
  const expected=[...data.leaderboard].sort((a,b)=>(direction==='ascending'?1:-1)*(a[button.dataset.sort]-b[button.dataset.sort])||a.rank-b.rank);
  const actual=[...element('#board').innerHTML.matchAll(/<tr><td>(\d+)<\/td>/g)].map(m=>Number(m[1]));
  assert.deepEqual(actual,expected.map(r=>r.rank));
 }
}
function selected(i){assert.equal(tabs.filter(t=>t.tabIndex===0).length,1);tabs.forEach((t,j)=>{assert.equal(t.attrs['aria-selected'],String(i===j));assert.equal(element('#panel-'+t.dataset.tab).hidden,i!==j);});}
selected(0);tabs[0].fire('keydown','ArrowLeft');selected(4);assert.equal(focused,tabs[4]);
tabs[4].fire('keydown','ArrowRight');selected(0);tabs[0].fire('keydown','End');selected(4);
tabs[4].fire('keydown','Home');selected(0);tabs[2].fire('click');selected(2);
element('#query-search').value='no-match-unit-fixture';element('#query-search').fire('input');
assert.equal(element('#prev-query').disabled,true);assert.equal(element('#next-query').disabled,true);
assert.equal(element('#query-position').textContent,'0 / 0');
assert.equal(element('#query-jump').disabled,true);
element('#query-search').value='高流失率';element('#query-search').fire('input');
assert.match(element('#query-card').innerHTML,/prometheus 的高流失率会造成什么影响/);
assert.match(element('#query-card').innerHTML,/报告是否正确说明高流失率/);
assert.match(element('#query-card').innerHTML,/哪篇更清楚且合理地从序列变化解释/);
assert.match(element('#query-card').innerHTML,/Scoring anchors &amp; scope/);
assert.match(element('#query-card').innerHTML,/data\/reports\/main9\/drb1_19/);
assert.equal(element('#query-jump').disabled,false);
element('#query-search').value='';element('#query-search').fire('input');
assert.equal(element('#query-count').textContent,'40 / 40 tasks');
assert.deepEqual([...element('#query-jump').innerHTML.matchAll(/>(\d+) · /g)].map(m=>Number(m[1])),Array.from({length:40},(_,i)=>i+1));
assert.match(element('#query-jump').innerHTML,/>29 · Memory engrams/);
assert.match(element('#query-card').innerHTML,/<span>Task 1<\/span>/);
assert.doesNotMatch(element('#query-card').innerHTML.replace(/<[^>]*>/g,''),/DRB-I|drb1_19/);
element('#query-jump').value=data.queries[39].id;element('#query-jump').fire('change');
assert.equal(element('#query-position').textContent,'40 / 40');
assert.equal(element('#next-query').disabled,true);
assert.match(element('#query-card').innerHTML,/<span>Task 40<\/span>/);
element('#language-filter').value='en';element('#language-filter').fire('change');
assert.equal(element('#query-count').textContent,'20 / 40 tasks');
assert.match(element('#query-card').innerHTML,/<span>Task 6<\/span>/);
assert.match(element('#query-jump').innerHTML,/>29 · Memory engrams/);
for(const search of ['29','#29','Task 29']){
 element('#query-search').value=search;element('#query-search').fire('input');
 assert.equal(element('#query-count').textContent,'1 / 40 tasks');
 assert.match(element('#query-card').innerHTML,/<span>Task 29<\/span>/);
 assert.doesNotMatch(element('#query-card').innerHTML.replace(/<[^>]*>/g,''),/ResearchRubrics|rr_683a58/);
 assert.match(element('#query-card').innerHTML,/data\/reports\/main9\/rr_683a58c9a7e7fe4e76958488/);
}
element('#query-search').value='40';element('#query-search').fire('input');
assert.match(element('#query-card').innerHTML,/<span>Task 40<\/span>/);
element('#language-filter').value='zh';element('#language-filter').fire('change');
assert.equal(element('#query-count').textContent,'0 / 40 tasks');
const malicious={id:'x',title:'<img src=x onerror=alert(1)>',question:'<script>alert(1)</script>',anchors:{1:'<svg onload=x>'},boundary:'<iframe>'};
context.malicious=malicious;
const rendered=vm.runInContext("criterionCard(malicious,1,'POINTWISE','en')",context);
assert.equal(rendered.includes('<script>'),false);assert.equal(rendered.includes('<img'),false);
assert.equal(rendered.includes('&lt;script&gt;'),true);
console.log('PASS: sort order/arrows, tab focus/selection/wrapping, and empty filtering.');
console.log('PASS: Chinese full text, PT/PW examples, anchors, resource links, stable task numbers 1–40, number search, language filtering and escaped text.');

// The standalone page has no experiment tabs or explorer controls.
const standaloneBoard=new Element();
const standaloneDocument={querySelector:s=>s==='#board'?standaloneBoard:null,querySelectorAll:()=>[]};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'dist/assets/leaderboard.js'),'utf8'),{document:standaloneDocument,window:{BENCH_DATA:data}});
assert.equal((standaloneBoard.innerHTML.match(/<tr>/g)||[]).length,9);
console.log('PASS: standalone board initializes without homepage-only elements.');

// Clipboard access can be denied or absent when opening an offline file.
(async()=>{
 const copyButton=new Element(),copyStatus=new Element();
 const citation='@unpublished{wu2026comparedr}';let copied;
 const copyDocument={querySelector:s=>({'#copy-citation':copyButton,'#copy-status':copyStatus,'#citation-text':{textContent:citation}}[s]??null)};
 const navigator={clipboard:{writeText:async text=>{copied=text;}}};
 const projectScript=fs.readFileSync(path.join(__dirname,'dist/assets/project.js'),'utf8');
 vm.runInNewContext(projectScript,{document:copyDocument,navigator});
 await copyButton.events.click();assert.equal(copied,citation);assert.equal(copyStatus.textContent,'BibTeX copied.');
 navigator.clipboard.writeText=async()=>{throw new Error('denied');};
 await copyButton.events.click();assert.match(copyStatus.textContent,/download the .bib file/);
 navigator.clipboard=undefined;await copyButton.events.click();assert.match(copyStatus.textContent,/Select the BibTeX/);
 vm.runInNewContext(projectScript,{document:standaloneDocument});
 console.log('PASS: citation copying, denied or unavailable clipboard fallback, and absent citation control.');
})().catch(error=>{console.error(error);process.exitCode=1;});
