import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime
import json
import os

# Essayer d'importer holidays, sinon afficher un message clair
try:
    import holidays
except ImportError:
    st.error("⚠️ La bibliothèque 'holidays' est en cours d'installation. Veuillez patienter 1 minute et rafraîchir la page (F5).")
    st.stop()

st.set_page_config(page_title="Planning PRO", layout="wide")

NURSE_NAMES = ["BUFFA. C", "BAMBOU. D", "SERVOIN. N", "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"]
SAVE_FILE = "stats_backup.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f: return json.load(f)
        except: return {name: 0.0 for name in NURSE_NAMES}
    return {name: 0.0 for name in NURSE_NAMES}

if 'stats' not in st.session_state: st.session_state['stats'] = load_data()

st.title("🏥 Gestion du Planning de l'Équipe")

st.sidebar.header("🗓️ Période")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026], index=0)
month = st.sidebar.slider("Mois", 1, 12, datetime.datetime.now().month)

fr_holidays = holidays.France(years=year)
current_month_holidays = [d for d, name in fr_holidays.items() if d.month == month]

if st.button("🚀 Générer le Planning du Mois"):
    with st.spinner('Optimisation des blocs et de l\'équité...'):
        raw_data = generate_schedule(NURSE_NAMES, year, month, st.session_state['stats'], current_month_holidays)
        if raw_data:
            st.session_state['current_plan'] = raw_data
        else:
            st.error("Erreur : Impossible de respecter les 48h glissantes.")

if 'current_plan' in st.session_state:
    df_display = pd.DataFrame.from_dict(st.session_state['current_plan'], orient='index')
    df_display.columns = [f"{d}" for d in df_display.columns]

    st.subheader(f"Tableau de Service - {month}/{year}")
    st.caption("☀️=Jour (12h) | 🌙=Nuit (12h) | 🛠️=TIIH (7.7h) | -=Repos")

    def style_planning(col):
        res = []
        day_num = int(col.name)
        date_obj = datetime.date(year, month, day_num)
        bg_color = ""
        if date_obj.weekday() >= 5: bg_color = "background-color: #FFF3CD;"
        if date_obj in current_month_holidays: bg_color = "background-color: #F8D7DA; color: #721C24; font-weight: bold;"
            
        for val in col:
            style = bg_color
            if "☀️" in str(val): style += "color: orange;"
            elif "🌙" in str(val): style += "color: blue;"
            elif "🛠️" in str(val): style += "color: green;"
            res.append(style)
        return res

    styled_df = df_display.style.apply(style_planning, axis=0)
    st.write("### Vue Lecture (Couleurs)")
    st.dataframe(styled_df, use_container_width=True)

    st.write("### Vue Modification")
    edited_df = st.data_editor(df_display, use_container_width=True)

    if st.button("✅ Valider et enregistrer les heures"):
        new_stats = st.session_state['stats'].copy()
        for nurse in NURSE_NAMES:
            row = edited_df.loc[nurse]
            h_month = 0
            for val in row:
                if "☀️" in str(val): h_month += 12
                elif "🌙" in str(val): h_month += 12
                elif "🛠️" in str(val): h_month += 7.7
            new_stats[nurse] += h_month
        
        st.session_state['stats'] = new_stats
        with open(SAVE_FILE, "w") as f: json.dump(new_stats, f)
        st.success("Heures enregistrées et sauvegardées !")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Compteurs d'Heures")
for n in NURSE_NAMES:
    h = st.session_state['stats'].get(n, 0)
    st.sidebar.write(f"**{n}** : {round(h, 1)} h")
