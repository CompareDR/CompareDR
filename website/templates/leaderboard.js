"use strict";
// Shared by the project homepage and standalone leaderboard. Static rows remain
// readable without JavaScript; this script adds full-precision column sorting.
(() => {
 const data=window.BENCH_DATA;
 const target=document.querySelector('#board');
 if(!data||!target)return;
 const keys=['D1','D2','D3','D4','D5_D6','overall'];
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const maximum=Object.fromEntries(keys.map(k=>[k,Math.max(...data.leaderboard.map(r=>r[k]))]));
 let sortKey='overall',descending=true;
 function render(){
  const rows=[...data.leaderboard].sort((a,b)=>(descending?-1:1)*(a[sortKey]-b[sortKey])||a.rank-b.rank);
  target.innerHTML=rows.map(r=>`<tr><td>${r.rank}</td><td><span class="model">${esc(r.model)}</span><span class="harness">${esc(r.harness)}</span></td>${keys.map(k=>`<td class="${k==='overall'?'total ':''}${r[k]===maximum[k]?'best':''}">${Number(r[k]).toFixed(2)}</td>`).join('')}</tr>`).join('');
  document.querySelectorAll('[data-sort]').forEach(b=>{
   const active=b.dataset.sort===sortKey;
   b.closest('th').setAttribute('aria-sort',active?(descending?'descending':'ascending'):'none');
   b.innerHTML=b.innerHTML.replace(/[↕↓↑]\s*$/,active?(descending?'↓':'↑'):'↕');
  });
 }
 document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{
  descending=b.dataset.sort===sortKey?!descending:true;sortKey=b.dataset.sort;render();
 }));
 render();
})();
