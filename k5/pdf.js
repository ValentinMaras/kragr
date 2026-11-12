// kragr · PDF aus einem Bericht (11.11.2026, Kopf auf jeder Seite 12.11.2026): erzeugt eine echte PDF-Datei im Browser (html2canvas + jsPDF, beide MIT, selbst gehostet)
// und gibt sie zum Teilen (Handy: Teilen-Menü mit Dateien, Mail, Messenger) oder zum Herunterladen (Rechner) aus.
// Knöpfe: <button data-kragr-pdf="#report" data-kragr-pdf-name="…"> — Text und Ablauf setzt dieses Skript.
// Ablauf am Handy in zwei Tipps: 1. „PDF erstellen“ (rechnet einige Sekunden), 2. „PDF teilen“ — das Teilen-Menü braucht einen
// frischen Tipp, nach der Rechenzeit lässt Safari es sonst nicht mehr zu.
(function(){
  if(typeof document==='undefined') return;
  const TX={
    de:{make:'PDF erstellen', busy:'PDF wird erstellt …', share:'PDF teilen', save:'PDF speichern', again:'Erneut erstellen', fail:'PDF konnte nicht erstellt werden.'},
    en:{make:'Create PDF', busy:'Creating PDF …', share:'Share PDF', save:'Save PDF', again:'Create again', fail:'The PDF could not be created.'},
    fr:{make:'Créer le PDF', busy:'Création du PDF …', share:'Partager le PDF', save:'Enregistrer le PDF', again:'Recréer', fail:'Le PDF n’a pas pu être créé.'},
    es:{make:'Crear PDF', busy:'Creando PDF …', share:'Compartir PDF', save:'Guardar PDF', again:'Volver a crear', fail:'No se pudo crear el PDF.'}};
  const lang=()=>((document.documentElement.lang||'de').slice(0,2));
  const T=k=>(TX[lang()]||TX.de)[k];
  const base=(()=>{ const s=document.currentScript && document.currentScript.src; return s ? s.replace(/pdf\.js(\?.*)?$/,'') : 'k5/'; })();
  const load=src=>new Promise((ok,no)=>{ const s=document.createElement('script'); s.src=base+src; s.onload=ok; s.onerror=()=>no(new Error('load '+src)); document.head.appendChild(s); });
  let libs=null;
  const needLibs=()=> libs || (libs=Promise.all([ window.html2canvas?0:load('html2canvas.min.js'), (window.jspdf&&window.jspdf.jsPDF)?0:load('jspdf.umd.min.js') ]).catch(e=>{ libs=null; throw e; }));
  const canShareFiles=()=>{ try{ return !!(navigator.canShare && navigator.canShare({files:[new File(['x'],'x.pdf',{type:'application/pdf'})]})); }catch(e){ return false; } };

  // Seitenumbrüche: an Unterkanten von Blöcken, nie mitten durch Zeilen, Bilder, Tabellenzeilen oder Schrittköpfe
  const ATOM='svg,img,canvas,tr,li,p,pre,h1,h2,h3,h4,.st-h,.rb-dia,.rb-h,.eq,.eq-l,.eq-r,.figure,figure,.rep-disc,.meta,.rb-note,.rw-figs';
  const HEAD='h1,h2,h3,h4,.rb-h,.rb-dia-t,.st-h';
  function breaks(el, pageH, nextH){
    const top=el.getBoundingClientRect().top, H=el.scrollHeight, atoms=[], cand=new Set([H]);
    el.querySelectorAll('*').forEach(e=>{ const r=e.getBoundingClientRect(); if(!r.height) return; const a=r.top-top, b=r.bottom-top;
      if(e.matches(ATOM) && r.height<pageH*0.9) atoms.push([a,b]); cand.add(Math.round(b)); cand.add(Math.round(a));
      // keine Überschrift allein am Seitenende: zwischen Überschrift und dem Anfang des folgenden Blocks wird nicht getrennt
      if(e.matches(HEAD)){ const n=e.nextElementSibling, q=n && n.getBoundingClientRect(); if(q && q.height) atoms.push([a, q.top-top+3]); } });
    const ok=y=>!atoms.some(([a,b])=>y>a+1 && y<b-1), ys=[...cand].filter(y=>y>0 && y<=H && ok(y)).sort((a,b)=>a-b), out=[0];
    let cur=0;
    while(cur<H-1){ const ph=out.length>1 ? (nextH||pageH) : pageH, lim=cur+ph; if(lim>=H){ out.push(H); break; }
      let best=0; for(const y of ys){ if(y>cur+ph*0.35 && y<=lim) best=y; }
      cur = best || lim; out.push(cur); }
    return out;
  }

  // Druckansicht nachbilden: alle @media-print-Regeln der Seite gelten während der Aufnahme (Schriftfeld, zwei Spalten, keine Knöpfe)
  function printRules(){ const out=[];
    const walk=rules=>{ for(const r of rules){ if(r.type===4 && /\bprint\b/.test(r.media.mediaText) && !/\bscreen\b/.test(r.media.mediaText)) for(const x of r.cssRules) out.push(x.cssText); else if(r.type===4 && r.cssRules) walk(r.cssRules); } };
    for(const sh of document.styleSheets){ try{ walk(sh.cssRules); }catch(e){} }
    return out.join('\n'); }
  async function makePdf(el, name){
    await needLibs();
    if(document.fonts && document.fonts.ready) { try{ await document.fonts.ready; }catch(e){} }
    const W=760;                                     // Satzbreite in px (A4 mit 12 mm Rand)
    const body=document.body, old={ st:el.getAttribute('style')||'', sx:window.scrollX, sy:window.scrollY };
    const ps=document.createElement('style'); ps.setAttribute('data-kragr-pdf-print',''); ps.textContent=printRules(); document.head.appendChild(ps);
    body.classList.add('kragr-pdf');
    el.setAttribute('style', old.st+';position:absolute!important;left:0!important;top:0!important;width:'+W+'px!important;max-width:none!important;margin:0!important;background:#fff!important;z-index:2147483000!important;box-sizing:border-box!important;padding:0!important');
    window.scrollTo(0,0);
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    // SVG vorab selbst in Bilder umrechnen und für die Aufnahme ersetzen: html2canvas zeichnet eingebettete SVG (nur viewBox,
    // Breite 100 %, Maße in ex) verschoben und abgeschnitten — Systemskizze ohne zweites Feld, das „r“ der Wortmarke versetzt
    const scale0=Math.min(2, Math.max(1.5, window.devicePixelRatio||1)), swaps=[];
    for(const v of [...el.querySelectorAll('svg')]){
      const r=v.getBoundingClientRect(); if(r.width<1 || r.height<1) continue;
      try{
        const c=v.cloneNode(true), cs=getComputedStyle(v);
        c.setAttribute('xmlns','http://www.w3.org/2000/svg'); c.setAttribute('width', r.width); c.setAttribute('height', r.height); c.removeAttribute('class');
        c.setAttribute('style', 'color:'+cs.color+';font-family:'+cs.fontFamily.replace(/"/g,"'")+';overflow:'+(cs.overflow==='visible'?'visible':'hidden'));
        const img=new Image(); img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(c));
        await (img.decode ? img.decode() : new Promise((ok,no)=>{ img.onload=ok; img.onerror=no; }));
        const cv=document.createElement('canvas'); cv.width=Math.max(1,Math.round(r.width*scale0*1.5)); cv.height=Math.max(1,Math.round(r.height*scale0*1.5));
        cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
        cv.style.cssText='width:'+r.width+'px;height:'+r.height+'px;display:'+(cs.display==='inline'?'inline-block':cs.display)+';vertical-align:'+cs.verticalAlign+';margin:'+cs.margin+';flex:none';
        v.replaceWith(cv); swaps.push([cv, v]);
      }catch(e){}
    }
    const unsvg=()=>swaps.forEach(([cv,v])=>{ try{ cv.replaceWith(v); }catch(e){} });
    try{
      const pdf=new window.jspdf.jsPDF({unit:'mm', format:'a4', compress:true}), M=12, cw=210-2*M, ch=297-2*M;
      const pageH=Math.floor(W*ch/cw), r=el.getBoundingClientRect(), x0=r.left+window.scrollX, y0=r.top+window.scrollY;
      const scale=Math.min(2, Math.max(1.5, window.devicePixelRatio||1));
      const shot=(y,h)=>window.html2canvas(el, {scale, backgroundColor:'#ffffff', x:x0, y:y0+y, width:W, height:h, scrollX:0, scrollY:0, windowWidth:document.documentElement.clientWidth, logging:false, useCORS:true});
      // Schriftfeld (Wortmarke, Position, Datum, Version) steht auf jeder Seite oben: einmal aufnehmen, ab Seite 2 wiederholen
      const sf=el.querySelector('.rb-sf'), GAP=14; let head=null, headH=0;
      if(sf){ const q=sf.getBoundingClientRect(), a=Math.max(0, Math.floor(q.top-r.top)-1), h=Math.ceil(q.height)+2;
        if(h>8 && h<pageH*0.3){ head=(await shot(a,h)).toDataURL('image/jpeg', 0.92); headH=h; } }
      // Fußzeile des Berichts wandert in die Fußzeile jeder Seite (links), rechts die Seitenzahl — sonst stünde sie allein auf der letzten Seite
      const ft=el.querySelector('.rb-foot'), foot=ft ? ((ft.firstElementChild||ft).textContent||'').replace(/\s+/g,' ').trim() : '';
      if(ft){ ft.setAttribute('data-kragr-pdf-off', ft.style.display||''); ft.style.display='none'; }
      const cuts=breaks(el, pageH, head ? pageH-headH-GAP : pageH);
      for(let i=0;i<cuts.length-1;i++){
        const h=cuts[i+1]-cuts[i]; if(h<2) continue;
        const cv=await shot(cuts[i], h), off=(i>0 && head) ? headH+GAP : 0;
        if(i>0) pdf.addPage();
        if(off) pdf.addImage(head, 'JPEG', M, M, cw, cw*headH/W, 'kragr-kopf', 'FAST');
        pdf.addImage(cv.toDataURL('image/jpeg', 0.9), 'JPEG', M, M+cw*off/W, cw, cw*h/W, undefined, 'FAST');
        pdf.setFontSize(8); pdf.setTextColor(120); pdf.text((i+1)+' / '+(cuts.length-1), 210-M, 297-5, {align:'right'});
        if(foot) pdf.text(foot, M, 297-5);
      }
      pdf.setProperties({title:name, creator:'kragr'});
      return new File([pdf.output('blob')], name.replace(/[\\/:*?"<>|]+/g,'-').trim()+'.pdf', {type:'application/pdf'});
    } finally {
      unsvg();
      el.querySelectorAll('[data-kragr-pdf-off]').forEach(e=>{ e.style.display=e.getAttribute('data-kragr-pdf-off'); e.removeAttribute('data-kragr-pdf-off'); if(!e.getAttribute('style')) e.removeAttribute('style'); });
      el.setAttribute('style', old.st); if(!old.st) el.removeAttribute('style');
      body.classList.remove('kragr-pdf'); ps.remove(); window.scrollTo(old.sx, old.sy);
    }
  }

  function download(file){
    const u=URL.createObjectURL(file), a=document.createElement('a'); a.href=u; a.download=file.name; a.rel='noopener';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(u), 60000);
  }

  // Zustand je Knopf: leer → erstellen; fertig → teilen/speichern
  function label(b){ const st=b._pdf||{}; b.textContent = st.busy ? T('busy') : st.file ? (canShareFiles()?T('share'):T('save')) : T('make'); b.disabled=!!st.busy; b.setAttribute('aria-busy', st.busy?'true':'false'); }
  async function click(b){
    const st=b._pdf||(b._pdf={});
    if(st.busy) return;
    const el=document.querySelector(b.getAttribute('data-kragr-pdf')); if(!el) return;
    if(st.file && el.innerHTML.length!==st.at) st.file=null;   // anderer Bericht geöffnet → neu erstellen
    if(st.file){   // zweiter Tipp: teilen bzw. speichern (frischer Tipp, daher vom Browser erlaubt)
      const f=st.file;
      if(canShareFiles()){ try{ await navigator.share({files:[f], title:f.name.replace(/\.pdf$/,'')}); }catch(e){ if(e && e.name!=='AbortError') download(f); } }
      else download(f);
      return; }
    const name=(b.getAttribute('data-kragr-pdf-name') || (typeof b.kragrPdfName==='function' && b.kragrPdfName()) || document.title || 'kragr').trim();
    st.busy=true; label(b);
    const ov=document.createElement('div'); ov.className='kragr-pdf-ov'; ov.textContent=T('busy'); document.body.appendChild(ov);   // deckt die Seite ab, solange die Druckansicht für die Aufnahme gilt
    try{ st.file=await makePdf(el, name); st.at=el.innerHTML.length;
      if(!canShareFiles()){ download(st.file); } }   // Rechner: gleich herunterladen
    catch(e){ st.file=null; try{ console.error(e); }catch(_){} alert(T('fail')); }
    finally{ ov.remove(); st.busy=false; label(b); }
  }
  function wire(root){ (root||document).querySelectorAll('[data-kragr-pdf]').forEach(b=>{ if(b._pdfWired) return; b._pdfWired=true; b._pdf={}; b.addEventListener('click', e=>{ e.preventDefault(); click(b); }); label(b); }); }
  // Neuer Bericht im selben Fenster → Knopf zurücksetzen
  window.kragrPdfReset=()=>document.querySelectorAll('[data-kragr-pdf]').forEach(b=>{ if(b._pdf && !b._pdf.busy){ b._pdf={}; label(b); } });
  window.kragrPdf=makePdf;
  const st=document.createElement('style');
  st.textContent='body.kragr-pdf,body.kragr-pdf *{-webkit-text-size-adjust:100%!important;text-size-adjust:100%!important}body.kragr-pdf{overflow:visible!important}body.kragr-pdf .eq-r{text-indent:0!important;padding-left:0!important}body.kragr-pdf .rb-sf{grid-template-columns:auto 1.6fr 1fr 1fr!important}body.kragr-pdf .rb-sf>div{border-bottom:none!important;border-right:1px solid #111!important}body.kragr-pdf .rb-sf>div:last-child{border-right:none!important}body.kragr-pdf .k5-scrim,body.kragr-pdf .k5-menu,body.kragr-pdf #k-bar,body.kragr-pdf .mob-status{visibility:hidden!important}'
    +'.kragr-pdf-ov{position:fixed!important;inset:0!important;display:flex!important;visibility:visible!important;align-items:center;justify-content:center;background:rgba(240,241,243,.97);color:#111114;font:600 15px Figtree,system-ui,sans-serif;z-index:2147483646!important}'
    +'@media print{[data-kragr-pdf]{display:none!important}}';
  (document.head||document.body).appendChild(st);
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', ()=>wire()); else wire();
  if(typeof MutationObserver!=='undefined') new MutationObserver(()=>document.querySelectorAll('[data-kragr-pdf]').forEach(b=>{ if(b._pdfWired) label(b); else wire(); })).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
})();
