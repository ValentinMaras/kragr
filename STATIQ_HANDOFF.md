# Muly (vormals Statiq) — Übergabe für neuen Chat (calc v0.8.24 · ref v0.3.32 · size v0.5.41 · projekt v0.1.4 · rechtliches v0.1.3 · Startseite)

## Dateien
- `index.html` — Startseite der Suite (Module calc, size, ref)
- `calc.html` — Schnittgrößen-App (Muly·calc v0.8.24, DE/EN/FR/ES)
- `projekt.html` — „Meine Projekte“: Positionsliste über calc und size (Muly·projekt v0.1.4, Test von Variante C)
- `ref.html` — Nachschlagewerk (Muly·ref v0.3.32, vollständig auf Englisch, Französisch und Spanisch)
- `size.html` — Bemessung (Muly·size v0.5.41, Beta: DE/EN/FR/ES, Pakete A–C mit 27 neuen Nachweisen, Abhilfe bei nicht erfüllten Nachweisen, vollständig auf Englisch, Bauphysik neu, dazu Wasserbau, Mauerwerk und Grundbau; Stahlbeton inkl. Stützen und Durchstanzen, Stahl inkl. Anschlüsse, Schweißnähte und Stützenfuß, Holz inkl. Verbindungen)
- `rechtliches.html` — Impressum (Platzhalter in eckigen Klammern), Haftung, Normen und Quellen, Datenschutz, Lizenzen; DE/EN/FR/ES (Muly·rechtliches v0.1.3)
- `manifest.json`, `sw.js`, `icons/` — Installierbare Web-App (PWA): Manifest, Service Worker für Offline-Betrieb, App-Symbole (192, 512, maskable 512, Apple 180, Favicon 32)
- `fonts/` — Inter, DM Sans, DM Mono, Bebas Neue als woff2 mit `fonts.css` und OFL-Lizenzen (muss neben den HTML-Dateien liegen)
- `statiq-tests/` — alle Tests, `python3 statiq-tests/run_all.py`

**Versionierung (Wunsch von Valentin):** in kleinen Schritten weiterzählen (0.8.1 → 0.8.2 …).
Einen Sprung auf die nächste Nebenversion (0.9) gibt es nur bei größeren neuen Funktionen (neues Tragsystem, neues Modul). Nicht zu schnell Richtung 1.0.
**Wichtig (Valentin, size 0.5.5):** v1.0 ist die finale Version. Neue Inhalte, auch ganze neue Bereiche, zählen nur die letzte Stelle hoch (0.5.5 → 0.5.6 …). Die mittlere Stelle nur nach Absprache. size wurde deshalb von 0.9.1 auf 0.5.5 zurückgesetzt.
Versionsnummer steht in `STATIQ_VERSION` und an 8 Stellen im HTML (Kopfzeile, Fußnoten).

---

## Statiq·size v0.4.0 — Druckbewehrung, Zugkraftdeckung, Stahlbetonstütze

- **Druckbewehrung** (nur Typ Balken/Rechteck): bei μ > μ_lim wird der Beton bis ξ_lim = 0,45 ausgenutzt (M_Rd,lim), das Restmoment ΔM über A_s2 (σ_s2 aus ε_s2 = 3,5‰·(x−d2)/x) und zusätzliches A_s1 mit Hebel d − d2. Neue Felder `in-n2`/`in-ds2` („Feld oben“, Klasse `dz-only`), Automatik über `topDruck()`. `res.DZ`, Abbildung zeigt F_s2. Bei Platte/Unterzug weiterhin Hinweis „Querschnitt vergrößern“.
- **Zugkraftdeckung und Staffelung** (Info-Zeile `zkd`): nur Balken/Unterzug, Einfeldträger (K = 1,0, kein Stützmoment), Gleichlast, ohne Druckbewehrung. Versatzmaß a_l = z·cot θ/2, die Hälfte der Stäbe (mind. 2 durchlaufend) endet bei x_E − l_bd (l_bd mit σ_sd = f_yd). Zugkraftdeckungsbild als SVG im Rechenschritt.
- **Stahlbetonstütze** (Typ `stuetze`, eigener Eingabeblock `#beton-stuetze`, Felder `su-*`): Modellstützenverfahren mit Nennkrümmung (5.8.8): λ_lim nach NA (25 bzw. 16/√n), M_0e = max(0,6·M02 + 0,4·M01; 0,4·M02), e_i = θ_i·l0/2 (α_h = 2/√l ≤ 1), e2 = K_r·K_φ·ε_yd/(0,45·d)·l0²/10, M_Ed ≥ M02 + N·e_i und ≥ N·max(h/30; 20 mm). Querschnitt: Dehnungsebenen-Integration (`stuetzeQS`, Parabel-Rechteck, B500 bilinear, symmetrische Bewehrung in zwei Lagen), A_s,tot,erf per Bisektion mit K_r(A_s). Interaktionsdiagramm (`figInteraktion`), Ansicht des Ersatzstabs mit Knickfigur (`figStuetze`). Bewehrungsregeln NA 9.5.2/9.5.3. Bericht `buildReportStuetze`.
- Tests: `test_size_beton2.py` (17, Sollwerte unabhängig in Python: Streifenmodell für M_Rd(N), Bisektion für A_s,erf, numerischer Endpunkt E).
- Offen in size/Stahlbeton: schiefe Biegung bei Stützen, Querkraft Stütze, Zugkraftdeckung für Durchlaufträger/Einzellasten (Durchstanzen erledigt in v0.6.0).

## Statiq·size v0.3.1 — Kräfte in den Abbildungen, kleinschrittige Nachweise

- **Rechenschritte:** Jede Zeile in `steps`, die mit `H('…')` (= `'§…'`) beginnt, ist eine nummerierte Schrittüberschrift in Worten (was und warum). Die folgenden Zeilen sind die Formeln mit Zahlen. `stepsHtml(S)` rendert das, auch im Bericht. Zusammengefasste „ · “-Zeilen wurden in einzelne Zeilen getrennt. Für alle Module (Beton, Stahl, Anschluss, Holz).
- **Abbildungen mit Kräften:** orange = Einwirkungen (`C_EW`), blau = innere Kräfte (`C_IN`). Helfer: `svgArrow` (auch Doppelpfeil = Momentenvektor), `svgPunkt` (⊙ Zug / ⊗ Druck senkrecht zur Ebene), `svgBogen` (Drehpfeil), `figLegend` (HTML-Legende unter dem SVG mit Werten).
  - Stahlbeton: Querschnitt mit Druckzone und Nulllinie, daneben „Ansicht am Schnitt“ mit M (Drehpfeil, Zug unten), V, F_cd, F_sd und z. Eigener Maßstab für die Ansicht (dünne Platten). `nachweise` liefert dazu `BI = {x, z, Fc}`.
  - Stahl: M_y/M_z als Momentenvektoren, V_z, N (⊙/⊗), Torsion als Drehpfeil, F_Ed auf dem Obergurt. `figProfil(P, K, I)`.
  - Anschluss: Kraft je Schraube als Pfeil, N als ⊙. Holz: M_y, V_z, N, Auflagerkraft. `figHolz(I, h)`.
- Tests mit Textabgleich angepasst (Stütze A_s,erf, w_k Stütze, χ_LT,mod, k_F, F_w,Rd).

## Statiq·size v0.3.0 — Stahl erweitert, Anschlüsse, Holz
Nebenversion erhöht (neuer Werkstoff Holz). Werkstoffumschalter Stahlbeton | Stahl | Holz; im Stahlteil Unterumschalter Träger/Stütze | Anschluss (`STMODE`). Info-Zeilen (`info:true`) erscheinen ohne Ausnutzung und zählen nicht zur größten Ausnutzung.
### Stahlträger
- **Klasse 4** (`effektiv`, EN 1993-1-5, 4.4): A_eff für reinen Druck (Steg ψ = 1, Gurte k_σ = 0,43), W_eff,y für reine Biegung iterativ (ψ, k_σ nach Tab. 4.1, Loch zwischen b_e1 und b_c − b_e2, Schwerpunktverschiebung); Querschnitt nach 6.44 (e_N = 0), Stabilität mit A_eff/W_eff und λ̄·√(A_eff/A). Geprüft gegen unabhängige Gitter-Integration (synthetisches Profil h/t_w = 160): Abweichung < 0,3 %
- **Biegung um z**: W_pl,z/W_el,z, Querschnitt (6.41) mit α = 2, β = 5n ≥ 1, M_N,z; Klasse 3/4 elastisch; Stabilität mit k_zz, k_yz (Anhang B), C_mz = C_my angenommen
- **Torsion** (`torsion`): gabelgelagerter Einfeldträger, Einzeltorsionsmoment in Feldmitte oder Streckentorsion, geschlossene Lösung (T_t, T_w, Bimoment B); Spannungen σ_w, τ_t, τ_w; elastischer Nachweis. Gegen Differenzenverfahren der Torsions-DGL geprüft (B, T_t identisch auf 3 Stellen)
- **Lasteinleitung** (`lasteinleitung`, EN 1993-1-5, 6): Typ a (Feld, k_F = 6) und Typ c (Trägerende, k_F = 2 + 6(s_s + c)/h_w ≤ 6, l_y = min(6.10, 6.11, 6.12)), m₂ abhängig von λ̄_F, Interaktion η₂ + 0,8η₁ ≤ 1,4
### Anschlüsse (EN 1993-1-8)
- Schrauben M12–M30, 4.6/5.6/8.8/10.9, Schraubenbild n₁ × n₂, ein-/zweischnittig, Gewinde/Schaft in der Scherfuge, d₀ normales Lochspiel
- Rand-/Lochabstände (Tab. 3.3), Abscheren, Lochleibung je Schraubenposition (End-/Randschrauben), Gruppenregel 3.7, Zug und Interaktion (Tab. 3.4), Kehlnaht vereinfachtes Verfahren mit β_w, Mindestdicke √t_max − 0,5 und Mindestlänge
### Holz (EC5 mit NA)
- Vollholz C14–C50, BSH GL20h–GL32c (Tabellen aus ref), k_mod (NKL, KLED), γ_M = 1,3, k_h
- Biegung, Schub (k_cr = 2,0/f_v,k bzw. 2,5/f_v,k), Auflagerpressung (l + 30 mm, k_c,90 1,5/1,75), Kippen (l_ef nach EN Tab. 6.1 mit +2h/−0,5h, σ_m,crit = 0,78·b²·E_0,05/(h·l_ef), k_crit), Knicken mit Biegung (6.23/6.24, β_c 0,2/0,1, k_m = 0,7) und mit Kippen (6.35), Durchbiegung w_inst, w_fin, w_net,fin mit k_def 0,6/0,8/2,0
- automatische Höhe (Vollholz 100–280 mm, BSH ab 120 mm in 40-mm-Schritten)
- Quellen: KIT-Zusammenfassung Holzbau, Leporello FH Bielefeld (k_cr, k_c,90, k_def, Grenzwerte)
### Tests
- `test_size_import.py` (14): calc → size für alle vier Systeme und alle Baustoffe, Hinweise
- `test_calc_cont.py` (11): Durchlaufträger mit Einspannung, Kragarmen, Gerberträger, EI je Feld, Einzelmomenten, Mechanismus
- `test_size_beton2.py` (17): Druckbewehrung, Staffelung, Stütze (λ, e2, M_Rd(N), A_s,erf, Kriechen, gedrungen, Bericht)
- `test_size_ext.py` (19): Torsion gegen Differenzenverfahren, W_eff gegen Gitter-Integration, A_eff, (6.41), Lasteinleitung Typ c, Schrauben 2×2 mit Zug, Abstände, Kehlnaht, Kippen BSH, Knicken C24, automatische Holzhöhe, Positionen und Berichte
- **Nicht online bestätigt:** l_y-Formeln 6.11/6.12 für Typ c (aus Sekundärquelle, teils unleserlich), l_ef-Tabelle 6.1 (NA erlaubt genaueres Verfahren), d₀ für M12 (+1 mm)
- Offen: V_y, Schubbeulen, Steifen, Torsion + BDK, Blockversagen/Nettoquerschnitt, Momentenanschlüsse, Holz: Querzug, Ausklinkungen, Verbindungsmittel, Brand, Schwingungen

## Statiq·size v0.2.0 — Stahlteil (EC3)
Nebenversion erhöht, weil ein neuer Werkstoff dazukommt. Umschalter „Stahlbeton | Stahl“ über den Eingaben (`MAT`, `setMat`, `showMat`); gemeinsame Ausgabe über `renderOut`, Bericht über `buildReportStahl`/`reportChecks`.
- Profile: 52 Walzprofile IPE/HEA/HEB (Tabelle aus ref kopiert), Stahlsorten S235–S460; `profil()` ergänzt I_T (Herstellerformel mit Ausrundung, Abweichung zu Tabellenwerten ≤ 3 %), I_w = t_f·b³·(h − t_f)²/24 (exakt wie Tabellen), A_vz mit η = 1,0
- **Querschnittsklassifizierung** (`klasse`, Tab. 5.2): Gurt 9ε/10ε/14ε, Steg unter N + M über α (plastisch) und ψ (elastisch); Klasse 4 wird erkannt und als „nicht enthalten“ gemeldet
- **Querschnitt**: N_pl, V_pl,z, M_c (W_pl bzw. W_el), Abminderung bei V > 0,5·V_pl (6.30), M_N,y,Rd (6.36), Klasse 3 elastisch, Schubbeulen-Grenze 72ε
- **Biegeknicken**: Knicklinien nach h/b (S460 a0/a), γ_M1 = 1,1; Knicklänge z aus dem Abstand der seitlichen Halterungen
- **Biegedrillknicken**: M_cr mit C₁, C₂ nach NCCI SN003 (Gleichlast 1,127/0,454, Einzellast 1,348/0,630, linear aus Tabelle), z_g aus Lastangriff; χ_LT nach 6.3.2.3 (λ_LT,0 = 0,4, β = 0,75, Linie b/c nach h/b) mit f und k_c; L_LT = 0 → gehalten
- **Interaktion** (6.3.3, Anhang B): k_yy, k_zy nach Tab. B.2 (torsionsweich) bzw. B.1 (gehalten), C_m nach Momentenverlauf
- **Durchbiegung** aus M_y,k mit c = 5/48, 1/12, 1/8 bzw. (1 + ψ)/16
- Automatische Profilwahl: leichtestes Profil der Reihe mit allen Nachweisen
- Positionen speichern auch Stahl; Neuladen bleibt im gewählten Werkstoff
- Tests: `test_size_stahl.py` (18), Sollwerte unabhängig in Python (M_cr, χ_LT, χ, k_yy/k_zy, Klassifizierung mit N, Querkraftabminderung, Auto-Profil)
- Geprüft online: γ_M1 = 1,1 und λ_LT,0 ≤ 0,4 im NA (LBV Brandenburg), C₁/C₂ (NCCI SN003), I_w/I_T gegen Profiltabellen
- Offen: Klasse 4, schiefe Biegung, Torsion, Stegkrüppeln, Anschlüsse, Holz

## Statiq·size v0.1.2 — Optimierung
- **Rissbreite über der Stütze** (`riss_st`): neue Eingabe |M_qp,Stütze|, Zustand II mit Druckzone b bzw. b_w, ρ_p,eff mit b_eff,Stütze beim Unterzug; obere Bewehrung wird automatisch auch nach Rissbreite gewählt
- **Indirekte Lagerung** (Unterzug auf Unterzug): l_bd,ind = max(α₁·l_b,rqd; 0,3·α₁·l_b,rqd; 10·Ø; 100 mm) ohne ⅔-Faktor, verfügbare Länge = Breite des stützenden Trägers − c_nom, Aufhängebewehrung A_s,h = V_Ed/f_yd
- **Positionen**: speichern (Bezeichnung = Name, gleicher Name überschreibt), laden, löschen mit Bestätigung ohne Pop-up; `localStorage` `statiq-size-positionen`
- Unterzug: Feldart setzt K für l/d automatisch (Einfeld 1,0 / Endfeld 1,3 / Innenfeld 1,5)
- Mobil: Ergebnis-Kurzinfo unter der Kopfzeile, Tipp springt zum Ergebnis
- Rechenzeit einer Auswertung mit automatischer Bewehrungswahl (Unterzug mit Stütze) ≈ 60 ms
- Tests: `test_size.py` jetzt 37

## Statiq·size v0.1.1 — Unterzug als Plattenbalken, Stütze, Endauflager
Valentins Frage: „Unterzug oder Plattenbalken?“ → Unterzug ist das Bauteil, Plattenbalken das Rechenmodell im Feld (Platte als Druckgurt); über der Stütze liegt die Platte in der Zugzone → Rechteck mit b_w.
- Neuer Bauteiltyp **Unterzug**: Eingaben h_f, b₁, b₂, Feldart (l₀ = 1,0/0,85/0,70·l); `beffCalc` nach 5.3.2.1
- Feldbiegung für beliebige Breite b(y) über Faserintegration (`biegeQS`, Parabel-Rechteck, gleiche Dehnungszustände wie `biegeState`, mit Memo); erkennt Nulllinie in Platte/Steg. Unabhängig in Python geprüft (Suche über x): Abweichung < 0,01 %
- A_s,min aus Rissmoment des T-Querschnitts (`tSection`)
- **Stützmoment** (alle Bauteiltypen, Betrag): Rechteck mit b bzw. b_w, obere Bewehrung; Unterzug: über b_eff,Stütze (l₀ ≈ 0,3·l bei gleichen Stützweiten) verteilt; Hinweis ¼ Feldbewehrung am Zwischenauflager
- **Gurtanschluss** (6.2.4): F_ca aus Faserintegration, Δx = l₀/4, ΔF_d = 0,75·F_ca (Gleichlast), cot θ_f = 1,2, v_Rd,max = ν₁·f_cd·sin θ_f·cos θ_f, Grenze 0,4·f_ctd, a_sf
- **Endauflager** (alle Typen, abschaltbar): F_Ed = V_Ed·cot θ/2 (Balken) bzw. V_Ed·d/z (Platte, a_l = d), l_bd,dir = max(⅔·α₁·l_b,rqd; 0,3·α₁·l_b,rqd; 6,7·Ø; 100 mm), vorhandene Länge t − c_nom
- Rissbreite Zustand II mit b(y) (`rissbreiteQS`), ρ_p,eff mit b_w; unabhängig geprüft
- Bügelwahl: erst Abstände ≥ 15 cm mit allen Ø, dann engere
- Tests: `test_size.py` jetzt 30
- **Nicht online bestätigt:** ⅔-Faktor und 6,7·Ø bei direkter Lagerung (aus Sekundärquelle), Faktor 0,75 für ΔF_d (Annahme Gleichlast)
- Offen: Zugkraftdeckung/Staffelung, Druckbewehrung, Mehrsprachigkeit

## Statiq·size v0.1.0 — erstes Modul: Stahlbeton (Beta)
Entscheidungen von Valentin: Start mit Stahlbeton; Schnittgrößen **nur von Hand** (keine Übernahme aus calc); Ergebnis = Nachweise **und** Druckbericht.
- Eine Seite `size.html`, links Eingaben, rechts Ergebnis (Übersicht mit Ausnutzungsbalken), Querschnittsbild, Nachweise mit allen Zwischenschritten
- Bauteile: Rechteckbalken (zweischnittige Bügel, Längsbewehrung einlagig) und Platte (1 m Streifen, ohne Querkraftbewehrung)
- Nachweise (`nachweise(I, R)` → Liste `C` mit `eta`, `ok`, `steps`, `note`): Betondeckung/Nutzhöhe/Mindestfestigkeit · Biegung (ω-Verfahren, A_s,min, 0,08·A_c) · Stababstände (lichter Abstand, s_max Platte) · Querkraft (V_Rd,c, V_Rd,max, a_sw, ρ_w,min, s_max nach Tab. NA.9.1) · Rissbreite (direkt, optional Mindestbewehrung für Zwang mit f_ct,eff ≥ 3,0) · Biegeschlankheit
- Automatische Bewehrungswahl (`autoBewehrung`, `stirrups`): kleinste Fläche, die Biegung, Stababstände und Rissbreite erfüllt; Bügel kleinster Ø, größter Abstand
- Bericht: `buildReport()` aus dem letzten Ergebnis, eigene Druckansicht (`@media print`), „Drucken / als PDF speichern“
- Eingaben werden im Browser gemerkt (`localStorage`, Schlüssel `statiq-size-v1`, mit try/catch)
- Normdaten und Formeln sind aus ref **kopiert** (BETON, EXPO, deckung, Parabel-Rechteck, querkraft, rissbreite) — bei Änderungen beide Dateien anpassen (später gemeinsames Modul)
- Startseite: size-Karte verlinkt, Badge „BETA“, neue Beschreibung und Tags in 4 Sprachen; Fußzeile mit size-Version
- Tests: `test_size.py` (20, Playwright), Sollwerte unabhängig in Python (ω numerisch integriert, Querkraft, Rissbreite Zustand II)
- **Noch nicht enthalten:** Druckbewehrung, Plattenbalken, Stützmomente/Durchlaufträger (nur Feld), Verankerung und Zugkraftdeckung, Torsion, Brandschutz, Speichern mehrerer Positionen, Mehrsprachigkeit (nur Deutsch), Stahl und Holz

## Statiq·ref v0.3.1 — Stahlbeton erweitert, ref auf der Startseite freigeschaltet
- **Startseite:** ref-Karte ist verlinkt (LIVE, `badge-live-2`) und steht vor size; Rückfall-Animation für `.module-card`; Tag „Concrete EC2“ auch im statischen HTML; Untertitel um Eurocode 7 ergänzt
- **Druckbewehrung** im Biegerechner (`biegeDruck`): ξ = 0,45 fest, σ_s2 aus ε_s2, Prüfung 0,08·A_c. Kontrolle von Hand: 30/60, C30/37, 600 kNm → A_s1 30,09 / A_s2 6,59 cm²
- **Plattenbalken** (`beffCalc`, `updatePlattenbalken`): b_eff nach 5.3.2.1, Nulllinie in Platte → ω-Verfahren mit b_eff, sonst Näherung z = d − h_f/2 mit σ_cd-Kontrolle und Hinweis bei b_eff/b_w < 5
- **Durchstanzen** (`durchstanzen`): NA-Werte geprüft (C_Rd,c = 0,18/γ_c, Abminderung u₀/d < 4 bei Innenstützen, β 1,10/1,40/1,50/1,35/1,20, v_Rd,max = 1,4·v_Rd,c, ρ_l ≤ min(0,02; 0,5 f_cd/f_yd)); Rand- und Eckstützen mit verkürztem u₁
- **Stützen** (neues Kapitel): Schlankheit (λ_lim nach NA geprüft), Nennkrümmung (K₁, e_i, e₀ ≥ h/30 bzw. 20 mm), Querschnittsbemessung symmetrisch bewehrt über Dehnungsebenen (`ebene`, `querschnittNM`, `stuetzeAs`). Gegen eine unabhängige Python-Implementierung geprüft (3 Fälle, Abweichung < 0,1 %); konstruktive Regeln 9.5
- **Rissbreite:** w_max Tab. 7.1DE, Mindestbewehrung, Grenzdurchmesser Ø* = w_k·3,48·10⁶/σ_s² (Tab. 7.2DE), direkte Berechnung mit s_r,max = Ø/(3,6·ρ_p,eff) nach NA; Rechner `rissbreite` (Zustand II linear-elastisch, von Hand nachgerechnet)
- **Nicht einzeln online bestätigt:** Tab. 7.1DE-Zeilen für XD/XS, Bügelabstände Stützen (12·Ø/300 mm, × 0,6), K₁-Formel, l₀-Werte Plattenbalken (aus EN-Bild 5.2)
- Tests: `test_ref.py` jetzt 67

## Statiq·ref v0.3.0 — Fach Stahlbeton, Sohlwiderstand
### Neues Fach Stahlbeton (EC2), 8 Themen
- Baustoffe: Beton Tab. 3.1 (`BETON`, gegen Formeln f_ctm = 0,3·f_ck^(2/3), E_cm = 22·(f_cm/10)^0,3 geprüft), f_cd mit α_cc = 0,85; Betonstahl B500A/B, f_yd, γ_c/γ_s
- Dauerhaftigkeit: Expositionsklassen XC/XD/XS (`EXPO`) mit c_min,dur, Δc_dur,γ, Δc_dev nach Tab. 4.4DE, Mindestfestigkeit; Rechner `updateDeckung`
- Biegung: ω-Tabelle wird live aus dem Parabel-Rechteck-Diagramm gerechnet (`biegeAusMu`, ε_s ≤ 25 ‰, horizontaler Stahlast). Unabhängig per numerischer Integration geprüft; stimmt mit Literaturtafeln überein (μ 0,10/0,20/0,25 → ω 0,1057/0,2263/0,2946). Rechner mit A_s,min aus Rissmoment und Stabvorschlag
- Querkraft: V_Rd,c (inkl. v_min, κ₁ zwischen d = 600 und 800 mm interpoliert), V_Rd,max, a_sw, ρ_w,min, z nach NA, Bügelabstände Tab. NA.9.1; Rechner `updateQuerkraft`
- Bewehrung: A_s-Tabellen (n Stäbe, je Meter), Plattenregeln; Verankerung f_bd/l_b,rqd-Tabelle und Rechner `updateVerankerung`
- Gebrauchstauglichkeit: Biegeschlankheit K·35 und K²·150/l, Rechner `updateSchlank`
- Abbildung `figBiegung` (Querschnitt, Dehnung, Spannungsblock)
### Sohlwiderstand (Grundbau › Flachgründungen)
- Tabellen DIN 1054 A 6.1, A 6.2 (nichtbindig) und A 6.5–A 6.8 (bindig) in `SOHL_NB`/`SOHL_B`, Voraussetzungen, Erhöhungen/Abminderungen, Rechner `sohlBerechne`/`updateSohl` mit Interpolation
- Werte = 1,4 × zul. σ der DIN 1054:2005. Geprüft gegen Baugrundgutachten (gemischtkörnig steif 210/250/310/350, tonig-schluffig steif 170/200/220/250; Regeln +20 % Rechteck, −10 %/m für b 2–5 m, +1,4 × Entlastung für d > 2 m) und Programmbeispiel (nichtbindig d = b = 1 m: 520; bindig steif Streifen 250 / Rechteck 300). **Halbfeste/feste Zeilen und Ton-Tabelle nicht einzeln online bestätigt.**
### Sonstiges
- `textTable` bricht lange Texte in hinteren Spalten automatisch um (Klasse `text-table`), statt waagerecht zu scrollen
- `deNum` rundet Halbwerte korrekt (1,575 → 1,58)
- Startseite: Tag „Stahlbeton EC2“ in allen vier Sprachen; `FAECHER_SOON` ist leer
- Tests: `test_ref.py` jetzt 55

## Statiq·ref v0.2.1 — Werte ergänzt und geprüft
- **Nutzlasten:** vollständige Tab. 6.1DE (22 Kategorien A1 … Z mit Beispielen), A2 ohne Q_k (vorher fälschlich 1,0), Fußnote A3 (−0,5 kN/m² für Weiterleitung), Kat. H (Q_k = 1,0) und F (3,5 kN/m² / 20 kN), Beispiel Trennwandzuschlag
- **ψ-Beiwerte:** „Sonstige Einwirkungen 0,8 / 0,7 / 0,5“ ergänzt, Erklärung ψ₀/ψ₁/ψ₂ mit Zahlenbeispiel
- **Kombinationen:** EQU-Beiwerte (1,10 / 0,90) ergänzt
- **Eigenlasten:** 22 Wichten (Datenarray `WICHTEN`), Putz/Estrich je cm, Ausbau-Pauschalwerte, neuer Rechner **Deckenaufbau** (`updateAufbau`, 4 Schichten)
- **Nägel:** Einschlagtiefe Abscheren nach NA vereinfacht (9d voll, 4d … 9d × t/9d, < 4d zählt nicht), Herausziehen nach EN 8.3.2(7) (glatt 8d/12d, Sondernagel 6d/8d mit Abminderungsfaktoren), Mindestholzdicke 8.3.1.2(6), neuer Rechner `updateNagel`
- **Bodenkennwerte:** Spalten E_s und k, Kies und Ton halbfest ergänzt, Lagerungsdichte/Konsistenz mit I_c
- **Grundbruch:** Teilsicherheitsbeiwerte DIN 1054 Tab. A 2.1/A 2.3 (BS-P/T/A)
- Quellen: Mauerwerksbau-Lehre (Tab. 6.1DE, Putzlasten), xlstatik (6.1DE/6.10DE), KIT-Zusammenfassung Holzbau (9d/4d), EN 1995-1-1 Text 8.3.2; Wichten aus EN 1991-1-1 Anhang A bzw. EN 338/EN 14080 (ρ_mean · g), Bodenwerte als Größenordnungen (Abgleich mit einem echten Baugrundgutachten)
- **Nicht online gegengeprüft:** Bodenkennwerte (nur Plausibilität), Kat. F Q_k, einige Wichten (Gussasphalt, Mineralwolle)
- Tests: `test_ref.py` jetzt 37 (+8: Deckenaufbau, Nagelrechner, 22 Nutzlastkategorien, ψ)

## Statiq·ref v0.2.0 — neue Fächer

Neue Nebenversion, weil fünf Fächer dazukommen (Versionsregel: 0.x-Sprung nur bei größeren neuen Funktionen).
45 Themen insgesamt (vorher 12). Reihenfolge auf der Startseite: Baustatik, Lastannahmen, Stahlbau, Holzbau, Grundbau, Mathematik; Stahlbeton (EC2) „in Vorbereitung“.

| Fach | Kapitel / Themen | Rechner, Abbildungen |
|---|---|---|
| **Baustatik** | Lager und Gelenke, Statische Bestimmtheit, Schnittgrößen/Vorzeichen · Balkentafeln (Einfeldträger, Kragarm, eingespannte Träger, Durchlaufträger) · Querschnittswerte + Steiner (Beispiel T-Querschnitt), Spannungen, Euler · Arbeitssatz, Koppeltafel (mit Beispiel 5qL⁴/384EI) | Rechteck-Rechner · SVG Lagersymbole |
| **Lastannahmen** | Kombinationen GZT/GZG (EC0), ψ-Beiwerte (NA) · Wichten, Nutzlasten (Auszug Tab. 6.1DE), Schnee (Zonen-Formeln NA, μ₁), Wind (vereinfachte q nach NA, c_pe,10 Wände) | Schnee- und Wind-Rechner |
| **Stahlbau** | Stahlsorten, Kennwerte, γM (NA) · Walzprofile IPE 80–600, HEA/HEB 100–500 (Filter) · Querschnittsklassen, Widerstände · Biegeknicken (χ, Knicklinien) | Knick-Rechner (Profil, Stahl, L_cr, Achse → N_b,Rd) · SVG I-Profil |
| **Grundbau** | Bodenkennwerte (Anhaltswerte, deutlich als solche gekennzeichnet), Setzungen · Erddruckbeiwerte + Verteilung · Sohldruck/Kernweiten, Grundbruch DIN 4017 (N-Tabelle), Gleiten | Erddruck-Rechner · SVG Stützwand |
| **Mathematik** | Trigonometrie, Flächen und Schwerpunkte · Ableitungen/Integrale, DGL der Biegelinie · Gleichungen/LGS, Einheiten (mit typischem Fehlerbeispiel) | SVG Dreieck |

### Geprüft / Quellen
- **Walzprofile:** aus Nennmaßen (h, b, t_w, t_f, r) mit Herstellerformeln berechnet; Abgleich mit veröffentlichten Werten für 14 Profile: max. 0,26 % Abweichung (Rundung). W_pl stichprobenartig geprüft
- **Wind:** vereinfachte Geschwindigkeitsdrücke gegen Herstellerunterlage (DIN 1055-4 = NA-Werte) bestätigt
- **Schnee:** Mindestwerte, Zone-2-Formel und +25 % für 1a/2a bestätigt; Zone 1 und 3 nach demselben Aufbau
- **Grundbruch:** N-Beiwerte gerechnet, stimmen mit DIN-4017-Tabellenwerten (φ = 30°: 18,4/30,1/10,0)
- **Nicht online prüfbar (Stichprobe gegen Norm empfohlen):** Nutzlasten-Tabelle (nur gängige Kategorien aufgenommen), ψ-Tabelle, Wichten, Bodenkennwerte (als Anhaltswerte gekennzeichnet)

### Navigation
- Logo „statiq“ führt jetzt wie in calc zur **Startseite** (`index.html`), Pfadleiste: statiq › ref › Fach › Kapitel › Thema
- Suche findet auch einzelne Profile („HEB 200“) und stellt die Profiltabelle direkt auf die Reihe

### Tests
`test_ref.py` jetzt 29 Prüfungen: u. a. alle 45 Themen, Rückweg zur Startseite, Schnee (Formel, Mindestwert, Zone 2a), Wind (Wert, Gültigkeitsgrenze 25 m), Erddruck, Biegeknicken (unabhängig nachgerechnet), Profilwerte gegen veröffentlichte Werte, Rechteck, Suche.

---

## Statiq·ref v0.1.1 (aus v0.1.0)

### Fachliche Korrekturen (gegen Norm/Sekundärquellen geprüft)
- **BSH (EN 14080):** f_c,90,g,k = 2,5 N/mm² für **alle** Klassen (vorher 2,7…3,3 bei GL26…GL32). GL26c E_0,mean/E_0,05 = 12,0/10,0 (vorher 11,3/9,4), GL28c 12,5/10,4 (vorher 12,3/10,2)
- **γM:** Tabelle war mit „NA Deutschland“ überschrieben, enthielt aber die EN-Empfehlungswerte (BSH 1,25, LVL/Holzwerkstoffe 1,20). Nach DIN EN 1995-1-1/NA gilt γM = 1,30 für Holz, Holzwerkstoffe und Verbindungen. Jetzt zwei Spalten: NA / EN-Empfehlung
- **Durchbiegung:** Tabelle mischte Kombinationen (w_net,fin „quasi-ständig ℓ/250“, Kragarme ℓ/150 und ℓ/125). Jetzt NA-Werte: w_inst ℓ/300 (Krag ℓ/150), w_fin − w_c ℓ/200 (ℓ/100), w_net,fin ℓ/300 (ℓ/150); Kriech-Formeln für G, Q₁, Qᵢ ergänzt; k_def für OSB/2 und OSB/3,4 getrennt
- **Schwingung:** Frequenzbereiche waren vertauscht. EN 1995-1-1, 7.3.3: f₁ ≤ 8 Hz → Sonderuntersuchung; Steifigkeits- und Geschwindigkeitskriterium gelten für f₁ > 8 Hz. Hinweis, dass der deutsche NA abweicht
- **Mindestabstände:** Stabdübel und Bolzen wurden in einer Tabelle vermischt, a₃,c „max(3,5d; 40 mm)“ steht in keiner der beiden. Jetzt getrennt nach Tab. 8.5 (Stabdübel) und 8.4 (Bolzen); Nägel vollständig (nicht vorgebohrt ρ ≤ 420 und 420–500, vorgebohrt; a₃,c, a₄,c und a₄,t für d < 5 mm ergänzt). Legende korrigiert: t = beansprucht, c = unbeansprucht (vorher bei a₃,c „belastet“)
- **kmod:** Zuordnung nach NA ergänzt (Schnee ≤ 1000 m „kurz“, Wind Mittelwert kurz/sehr kurz → 1,00 in NKL 1/2)
- **Nagel-Einschlagtiefe:** Die Zahlen (8d voll, 6d–8d linear, < 6d nicht tragend) ließen sich nicht belegen → durch Hinweis „in DIN EN 1995-1-1/NA nachschlagen“ ersetzt. **Offen: prüfen und ergänzen**

### Neu
- **Adressen je Seite** (`#/holzbau/baustoffe/vollholz`): Zurück-Taste und Wischgeste funktionieren, Seiten verlinkbar, Neuladen bleibt auf der Seite. Links statt `onclick`-divs (Tastatur, Barrierefreiheit)
- **Suche** auf der Startseite über Titel und Inhalte aller Themen, mit Textausschnitt und Markierung
- **Rechner „Bemessungswerte“** bei Vollholz und BSH: Klasse, NKL, KLED (inkl. Wind), γM (NA/EN) → f_d für alle Festigkeiten (ohne k_h, k_cr, k_sys — steht dabei)
- **Skizze Mindestabstände** (schwarz-weiß SVG): a₁…a₄, Kraft unter α, beanspruchte/unbeanspruchte Seite
- Weiter/Zurück zwischen Themen eines Kapitels, Themenanzahl in Listen, Seitentitel je Thema
- Tabellen: erste Spalte bleibt beim waagerechten Scrollen stehen, Zeile antippen = markieren
- Links zu calc (Kopfzeile, Durchbiegung) und zur Übersicht; statiq·size-Verweise ohne Pop-up als „folgt“
- Druckansicht ohne Kopf/Navigation

### Tests
`statiq-tests/test_ref.py` (14, Browser): alle Themen laden, Direktlink + Zurück + Neuladen, Rechner (C24/NKL1/mittel → 14,77; Wind → kmod 1,00; GL24h γM 1,25 → 15,36), korrigierte Werte, Suche, ungültige Adresse, keine Pop-ups.


---

## Startseite (index.html)
- Fußzeile mit echten Versionen (jetzt calc v0.8.4 · ref v0.2.0) statt v0.5.5
- Sprachauswahl mit Kürzeln EN/DE/FR/ES statt Flaggen-Emojis (Windows zeigt Flaggen nur als Buchstaben); aktive Sprache über `data-lang` statt `onclick.toString()`
- calc-Karte: aktuelle Beschreibung und Stichworte (Wind, exakte Durchbiegung, Bericht als PDF), alle Stichworte in 4 Sprachen (auch size und ref)
- ref-Karte beschreibt den tatsächlichen Inhalt (Holzbau statt „IPE/HEA/HEB“), bleibt „bald“ und unverlinkt
- Neuer Link „Gespeicherte Berechnungen & Berichte“ → `calc.html#saved`
- Einblendung: ohne Korrektur wäre die ref-Karte durch den neuen Link unsichtbar geblieben (`nth-child`)

## size v0.5.13 — Übersichtlichkeit

- **Auswahlmenü** (`#pick`, `buildPick`, `updatePick`): ein Knopf „Bereich › Nachweis ▾“ ersetzt die Bereichsleiste und die Unterleisten. Die alten Leisten (`#seg-mat`, `#seg-typ`, `#seg-st`, `#seg-ho`, `#seg-mw`, `#seg-gr`, `#seg-wb`) bleiben im DOM (Klasse `ux-hide`), das Menü wird aus ihnen gebaut und klickt sie an — neue Nachweise erscheinen also automatisch, wenn sie in ihrer Leiste stehen. Zuordnung in `PICK_GROUPS`.
- **Projekt-Menü** (`#proj-btn`, `#proj-panel`, `openProj/closeProj`): Positionen und calc-Import werden beim Start aus der Eingabespalte in ein Fenster unter der Kopfzeile verschoben; Aufruf aus calc (`#calc=`) öffnet es.
- **Aufklappbare Eingabekarten** (`initFold`): Titel klickbar, zugeklappt mit Kurzfassung der sichtbaren Felder (`foldSummary`, max. 4 Werte). Nebenkarten starten zu (`FOLD_CLOSED`, Schlüssel = erste Feld-ID der Karte), Zustand je Karte in `statiq-size-fold`. Zuklappen über max-height (Felder bleiben im Layout, Tests können sie füllen).
- **Nachweisdetails** (`foldDetails`): zugeklappt, nicht erfüllte offen, „Alle aufklappen“, Klick in der Ergebnisliste öffnet; geöffnete bleiben bei neuer Rechnung offen (`DET_OPEN`). Bericht unverändert vollständig.
- Tests: Klicks auf die alten Leisten durch `setMat/setTyp/setStMode` ersetzt, Positionen/calc-Import öffnen vorher `openProj()`, Checkboxen in zugeklappten Karten vorher aufklappen. Neu `test_size_ux.py` (21).
- Noch offen aus dem Vorschlag: Hinweistexte hinter (i), Ergebnis mitlaufen lassen; calc (Lasten zugeklappt, „Erweitert“) und ref (Pfadleiste mit Dropdowns, Inhaltsmenü).

## Design 2026 für calc v0.8.14 · ref v0.3.3 · size v0.5.8

- Neuer Stil wie die Startseite als CSS-Schicht am Ende des ersten `<style>`-Blocks jeder Seite („Design 2026“): Variablen überschrieben (weiß, --card #f8f8f9, Radius 18/10 px), Raster `body::before` aus, Schrift Inter (zusätzlich zu DM Mono für Zahlen/Formeln geladen).
- Karten ohne Rahmen/Schatten mit hellgrauer Fläche, Kartentitel fett schwarz statt Mono-Großbuchstaben, Seitentitel groß und fett, Eingabefelder weiß mit feiner Kontur, Segmente als graue Leiste mit weißem aktivem Feld, Hauptknöpfe schwarz, Zweitknöpfe hellgrau.
- size: Bereichsleiste immer 3er-Raster, Unterleisten umbrechen; ref: Kacheln/Listen/Suchtreffer als dezente Knöpfe (Pfeile ausgeblendet), Tabellen ohne Rahmen; calc: Kopfzeile auf `header-links` umgestellt, Tabs als graue Pillen, Speichern-Knöpfe hellgrau, Diagramm-Umschalter behalten ihre Schnittgrößenfarben.
- Rückgängig: die Schicht „Design 2026“ löschen und den Google-Fonts-Link zurücksetzen.

## Startseite neu (Design-Test, von Valentin freigegeben)

- Weiß, ohne Raster, Rahmen und Schatten; Schrift Inter (fett, schwarz), „iq“ in Blau (#2563eb) oben und in der Fußzeile.
- Oben nur großes „statiq“ + „Eurocode 0 · 1 · 2 · 3 · 5 · 6 · 7“, kein Slogan, keine Überschrift „Module“, kein kleines Logo in der Kopfzeile (nur Sprachwahl).
- Module in der Reihenfolge Schnittkräfte, Bemessung, Theorie & Tafeln; nur Kennung + Status + großer Titel (Beschreibung und Stichworte per CSS ausgeblendet, Texte bleiben in der Datei). Keine Pfeile.
- Dezenter Knopf: hellgraue Fläche (#f9f9fa, Radius 18 px), beim Überfahren dunkler, beim Drücken dunkler + scale(0,985).
- Fußzeile: „Valentin Maras · calc … · ref … · size …“ (in allen Sprachen).
- Nächster Schritt laut Plan: calc, size und ref im gleichen Stil angleichen (zusammen mit der Übersetzung von size/ref).

## size v0.5.7 — Korrektur Skizze Holzverbindung

- `figHV`: Der Schnitt quer zur Faser zeigt jetzt alle m Reihen von Verbindungsmitteln übereinander (Abstand a₂, Rand a₄, mit Maß a₂), vorher war unabhängig von m nur ein Stift gezeichnet. Bauteilhöhe im Schnitt aus 2a₄ + (m − 1)a₂. Rechnung unverändert.

## size v0.5.6 — neuer Bereich Wasserbau (Hydrostatik und Hydrodynamik)

- Reiter „Wasserbau“ (`MAT='wasser'`, `WBMODE` druck/schwimm/rohr/gerinne/wehr, Positionstypen `wasser_*`). g = 9,81, γ_w = 9,81 kN/m³. Auf dem Handy wird die Bereichsleiste ab 560 px zum 3er-Raster. Hinweis „Schnittgrößen aus calc“ ist bei Wasserbau ausgeblendet (`page-calc`). `renderOut` zeigt „Ergebnisse berechnet“, wenn ein Fall nur Info-Abschnitte hat.
- **Wasserdruck** (`wd-*`, `wdFlaeche`): ebene Rechteckfläche, Neigung α, Oberkante t_o unter Wasser, Unterwasser h_u; Druckfigur (Trapez), F, Druckmittelpunkt (auch Steiner), Komponenten, Gegendruck, Resultierende und Moment um die Unterkante.
- **Schwimmkörper** (`ws-*`): Ponton L×B×H, G, z_G; Tiefgang, Freibord, z_B = T/2, BM = B²/(12T), GM = z_B + BM − z_G; Süß-/Seewasser.
- **Rohrleitung** (`wr-*`): v, Re, λ (laminar 64/Re, sonst Colebrook-White iterativ), h_v = (λL/D + Σζ)·v²/2g gegen Δh, Q_max per Bisektion; Energie- und Drucklinie, Reserve.
- **Gerinne** (`wg-*`): Rechteck/Trapez, Manning-Strickler (h_n per Bisektion), Grenztiefe aus Q²B/(gA³) = 1, Froude, spezifische Energie E(h) als Diagramm, Freibord.
- **Wehr** (`ww-*`): Poleni, μ-Vorgaben scharf-/rund-/breitkronig, Kontrolle der vernachlässigten Zulaufgeschwindigkeit, Oberwasserstand gegen zulässigen Wert.
- Tests: `test_size_wasserbau.py` (28) mit unabhängiger Python-Rechnung (numerische Integration, scipy brentq).

## size v0.5.5 (vorher als 0.9.1 ausgeliefert) — Setzung mit Bodenschichten

- Setzung hat eine eigene Baugrundkarte (die allgemeine Grundbau-Karte ist im Modus Setzung ausgeblendet, `gr-Es` entfällt): 1–4 Schichten (`gs-n`), je Schicht Bodenauswahl `gs-b{i}` (füllt γ und E_s aus `GR_BODEN`, `gsPreset`), Dicke `gs-h{i}` (letzte Schicht unbegrenzt), `gs-g{i}`, `gs-E{i}`; γ über der Sohle `gs-g0`; Grundwasser `gs-gw`/`gs-zw` (Tiefe unter Gelände).
- `gsUeber(I,z)`: wirksame Überlagerungsspannung schichtweise, unter GW γ′ = γ − 10; GW über der Sohle verringert auch die Aushubentlastung.
- Abbildung mit Schichtnamen und Farben, GW-Linie; Bericht mit Schichttabelle (Δs je Schicht).
- Tests in `test_size_grundbau.py` angepasst (33): drei Profile inkl. Grundwasser gegen unabhängige Boussinesq-Integration.

## size v0.5.4 (vorher 0.9.0) — neuer Bereich Mauerwerk (EC6 mit NA, γ_M = 1,5, ζ = 0,85)

- Reiter „Mauerwerk“ (`MAT='mauer'`, `MWMODE` druck/teil/keller/schub, Positionstypen `mauer_*`, `LAST.mat='mauer'`). Baustoffkarte `mw-*`: Steinart (Ziegel/KS/Porenbeton/Leichtbeton, Gruppe 1/2), Normal- oder Dünnbettmörtel; f_k nach EN 1996-1-1 Gl. 3.1–3.3 mit **empfohlenen** K-Werten (Tab. 3.3) oder eigener Wert (NA-Tabelle/Zulassung); f_vk0 nach Tab. 3.4 (empfohlen).
- **Wand auf Druck** (`md-*`): DIN EN 1996-3/NA vereinfachtes Verfahren. ρ_2 = 0,75/0,90/1,0 (t ≤ 175/≤ 250/> 250 mm, Holzbalkendecke 1,0), Φ_2 = 0,85·a/t − 0,0011·(h_ef/t)², Φ_1 = 1,6 − l_f/6 (f_k < 1,8: /5) ≤ 0,9·a/t, Dachdecke 0,333, Zwischenauflager ohne Φ_1; kurze Wand A < 0,1 m² → f_d·0,8. Anwendungsgrenzen (Auszug) als eigener Nachweis.
- **Teilflächenpressung** (`mt-*`): EN 1996-1-1 6.1.3, Ausbreitung 60° bis h_c/2, β = (1 + 0,3a_1/h_c)(1,5 − 1,1A_b/A_ef), 1 ≤ β ≤ min(1,25 + a_1/(2h_c); 1,5), Lochsteine β = 1.
- **Kellerwand** (`mk-*`): EN 1996-3 4.5, n_min ≥ ρ_e·h·h_e²/(β·t) mit β = 20/60 − 20b_c/h/40, n_max ≤ t·f_d/3, Anwendungsbedingungen (Auszug).
- **Schubwand** (`mh-*`): EN 1996-1-1 6.2, e = M/N, l_c = 3(l/2 − e), f_vk = f_vk0 + 0,4σ_d ≤ 0,065f_b, Stoßfugen unvermörtelt 0,5·f_vk0, Randdruck, e ≤ l/3. Hinweis: NA ergänzt Steinzug/Schubschlankheit.
- Offene Prüfpunkte: K/f_vk0-Werte sind EN-Empfehlungen, nicht NA-Tabellen; NA-Tabellen für f_k ggf. ergänzen.
- Tests: `test_size_mauerwerk.py` (29), unabhängige Python-Rechnung.

## size v0.5.3 (vorher 0.8.0) — neuer Bereich Grundbau (EC7 mit DIN 1054, BS-P)

- Vierter Reiter „Grundbau“ (`MAT='grund'`, Untermodi `GRMODE` flach/setzung/wand/upl, Positionstypen `grund_*`, `LAST.mat='grund'`, `LAST.mode`). Gemeinsame Baugrund-Karte `gr-*` mit Anhaltswerten wie in ref (`GR_BODEN`: γ, φ′, c′, E_s), „eigene Werte“ sobald ein Feld geändert wird.
- **Flachgründung** (`gf-*`): Eigengewicht Fundament + Überschüttung, H an OK Fundament (Hebel h_f). Lage der Resultierenden e_G ≤ b/6, e ≤ b/3 (ungünstig: volles M, nur V_G). Grundbruch DIN 4017 (`grundbruch()`: N_d0/N_b0/N_c0, Form- und Neigungsbeiwerte, m = (2 + b′/a′)/(1 + b′/a′), b′ als kürzere Seite im Breitenglied), R_n,d = R_n,k/1,4 gegen V_d = 1,35·G + 1,5·Q. Gleiten R_t,d = V_G·tan φ′/1,1. Streifen je m.
- **Setzung** (`gs-*`): σ_1 = V/A − γ·d, Steinbrenner (`steinbrenner`, `steinPunkt` durch Überlagerung), kennzeichnender Punkt 0,37a/0,37b von der Mitte, Grenztiefe 20 %-Kriterium, bis 3 Schichten (Schicht 1 E_s aus Baugrundkarte), Vergleich mit Mitte der schlaffen Last, optional s_zul.
- **Winkelstützmauer** (`gw-*`): Erddruck auf Ersatzwand am hinteren Sporn, Coulomb (`kaCoulomb`, δ_a = 0, φ/3, 2φ/3), Eigengewichte + Erde über den Spornen, Kippen über Exzentrizität, Gleiten, Grundbruch (Streifen) mit derselben Funktion.
- **Auftrieb** (`gu-*`): G aus Sohle, Außenwänden, Decke, Zusatzlast; A = γ_w·h_w·L·B; BS-P/T: 1,05/0,95, BS-A: 1,00/0,95; erforderliche Sohldicke.
- Tests: `test_size_grundbau.py` (28): N_d0 gegen DIN-4017-Tabellenwerte, Grundbruch/Exzentrizität/Gleiten unabhängig, Steinbrenner gegen numerisch integrierte Boussinesq-Lösung, Setzung und Grenztiefe unabhängig integriert, Stützwand, Auftrieb.
- Wasserbau erledigt in size v0.5.6.

## size v0.5.2 (vorher 0.7.0) — Schweißverbindungen (EN 1993-1-8, 4.5)

- Stahl › „Schweißnaht“ (`STMODE='schweiss'`, Felder `sw-*`, Positionstyp `schweiss`, Bericht `buildReportSW`). Drei Fälle über `sw-fall`:
  - `stirn` Träger an Stirnplatte, Rundumnaht: Gurtnähte außen (l = b) und innen (b − t_w − 2r, nur wenn je Stück ≥ max(30; 6a)), Stegnähte l_w = h − 2t_f − 2r. A_w, I_w mit Schwerpunkten in Nahtmitte; σ_w = N/A_w + M/I_w·z auf alle Nähte, τ_w = V/A_w,Steg nur Steg. Nachweis am äußeren Gurtrand und am Stegnahtende.
  - `lasche` Flachstahl an Knotenblech: Stirnnaht σ_w,Rd = f_u/(√2·β_w·γ_M2), Flankennaht τ_∥,Rd = f_u/(√3·β_w·γ_M2), lange Nähte β_Lw,1 (4.11), Tragfähigkeiten addiert; Flachstahl N_pl,Rd.
  - `konsole` Konsolblech an Stütze: zwei senkrechte Nähte, σ_w = F·e/W_w, τ_∥ = F/A_w; Blech im Anschnitt mit Vergleichsspannung.
- `swPunkt`: σ⊥ = τ⊥ = σ_w/√2, beide Bedingungen aus 4.5.3.2(6), Vergleich zum vereinfachten Verfahren in jedem Nachweis. `swKonstr`: a ≥ max(3; √t_max − 0,5) (NA), l ≥ max(30; 6a); a ≤ 0,7·t_min nur als Empfehlung.
- Nicht enthalten: Stumpfnähte, Ermüdung, Hohlprofile, Grundwerkstoff im Anschluss (Stirnplatte, Stützengurt).
- Tests: `test_size_schweiss.py` (16), unabhängige Python-Rechnung.

## calc v0.8.10 — Streckenlast auf dem Riegel in drei Richtungen

- Riegel-Streckenlast hat jetzt eine Richtung `rdir` (eigener Schlüssel, damit alte Dateien mit `dir` unverändert bleiben):
  - `v` (Standard): senkrecht, je m Grundriss — wie bisher.
  - `n`: rechtwinklig zum Riegel, je m Stablänge; q > 0 drückt auf den Riegel (Winddruck), q < 0 = Sog. Global (sin α, −cos α)·q.
  - `h`: waagerecht, je m Höhe (Projektion), q > 0 nach rechts; auf flachem Riegel wirkungslos.
- Position a/b bleibt die waagerechte Koordinate x. Zeichnung: Pfeile in Lastrichtung, Beschriftung ohne Überlappung, Zeichenfläche wächst bei vielen Lastlagen nach oben (`placeLabels(..., Y0)`).
- Bericht nennt die Richtung (`perNormal`, `perHeight`), alle Texte in 4 Sprachen (`rdirV/N/H`, `rdirNote`).
- Tests: `test_calc_rafterload.py` (9) gegen erweitertes `fem.py` (`rdir` dort unabhängig umgesetzt) und Gleichgewicht.

## size v0.5.1 (vorher 0.6.0) — gelenkiger Stützenfuß und Durchstanzen

### Stützenfuß (EN 1993-1-8, 6.2.5) — Stahl › „Stützenfuß“ (`STMODE='fuss'`)
- Felder `fp-*`; Fugenfestigkeit f_jd = 2/3·k_j·f_cd mit k_j = min(B_f/B, L_f/L, 3); c = t_p·√(f_y/(3·f_jd·γ_M0)).
- Wirksame Fläche als Vereinigung der T-Stummel um Gurte und Steg, auf die Platte begrenzt (`fpFlaeche`); N_j,Rd = A_eff·f_jd.
- Querkraft über Reibung 0,2·N_c,Ed, Kehlnähte am Steg. Import aus calc füllt N/V aus der Rahmenstütze. Positionstyp `fuss`.
- Tests: `test_size_fuss.py` (7), A_eff unabhängig per Raster.

### Durchstanzen (DIN EN 1992-1-1 mit NA, 6.4) — Stahlbeton › „Durchstanzen“
- Felder `ds-*`: Stütze rechteckig/rund, Innen-/Rand-/Eckstütze (β = 1,10/1,40/1,50 nach NA), V_Ed, Biegebewehrung oben in beiden Richtungen.
- d als Mittel aus d_x/d_y; ρ_l = √(ρ_x·ρ_y) ≤ min(2 %, 0,5·f_cd/f_yd).
- u_0, u_1 im Abstand 2d (Rand: 2c₁ + c₂ + π·2d, Ecke: c₁ + c₂ + π·d; rund: Halb-/Viertelkreis + D). C_Rd,c nach NA (Innenstütze mit u_0/d < 4 abgemindert), v_min, v_Rd,max = 1,4·v_Rd,c.
- Durchstanzbewehrung: A_sw je Reihe mit s_r = 0,75d, f_ywd,ef = 250 + 0,25d; NA-Faktoren 2,5 (1. Reihe) und 1,4 (2. Reihe); äußerer Rundschnitt mit C_Rd = 0,15/γ_c, Anzahl Reihen bis 1,5d innerhalb u_out.
- Abbildung: Draufsicht mit u₁, Bewehrungsreihen und u_out (freie Ränder bei Rand-/Eckstütze), Schnitt mit Bruchkegel.
- Nicht enthalten: Öffnungen, Stützenkopfverstärkung, genaues β, Fundamente, Mindestmomente 6.4.4.
- Tests: `test_size_durchstanzen.py` (13), unabhängige Python-Rechnung für 8 Fälle.

## size v0.5.0 — Holzverbindungen (EN 1995-1-1, Abschnitt 8)

- Holz hat Untermodi „Träger / Stütze“ und „Verbindung“ (`HOMODE`, `setHoMode`, Felder `hv-*`, Bericht `buildReportHV`, Positionstyp `holzverb`).
- Verbindungsmittel: Stabdübel (f_u,k 360/490), Nägel glattschaftig (vorgebohrt oder nicht), Holzschrauben (d_ef = 1,1·d_k; ≤ 6 mm nagelartig, sonst wie Stabdübel; F_ax,Rk aus ETA).
- Anordnungen: Holz–Holz ein-/zweischnittig (8.6/8.7), Schlitzblech innen (8.11), Bleche außen (8.12/8.13), Blech–Holz einschnittig (8.9/8.10) mit Interpolation zwischen dünnem und dickem Blech. Alle Modi werden mit Zahlen angezeigt, maßgebender markiert.
- f_h,k (Nägel/Stabdübel, Winkel mit k90 = 1,35 + 0,015·d), M_y,Rk = 0,3·f_u·d^2,6, Einhängeeffekt begrenzt (Nagel 15 %, Schraube 100 %, Stabdübel 0); Nagel-F_ax aus f_ax,k/f_head,k mit Einbindetiefe.
- n_ef: Stabdübel (8.34) mit Interpolation 0°–90°, Nägel Tab. 8.1 (k_ef). Mindestabstände Tab. 8.2/8.5 (Hirnholz belastet, Rand bei α = 0 unbelastet), Mindestholzdicke und Einbindetiefe nicht vorgebohrter Nägel.
- Abbildung: Schnitt mit verformtem Stift (Fließgelenke, Lochleibung farbig, Kräfte der Teile) und Draufsicht mit a₁…a₄.
- Nicht enthalten: Blockscheren/Nettoquerschnitt, Querzug, axial beanspruchte Schrauben, vereinfachtes Verfahren des NA.
- Tests: `test_size_holzverb.py` (16).

## size v0.4.3 · ref v0.3.2 (Grundgerüst Sprache)

- Beide Seiten haben dasselbe Gerüst wie calc: `LANG` (aus `statiq-lang`), `I18N` mit Schlüsseln, `tx(key, …)`, `applyI18n()` für `data-i18n`, `data-i18n-ph` (Platzhalter), `data-i18n-title`. **Rückfall ist Deutsch** (Inhalte bisher nur deutsch). Oberflächenrahmen (Kopf, Positionen, calc-Import, Baustoffwahl, Bericht-Knöpfe; in ref Startseite, Suche, Zähler, „in Vorbereitung“) läuft schon über Schlüssel.
- Bei EN/FR/ES erscheint ein Hinweis in der gewählten Sprache: Seite bisher nur deutsch, Nachweise nach deutschem NA (`showLangNotice`).
- Regel für neue Inhalte: Texte gleich als Schlüssel anlegen. Reihenfolge laut Absprache: erst Inhalte, zum Schluss Übersetzung von size/ref zusammen mit der Design-Überarbeitung.
- ref: Kopfzeile hat jetzt auch einen Link zu size.

## calc v0.8.9 (Mehrsprachigkeit)

- Alle Texte in calc über feste Schlüssel: statisch `data-i18n="key"` (innerHTML) und `data-i18n-title`, dynamisch `tr(key)` bzw. `trf(key, …)` mit Platzhaltern {0}. Zusätzliche Schlüssel in `I18N_UI` (EN/DE/FR/ES), wird in `calcTranslations` gemischt; fehlt ein Schlüssel, gilt Englisch.
- `applyCalcTranslations()` neu ohne Textvergleich; Sprachwahl EN/DE/FR/ES im Menü (`setCalcLang`, gemeinsamer Schlüssel `statiq-lang` mit der Startseite), danach werden Lastlisten, Durchlaufträger, Rahmen und Gespeichert neu aufgebaut.
- Bericht, Namen gespeicherter Berechnungen, Hinweise (`MSG.fr/es`), Datumsformat (`LOCALE()`) in der App-Sprache. Theorie-Fenster aller vier Systeme vollständig übersetzt; Durchlaufträger-Hilfe inhaltlich aktualisiert (Randbedingungen mit Kragarm, Superposition als Handrechnung).
- Namen bereits gespeicherter Berechnungen bleiben in der Sprache, in der gespeichert wurde.
- Offen: size und ref sind nur deutsch.
- Tests: `runtests_report.py` prüft die Berichte auf DE (Inhalte) und EN/FR/ES; `test_calc_ui.py` FR-Hilfe und Rückfall auf Englisch.

## calc v0.8.8 · size v0.4.2 (calc → size)

- calc, Gespeichert: Knopf „In size bemessen →“ (`tr('toSize')`) öffnet `size.html#calc=<Schlüssel>`.
- size: Karte „Schnittgrößen aus statiq·calc“ (`#calc-import`) mit Auswahl aller gespeicherten calc-Berechnungen; bei Rahmen Wahl Riegel / Stiel (stärker gedrückt). Übernahme in den gerade aktiven Baustoff und das Bauteil (`importCalc`), Hinweistext mit Quelle und den übernommenen Werten.
- `calcSchnitt(sdf)` liest die gespeicherten Verläufe (`plot`): Vorzeichen M = −plot.M bei Einfeld-/Durchlaufträger, +plot.M beim Kragarm; Rahmen über `plot.fine` (Zug innen +, N Zug +). Feldmoment = max M > 0, Stützmoment = max(−M), V = max|Q|; DLT: Stützweite und K/l0-Faktor des Feldes mit dem größten Feldmoment (Endfeld 1,3 / 0,85, Innenfeld 1,5 / 0,7). Einfeldträger: Momentenverlauf Gleichlast oder Einzellast aus den Lasten. Stiel: M02/M01 aus den Endmomenten (gleiches Vorzeichen = einsinnig, M01 > 0).
- Nicht übernommen (Hinweis): M_qp, charakteristische Momente für Durchbiegung, Knicklänge/Kriechzahl. Alte Speicherstände ohne `plot` → Hinweis „neu speichern“.
- Tests: `test_size_import.py` (14).

## calc v0.8.7 · size v0.4.1 · Startseite (Navigation)

- calc: Menü verlinkt size und ref (vorher „SOON“, ausgegraut); Kopfzeile mit Links calc · size · ref wie in size; Bereichsname oben in der gewählten Sprache (`showTab` las eine nie gesetzte Variable `window._i18n`).
- size: Kopf-Link „ref“ folgt dem Baustoff (#/stahlbeton, #/stahlbau, #/holzbau); `scroll-margin-top` für Karten und Ergebnis, damit Sprünge nicht unter der festen Kopfzeile landen.
- Startseite: `overflow-x: clip` auf html/body — der dekorative I-Träger stand auf dem Handy 20 px über.
- Offen aus der UI-Prüfung: englische Reste in calc auf Deutsch (Auflagertabelle, „Reaction V_A“, „Bending Moment“, „Head Support“) und deutsche Reste auf Englisch („Gespeichert“, Namen gespeicherter Berechnungen) → gehört zur Mehrsprachigkeit.
- Hinweis: Die Seiten verlinken sich über relative Pfade — alle vier HTML-Dateien müssen im selben Ordner liegen.

## calc v0.8.6 (Durchlaufträger: Einspannung, Kragarme, Gelenke, EI je Feld, Einzelmomente)

- Zustand `contCfg = {supL, supR, ovL, ovR, hinges}`; `ovL`/`ovR` sind wie ein Feld aufgebaut (`L` = 0: kein Kragarm), Zugriff über `contSeg(k)` mit k = Feldindex, `'L'` oder `'R'`. `spanData[i]` hat zusätzlich `k` (I_i/I) und `mom` (Einzelmomente, ↻ +).
- `contLayout()` liefert Abschnitte, Lager (Typen an den Enden wählbar: Festlager, Loslager, Einspannung; innen Loslager) und Gelenk-x. Nur Loslager → ein Lager wird intern waagerecht gehalten (`hfix`).
- `lineBuildModel` kann jetzt `hinges` (zweiter Drehfreiheitsgrad `rot2` rechts vom Knoten) und `EIfn(x)` (EI je Stelle). Einfeldträger/Kragarm nutzen das nicht, Verhalten unverändert.
- Mechanismus → Hinweis „kinematisch verschieblich“. Auflagertabelle: Moment über jedem Lager (inkl. Einspannmoment).
- Bericht/SDF: `geometry.ovL/ovR/k`, `system.hinges`, `loads.ovL/ovR`, `mom`; `plot.layout` für das Diagramm (ältere Speicherstände ohne layout werden wie bisher gezeichnet).
- Neue dynamische Texte über `tr(key)` mit Schlüsseln in allen vier Sprachen (Anfang der Umstellung auf Schlüssel statt Textvergleich). Theorie-Hilfe: Lösungsweg korrigiert (Weggrößenverfahren statt Dreimomentengleichung) und Abzählkriterium ergänzt (`data-i18n`, EN/DE).
- Tests: `test_calc_cont.py` (11) gegen eigene Balken-FEM mit Gelenk-Freiheitsgraden und Handwerte (−qL²/12, Gerberträger M_B = −48,75 kNm, M im Gelenk = 0).

## calc v0.8.5 (Rahmentypen, Theorie-Hilfe, Modellprüfung)
### Rahmentyp-Schaltflächen (Dreigelenkrahmen wieder da)
Seit dem gemeinsamen Solver (v0.8.0) ist ein Rahmen mit zwei Gelenklagern ein **Zweigelenkrahmen** (1-fach unbestimmt). Der Dreigelenkrahmen braucht ein echtes Riegelgelenk, das man vorher von Hand setzen musste. Neu oberhalb von „Lager A“:
- **Dreigelenkrahmen**: Gelenk/Gelenk + Riegelgelenk in Feldmitte (b/2), kein Kopflager
- **Zweigelenkrahmen**: Gelenk/Gelenk, keine Gelenke
- **Eingespannt**: Einspannung/Einspannung, keine Gelenke
- `applyFramePreset(name)` setzt Lager und Gelenke; `updatePresetButtons()` (aufgerufen aus `updateIndetInfo`) hebt den passenden Typ hervor, auch wenn man das System von Hand so einstellt
- Prüfung: q=10, h=4, b=5 → V=25 kN, H=±7,81 kN, Eckmoment −31,25 kNm, Gelenkmoment 0 (stimmt mit Handrechnung)

### Theorie-Fenster Rahmen neu geschrieben
Abzählregel n = a − 3 − g, typische Rahmen, Dreigelenkrahmen von Hand (V = qb/2, H = qb²/(8h), M_Ecke = −qb²/8 mit Zahlenbeispiel), wie calc rechnet (Weggrößenverfahren), Vorzeichen. Schlüssel `mfs1h…mfs5t` in en/de; fr/es fallen auf Englisch zurück. `data-i18n` fällt jetzt generell auf Englisch zurück, statt leer zu bleiben.

### Modellprüfung (Fuzz-Tests)
- `fuzz_frame.py`: zufällige Rahmen (Lager, Gelenke, Kopflager, Lasten, Neigung) gegen `fem.py`. 3 × 150 = 450 Fälle: 298 Übereinstimmung, 132 Mechanismen von beiden erkannt, 20 kleine Abweichungen 0,2–0,7 % — alle durch das grobe Referenznetz (`nseg=50`); mit `nseg=400` sinkt die Abweichung von 0,39 % auf 0,01 %. **Keine echte Abweichung.**
- `fuzz_beam.py`: 60 zufällige Balken (Einfeld, Kragarm, DLT) gegen `beamfem.py`: 60/60
- Aufruf: `python3 statiq-tests/fuzz_frame.py [Anzahl] [Seed]` bzw. `fuzz_beam.py` — langsam, deshalb nicht in `run_all.py`
- `fem.py` erkennt jetzt Mechanismen: skalierte Steifigkeitsmatrix, kleinster/größter Eigenwert ≤ 1e-14 → Fehler. Gemessen: stabile Systeme 4e-13 … 7e-12, Mechanismen ≤ 1e-16

### Tests
- `test_calc_ui.py` (12, Playwright): Schaltflächen, Dreigelenk-Ergebnisse, Gelenkmoment 0, Hervorhebung, Theorie-Fenster DE und FR

## calc v0.8.4
- `calc.html#saved` (sowie `#beam`, `#cantilever`, `#cont`, `#frame`) öffnet direkt den Bereich

---

## Was in v0.8.3 passiert ist (Vorzeichen der Lagerkräfte vereinheitlicht)

Überall gilt jetzt dieselbe Regel: **Kraft des Lagers auf das Tragwerk, H → +, V ↑ +, M ↺ +** (Rahmen-Tabelle, Bericht, Einfeldträger, Kragarm). Die Beschriftungen tragen die Pfeile (Tooltip „Kraft des Lagers auf das Tragwerk“).
- **Einfeldträger H_A:** zeigte bisher die Summe der Horizontallasten (= −H_A). Beispiel H = 5 kN → : jetzt H_A = −5,00 kN
- **Kragarm H_A:** ebenso
- **Kragarm M_A:** zeigte bisher das Schnittmoment an der Einspannung (Zug oben negativ, z. B. −37,5), der Bericht aber das Lagermoment (+37,5 ↺). Jetzt überall das Lagermoment ↺
- **Kragarm M max** bleibt das Schnittmoment mit Vorzeichen, Einheit jetzt „kNm · Zug unten +“. Last nach unten: M_A = +37,5 ↺, M max = −37,5
- Tests: Lagerkräfte von Einfeldträger und Kragarm gegen die FEM-Reaktionen, und App = Bericht (im Browser)

---

## Was in v0.8.2 passiert ist (Bericht)

### Behobene Fehler
- **Bericht für Einfeldträger, Kragarm, Durchlaufträger stürzte immer ab** (`sup.A` auf nicht gespeicherte Lager). Außerdem las er Auflagerkräfte aus nicht existierenden Feldern (`b-res-VA`) und aus der aktuellen App-Anzeige statt aus der Speicherung; L wurde nie angezeigt
- **Gespeichert wurde der Stand beim Klick auf „Speichern“**, nicht der berechnete. Wer nach dem Berechnen etwas änderte, bekam Eingaben und Ergebnisse, die nicht zusammenpassen. Jetzt hält jede erfolgreiche Berechnung einen Schnappschuss (`lastCalc[sys]`: Geometrie, Lager, Lasten, Steifigkeit, Auflagerkräfte, Maxima, Systembild, Verläufe). Speichern nimmt nur diesen; nach einem Rechenfehler wird er gelöscht
- **Rahmen-Bericht:** Einzellast auf dem Riegel stand als „H=20 kN“, Lager auf Englisch, Verläufe aller Stäbe als eine flache Kurve hintereinander, w eine Fantasiekurve
- **Doppelte SVG-ids** (Pfeilspitzen, Muster) zwischen App, Bericht und Speicherliste → Pfeilspitzen konnten fehlen. `uniquifySvgIds()` für gespeicherte Systembilder, eigenes id-Präfix für Diagramme (`target.idp`)

### Neuer Bericht
- **Verläufe am Tragwerk** mit denselben Zeichenfunktionen wie die App: `renderDiagram` und die Builder (`renderBeamDiagram`, `renderCantDiagram`, `renderContDiagram`, `renderFrameDiagram`) nehmen ein Ziel `{svg, mode, idp}` an (`ex.target` bzw. `opts.target`) und verändern dann den App-Zustand (`diagData`) nicht
- **Exakte Verformung** (Balken: w, Rahmen: u der Stiele und w des Riegels) als Diagramm und als Kennwert
- **Inhalte:** Systembild, Typ, Geometrie, Lagerung (inkl. Kopfhalterung, Gelenke), Steifigkeit, lesbare Lastliste mit Stab, Lage und Richtung, Maxima, Auflagerreaktionen mit Vorzeichenregel, beim DLT die Stützmomente. N-Diagramm entfällt, wenn N überall 0 ist (DLT)
- **Druck/PDF:** eigene Druckregeln (keine App-Kopfzeile, kein Raster, volle Seitenbreite, Diagramme zweispaltig, keine Umbrüche in Karten/Tabellen) → Rahmen-Bericht auf 2 A4-Seiten
- **Ältere Speicherungen** (ohne `sdf.plot`): öffnen weiter, vereinfachte Verläufe (`renderReportDiagramsLegacy`) mit Hinweis; Durchbiegung wird nicht mehr als Ersatzkurve erfunden, sondern als „nicht enthalten, neu berechnen“ angezeigt
- Rahmen-Speichername deutsch: „Rahmen Einspannung/Festlager b=5m h=4/4m“

### SDF (neu ab 0.8.2)
`sdf.plot` = exakte Verläufe (Balken: `ts, M, Q, N, w` in den Array-Vorzeichen der App; Rahmen: `allM/allQ/allN, NP, fine{left,rafter,right}` mit `t, M, Q, N, ux, uy`), `sdf.system.supports/loads/stiffness` für alle Systeme, `results.w` (und beim Rahmen `results.u`), beim DLT `results.supportMoments`. `results.members` (gleichmäßig) bleibt für statiq·size.
Lasten im Schnappschuss tragen `i` (Nummer wie in der Eingabe) und `enabled`; `loadSDF` entfernt sie beim Laden.

---

## Was in v0.8.1 passiert ist

### Pop-ups ersetzt (Bedienung)
Alle 18 `alert()` sind raus.
- **Hinweisfeld unter jedem Berechnen-Knopf** (`#msg-beam|cant|cont|frame`): Fehler rot, Warnungen gelb. Bei einem Fehler werden alte Ergebnisse ausgeblendet (vorher blieben veraltete Werte stehen)
- **Einblendung unten** (`showToast`) für Aktionen in der Speicherliste (Laden, Export)
- Texte zentral in `MSG` (EN + DE, FR/ES fallen auf EN zurück), `msgText(key, …)`. Helfer: `showCalcMsgs`, `clearCalcMsg`, `calcError`

### Behobene Fehler
- **Gelenk am Stützenfuß bei Fest-/Loslager** zählte als Gelenk → z. B. Festlager + Loslager + Gelenk am Fuß wurde als „Mechanismus“ abgebrochen, obwohl stabil. Neu `frameEffectiveHinges()`: zählt nur wirksame Gelenke (nicht am gelenkigen Fuß, doppelte Stellen einmal, Stütze + Riegel an derselben Ecke einmal). Gelenk am Fuß einer Einspannung wirkt wie ein Festlager
- **Kragarm, M max:** zeigte immer −|M|max, auch bei positivem Moment (Last nach oben). Jetzt der betragsgrößte Wert mit Vorzeichen (wie das Einspannmoment)
- **Positionen außerhalb des Stabs** wurden still aufs Stabende gesetzt → jetzt mit Hinweis (Lasten, Gelenke, alle Systeme). Beschriftung wie in der Eingabe (F1, q2, P1, L2·F1 …)
- **Streckenlast über das Stabende hinaus** wurde auf den Stab *gestaucht* (0→10 kN/m auf 0…6 m wurde auf 0…5 m zu 0→10). Jetzt abgeschnitten mit linear interpolierter Ordinate (0→8,33). Helfer `cutRange()`, `checkPos()`. a > b ist erlaubt (wird getauscht)
- **Eingabegrenzen beim Rahmen** (`max` der Positionsfelder) werden bei Änderung von b/h/hA/hB nachgeführt (`refreshFrameInputs()`); Gelenke nutzen hA/hB statt h

---

## Was in v0.8.0 passiert ist

### Ein Rechenweg für alle vier Systeme
Einfeldträger, Kragarm und Durchlaufträger laufen jetzt über dasselbe Weggrößenverfahren wie der Rahmen
(`lineBuildModel` / `lineSolve`, Abschnitt LINIENTRAGWERKE). Ein Balken ist ein gerader Stab auf der x-Achse.
Wiederverwendet: `frameSolveDSM`, `frameForcesAt`, `frameDispAt`, `sampleFine`, `sampleUniform`
(die beiden letzten sind die aus `frameSampleFine`/`frameSampleForces` herausgelösten Kerne).
- Alte Formeln entfernt: Handformeln Einfeldträger/Kragarm, Dreimomentengleichung (`spanLoadTerms`, `gaussElim`),
  numerische Durchbiegung (`computeDeflection`, `computeDeflectionCant`), alter Rahmen-Zweig im w-Renderer
- Array-Vorzeichen je System unverändert (Einfeldträger/DLT: M- und Q-Array = −M/−Q, Kragarm: +M/−Q),
  neu dazu `ts` (Stützstellen), `w` (exakt, mm) und `uni` (gleichmäßig, für SDF/Bericht)
- EI-Eingaben bei Einfeldträger/Kragarm/DLT rechnen neu (vorher nur neu gezeichnet)

### Behobene Fehler (vorher durch den neuen Balken-Test gegen FEM gefunden)
- **Durchlaufträger, Durchbiegung:** Um Größenordnungen falsch (z. B. −2364 mm statt −6.53 mm). Integriert wurde über die Pixellänge, als Einfeldträger über die Gesamtlänge; Innenstützen wurden ignoriert
- **Durchlaufträger, ungleiche Felder:** Diagrammpunkte gleichmäßig über die Gesamtlänge verteilt → Verlauf verzerrt, Stützmoment optisch bis ~1 m neben der Stütze (bis zu 30 kNm Abweichung an der gezeichneten Stelle)
- **Durchlaufträger, unsymmetrische Streckenlast (Trapez, Teilbereich):** Lastglieder der Dreimomentengleichung vertauscht → falsche Stützmomente (ΔM ≈ 1.8 kNm im Testfall)
- **Durchlaufträger speichern:** stürzte immer ab (`contSpans` nicht deklariert; `?.` schützt nicht vor nicht deklarierten Namen), max-Werte wurden mit falscher id gelesen
- **Rahmen laden:** Gelenke und Kopfhalterung wurden gespeichert, aber nicht geladen → geladenes System war ein anderes. Jetzt inkl. Kopfhalterungs-Typ und Steifigkeiten (neu im SDF: `supports.headType`, `stiffness`)
- **Speichern-Button FR/ES:** zeigte „undefined“ (`'💾 '+t.save||…` — Operator-Vorrang)
- **Umschalter (Lager, Kopfhalterung):** `.toggle-btn` hatte keinen CSS-Stil → Browser-Standardknöpfe; aktive Auswahl nicht erkennbar. Jetzt gestylt
- **Loslager-Knopf:** war fest „Gleitlager“ → wurde nicht übersetzt. Jetzt „Roller ○“ als Ausgangstext

### Aufräumen
- Emojis durch Linien-Icons ersetzt (`ICON.save/eye/eyeOff/check/warn/indet`, Farbe über currentColor). Statische Stellen über `data-icon="…"`
- Versionskonstante `STATIQ_VERSION` für App und SDF. SDF vor 0.8 tragen immer „0.5.5“ (auch aus v0.6/0.7), daher keine Migration möglich
- `escapeHtml()` für Namen in der Speicherliste (Namen erzeugt die App selbst, Import gibt es nicht → vorsorglich)
- „Laden“ erscheint nur noch bei Rahmen (für Balken gab es nie eine Ladefunktion)
- Entfernt: `syncColumnHeights` (nie aufgerufen), `calcFlags` (nie benutzt), Parameter `SM`, `Morig`-Fallbacks, Kommentar „Force Method“
- Beschriftungen: Sprungwert, der dasselbe zeigt wie ein nahes Label, entfällt; Stützen sind Sperrflächen im Systembild

---

## Was in v0.7.0 passiert ist (alle 5 offenen Punkte aus v0.6.0)

### 1. Exakte Spitzenwerte (nicht gleichmäßige Stützstellen)
Neue Funktion `frameSampleFine(model, NP)`. Stützstellen je Stab:
- gleichmäßiges Raster k/NP (wie bisher)
- jede Elementgrenze (Einzellast, Gelenk, Lastgrenze) **doppelt**: Ende des Elements davor + Anfang danach → Sprünge in Q/N und Knicke in M liegen exakt auf einer Stützstelle
- Nullstellen von Q im Element (Bisektion) → Feldmoment max M exakt

Ausgabe je Stab: `t[]` (0…1, nicht gleichmäßig), `M[] Q[] N[]`, `ux[] uy[]`.
Die Renderer nutzen `mem.ts`, wenn vorhanden, sonst wie bisher `i/n` (Beam/Kragarm/DLT, geladene Dateien).
M max / Q max / N max in der Ergebniszeile kommen jetzt aus den feinen Arrays.
Die gleichmäßigen Arrays (NP+1 = 51) bleiben für SDF/Bericht/statiq·size und für die Tests (`members[i].uni`).

### 2. Exakte Durchbiegung (W-Modus)
`frameDispAt(e, ξ)`: v(ξ) = v_i + θ_i·ξ + 1/EI·∫₀^ξ (ξ−τ)·M(τ)dτ, Knotenwerte aus `u`, 4-Punkt-Gauss (exakt, M ist kubisch).
- Der Solver rechnet jetzt mit **echtem EI in kNm²**: EI = E·Iy·10 (E-Eingabe in 10³ N/mm², Iy in 10³ cm⁴). Schnittgrößen unverändert (nur das Verhältnis zählt).
- Neuer Renderer `renderFrameDeflection()`: verschiebt jeden Punkt um (ux, uy), Biegelinie schließt an den Ecken von selbst, Knick an Gelenken, Lagerverschiebungen (Loslager) sichtbar.
- Beschriftung: Stützen → größte horizontale Verschiebung **u**, Riegel → größte vertikale Durchbiegung **w** (mm). Hinweis „u → +, w ↑ +“ unten rechts.
- Vorher: Stützen als Kragarme integriert, Riegel als Einfeldträger → physikalisch falsch bei Rahmen.

### 3. Stützen-Streckenlasten (Wind)
Streckenlast auf einer Stütze hat jetzt `dir`:
- `dir='h'` → horizontal, **q > 0 nach rechts →** (globale Richtung; Wind von links = beide Stützen positiv)
- `dir='ax'` → axial, q > 0 nach unten (Standard, wenn `dir` fehlt → alte Dateien rechnen gleich)
UI: Auswahl „Direction“ erscheint, sobald Stab = Stütze. Beim Wechsel auf eine Stütze wird `dir='h'` gesetzt und a/b auf die Stützenhöhe begrenzt.
*Achtung:* Einzellasten F auf Stützen bleiben „nach außen positiv“ (wie v0.6). Streckenlasten sind global „→ positiv“. Das ist bewusst so (Wind), steht in der UI dran.

### 4. Beschriftungen ohne Überlappung
Neue Funktion `placeLabels(list, W, H, blocked)`: Beschriftungen mit Priorität, Ausweichpositionen (oben/unten/seitlich oder vorgegebene `cands`), gedrehte Labels (`rot:-90`), Sperrflächen (Pfeile, Lager).
- Diagramm: Eckwerte (prio 0) → Maxima (1) → Sprungwerte (2, dürfen entfallen)
- N-Modus: bei konstantem Verlauf steht das Riegel-Label in Stabmitte (nicht mehr auf dem Kopf-A-Label)
- M-Modus: Riegel zeigt das **Feldmoment** (lokales Extremum im Inneren), nicht noch einmal den Eckwert
- Q-Modus: Riegel zeigt **beide Endwerte**
- Systembild: gestapelte Streckenlasten (jede Last sitzt auf der Oberkante der darunter), Label über dem Block oder daneben; Stützenlasten senkrecht beschriftet; Einzellast-Pfeil auf dem Riegel reicht über gestapelte Lasten hinaus

### 5. Ecken-Rendering
Keine Hypotenusen-Linie in anderer Farbe mehr, sondern ein **gefülltes Dreieck** Stützenordinate – Eckpunkt – Riegelordinate in Diagrammfarbe. Riegelordinaten stehen überall senkrecht zum Riegel (der alte Trick „an den Enden nur horizontal“ und die Clip-Pfade sind raus) → saubere Ecken auch bei hA ≠ hB.

### Weitere Fixes
- Sprunglinien im Rahmen lagen auf der falschen Seite (Vorzeichen) → gleiche Offset-Funktion wie das Diagramm
- Gelenke werden auch im Schnittgrößen-/Biegeliniendiagramm als Kreis gezeichnet
- Systembild: Gelenke/Einzellasten auf Stützen nutzten `h`/`col_top` statt hA/hB, Gelenk auf geneigtem Riegel lag nicht auf dem Riegel → behoben
- Einfeldträger/Kragarm W-Modus: w-Label stand weit neben der Kurve → sitzt jetzt am Maximum
- Positionsgrenze in der Lasteingabe nutzt hA bzw. hB je Stütze

---

## Konventionen (für alle Stäbe gleich)

**Stabrichtung:** linke Stütze A→K2 (nach oben), Riegel K2→K3, rechte Stütze K3→B (nach unten).
Array-Reihenfolge wie bisher: `Mleft[0]`=Fuß A, `Mraf[0]`=links, `Mright[0]`=Kopf B.

- **M > 0** = Zug innen (gestrichelte Faser innen)
- **Q** = dM/ds in Stabrichtung
  *Änderung:* Q in der linken Stütze hat jetzt das umgekehrte Vorzeichen wie vorher. Das ist konsistent: Bei einem symmetrischen System ist Q antimetrisch.
- **N > 0** = Zug
- **Reaktionstabelle:** H > 0 nach rechts →, V > 0 nach oben ↑, M > 0 gegen den Uhrzeigersinn ↺ (Pfeile im Tabellenkopf)
  *Änderung:* Vorher war H je nach Fall unterschiedlich, und M zeigte das Fußmoment statt der Reaktion.

**Lasteingabe:**
- Streckenlast: Riegel je m Grundriss (a, b = x); Stütze je m Höhe (a, b = z), `dir='h'` horizontal (→ +) oder `dir='ax'` axial (↓ +)
- Einzellast linke Stütze: F > 0 nach links, rechte Stütze: F > 0 nach rechts (beide nach außen), H > 0 nach unten
- Einzellast Riegel: F > 0 senkrecht zum Riegel nach unten, H > 0 in Riegelrichtung, Position z = x

*Achtung:* Bei Stützenlasten war H vorher dasselbe wie F (horizontal). Jetzt ist H wie beschriftet ∥ zum Stab, wirkt also axial. Alte gespeicherte Dateien mit H auf Stützen rechnen dadurch anders.

---

## Auswahlmenü als Akkordeon (size v0.5.13)
`buildPick()` baut je Bereich `.pick-group[data-mat]` mit Kopf `.pick-head` (Name, Anzahl bzw. aktuelles Thema, ▾) und `.pick-body` mit den `.pick-item`. Nur der aktuelle Bereich ist offen; Klick auf einen Kopf klappt um (eine Liste zur Zeit), das Menü bleibt offen. Aktives Thema mit blauem Punkt.

## Holz-Erweiterung in size (v0.5.10)
`HOMODE` jetzt `bauteil | verbindung | ausklink | sattel | versatz`. Gemeinsame Baustoffkarte `#ho-x` (`hx-art`, `hx-kl`, `hx-nkl`, `hx-kled`, `fillHxKlassen`, `hxMat()` ohne k_h, `M.kh(h)` gesondert). Dispatcher `HX_FN[mode] = [read, validate, nachweise, fig]`, `runHX`, `buildReportHX`, `LAST.mat = 'holzx'`, Positions-Typ `holz_<mode>`.
- **Ausklinkung** (6.5.2): τ = 1,5V/(k_cr·b·h_ef) ≤ k_v·f_v,d; k_v nach (6.62) mit k_n = 5 (VH) / 6,5 (BSH); oben k_v = 1; Hinweis α < 0,5.
- **Satteldach/Pultdach** (6.4, nur BSH): σ-Maximum am angeschnittenen Rand numerisch (Test gegen L·h₀/(2h_ap) bzw. L·h₀/(h₀+h_ap)), k_m,α (6.40, Druckrand), k_h an der Stelle; First: k_l = k₁, k_p = k₅, V = b·h_ap²(1 − tanα/4) ≤ 2/3·V_b, k_dis = 1,4; Schub am Auflager mit k_cr.
- **Versatz** (6.2.2): Stirn σ = S·cos²(γ/2)/(b·t_v), Ferse σ = S·cos γ/(b·t_v), f_c,α,d (6.16) mit k_c,90 (Eingabe, Standard 1); t_v ≤ h/4 (γ ≤ 50°) … h/6 (γ ≥ 60°); Vorholz l_v,ef = min(l_v; 8t_v) ohne k_cr.

---

## Lehrbuch-Skizzen in ref (v0.3.4)
Bibliothek im Skript direkt vor „RECHNER (neue Fächer)“: `SK` (Farben), `sv(w,h,label,body)` (SVG mit Markern skd/ska/skb/skc, max-width 1,7·w), Text `it` (kursiv, Formelzeichen) und `tl` (Beschriftung; **nicht** `tx`, das ist die i18n-Funktion), `ln`, `poly`, `pl`, `dimL` (Maßlinie), `arcA` (Winkelbogen), `arcArrow` (Momentenpfeil), `rAng`, `cen` (Schwerpunkt), `axH/axV`, Lager `supPin/supRoll/supClamp`, `hinge`, `beam`, Lasten `udl/pload/vec`, `mLine` (M-Verlauf, positiv unten).
Einbinden: `fig(svg, caption)`, `shapeCard(svg, titel, [[k,v],…])` in `shapeGrid([...])`, zwei nebeneinander mit `<div class="sk-row">`.
Skizzen: Mathematik (9 Flächen, Dreiecke, Einheitskreis, Kraftzerlegung, Ableitung, Biegelinie), Baustatik (Schnittufer, Bestimmtheit, Balkentafeln `BT.*` mit `btTile`, Durchlaufträger `dlTrag(n)`, T-Querschnitt, Spannungen, Eulerfälle, PVK), Schnee μ₁, Knicklinien χ, Plattenbalken b_eff, Rundschnitt u₁, Fachwerkmodell, Sohldruck, Grundbruchkörper.

---
## Startseite — vier Kacheln
- Vierte Kachel „Gespeichert“ (`#saved-card`, Link `calc.html#saved`) ersetzt die Textzeile unter calc; zeigt die Anzahl gespeicherter Einträge aus calc (`statiq_sdf_*`) und size (`statiq-size-positionen`) — `savedCount()`, Texte `saved`/`saved_n` in allen vier Sprachen
- Zusätze „LIVE“ und „BETA“ entfernt (samt CSS)

## Vertrauen und Seriosität — calc v0.8.24 · size v0.5.41 · ref v0.3.32 · rechtliches v0.1.3

Erster Block aus Valentins Optimierungsliste (Reihenfolge: 1 Vertrauen, 4 Handy-Eingabe, 2 Ladezeit, dann Dunkelmodus, Übungsmodus).
- **Fehler melden:** in calc (alle vier Fußnoten), size (Karte „Umfang und Grundlagen“) und ref (Fußnote jedes Themas) ein dezenter Link `.fehler-link`. `mulyFehlerHref(app, ver, extra)` (am Ende des letzten Skripts von calc/size/ref — kein eigener `<script>`-Block, sonst bricht der Node-Harness, der calc per Regex vom ersten `<script>` bis zum letzten `</script>` liest) baut eine mailto-Adresse mit Seite, Modul, Version, Sprache; size hängt `fixMode()` und `LAST.I` an (gekürzt auf 1400 Zeichen), ref den Hash des Themas. **`MULY_MAIL = 'kontakt@muly.eu'` ist ein Platzhalter**, bis Valentin die Adresse anlegt (in allen drei Dateien gleich).
- **Startseite:** Fußzeile mit aktuellen Versionen (stand noch auf calc 0.8.22 / ref 0.3.28 / size 0.5.36 / projekt 0.1.3) und neuer Zeile `#footer-check` „Jeder Rechenweg wird gegen unabhängige Nachrechnungen geprüft — derzeit über 1.500 automatische Prüfungen“ (DE/EN/FR/ES, Schlüssel `check`).
- **Impressum (rechtliches.html):** Name Valentin Maras eingetragen; Hosting GitHub, Inc. (GitHub Pages) mit Hinweis auf mögliche Übermittlung in die USA (4 Sprachen). Offen und markiert: Anschrift, E-Mail `[kontakt@muly.eu]`, USt-IdNr. `ph()` markiert nur noch Werte in eckigen Klammern.
- **Normstand:** Umfang-Karten ohne Norm ergänzt — Platte zweiachsig (DIN EN 1992-1-1 mit NA), Holz Durchbruch (DIN EN 1995-1-1 mit NA), Spundwand (DIN 1054, DIN 4085), Ausfachung (DIN EN 1996-3 mit NA, Anhang NA.C). Wasserbau-Modi nennen Verfahren (Darcy-Weisbach, Manning-Strickler …) und bleiben so.
- **Handy-Eingabe geprüft, bewusst nicht geändert:** `inputmode="decimal"` hätte auf dem iPhone keine Minustaste — viele Felder brauchen negative Werte (θ_e, Momente, N). `type="number"` bleibt. Dezimalkomma in Safari auf einem echten iPhone prüfen (Prüfliste).
- Test neu: `test_vertrauen.py` (9 Prüfungen). sw.js `VERSION = 'statiq-2026-10-20-1'`.

## size v0.5.40 · ref v0.3.31 — Baustoffe in Gruppen, 37 neue Einträge, Luftschichten

- **`BP_MAT` (gleich in size und ref) ab Index 28 erweitert** — nur angehängt, alte Indizes und Speicherstände bleiben: Leichtputz, Lehmputz, Wärmedämmputz, Calciumsulfat- und Gussasphaltestrich, gefügedichter Leichtbeton, Hochlochziegel mit Dämmstofffüllung, Leichtbeton-Hohlblock, Klinker, Sandstein, Granit, MW 040, Schaumglas, Phenolharz, VIP, Kork, Hanf/Flachs, BSH, BSP, Laubholz, Spanplatte, MDF, Sperrholz, Gipsfaser, Faserzement, Unterdeckbahn, Alu-Dampfsperre, Kunststoff-Dachabdichtung, Fliesen, Parkett, Teppich, Linoleum, Aluminiumblech, Kies; Index 62–64 Luftschichten (ruhend / schwach / stark belüftet, λ = 0 als Kennung). Werte: Anhaltswerte DIN 4108-4 / DIN EN ISO 10456 bzw. Herstellerwerte → Prüfliste.
- **`BP_GRP`**: 8 Gruppen (Putze und Estriche, Beton, Mauerwerk und Naturstein, Dämmstoffe, Holz und Plattenwerkstoffe, Bahnen und Folien, Beläge und Bekleidungen, Luftschichten). size: `<optgroup data-i18n-label="bgN">`, Übersetzer setzt `el.label`; neue Namen als Schlüssel `bm28`–`bm64` in den vier Wörterbüchern. ref: `bpSel()` baut die Gruppen, Namen über TTX.
- **Luftschichten (DIN EN ISO 6946)**: `bpLuftR(dmm, dir)` Tab. 8 (auf/hor/ab, linear, ab 300 mm gedeckelt); `bpMitLuft(L, art)` liefert gleichwertige Schichten (λ = d/R) und `W`: ruhend R aus Tab. 8; schwach belüftet R_T = ½·R_T,u + ½·R_T,v (A_v ≈ 1000 mm²/m) und gleichwertiges R der Luftschicht; stark belüftet: Luftschicht und alles außerhalb entfällt, R_se = R_si. Richtung: dach → auf, boden → ab, sonst horizontal.
- **Glaser**: `glaser(L, rse=GL.Rse)`; bei stark belüfteter Luftschicht Schichten außerhalb weg und R_se = 0,08 (DIN 4108-3, hinterlüftet). Randbedingungszeile in size mit Platzhalter für R_se, in ref eigene Hinweiszeile.
- size: λ-Feld der Luftschicht gesperrt (Platzhalter „R nach Tabelle“), `bpDStd` mit Dicken für die neuen Baustoffe (Luft 4 cm, Klinker 11,5 cm, Bahnen 0,04–0,15 cm …), Farben für Luft und neue Dämmstoffe. Schall: Luftschicht trennt die Schalen, angesetzt bleibt die schwerere.
- Test neu: `test_size_luftschicht.py` (12 Prüfungen, Sollwerte unabhängig in Python).
- sw.js `VERSION = 'statiq-2026-10-19-2'`.

## size v0.5.39 · ref v0.3.30 — Bauphysik auf Plausibilität geprüft

Anlass: Valentins Kommentare — ρ ändert im U-Wert nichts; Rohdichte steht doppelt (im Namen und in der Spalte ρ), ebenso beim Tauwasser.
- **Spalten je Modus** (`#bp-lay-card.bpm-<modus>`, Eingaben mit `data-c="d|l|u|r"`): U-Wert d, λ, ρ · Tauwasser d, λ, μ · Schall d, ρ. Hinweiszeile `#bp-lay-mode` sagt, was zählt.
- **ρ wirkt im U-Wert:** Mindestwärmeschutz mit m′ = Σρ·d; m′ < 100 kg/m² → leichtes Bauteil, R_min = max(Tab. 3; 1,75) nach DIN 4108-2, 5.1.2.2. Karte `bumin` trägt `Rmin`, `mF`. Gleiche Regel im ref-Rechner U-Wert und in der Legende der Anforderungstabelle.
- **Baustoffnamen in size ohne Rohdichte/λ/Dicke:** Optionen z211–z217, z227–z229 neu (DE/EN/FR/ES), z. B. „Kalksandstein“, „PE-Folie“. `BP_MAT` bleibt unverändert (gleich mit ref, Test). KS 2,0 (Index 6) ist `hidden`, alte Speicherstände laden weiter. Schicht hat jetzt `label` (übersetzter Optionstext) für Rechenweg und Bericht; `name` bleibt deutsch für Farben/Logik.
- **Folien:** `bpDStd()` setzt beim Wählen übliche Dicken (Folie/Dampfbremse 0,02 cm, Bitumenbahn 0,4, GK 1,25, Putz/OSB 1,5, Estrich 5, sonst 10). Vorher 10 cm → PE-Folie s_d = 50 000 m. Dicken < 1 cm im Rechenweg mit vier Stellen (`bpDm`).
- **Schall: Massegesetz nur für die massive Schale** (`bpSchale`: zusammenhängende Schichten mit ρ ≥ 300 kg/m³ um die schwerste). Dämmung und Putz auf der Dämmung (WDVS) zählen nicht, Hinweis „Nicht angesetzt …“ mit Verweis auf ΔR_w nach DIN 4109-34. Standardwand: m′ 355,8 → 333,0 kg/m². Trittschall nutzt dieselbe Masse.
- „(DIN 4109-32, einschalig massiv)“ jetzt übersetzt.
- **ref-Fehler gefunden:** U-Wert- und Glaser-Rechner zeigten in EN/FR/ES „Bitte Schicht eingeben“, weil die Vorgaben mit `tt(name)` kamen und `bpMatIdx` nur den deutschen Namen suchte → `bpMatIdx` sucht jetzt beide. Alle 132 Themen in 4 Sprachen ohne leere Rechner. „EPS WLS 032 (grau)“ in ref übersetzt.
- Ohne Befund geprüft: U-Wert (R_si/R_se, GEG-Referenz- und Bestandswerte, f_Rsi mit R_si = 0,25), Glaser-Randbedingungen, Massegesetz und Flankenformeln, Trittschall (L_n,eq, ΔL_w, K), Gebäudeklassen, Sonneneintrag (S1 Tab. 8, S2 = 0,060 − 0,231·f_WG).
- Legende der ref-Anforderungstabelle ohne `<sub>` (Textknoten-Übersetzung trFig findet sonst keinen Schlüssel).
- Test neu: `test_size_bauph_plaus.py` (16 Prüfungen).
- sw.js `VERSION = 'statiq-2026-10-19-1'`.

## size v0.5.38 — Stahlträger: eigener Querkraftnachweis und Schubbeulen

Anlass: Valentin hat den Schubnachweis bei Stahl › Träger/Stütze vermisst. Bisher steckte V_Ed/V_pl,Rd nur im η der Querschnittskarte, Schubbeulen wurde nur angekündigt, und die Grenze rechnete mit 72·ε (η = 1,0) — das war zu großzügig, richtig ist 72·ε/η mit η = 1,2.
- `nachweiseStahl`: neue Karte `id:'qv'` („Querkraft“) direkt nach `qs`. Inhalt: Schubfläche A_v,z (η = 1,0 in der Fläche, sichere Seite), V_pl,z,Rd (6.2.6), Nachweis V_Ed ≤ V_pl,z,Rd, Schlankheitsgrenze h_w/t_w ≤ 72·ε/η mit η = 1,2 für S235–S460 (sonst 1,0).
- Bei Überschreitung: Schubbeulen nach EN 1993-1-5, 5.2/5.3 mit Steifen nur an den Auflagern (k_τ = 5,34 → λ̄_w = h_w/(86,4·t_w·ε)), verformbarer Endpfosten (Tab. 5.1: χ_w = η bzw. 0,83/λ̄_w), V_bw,Rd mit γ_M1 = 1,1, Gurtanteil V_bf,Rd nicht angesetzt, V_b,Rd ≤ η·f_y·h_w·t_w/(√3·γ_M1). Interaktion M–V nach 7.1 bei η̄_3 > 0,5 und η̄_1 ≥ M_f,Rd/M_pl,Rd; M_f,Rd mit Abminderung für N.
- Hinweis im Rechenweg: V und M werden im selben Schnitt angesetzt (beide Größtwerte = sichere Seite).
- Querschnittskarte `qs`: η ohne Querkraft; die Abminderung von M_Rd für V > 0,5·V_pl,Rd bleibt dort. Alte Schubbeulen-Zeile entfernt.
- Ergebnisse der Karte zusätzlich als `C[].qv` (V, Vpl, hwt, lim, etaS, beul, lw, chi, Vbw, Vb, mv) für Tests.
- Abhilfe: `FIX_WHY['stahl:qv']`. „Nicht enthalten“: jetzt „Schubbeulen mit Zwischensteifen und Mitwirkung der Gurte“ statt „Plattenbeulen bei Schub“. Alle neuen Texte EN/FR/ES.
- Vier alte Übersetzungsschlüssel der früheren Schubbeulen-Zeile entfernt (test_size_i18n verlangt, dass jeder Schlüssel im Code vorkommt).
- Test neu: `test_size_schub.py` (19 Prüfungen, Sollwerte unabhängig in Python: IPE 300 S235, IPE 600 S460 mit und ohne Interaktion, mit N, IPE 600 S355 knapp unter der Grenze, Abhilfe, Umfang, EN/FR/ES).

## Neuer Markenname Muly — calc v0.8.23 · size v0.5.37 · ref v0.3.29 · projekt v0.1.4 · rechtliches v0.1.2

Valentin hat sich für den Namen **Muly** entschieden (DPMA-Prüfung ohne Treffer). Logo: Schriftzug „muly“ mit blauem μ als Exponent (Entwurf E2). App-Symbol: blaues Quadrat mit weißem „μ.ly“ (Entwurf D).
- **Sichtbar umbenannt:** Seitentitel, Startbildschirm-Name (`apple-mobile-web-app-title`), Manifest (`name`, `short_name`), Kopfzeilen-Logo aller Seiten (`muly<span>μ</span>`), großer Schriftzug der Startseite (`muly<span class="iq">μ</span>`), Modulnamen `muly·calc`, `muly·size`, `muly·ref`, Fußnoten und Berichtsköpfe (calc, size, ref, projekt), Installationshinweis, alle Texte in rechtliches.html (DE/EN/FR/ES), Übersetzungsschlüssel in ref/size mit umbenannt.
- **Logo-CSS:** je Seite ein `<style>` direkt vor `</head>`: `.logo span` 0,58 em, `vertical-align: .85em`; `.headline .iq` 0,44 em, `vertical-align: 1.05em` (wie Entwurf E2), `line-height: 0`, damit die Zeilenhöhe gleich bleibt.
- **App-Symbole neu** (`icons/`): 192 und 512 mit runden Ecken (transparent), maskable 512 und Apple 180 vollflächig blau (Schrift im sicheren Bereich), Favicon 32. Erzeugt mit Inter 800, Text „μ.ly“ in Weiß auf #2563eb.
- **Absichtlich unverändert**, damit nichts verloren geht: alle `localStorage`-Schlüssel (`statiq-lang`, `statiq-size-positionen`, `statiq-projekt` …), das Feld `statiq:'projekt'` in Projektdateien, der Präfix `statiq-` der Service-Worker-Speicher (alte werden beim Update gelöscht), Konstante `STATIQ_VERSION`, Ordner `statiq-tests/`, `statiq-tools/`, diese Datei. Projektdateien werden jetzt als `*.muly.json` gespeichert, alte `*.statiq.json` lassen sich weiter laden.
- Die Adresse `valentinmaras.github.io/statiq` in der calc-Berichtsfußzeile bleibt, bis das GitHub-Repository umbenannt ist.
- calc: Versionsanzeige im Kopf (`<span class="version">`) zeigte noch v0.8.22 → korrigiert; der neue Test prüft, dass sie zu `STATIQ_VERSION` passt.
- sw.js `VERSION = 'statiq-2026-10-18-2'`.
- Logo: Abstand des μ-Exponenten vergrößert (Rückmeldung Valentin): `.headline .iq` margin-left .16em, `.logo span` margin-left .12em.
- Startseite: Schriftzug „muly“ war zu eng (Rückmeldung Valentin) → `.headline` letter-spacing −0,055 em → −0,03 em.
- Tests: neu `test_marke_muly.py` (24 Prüfungen: kein sichtbares „Statiq“ in 6 Seiten × 4 Sprachen, Logo mit hochgestelltem μ, Manifest, Symbole, alte Schlüssel und Projektdateien). Angepasst: `test_pwa.py`, `test_projekt.py`, `test_size_import.py`, `test_calc_fres.py`, `test_rechtliches.py`. Stand 1473/1473 grün.

## Skizzen-Durchsicht — calc v0.8.22 · size v0.5.36 · ref v0.3.28

Alle Skizzen (ref 107, size 64 Modi, calc 4 Systeme mit Schnittgrößenlinien) als Bild gerendert und in zwei Runden geprüft.
- **Fachlich korrigiert:** ref Euler Fall 3 (Knickfigur war gespiegelt; oben jetzt seitliches Rolllager bzw. Parallelführung), ref Biegung (ε_cu2 statt ε_c2, F_cd zeigt in Druckrichtung), size Doppelbiegung (q_z/q_y in die gedrehten Achsen), Zugstab (Nettoquerschnitt an der lastnahen Lochreihe), Kellerwand (Druckbogen wölbt sich zur Erdseite), Böschung (z lotrecht wie in τ = γ·z·sinβ·cosβ), Wasserdruck (Gegendruck aus γ_w·(h_u − (L−a)·sin α)), Stirnplatte (h_r sichtbar, Momentenpaar), Schwimmen/Ponton (F_G und F_A auf der Wirkungslinie), Torsion (h in cm), Verbindung Holz (Schnitt in Kraftrichtung mit a₁).
- **Beschriftung:** Indizes werden in Skizzen automatisch tiefgestellt (`subIdx` in ref `T()`, `svgSub` in size `svgT()`); Einheiten an Maßen; Sohldruck beide Randwerte; Legenden und Bezeichnungen vereinheitlicht (G_k, Q_k,N …); Trigonometrie jetzt a gegenüber α (sin α = a/c) wie bei Pythagoras.
- **Layout:** `sv()` in ref hat 6 px Rand oben und unten; viele Überlappungen verschoben; calc Einfeld- und Durchlaufträger zeigen die Längen wieder vollständig (viewBox 128 bzw. 104).
- **calc Schnittgrößen:** Momente am Balken mit baustatischem Vorzeichen (unten gezogen positiv, `beamTxt`), alle inneren Extremwerte beschriftet (Feldmomente beim Durchlaufträger), Einheit „M [kNm]“ in der Ecke; Theorie-Fenster erklärt ā und b̄.
- Neuer Test `test_skizzen_klarheit.py`: keine Beschriftung ragt aus einer Skizze (alle ref-Themen, alle size-Modi, calc), dazu Stichproben der fachlichen Korrekturen.

## PWA — calc v0.8.21 · size v0.5.35 · ref v0.3.27 · projekt v0.1.3 · rechtliches v0.1.1

- **Installierbar:** `manifest.json` (Name „Statiq“, start_url `./index.html`, standalone, weiß), Symbole in `icons/` (Monogramm „st.“ in Inter 800, Punkt blau; erzeugt aus HTML mit Playwright). Alle sechs Seiten binden Manifest, Favicon, Apple-Symbol und Apple-Meta-Tags ein.
- **Offline:** `sw.js` legt beim ersten Besuch alle Seiten, Schriften, Symbole und das Manifest ab. HTML: zuerst Netz (Updates kommen sofort), offline aus dem Speicher; Schriften/Symbole: zuerst Speicher. **Bei geänderten Schriften oder Symbolen `VERSION` in sw.js hochzählen**; neue Dateien in `FILES` eintragen. Registrierung nur über http/https (nicht bei file://), in calc im Hauptskript (Node-Harness).
- **Startseite:** Karte „Statiq als App“ unter den Modulen: in Chrome/Edge/Android mit Knopf „Installieren“ (beforeinstallprompt), auf iPhone/iPad mit Anleitung „Teilen → Zum Home-Bildschirm“, als installierte App verborgen. DE/EN/FR/ES (`install_t/_s/_ios/_b`).
- **rechtliches.html:** Abschnitt „Offline-Nutzung und Installation“ in der Datenschutzerklärung.
- **Hosting:** Service Worker brauchen HTTPS. Hochladen: alle HTML-Dateien, `manifest.json`, `sw.js`, `fonts/`, `icons/`.
- Test: `test_pwa.py` (lokaler Server, Installierbarkeit über Chrome-CDP, offline alle Seiten, calc/size rechnen offline, Installationskarte Chrome und iPhone).

## calc v0.8.20 · size v0.5.34 · ref v0.3.26 — gleicher Rahmen, keine Pfadleiste

- size übernimmt den Rahmen von calc: ab 1000 px `max-width:1180px`, Innenabstand `6px 20px 20px`, Spalten `minmax(0,1fr) minmax(0,1.2fr)`, Abstand 20 px; am Handy Seitenrand 20 px. Kopfzeile in beiden `min-height:58px`. Die Auswahl beginnt in beiden bei 64 px, Eingabe- und Ergebnisspalte liegen pixelgleich.
- ref: Pfadleiste `#breadcrumb` ausgeblendet (Startseite und Themen); zurück zur Startseite über das Logo, am Handy über „☰ Alle Themen“.
- Tests: `test_layout_rahmen.py` neu (1100/1440/1920 px), `test_ref.py` angepasst.

## ref v0.3.25 — Startseite ohne Titel

- Titel „Nachschlagewerk“ und Untertitel (`refTitle`, `refSub`) auf der Startseite entfernt; das Suchfeld (`.home-search`) steht direkt unter dem Pfad. Themenseiten behalten ihren Titel.
- Tests: test_ref.py (Startseite über Suche/Kacheln erkannt), test_fres.py (Startseite über das übersetzte Suchfeld).

## size v0.5.33 — Kopf entfernt

- Kein Seitentitel mehr (`.page-head` ausgeblendet; `#page-title`/`#page-sub` bleiben im DOM, weil `renderOut()` die Beschreibung für die Karte „Umfang und Grundlagen“ daraus liest). Oben steht direkt die Auswahl (`#pick`).
- Kein Sprachhinweis mehr in EN/FR/ES (`showLangNotice()` kehrt sofort zurück).
- Tests: test_size_i18n, test_fres, test_size_paketA/B/C (Titel per textContent), test_rechtliches erweitert.

## size v0.5.32 — Beschreibung ans Seitenende

- Die Beschreibung unter dem Seitentitel (`.page-sub`, z. B. „Bemessung nach DIN EN 1993-1-1 …“) ist oben ausgeblendet und steht jetzt in der letzten Karte unter den Rechenschritten: „Umfang und Grundlagen“ (I18N `scopeT`) mit Beschreibung und calc-Hinweis, darunter „Nicht enthalten“. Erzeugt in `renderOut()` aus `#page-sub` und `tx('z001')`.
- Test in `test_rechtliches.py` (DE/EN).

## ref v0.3.24 · size v0.5.31 · calc v0.8.19 · projekt v0.1.2 · rechtliches v0.1.0 — Veröffentlichung vorbereitet

- **Schriften lokal:** kein Google-Fonts-Link mehr; `fonts/fonts.css` mit woff2 (Inter und DM Sans variabel, latin/latin-ext, Inter zusätzlich greek), OFL-Lizenztexte daneben. Hintergrund: Abmahnungen wegen Google Fonts (LG München I, 2022).
- **rechtliches.html (neu):** Impressum nach § 5 DDG und § 18 MStV mit Platzhaltern (`PH` oben im Skript: Name, Anschrift, E-Mail, USt-IdNr., Hosting-Anbieter), Haftungsausschluss, Normen und Quellen (keine Normtexte, Auszüge, DIN-Marke), Urheberrecht, Datenschutz (localStorage, Server-Logs, Rechte), Lizenzen. Sprache aus `statiq-lang`, Umschalter oben.
- **Fußleiste auf allen Seiten:** Haftungshinweis + Link „Impressum · Datenschutz · Hinweise“; folgt `<html lang>` per MutationObserver, im Druck ausgeblendet; `statiqDisclaimer()` liefert den Satz für Berichte (calc, size, projekt hängen ihn an). In calc steht der Code im Hauptskript (Node-Harness liest `<script>…</script>` gierig).
- **Normtabellen in ref entschärft:** EN 338 nur C16/C18/C24/C27/C30, EN 14080 nur GL24h/28h/30h/32h und GL24c/28c (Daten vollständig für die Rechner); Nutzlasten Tab. 6.1DE als Auszug (14 Kategorien); Sohlwiderstand DIN 1054 ohne Zwischenstufe 1,5 m. Elf weitere Normtabellen tragen den Hinweis „Eigene, gekürzte Darstellung nach der genannten Norm; maßgebend ist der Normtext.“
- Tests: `test_rechtliches.py` neu; `test_ref.py` an die Auszüge angepasst.

## ref v0.3.23 · size v0.5.30 · calc v0.8.18 — Prüfliste gegen frei zugängliche Quellen abgeglichen

Rund 90 Norm-/NA-Werte gegen Skripte, NCCI, Herstellerunterlagen, Fachaufsätze und Gesetzestext gehalten (Ergebnistabelle mit Quellen in der Prüfliste, Abschnitt „Quellenabgleich“). Korrigiert:
- **Stahl:** C₁/C₂ in ref auf NCCI SN003a (Gleichlast 1,13/0,45, Einzellast 1,35/0,63, linear als Tabelle `C1_LIN` wie in size; alte ENV-Formel 1,88 − 1,40ψ + 0,52ψ² war unsicher). β_w nach NA: S420 0,88, S460 0,85 (ref und size). S420-Legende: N/NL hat f_u = 520 bei 40–80 mm. Stirnplatte: Hinweis, dass 4m + 1,25e die untere Grenze von α·m ist. Kehlnaht √t_max − 0,5 als NCI des NA benannt.
- **Holz:** Kippen BSH mit E_0,05·G_0,05 × 1,4 (NA); size rechnet BSH jetzt mit der allgemeinen Formel (`itRect`, Funktionsdeklaration). KLED Kat. D = mittel (ref `QART.nD`). Durchbruch: Grenzen für **unverstärkte** Durchbrüche (h_d ≤ 0,15h, h_ro/h_ru ≥ 0,35h, a ≤ 0,4h), rund l_t,90 = 0,353h_d + 0,5h, Vorgabe h = 600 / h_d = 90 / h_ro = 255 / a = 200. Schwingung: Steifigkeitskriterium mit 2 kN Prüflast. k_shape nach A2 = min(1 + 0,05h/b; 1,3).
- **Beton:** Hinweis zur Fußnote Tab. 8.3DE (α₆ = 1,0 bei Stoßabstand ≥ 8Ø und Randabstand ≥ 4Ø). Betondeckung war richtig.
- **Grundbau:** HYD γ_G,stb = 0,95 (ref und size), ref-Tabelle A 2.1 um UPL/HYD ergänzt. Pfahl γ_t = 1,40 in allen BS, Einwirkungen jetzt nach BS (`PF_GQ`).
- **Wasserbau:** Abflussbeiwerte C_s nach DIN 1986-100:2016 Tab. 9, Vorgaben 1,0 / 0,9 / 0,2.
- **Mauerwerk:** Φ₁ = (1,6 − l_f/6)·a/t ≤ 0,9·a/t, Dachdecke 0,333·a/t (zweiachsig 0,4·a/t), ref und size. Ausfachung nach Tab. NA.C.1 (0–8 / 8–20 m, Zeile 150 mm, 115 mm nur bis 8 m, SFK ≥ 12 → 115/150 × 4/3, Auswahl `af-sfk` statt `af-halt`, keine Halbregel für dreiseitig). Ziegel-Schwinden 0. Hinweis 115-mm-Außenwand q_k ≤ 3 kN/m².
- **Lasten:** Schneeverwehung μ_w ≤ 4,0, NA begrenzt μ₂ = μ_s + μ_w auf 0,8 … 2,4. Wind Flachdach Bereich I +0,2/−0,6. Schneeüberhang k = 0,4 (NA).
- **Bauphysik:** Glaser-Verdunstung nach DIN 4108-3:2018 (p_i = p_e = 1200 Pa, 1700 Pa in der Tauwasserebene, Wand), δ₀ = 2·10⁻¹⁰ → `GL.Z` = 1,39·10⁶. Mindestwärmeschutz Wand zu unbeheiztem Raum 1,20. K_ij nach DIN 4109-2:2018 (K₁₂ = 5,7 + 15,4M² bzw. 4,7 + 5,7M², K₁₃ abschnittsweise). μ OSB 50, Gipskarton 10. F_C (2-fach, g > 0,40): innen weiß 0,70, Markise parallel 0,25, allgemein 0,50.
- **Offen:** f_k nach NA-Tafeln statt EN-Formel (Abweichung bis ±15 %); α aus Bild 6.11 für die Stirnplatte; S₄ (Dachfenster) im sommerlichen Wärmeschutz; Glaser-Verdunstung für Dächer (2000 Pa).
- **calc/size/Startseite:** Fehlt `projekt.html` auf dem Server, zeigt ein Klick auf „Meine Projekte“ einen Hinweis statt 404 (HEAD-Abfrage, nur http/https).
- **Werkzeug:** `retext(path, old, new, en, fr, es)` tauscht einen deutschen Text samt Schlüssel in TTX/FRES; Achtung, `old` darf nicht Teil von `new` sein. Kein `<`/`>` in übersetzten Formeltexten (innerHTML liefert `&gt;`).
- Tests: `test_pruefliste.py` (36) und `test_projekt_link.py` (8) neu; angepasst: test_ref_stahl, test_ref_holz, test_ref_grundbau, test_ref_lasten, test_ref_bauphysik, test_size_bauphysik, test_size_ext, test_size_mauerwerk, test_ref_mauerwerk, test_size_paketA/B/C.

## projekt v0.1.1 · calc v0.8.17 · size v0.5.29 — einheitlich „Meine Projekte“
- Überall „Meine Projekte“ (EN My projects, FR Mes projets, ES Mis proyectos): Startseite-Kachel, Navigation und Seitentitel von `projekt.html`, calc (Menügruppe `UXT.project`, Link in „Gespeichert“), size (Knopf `projBtn` oben, Link `projLink`). FR/ES für size in `fres-i18n/extra_ui.json`.
- Der Projektname auf der Seite („Mein Projekt“) bleibt Singular — er bezeichnet das einzelne Projekt.

## projekt v0.1.0 (neu) · calc v0.8.16 · size v0.5.28 — Positionsliste (Speichern, Variante C)
- Neue Seite `projekt.html`: Projektname, Positionen (Nr., Bezeichnung, Status, Vorschau des calc-Systems) mit ihren Einträgen aus calc (`statiq_sdf_*`) und size (`statiq-size-positionen`), dazu „Ohne Position“. Daten in `statiq-projekt` = { name, pos:[{id,nr,title}], asg:{'c:Schlüssel'|'s:Name': posId} }.
- Zuordnen je Eintrag über eine Auswahl (bestehende Position, „Neue Position“, „Aus Position lösen“). size-Einträge mit calc-Quelle folgen automatisch der Position dieser calc-Berechnung, solange sie nicht eigens zugeordnet sind.
- „Veraltet“: Liegt in der Position eine neuere calc-Berechnung als die Quelle des Nachweises, zeigt der Nachweis „calc geändert — neu rechnen“; ältere calc-Stände sind als „älterer Stand“ ausgegraut. „Neu rechnen“ öffnet `size.html#pos=Name&calc=Schlüssel(&part=…)`: Position laden, aus calc übernehmen, unter demselben Namen speichern.
- Gesamtbericht (Drucken/PDF): Deckblatt, Positionsübersicht, je Position das aktuelle calc-System (Skizze, Größtwerte, Auflagerkräfte) und die gespeicherten size-Berichte.
- Projekt als Datei sichern (`*.statiq.json`: Projekt, calc-Einträge, size-Positionen, Berichte) und wieder laden (fremde Dateien werden abgelehnt).
- size: Position speichert jetzt `src` (calc-Quelle, nur bei gleicher Nachweisart, `curTyp()`), `eta` (größte Ausnutzung), `label`, und den Bericht unter `statiq-size-bericht:Name`; `savePos` rechnet vorher neu. Adresse `#pos=…` öffnet eine Position. Link „Projektübersicht“ im Projekt-Menü.
- calc: Adresse `#report=Schlüssel` öffnet den Bericht; in „Gespeichert“ ersetzt ein Link zur Projektübersicht den Filter „size“ (blieb immer leer).
- Startseite: Kachel „Meine Projekte“ (EN My projects, FR Mes projets, ES Mis proyectos; vorher „Gespeichert“) → `projekt.html`, zählt Positionen und Einträge.
- Sprachen DE/EN/FR/ES (eigenes Wörterbuch `T` in projekt.html; FR/ES-Schlüssel für size in `fres-i18n/extra_ui.json`).

## size v0.5.27 — Momentenverlauf (C₁, ψ) beim Import aus calc
- `ciMomentVerlauf(D, beamMv)` leitet den Momentenverlauf für Stahlträger und Holz Träger/Stütze aus der Momentenlinie von calc ab. Abschnitt = Feld mit dem betragsgrößten Moment (bei einem Stützmoment das längere Nachbarfeld); L und L<sub>LT</sub> = Länge dieses Abschnitts.
- Regeln: ohne Querlast im Abschnitt → linear, ψ = M<sub>klein</sub>/M<sub>groß</sub> (exakt); Querlast ohne Endmomente → Gleichlast bzw. Einzellast (wie bisher aus den Lasten); Querlast mit Endmomenten (Durchlaufträger, Rahmenriegel) → konstantes Moment, C₁ = 1 als untere Grenze (sichere Seite); Kragarm → konstant (C₁ für gabelgelagerte Träger gilt nicht). Holz kennt „linear“ nicht → konstant.
- Hinweis im Import nennt Verlauf, Begründung und Abschnitt; die Seitenansicht markiert den Abschnitt („Abschnitt für den Nachweis“). Der alte Hinweis „für Stahl und Holz als Gleichlast angesetzt“ entfällt dort (`ciNoteDrop`).
- Folge: Durchlaufträger und Rahmenriegel rechnen jetzt mit C₁ = 1 statt 1,13 — Ergebnisse liegen etwas ungünstiger, dafür sicher.

## size v0.5.26 — Seitenansicht nach Übernahme aus calc
- Vorher zeigte die Seitenansicht nach „Aus calc übernehmen“ immer den schematischen Einfeldträger mit Feldmoment — falsch bei Kragarm, Durchlaufträger (Stützmoment maßgebend) und Rahmen.
- Jetzt: `ciSideSet()` merkt sich beim Import (Stahlträger, Holz Träger/Stütze) mit `ciSideData(sdf, C, part)` das echte System: Lager (Fest-/Loslager, Einspannung, Rahmenecken; beim Stiel Fuß und Kopf), Lasten (Strecken- und Einzellasten, beim Durchlaufträger je Feld, beim Stiel die Horizontallasten) und die Momentenlinie aus `sdf.plot`. `figSeiteCalc()` zeichnet sie samt gedrücktem Gurt/Rand nach Vorzeichen (unten bei Stütz- und Kragmomenten) und beschriftet Feld- und Stützmoment.
- Gilt, solange L und M den übernommenen Werten entsprechen (`ciSideOn`); nach einer Änderung wieder die schematische Ansicht. Legende des Querschnitts dann „Druck unten“, wenn das negative Moment überwiegt (`I.hog`).
- Import in den Stahlträger setzt L<sub>LT</sub> = Stützweite (vorher blieb der Startwert 3 m stehen), mit Hinweis.
- Kleinigkeit: bei ψ ≈ 0 keine doppelte Beschriftung „M₂ = 0“.

## size v0.5.25 — Seitenansicht Holzbauteil, Längsansicht Holz-Beton-Verbund
- Holz Träger/Stütze: `figHolzSeite(I, h)` nutzt `figTraegerSeite(…, {holz:true, lef, lefTxt})` — Holzbalken mit oberem/unterem Rand statt Gurten, gedrückter Rand blau, statt C₁ die wirksame Kipplänge l<sub>ef</sub> = Faktor·L<sub>K</sub> (+ 2h / − 0,5h je Lastangriff) wie im Kippnachweis. Nur bei M > 0; auch im Bericht.
- Holz-Beton-Verbund: `figVBSeite(I, res)` unter dem Querschnitt — Einfeldträger unter Gleichlast (schematisch aus M<sub>Ed</sub>, V<sub>Ed</sub>), Verbinder im Abstand s (bis 60 gezeichnet), nach |V(x)| eingefärbt (orange in den Randvierteln), M- und V-Linie, F₁ am Auflager wie im Nachweis.
- Erklärzeilen bei L<sub>LT</sub> bzw. L<sub>K</sub> = 0 ohne Hinweis zum Lastangriff (dort ohne Bedeutung).

## size v0.5.24 — Seitenansicht beim Stahlträger
- Unter dem Profil zeigt `figTraegerSeite(I, MV)` den Abschnitt zwischen den seitlichen Halterungen (L<sub>LT</sub>; bei L<sub>LT</sub> = 0 die Stützweite mit durchgehend gehaltenem Druckgurt): Gabellager, Belastung passend zum Momentenverlauf (Gleichlast/Einzellast mit Lastangriff Obergurt, Schwerpunkt oder Untergurt; konstant und linear als Endmomente M₁, M₂ = ψ·M₁ mit Drehsinn), gedrückter Gurt blau (oben bei M > 0, unten bei M < 0), Momentenlinie mit Werten und Nullpunkt, C₁ aus `mvWerte`.
- Erklärzeile je Fall (linear: keine Querlast, Endmomente aus anschließenden Bauteilen; konstant: ungünstigster Fall C₁ = 1; Last am Obergurt destabilisierend). Auch im Bericht (Abschnitt „Seitenansicht“). EN/FR/ES über `size-i18n/pc.json` bzw. `fres-i18n/extra_tri.json`.
- Nebenbei: „Zug“ in der Profil-Legende (N < 0) war in allen Fremdsprachen deutsch.

## calc v0.8.15 — Französisch und Spanisch vollständig
- Rechenweg (`RWT`) jetzt auch FR/ES; die festen Weichen `calcLang==='de' ? … : …` (Anteil links vom Schnitt, Felder, links/rechts, Hinweis k = I/I₀) laufen über `rwT()`-Schlüssel (`cutLeft`, `spans`, `left`, `right`, `kNote`, `with`) — vorher erschienen sie in FR/ES englisch; das „mit l′ = l/k“ in der Dreimomentengleichung war in allen Sprachen deutsch.
- Theorie-Fenster Rahmen: „(left part)“ und „corner“ stehen in eigenen Elementen (`mfs3lp`, `mfs3cn`) mit Schlüsseln `modalFrameLeftPart`/`modalFrameCorner` — waren in allen Sprachen englisch, auch im Deutschen.
- FR/ES-Überschriften in Satzschreibung statt englischer Großschreibung („Charges ponctuelles“, „Cargas distribuidas“, „Moment fléchissant M(x)“ …).
- Test `test_calc_fres.py`: Wörterbücher vollständig, alle Systeme samt Rechenweg, Rahmen-Voreinstellungen, Kopfhalterung, Durchlaufträger mit Gelenk/Kragarm, Speicherliste und Bericht in FR/ES ohne englische Reste.

## size v0.5.23 · ref v0.3.22 — Französisch und Spanisch (Sprachausbau Stufe 4, Abschluss)
- size und ref vollständig auf Französisch und Spanisch: size-Oberfläche (alle 1038 Schlüssel in `I18N.fr/es`), Rechenwege, Abbildungen, Berichte und Abhilfe; ref mit Navigation, Startseite, Suche und allen 132 Themen samt Rechnern. calc und Startseite hatten FR/ES schon.
- Technik: `TTX.fr`/`TTX.es` (Schlüssel = deutscher Text wie bei EN) stehen in einem eigenen Block `/*FRES*/Object.assign(TTX,{fr:…,es:…})/*/FRES*/` hinter dem EN-Wörterbuch; so bleiben die EN-Bauskripte unverändert nutzbar. size zusätzlich `TTR.fr/es` (Schicht-Nummern). ref: `REF_DONE[LANG]` statt nur EN, kein „DE“-Hinweis mehr.
- Zahlen: FR und ES behalten das Dezimalkomma (nur EN stellt auf Punkt um); Datum über `dLoc()` fr-FR/es-ES.
- Sprachhinweise neu: size FR/ES „Les vérifications suivent l’Annexe nationale allemande …“ bzw. „Las comprobaciones siguen el Anejo Nacional alemán …“; ref EN/FR/ES ohne „noch nicht übersetzt“.
- Übersetzt in 34 Paketen (rund 7900 Texte je Sprache) mit verbindlichem Glossar (`statiq-tools/fres-i18n/GLOSSAR.md`, Eurocode-Begriffe NF EN / UNE-EN), maschinell geprüft auf Platzhalter, HTML-Tags, Zahlen und deutsche Reste. Werkzeuge und alle Übersetzungen in `statiq-tools/fres-i18n/` (README).
- Abbildungen: `fitSvgText()` (size und ref, nur EN/FR/ES) verkleinert Beschriftungen, die durch längere Übersetzungen über den Rand der Zeichnung ragen (MutationObserver, je Bild-Frame einmal). Von Hand angepasst: Legende Fachwerk-Stabkräfte (Abstände nach Textlänge), „Lastpfad“ über den Stützweiten, Querkraft-Fachwerkmodell (zweite Legendenzeile). Prüfwerkzeug `statiq-tools/fres-i18n/overlap.py`: 0 Stellen.
- Nebenbei im Englischen behoben (vorher von den Tests nicht erkannt): „Zug“ in Vorzeichen-Skizze, Holz-Festigkeiten, Stoßtabelle und Querschnittswiderständen; Schichtzeilen in Spannungen/Erddruck geschichtet (ref); „Schicht“ im Bericht der Zeitsetzung (size).

## ref v0.3.21 — Englisch: alle übrigen Fächer (Sprachausbau Stufe 3, Abschluss)
- Übersetzt: Stahlbeton, Stahlbau, Holzbau, Mauerwerk, Grundbau, Wasserbau, Bauphysik, Mathematik — damit alle 10 Fächer (132 Themen) samt Rechnern, Rechenwegen, Skizzen und Tabellen. `REF_EN_DONE` enthält alle Fächer; Hinweis „DE“ in der Seitenleiste und `notYet` erscheinen nicht mehr.
- Code-Reste nachgezogen: unmarkierte Zweigtexte mit `tt()` umschlossen (Verbund „guter“, plastische/elastische Biegetragfähigkeit, Plastizität nach w<sub>L</sub>, freies/gespanntes Grundwasser, „freistehend: GK 1“, KLED im Holz-Rechenweg); Rechenweg-Zeilen „§Baustoff …“, „§Querschnitt …“ (Holz) und „§Nachweis (…)“ (Flankenübertragung) jetzt `_L`. Mehrzahl ohne angehängte Endung: „Nutzungseinheit/Nutzungseinheiten“, „Scherfuge/Scherfugen“ als ganze Wörter.
- Auch Texte, die mit Standardwerten nie erscheinen (rund 140 Fehlermeldungen „Bitte … eingeben“, Grenzfälle, Warnhinweise), haben jetzt eine Übersetzung; geprüft statisch über alle `tt('…')` und kurzen `_L`-Vorlagen im Code (`test_ref_i18n_code.py`).
- Begriffe: Bügel → links, mäßiger Verbund → poor bond, Gebäudeklasse → building class (BC), Nutzungsklasse → service class (SC), KLED → load duration, BSH → glulam, schießend → supercritical. Deutsche NA-Hinweise bleiben.
- Werkzeuge und alle Übersetzungsdateien in `statiq-tools/ref-i18n/` (je Fach `todo_<fach>.json` + `<fach>_eN.py`; Code-Texte direkt in `ttx_ref.json`).

## size v0.5.22 — Paket C: acht größere Themen
Mit Valentin neu abgestimmt (die ursprüngliche Liste war beim Zusammenfassen des Verlaufs verloren gegangen). Alle über die Registry `PA`:
- **Stahlbeton**: *Stütze zweiachsig* (5.8.9: M<sub>Rd,y</sub>/M<sub>Rd,z</sub> mit `stuetzeQS` bei N<sub>Ed</sub>, je Richtung zwei Lagen mit n Stäben, Seitenstäbe vernachlässigt, Exponent a linear über N<sub>Ed</sub>/N<sub>Rd</sub>; Interaktionsbild). *Platte zweiachsig* (allseitig gelenkig, Lastaufteilung und Abminderung nach Marcus, Bemessung je Richtung mit ω = 1 − √(1 − 2μ), μ ≤ 0,296, Mindestbewehrung).
- **Stahl**: *Stirnplattenstoß* bündig, eine Zugreihe (T-Stummel Modus 1–3 mit l<sub>eff</sub> = min(2πm; 4m + 1,25e), Steg auf Zug, Flansch auf Druck, M<sub>j,Rd</sub> = F<sub>Rd</sub>·h<sub>r</sub>, Querkraft in den Druckschrauben). Profilauswahl aus `PROFILE`.
- **Holz**: *Holz-Beton-Verbund* (γ-Verfahren Anhang B, E<sub>cm</sub> und E<sub>0,mean</sub>, Holz Zug+Biegung, Beton Druck, Schub, Verbinderkraft; Vergleich mit starrem Verbund).
- **Grundbau**: *Spundwand nach Blum* (Rankine, Teilsicherheiten BS-P/T, t<sub>0</sub> aus Momentengleichgewicht um den Fußpunkt, t = 1,2·t<sub>0</sub>, M<sub>max</sub> im Querkraftnullpunkt, W-Nachweis). *Pfahl axial* (q<sub>b,k</sub>, q<sub>s,k</sub> je Schicht, γ<sub>t</sub> 1,40/1,30/1,20).
- **Wasserbau**: *Brunnen* (Grundwasserabsenkung, Brunnen auf einem Kreis, Dupuit-Thiem-Überlagerung, Reichweite nach Sichardt gedämpft iteriert, Fassungsvermögen, erforderliche Entnahme).
- **Bauphysik**: *Sommerlicher Wärmeschutz* (S<sub>vorh</sub> gegen S<sub>zul</sub> = S<sub>1</sub> … S<sub>6</sub> für Wohngebäude; Tabellenwerte als Anhaltswerte gekennzeichnet).
- Werte aus dem Gedächtnis (S<sub>1</sub>-Tabelle, F<sub>C</sub>, γ<sub>t</sub>, Stirnplatten-Vereinfachungen) stehen in der Prüfliste.

## size v0.5.21 — Paket B: acht Prüfungsklassiker
Acht weitere Nachweise über dieselbe Registry `PA` (Rechenweg, Abbildung, Bericht, Abhilfe, Englisch):
- **Stahlbeton**: *Brandschutz* nach Tabellen (EN 1992-1-2: Balken statisch bestimmt Tab. 5.5 mit linearer Interpolation und a + 10 mm für Eckstäbe bei einlagiger Bewehrung; Platten einachsig Tab. 5.8; a aus Verlegemaß der Expositionsklasse oder vorgegeben). *Zugkraftdeckung* am Durchlaufträger (Gleichstreckenlast + Stützmomente, Versatzmaß a<sub>l</sub> = z·cot θ/2, verschobene Zugkraftlinie, Staffelung mit l<sub>bd</sub>, Länge der Stützbewehrung, ≥ 25 % bis über die Auflager; Abbildung mit Zugkraft- und Deckungslinie).
- **Stahl**: *Zugstab* mit Lochschwächung (N<sub>pl,Rd</sub>, N<sub>u,Rd</sub> = 0,9·A<sub>net</sub>·f<sub>u</sub>/γ<sub>M2</sub>, Blockversagen V<sub>eff,1,Rd</sub> als Minimum aus Block innen und Randstreifen, Abstände Tab. 3.3). *Stumpfnaht* durchgeschweißt (Blechquerschnitt, σ am Rand bzw. σ<sub>v</sub> in der Mitte) und nicht durchgeschweißt (richtungsbezogen mit β<sub>w</sub>).
- **Holz**: *Querzug* am Queranschluss (NA-Formel k<sub>s</sub>·k<sub>r</sub>·(6,5 + 18α²)·(t<sub>ef</sub>·h)<sup>0,8</sup>·f<sub>t,90,d</sub>, k<sub>r</sub> = 1, kein Nachweis bei α > 0,7, EN-Formel 8.4 zum Vergleich), *Durchbruch* (NA NCI NA.6.7: F<sub>t,V,d</sub> + F<sub>t,M,d</sub> gegen 0,5·l<sub>t,90</sub>·b·k<sub>t,90</sub>·f<sub>t,90,d</sub>, Grenzen, Schub und Biegung im Restquerschnitt), *Doppelbiegung* einer gekippten Pfette (k<sub>m</sub> = 0,7, k<sub>h</sub> je Achse, Schub quadratisch).
- **Mauerwerk**: *Ausfachungswand* (zulässige Fläche nach Dicke 115/175/240/≥ 300 mm, ε linear 1 … 2, Höhe über Gelände, dreiseitig halber Wert). Karte „Mauerwerk“ dort ausgeblendet.
- Verteiler: `runStahl` und `runMauer` fragen jetzt auch `PA`; Seitentitel-Schlüssel um Stahl und Mauerwerk ergänzt; Positionen speichern Stahl-Modi als `stahl_<modus>`.
- Werte aus dem Gedächtnis (Tabellen EN 1992-1-2, NA-Formeln Querzug/Durchbruch, Ausfachungstabelle) stehen in der Prüfliste als „hoch“.

## size v0.5.20 — Paket A: elf neue Nachweise
Elf Nachweise, deren Formeln schon in statiq·ref stehen, sind jetzt eigene Modi mit Rechenweg, Abbildung, Bericht, Abhilfe und Englisch:
- **Stahlbeton** (Bauteil-Knöpfe): *Torsion* — Ersatzhohlkasten (t<sub>ef</sub> = max(A/u; 2c), c aus Betondeckung), Druckstreben quadratisch mit V<sub>Rd,max</sub> (NA, ν = 0,525·ν<sub>2</sub>), Bügel je Schenkel a<sub>sw,T</sub> + a<sub>sw,V</sub>/2 (z = 0,9d), A<sub>sl</sub>, Regeln 9.2.3 (s ≤ u<sub>k</sub>/8, Längsstäbe ≤ 350 mm). *Übergreifungsstoß* — f<sub>bd</sub>, l<sub>b,rqd</sub>, α<sub>1</sub> (Haken 0,7), α<sub>6</sub> nach Tab. 8.3DE, l<sub>0,min</sub>, Zuschlag a − 4Ø, Querbewehrung bei Ø ≥ 20 und > 25 % gestoßen (ΣA<sub>st</sub> = ⌊l<sub>0</sub>/s⌋·A).
- **Holz**: *Abbrand* (EN 1995-1-2, reduzierter Querschnitt, β<sub>n</sub> 0,8/0,7, k<sub>0</sub>, k<sub>fi</sub>, Biegung und Schub mit k<sub>cr</sub>) und *Schwingung* (f<sub>1</sub> = π/(2ℓ²)·√(EI/m), w(1 kN) mit b<sub>ef</sub> aus dem Estrich, Deckenklassen I: 8 Hz/0,5 mm, II: 6 Hz/1,0 mm). Material aus der gemeinsamen Karte `#ho-x`; Nutzungsklasse/KLED dort ausgeblendet.
- **Grundbau**: *Hydraulischer Grundbruch* (HYD, Sickerweg vereinfacht L = Δh + 2t oder eigener Wert, erforderliches t), *Zeitsetzung* (Terzaghi-Reihe, Restsetzung nach Nutzungsbeginn, Wartezeit, t<sub>50</sub>/t<sub>90</sub>), *Böschungsbruch* (unendliche Böschung, GEO-3, trocken/hangparallel, steilste Neigung — erste Überschreitung von μ = 1, weil μ mit c′ bei sehr steilen Neigungen wieder fällt). Karte „Baugrund“ bei HYD und Zeitsetzung ausgeblendet.
- **Wasserbau**: *Druckstoß* (a, T<sub>r</sub>, Joukowsky bzw. Michaud, p<sub>max</sub> gegen PN, nötige Schließzeit), *Pumpe* (H<sub>A</sub>, Leistung, NPSH<sub>A</sub> mit Dampfdruck nach Temperatur, Zuschlag 0,5 m, zulässige Saughöhe), *Teilfüllung* (Kreisabschnitt, Manning-Strickler, h/D iterativ, Druckabfluss über Q<sub>max</sub> ≈ 1,076·Q<sub>v</sub>, Mindestgeschwindigkeit).
- **Bauphysik**: *Gebäudeklasse* (MBO § 2, `gebaeudeklasse`/`GK_ANF` wie ref) und Feuerwiderstand tragender Wände/Stützen gegen die Anforderung; Hochhaus > 22 m außerhalb.
- Technik: Registry `PA['bereich/modus'] = { rd, va, na, fg, line, nicht, title, norm, rows, ref, pre }`, gemeinsam `runPA()` und `buildReportPA()`; die vorhandenen Verteiler (`runBeton`, `runHX`, `runGrund`, `runWasser`, `runBauph`, `buildReport`) rufen zuerst `PA`. Seitentitel aus `PA_HEAD`. Abhilfe über `Object.assign(FIX_LEVERS/FIX_WHY, …)`. `fixSearch` prüft nach dem Runden zusätzlich einen Rasterschritt näher am Ausgangswert (vorher konnte ein Vorschlag eine Stufe zu groß sein).
- Englisch: Wörterbuch-Ergänzungen in `statiq-tools/size-i18n/pa.json`; nebenbei behoben: der Baustoff-Hinweis „mindestens …“ unter den Betonklassen war im Englischen deutsch.
- „Nicht enthalten“ in Stahlbeton, Holz, Setzung und Rohrleitung verweist jetzt auf die neuen Modi.

## size v0.5.19 — Abhilfe: warum ein Nachweis nicht erfüllt ist und wie er erfüllt wird
- Unter jedem nicht erfüllten Nachweis erscheint ein Kasten: **Warum nicht erfüllt?** (Ursache in einem Satz aus `FIX_WHY`, Schlüssel „Bereich:id“, dazu η) und **So wird der Nachweis erfüllt** mit berechneten Werten, z. B. „Höhe h [mm]: 290 (statt 220) · damit sind alle Nachweise erfüllt [Übernehmen]“.
- Rechenweg: Je Modus listet `FIX_LEVERS` die Stellschrauben (Abmessungen, Baustoff, Profil, Abstände; keine Lasten). `computeFix` probiert sie einzeln durch: Zahlen werden vergrößert (bzw. verkleinert) bis der Nachweis erfüllt ist, dann halbiert und auf das Raster gerundet; Auswahllisten werden in Listenreihenfolge durchlaufen. Gerechnet wird mit den echten Rechenkernen: `PROBE` lässt `renderOut`/`showBad` nur die Nachweise merken. Danach werden alle Eingaben, `LAST` und Hinweise wiederhergestellt. Ausgeblendete oder gesperrte Felder (z. B. Bewehrung bei „automatisch“) werden nicht angefasst; Zeitgrenze 2,5 s.
- „Übernehmen“ setzt den Wert und rechnet neu. Im Bericht steht die Abhilfe unter dem Nachweis (`fixRep`). Englisch über `TTX`/I18N.
- Findet keine einzelne Stellschraube eine Lösung, sagt der Kasten das (mehrere Größen zugleich ändern oder Einwirkungen prüfen).

## ref v0.3.20 — Englisch: Navigation, Baustatik und Lastannahmen (Sprachausbau Stufe 3, Teil 1)
- Navigation vollständig englisch: Titel von Fach, Kapitel und Thema werden beim Laden aus `TTX.en` ersetzt (Schlüssel/Adressen bleiben deutsch), dazu Startseite, Seitenleiste, „On this page“, Vor/Zurück, Suche (Index aus übersetzten Inhalten), `<html lang>`.
- Inhalte: Code-Texte wie in size mit `tt()`/`_L` (einmalig per AST markiert; CONTENT, FAECHER, SEARCH_EXTRA, I18N ausgenommen). Seiteninhalte werden nach dem Aufbau übersetzt: `trRef(root)` zerlegt in Inline-Läufe (`refUnits`: zusammenhängender Text mit sub/b/br/a … innerhalb eines Elements) und schlägt deren normalisiertes HTML in `TTX.en` nach; sonst einzelne Textstücke, im Englischen Dezimalpunkt. Ein `MutationObserver` auf `#main` übersetzt nachträglich geänderte Rechnerausgaben (eigene Änderungen werden mit `takeRecords` verworfen, Übersetzung = Schlüssel wird übersprungen).
- Übersetzt: Baustatik (16 Themen) und Lastannahmen (7 Themen) samt Rechnern, Rechenwegen und Skizzen. `REF_EN_DONE` listet die fertigen Fächer; die übrigen tragen in der Seitenleiste „DE“ und auf ihren Seiten den Hinweis `notYet`.
- Werkzeuge für die nächsten Fächer: `statiq-tools/ref-i18n/` (README: sammeln → Pakete → übersetzen → einbauen → prüfen).
- Nächste Fächer in dieser Reihenfolge: Stahlbeton, Stahlbau, Holzbau, Mauerwerk, Grundbau, Wasserbau, Bauphysik, Mathematik.

## size v0.5.18 — Rechenwege, Abbildungen und Berichte auf Englisch (Sprachausbau Stufe 2)
- Alle Texte im Code sind markiert (einmalig per AST-Skript, Deutsch bleibt Zeichen für Zeichen gleich): feste Texte `tt('…')`, Texte mit Werten als Tagged Template `_L\`… ${x} …\``. Schlüssel = deutscher Text, bei `_L` mit `{}` an den Stellen der Werte; die Übersetzung darf `{0}`, `{1}` … zum Umstellen nutzen (z. B. Mehrzahl „Schicht{}“ → „layer(s)“).
- Wörterbuch `TTX.en` (rund 1630 Einträge) direkt nach `applyI18n`. Werte, die `_L` einsetzt, laufen auch durch `tt` — so werden Tabellennamen (KLED, Bodenarten, Bauteile nach DIN 4109-1, BP_RS/BP_ANF) übersetzt, ohne die mit ref geteilten Tabellen zu ändern.
- `trFig(html)`: übersetzt in Abbildungen, Rechenwegen, Ergebnistabelle, Ergebniszeile und Bericht einzelne Textknoten und setzt im Englischen den Dezimalpunkt auch in festen Formeltexten (Attribute wie SVG-Koordinaten bleiben unberührt). `deNum`, `dk` und die Glaser-Werte geben im Englischen Punkt aus; Datum im Bericht über `dLoc()`.
- Neue deutsche Texte im Code bitte gleich mit `tt()`/`_L` schreiben und in `TTX.en` eintragen — `test_size_i18n.py` meldet sonst deutsche Reste in allen 31 Nachweisen und im Bericht.
- Hinweis auf Englisch: alles englisch, Nachweise nach deutschem NA, deutsche Normverweise bleiben.

## size v0.5.17 — Oberfläche auf Englisch (Sprachausbau Stufe 1)
Plan (mit Valentin abgestimmt): 1. size-Oberfläche EN · 2. size-Rechenwege und Berichte EN · 3. ref EN (erst Navigation/Titel, dann Fach für Fach) · 4. FR/ES. Begriffe: englische Eurocode-Begriffe, deutsche NA-Hinweise bleiben.
- Statische Texte: 476 Elemente und 15 Textstellen tragen `data-i18n="zNNN"` bzw. sprechende Schlüssel; `I18N.de` hat 687 Schlüssel, `I18N.en` alle davon. Deutscher HTML-Text = `I18N.de` (Test), Deutsch bleibt dadurch unverändert.
- Dynamische Texte: `tx(key, …)` mit {0}-Platzhaltern für Meldungen mit Zahlen (Zusammenfassung, Mobilstatus, Kennzeichen erfüllt/nicht erf./Info, „Nicht enthalten“, Rechenschritte-Leiste, Positionen, calc-Import, „n Themen“).
- Feste Texte aus dem Code (Seitentitel/Untertitel/Abbildungstitel aus `showMat`, wechselnde Feldbeschriftungen, Expositionsklassen, System für l/d, `TYP_NAME`, Eingabefehler aus `validate*`, calc-Import-Hinweise, Beispielnamen): `tt(deText)` schlägt in `TTX[LANG]` nach (deutscher Text = Schlüssel), Regeln in `TTR` für „Schicht n“. Ohne Eintrag bleibt der Text deutsch.
- `applyI18n` setzt außerdem `<html lang>`, übersetzt `aria-label`/`title` in der Eingabespalte und unveränderte Beispielnamen; Datum in Positionen und calc-Auswahl über `dLoc()` (en-GB usw.).
- Noch deutsch (Stufe 2): Nachweistitel, Rechenschritte, Ergebniszeile (`reinf-line`), „Nicht enthalten“-Texte, Abbildungsbeschriftungen, Bericht; Zahlen weiter mit Dezimalkomma. Der EN-Hinweis (`langNotice`) sagt das.
- Werkzeuge im Arbeitsordner: `i18n/audit_en2.py` (alle Modi, alle Auswahlfelder durchschalten, deutsche Reste suchen).

## ref v0.3.19 und size v0.5.16 — Flankenübertragung nach DIN 4109-2
- Kern (ref und size gleich): `kStoss(art, m⊥, mi)` (starre Kreuz-/T-Stöße, DIN 4109-32), `flankenR({mD, S, d, RDdPlus, F})` — R<sub>Dd</sub> plus je Flanke Ff/Df/Fd, K<sub>ij</sub> ≥ K<sub>ij,min</sub> (S<sub>f</sub> = l<sub>f</sub> · Raumtiefe), energetische Summe über 13 Wege, Anteile je Weg; `kTritt(mDecke, mfm)` = 0,6 + 5,5·lg(m′/m′<sub>f,m</sub>) ≥ 0
- ref: neues Thema „Flankenübertragung (DIN 4109-2)“ mit Wege-Skizze `skFlanken`, Rechner `updateFL` (Tabelle aller Flanken, größter Flankenweg); Trittschall-Rechner berechnet K aus m′<sub>f,m</sub> (0 = K von Hand)
- size: Schallschutz mit Auswahl `bs-fl` genau (Standard) / pauschal; Felder `bf-S`, `bf-d`, `bf-dR`, `bf-m/l/a1…4`; im genauen Modus K für Trittschall aus dem Mittel der vier Flanken

## ref v0.3.18 und size v0.5.15 — Bauphysik (neues Fach)
- Gemeinsame Rechenkerne in ref und size (identisch, der Test vergleicht sie): `BP_MAT` (28 Baustoffe mit λ, μ, ρ), `BP_RS` (R<sub>si</sub>/R<sub>se</sub>), `BP_ANF` (DIN 4108-2 R<sub>min</sub>, GEG-Referenz- und Bestandswerte), `bpWaerme`, `bpTemperaturen`, `psat`/`taupunkt` (Magnus nach DIN 4108-3), `glaser` (untere konvexe Hülle `bpHull` = Tangentenkonstruktion; Tauperiode 2160 h 20/50 % und −5/80 %, Verdunstung 2160 h 20/50 % und 12/70 %, Z = 1,5·10⁶), `rwMasse` (DIN 4109-32), `f0Zweischalig`, `lnEq`, `dLwEstrich`, `BP_SCHALL` (DIN 4109-1), `gebaeudeklasse` + `GK_ANF` (MBO)
- ref: Fach `bauphysik` (Tag BPh, vor Mathematik) mit Wärmeschutz (Kennwerte mit Filtertabelle, U-Wert-Rechner `updateUW` mit Skizze `skBauteil`, Anforderungen und Wärmebrücken), Feuchteschutz (Taupunkt `updateTP`, Glaser `updateGL` mit Diagramm `skGlaser`), Schallschutz (Grundlagen, Luftschall `updateLS` mit f<sub>0</sub>, Trittschall `updateTS`), Brandschutz (Klassen, Gebäudeklassen `updateGK`). Schichteingabe `bpSchichtFelder`/`bpLesen`, CSS `.bp-row`
- size: Bereich `bauph` mit `BPMODE` uwert / glaser / schall; gemeinsame Schichtkarte (Felder `bl-m/d/l/u/r1…6`, λ μ ρ überschreibbar, `bpPick`), Nachweise `nachweiseBU/BG/BS`, Bilder `figBU/BG/BS`, Bericht `buildReportBauph`, Speichern/Positionen/Menü eingebunden. Schall vereinfacht: R′<sub>w</sub> ≈ R<sub>w</sub> − Flankenabschlag (Eingabe), dazu u<sub>prog</sub>
- Startseite: Beschreibungen und Schlagworte um Bauphysik ergänzt (alle vier Sprachen)

## ref v0.3.17 — Lastannahmen ausgebaut (Stufe 7c, Abschluss Stufe 7)
- Schnee: Lastanordnungen und Sonderfälle (Satteldach, Überhang, Schneefanggitter), Verwehung am Höhensprung `hoehensprung`/`updateHS` mit Skizze `skHoehensprung` (μ<sub>w</sub> ≤ γh/s<sub>k</sub>, 0,8 ≤ μ<sub>w</sub> ≤ 2,4 nach NA — Konstante `SN_MUW_MAX`, μ<sub>s</sub>, l<sub>s</sub> = 2h in 5 … 15 m); nutzt die vorhandenen `schneeSk`, `schneeMu1`
- Wind: Flachdach F/G/H/I, c<sub>pe,1</sub>/c<sub>pe,10</sub>-Interpolation, Innendruck; Rechner Windbereiche `windZonen`, `cpeWand` (Interpolation in h/d), `updateWB` mit Draufsicht `skWindZonen`
- Neues Thema Lastweiterleitung (`lastAbtrag`, `updateLW`, `skLastabtrag`): Innenwand unter Zweifelddecken mit/ohne Durchlaufwirkung, Summe über n Geschosse, GZT mit Nutzlast bzw. Schnee führend
- Formatierer `dL` (echtes Minus) im Lasten-Block

## ref v0.3.16 — Baustatik ausgebaut (Stufe 7b)
- Durchlaufträger: Dreimomentengleichung `dltRechnung(n, loads, L)` (Thomas-Algorithmus), Laststellungen durchprobiert `dltExtrem(n)`, Beiwerttabellen für 2–5 Felder (Volllast und Extremwerte, `dltTabelle`), Bemessungsrechner g + q mit Skizze (`updateDLT`, `skDLT`); das Feldmoment wird für den echten Lastfall berechnet, die Beiwertsumme nur als Vergleich
- Neue Themen: Einflusslinien (`updateEL`, `skEL`), Fachwerke mit Ritterschnitt (Parallelträger, `fachwerk`, `updateFW`, Skizze `skFW` — Achtung: `skFachwerk` ist das Stahlbeton-Fachwerkmodell), Dreigelenkrahmen und -bogen (`dreigelenk`, `updateDGR`, `skDreigelenk` mit Momentenlinie), Kraftgrößenverfahren (Zweifeldträger mit Koppeltafel, `kgvZweifeld`, `updateKGV`)
- Querschnittswerte: Steiner-Rechner für bis zu 4 Rechtecke (`steinerRechnung`, `updateSteiner`, `skSteiner`), Tabelle um Halbkreis, dünnwandiges Rohr und Trapez ergänzt
- Formatierer `dS` (echtes Minuszeichen) für den Baustatik-Block; Test prüft jetzt auch, dass keine Funktion doppelt definiert ist

## ref v0.3.15 — Mauerwerk als neues Fach (Stufe 7a)
- Neues Fach `mauerwerk` (Tag EC6) zwischen Holzbau und Grundbau: Baustoffe (Steine und Formate mit Skizze `skMWFormat`, f<sub>st</sub> = 1,25 · SFK; Maßordnung mit Rechner `updateMass`; Mörtel und Verband; Druckfestigkeit f<sub>k</sub> nach EN-Formel mit K-Tabelle, Rechenwerte K<sub>E</sub>/φ/ε/α<sub>t</sub> `MWR_RW`, Rechner `updateFk`) und Bemessung (Knicklänge ρ<sub>2</sub>/ρ<sub>3</sub>/ρ<sub>4</sub> mit 15t/30t-Grenze `mwRhoN`, `updateHef`, Skizze `skMWHalt`; Wand unter Druck `updateMWD` mit Skizze `skMWAuflager`; Teilflächenpressung `updateMWT`; Kellerwand `updateMWK`; Schubwand `updateMWS`)
- Rechenkerne identisch mit statiq·size (`MWR_K`/`MWR_ART` = `MW_K`/`MW_ART`; γ<sub>M</sub> = 1,5, ζ = 0,85, kurze Wand f<sub>d</sub> · 0,8) — der Test vergleicht ref, Python und size

## ref v0.3.14 — Wasserbau als Nachschlagewerk (Stufe 6)
- Neue Kapitel: Grundlagen (Stoffwerte von Wasser 0–100 °C `WASSER`/`wasserBei`, Kennzahlen Re/Fr/We/Eu/St mit Rechner `updateKZ`), Grundwasser (Brunnen Dupuit-Thiem, Sichardt, `updateBrunnen`), Hydrologie (Regenabfluss mit ψ-Tabelle `PSI`, `updateRegen`); neue Themen Pumpen (`updatePumpe`, NPSH mit Dampfdruck aus der Stoffwertetabelle), Druckstoß (`updateDruckstoss`, Joukowsky, Reflexionszeit, Michaud), Wechselsprung (`updateSprung`, Skizze `skSprung`), Teilgefülltes Kreisrohr (`kreisTeil`, `updateTeil`, Skizze `skTeil` mit Teilfüllungskurven)
- Rohrreibung: `lamColebrook`, `lamSwamee`, Temperatur und Σζ als Eingabe, Moody-Diagramm `skMoody` mit Betriebspunkt, erweiterte ζ-Tabelle; h<sub>v,R</sub> jetzt mit 3 Nachkommastellen
- Ausfluss: Rechner mit Entleerungszeit (`updateAusfl`); Grenztiefe: Rechner Rechteck/Trapez (`grenztiefe`, `updateGrenz`)
- `updateManning`, `updateRohrR`, `updatePoleni` geben den Rechenweg mit `ablauf()` aus

## ref v0.3.13 — Grundbau als Nachschlagewerk (Stufe 5)
- Neue Kapitelstruktur: Boden (Kennwerte, Bodengruppen und Plastizität, Bodenphysik, Scherfestigkeit, Grundwasser) · Spannungen und Setzungen (Spannungen, Setzungen — Pfad jetzt `grundbau/verformung/setzung`, Konsolidation) · Erddruck (Beiwerte, Coulomb und geschichteter Boden) · Flachgründungen (Sohldruck, Grundbruch, Sohlwiderstand) · Böschungen
- Rechner mit Rechenweg: `updatePhasen` (w, ρ, n, e, S<sub>r</sub>, Wichten, I<sub>D</sub>, I<sub>C</sub>), `updatePlast` (A-Linie, Skizze Plastizitätsdiagramm), `updateMohr` (c′, φ′ aus zwei Triaxialversuchen, Mohrkreise), `updateDarcy` (Darcy + HYD), `updateSpann` (σ, u, σ′ geschichtet, Skizze), `updateSetz` (Steinbrenner Mittelpunkt, Grenztiefe 20 %, Tabelle), `updateKons` (Terzaghi-Reihe, t<sub>50</sub>/t<sub>90</sub>), `updateCoulomb` (K<sub>agh</sub>, K<sub>pgh</sub>, K<sub>ach</sub>), `updateErdS` (geschichtet mit GW, Skizze), `updateSohldruck`, `updateGB` (DIN 4017 wie size: `gb4017`), `updateBoesch` (unendliche Böschung, GEO-3)
- γ<sub>w</sub> = 10 kN/m³ in Spannungen, Erddruck, Darcy, Böschung (`GW_W`); in der Bodenphysik γ = ρ · 9,81

## ref v0.3.12 — Stahlbeton als Nachschlagewerk (Stufe 4)
- Alle neun bisherigen Rechner (Deckung, Biegung, Querkraft, Verankerung, Biegeschlankheit, Plattenbalken, Durchstanzen, Rissbreite, Stütze) geben jetzt den Rechenweg mit `ablauf()` aus; die Rechenkerne (`biegeAusMu`, `querkraft`, `durchstanzen`, `rissbreite`, `stuetzeBerechne` …) sind unverändert
- Neu: „Kriechen und Schwinden“ (`kriechen`, `updateKS`, Anhang B mit Zementart, k<sub>h</sub> interpoliert), „kd-Verfahren“ (`kdTafel` für C20–C50 aus dem Parabel-Rechteck-Diagramm, `updateKD`), „Torsion“ (`updateTor`, Ersatzhohlkasten, ν = 0,525·ν<sub>2</sub>, quadratische Interaktion mit Querkraft), „Matten, Biegerollen, Übergreifung“ (Lagermatten, Tab. 8.1DE, α<sub>6</sub>)
- Betonseite: hochfester Beton C55–C90 (`HOCHFEST`, Werte aus Tab. 3.1, Grenzdehnungen aus den Formeln)

## ref v0.3.11 — Holzbau als Nachschlagewerk (Stufe 3)
- **Baustoffe:** neue Themen „Querschnittswerte Vollholz, KVH, BSH“ (`QS_VH` 75 Kanthölzer mit KVH-Vorzugsmaßen •, `QS_BSH` 232 BSH-Querschnitte, Auswahl der Breite per Chip, `qsTable`, `rectProps`; I<sub>t</sub> exakt per Saint-Venant-Reihe `itRect`) und „Beiwerte“ (k<sub>h</sub>, k<sub>cr</sub> nach NA, k<sub>c,90</sub>, k<sub>m</sub>, β<sub>c</sub>, k<sub>sys</sub>, k<sub>shape</sub>, k<sub>fi</sub>, Abbrandraten)
- **Nachweise mit Rechenweg:** `updateHEF` Einfeldträger komplett (maßgebende LK über q<sub>d</sub>/k<sub>mod</sub>, Biegung mit k<sub>h</sub>, Schub mit k<sub>cr</sub>, Auflagerpressung mit l<sub>ef</sub> = l + 30 mm, w<sub>inst</sub>/w<sub>fin</sub>/w<sub>net,fin</sub> mit k<sub>def</sub> und ψ<sub>2</sub>); `updateHKN` Knicken mit Biegung (6.23/6.24); `updateHKI` Kippen (VH vereinfachte Formel 6.32, BSH allgemein mit G<sub>0,05</sub> = 540); `updateHWI` Druck unter Winkel (6.16); `updateHBR` Abbrand (EN 1995-1-2, reduzierter Querschnitt)
- Gemeinsam: `holzMat(cls)`, `khOf`, `kcrOf`, `selHolz`, `selNkl`, `selKled`, `QART` (Nutzlast/Schnee/Wind mit KLED und ψ)
- Offen im Holzbau: Laubholz-Klassen (EN 338 D), Querzug, Durchbrüche, Schwingungsnachweis nach NA, Verbindungen weiter ausbauen

## ref v0.3.10 und size v0.5.14 — Beispielrechnungen, Gleiten, Schwimmkörper
- **ref, Lastannahmen › Kombinationsregeln:** Beispiel 1 Stütze mit G, Nutzlast, Schnee, Wind (`kombiRechnung`, `KB`): jede veränderliche Last einmal führend, GZG charakteristisch/häufig/quasi-ständig; Beispiel 2 Träger mit Kragarm (`kragRechnung`, `KR`): max Feldmoment, Stützmoment, Abheben (EQU). Skizzen `skKombiStuetze`, `skKrag`
- **ref, Stahlbau › Querschnittsklassen:** Rechner für geschweißte I-Querschnitte mit ungleichen Gurten (`zqGeom`, `zqKlasse`, `updateZQ`, Skizze `skZQ` maßstäblich mit elastischer und plastischer Nulllinie); c bis Nahtfuß (√2·a), α aus plastischer NL, ψ aus elastischer
- **ref, Mathematik › Gleichungen:** Beispiel quadratische Gleichung (Druckzonenhöhe Zustand II, Parabelskizze), Cramer 2×2 (Fachwerkknoten, Skizze), Gauß 3×3 mit eigenen Werten, Zeilentausch, Determinante, Probe (`gaussSchritte`, `updateGauss`)
- **size, Grundbau › Gleiten (neuer Modus):** `readGL`/`nachweiseGL`/`figGL`/`runGL`/`buildReportGL`, BS-P/T/A (`GL_F`), Ortbeton δ = φ′ bzw. Fertigteil 2/3 φ′ (δ ≤ 35°), dräniert/undräniert (c<sub>u</sub>, Hinweis 0,4·V), Erdwiderstand wahlweise 50 % mit γ<sub>R,e</sub>
- **size, Wasserbau › Schwimmen:** fünf Formen (`WS_FORM`): Quader, Trapezprisma (auch Keil), stehender und liegender Zylinder, Kugel. `wsGeo` liefert V(T), z<sub>B</sub>(T), I<sub>W</sub>(T); Tiefgang per Bisektion; Untergang wird erkannt; Beispielwerte beim Formwechsel (`wsPreset`)

## ref v0.3.9 — Stahlbau als Nachschlagewerk (Stufe 2)
- **Profildaten:** nur noch Nennmaße im Code (`I_DIMS` IPE/HEA/HEB/HEM bis 1000, `UPN_DIMS`, `UPE_DIMS`, `L_DIMS`, `SHS_DIMS`, `RHS_DIMS`, `CHS_DIMS`); alle Werte werden berechnet und liegen in `PROF[name]` (volle Genauigkeit, Einheiten cm). `PROFILE` (alte 16-Spalten-Form, gerundet) und `I_EXT` werden daraus erzeugt
  - I-Profile: Herstellerformeln (`iProps`) inkl. A_vz, I_t, I_w
  - U und L: Polygon mit Ausrundungen (`roundPoly`) + Gauß-Integration (`polyProps`), W_pl per Halbierungslinie (`wplY`). UPN: Neigung 8 % mit t_f in b/2 (h ≤ 300), 5 % mit t_f in (b+s)/2 (h > 300)
  - Hohlprofile EN 10210: `rhsProps` (r_o = 1,5t, r_i = t), `chsProps`
- **Themen:** Profiltabellen (I, U, Winkel, Hohlprofile, Tabellen mit festem Kopf und Filter), Querschnittsklassen, Querschnittswiderstände, Biegeknicken, Biegedrillknicken, Biegung und Druck (Anhang B), Durchbiegung, Schrauben, Schweißnähte
- **Rechner mit Rechenweg** (`ablauf`): `updateSteckbrief`, `updateQK`, `updateQN`, `updateKnick`, `updateBDK`, `updateNMI`, `updateDurchb`, `updateSchraube`, `updateKehl`; gemeinsame Bausteine `klassifiziere`, `knickLinie(name, achse, stahl)` (Tab. 6.2 inkl. S460, t_f > 40), `chiOf`, `mcrOf`, `chiLT` (6.3.2.3 mit f)
- `STAHL` um S420 ergänzt; f_y je nach Flanschdicke (`stFy`)
- size-Tests (`test_size_stahl`, `test_size_ext`) lesen die Profiltabelle jetzt aus size.html; `run_all.py` wertet abgebrochene Testdateien als Fehler
- Offen im Stahlbau: IPN, T-Profile, ungleichschenklige Winkel, kaltgefertigte Hohlprofile; Biegedrillknicken nur für doppeltsymmetrische I-Profile mit Gabellagerung

## ref v0.3.8 — Startseite
- Ab 1000 px (Themenbaum sichtbar) zeigt die Startseite nur Titel, Suche und einen kurzen Hinweis; die Fach-Kacheln (`.home-tiles`) erscheinen nur noch am Handy, wo der Themenbaum eingeklappt ist

## ref v0.3.7 — neues Layout (Stufe 1 des Ausbaus zum Nachschlagewerk)
- Drei Spalten ab 1000 px: Themenbaum links (Filterfeld `#side-q`, offene Fächer in `localStorage['statiq-ref-open']`), Inhalt, ab 1300 px „Auf dieser Seite“ (`renderToc`, Karten bekommen ids `s-…`, IntersectionObserver markiert den sichtbaren Abschnitt)
- Unter 1000 px: Knopf „☰ Alle Themen“ öffnet den Themenbaum als Überlagerung (`toggleSideMenu`)
- Themenseiten mit Vor/Zurück-Leiste `.topic-pager`; alter Pager ausgeblendet
- Bausteine für die folgenden Stufen: `ablauf(titel, ['§Schritt', '!Hinweis', 'Formelkette …'])` setzt Nachweise Schritt für Schritt (Formelketten über `eqLine` zeilenweise, „=“ untereinander); `filterBox(id, platzhalter)` + `tableFind` filtern lange Tabellen; `.data-table-wrap.tall` mit festem Tabellenkopf
- `eqLine` (in calc, size, ref gleich): „ · Name“ vor einem „=“ gilt nur noch als neue Zuweisung, wenn danach ein reines Formelzeichen steht („q · l² / 8“ ist jetzt eine Rechenkette)
- Plan der Stufen: Stahlbau → Holzbau → Stahlbeton → Grundbau → Wasserbau → Mauerwerk/Baustatik/Lasten — mit v0.3.17 alle sieben Stufen umgesetzt

---

## Tests (`statiq-tests/`)
Alles auf einmal: `python3 statiq-tests/run_all.py` (braucht Node, Python 3 und numpy).
- `harness.js` — Rahmen: extrahiert die Solver-Funktionen aus calc.html, führt `calculateFrame()` in Node aus
- `harness_beam.js` — **neu**: Einfeldträger/Kragarm/DLT, führt das ganze Skript mit DOM-Stub aus
- `fem.py` — unabhängige 2D-FEM für den Rahmen; `beamfem.py` — **neu**: unabhängige 1D-FEM für Balken
- `runtests.py` (60), `runtests2.py` (15), `runtests3.py` (14) — Rahmen wie in v0.7
- `runtests_beam.py` (15) — 9 Fälle M/Q/N/w an allen Stützstellen gegen FEM (inkl. schräge Last, Moment, Trapez, ungleiche Felder, 3 Felder) und 4 Prüfungen der Anzeige (Auflagerkräfte, max M, Stützmomente)
- `runtests4.py` (14) — **neu in v0.8.1**: Gelenke an Lagern/Ecken, echter Mechanismus weiter erkannt, Positionshinweise, abgeschnittene Streckenlasten, Kragarm M max, Fehlermeldung statt Pop-up
- `test_calc_ui.py` (12) — **neu in v0.8.5**, Rahmentypen und Theorie-Fenster im Browser
- `fuzz_frame.py`, `fuzz_beam.py` — Zufallsprüfung gegen FEM (separat aufrufen)
- `runtests_report.py` (27) — **neu in v0.8.2**, im echten Browser (Playwright, sonst SKIP): je System speichern → Bericht öffnen ohne Fehler, Inhalte, Diagramme am Tragwerk, gespeichert = Stand der Berechnung, Verformung = Berechnung, Systembild; alte Speicherung öffnet mit Hinweis
- Die Harnesses stubben Meldungen und Schnappschuss: `calcError` wirft weiterhin (→ `err`), Hinweise landen in `warns` bzw. `msgs`

- `test_ref_skizzen.py` (22) — **neu in ref v0.3.6** (ab v0.3.14 Rohr mit ν(10 °C) = 1,306·10⁻⁶ und 3 Nachkommastellen): 21 Themen mit Skizzen ohne NaN/Fehler, mobil ohne Querscrollen; Momentenlinien der Balkentafel-Kacheln und der Durchlaufträger gegen unabhängiges Kraftgrößenverfahren (numpy); Eulerfall 3 (tan kL = kL); Flächenformeln per Integration

- `test_size_holz2.py` (37) — **neu in size v0.5.13**: Ausklinkung (k_v, 6 Fälle), Satteldach/Pultdach (Maximum per scipy, k_m,α, k_l, k_p, k_vol, Schub), Versatz (f_c,α aus Kraft/Fläche, t_v-Grenze, Vorholz), Bericht, Positionen, Speichern, Menü, mobil

- `test_ref_stahl.py` (27) — **neu in ref v0.3.9**: alle 90 I-Profile, 68 Hohlprofile und 22 Winkel gegen unabhängige shapely-Geometrie mit eigener Flächenintegration (A, I, W_pl, Hauptachsen); Stichproben gegen veröffentlichte Tabellenwerte (auch UPN/UPE, I_t, I_w); alle Rechner gegen Python (Klasse mit α/ψ, M–V–N, χ, M_cr auch gegen klassische Kippformel, Anhang B, Schrauben ein-/zweischnittig, Kehlnaht); 13 Seiten mobil
- `test_ref_beispiele.py` (17) — **neu in ref v0.3.10**: Lastkombinationen, Kragarm (numerisch), vier geschweißte Querschnitte gegen shapely + unabhängige Klassifizierung, Zustand II (numpy.roots), Cramer, Gauß (3 Systeme inkl. Zeilentausch, Determinante, singulär)
- `test_size_gleit_schwimm.py` (27) — **neu in size v0.5.14**: Gleiten in 6 Fällen gegen Python; Schwimmen 8 Körper gegen shapely-Querschnitte bzw. Scheibenintegration (brentq), Metazentrum im Mittelpunkt bei Kreis/Kugel, Untergang, Speichern, Bericht
- `test_ref_holz.py` (28) — **neu in ref v0.3.11**: 307 Rechteckquerschnitte (I<sub>t</sub> gegen Reihenlösung und Tabellen-β), Einfeldträger in 4 Varianten, Knicken 3, Kippen 4, Druck unter Winkel 4, Abbrand 3 — alles gegen Python
- `test_ref_stahlbeton.py` (14) — **neu in ref v0.3.12**: hochfester Beton gegen Tab. 3.1, kd-Tafel gegen numerische Integration, Kriechen/Schwinden in 4 Fällen + Nomogramm-Plausibilität, Torsion, Rechenweg in allen 12 Rechnern
- `test_ref_grundbau.py` (21) — **neu in ref v0.3.13**: Steinbrenner gegen Boussinesq-Doppelintegral, Coulomb-K<sub>agh</sub> gegen Gleitkeil-Optimierung (5 Fälle), Mohr-Gerade tangiert beide Kreise, geschichteter Erddruck per Integration, Grundbruch DIN 4017 unabhängig, Konsolidation, Bodenphysik, Plastizität (6 Böden), Sohldruck, Böschung
- `test_ref_wasserbau.py` (39) — **neu in ref v0.3.14**: Stoffwerte gegen Tanaka (ρ), Vogel (μ), Buck (p<sub>D</sub>); Colebrook an 36 Punkten gegen brentq, Swamee-Jain im Gültigkeitsbereich; Pumpe/NPSH, Joukowsky, Entleerung gegen ODE, Grenztiefe = Minimum E(h), Wechselsprung per Stützkraft, Teilfüllung per numerischer Integration, Dupuit, Regen; 17 Seiten Desktop + mobil
- `test_ref_mauerwerk.py` (16) — **neu in ref v0.3.15**: f<sub>k</sub> in 36 Kombinationen, Maßordnung, Knicklänge in 10 Fällen, Wand/Teilfläche/Keller/Schub jeweils gegen Python **und** gegen die Rechenkerne von size; 9 Seiten Desktop + mobil
- `test_ref_baustatik.py` (13) — **neu in ref v0.3.16**: Dreimomentengleichung gegen eigene Balken-FEM (12 Träger), exakte Beiwerte, Laststellungen per Durchprobieren, Bemessung g + q, Steiner gegen shapely und Streifenintegration, Fachwerk gegen Knotengleichgewicht (lstsq), Dreigelenkrahmen gegen Starrkörpergleichgewicht, Kraftgrößenverfahren gegen FEM, Einflusslinien gegen wandernde Last; doppelte Funktionsnamen
- `test_ref_lasten.py` (7) — **neu in ref v0.3.17**: Höhensprung mit allen Begrenzungen, c<sub>pe</sub>-Interpolation (25 Werte), Windbereiche flächentreu, Lastweiterleitung gegen Verträglichkeit der Durchbiegung
- `test_ref_bauphysik.py` (18) — **neu in ref v0.3.18**, ab v0.3.19 mit Flankenübertragung (3 Trennwände gegen Python, Monotonie) und Trittschall-K: U-Wert 4 Bauteile, Temperaturen, Magnus gegen DIN-Tabelle, Taupunkt, Glaser in 5 Aufbauten gegen scipy-ConvexHull (200 Punkte je Schicht) und Verdunstung, Massegesetz, f<sub>0</sub>, Trittschall, Gebäudeklassen
- `test_size_bauphysik.py` (23) — **neu in size v0.5.15**, ab v0.5.16 genauer Flankennachweis = ref: Kerne identisch mit ref, U-Wert (auch überschriebenes λ), Glaser 4 Aufbauten gegen scipy, Luft- und Trittschall, Bericht, Speichern/Laden, Handy
- `test_size_paketC.py` (43) — **neu in size v0.5.22**: alle 8 Modi gegen unabhängige Python-Rechnung (Stütze zweiachsig mit eigener Dehnungsebenen-Iteration, Marcus inkl. Vergleich mit Czerny, Stirnplatte, γ-Verfahren inkl. Grenzfall starr, Blum, Pfahl, Brunnen, Sommer), Abhilfe je Modus, Bericht, Positionen, Englisch
- `test_size_paketB.py` (43) — **neu in size v0.5.21**: alle 8 Modi gegen unabhängige Python-Handrechnung (Brandschutz 5 Fälle, Zugkraftdeckung 2 + Mindestbewehrung, Zugstab 2, Stumpfnaht 2, Querzug 3, Durchbruch 3, Doppelbiegung 2, Ausfachung 5 Fälle), Abhilfe je Modus mit „Übernehmen“, Bericht, Positionen, Englisch
- `test_size_paketA.py` (61) — **neu in size v0.5.20**: alle 11 neuen Modi gegen unabhängige Python-Handrechnung (Torsion 2 Fälle, Stoß 8 Varianten + Querbewehrung, Abbrand 3, Schwingung 2, HYD 3, Zeitsetzung 2 + T<sub>90</sub>, Böschung 3, Druckstoß 2, Pumpe 2, Teilfüllung 3, GK 7 Fälle + Anforderungen), Kernfunktionen identisch mit ref, Abhilfe je Modus mit erwartetem Wert und „Übernehmen“, Bericht, Positionen, Englisch
- `test_size_abhilfe.py` (48) — **neu in size v0.5.19**: 8 Fälle aus allen Bereichen, Eingaben und Ergebnis nach der Suche unverändert, Vorschläge gegen Handrechnung (Holz h/b aus σ = 6M/(bh²), Stahl IPE 360 aus W_pl), „Übernehmen“ erfüllt den Nachweis, Bericht, Englisch, Laufzeit < 3 s
- `test_ref_i18n.py` (21) — seit ref v0.3.20, erweitert in v0.3.21: DE unverändert, Seitenleiste mit allen 132 Themen englisch, alle 10 Fächer ohne deutsche Reste (auch nach Eingaben), kein „DE“-Hinweis mehr, Dezimalpunkt, englische Suche
- `test_ref_i18n_code.py` (8) — **neu in ref v0.3.21**: jeder `tt('…')`-Text und jede kurze `_L`-Vorlage im Code hat eine Übersetzung, Platzhalterzahl stimmt; Stichproben DE/EN (Gebäudeklasse Ein-/Mehrzahl, Holz-Druckstab, Fehlermeldung)
- `test_fres.py` — **neu in size v0.5.23 / ref v0.3.22**: I18N.fr/es vollständig, TTX.fr/es decken TTX.en ab (size und ref), alle 58 size-Nachweise (Oberfläche, Rechenweg, Bericht) und alle 132 ref-Themen (auch nach Eingaben) in EN, FR und ES ohne deutsche Reste (strengeres Wortmuster als die EN-Tests), Dezimalzeichen je Sprache, Suche, DE/EN unverändert
- `test_calc_fres.py` (10) — **neu in calc v0.8.15**: RWT/MSG/Oberfläche FR/ES vollständig, Rechenweg Durchlaufträger ohne deutsche Wörter, alle calc-Systeme, Rechenweg, Theorie-Fenster und Bericht in FR/ES ohne englische Reste, DE-Theoriefenster Rahmen ohne Englisch
- `test_size_traeger_seite.py` (36) — seit size v0.5.24: Seitenansicht Stahlträger je Momentenverlauf (gedrückter Gurt, Nullpunkt, Endmomente, Lastangriff, C₁, L_LT = 0); v0.5.25: Holzbauteil (l_ef wie im Kippnachweis, L_K = 0, ohne M keine Ansicht) und Holz-Beton-Verbund (Verbinderzahl, Einfärbung, F₁); Berichte, EN/FR/ES
- `test_size_import_seite.py` (26) — seit size v0.5.26; v0.5.27: Momentenverlauf aus calc (Einfeld → Gleichlast, Kragarm/Durchlaufträger/Riegel → konstant, Stiel → linear mit ψ, Regeln an Beispielsystemen), Abschnitt markiert; Seitenansicht nach Import aus calc (Einfeldträger, Kragarm, Durchlaufträger, Rahmen-Riegel und -Stiel, Holz), Lager, Lasten, Feld-/Stützmoment, gedrückter Gurt nach Vorzeichen, L_LT = Stützweite, Rückfall nach Änderung, EN/FR/ES
- `test_projekt.py` (32) — seit projekt v0.1.0, v0.1.1: einheitlich „Meine Projekte“ (Startseite, Projektseite, calc, size, EN/FR/ES); Zuordnen, size folgt calc-Quelle, andere Nachweisart ohne Quelle, veraltet/älterer Stand, Neu rechnen über size, Gesamtbericht, Projektdatei, Sprünge calc/size, Löschen, Startseite, EN/FR/ES
- `test_size_i18n.py` (28) — **neu in size v0.5.17**, ab v0.5.18 auch Rechenwege, Abbildungen und Berichte ohne Deutsch, Dezimalpunkt, Berichtsdatum en-GB; I18N.en vollständig, Platzhalter gleich, HTML-Text = I18N.de, TTX ohne Altlasten, alle 58 Nachweise auf Englisch ohne deutsche Reste in der Oberfläche, Fehler-/Positions-/Importmeldungen englisch, DE unverändert
- `test_ref_layout.py` (15) — **neu in ref v0.3.7**, Startseite ohne Kacheln ab v0.3.8: Seitenleiste mit Filter, „Auf dieser Seite“, Themen-Pager, Handy-Menü, Bausteine `ablauf()` und `eqLine()`

- `test_pruefliste.py` (36) — **neu in ref v0.3.23 / size v0.5.30**: korrigierte Norm-/NA-Werte aus dem Quellenabgleich (C₁ SN003a, β_w, Kippen BSH × 1,4, KLED D, Schnee μ₂, Wind I, Φ₁ mit a/t, Glaser 4108-3:2018, K_ij, Mindestwärmeschutz, Abflussbeiwerte, Durchbruch, Schwingung 2 kN, Pfahl, HYD, Ausfachung NA.C.1, F_C) unabhängig in Python
- `test_rechtliches.py` — neu in v0.3.24/v0.5.31: Rechtsseite DE/EN/FR/ES, Haftungshinweis und Link auf allen Seiten, Hinweis im Bericht, Schriften lokal ohne fremde Anfragen, Normtabellen als Auszug
- `test_projekt_link.py` (8) — neu: „Meine Projekte“ über einen lokalen Webserver mit und ohne projekt.html (Navigation bzw. Hinweis statt 404, DE/EN)

Stand: **1529/1529 grün** (inklusive `test_skizzen_klarheit.py` 16, `test_marke_muly.py` 24, `test_size_schub.py` 19, `test_size_bauph_plaus.py` 16, `test_size_luftschicht.py` 12 und `test_vertrauen.py` 9 Prüfungen).
Referenzfälle: Rahmen fix/fix h=4 b=5 q=10 → Kopf −14.88, Fuß +7.44, Feld +16.37 · DLT 2×5 m q=10 → 18.75 / 62.5 / 18.75 kN, M_B = −31.25 kNm

---

## Noch offen
1. **Bericht:** nur auf Deutsch (App-Sprache wird nicht berücksichtigt). Balken-Lasten erst ab 0.8.2 gespeichert, ältere Balken-Berichte zeigen „—“ bei den Einwirkungen
2. ~~Mehrsprachigkeit in calc~~ erledigt in v0.8.9 (Schlüssel, Bericht, Sprachwahl). size: vollständig EN seit v0.5.18; ref: vollständig EN seit v0.3.21; size und ref FR/ES seit v0.5.23 / v0.3.22 (Stufe 4 abgeschlossen)
3. **Modul-Struktur:** Solver liegt noch im selben Skript wie UI/Zeichnen. Ein abgegrenzter Block (`Statiq.solver`) würde die Harnesses vereinfachen
4. ~~Neue Möglichkeiten beim Durchlaufträger~~ erledigt in calc v0.8.6 (Gelenke/EI je Feld beim Einfeldträger wären noch möglich)
5. ~~Riegel-Streckenlast horizontal~~ erledigt in calc v0.8.10 (`rdir` n/h)
7. **ref:** Bodenkennwerte und Sohlwiderstand (halbfest/fest, Ton) gegen Norm prüfen; Stahlbeton weiter: Durchstanzen als Thema (size kann es schon), schiefe Biegung bei Stützen, Kriechen (K_φ); Torsion als size-Modus seit v0.5.20
6. ~~Unbestimmtheits-Info und Meldungen in FR/ES nur Englisch~~ erledigt in calc v0.8.15 (dazu Rechenweg FR/ES)
8. ~~Schweißverbindungen~~ erledigt in size v0.7.0 (Kehlnähte; offen: Stumpfnähte, Fall Laschenstoß mit Moment). Danach: Übersetzung von size/ref zusammen mit der Design-Überarbeitung aller Seiten.
