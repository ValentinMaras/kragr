# Übersetzung von statiq·ref — Werkzeuge

Ablauf je Fach (Beispiel `stahlbeton`), im Ordner `statiq-tools/ref-i18n/`, Playwright nötig:

1. `python3 collect.py stahlbeton` — rendert alle Themen des Fachs auf Deutsch (Inline-Läufe aus `refUnits`) und sammelt auf Englisch die fehlenden Code-Texte (`tt`/`_L`, beim Durchschalten der Eingaben) → `col_stahlbeton.json`
2. `python3 chunk.py stahlbeton` — hängt neue deutsche Texte an `todo_stahlbeton.json` an (Indizes bleiben stabil) und schreibt Pakete `stahlbeton_cN.txt`
3. Übersetzen in `stahlbeton_eN.py` als `E = {Index: 'englischer Text'}` (HTML und `{}`-Platzhalter beibehalten; `{0}`, `{1}` zum Umstellen)
4. `python3 build_ref.py ../../ref.html` — schreibt `TTX.en` in ref.html (Navigation aus `ttx_ref.json` + alle `*_eN.py`, Dezimalpunkt automatisch)
5. `python3 audit_ref.py stahlbeton full` — sucht deutsche Reste auf Englisch, auch nach Eingaben
6. Fach in `REF_EN_DONE` (ref.html) eintragen; `test_ref_i18n.py` prüft dann alle eingetragenen Fächer

Texte, die aus Datentabellen in Vorlagen ohne `_L` eingesetzt werden, im Code mit `tt(…)` umschließen.

Stand ref v0.3.21: alle 10 Fächer fertig. Code-Texte, die mit Standardwerten nicht erscheinen (Fehlermeldungen, Zweige), stehen direkt in `ttx_ref.json`; `statiq-tests/test_ref_i18n_code.py` meldet jeden `tt()`-/`_L`-Text ohne Übersetzung.
