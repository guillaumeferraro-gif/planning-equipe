from datetime import date
from pathlib import Path
from streamlit.testing.v1 import AppTest
from planning.storage import Store

APP=Path(__file__).resolve().parents[1]/"app.py"

def button(app,label):
    return next(x for x in app.button if x.label==label)

def field(items,label):
    return next(x for x in items if x.label==label)

def fresh(monkeypatch,tmp_path):
    monkeypatch.setenv("PLANNING_DATA_DIR",str(tmp_path))
    app=AppTest.from_file(APP,default_timeout=20).run()
    app.number_input(key="year").set_value(2026)
    app.selectbox(key="month").set_value(11).run()
    assert not app.exception
    return app

def test_navigation_and_team_configuration(monkeypatch,tmp_path):
    app=fresh(monkeypatch,tmp_path)
    assert button(app,"Générer une proposition").disabled
    for page in ["Absences","TIIH","Équipe et règles","Compteurs","Données"]:
        app.radio(key="page").set_value(page).run()
        assert not app.exception
    app.radio(key="page").set_value("Équipe et règles").run()
    editor=app.data_editor[0]
    app.session_state[editor.key]={"edited_rows":{i:{"Quotité (%)":100} for i in range(3,7)},"added_rows":[],"deleted_rows":[]}
    button(app,"Enregistrer l'équipe").click().run()
    assert not app.exception
    assert Store(tmp_path).load()["nurses"][6]["contracts"][0]["percent"]==100
    app.radio(key="page").set_value("Planning").run()
    assert not button(app,"Générer une proposition").disabled
    app.number_input(key="year").set_value(2027).run()
    assert any(t.value=="Novembre 2027" for t in app.title)

def test_absence_credit_and_tiih_forms_persist(monkeypatch,tmp_path):
    app=fresh(monkeypatch,tmp_path)
    app.radio(key="page").set_value("Absences").run()
    field(app.date_input,"Dates de l'absence (début et fin inclus)").set_value((date(2026,11,20),date(2026,11,23)))
    button(app,"Enregistrer l'absence").click().run()
    assert not app.exception
    saved=Store(tmp_path).load()
    assert sum(saved["absences"][0]["credits"].values())==924
    app.radio(key="page").set_value("TIIH").run()
    field(app.radio,"Action").set_value("Déplacer").run()
    field(app.date_input,"Date d'origine du poste TIIH").set_value(date(2026,11,24))
    field(app.date_input,"Nouvelle date").set_value(date(2026,11,25))
    button(app,"Appliquer au poste TIIH").click().run()
    assert not app.exception
    assert Store(tmp_path).load()["tiih_changes"]["2026-11-24"]=="2026-11-25"
    reloaded=AppTest.from_file(APP).run()
    assert len(reloaded.session_state.state["absences"])==1

def test_manual_edit_cross_month_conflict_and_reload(monkeypatch,tmp_path,state):
    Store(tmp_path).save(state,expected_revision=0)
    app=fresh(monkeypatch,tmp_path)
    editor=app.data_editor[0]
    app.session_state[editor.key]={"edited_rows":{0:{"2026-11-30":"SMUR N"}},"added_rows":[],"deleted_rows":[]}
    button(app,"Enregistrer le brouillon").click().run()
    assert Store(tmp_path).load()["assignments"]["2026-11-30"]["ide-a"]["shift"]=="N"
    app.selectbox(key="month").set_value(12).run()
    editor=app.data_editor[0]
    app.session_state[editor.key]={"edited_rows":{0:{"2026-12-01":"TIIH"}},"added_rows":[],"deleted_rows":[]}
    button(app,"Enregistrer le brouillon").click().run()
    assert not app.exception
    frames=[f.value for f in app.dataframe]
    assert any("Détail" in f and f["Détail"].str.contains("repos").any() for f in frames)
    assert Store(tmp_path).load()["assignments"]["2026-12-01"]["ide-a"]["shift"]=="T"
