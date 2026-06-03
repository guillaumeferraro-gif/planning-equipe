import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime, json, os, holidays

st.set_page_config(page_title="Planning IDE Expert", layout="wide")

NURSE_NAMES = ["BUFFA. C", "BAMBOU. D", "SERVOIN. N", "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"]
SHIFT_OPTIONS = ["-", "☀️ JOUR", "🌙 NUIT", "🛠️ TIIH"]
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- FONCTIONS DE GESTION ---
def get_file_path(y, m): return os.path.join(DATA_DIR, f"planning_{y}_{m:02d}.json")

def load_month_data(y, m):
    path = get_file_path(y, m)
    if os.path.exists(path):
        with open(path, "r") as f: return pd.DataFrame(json.load(f))
    return None

def calculate_global_stats(current_y, current_m):
    """Calcule les heures de tous les mois AVANT le mois sélectionné"""
    stats = {n: 0.0 for n in NURSE_NAMES}
    files = [f for f in os.listdir(DATA_DIR) if f.startswith("planning_")]
    for f in files:
        parts = f.replace(".json", "").split("_")
        y, m = int(parts[1]), int(parts[2])
        if (y < current_y) or (y == current_y and m < current_m):
            with open(os.path.join(DATA_DIR, f), "r") as f_in:
                df = pd.DataFrame(json.load(f_in))
                for n in NURSE_NAMES:
                    for val in df.loc[n]:
                        if "☀️" in str(val) or "🌙" in str(val): stats[n] += 12
                        elif "🛠️" in str(val): stats[n] += 7.7
    return stats

# --- UI SIDEBAR ---
st.sidebar.header("🗓️ Sélection")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026])
month = st.sidebar.slider("Mois", 1, 12, datetime.datetime.now().month)
current_stats = calculate_global_stats(year, month)

# --- LOGIQUE D'AFFICHAGE ---
st.title(f"🏥 Planning - {month:02d}/{year}")
existing_df = load_month_data(year, month)
fr_holidays = holidays.France(years=year)
month_holidays = [d for d in fr_holidays if d.month == month]

# Cas 1 : Le planning existe déjà -> Modification uniquement
if existing_df is not None:
    st.success("✅ Planning validé. Modification autorisée.")
    df_to_edit = existing_df
else:
    # Cas 2 : Passé sans planning -> Création manuelle vide
    now = datetime.datetime.now()
    if year < now.year or (year == now.year and month < now.month):
        st.info("📜 Mois passé sans données. Vous pouvez le remplir manuellement.")
        num_days = (datetime.date(year, month, 28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        df_to_edit = pd.DataFrame("-", index=NURSE_NAMES, columns=[f"{d}" for d in range(1, num_days.day + 1)])
    # Cas 3 : Futur ou présent -> Bouton Générer disponible
    else:
        if st.button("🚀 Générer le planning automatique"):
            with st.spinner("Calcul équitable..."):
                raw = generate_schedule(NURSE_NAMES, year, month, current_stats, month_holidays)
                if raw:
                    st.session_state[f"temp_{year}_{month}"] = pd.DataFrame(raw)
                    st.rerun()
                else: st.error("Échec de la génération.")
        
        df_to_edit = st.session_state.get(f"temp_{year}_{month}", None)

# --- ÉDITEUR ET SAUVEGARDE ---
if df_to_edit is not None:
    config = {f"{c}": st.column_config.SelectboxColumn(f"{c}", options=SHIFT_OPTIONS, width="small") for c in df_to_edit.columns}
    edited_df = st.data_editor(df_to_edit, column_config=config, use_container_width=True)
    
    if st.button("💾 Valider et Enregistrer définitivement"):
        with open(get_file_path(year, month), "w") as f:
            json.dump(edited_df.to_dict(), f)
        st.success("Enregistré ! Ce mois est maintenant verrouillé pour la génération.")
        st.rerun()

# Stats en sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Heures cumulées (Historique)")
for n, h in current_stats.items(): st.sidebar.write(f"**{n}** : {round(h,1)}h")
