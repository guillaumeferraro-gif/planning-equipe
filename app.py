import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime

st.set_page_config(page_title="Planning IDE v2", layout="wide")

# --- LISTE DES INFIRMIÈRES ---
NURSE_NAMES = [
    "BUFFA. C", "BAMBOU. D", "SERVOIN. N", 
    "HIZETTE. C", "DUSSAUT. S", "HOAREAU. E", "THOMAS. N"
]

st.title("🗓️ Générateur de Planning Infirmières")

# Initialisation des compteurs en HEURES dans la mémoire de la page
if 'stats' not in st.session_state:
    st.session_state['stats'] = {name: 0.0 for name in NURSE_NAMES}

# --- BARRE LATÉRALE ---
st.sidebar.header("⚙️ Configuration")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026])
month = st.sidebar.slider("Mois", 1, 12, value=datetime.datetime.now().month)

# Affichage des compteurs actuels
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Heures Cumulées (Historique)")
for n in NURSE_NAMES:
    h = st.session_state['stats'][n]
    st.sidebar.write(f"**{n}** : {round(h, 1)} h")

# --- ACTIONS ---
if st.button("🚀 Générer le mois suivant"):
    with st.spinner('L\'algorithme cherche la meilleure répartition...'):
        df = generate_schedule(NURSE_NAMES, year, month, st.session_state['stats'], [])
        if df is not None:
            st.session_state['current_df'] = df
        else:
            st.error("Impossible de trouver un planning équitable. Essayez de changer de mois.")

# --- AFFICHAGE ET MODIFICATION ---
if 'current_df' in st.session_state:
    st.subheader(f"Planning du mois : {month}/{year}")
    st.info("💡 Vous pouvez modifier les noms manuellement dans le tableau. Les statistiques se mettront à jour au clic sur Valider.")
    
    # Éditeur de tableau
    edited_df = st.data_editor(st.session_state['current_df'], use_container_width=True, num_rows="fixed")
    
    if st.button("✅ Valider ce planning et enregistrer les heures"):
        # On repart des stats actuelles
        new_stats = st.session_state['stats'].copy()
        
        # On calcule les heures travaillées dans le tableau affiché
        for name in NURSE_NAMES:
            jours = len(edited_df[edited_df['Jour'] == name])
            nuits = len(edited_df[edited_df['Nuit'] == name])
            tiihs = len(edited_df[edited_df['TIIH'] == name])
            
            # Calcul : Jour(12h) + Nuit(12h) + TIIH(7.7h)
            total_heures_mois = (jours * 12) + (nuits * 12) + (tiihs * 7.7)
            new_stats[name] += total_heures_mois
        
        st.session_state['stats'] = new_stats
        st.success("Statistiques enregistrées ! Le mois prochain sera équilibré en conséquence.")
        st.rerun() # Recharge la page pour mettre à jour la sidebar
