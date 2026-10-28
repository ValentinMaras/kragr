// Rechenblatt speichern (calc v0.11.11 · size v0.7.9; seit calc v0.11.12 · size v0.7.10 ganz unten rechts): ersetzt „Projekte“. Knopf „Als Rechenblatt speichern“,
// darunter ein kleines Feld für den Namen. Gleicher Name: erst „Überschreiben?“, dann ersetzen. Alle Rechenblätter zeigt projekt.html.
// calc: Eintrag statiq_sdf_<Zeit> = {name, sdf, draft} — draft sind die Eingaben (k4Snap), damit „Öffnen“ alles wiederherstellt.
// size: wie bisher savePos() → statiq-size-positionen + Bericht statiq-size-bericht:<Name>. Öffnen: size.html#blatt=<Name>.
(function(){
  var D=document, PAGE=(location.pathname.split('/').pop()||'').replace(/\.html?$/,'');
  if(PAGE!=='calc' && PAGE!=='size') return;
  var T={
    de:{save:'Als Rechenblatt speichern', name:'Name des Rechenblatts', ok:'Speichern', cancel:'Abbrechen', over:'Überschreiben?', done:'Gespeichert: „{0}“', upd:'Überschrieben: „{0}“', go:'Rechenblätter ansehen →', first:'Erst rechnen, dann speichern.', full:'Speicher voll — nicht gespeichert.', opened:'Rechenblatt geöffnet: „{0}“'},
    en:{save:'Save as calculation sheet', name:'Name of the sheet', ok:'Save', cancel:'Cancel', over:'Overwrite?', done:'Saved: “{0}”', upd:'Overwritten: “{0}”', go:'View calculation sheets →', first:'Calculate first, then save.', full:'Storage full — not saved.', opened:'Calculation sheet opened: “{0}”'},
    fr:{save:'Enregistrer comme note de calcul', name:'Nom de la note', ok:'Enregistrer', cancel:'Annuler', over:'Remplacer ?', done:'Enregistré : « {0} »', upd:'Remplacé : « {0} »', go:'Voir les notes de calcul →', first:'Calculer d’abord, puis enregistrer.', full:'Mémoire pleine — non enregistré.', opened:'Note de calcul ouverte : « {0} »'},
    es:{save:'Guardar como memoria de cálculo', name:'Nombre de la memoria', ok:'Guardar', cancel:'Cancelar', over:'¿Sobrescribir?', done:'Guardado: «{0}»', upd:'Sobrescrito: «{0}»', go:'Ver memorias de cálculo →', first:'Primero calcular, luego guardar.', full:'Memoria llena: no se ha guardado.', opened:'Memoria de cálculo abierta: «{0}»'}};
  function lang(){ try{ if(PAGE==='calc' && typeof calcLang!=='undefined' && T[calcLang]) return calcLang; }catch(e){} var l=null; try{ l=localStorage.getItem('statiq-lang'); }catch(e){} return T[l]?l:'de'; }
  function t(k, a){ return String((T[lang()]||T.de)[k]).replace('{0}', a==null?'':a); }
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  var ICON='<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 15.5h6M9 19h3"/></svg>';

  // ── Seiten-Anpassung ───────────────────────────────────────────────
  function calcTab(){ try{ var c=curTab(); return ['beam','cantilever','cont','frame'].indexOf(c)>=0 ? c : null; }catch(e){ return null; } }
  function calcList(){ var out=[]; try{ for(var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); if(!k || k.indexOf('statiq_sdf_')!==0 || k.indexOf('statiq_sdf_pos_')===0) continue;
    try{ var e=JSON.parse(localStorage.getItem(k)); if(e && e.sdf && (e.sdf.module||'calc')==='calc') out.push({key:k, name:e.name}); }catch(_){} } }catch(e){} return out; }
  var A = PAGE==='calc' ? {
    host: function(t){ return D.getElementById('tab-'+t); },   // ganz unten im Bereich, rechts (v0.11.12)
    def: function(){ var t=calcTab(); if(!t) return ''; try{ var sid=t==='cantilever'?'cant':t, lc=lastCalc[sid], tabs=(calcTranslations[calcLang]||calcTranslations.en).tabs,
        lab={beam:tabs[0],cantilever:tabs[1],cont:tabs[2],frame:tabs[3]}[t]||t; if(!lc) return lab; var g=lc.geometry;
        if(t==='cont') return trf('nameSpans', lab, g.spans.length, g.spans.join('/'));
        if(t==='frame') return lab+' '+supW(lc.supports.A)+'/'+supW(lc.supports.B)+' b='+g.b+'m h='+g.hA+'/'+g.hB+'m'+(g.gable?' f='+g.gable.f+'m':'');
        return lab+' L='+(g.L||'?')+'m'; }catch(e){ return ''; } },
    exists: function(n){ var e=calcList().filter(function(x){ return x.name===n; })[0]; return e ? e.key : null; },
    save: function(n){ var t=calcTab(); if(!t) return 'first'; try{ liveCalc(true); }catch(e){}
      var key=A.exists(n) || 'statiq_sdf_'+Date.now(), r=null;
      try{ r = t==='frame' ? saveFrameCalc({key:key, quiet:true}) : saveCalc(t, {key:key, quiet:true}); }catch(e){ r=null; }
      if(!r) return 'first';
      try{ var o=JSON.parse(localStorage.getItem(key)); o.name=n; o.draft=k4Snap(); localStorage.setItem(key, JSON.stringify(o)); }catch(e){ return 'full'; }
      return 'ok'; }
  } : {
    host: function(){ return D.querySelector('main.main') || D.querySelector('main'); },   // ganz unten auf der Seite, rechts (size v0.7.10)
    def: function(){ try{ return (D.getElementById(nameField()).value||'').trim(); }catch(e){ return ''; } },
    exists: function(n){ try{ return posRead().some(function(p){ return p.name===n; }); }catch(e){ return false; } },
    save: function(n){ try{ var f=D.getElementById(nameField()); if(f){ f.value=n; f.dispatchEvent(new Event('input',{bubbles:true})); } savePos(); }catch(e){ return 'full'; }
      return A.exists(n) ? 'ok' : 'full'; }
  };

  // ── Knopf und Namensfeld ───────────────────────────────────────────
  function build(host){
    if(!host || host.querySelector(':scope > .kbl')) return;
    var w=D.createElement('div'); w.className='kbl';
    w.innerHTML='<button type="button" class="kbl-btn">'+ICON+'<span></span></button>'
      +'<div class="kbl-form" hidden><label class="kbl-l"><span></span><input type="text" class="kbl-in" maxlength="80" autocomplete="off" spellcheck="false"></label>'
      +'<div class="kbl-row"><button type="button" class="kbl-ok"></button><button type="button" class="kbl-x"></button></div></div>'
      +'<div class="kbl-msg" aria-live="polite"></div>';
    host.appendChild(w); label(w);
    var btn=w.querySelector('.kbl-btn'), form=w.querySelector('.kbl-form'), inp=w.querySelector('.kbl-in'), ok=w.querySelector('.kbl-ok'), msg=w.querySelector('.kbl-msg');
    function close(){ form.hidden=true; btn.hidden=false; ok.classList.remove('armed'); ok.textContent=t('ok'); }
    btn.addEventListener('click', function(){ msg.innerHTML=''; label(w); inp.value=A.def(); form.hidden=false; btn.hidden=true; inp.focus(); inp.select(); });
    w.querySelector('.kbl-x').addEventListener('click', close);
    inp.addEventListener('input', function(){ ok.classList.remove('armed'); ok.textContent=t('ok'); });
    inp.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); ok.click(); } else if(e.key==='Escape'){ e.preventDefault(); close(); btn.focus(); } });
    ok.addEventListener('click', function(){
      var n=inp.value.trim()||A.def(); if(!n){ inp.focus(); return; }
      var had=!!A.exists(n);
      if(had && !ok.classList.contains('armed')){ ok.classList.add('armed'); ok.textContent=t('over'); return; }
      var r=A.save(n);
      if(r==='ok'){ close(); msg.innerHTML='<span>'+esc(t(had?'upd':'done', n))+'</span> <a href="projekt.html">'+esc(t('go'))+'</a>'; }
      else msg.textContent=t(r==='first'?'first':'full');
    });
  }
  function label(w){ w.querySelector('.kbl-btn span').textContent=t('save'); w.querySelector('.kbl-l > span').textContent=t('name');
    var ok=w.querySelector('.kbl-ok'); if(!ok.classList.contains('armed')) ok.textContent=t('ok'); w.querySelector('.kbl-x').textContent=t('cancel'); }
  function relabel(){ Array.prototype.forEach.call(D.querySelectorAll('.kbl'), label); }

  // Reste aus dem früheren Projektmodus (bis calc v0.11.10 im Block data-pm): altes Projekt-Fenster verborgen, aber für Prüfstände
  // über mulyAltProj() erreichbar (Speichern/Laden in size, Übernahme aus calc); Ordner-Symbol der alten Kopfzeile → Rechenblätter;
  // Version unten auf der Seite (#k-verfoot).
  function legacy(){
    var L0={ open:window.openProj }; window.mulyAltProj=function(){ var o=D.getElementById('proj-panel'); if(o) o.removeAttribute('hidden'); if(L0.open) L0.open(); };
    window.toggleProj=function(e){ if(e && e.stopPropagation) e.stopPropagation(); location.href='projekt.html'; }; window.openProj=window.toggleProj; window.closeProj=function(){};
    var old=D.getElementById('proj-panel'); if(old){ old.classList.remove('open'); old.setAttribute('hidden',''); }
    var b=D.getElementById('proj-btn'); if(b){ b.removeAttribute('aria-haspopup'); b.removeAttribute('aria-expanded'); }
    var hv=D.querySelector('.app-header .version'), m=D.querySelector('.app-header .module-name');
    if(hv && m && !D.getElementById('k-verfoot')){ var f=D.createElement('div'); f.id='k-verfoot'; f.className='k-verfoot'; f.textContent='kragr · '+m.textContent.trim()+' '+hv.textContent.trim(); D.body.appendChild(f); }
  }
  function init(){
    try{ legacy(); }catch(e){}
    if(PAGE==='calc') ['beam','cantilever','cont','frame'].forEach(function(t){ build(A.host(t)); });
    else build(A.host());
    if(PAGE==='calc' && typeof window.setCalcLang==='function'){ var o=window.setCalcLang; window.setCalcLang=function(){ var r=o.apply(this, arguments); relabel(); return r; }; }
    // Aus „Rechenblätter“ geöffnet
    if(PAGE==='calc' && window.kBlattOpen){ var h=A.host(calcTab()); var m=h && h.querySelector('.kbl-msg'); if(m) m.textContent=t('opened', window.kBlattOpen); }
    if(PAGE==='size'){ var mm=String(location.hash||'').match(/^#blatt=(.+)$/); if(mm){ var n=decodeURIComponent(mm[1]); history.replaceState(null,'',location.pathname+location.search);
      try{ var i=posRead().findIndex(function(p){ return p.name===n; }); if(i>=0){ loadPos(i); var mg=D.querySelector('.kbl .kbl-msg'); if(mg) mg.textContent=t('opened', n); } }catch(e){} } }
  }
  // nach allen anderen Start-Routinen (Spalten in calc entstehen erst beim Start)
  D.readyState==='loading' ? D.addEventListener('DOMContentLoaded', function(){ setTimeout(init, 0); }) : setTimeout(init, 0);
  window.kragrBlatt={ t:t, relabel:relabel };
})();
