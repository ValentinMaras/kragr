# Ansichtsfenster für die Querschnittskizze (size v0.7.19): Lupe oder Antippen der Skizze öffnet ein Fenster; zwei Finger zoomen
# (Mittelpunkt bleibt unter den Fingern), ein Finger verschiebt, Doppeltippen zoomt, Mausrad zoomt, Zurücksetzen, Esc/✕ schließt.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
EV="""([type, id, x, y])=>{ const st=document.querySelector('#zv .zv-stage'), r=st.getBoundingClientRect();
  st.dispatchEvent(new PointerEvent(type, {pointerId:id, pointerType:'touch', clientX:r.left+x, clientY:r.top+y, bubbles:true, isPrimary:id===1})); }"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        ctx=await br.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
        pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        check('Lupe an der Abbildung', await pg.evaluate("!!document.querySelector('#fig').closest('.card').querySelector('.zv-open')"))
        await pg.tap('#fig svg'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[document.getElementById('zv').classList.contains('open'), !!document.querySelector('#zv .zv-in svg'), document.querySelector('#zv .zv-t').textContent, document.querySelector('#zv .zv-hint').textContent, document.body.classList.contains('zv-lock')]")
        check('Antippen der Skizze öffnet das Fenster mit Kopie, Titel und Hinweis', r[0] and r[1] and r[2]=='Querschnitt' and 'Zwei Finger' in r[3] and r[4], r)
        st=await pg.evaluate("zoomView.state()"); check('startet bei 100 %', st['s']==1, st)
        # zwei Finger auseinander: 100 → 300 px Abstand, Mitte (180, 300)
        await pg.evaluate(EV, ['pointerdown',1,130,300]); await pg.evaluate(EV, ['pointerdown',2,230,300])
        await pg.evaluate(EV, ['pointermove',1,30,300]); await pg.evaluate(EV, ['pointermove',2,330,300])
        st=await pg.evaluate("zoomView.state()")
        check('zwei Finger: Zoom 300 %, Punkt unter der Mitte bleibt stehen', abs(st['s']-3)<1e-6 and abs((180-st['tx'])/st['s']-180)<0.5 and abs((300-st['ty'])/st['s']-300)<0.5, st)
        await pg.evaluate(EV, ['pointerup',2,330,300]); await pg.evaluate(EV, ['pointerup',1,30,300])
        # ein Finger verschiebt
        a=await pg.evaluate("zoomView.state()")
        await pg.evaluate(EV, ['pointerdown',1,200,300]); await pg.evaluate(EV, ['pointermove',1,240,340]); await pg.evaluate(EV, ['pointerup',1,240,340])
        b=await pg.evaluate("zoomView.state()")
        check('ein Finger verschiebt den Ausschnitt (40 px, 40 px)', abs(b['tx']-a['tx']-40)<0.5 and abs(b['ty']-a['ty']-40)<0.5 and b['s']==a['s'], (a,b))
        # nicht über den Rand hinaus
        await pg.evaluate(EV, ['pointerdown',1,200,300]); await pg.evaluate(EV, ['pointermove',1,2000,2000]); await pg.evaluate(EV, ['pointerup',1,2000,2000])
        c=await pg.evaluate("zoomView.state()")
        check('Verschieben endet am Rand (Inhalt bleibt im Fenster)', c['tx']<=40 and c['ty']<=40, c)
        # Zoom-Grenzen
        await pg.evaluate("zoomView.zoomAt(100, 100, 100)"); s1=(await pg.evaluate("zoomView.state()"))['s']
        await pg.evaluate("zoomView.zoomAt(0.001, 100, 100)"); s2=(await pg.evaluate("zoomView.state()"))
        check('Zoom zwischen 100 % und 800 %, bei 100 % zentriert', s1==8 and s2['s']==1 and s2['tx']==0 and s2['ty']==0, (s1, s2))
        # Doppeltippen
        await pg.evaluate(EV, ['pointerdown',1,150,200]); await pg.evaluate(EV, ['pointerup',1,150,200]); await pg.wait_for_timeout(80)
        await pg.evaluate(EV, ['pointerdown',1,150,200]); await pg.evaluate(EV, ['pointerup',1,150,200]); await pg.wait_for_timeout(350)
        d=await pg.evaluate("zoomView.state()")
        check('Doppeltippen zoomt auf 250 %', abs(d['s']-2.5)<1e-6, d)
        await pg.click('#zv .zv-r'); await pg.wait_for_timeout(350)
        check('Zurücksetzen: 100 %', (await pg.evaluate("zoomView.state()"))['s']==1)
        await pg.click('#zv .zv-x'); await pg.wait_for_timeout(200)
        check('✕ schließt, Seite wieder scrollbar', await pg.evaluate("!document.getElementById('zv').classList.contains('open') && !document.body.classList.contains('zv-lock')"))
        # Rechner: Mausrad und Esc, Stahl
        d=await br.new_page(viewport={'width':1280,'height':900}); d.on('pageerror', lambda e: errs.append(str(e)))
        await d.goto(B+'size.html'); await d.wait_for_timeout(900); await d.evaluate("setMat('stahl')"); await d.wait_for_timeout(300)
        await d.click('.zv-open'); await d.wait_for_timeout(400)
        t=await d.evaluate("[document.querySelector('#zv .zv-t').textContent, document.querySelector('#zv .zv-hint').textContent]")
        check('Stahl: Fenster „Profil“, Hinweis für die Maus', t[0]=='Profil' and 'Mausrad' in t[1], t)
        box=await d.evaluate("(()=>{ const r=document.querySelector('#zv .zv-stage').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; })()")
        await d.mouse.move(box[0], box[1]); await d.mouse.wheel(0, -400); await d.wait_for_timeout(150)
        check('Mausrad zoomt hinein', (await d.evaluate("zoomView.state()"))['s']>1.5)
        await d.keyboard.press('Escape'); await d.wait_for_timeout(150)
        check('Esc schließt', await d.evaluate("!document.getElementById('zv').classList.contains('open')"))
        for L,w in (('en','Two fingers'),('fr','Deux doigts'),('es','Dos dedos')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800)
            await pg.tap('.zv-open'); await pg.wait_for_timeout(300)
            h=await pg.evaluate("[document.querySelector('#zv .zv-hint').textContent, document.querySelector('#zv .zv-r').textContent]")
            check(f'{L}: Hinweis und Knopf übersetzt', h[0].startswith(w) and h[1]!='Zurücksetzen', h)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
