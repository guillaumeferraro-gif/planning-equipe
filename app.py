import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime, json, os, holidays

st.set_page_config(page_title="Planning IDE v6", layout="wide")

NURSE_NAMES = ["BUFFA. C", "BAMBOU. D", "SERVOIN. N", "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"]
SHIFT_OPTIONS = ["-", "☀️ JOUR", "🌙 NUIT", "🛠️ TIIH"]
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def get_file_path(y, m): return os.path.join(DATA_DIR, f"planning_{y}_{m:02d}.json")

def load_month_data(y, m):
    path = get_file_path(y, m)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return pd.DataFrame.from_dict(data, orient='index').reindex(NURSE_NAMES)
    return None

def calculate_global_stats(current_y, current_m):
    stats = {n: 0.0 for n in NURSE_NAMES}
    if not os.path.exists(DATA_DIR): return stats
    files = [f for f in os.listdir(DATA_DIR) if f.startswith("planning_")]
    for f in files:
        parts = f.replace(".json", "").split("_")
        y, m = int(parts[1]), int(parts[2])
        if (y < current_y) or (y == current_y and m < current_m):
            with open(os.path.join(DATA_DIR, f), "r") as f_in:
                df = pd.DataFrame.from_dict(json.load(f_in), orient='index')
                for n in NURSE_NAMES:
                    if n in df.index:
                        for val in df.loc[n]:
                            if "☀️" in str(val) or "🌙" in str(val): stats[n] += 12
                            elif "🛠️" in str(val): stats[n] += 7.7
    return stats

# --- UI SIDEBAR ---
st.sidebar.header("🗓️ Sélection")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026], index=2)
month = st.sidebar.slider("Mois", 1, 12, datetime.datetime.now().month)
current_stats = calculate_global_stats(year, month)

st.title(f"🏥 Planning Expert - {month:02d}/{year}")

existing_df = load_month_data(year, month)
fr_holidays = holidays.France(years=year)
month_holidays = [d for d in fr_holidays if d.month == month]

# --- LOGIQUE ---
df_to_edit = None

if existing_df is not None:
    st.success("✅ Planning validé. Vous pouvez modifier manuellement.")
    df_to_edit = existing_df
else:
    now = datetime.date.today()
    target_date = datetime.date(year, month, 1)
    
    if target_date >= now.replace(day=1):
        if st.button("🚀 Générer le planning automatique"):
            with st.spinner("Calcul en cours (règles complexes)..."):
                raw = generate_schedule(NURSE_NAMES, year, month, current_stats, month_holidays)
                if raw:
                    st.session_state[f"temp_{year}_{month}"] = pd.DataFrame.from_dict(raw, orient='index').reindex(NURSE_NAMES)
                    st.rerun()
                else: 
                    st.error("Échec : Le logiciel ne trouve pas de solution respectant toutes les contraintes (48h, Repos Lundi, Blocs de 2).")
        
        df_to_edit = st.session_state.get(f"temp_{year}_{month}", None)
    else:
        st.info("📜 Saisie manuelle pour ce mois passé.")
        last_d = (datetime.date(year, month, 28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        df_to_edit = pd.DataFrame("-", index=NURSE_NAMES, columns=[f"{d}" for d in range(1, last_d.day + 1)])

# --- ÉDITEUR ---
if df_to_edit is not None:
    config = {}
    for col in df_to_edit.columns:
        date_obj = datetime.date(year, month, int(col))
        label = col
        if date_obj.weekday() == 5: label += " (Sam)"
        elif date_obj.weekday() == 6: label += " (Dim)"
        elif date_obj.weekday() == 0: label += " (Lun)"
        
        if date_obj in month_holidays: label += " 🚩"
        
        config[col] = st.column_config.SelectboxColumn(label, options=SHIFT_OPTIONS, width="small")

    edited_df = st.data_editor(df_to_edit, column_config=config, use_container_width=True)
    
    if st.button("💾 Enregistrer"):
        with open(get_file_path(year, month), "w") as f:
            json.dump(edited_df.to_dict(orient='index'), f)
        st.success("Planning enregistré !")
        st.rerun()

# Sidebar Stats
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Totaux cumulés")
for n, h in current_stats.items(): st.sidebar.write(f"**{n}** : {round(h,1)}h")
