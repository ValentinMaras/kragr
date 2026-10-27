# Fügt die gemeinsame Design-Schicht (k5.css, k5.js, k5-pages.js; in calc und size zusätzlich blatt.css/blatt.js „Als Rechenblatt speichern“; dazu GSAP 3.13 selbst gehostet als k5/gsap.min.js) identisch in alle App-Seiten ein.
# Aufruf: python3 k5/inject.py   (aus dem Hauptordner; ersetzt vorhandene data-k5-Blöcke)
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
if not os.path.exists(os.path.join(ROOT, 'calc.html')): ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
css = open(os.path.join(HERE, 'k5.css'), encoding='utf-8').read().rstrip()
js = open(os.path.join(HERE, 'k5.js'), encoding='utf-8').read().rstrip()
pages = open(os.path.join(HERE, 'k5-pages.js'), encoding='utf-8').read().rstrip()
STYLE = '<style data-k5>\n' + css + '\n</style>\n'
GSAP = '<script data-k5-gsap src="k5/gsap.min.js" defer></script>\n'
SCRIPT = '<script data-k5>\n' + pages + '\n' + js + '\n</script>\n'
blatt_css = open(os.path.join(HERE, 'blatt.css'), encoding='utf-8').read().rstrip()
blatt_js = open(os.path.join(HERE, 'blatt.js'), encoding='utf-8').read().rstrip()
BLATT = '<style data-blatt>\n' + blatt_css + '\n</style>\n<script data-blatt>\n' + blatt_js + '\n</script>\n'
for f in ['index.html', 'calc.html', 'size.html', 'ref.html', 'projekt.html', 'rechtliches.html']:
    p = os.path.join(ROOT, f); s = open(p, encoding='utf-8').read()
    s = re.sub(r'<style data-k5>.*?</style>\n', '', s, flags=re.S)
    s = re.sub(r'<script data-k5>.*?</script>\n', '', s, flags=re.S)
    s = re.sub(r'<script data-k5-gsap[^>]*></script>\n', '', s)
    s = re.sub(r'<style data-blatt>.*?</style>\n<script data-blatt>.*?</script>\n', '', s, flags=re.S)
    # Skript im head (startet bei DOMContentLoaded): so bleibt das letzte <script> der Seite deren Hauptskript (Prüfstände lesen es aus)
    i = s.index('</head>'); s = s[:i] + STYLE + GSAP + SCRIPT + (BLATT if f in ('calc.html', 'size.html') else '') + s[i:]
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', f)
