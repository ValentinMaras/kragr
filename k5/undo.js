// kragr · Rückgängig (13.11.2026): ein Knopf links neben dem Menü-Knopf, in Schnittkräfte und Bemessung.
// Die Seite meldet sich an mit  kragrUndo({ get:()=>Stand, set:Stand=>…, nav:['tab'], navFns:['showTab'] }).
//  · get liefert den kompletten Eingabestand (dieselben Daten wie der Entwurf bzw. das Rechenblatt), set stellt ihn wieder her.
//  · nav: Schlüssel, die nur die Ansicht wählen (Reiter, Nachweis). Ein Wechsel dort ist kein eigener Schritt; beim Zurücknehmen
//    springt die Seite aber dorthin, wo die Änderung gemacht wurde.
// Ein Schritt ist eine abgeschlossene Änderung (Feld verlassen, Knopf, Auswahl, Last hinzu/weg), nicht jeder Tastendruck.
// Bis zu 50 Schritte; nach dem Neuladen beginnt der Verlauf neu. Nach dem Zurücknehmen kurz ein Hinweis unter der Kopfzeile mit
// „Wiederholen“; zurückgenommene Felder werden kurz hinterlegt (zugeklappte Karte geht dafür auf).
// Tastatur: Strg/Cmd+Z, Strg/Cmd+Umschalt+Z (außerhalb von Eingabefeldern — dort bleibt das Rückgängig des Browsers).
(function(){
  if(typeof document==='undefined') return;
  const D=document, MAX=50;
  const TX={
    de:{undo:'Rückgängig', none:'Nichts rückgängig zu machen', done:'Rückgängig gemacht', redo:'Wiederholen'},
    en:{undo:'Undo', none:'Nothing to undo', done:'Undone', redo:'Redo'},
    fr:{undo:'Annuler', none:'Rien à annuler', done:'Annulé', redo:'Rétablir'},
    es:{undo:'Deshacer', none:'Nada que deshacer', done:'Deshecho', redo:'Rehacer'}};
  const T=k=>(TX[(D.documentElement.lang||'de').slice(0,2)]||TX.de)[k];
  let U=null, btn=null, toast=null, toastT=0, inT=0;

  const strip=o=>{ if(!U.nav.length || !o || typeof o!=='object') return o; const c=Object.assign({}, o); U.nav.forEach(k=>delete c[k]); return c; };
  const navOf=full=>{ if(!U.nav.length) return ''; try{ const o=JSON.parse(full); return JSON.stringify(U.nav.map(k=>o[k])); }catch(e){ return ''; } };
  const read=()=>{ try{ const o=U.get(); return {full:JSON.stringify(o), key:JSON.stringify(strip(o))}; }catch(e){ return null; } };

  // Stand vergleichen: geänderte Eingaben → der vorige Stand kommt auf den Stapel; nur Ansicht gewechselt → still nachführen
  function check(){
    if(!U || U.busy) return; const s=read(); if(!s) return;
    // vor der ersten Bedienung (Seite baut noch Felder auf) und beim Wechsel von Reiter/Nachweis (setzt dort Vorgaben): kein Schritt
    if(!U.cur || !U.armed || (s.full!==U.cur.full && navOf(s.full)!==navOf(U.cur.full))){ U.cur=s; return; }
    if(s.key!==U.cur.key){ U.stack.push(U.cur.full); if(U.stack.length>MAX) U.stack.shift(); U.redo.length=0; U.cur=s; label(); hideToast(); }
    else if(s.full!==U.cur.full) U.cur=s;
  }
  const later=ms=>setTimeout(check, ms||0);

  // Werte aller Felder, um nach dem Zurücknehmen zu zeigen, was sich geändert hat
  const fields=()=>{ const m=new Map(); D.querySelectorAll('main input[id], main select[id], main textarea[id], .main input[id], .main select[id]').forEach(e=>m.set(e, e.type==='checkbox'||e.type==='radio' ? e.checked : e.value)); return m; };
  function show(before){
    const ch=[]; fields().forEach((v,e)=>{ if(before.has(e) && before.get(e)!==v) ch.push(e); });
    let opened=false;
    const vis=ch.filter(e=>{ let p=e; while(p && p!==D.body){ if(p.classList && p.classList.contains('closed') && p.classList.contains('fold')){ p.classList.remove('closed'); opened=true; } p=p.parentElement; } return e.offsetParent!==null; });
    if(opened){ try{ D.dispatchEvent(new CustomEvent('k5refold')); }catch(e){} }   // Kurzfassung im Kartenkopf nachführen
    vis.forEach(e=>{ const f=e.closest('.field, .k-field, label, .row, .grid2 > div') || e; clearTimeout(f._k5u); f.classList.add('k5-undo-fx','k5-undone');   // kurz hinterlegt, dann ausblenden
      f._k5u=setTimeout(()=>{ f.classList.remove('k5-undone'); f._k5u=setTimeout(()=>f.classList.remove('k5-undo-fx'), 800); }, 1100); });
    const first=vis[0]; if(first){ const r=first.getBoundingClientRect(), top=(parseFloat(getComputedStyle(D.documentElement).getPropertyValue('--k-hdr-h'))||64)+8;
      if(r.top<top || r.bottom>innerHeight-90) first.scrollIntoView({block:'center', behavior:'smooth'}); }
  }
  function go(fromStack, toStack){
    if(!U || !fromStack.length) return false;
    const a=D.activeElement; if(a && a!==D.body && a.blur && a.closest && a.closest('main, .main')) a.blur();
    check();                                   // eben Getipptes zählt als eigener Schritt
    if(!fromStack.length) return false;
    const prev=fromStack.pop(); toStack.push(U.cur.full);
    const before=fields(); U.busy=true;
    const old=D.getElementById('k-undo'); if(old) old.classList.remove('on');   // Hinweis „Last gelöscht · Rückgängig“ (calc) gilt nicht mehr
    try{ U.set(JSON.parse(prev)); }catch(e){ try{ console.error(e); }catch(_){} }
    setTimeout(()=>{ U.busy=false; const s=read(); if(s) U.cur=s; label(); try{ show(before); }catch(e){} }, 60);
    return true;
  }
  const undo=()=>{ if(go(U.stack, U.redo)) showToast(); };
  const redo=()=>{ if(go(U.redo, U.stack)) { if(U.redo.length) showToast(); else hideToast(); } };

  function label(){ if(!btn) return; const n=U ? U.stack.length : 0; btn.disabled=!n; btn.setAttribute('aria-disabled', String(!n));
    const t=n ? T('undo') : T('none'); btn.title=t; btn.setAttribute('aria-label', T('undo')); }
  function showToast(){
    if(!toast){ toast=D.createElement('div'); toast.className='k5-undo-toast'; toast.setAttribute('role','status');
      toast.innerHTML='<span></span><button type="button"></button>'; toast.querySelector('button').addEventListener('click', e=>{ e.stopPropagation(); redo(); }); D.body.appendChild(toast); }
    toast.querySelector('span').textContent=T('done'); toast.querySelector('button').textContent=T('redo');
    toast.querySelector('button').style.display=U.redo.length ? '' : 'none';
    toast.classList.add('on'); clearTimeout(toastT); toastT=setTimeout(hideToast, 4500);
  }
  function hideToast(){ if(toast) toast.classList.remove('on'); clearTimeout(toastT); }

  function place(){
    if(!U || btn) return true; const bg=D.getElementById('k5-burger'); if(!bg) return false;
    btn=D.createElement('button'); btn.type='button'; btn.id='k5-undo'; btn.className='k5-undo';
    btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg>';
    btn.addEventListener('click', e=>{ e.stopPropagation(); undo(); });
    bg.parentNode.insertBefore(btn, bg); label(); return true;
  }

  window.kragrUndo=function(o){
    if(U || !o || typeof o.get!=='function' || typeof o.set!=='function') return;
    U={get:o.get, set:o.set, nav:o.nav||[], stack:[], redo:[], cur:null, busy:false, armed:false};
    U.cur=read();
    // Ansichtswechsel per Funktion (Reiter, Nachweis): danach Stand still nachführen, damit die nächste Änderung dem neuen Reiter gehört
    (o.navFns||[]).forEach(n=>{ const f=window[n]; if(typeof f!=='function' || f._k5u) return; const w=function(){ const r=f.apply(this, arguments); later(0); return r; }; w._k5u=1; window[n]=w; });
    const arm=e=>{ if(e.isTrusted===false) return; if(!U.armed){ check(); U.armed=true; } };   // Ausgangsstand = Stand bei der ersten Bedienung
    ['pointerdown','touchstart','keydown','focusin'].forEach(t=>D.addEventListener(t, arm, true));
    if(!place()){ const mo=new MutationObserver(()=>{ if(place()) mo.disconnect(); }); mo.observe(D.documentElement,{childList:true, subtree:true}); }
    const own=e=>e.target.closest && e.target.closest('#k5-undo, .k5-undo-toast, #k5-menu, #k5-burger, .k5-scrim');
    D.addEventListener('change', e=>{ if(!own(e)) later(0); }, true);
    D.addEventListener('click', e=>{ if(!own(e)) { later(0); later(250); } }, true);
    D.addEventListener('input', e=>{ if(own(e)) return; clearTimeout(inT); inT=setTimeout(check, 1200); }, true);
    D.addEventListener('keydown', e=>{
      if(!(e.ctrlKey||e.metaKey) || e.altKey) return; const k=(e.key||'').toLowerCase(); if(k!=='z' && k!=='y') return;
      const t=e.target; if(t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;   // Feld: Rückgängig des Browsers
      e.preventDefault(); if(k==='y' || e.shiftKey) redo(); else undo(); });
    new MutationObserver(label).observe(D.documentElement,{attributes:true, attributeFilter:['lang']});
  };
  window.kragrUndoCheck=()=>check();
  window.kragrUndoInfo=()=>U ? {back:U.stack.length, fwd:U.redo.length, armed:U.armed} : null;   // für Tests   // für Änderungen ohne Klick oder Eingabe (z. B. Rechenblatt geladen)

  const st=D.createElement('style');
  st.textContent=
    '.k5-undo{flex:none;display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;margin-left:auto;padding:0;border:none;border-radius:14px;background:var(--k5-card,#fff);box-shadow:var(--k5-sh,0 1px 3px rgba(17,17,20,.12));color:#111114;cursor:pointer;transition:transform .25s var(--k5-spring,ease),box-shadow .25s,opacity .2s;-webkit-tap-highlight-color:transparent}'
    +'.k5-undo svg{width:21px;height:21px}.k5-undo:hover:not(:disabled){box-shadow:var(--k5-sh-h,0 4px 12px rgba(17,17,20,.14))}.k5-undo:active:not(:disabled){transform:scale(.92)}'
    +'.k5-undo:disabled{cursor:default;color:#b4b6bd;box-shadow:none;background:transparent}'
    +'.k5-undo + .k5-burger{margin-left:8px!important}'
    +'@media (orientation:landscape) and (max-height:540px) and (min-width:640px) and (max-width:999px){.k-hdr .k5-undo{height:38px;width:38px}}'
    +'.k5-undo-fx{border-radius:10px;transition:background-color .7s,box-shadow .7s}.k5-undone{background-color:rgba(245,158,11,.2)!important;box-shadow:0 0 0 5px rgba(245,158,11,.2)!important}'
    +'.k5-undo-toast{position:fixed;left:50%;top:calc(var(--k-hdr-h,60px) + 8px);transform:translate(-50%,-12px);z-index:46;display:flex;align-items:center;gap:14px;padding:10px 16px;border-radius:12px;background:#111114;color:#fff;font:600 14px Figtree,system-ui,sans-serif;opacity:0;pointer-events:none;transition:opacity .2s,transform .25s;white-space:nowrap}'
    +'.k5-undo-toast.on{opacity:1;transform:translate(-50%,0);pointer-events:auto}.k5-undo-toast button{border:0;border-radius:8px;padding:6px 10px;margin:-4px -6px -4px 0;background:#fff;color:#111114;font:inherit;font-size:13px;font-weight:700;cursor:pointer}'
    +'@media print{.k5-undo,.k5-undo-toast{display:none!important}}';
  (D.head||D.body).appendChild(st);
})();
