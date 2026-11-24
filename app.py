"""Interface locale du planning IDE."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from planning.domain import (
    ABSENCE_KINDS, DomainError, SHIFT_LABELS, absence_on, annual_totals, change_tiih,
    credit_minutes, dates, default_tiih, format_minutes, local_datetime, month_bounds,
    parse_duration, quota_on, set_absence, set_contract, shift_interval,
    tiih_required, validate_schedule, validate_state,
)
from planning.solver import generate_schedule
from planning.storage import Store, StorageError, import_legacy

st.set_page_config(page_title="Planning IDE", page_icon="📅", layout="wide")
st.markdown("""
<style>
.block-container { max-width: 1600px; padding-top: 2rem; }
h1 { letter-spacing: -.035em; }
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
[data-testid="stSidebar"] { border-right: 1px solid #dde4ea; }
</style>
""", unsafe_allow_html=True)

TODAY = datetime.now(ZoneInfo("Europe/Paris")).date()
MONTHS = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
WEEKDAYS = ["lun","mar","mer","jeu","ven","sam","dim"]
LABEL_TO_CODE = {v:k for k,v in SHIFT_LABELS.items()}
DATA_DIR = Path(os.environ.get("PLANNING_DATA_DIR", str(Path(__file__).parent/"data")))
try:
    store = Store(DATA_DIR)
    if "state" not in st.session_state:
        st.session_state.state = store.load()
except (StorageError, OSError) as exc:
    st.error(str(exc))
    st.stop()

state = st.session_state.state
version = st.session_state.get("editor_version",0)
names = {n["id"]:n["name"] for n in state["nurses"]}
with st.sidebar:
    st.title("Planning IDE")
    st.caption("SMUR · TIIH")
    page = st.radio("Espace", ["Planning","Absences","TIIH","Équipe et règles","Compteurs","Données"], key="page")
    st.divider()
    year = int(st.number_input("Année", min_value=1900, max_value=2200, value=TODAY.year, step=1, key="year"))
    month = st.selectbox("Mois", range(1,13), index=TODAY.month-1, format_func=lambda m:MONTHS[m-1], key="month")
    st.caption("SMUR J · 8 h–20 h\n\nSMUR N · 20 h–8 h\n\nTIIH · 9 h–16 h 42")
    st.caption("Données enregistrées sur cet ordinateur.")
start,end = month_bounds(year,month)

def save(candidate, message):
    try:
        saved = store.save(candidate, expected_revision=state["revision"])
        st.session_state.state = saved
        st.session_state.editor_version = version+1
        st.session_state.pop("proposal",None)
        st.session_state.flash = message
        st.rerun()
    except (StorageError, DomainError) as exc:
        st.error(str(exc))

def show_issues(issues):
    errors = [i for i in issues if i.severity=="error"]
    warnings = [i for i in issues if i.severity!="error"]
    if errors:
        st.error(f"{len(errors)} point(s) à corriger — ce planning reste un brouillon.")
    elif warnings:
        st.warning("Aucun conflit détecté dans les données connues. Le contexte reste à compléter.")
    else:
        st.success("Planning conforme aux règles paramétrées et au contexte renseigné.")
    if warnings:
        with st.expander(f"Contexte et paramètres à compléter ({len(warnings)})"):
            for issue in warnings:
                st.write("• "+issue.message)
    if errors:
        with st.expander("Voir les conflits",expanded=True):
            st.dataframe(pd.DataFrame([{"Date":i.day or "","Règle":i.code,"Détail":i.message} for i in errors]),
                         hide_index=True,width="stretch")
    return errors,warnings

def grid(value, first, last):
    rows=[]
    for nurse in value["nurses"]:
        nid=nurse["id"]
        row={"IDE":nurse["name"]}
        for d in dates(first,last):
            code=value["assignments"].get(str(d),{}).get(nid,{}).get("shift","-")
            row[str(d)]="Absence" if code=="-" and absence_on(value,nid,d) else SHIFT_LABELS[code]
        rows.append(row)
    return pd.DataFrame(rows)

def export_csv(frame):
    # Les noms restent du texte lorsqu'ils sont ouverts dans un tableur.
    def safe(v):
        if isinstance(v,str) and v.lstrip().startswith(("=","+","-","@","\t","\r")):
            return "'"+v
        return v
    return frame.map(safe).to_csv(index=False,sep=";").encode("utf-8-sig")

def display_phases(value, first, last):
    rows=[]
    for nurse in value["nurses"]:
        row={"IDE":nurse["name"]}
        for d in dates(first,last):
            p=value["phases"].get(str(d),{}).get(nurse["id"])
            row[str(d)]=(f"{'Nuit' if p['mode']=='N' else 'Jour'} · {p['age']}" if p else "À renseigner")
        rows.append(row)
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
    st.caption("Le nombre indique le jour de la période, repos et absences compris.")

if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"))

if page=="Planning":
    st.title(f"{MONTHS[month-1]} {year}")
    st.caption("Construire, ajuster et contrôler le planning de l'équipe.")
    totals={s:sum(a["shift"]==s for d,ns in state["assignments"].items()
                  if str(start)<=d<=str(end) for a in ns.values()) for s in ("J","N","T")}
    cols=st.columns(4)
    cols[0].metric("SMUR jour",f"{totals['J']} / {(end-start).days+1}")
    cols[1].metric("SMUR nuit",f"{totals['N']} / {(end-start).days+1}")
    cols[2].metric("TIIH",f"{totals['T']} / {sum(tiih_required(state,d) for d in dates(start,end))}")
    cols[3].metric("Équipe",f"{len(names)} IDE")
    missing=[n["name"] for n in state["nurses"] if quota_on(n,start) is None]
    if missing:
        st.info("Avant de générer : compléter les quotités dans Équipe et règles. "+", ".join(missing))
    c1,c2=st.columns([3,1])
    with c2:
        limit=st.number_input("Temps de recherche (secondes)",min_value=5,max_value=120,value=20,step=5)
    with c1:
        if st.button("Générer une proposition",type="primary",disabled=bool(missing),key="generate"):
            with st.spinner("Recherche d'un planning respectant vos règles…"):
                result=generate_schedule(state,year,month,time_limit=float(limit))
            if result.candidate is not None:
                st.session_state.proposal={"result":result,"year":year,"month":month,"revision":state["revision"]}
            else:
                st.error(result.message)
        st.caption("La proposition inclut environ trois semaines d'anticipation pour contrôler les enchaînements.")
    proposal=st.session_state.get("proposal")
    if proposal and proposal["year"]==year and proposal["month"]==month and proposal["revision"]==state["revision"]:
        result=proposal["result"]
        with st.container(border=True):
            st.subheader("Proposition à examiner")
            st.write(result.message)
            st.caption(f"Recherche : {result.elapsed:.1f} s · nuits isolées : {result.isolated_nights} · anticipation jusqu'au {result.end:%d/%m/%Y}")
            st.dataframe(grid(result.candidate,start,end),hide_index=True,width="stretch")
            show_issues(validate_schedule(result.candidate,start,end))
            with st.expander("Voir les affectations d'anticipation"):
                st.dataframe(grid(result.candidate,end+timedelta(days=1),result.end),hide_index=True,width="stretch")
            a,b=st.columns(2)
            if a.button("Conserver cette proposition",type="primary",key="accept_proposal"):
                save(result.candidate,f"Proposition enregistrée, anticipation jusqu'au {result.end:%d/%m/%Y}.")
            if b.button("Écarter la proposition",key="discard_proposal"):
                st.session_state.pop("proposal",None)
                st.rerun()
    st.subheader("Planning enregistré")
    st.caption("Les absences se renseignent dans l'espace Absences. Les postes verrouillés ou confirmés sont protégés.")
    config={"IDE":st.column_config.TextColumn("IDE",width="medium")}
    for d in dates(start,end):
        config[str(d)]=st.column_config.SelectboxColumn(f"{d.day:02d} · {WEEKDAYS[d.weekday()]}",
            options=["Repos","SMUR J","SMUR N","TIIH","Absence"],required=True,width="small")
    with st.form("planning_form"):
        edited=st.data_editor(grid(state,start,end),hide_index=True,disabled=["IDE"],column_config=config,
                              width="stretch",key=f"planning_grid_{year}_{month}_{version}")
        submitted=st.form_submit_button("Enregistrer le brouillon")
    if submitted:
        try:
            candidate=deepcopy(state)
            for i,nurse in enumerate(state["nurses"]):
                nid=nurse["id"]
                for d in dates(start,end):
                    label=edited.iloc[i][str(d)]
                    if label=="Absence" and not absence_on(state,nid,d):
                        raise DomainError("Créer d'abord l'absence correspondante dans l'espace Absences.")
                    code="-" if label=="Absence" else LABEL_TO_CODE[label]
                    old=state["assignments"].get(str(d),{}).get(nid,{"shift":"-","locked":False,"confirmed":False})
                    if (old["locked"] or old["confirmed"]) and old["shift"]!=code:
                        raise DomainError(f"{nurse['name']} · {d:%d/%m} : poste protégé. Modifier sa protection avant de le changer.")
                    candidate["assignments"].setdefault(str(d),{})[nid]={**old,"shift":code}
                    candidate["reviewed"][str(d)]=list(names)
            save(candidate,"Brouillon enregistré ; les contrôles sont affichés ci-dessous.")
        except (DomainError,KeyError) as exc:
            st.error(str(exc))
    st.download_button("Exporter ce mois en CSV",export_csv(grid(state,start,end)),
                       file_name=f"planning_{year}_{month:02}.csv",mime="text/csv")
    with st.expander("Verrouiller un poste ou un repos · confirmer le réalisé"):
        with st.form("protection_form"):
            nid=st.selectbox("IDE",list(names),format_func=names.get,key="lock_nurse")
            d=st.date_input("Date",value=start,key="lock_date")
            locked=st.checkbox("Verrouiller cette affectation ou ce repos",value=True)
            confirmed=st.checkbox("Confirmer que ce poste a été réalisé",value=False)
            if st.form_submit_button("Appliquer la protection"):
                try:
                    candidate=deepcopy(state)
                    item=candidate["assignments"].setdefault(str(d),{}).get(nid,{"shift":"-","locked":False,"confirmed":False})
                    if confirmed:
                        if item["shift"]=="-" or shift_interval(d,item["shift"],state["settings"]["timezone"])[1] > int(datetime.now(timezone.utc).timestamp()//60):
                            raise DomainError("Seul un poste terminé peut être confirmé réalisé.")
                    candidate["assignments"][str(d)][nid]={**item,"locked":locked,"confirmed":confirmed}
                    candidate["reviewed"][str(d)]=sorted(set(candidate["reviewed"].get(str(d),[]))|{nid})
                    save(candidate,"Protection et état du poste enregistrés.")
                except DomainError as exc:
                    st.error(str(exc))
        st.caption("Pour corriger un poste confirmé, décocher la confirmation et la protection, puis modifier le brouillon.")
    with st.expander("Périodes jour / nuit"):
        display_phases(state,start,end)
    st.subheader("Contrôle du planning")
    show_issues(validate_schedule(state,start,end))

elif page=="Absences":
    st.title("Absences et créneaux")
    st.caption("Indisponibilité sur toute la période ; crédit par défaut de 7 h 42 uniquement du lundi au vendredi.")
    existing={a["id"]:a for a in state["absences"]}
    options=["new"]+list(existing)
    selected=st.selectbox("Absence à saisir ou modifier",options,
        format_func=lambda k:"Nouvelle absence" if k=="new" else f"{names[existing[k]['nurse_id']]} · {existing[k]['kind']} · {existing[k]['start'][:10]}")
    old=existing.get(selected)
    mode=st.radio("Type de saisie",["Période de jours","Créneau horaire"],
                  index=1 if old and (datetime.fromisoformat(old["start"]).time()!=time() or datetime.fromisoformat(old["end"]).time()!=time()) else 0,
                  horizontal=True,key=f"absence_mode_{selected}")
    ids=list(names)
    first=datetime.fromisoformat(old["start"]).date() if old else start
    last=(datetime.fromisoformat(old["end"])-timedelta(seconds=1)).date() if old else start
    with st.form(f"absence_form_{selected}_{mode}"):
        nid=st.selectbox("IDE concernée",ids,index=ids.index(old["nurse_id"]) if old else 0,format_func=names.get)
        kind=st.selectbox("Motif",ABSENCE_KINDS,index=ABSENCE_KINDS.index(old["kind"]) if old and old["kind"] in ABSENCE_KINDS else 0)
        if mode=="Période de jours":
            interval=st.date_input("Dates de l'absence (début et fin inclus)",value=(first,last))
            daily=st.text_input("Crédit par jour du lundi au vendredi (h:mm)",value=f"{next(iter(old['credits'].values()),462)//60}:{next(iter(old['credits'].values()),462)%60:02}" if old else "7:42")
            st.caption("Samedi et dimanche bloquent la disponibilité, sans crédit automatique. Les jours fériés de semaine restent crédités.")
        else:
            d=st.date_input("Date du créneau",value=first)
            a,b=st.columns(2)
            begin=a.time_input("Début",value=datetime.fromisoformat(old["start"]).time() if old else time(9))
            finish=b.time_input("Fin",value=datetime.fromisoformat(old["end"]).time() if old else time(11))
            tomorrow=st.checkbox("Fin le lendemain",value=bool(old and last>first))
            explicit=st.text_input("Crédit explicite du créneau (h:mm)",value=format_minutes(sum(old["credits"].values())).replace(" h ",":") if old else "2:00")
            st.caption("Ce crédit est choisi explicitement, y compris pour un créneau de week-end.")
        submitted=st.form_submit_button("Enregistrer l'absence",type="primary")
    if submitted:
        try:
            candidate=deepcopy(state)
            zone=state["settings"]["timezone"]
            if mode=="Période de jours":
                if len(interval)!=2:
                    raise DomainError("Sélectionner une date de début et une date de fin.")
                a=local_datetime(interval[0],time(),zone)
                b=local_datetime(interval[1]+timedelta(days=1),time(),zone)
                set_absence(candidate,nid,a,b,kind,parse_duration(daily),absence_id=old["id"] if old else None)
            else:
                a=local_datetime(d,begin,zone)
                b=local_datetime(d+timedelta(days=int(tomorrow)),finish,zone)
                set_absence(candidate,nid,a,b,kind,credits={str(d):parse_duration(explicit)},absence_id=old["id"] if old else None)
            save(candidate,"Absence enregistrée. Les affectations qui la chevauchent seront signalées.")
        except (DomainError,ValueError) as exc:
            st.error(str(exc))
    if old and st.button("Supprimer cette absence",key="delete_absence"):
        candidate=deepcopy(state)
        candidate["absences"]=[a for a in candidate["absences"] if a["id"]!=old["id"]]
        save(candidate,"Absence supprimée.")
    st.subheader("Absences enregistrées")
    if existing:
        st.dataframe(pd.DataFrame([{"IDE":names[a["nurse_id"]],"Motif":a["kind"],"Début":a["start"][:16].replace("T"," "),
                                   "Fin exclusive":a["end"][:16].replace("T"," "),"Crédit":format_minutes(sum(a["credits"].values()))}
                                  for a in state["absences"]]),hide_index=True,width="stretch")
    else:
        st.info("Aucune absence enregistrée.")

elif page=="TIIH":
    st.title("Adapter les postes TIIH")
    st.caption("Mardi, jeudi et vendredi hors jours fériés. Une modification concerne une seule occurrence ; SMUR jour et nuit restent obligatoires.")
    action=st.radio("Action",["Supprimer","Déplacer","Restaurer"],horizontal=True)
    defaults=[d for d in dates(start,end) if default_tiih(state,d)]
    with st.form("tiih_form"):
        origin=st.date_input("Date d'origine du poste TIIH",value=defaults[0] if defaults else start)
        target=st.date_input("Nouvelle date",value=origin+timedelta(days=1)) if action=="Déplacer" else None
        submitted=st.form_submit_button("Appliquer au poste TIIH",type="primary")
    if submitted:
        try:
            candidate=deepcopy(state)
            change_tiih(candidate,origin,target,restore=action=="Restaurer")
            save(candidate,"Besoin TIIH mis à jour. Vérifier ou régénérer les affectations concernées.")
        except DomainError as exc:
            st.error(str(exc))
    origins=set(defaults)|{date.fromisoformat(d) for d,t in state["tiih_changes"].items()
                           if str(start)<=d<=str(end) or (t and str(start)<=t<=str(end))}
    rows=[]
    for d in sorted(origins):
        target=state["tiih_changes"].get(str(d),str(d))
        rows.append({"Date d'origine":str(d),"Date effective":target or "—",
                     "État":"Supprimé" if target is None else "Déplacé" if target!=str(d) else "Maintenu"})
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")

elif page=="Équipe et règles":
    st.title("Équipe et règles")
    st.caption("Toutes les IDE peuvent occuper SMUR J, SMUR N et TIIH. Les noms initiaux sont des repères à personnaliser.")
    effective=st.date_input("Date d'effet des quotités",value=date(year,1,1),key="quota_effective")
    with st.form("team_form"):
        frame=pd.DataFrame([{"IDE":n["name"],"Quotité (%)":quota_on(n,effective)} for n in state["nurses"]])
        edited=st.data_editor(frame,hide_index=True,width="stretch",key=f"team_grid_{version}_{effective}",
            column_config={"IDE":st.column_config.TextColumn(required=True),
                           "Quotité (%)":st.column_config.NumberColumn(min_value=1,max_value=100,step=1,format="%d %%")})
        submitted=st.form_submit_button("Enregistrer l'équipe",type="primary")
    if submitted:
        try:
            candidate=deepcopy(state)
            for i,n in enumerate(candidate["nurses"]):
                n["name"]=str(edited.iloc[i]["IDE"]).strip()
                raw=edited.iloc[i]["Quotité (%)"]
                if not pd.isna(raw) and float(raw)!=int(raw):
                    raise DomainError("Saisir des quotités en pourcentage entier.")
                set_contract(n,effective,None if pd.isna(raw) else int(raw))
            if len({n["name"] for n in candidate["nurses"]})!=len(candidate["nurses"]):
                raise DomainError("Utiliser des noms d'affichage distincts pour repérer chaque IDE.")
            save(candidate,"Équipe et dates d'effet enregistrées.")
        except (DomainError,ValueError) as exc:
            st.error(str(exc))
    st.caption("Deux quotités de 80 % et une de 100 % sont connues. Les quatre autres restent à compléter ; aucune valeur n'est déduite automatiquement.")
    with st.expander("Historique des quotités"):
        st.dataframe(pd.DataFrame([{"IDE":n["name"],"Depuis":c["from"],"Quotité (%)":c["percent"]}
                                  for n in state["nurses"] for c in n["contracts"]]),hide_index=True,width="stretch")
    st.subheader("Temps annuel et organisation")
    with st.form("rules_form"):
        oat=state["oat"].get(str(year))
        oat_text=st.text_input(f"OAT pour 1 ETP en {year} (h:mm)",value=f"{oat//60}:{oat%60:02}" if oat else "",
                               placeholder="À renseigner lorsque vous connaissez la valeur")
        clock=st.selectbox("Calcul des 12 h de repos",["wall","elapsed"],
            index=0 if state["settings"]["rest_clock"]!="elapsed" else 1,
            format_func=lambda v:"Horaires affichés · 20 h–8 h = 12 h" if v=="wall" else "Heures réellement écoulées")
        a,b,c=st.columns(3)
        minimum=a.number_input("Période minimale (jours)",min_value=2,max_value=60,value=state["settings"]["phase_min"])
        preferred=b.number_input("Durée recherchée (jours)",min_value=2,max_value=60,value=state["settings"]["phase_target"])
        maximum=c.number_input("Période maximale (jours)",min_value=2,max_value=60,value=state["settings"]["phase_max"])
        extra=st.text_area("Jours fériés locaux supplémentaires · une date AAAA-MM-JJ par ligne",
                           value="\n".join(state["settings"]["extra_holidays"]))
        submitted=st.form_submit_button("Enregistrer les règles")
    if submitted:
        try:
            candidate=deepcopy(state)
            value=parse_duration(oat_text,allow_blank=True)
            if value is None:
                candidate["oat"].pop(str(year),None)
            else:
                candidate["oat"][str(year)]=value
            candidate["settings"].update(rest_clock=clock,phase_min=int(minimum),phase_target=int(preferred),
                phase_max=int(maximum),extra_holidays=sorted({str(date.fromisoformat(x.strip())) for x in extra.splitlines() if x.strip()}))
            save(candidate,"Règles enregistrées. Les plannings existants sont à contrôler avec ces paramètres.")
        except (DomainError,ValueError) as exc:
            st.error(str(exc))
    st.caption("48 h de travail effectif sur 168 h glissantes ; 3 prises de poste consécutives maximum ; samedi et dimanche ensemble, puis aucune nouvelle prise de poste le lundi. Les nuits isolées sont autorisées et pénalisées dans la recherche.")
    with st.expander("Renseigner un point de départ des périodes jour / nuit"):
        anchor=st.date_input("Date du point de départ connu",value=start-timedelta(days=1),key="phase_anchor")
        rows=[]
        for n in state["nurses"]:
            p=state["phases"].get(str(anchor),{}).get(n["id"])
            rows.append({"IDE":n["name"],"Régime":("Nuit" if p["mode"]=="N" else "Jour") if p else "Inconnu","Jour de la période":p["age"] if p else 1})
        with st.form("phase_form"):
            phase_frame=st.data_editor(pd.DataFrame(rows),hide_index=True,disabled=["IDE"],width="stretch",
                key=f"phase_grid_{anchor}_{version}",column_config={
                    "Régime":st.column_config.SelectboxColumn(options=["Inconnu","Jour","Nuit"],required=True),
                    "Jour de la période":st.column_config.NumberColumn(min_value=1,max_value=60,step=1,required=True)})
            if st.form_submit_button("Enregistrer ce contexte"):
                try:
                    candidate=deepcopy(state)
                    for i,n in enumerate(state["nurses"]):
                        row=phase_frame.iloc[i]
                        if row["Régime"]=="Inconnu":
                            candidate["phases"].get(str(anchor),{}).pop(n["id"],None)
                        else:
                            candidate["phases"].setdefault(str(anchor),{})[n["id"]]={
                                "mode":"N" if row["Régime"]=="Nuit" else "J","age":int(row["Jour de la période"]),"locked":True}
                    save(candidate,"Point de départ des périodes enregistré.")
                except (DomainError,ValueError) as exc:
                    st.error(str(exc))
        st.caption("Exemple : Nuit, jour 8 signifie que cette date est le huitième jour du régime de nuit, repos compris. L'historique des postes se renseigne dans le mois précédent.")

elif page=="Compteurs":
    st.title(f"Compteurs {year}")
    st.caption("Année civile · les crédits d'absence restent distincts du travail effectué.")
    rows=annual_totals(state,year)
    c1,c2,c3=st.columns(3)
    c1.metric("Travail confirmé",format_minutes(sum(r["confirmed_minutes"] for r in rows)))
    c2.metric("Travail encore planifié",format_minutes(sum(r["planned_minutes"] for r in rows)))
    c3.metric("Crédits d'absence",format_minutes(sum(r["absence_minutes"] for r in rows)))
    if str(year) not in state["oat"]:
        st.info("OAT à renseigner : les heures sont comptabilisées, sans cible annuelle supposée.")
    table=pd.DataFrame([{
        "IDE":r["name"],"Confirmé":format_minutes(r["confirmed_minutes"]),
        "Planifié non confirmé":format_minutes(r["planned_minutes"]),
        "Absences créditées":format_minutes(r["absence_minutes"]),
        "Total prévisionnel":format_minutes(r["total_minutes"]) if not r["conflicts"] else "Conflit à corriger",
        "Cible annuelle":format_minutes(r["target_minutes"]),
        "Reste à planifier":format_minutes(r["remaining_minutes"]),
        "Jours renseignés":r["reviewed_days"],"Conflits":r["conflicts"],
    } for r in rows])
    st.dataframe(table,hide_index=True,width="stretch")
    st.caption("Une cible n'est calculée que si l'OAT et les quotités de toute l'année sont connus. Le total prévisionnel additionne confirmé, planifié non confirmé et crédits. Une nuit est comptabilisée à sa date de début.")
    st.download_button("Exporter les compteurs en CSV",export_csv(table),file_name=f"compteurs_{year}.csv",mime="text/csv")

else:
    st.title("Données et sauvegardes")
    st.caption("Les données de l'équipe sont séparées du code du projet.")
    st.download_button("Télécharger une sauvegarde complète",json.dumps(state,ensure_ascii=False,indent=2),
                       file_name=f"planning_ide_sauvegarde_{TODAY}.json",mime="application/json",type="primary")
    st.subheader("Restaurer une sauvegarde")
    uploaded=st.file_uploader("Sauvegarde JSON",type=["json"])
    if uploaded is not None:
        try:
            if uploaded.size>20*1024*1024:
                raise DomainError("Sauvegarde trop volumineuse (maximum 20 Mo).")
            restored=json.loads(uploaded.getvalue())
            validate_state(restored)
            st.write(f"{len(restored['nurses'])} IDE · {len(restored['assignments'])} dates · {len(restored['absences'])} absences")
            if st.button("Remplacer les données par cette sauvegarde"):
                save(restored,"Sauvegarde restaurée ; l'état précédent reste dans le fichier de secours.")
        except (ValueError,DomainError) as exc:
            st.error(f"Sauvegarde refusée : {exc}")
    st.subheader("Reprendre les anciens plannings")
    st.write("Les fichiers planning_année_mois.json présents dans le répertoire de données peuvent être importés. Les originaux sont conservés.")
    if st.button("Importer les anciens fichiers"):
        try:
            candidate,warnings=import_legacy(state,DATA_DIR)
            save(candidate,"Import terminé. "+" ".join(warnings))
        except StorageError as exc:
            st.error(str(exc))
    if st.button("Recharger les données enregistrées"):
        try:
            st.session_state.state=store.load()
            st.session_state.editor_version=version+1
            st.session_state.pop("proposal",None)
            st.rerun()
        except StorageError as exc:
            st.error(str(exc))
