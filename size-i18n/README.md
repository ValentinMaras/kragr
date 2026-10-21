# size — englisches Wörterbuch ergänzen

`TTX.en` in `size.html` wird aus mehreren Quellen zusammengesetzt (`build.py`).
Für Paket A (v0.5.20), B (v0.5.21) und C (v0.5.22) liegen hier die Ergänzungen:

- `pa.json`, `pb.json`, `pc.json` — deutscher Schlüssel → englischer Text (bei `_L` mit `{}` an den Stellen der Werte)
- `pa_drop.json` — Schlüssel, die nicht mehr im Code vorkommen und entfernt werden

Neue Texte: im Code mit `tt('…')` bzw. ``_L`… ${x} …` `` schreiben, Eintrag in `pa.json` ergänzen,
`build.py size.html` ausführen, danach `test_size_i18n.py` und `test_size_paketA.py`.
