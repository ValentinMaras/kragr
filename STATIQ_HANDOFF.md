# Statiq — Übergabe für neuen Chat (calc v0.8.7 · ref v0.3.1 · size v0.4.1 · Startseite)

## Dateien
- `index.html` — Startseite der Suite (Module calc, size, ref)
- `calc.html` — Schnittgrößen-App (Statiq·calc v0.8.7)
- `ref.html` — Nachschlagewerk (Statiq·ref v0.3.1)
- `size.html` — Bemessung (Statiq·size v0.4.1, Beta: Stahlbeton inkl. Stützen, Stahl, Anschlüsse, Holz)
- `statiq-tests/` — alle Tests, `python3 statiq-tests/run_all.py`

**Versionierung (Wunsch von Valentin):** in kleinen Schritten weiterzählen (0.8.1 → 0.8.2 …).
Einen Sprung auf die nächste Nebenversion (0.9) gibt es nur bei größeren neuen Funktionen (neues Tragsystem, neues Modul). Nicht zu schnell Richtung 1.0.
Versionsnummer steht in `STATIQ_VERSION` und an 8 Stellen im HTML (Kopfzeile, Fußnoten).

---

## Statiq·size v0.4.0 — Druckbewehrung, Zugkraftdeckung, Stahlbetonstütze

- **Druckbewehrung** (nur Typ Balken/Rechteck): bei μ > μ_lim wird der Beton bis ξ_lim = 0,45 ausgenutzt (M_Rd,lim), das Restmoment ΔM über A_s2 (σ_s2 aus ε_s2 = 3,5‰·(x−d2)/x) und zusätzliches A_s1 mit Hebel d − d2. Neue Felder `in-n2`/`in-ds2` („Feld oben“, Klasse `dz-only`), Automatik über `topDruck()`. `res.DZ`, Abbildung zeigt F_s2. Bei Platte/Unterzug weiterhin Hinweis „Querschnitt vergrößern“.
- **Zugkraftdeckung und Staffelung** (Info-Zeile `zkd`): nur Balken/Unterzug, Einfeldträger (K = 1,0, kein Stützmoment), Gleichlast, ohne Druckbewehrung. Versatzmaß a_l = z·cot θ/2, die Hälfte der Stäbe (mind. 2 durchlaufend) endet bei x_E − l_bd (l_bd mit σ_sd = f_yd). Zugkraftdeckungsbild als SVG im Rechenschritt.
- **Stahlbetonstütze** (Typ `stuetze`, eigener Eingabeblock `#beton-stuetze`, Felder `su-*`): Modellstützenverfahren mit Nennkrümmung (5.8.8): λ_lim nach NA (25 bzw. 16/√n), M_0e = max(0,6·M02 + 0,4·M01; 0,4·M02), e_i = θ_i·l0/2 (α_h = 2/√l ≤ 1), e2 = K_r·K_φ·ε_yd/(0,45·d)·l0²/10, M_Ed ≥ M02 + N·e_i und ≥ N·max(h/30; 20 mm). Querschnitt: Dehnungsebenen-Integration (`stuetzeQS`, Parabel-Rechteck, B500 bilinear, symmetrische Bewehrung in zwei Lagen), A_s,tot,erf per Bisektion mit K_r(A_s). Interaktionsdiagramm (`figInteraktion`), Ansicht des Ersatzstabs mit Knickfigur (`figStuetze`). Bewehrungsregeln NA 9.5.2/9.5.3. Bericht `buildReportStuetze`.
- Tests: `test_size_beton2.py` (17, Sollwerte unabhängig in Python: Streifenmodell für M_Rd(N), Bisektion für A_s,erf, numerischer Endpunkt E).
- Offen in size/Stahlbeton: schiefe Biegung bei Stützen, Querkraft Stütze, Zugkraftdeckung für Durchlaufträger/Einzellasten, Durchstanzen.

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

Stand: **326/326 grün** (calc 168 + ref 67 + size 91).
Referenzfälle: Rahmen fix/fix h=4 b=5 q=10 → Kopf −14.88, Fuß +7.44, Feld +16.37 · DLT 2×5 m q=10 → 18.75 / 62.5 / 18.75 kN, M_B = −31.25 kNm

---

## Noch offen
1. **Bericht:** nur auf Deutsch (App-Sprache wird nicht berücksichtigt). Balken-Lasten erst ab 0.8.2 gespeichert, ältere Balken-Berichte zeigen „—“ bei den Einwirkungen
2. **Mehrsprachigkeit:** Übersetzung per Textvergleich (fragil), viele Rahmen-Felder nur Englisch, FR/ES ohne `save`/`saved`. Besser durchgängig `data-i18n`-Schlüssel
3. **Modul-Struktur:** Solver liegt noch im selben Skript wie UI/Zeichnen. Ein abgegrenzter Block (`Statiq.solver`) würde die Harnesses vereinfachen
4. ~~Neue Möglichkeiten beim Durchlaufträger~~ erledigt in calc v0.8.6 (Gelenke/EI je Feld beim Einfeldträger wären noch möglich)
5. **Riegel-Streckenlast horizontal** (Wind auf geneigtes Dach): im Solver derselbe Zweig wie `dir='h'` bei Stützen
7. **ref:** Bodenkennwerte und Sohlwiderstand (halbfest/fest, Ton) gegen Norm prüfen; Stahlbeton weiter: Durchstanzbewehrung, schiefe Biegung bei Stützen, Kriechen (K_φ), Torsion; size-Modul noch offen
6. **Unbestimmtheits-Info** („Statically determinate“ usw.) und Meldungen in FR/ES nur Englisch — gehört zur Mehrsprachigkeit (Punkt 2)
