// Builds overlay DOM from window.PLAN (classic script, runs before the module)
(function(){
  const P=window.PLAN;const host=document.getElementById('scenes');
  const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
  const cnt=t=>esc(t).replace(/\{(\d+)\|([^}]*)\}/g,(m,v,suf)=>`<span data-count="${v}" data-suf="${suf}">0</span>`);
  P.scenes.forEach((s,i)=>{
    const d=document.createElement('div');d.className='scene';
    d.dataset.shots=s.shots.map((_,j)=>`k_${i}_${j}`).join('|');
    d.dataset.beats=(s.beats||s.shots.map((_,j)=>j/s.shots.length)).join('|');
    let h='';
    (s.overlay||[]).forEach(o=>{
      const f=o.f||0,c=o.color||'';
      if(o.kind==='title'){d.classList.add('title');h+=`<div class="tag">${esc(o.tag||'3D GYAAN')}</div><div class="big"><span class="a">${esc(o.a)}</span><span class="vs">${esc(o.vs||'VS')}</span><span class="c">${esc(o.c)}</span></div>`;}
      else if(o.kind==='headline'){d.classList.add('title');h+=`<div class="tag">${esc(o.tag||'3D GYAAN')}</div><div class="big" style="font-size:${o.size||84}px"><span class="a">${esc(o.text)}</span></div>`;}
      else if(o.kind==='outro'){d.classList.add('outro');h+=`<div class="big">${esc(o.big)}</div><div class="q">${esc(o.q)}</div><div class="cta">${esc(o.cta)}</div><div class="src">${esc(o.src||'')}</div>`;}
      else if(o.kind==='bigcount')h+=`<div class="hookc" data-hide="${o.hide||0.6}"><div class="num" data-count="${o.value}" data-suf="${esc(o.suffix||'')}" data-dur="${o.dur||0.5}">0</div><div class="lbl">${esc(o.label||'')}</div></div>`;
      else if(o.kind==='bigtext')h+=`<div class="hookq" data-show="${o.show||0.6}">${esc(o.text)}</div>`;
      else if(o.kind==='kin')h+=`<div class="kin" data-f="${f}">${cnt(o.text)}</div>`;
      else if(o.kind==='stk')h+=`<div class="stk ${c}" data-f="${f}">${cnt(o.text)}</div>`;
      else if(o.kind==='stamp')h+=`<div class="stamp ${c||'red'}" data-f="${f}" style="${o.center?'left:50%;top:300px;transform-origin:center;margin-left:-'+(o.w||160)+'px':'right:80px;top:'+(o.top||440)+'px'}">${esc(o.text)}</div>`;
      else if(o.kind==='versus')h+=`<div class="plus" data-f="${f}"><span class="a">${esc(o.a)}</span><span class="p"><span class="strike">VS</span> +</span><span class="c">${esc(o.c)}</span></div>`;
      else if(o.kind==='foot')h+=`<div class="foot">${esc(o.text)}</div>`;
    });
    d.innerHTML=h;host.appendChild(d);
  });
})();
