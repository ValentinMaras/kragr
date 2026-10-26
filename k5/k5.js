// kragr-Design 5 (Oktober 2026): Burgermenü, Akkordeon-Karten und ruhige Bewegung. Identisch in calc, size, ref, projekt, rechtliches.
// Bedienelemente der alten Kopfzeile (#lang-sel, #ueb-btn, #theme-btn, #proj-btn) bleiben im DOM (versteckt); das Menü steuert sie.
(function(){
  if(window.kragrK5) return;
  var D=document, H=D.documentElement;
  var PAGE=(location.pathname.split('/').pop()||'index.html').replace(/\.html?$/,'')||'index';
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  // Automatisierte Browser (Tests) ohne Bewegung, außer ?k5motion steht in der Adresse
  if(navigator.webdriver && !/k5motion/.test(location.search)) H.classList.add('k5-still');
  var STILL=function(){ return RM || H.classList.contains('k5-still'); };
  var T={
    de:{menu:'Menü',open:'Menü öffnen',close:'Menü schließen',mods:'Module',calc:'Schnittgrößen',size:'Bemessung',ref:'Nachschlagewerk',proj:'Meine Projekte',projS:'Positionen aus calc und size',
        set:'Einstellungen',ueb:'Übungsmodus',uebS:'Zahlen verborgen, selbst rechnen',look:'Erscheinungsbild',auto:'Auto',light:'Hell',dark:'Dunkel',lang:'Sprache',legal:'Impressum · Datenschutz',home:'Startseite',more:'mehr',less:'weniger'},
    en:{menu:'Menu',open:'Open menu',close:'Close menu',mods:'Modules',calc:'Internal forces',size:'Design & sizing',ref:'Reference',proj:'My projects',projS:'Items from calc and size',
        set:'Settings',ueb:'Practice mode',uebS:'Numbers hidden, work it out',look:'Appearance',auto:'Auto',light:'Light',dark:'Dark',lang:'Language',legal:'Legal notice · Privacy',home:'Home',more:'more',less:'less'},
    fr:{menu:'Menu',open:'Ouvrir le menu',close:'Fermer le menu',mods:'Modules',calc:'Efforts internes',size:'Dimensionnement',ref:'Référence',proj:'Mes projets',projS:'Éléments de calc et size',
        set:'Réglages',ueb:'Mode exercice',uebS:'Valeurs masquées, à calculer soi-même',look:'Apparence',auto:'Auto',light:'Clair',dark:'Sombre',lang:'Langue',legal:'Mentions légales · Confidentialité',home:'Accueil',more:'plus',less:'moins'},
    es:{menu:'Menú',open:'Abrir menú',close:'Cerrar menú',mods:'Módulos',calc:'Esfuerzos internos',size:'Dimensionado',ref:'Referencia',proj:'Mis proyectos',projS:'Elementos de calc y size',
        set:'Ajustes',ueb:'Modo práctica',uebS:'Valores ocultos, calcúlalo tú',look:'Apariencia',auto:'Auto',light:'Claro',dark:'Oscuro',lang:'Idioma',legal:'Aviso legal · Privacidad',home:'Inicio',more:'más',less:'menos'}};
  // Startseite: keine Auswahlliste, die Sprache wechselt über ihr setLang()
  var VSEL={ _v:null, get value(){ if(this._v) return this._v; try{ return localStorage.getItem('statiq-lang')||'en'; }catch(e){ return 'en'; } }, set value(v){ this._v=v; },
    dispatchEvent:function(){ var v=this._v; this._v=null; if(v && typeof window.setLang==='function') window.setLang(v); return true; } };
  function langSel(){ return D.getElementById('lang-sel')||D.getElementById('lang')||(PAGE==='index' && typeof window.setLang==='function' ? VSEL : null); }
  function lang(){ var l=null; try{ l=localStorage.getItem('statiq-lang'); }catch(e){} if(!T[l]){ var s=langSel(); l=s&&s.value; } return T[l]?l:'de'; }
  function t(k){ return (T[lang()]||T.de)[k]; }
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  var CHEV='<svg class="k-chev k5-tri" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><path d="M1 7 L5 3 L9 7 Z"/></svg>';

  // ── Höhe weich ändern (FLIP): vorher messen, Änderung ausführen, nachher animieren ──────────
  function measure(els){ return els.map(function(el){ return {el:el, h:el.getBoundingClientRect().height}; }); }
  function flip(before, anchor, anchorTop){
    if(anchor && anchorTop!=null){ var d=anchor.getBoundingClientRect().top-anchorTop; if(Math.abs(d)>1) window.scrollBy(0,d); }
    if(STILL()) return;
    before.forEach(function(b){ var el=b.el; if(!el.isConnected) return; var h1=el.getBoundingClientRect().height; if(Math.abs(h1-b.h)<2 || !el.animate) return;
      var ov=el.style.overflow; el.style.overflow='hidden';
      var a=el.animate([{height:b.h+'px'},{height:h1+'px'}],{duration:Math.min(520, 260+Math.abs(h1-b.h)*0.25), easing:'cubic-bezier(.22,.8,.24,1)'});
      a.onfinish=a.oncancel=function(){ el.style.overflow=ov; }; });
  }
  function openAnim(card){ if(STILL()) return; card.classList.remove('k5-open-anim'); void card.offsetWidth; card.classList.add('k5-open-anim'); setTimeout(function(){ card.classList.remove('k5-open-anim'); }, 450); }

  // ── Akkordeon: Karte mit Kopf (Titel · Kurzfassung · Pfeil), Gruppe = immer nur eine offen ──────
  // opt: {head, key, closed, group, sum(card) → Text, solo:true (nicht in Gruppe), store}
  var ACC_STORE='kragr-k5-acc';
  function accState(){ try{ return JSON.parse(localStorage.getItem(ACC_STORE)||'{}'); }catch(e){ return {}; } }
  function accSave(key, closed){ if(!key) return; var s=accState(); s[PAGE+':'+key]=closed; try{ localStorage.setItem(ACC_STORE, JSON.stringify(s)); }catch(e){} }
  function acc(card, opt){
    if(!card || card.k5acc) return; opt=opt||{};
    var head=opt.head||card.querySelector(':scope > .card-title'); if(!head) return;
    // Kopf in eine eigene Zeile legen: der Titel selbst kann übersetzt (textContent) werden, ohne Pfeil und Kurzfassung zu verlieren
    if(!head.classList.contains('k5-head')){ var w=D.createElement('div'); w.className='k5-head'; card.insertBefore(w, head); w.appendChild(head); head=w; }
    card.k5acc=opt; card.classList.add('k5-acc');
    head.setAttribute('role','button'); head.tabIndex=0;
    var body=D.createElement('div'); body.className='k5-body';
    Array.prototype.slice.call(card.childNodes).forEach(function(n){ if(n!==head) body.appendChild(n); });
    card.appendChild(body);
    if(!head.querySelector('.k5-hsum')){ var s=D.createElement('span'); s.className='k5-hsum'; head.appendChild(s); }
    if(!head.querySelector('.k5-tri')) head.insertAdjacentHTML('beforeend', CHEV);
    if(opt.group) card.dataset.k5g=opt.group;
    var st=accState(), k=PAGE+':'+(opt.key||'');
    var closed = opt.key && (k in st) ? st[k] : !!opt.closed;
    setClosed(card, closed, true);
    head.addEventListener('click', function(e){ if(e.target.closest('a, input, select, textarea, .info-btn, button:not(.k5-head)')) return; toggle(card); });
    head.addEventListener('keydown', function(e){ if((e.key==='Enter'||e.key===' ') && e.target===head){ e.preventDefault(); toggle(card); } });
  }
  function setClosed(card, c, quiet){
    card.classList.toggle('k5-closed', c);
    var head=card.querySelector(':scope > .k5-head'); if(head) head.setAttribute('aria-expanded', c?'false':'true');
    updSum(card);
    if(!quiet) accSave(card.k5acc&&card.k5acc.key, c);
  }
  function updSum(card){ var o=card.k5acc, s=card.querySelector(':scope > .k5-head .k5-hsum'); if(!o||!s) return;
    var tx=''; try{ tx=o.sum ? (o.sum(card, card.classList.contains('k5-closed'))||'') : ''; }catch(e){}
    if(s.textContent!==tx) s.textContent=tx; }
  function groupOf(card){ var g=card.dataset.k5g; if(!g) return []; var p=card.parentNode;
    return Array.prototype.filter.call(D.querySelectorAll('[data-k5g="'+g+'"]'), function(c){ return c!==card && c.offsetParent!==null && (!p || c.parentNode===p || c.closest('[data-k5gscope]')===card.closest('[data-k5gscope]')); }); }
  function toggle(card, force){
    var open = force!=null ? force : card.classList.contains('k5-closed');
    var others = open ? groupOf(card).filter(function(c){ return !c.classList.contains('k5-closed'); }) : [];
    var before=measure([card].concat(others)), top=card.getBoundingClientRect().top;
    others.forEach(function(c){ setClosed(c, true); });
    setClosed(card, !open);
    flip(before, card, top);
    if(open) openAnim(card);
    try{ D.dispatchEvent(new CustomEvent('k5toggle',{detail:{card:card, open:open}})); }catch(e){}
  }
  function refreshSums(){ Array.prototype.forEach.call(D.querySelectorAll('.k5-acc'), updSum); }
  var sumT=0; D.addEventListener('input', function(){ clearTimeout(sumT); sumT=setTimeout(refreshSums, 120); }, true);
  D.addEventListener('change', function(){ clearTimeout(sumT); sumT=setTimeout(refreshSums, 60); }, true);

  // Fremde Klapp-Mechaniken (Lasten-Karte, Lastzeilen, size-Karten, Rechenschritte, ref-Seitenleiste): weich animieren
  var FOREIGN='.k-loads > .k-head, .load-item .k-row-head, .load-item > .k-rh, .fold > .card-title, .dfold > .card-title, .k-row > button:first-child, #sidebar .sb-sub > button, #sidebar button.sb-h, #sidebar .grp > button, .pos-head, [data-k5-flip]';
  D.addEventListener('click', function(e){
    if(STILL()) return;
    var h=e.target.closest && e.target.closest(FOREIGN); if(!h || h.closest('.k5-acc > .k5-head')) return;
    var card=h.closest('.load-item, .card, .k-loads, .fold, .dfold, .sb-group, li, section, div') || h.parentNode;
    var parent=card.parentNode, sibs=parent ? Array.prototype.filter.call(parent.children, function(c){ return c.offsetParent!==null; }) : [card];
    var before=measure(sibs.slice(0,40)), top=card.getBoundingClientRect().top;
    requestAnimationFrame(function(){ flip(before, null, null); if(card.isConnected && !card.classList.contains('closed') && !card.classList.contains('k-closed')) openAnim(card); });
    void top;
  }, true);

  // ── Kopfzeile: Logo · ☰ ─────────────────────────────────────────────
  var MODS=[['calc','calc.html','Σ'],['size','size.html','η'],['ref','ref.html','§']];
  var ICON_PROJ='<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M2.6 5.6c0-.9.7-1.6 1.6-1.6h3.4l1.7 1.9h6.5c.9 0 1.6.7 1.6 1.6v7.4c0 .9-.7 1.6-1.6 1.6H4.2c-.9 0-1.6-.7-1.6-1.6z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>';
  var burger, menu, scrim, lastFocus;
  function buildHeader(){
    var hdr=D.querySelector('.app-header.k-hdr, header.k5-idx'); if(!hdr || D.getElementById('k5-burger')) return;
    burger=D.createElement('button'); burger.type='button'; burger.id='k5-burger'; burger.className='k5-burger';
    burger.setAttribute('aria-haspopup','dialog'); burger.setAttribute('aria-expanded','false'); burger.setAttribute('aria-controls','k5-menu');
    burger.innerHTML='<span class="k5-cur"></span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line class="l1" x1="4" y1="7" x2="20" y2="7"/><line class="l2" x1="4" y1="12" x2="20" y2="12"/><line class="l3" x1="4" y1="17" x2="20" y2="17"/></svg><span class="k5-dot"></span>';
    burger.addEventListener('click', function(){ menu && menu.classList.contains('open') ? closeMenu() : openMenu(); });
    hdr.appendChild(burger);
    scrim=D.createElement('div'); scrim.className='k5-scrim'; scrim.addEventListener('click', closeMenu);
    menu=D.createElement('div'); menu.id='k5-menu'; menu.className='k5-menu'; menu.setAttribute('role','dialog'); menu.setAttribute('aria-modal','true');
    D.body.appendChild(scrim); D.body.appendChild(menu);
    D.addEventListener('keydown', function(e){ if(e.key==='Escape' && menu.classList.contains('open')){ closeMenu(); } });
    labelBurger();
  }
  function labelBurger(){ if(!burger) return; var cur=burger.querySelector('.k5-cur'); var m=PAGE==='projekt'?t('proj'):(MODS.some(function(x){return x[0]===PAGE;})?PAGE:'');
    var tx=t('menu'); if(cur.textContent!==tx) cur.textContent=tx; burger.setAttribute('aria-label', t('open')+(m?' ('+m+')':'')); }
  function themeNow(){ return H.dataset.theme || (function(){ try{ return localStorage.getItem('muly-theme')||'auto'; }catch(e){ return 'auto'; } })(); }
  function setTheme(v){ var n=0; while(themeNow()!==v && n++<3 && window.mulyTheme) window.mulyTheme(); if(!window.mulyTheme){ try{ localStorage.setItem('muly-theme',v); }catch(e){} } }
  function hrefOf(name){ var a=D.querySelector('.k-hdr .header-links a[href^="'+name+'.html"]'); return a ? a.getAttribute('href') : name+'.html'; }
  function version(){ var v=D.querySelector('.k-hdr .version'); var s=v&&v.textContent.trim(); if(!s){ var m=(D.documentElement.outerHTML.slice(0,200).match(/v(\d+\.\d+\.\d+)/)||[])[0]; s=m||''; } return s; }
  function seg(id, items, cur){ return '<div class="k5-segm" role="group" id="'+id+'">'+items.map(function(it){ return '<button type="button" data-v="'+it[0]+'" aria-pressed="'+(it[0]===cur)+'">'+esc(it[1])+'</button>'; }).join('')+'<span class="k5-pill" aria-hidden="true"></span></div>'; }
  function renderMenu(){
    var ueb=D.getElementById('ueb-btn'), i=0, h='';
    function I(){ return ' style="--i:'+(i++)+'"'; }
    h+='<div class="k5-mhead"'+I()+'><a class="k5-mlogo" href="index.html" aria-label="'+esc(t('home'))+'">krag'+(D.querySelector('.k-hdr .logo-r')||{outerHTML:'r'}).outerHTML+'</a><button type="button" class="k5-x" aria-label="'+esc(t('close'))+'">✕</button></div>';
    h+='<div class="k5-mlabel"'+I()+'>'+esc(t('mods'))+'</div>';
    MODS.forEach(function(m){ h+='<a class="k5-mod" href="'+esc(hrefOf(m[0]))+'"'+(PAGE===m[0]?' aria-current="page"':'')+I()+' data-mod="'+m[0]+'"><span class="k5-ic">'+m[2]+'</span><span class="k5-mt"><b>'+m[0]+'</b><span>'+esc(t(m[0]))+'</span></span></a>'; });
    h+='<a class="k5-mod" href="projekt.html"'+(PAGE==='projekt'?' aria-current="page"':'')+I()+' data-mod="projekt"><span class="k5-ic">'+ICON_PROJ+'</span><span class="k5-mt"><b>'+esc(t('proj'))+'</b><span>'+esc(t('projS'))+'</span></span><span class="k5-badge"></span></a>';
    h+='<div class="k5-mlabel"'+I()+'>'+esc(t('set'))+'</div>';
    if(ueb && ueb.offsetParent!==null || ueb && getComputedStyle(ueb).display!=='none' || ueb && ueb.closest('.hdr-tools')) h+='<div class="k5-row"'+I()+'><span class="k5-rt">'+esc(t('ueb'))+'<span>'+esc(t('uebS'))+'</span></span><button type="button" class="k5-sw" id="k5-ueb" role="switch" aria-checked="'+(ueb.getAttribute('aria-pressed')==='true')+'" aria-label="'+esc(t('ueb'))+'"></button></div>';
    h+='<div class="k5-row k5-col"'+I()+'><span class="k5-rt">'+esc(t('look'))+'</span>'+seg('k5-theme',[['auto',t('auto')],['light',t('light')],['dark',t('dark')]], themeNow())+'</div>';
    if(langSel()) h+='<div class="k5-row k5-col"'+I()+'><span class="k5-rt">'+esc(t('lang'))+'</span>'+seg('k5-lang',[['de','DE'],['en','EN'],['fr','FR'],['es','ES']], lang())+'</div>';
    h+='<div class="k5-mfoot"'+I()+'><span class="k5-ver">'+esc(version()?('kragr'+(MODS.some(function(x){return x[0]===PAGE;})||PAGE==='projekt'?'·'+PAGE:'')+' '+version()):'kragr')+'</span><a href="rechtliches.html">'+esc(t('legal'))+'</a></div>';
    menu.innerHTML=h; menu.setAttribute('aria-label', t('menu'));
    menu.querySelector('.k5-x').onclick=closeMenu;
    var sw=menu.querySelector('#k5-ueb'); if(sw) sw.onclick=function(){ closeMenu(); setTimeout(function(){ ueb.click(); }, STILL()?0:180); };
    Array.prototype.forEach.call(menu.querySelectorAll('#k5-theme button'), function(b){ b.onclick=function(){ setTheme(b.dataset.v); pressSeg(b); }; });
    Array.prototype.forEach.call(menu.querySelectorAll('#k5-lang button'), function(b){ b.onclick=function(){ var s=langSel(); if(!s||s.value===b.dataset.v) return; pressSeg(b); s.value=b.dataset.v;
      setTimeout(function(){ s.dispatchEvent(new Event('change',{bubbles:true})); if(menu.isConnected){ renderMenu(); placePills(); labelBurger(); } }, STILL()?0:160); }; });
    var pb=D.getElementById('proj-btn'); var st=pb&&pb.dataset.st; menu.querySelector('[data-mod="projekt"]').classList.toggle('k5-unsaved', st==='changed'||st==='new');
  }
  function pressSeg(b){ Array.prototype.forEach.call(b.parentNode.querySelectorAll('button'), function(x){ x.setAttribute('aria-pressed', String(x===b)); }); placePills(); }
  function placePills(){ Array.prototype.forEach.call(D.querySelectorAll('.k5-segm'), function(g){ var p=g.querySelector('.k5-pill'), b=g.querySelector('button[aria-pressed="true"]'); if(!p) return;
    if(!b){ p.style.width='0'; return; } p.style.width=b.offsetWidth+'px'; p.style.transform='translateX('+b.offsetLeft+'px)'; }); }
  function openMenu(){ if(!menu) return; lastFocus=D.activeElement; renderMenu(); menu.classList.add('open'); scrim.classList.add('open'); D.body.classList.add('k5-lock');
    burger.setAttribute('aria-expanded','true'); requestAnimationFrame(placePills); var f=menu.querySelector('[aria-current="page"]')||menu.querySelector('.k5-mod'); if(f) f.focus({preventScroll:true}); }
  function closeMenu(){ if(!menu||!menu.classList.contains('open')) return; menu.classList.remove('open'); scrim.classList.remove('open'); D.body.classList.remove('k5-lock');
    burger.setAttribute('aria-expanded','false'); if(lastFocus && lastFocus.focus) try{ lastFocus.focus({preventScroll:true}); }catch(e){} }
  // Fokus im Menü halten
  D.addEventListener('keydown', function(e){ if(e.key!=='Tab' || !menu || !menu.classList.contains('open')) return;
    var f=menu.querySelectorAll('a,button'); if(!f.length) return; var a=f[0], z=f[f.length-1];
    if(e.shiftKey && D.activeElement===a){ e.preventDefault(); z.focus(); } else if(!e.shiftKey && D.activeElement===z){ e.preventDefault(); a.focus(); } });

  // ── Einblenden beim Laden und beim Scrollen ─────────────────────────────
  var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function(es){ es.forEach(function(en){ if(en.isIntersecting){ show(en.target); io.unobserve(en.target); } }); }, {rootMargin:'0px 0px -8% 0px'}) : null;
  var revealN=0, revealT=0;
  function show(el){ var now=Date.now(); if(now-revealT>400) revealN=0; revealT=now; el.style.setProperty('--k5-d', Math.min(revealN++,8)*55+'ms'); el.classList.add('k5-rv');
    setTimeout(function(){ el.classList.remove('k5-rv'); el.style.removeProperty('--k5-d'); }, 1300); }
  function reveal(sel){ if(STILL()) return; Array.prototype.forEach.call(D.querySelectorAll(sel), function(el){ if(el.k5seen || el.offsetParent===null) return; el.k5seen=1; io ? io.observe(el) : show(el); }); }

  // ── Zahlen zählen beim ersten Erscheinen hoch, danach kurzes Nachrücken bei Änderung ──
  // Der echte Text bleibt unverändert im Element; gezählt wird in einer darübergelegten Ebene.
  function countUp(el){
    if(STILL() || el.k5counted) return; var txt=el.textContent.trim(), m=txt.match(/^(-?)(\d[\d.,\s]*)(.*)$/); if(!m) return; el.k5counted=1;
    var raw=m[2].trim(), dec=(raw.match(/[.,](\d+)$/)||[])[1]||'', sep=(raw.match(/[.,](?=\d+$)/)||[])[0]||'.';
    var val=parseFloat(raw.replace(/[\s]/g,'').replace(sep===','?/\./g:/,/g,'').replace(',','.')); if(!isFinite(val)||val===0) return;
    var o=D.createElement('span'); o.className='k5-count'; o.setAttribute('aria-hidden','true'); el.classList.add('k5-counting'); el.appendChild(o);
    var t0=performance.now(), dur=700;
    (function step(now){ var p=Math.min(1,(now-t0)/dur), e=1-Math.pow(1-p,3), v=val*e;
      o.textContent=m[1]+v.toFixed(dec.length).replace('.',sep)+m[3];
      if(p<1 && o.isConnected) requestAnimationFrame(step); else { o.remove(); el.classList.remove('k5-counting'); } })(t0);
  }
  function watchNumbers(sel){
    Array.prototype.forEach.call(D.querySelectorAll(sel), function(el){ if(el.k5w) return; el.k5w=1; var last=el.textContent;
      if(/\d/.test(last) && el.offsetParent!==null) countUp(el);
      new MutationObserver(function(){ var now=el.textContent; if(el.querySelector('.k5-count')) return; if(now===last) return; var was=last; last=now;
        if(!/\d/.test(was) || !el.k5counted){ if(el.offsetParent!==null) countUp(el); return; }
        if(STILL()) return; el.classList.remove('k5-tick'); void el.offsetWidth; el.classList.add('k5-tick'); }).observe(el,{childList:true, characterData:true, subtree:true}); });
  }

  // ── Ausnutzungsbalken: von alter auf neue Breite gleiten ─────────────────
  var BARW={};
  function watchBars(host, rowKey){
    if(!host || host.k5b) return; host.k5b=1;
    function run(){ var rows=host.querySelectorAll('tr'); Array.prototype.forEach.call(rows, function(r, i){ var b=r.querySelector('.bar > i'); if(!b) return;
      var k=rowKey(r,i), w=b.style.width; var from=(k in BARW)?BARW[k]:'0%'; BARW[k]=w; if(STILL() || from===w || !b.animate) return;
      b.animate([{width:from},{width:w}],{duration:from==='0%'?820:480, delay:from==='0%'?120+i*45:0, easing:'cubic-bezier(.22,.8,.24,1)', fill:'backwards'}); }); }
    new MutationObserver(run).observe(host,{childList:true}); run();
  }

  // ── Segment-Umschalter (M/Q/N/w): gleitende Fläche unter der aktiven Taste ──
  function slider(host, activeSel){
    if(!host || host.k5s) return; host.k5s=1; host.classList.add('k5-seg-host','k5-seg-on'); var p=D.createElement('span'); p.className='k5-pill'; host.appendChild(p);
    function place(){ var b=host.querySelector(activeSel); if(!b||!host.offsetWidth){ p.style.opacity='0'; return; } p.style.opacity='1'; p.style.width=b.offsetWidth+'px'; p.style.transform='translateX('+b.offsetLeft+'px)'; p.style.top=b.offsetTop+'px'; p.style.height=b.offsetHeight+'px'; p.style.bottom='auto'; }
    new MutationObserver(place).observe(host,{attributes:true, subtree:true, attributeFilter:['class','aria-pressed']});
    window.addEventListener('resize', place); place(); host.k5place=place;
  }
  function wipe(el){ if(STILL()||!el) return; el.classList.remove('k5-wipe'); void el.getBoundingClientRect(); el.classList.add('k5-wipe'); setTimeout(function(){ el.classList.remove('k5-wipe'); }, 900); }

  window.kragrK5={ page:PAGE, acc:acc, toggle:toggle, setClosed:setClosed, refreshSums:refreshSums, flip:flip, measure:measure, reveal:reveal, countUp:countUp,
    watchNumbers:watchNumbers, watchBars:watchBars, slider:slider, wipe:wipe, openMenu:openMenu, closeMenu:closeMenu, t:t, lang:lang, still:STILL, CHEV:CHEV };

  function init(){
    buildHeader();
    try{ if(window.kragrK5Page) window.kragrK5Page(window.kragrK5); }catch(e){ if(window.console) console.error(e); }
    reveal('.k5-reveal, main .card, .pick-btn, .k5-card, .results-grid .metric');
    window.addEventListener('resize', function(){ if(menu && menu.classList.contains('open')) placePills(); });
    new MutationObserver(function(){ labelBurger(); }).observe(H,{attributes:true, attributeFilter:['lang']});
  }
  if(D.readyState==='loading') D.addEventListener('DOMContentLoaded', init); else init();
})();
