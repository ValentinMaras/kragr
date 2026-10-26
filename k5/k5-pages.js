// Seiten-Anpassungen der Design-Schicht 5: welche Karten zu Akkordeons werden und was ihre Kurzfassung zeigt.
window.kragrK5Page = function(K){
  var D=document, $=function(s,r){ return (r||D).querySelector(s); }, $$=function(s,r){ return Array.prototype.slice.call((r||D).querySelectorAll(s)); };
  var txt=function(el){ return el ? el.textContent.replace(/\s+/g,' ').trim() : ''; };
  // Regeln: Karten, die die Seite neu zeichnet, bekommen den Akkordeon-Kopf jedes Mal wieder
  var RULES=[];
  function rule(sel, opt){ RULES.push([sel,opt]); }
  function apply(){
    RULES.forEach(function(r){ $$(r[0]).forEach(function(el){
      if(el.k5acc && el.querySelector(':scope > .k5-head') && el.querySelector(':scope > .k5-body')) return;
      el.k5acc=null; el.classList.remove('k5-acc','k5-closed');
      var o=typeof r[1]==='function' ? r[1](el) : r[1]; if(o) K.acc(el, o); }); });
  }
  var pend=0; function later(){ if(pend) return; pend=requestAnimationFrame(function(){ pend=0; apply(); deco(); K.refreshSums(); }); }
  function deco(){}
  var P=K.page;

  if(P==='calc'){
    // Knotentabelle: zugeklappt, Kurzfassung = Anzahl Knoten und Stäbe
    rule('.k-knoten', function(el){ var h=$(':scope > .card-title', el)||$(':scope > .k5-head', el); if(!h) return null;
      return {head:h, key:'knoten', closed:true, sum:function(c){ var n=$$('.k-kn-list > li', c).length, b=$$('.k-kn-tab tr.k-kn-bar', c).length;
        var W={de:['Knoten','Stab','Stäbe'],en:['nodes','member','members'],fr:['nœuds','barre','barres'],es:['nudos','barra','barras']}[K.lang()]||['Knoten','Stab','Stäbe'];
        return n ? n+' '+W[0]+' · '+b+' '+(b===1?W[1]:W[2]) : ''; }}; });
    // Rahmen: Vorlage, Lager A, Lager B, Kopf, Gelenke als Unterabschnitte (immer nur einer offen)
    rule('#tab-frame .card > div', function(el){ if(/k5-head|k5-body|card-title-row/.test(el.className) || el.closest('.k-knoten')) return null; var h=$(':scope > .card-title', el); if(!h) return null;
      var key=h.getAttribute('data-i18n')||txt(h);
      return {head:h, key:'frame-'+key, closed:key!=='framePresets', group:'frame-sys', sum:function(c){
        var a=$$('.toggle-btn.active, .toggle-btn[aria-pressed="true"]', c).map(txt); if(a.length) return a.join(' · ');
        var n=$$('.load-item, .k-row', c).length; return n ? String(n) : ''; }}; });
    // Ergebniszahlen und Diagramm-Umschalter
    var tick=function(){ K.watchNumbers('.results-grid .m-value');
      $$('.diagram-toggle-row').forEach(function(r){ K.slider(r, '.diagram-toggle-btn[class*="active-"]'); }); };
    D.addEventListener('click', function(e){ var b=e.target.closest && e.target.closest('.diagram-toggle-btn'); if(!b) return;
      var card=b.closest('.card'); setTimeout(function(){ var s=card && $('svg[id*="diag"], .diagram-wrap svg, svg', card.querySelector('.diagram-toggle-row') ? card : null);
        var list=$$('svg', card).filter(function(x){ return x.getBoundingClientRect().height>60; }); K.wipe(list[0]); void s; }, 0); });
    // Lösungsweg-Karte: gleicher Kopf wie die anderen Karten, startet zugeklappt; Kurzfassung = Zahl der Schritte
    var STEPW={de:'Schritte',en:'steps',fr:'étapes',es:'pasos'};
    var RW0=false; try{ if(localStorage.getItem('statiq-rw-closed')===null){ localStorage.setItem('statiq-rw-closed','1'); RW0=true; } }catch(e){}
    if(RW0) $$('.rw-card').forEach(function(c){ c.classList.add('closed'); });
    deco=function(){ tick();
      $$('.rw-card').forEach(function(c){ var h=$(':scope > .rw-title', c); if(!h) return; c.classList.add('k5-rw');
        if(!$(':scope > .k5-tri', h)){ var sp=D.createElement('span'); sp.className='k5-hsum'; h.appendChild(sp); h.insertAdjacentHTML('beforeend', K.CHEV); h.setAttribute('role','button'); h.tabIndex=0; }
        var n=$$('.rw-body > .st', c).length, v=c.classList.contains('closed') && n ? n+' '+(STEPW[K.lang()]||STEPW.de) : '';
        var sp2=$(':scope > .k5-hsum', h); if(sp2.textContent!==v) sp2.textContent=v; h.setAttribute('aria-expanded', String(!c.classList.contains('closed'))); }); };
    // Ergebnis-Details (Knotentabelle, Lösungsweg): immer nur eines offen
    D.addEventListener('click', function(e){ var h=e.target.closest && e.target.closest('.rw-card > .rw-title'); if(!h) return; var rw=h.parentNode;
      setTimeout(function(){ if(rw.classList.contains('closed')) return; var col=rw.parentNode; $$('.k-knoten.k5-acc', col).forEach(function(k){ if(!k.classList.contains('k5-closed')) K.setClosed(k, true); }); deco(); }, 0); });
    D.addEventListener('k5toggle', function(e){ var c=e.detail.card; if(!e.detail.open || !c.classList.contains('k-knoten')) return;
      var col=c.closest('.col-out')||c.parentNode.parentNode; $$('.rw-card', col.parentNode||D).forEach(function(r){ if(!r.classList.contains('closed') && r.offsetParent!==null){ r.classList.add('closed'); try{ localStorage.setItem('statiq-rw-closed','1'); }catch(_){} } }); deco(); });
    // System wechseln: Karten neu einblenden
    D.addEventListener('click', function(e){ if(e.target.closest && e.target.closest('.pick-menu')) setTimeout(function(){ $$('main .card').forEach(function(c){ c.k5seen=0; }); K.reveal('main:not(.hidden) .card, main:not(.hidden) .results-grid .metric'); }, 30); });
  }

  if(P==='size'){
    // Eingabekarten: immer nur eine offen; Kurzfassung im Kopf (wie die Lastzeilen in calc)
    var FS='statiq-size-fold';
    var sumOf=function(c){ try{ return typeof foldSummary==='function' ? foldSummary(c) : ''; }catch(e){ return ''; } };
    deco=function(){
      $$('.col-in .card.fold').forEach(function(c){ var h=$(':scope > .card-title', c); if(!h) return; c.classList.add('k5-fold');
        if(!$(':scope > .k5-hsum', h)){ var s=D.createElement('span'); s.className='k5-hsum'; h.appendChild(s); h.insertAdjacentHTML('beforeend', K.CHEV); h.setAttribute('role','button'); h.tabIndex=0; }
        var s2=$(':scope > .k5-hsum', h), v=c.classList.contains('closed') ? sumOf(c) : ''; if(s2.textContent!==v) s2.textContent=v; h.setAttribute('aria-expanded', String(!c.classList.contains('closed'))); });
      $$('#details > .card.dfold').forEach(function(c){ var h=$(':scope > .card-title', c); if(h && !$(':scope > .k5-tri', h)) h.insertAdjacentHTML('beforeend', K.CHEV); });
      K.watchBars($('#chk-table'), function(r){ var a=$('a', r); return a ? a.getAttribute('href') : r.rowIndex; });
    };
    D.addEventListener('click', function(e){ var h=e.target.closest && e.target.closest('.col-in .card.fold > .card-title'); if(!h || e.target.closest('button, a, input, select')) return;
      var card=h.parentNode; if(card.classList.contains('closed')){ later(); return; }
      var st={}; try{ st=JSON.parse(localStorage.getItem(FS)||'{}'); }catch(_){}
      $$('.col-in .card.fold').forEach(function(c){ if(c===card || c.classList.contains('closed') || c.offsetParent===null) return; c.classList.add('closed'); if(c.dataset.fold) st[c.dataset.fold]=true; });
      try{ localStorage.setItem(FS, JSON.stringify(st)); }catch(_){}
      later();
    });
    D.addEventListener('keydown', function(e){ var h=e.target; if((e.key==='Enter'||e.key===' ') && h.matches && h.matches('.col-in .card.fold > .card-title')){ e.preventDefault(); h.click(); } });
    // Beim Laden: nur die erste offene Eingabekarte bleibt offen (Akkordeon)
    setTimeout(function(){ var open=$$('.col-in .card.fold').filter(function(c){ return !c.classList.contains('closed') && c.offsetParent!==null; });
      open.slice(1).forEach(function(c){ c.classList.add('closed'); }); deco(); }, 0);
    D.addEventListener('click', function(e){ if(e.target.closest && e.target.closest('.pick-menu, .seg button, [data-mode]')) setTimeout(function(){ var open=$$('.col-in .card.fold').filter(function(c){ return !c.classList.contains('closed') && c.offsetParent!==null; }); open.slice(1).forEach(function(c){ c.classList.add('closed'); }); deco(); }, 40); });
    // Umfang und Grundlagen: zugeklappt
    rule('#scope-card', function(el){ var h=$(':scope > .card-title', el); return h ? {head:h, key:'scope', closed:true, sum:function(){ return ''; }} : null; });
  }

  if(P==='ref'){
    // Seitenkopf wie die Auswahl in calc/size: Tippen öffnet am Handy die Themenliste
    D.addEventListener('click', function(e){ var h=e.target.closest && e.target.closest('#main .page-head'); if(!h || !$('#main .menu-toggle') || window.innerWidth>999) return;
      if(typeof toggleSideMenu==='function'){ e.stopPropagation(); toggleSideMenu(); } });
  }

  if(P==='rechtliches'){
    // Seitenkopf als Karte: Titel, Einleitung und Sprungmarken zusammen
    deco=function(){ var c=$('#content'), h=c && $(':scope > h1', c); if(!h) return; var w=D.createElement('div'); w.className='k5-card k5-phead'; c.insertBefore(w, h);
      var n=h; while(n && n!==w){ var nx=n.nextElementSibling; w.appendChild(n); if(nx && (nx.tagName==='H2' || nx.classList.contains('card') || nx.tagName==='SECTION')) break; n=nx; if(w.children.length>=3) break; } };
  }

  if(P==='projekt'){
    // Positionen als Akkordeon: Kopf mit Nummer, Titel, Kurzfassung (System · Nachweise); Rücksprung #pos-… öffnet die Position
    var W={de:['Nachweis','Nachweise','kein System'],en:['check','checks','no system'],fr:['vérification','vérifications','pas de système'],es:['comprobación','comprobaciones','sin sistema']};
    var hashId=function(){ return (location.hash.match(/^#pos-(.+)$/)||[])[1]; };
    // Neu angelegte Position (＋ Position): offen, die anderen klappen zu
    var known=null;
    rule('#list > .pos', function(el){ var h=$(':scope > .pos-h', el); if(!h) return null; var id=el.dataset.id, all=$$('#list > .pos'), ids=all.map(function(x){ return x.dataset.id; });
      if(!known) known=ids.slice();
      var nw=ids.filter(function(x){ return known.indexOf(x)<0; });
      if(nw.length){ var open=nw[nw.length-1]; known=known.concat(nw); try{ var st=JSON.parse(localStorage.getItem('kragr-k5-acc')||'{}'); ids.forEach(function(x){ st['projekt:pos-'+x]=x!==open; }); localStorage.setItem('kragr-k5-acc', JSON.stringify(st)); }catch(e){} }
      var isNew=false;
      var hid=hashId(), first=all[0]===el;
      return {head:h, key:'pos-'+id, group:'pos', closed: isNew ? false : hid ? hid!==id : !first, sum:function(c){ var w=W[K.lang()]||W.de;
        var sys=$('.items .it .d b', c), n=$$('.items .tag.size', c).length; return (sys ? sys.textContent : w[2])+' · '+n+' '+(n===1?w[0]:w[1]); }}; });
    if(hashId()) try{ var st=JSON.parse(localStorage.getItem('kragr-k5-acc')||'{}'); Object.keys(st).forEach(function(k){ if(/^projekt:pos-/.test(k)) st[k]=k!=='projekt:pos-'+hashId(); }); localStorage.setItem('kragr-k5-acc', JSON.stringify(st)); }catch(e){}
  }

  new MutationObserver(later).observe(D.body, {childList:true, subtree:true});
  apply(); deco();
  D.addEventListener('k5toggle', function(){ deco(); });
  D.addEventListener('change', function(e){ if(e.target && (e.target.id==='lang-sel'||e.target.id==='lang')) setTimeout(function(){ K.refreshSums(); deco(); }, 50); }, true);
  D.addEventListener('click', function(){ setTimeout(deco, 0); });
};
