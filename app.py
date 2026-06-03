import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime
import json
import os
import holidays

st.set_page_config(page_title="Planning IDE v5", layout="wide")

NURSE_NAMES = ["BUFFA. C", "BAMBOU. D", "SERVOIN. N", "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"]
SHIFT_OPTIONS = ["-", "☀️ JOUR", "🌙 NUIT", "🛠️ TIIH"]
SAVE_FILE = "stats_backup.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                # S'assurer que toutes les infirmières sont présentes
                for name in NURSE_NAMES:
                    if name not in data: data[name] = 0.0
                return data
        except: return {name: 0.0 for name in NURSE_NAMES}
    return {name: 0.0 for name in NURSE_NAMES}

if 'stats' not in st.session_state: 
    st.session_state['stats'] = load_data()

st.title("🏥 Planning : Gestion des Phases Jour/Nuit")

# --- SIDEBAR ---
st.sidebar.header("🗓️ Paramètres")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026])
month = st.sidebar.slider("Mois", 1, 12, datetime.datetime.now().month)

fr_holidays = holidays.France(years=year)
current_month_holidays = [d for d, name in fr_holidays.items() if d.month == month]

# --- GÉNÉRATION ---
if st.button("🚀 Générer le Planning"):
    with st.spinner('Calcul des cycles et de l\'équité...'):
        raw_data = generate_schedule(NURSE_NAMES, year, month, st.session_state['stats'], current_month_holidays)
        if raw_data:
            st.session_state['current_plan'] = raw_data
        else:
            st.error("❌ Pas de solution. Essayez de réduire l'historique ou de vérifier les fériés.")

# --- AFFICHAGE ---
if 'current_plan' in st.session_state:
    df_display = pd.DataFrame.from_dict(st.session_state['current_plan'], orient='index')
    df_display.columns = [f"{d}" for d in df_display.columns]

    st.subheader(f"Planning : {month}/{year}")
    
    # Configuration Selectbox
    column_config = {
        f"{d}": st.column_config.SelectboxColumn(
            f"{d}", options=SHIFT_OPTIONS, width="small"
        ) for d in df_display.columns
    }

    # Style pour repérer WE et Fériés
    def style_we(col):
        d_num = int(col.name)
        date_obj = datetime.date(year, month, d_num)
        bg = ""
        if date_obj.weekday() >= 5: bg = "background-color: #FFF3CD;"
        if date_obj in current_month_holidays: bg = "background-color: #F8D7DA;"
        return [bg] * len(col)

    edited_df = st.data_editor(df_display, column_config=column_config, use_container_width=True)

    if st.button("✅ Valider et Sauvegarder"):
        new_stats = st.session_state['stats'].copy()
        for nurse in NURSE_NAMES:
            h_month = 0
            for val in edited_df.loc[nurse]:
                if "☀️ JOUR" in str(val): h_month += 12
                elif "🌙 NUIT" in str(val): h_month += 12
                elif "🛠️ TIIH" in str(val): h_month += 7.7
            new_stats[nurse] += h_month
        
        st.session_state['stats'] = new_stats
        with open(SAVE_FILE, "w") as f: json.dump(new_stats, f)
        st.success("Compteurs mis à jour !")
        st.rerun()

# --- SIDEBAR STATS ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Totaux cumulés")
for n in NURSE_NAMES:
    h = st.session_state['stats'].get(n, 0)
    st.sidebar.write(f"**{n}** : {round(h, 1)} h")
