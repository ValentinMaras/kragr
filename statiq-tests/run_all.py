# Alle Testreihen nacheinander ausführen: python3 statiq-tests/run_all.py
import subprocess, sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
# Vorab: fehlende Pakete brechen den Lauf ab (am 10.11.2026 übersprang der Lauf vier Dateien stillschweigend, weil shapely/scipy fehlten)
missing=[]
for mod in ('playwright','shapely','scipy','numpy'):
    try: __import__(mod)
    except ImportError: missing.append(mod)
if missing:
    print('ABBRUCH: Pakete fehlen: '+', '.join(missing)+' — pip install --break-system-packages '+' '.join(missing)); sys.exit(2)
def run_file(t):
    r=subprocess.run([sys.executable,os.path.join(HERE,t)],capture_output=True,text=True,cwd=HERE); out=r.stdout
    ok=sum(l.startswith('OK') for l in out.splitlines()); bad=sum(l.startswith('FAIL ') for l in out.splitlines())
    if 'SKIP' in out and not ok and not bad:        # übersprungene Datei zählt als Fehler
        bad=1; out+='\nFAIL Testdatei übersprungen: '+out.strip().splitlines()[-1]
    elif r.returncode!=0 and not bad:               # Absturz zählt als Fehler
        bad=1; out+='\nFAIL Testdatei abgebrochen: '+(r.stderr.strip().splitlines() or ['?'])[-1]
    elif not ok and not bad:                        # keine einzige Prüfung gelaufen
        bad=1; out+='\nFAIL Testdatei ohne Prüfungen'
    return ok,bad,out
total=fails=0; retried=[]
for t in ['runtests.py','runtests2.py','runtests3.py','runtests_beam.py','runtests4.py','runtests_report.py','test_ref.py','test_calc_ui.py','test_calc_cont.py','test_size.py','test_size_stahl.py','test_size_ext.py','test_size_beton2.py','test_size_import.py','test_size_holzverb.py','test_size_fuss.py','test_size_durchstanzen.py','test_calc_rafterload.py','test_size_schweiss.py','test_size_grundbau.py','test_size_mauerwerk.py','test_size_wasserbau.py','test_size_ux.py','test_ref_skizzen.py','test_size_holz2.py','test_size_2lagen.py','test_calc_ux.py','test_calc_rechenweg.py','test_ref_layout.py','test_ref_stahl.py','test_ref_beispiele.py','test_size_gleit_schwimm.py','test_ref_holz.py','test_ref_stahlbeton.py','test_ref_grundbau.py','test_ref_wasserbau.py','test_ref_mauerwerk.py','test_ref_baustatik.py','test_ref_lasten.py','test_ref_bauphysik.py','test_size_bauphysik.py','test_size_i18n.py','test_ref_i18n.py','test_ref_i18n_code.py','test_size_abhilfe.py','test_size_paketA.py','test_size_paketB.py','test_size_paketC.py','test_fres.py','test_calc_fres.py','test_size_traeger_seite.py','test_size_import_seite.py','test_pruefliste.py','test_rechtliches.py','test_layout_rahmen.py','test_pwa.py','test_skizzen_klarheit.py','test_marke_kragr.py','test_size_schub.py','test_size_bauph_plaus.py','test_size_luftschicht.py','test_vertrauen.py','test_sprachdateien.py','test_size_uebung.py','test_calc_uebung.py','test_dunkel.py','test_startseite_glas.py','test_size_plakette.py','test_bericht_rechenblatt.py','test_size_listen.py','test_uebung_lernpfad.py','test_indizes.py','test_design_kragr.py','test_calc_design2.py','test_size_design3.py','test_rahmen_einheitlich.py','test_calc_bedienung.py','test_knoten.py','test_satteldach.py','test_lastfaelle.py','test_stufen.py','test_federn.py','test_lagerzeichen.py','test_design_k5.py','test_bewegung.py','test_flip.py','test_rechenblaetter.py','test_ref_spannungsbild.py','test_rechenweg_kgv.py','test_wissen_allgemein.py','test_integraltafel_figuren.py','test_rechenblatt_logo.py','test_wissen_lehrbuch.py','test_toc_marker.py','test_size_st_erweitert.py','test_size_ergebnisse.py','test_kopf_vorne.py','test_figtop.py','test_zoomview.py','test_quer.py','test_na_grundlage.py','test_schnitt_mobil.py','test_wissen_grundbau2.py','test_wissen_stahlbeton2.py','test_wissen_holz2.py','test_wissen_mauerwerk2.py','test_size_lasche.py','test_wissen_lasche.py','test_solver.py','test_handy_durchklick.py','test_pdf.py','test_undo.py']:
    ok,bad,out=run_file(t)
    if bad:                                         # ein zweiter Anlauf: unter Last sind einzelne Browser-Prüfungen gelegentlich zu früh
        first=[l for l in out.splitlines() if l.startswith('FAIL ')]
        ok2,bad2,out2=run_file(t)
        if not bad2: retried.append((t, first)); ok,bad,out=ok2,bad2,out2
    total+=ok+bad; fails+=bad
    print(f'{t:18} {ok:3} OK  {bad:3} FAIL')
    for l in out.splitlines():
        if l.startswith('FAIL '): print('   ',l)
for t,first in retried:
    print(f'Hinweis: {t} erst im zweiten Anlauf grün; zuerst:'); [print('   ',l[:160]) for l in first[:4]]
print(f'Gesamt: {total-fails}/{total} grün')
sys.exit(1 if fails else 0)
