# Französisch und Spanisch (size v0.5.23, ref v0.3.22)

Quelle ist jeweils der deutsche Text (Schlüssel) mit der geprüften englischen Fassung als Hilfe.

- `extract.py` — sammelt aus size.html (I18N.de/en, TTX.en) und ref.html (TTX.en) alle Texte → `pool.json`, Pakete `cNN.json` ({id, de, en}), `idmap.json` (Paket-id → Schlüssel). Einträge mit DE = EN (Formeln, Eigennamen) stehen in `pool.json` unter `same`.
- `oNN.json` — Übersetzungen {id: {fr, es}} je Paket; `check.py NN` prüft Platzhalter, HTML-Tags, Anfangszeichen ! und §.
- `GLOSSAR.md` — verbindliche Begriffe (Eurocode-Terminologie NF EN / UNE-EN).
- Nachträge: `fix.json` (Paket-id → {fr, es}), `same_fix.json` (DE = EN, aber in FR/ES zu übersetzen), `extra_tri.json` (neue Schlüssel mit {en, fr, es}; EN zusätzlich in `ref-i18n/ttx_ref.json` bzw. `size-i18n/*.json` eintragen).
- `python3 build_fres.py ../..` — schreibt in size.html und ref.html den Block `/*FRES*/Object.assign(TTX,{fr:…,es:…})/*/FRES*/` (size zusätzlich TTR.fr/es) sowie I18N.fr/es (size; ref-Oberfläche steht direkt im HTML).

Reihenfolge bei neuen Texten: erst EN bauen (`size-i18n/build.py` bzw. `ref-i18n/build_ref.py`), dann `build_fres.py`. Neue deutsche Texte ohne FR/ES-Eintrag bleiben deutsch; `statiq-tests/test_fres.py` meldet sie.
- `overlap.py` — prüft alle Abbildungen in size und ref auf Beschriftungen, die in EN/FR/ES über den Rand ragen oder sich überdecken (Vergleich mit Deutsch); Laufzeit etwa 6 Minuten.
