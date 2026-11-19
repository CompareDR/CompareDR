"use strict";
const D=window.BENCH_DATA;
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const f=n=>n==null?'—':Number(n).toFixed(2);
const q=s=>document.querySelector(s);
q('#inventory-table').innerHTML=D.benchmark_resources.map(r=>`<tr><td>${esc(r.component)}</td>${['drb1','drb2','researchrubrics','total'].map(k=>`<td>${r[k]}</td>`).join('')}</tr>`).join('');
q('#rubric-inventory-table').innerHTML=D.rubric_distribution.map(r=>`<tr><td>${esc(r.dimension)}</td><td>${esc(r.focus)}</td>${['pointwise','pairwise','total'].map(k=>`<td>${r[k].toLocaleString('en-US')}</td>`).join('')}</tr>`).join('');
q('#human-bars').innerHTML=D.human_alignment.map(r=>`<div class="metric-bar"><div class="bar-label"><span>${esc(r.method)}</span><b>${f(r.agreement)}%</b></div><div class="track"><div class="fill" style="width:${r.agreement}%"></div></div></div>`).join('')+'<div class="bar-axis"><span>0%</span><span>100%</span></div>';
q('#human-table').innerHTML=D.human_alignment.map(r=>`<tr><td>${esc(r.method)}</td><td>${f(r.agreement)}%</td><td>${r.kappa.toFixed(3)}</td><td>${r.macro_f1.toFixed(3)}</td><td>${r.ci.map(f).join('–')}%</td></tr>`).join('');
q('#ablation-table').innerHTML=D.ablations.map(r=>`<tr><td>${esc(r.method)}</td><td>${f(r.agreement)}%</td><td>${r.kappa.toFixed(3)}</td><td>${r.macro_f1.toFixed(3)}</td><td>${f(r.delta)}</td></tr>`).join('');
q('#judge-table').innerHTML=D.cross_judge.map(r=>`<tr><td>${esc(r.judge)}</td><td>${f(r.order_agreement)}%</td><td>${f(r.reversals)}%</td><td>${r.rho==null?'—':r.rho.toFixed(3)}</td><td>${r.icc==null?'—':r.icc.toFixed(3)}</td></tr>`).join('');
const rate=r=>`${r.correct}/${r.total} (${r.percent.toFixed(1)}%)`;
q('#controlled-table').innerHTML=D.controlled_revisions.rows.map(r=>`<tr><td>${esc(r.method)}</td><td>${r.threshold}</td>${['improvement','degradation','equivalent'].map(k=>`<td>${rate(r[k])}</td>`).join('')}<td>${r.accuracy.toFixed(1)}%</td><td>${r.macro_f1.toFixed(1)}%</td></tr>`).join('');
q('#dimension-table').innerHTML=D.controlled_dimensions.map(r=>`<tr><td>${esc(r.dimension)}</td><td>${r.n}</td><td>${rate(r.hybrid)}</td><td>${rate(r.pointwise)}</td></tr>`).join('');
q('#threshold-table').innerHTML=D.controlled_thresholds.map(r=>`<tr><td>${esc(r.method)}</td>${['absolute_acc','absolute_f1','percentage_acc','percentage_f1'].map(k=>`<td>${r[k].value.toFixed(1)} (${r[k].threshold})</td>`).join('')}</tr>`).join('');
q('#robustness-table').innerHTML=D.cross_judge.map(r=>`<tr><td>${esc(r.judge)}</td>${['tau','mean_query_rho','bias'].map(k=>`<td>${r[k]==null?'—':r[k].toFixed(3)}</td>`).join('')}<td>${f(r.cycles)}%</td></tr>`).join('');
q('#pilot-table').innerHTML=D.judge_pilot.map(r=>`<tr><td>${esc(r.metric)}</td>${r.values.map(v=>`<td>${typeof v==='number'?v.toFixed(2)+'%':esc(v)}</td>`).join('')}</tr>`).join('');
q('#entry-table').innerHTML=D.new_system_entry.map(r=>`<tr><td>${esc(r.opponents)}</td><td>${r.new_pairs}</td><td>${f(r.token_savings)}%</td><td>${r.mae.toFixed(3)}</td><td>${r.p95.toFixed(3)}</td><td>${f(r.rank_accuracy)}%</td></tr>`).join('');
q('#usage-table').innerHTML=D.token_usage.map(r=>`<tr><td>${esc(r.model)}</td><td>${r.responses.toLocaleString('en-US')}</td>${['input_m','output_m','total_m'].map(k=>`<td>${f(r[k])}</td>`).join('')}</tr>`).join('');
q('#human-dimensions').textContent='Dimension-level agreement: '+Object.entries(D.human_dimension_agreement).map(([k,v])=>`${k} ${f(v)}%`).join('; ')+'.';
const tabs=[...document.querySelectorAll('[data-tab]')];
function selectTab(b,focus=false){
 tabs.forEach(t=>{const on=t===b;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;q('#panel-'+t.dataset.tab).hidden=!on;});
 if(focus)b.focus();
}
tabs.forEach((b,i)=>{
 b.addEventListener('click',()=>selectTab(b));
 b.addEventListener('keydown',e=>{
  const index={ArrowRight:(i+1)%tabs.length,ArrowLeft:(i+tabs.length-1)%tabs.length,Home:0,End:tabs.length-1}[e.key];
  if(index!==undefined){e.preventDefault();selectTab(tabs[index],true);}
 });
});
selectTab(tabs.find(b=>b.getAttribute('aria-selected')==='true')||tabs[0]);
let queryIndex=0,filtered=[];
// Display numbers are stable across filters; source identities remain in the data and links.
const queryNumbers=new Map(D.queries.map((r,index)=>[r.id,index+1]));
const dimensionNames={D1:'Responsiveness',D2:'Evidence',D3:'Reasoning',D4:'Synthesis',D5_D6:'Readability',D5:'Organization',D6:'Expression'};
function criterionCard(example,count,kind,language){
 if(!example)return `<article><span class="tag">${kind}</span><p>No example is included for this task.</p></article>`;
 const anchors=Object.entries(example.anchors||{}).sort(([a],[b])=>Number(a)-Number(b)).map(([level,text])=>`<dt>${esc(level)}</dt><dd>${esc(text)}</dd>`).join('');
 return `<article><span class="tag">${kind} · ${count} criteria</span><h4 lang="${language}">${esc(example.title)}</h4><p class="muted">${esc(example.id)} · ${esc(dimensionNames[example.dimension]||example.dimension)}</p><p class="criterion-question" lang="${language}">${esc(example.question)}</p><details><summary>Scoring anchors &amp; scope</summary><dl class="anchor-list" lang="${language}">${anchors}</dl><p class="criterion-boundary" lang="${language}"><strong>Scope:</strong> ${esc(example.boundary||'No separate boundary field is included.')}</p></details></article>`;
}
function queryCard(){
 q('#query-count').textContent=`${filtered.length} / 40 tasks`;
 q('#query-position').textContent=filtered.length?`${queryIndex+1} / ${filtered.length}`:'0 / 0';
 q('#prev-query').disabled=queryIndex===0;q('#next-query').disabled=queryIndex>=filtered.length-1;
 q('#query-jump').disabled=!filtered.length;
 if(!filtered.length){q('#query-card').innerHTML='<p>No matching tasks. Try a different title or filter.</p>';return;}
 const r=filtered[queryIndex];
 const language=r.language==='zh'?'zh':'en';
 const card=q('#query-card'),tree=card.dataset.repositoryTree,blob=card.dataset.repositoryBlob,id=encodeURIComponent(r.id);
 q('#query-jump').value=r.id;
 const links=tree&&blob?`<div class="query-resource-links"><a href="${esc(tree)}/data/reports/main9/${id}" target="_blank" rel="noopener">Nine-system reports ↗</a><a href="${esc(tree)}/data/reports/studies7/${id}" target="_blank" rel="noopener">Seven-system study reports ↗</a><a href="${esc(blob)}/data/evaluation/main9/rubrics/${id}.json" target="_blank" rel="noopener">Full task criteria ↗</a></div><p class="access-note">Source-specific licenses and attribution apply to repository resources.</p>`:'';
 card.innerHTML=`<div class="query-badges"><span>Task ${queryNumbers.get(r.id)}</span><span>${language==='zh'?'Chinese':'English'}</span></div><h3>${esc(r.title)}</h3>${language==='zh'&&r.original_title?`<p class="query-title-original" lang="zh">${esc(r.original_title)}</p>`:''}<div class="query-text" lang="${language}">${esc(r.query)}</div><div class="example-grid">${criterionCard(r.pt_example,r.pt_count,'POINTWISE',language)}${criterionCard(r.pw_example,r.pw_count,'PAIRWISE',language)}</div>${links}`;
}
function filter(){
 const lang=q('#language-filter').value,s=q('#query-search').value.trim().toLowerCase();
 const number=s.match(/^(?:task\s*|#)?([1-9]\d?)$/);
 filtered=D.queries.filter(r=>(lang==='all'||r.language===lang)&&(!s||(number?queryNumbers.get(r.id)===Number(number[1]):[r.id,r.title,r.original_title,r.query].join(' ').toLowerCase().includes(s))));
 queryIndex=0;
 q('#query-jump').innerHTML=filtered.length?filtered.map(r=>`<option value="${esc(r.id)}">${queryNumbers.get(r.id)} · ${esc(r.language==='zh'?r.original_title||r.title:r.title)}</option>`).join(''):'<option value="">No matching tasks</option>';
 queryCard();
}
q('#language-filter').addEventListener('change',filter);q('#query-search').addEventListener('input',filter);
q('#query-jump').addEventListener('change',()=>{const index=filtered.findIndex(r=>r.id===q('#query-jump').value);if(index>=0){queryIndex=index;queryCard();}});
q('#prev-query').addEventListener('click',()=>{queryIndex=Math.max(0,queryIndex-1);queryCard();});q('#next-query').addEventListener('click',()=>{queryIndex=Math.min(filtered.length-1,queryIndex+1);queryCard();});
filter();
