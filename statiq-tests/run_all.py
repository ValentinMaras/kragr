# Alle Testreihen nacheinander ausführen: python3 statiq-tests/run_all.py
import subprocess, sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
total=fails=0
for t in ['runtests.py','runtests2.py','runtests3.py','runtests_beam.py','runtests4.py','runtests_report.py','test_ref.py','test_calc_ui.py','test_calc_cont.py','test_size.py','test_size_stahl.py','test_size_ext.py','test_size_beton2.py','test_size_import.py','test_size_holzverb.py','test_size_fuss.py','test_size_durchstanzen.py','test_calc_rafterload.py','test_size_schweiss.py','test_size_grundbau.py','test_size_mauerwerk.py','test_size_wasserbau.py','test_size_ux.py','test_ref_skizzen.py','test_size_holz2.py','test_size_2lagen.py','test_calc_ux.py','test_calc_rechenweg.py','test_ref_layout.py','test_ref_stahl.py','test_ref_beispiele.py','test_size_gleit_schwimm.py','test_ref_holz.py','test_ref_stahlbeton.py','test_ref_grundbau.py','test_ref_wasserbau.py','test_ref_mauerwerk.py','test_ref_baustatik.py','test_ref_lasten.py','test_ref_bauphysik.py','test_size_bauphysik.py','test_size_i18n.py','test_ref_i18n.py','test_ref_i18n_code.py','test_size_abhilfe.py','test_size_paketA.py','test_size_paketB.py','test_size_paketC.py','test_fres.py','test_calc_fres.py','test_size_traeger_seite.py','test_size_import_seite.py','test_projekt.py','test_pruefliste.py','test_projekt_link.py','test_rechtliches.py','test_layout_rahmen.py','test_pwa.py','test_skizzen_klarheit.py','test_marke_kragr.py','test_size_schub.py','test_size_bauph_plaus.py','test_size_luftschicht.py','test_vertrauen.py','test_sprachdateien.py','test_size_uebung.py','test_calc_uebung.py','test_dunkel.py','test_startseite_glas.py','test_size_plakette.py','test_projekt_menue.py','test_bericht_rechenblatt.py','test_size_listen.py','test_uebung_lernpfad.py','test_indizes.py','test_design_kragr.py','test_calc_design2.py','test_size_design3.py','test_rahmen_einheitlich.py','test_calc_bedienung.py','test_projektmodus.py','test_knoten.py','test_satteldach.py']:
    r=subprocess.run([sys.executable,os.path.join(HERE,t)],capture_output=True,text=True,cwd=HERE); out=r.stdout
    ok=sum(l.startswith('OK') for l in out.splitlines()); bad=sum(l.startswith('FAIL ') for l in out.splitlines())
    if r.returncode!=0 and not bad and 'SKIP' not in out:   # Absturz zählt als Fehler
        bad=1; out+='\nFAIL Testdatei abgebrochen: '+(r.stderr.strip().splitlines() or ['?'])[-1]
    total+=ok+bad; fails+=bad
    print(f'{t:18} {ok:3} OK  {bad:3} FAIL')
    for l in out.splitlines():
        if l.startswith('FAIL '): print('   ',l)
print(f'Gesamt: {total-fails}/{total} grün')
sys.exit(1 if fails else 0)
