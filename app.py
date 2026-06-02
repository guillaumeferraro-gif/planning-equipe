import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime
import json
import os

st.set_page_config(page_title="Planning IDE v3", layout="wide")

NURSE_NAMES = ["BUFFA. C", "BAMBOU. D", "SERVOIN. N", "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"]
SAVE_FILE = "stats_backup.json"

# --- LOGIQUE DE SAUVEGARDE ---
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {name: 0.0 for name in NURSE_NAMES}

def save_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

# Initialisation
if 'stats' not in st.session_state:
    st.session_state['stats'] = load_data()

st.title("🗓️ Planning Infirmières & Sauvegarde")

# --- BARRE LATÉRALE ---
st.sidebar.header("💾 Gestion des données")

# Import / Export Manuel (Sécurité)
st.sidebar.subheader("Import / Export")
stats_json = json.dumps(st.session_state['stats'])
st.sidebar.download_button("📥 Télécharger la sauvegarde", stats_json, "sauvegarde_planning.json")

uploaded_file = st.sidebar.file_uploader("📤 Réimporter une sauvegarde", type="json")
if uploaded_file is not None:
    st.session_state['stats'] = json.load(uploaded_file)
    save_data(st.session_state['stats'])
    st.sidebar.success("Données chargées !")

st.sidebar.markdown("---")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026])
month = st.sidebar.slider("Mois", 1, 12, value=datetime.datetime.now().month)

st.sidebar.subheader("📊 Heures Cumulées")
for n in NURSE_NAMES:
    h = st.session_state['stats'].get(n, 0)
    st.sidebar.write(f"**{n}** : {round(h, 1)} h")

# --- CORPS DE L'APP ---
if st.button("🚀 Générer le mois suivant"):
    with st.spinner('Calcul en cours...'):
        df = generate_schedule(NURSE_NAMES, year, month, st.session_state['stats'], [])
        if df is not None:
            st.session_state['current_df'] = df
        else:
            st.error("Calcul impossible : vérifiez les contraintes (48h).")

if 'current_df' in st.session_state:
    st.subheader(f"Planning : {month}/{year}")
    edited_df = st.data_editor(st.session_state['current_df'], use_container_width=True)
    
    if st.button("✅ Valider et Sauvegarder"):
        new_stats = st.session_state['stats'].copy()
        
        # Liste des jours TIIH pour le calcul
        tiih_days = []
        for d in range(1, len(edited_df) + 1):
            if datetime.date(year, month, d).weekday() in [1, 3, 4]:
                tiih_days.append(f"{d}/{month}")

        for name in NURSE_NAMES:
            jours = len(edited_df[edited_df['Jour'] == name])
            nuits = len(edited_df[edited_df['Nuit'] == name])
            tiihs = len(edited_df[edited_df['TIIH'] == name])
            
            # Calcul : Jour(12h) + Nuit(12h) + TIIH(7.7h)
            new_stats[name] = new_stats.get(name, 0) + (jours * 12) + (nuits * 12) + (tiihs * 7.7)
        
        st.session_state['stats'] = new_stats
        save_data(new_stats) # Sauvegarde dans le fichier local
        st.success("Données enregistrées dans le système et sauvegardées !")
        st.rerun()
