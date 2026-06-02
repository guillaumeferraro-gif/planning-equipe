import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import json

st.title("Générateur de Planning Infirmières")

# Initialisation des statistiques si elles n'existent pas
if 'stats' not in st.session_state:
    st.session_state['stats'] = {"Alice": 0, "Bob": 0, "Clara": 0, "David": 0, "Eve": 0}

nurses = list(st.session_state['stats'].keys())

# Menu latéral
st.sidebar.header("Paramètres")
year = st.sidebar.selectbox("Année", [2024, 2025])
month = st.sidebar.slider("Mois", 1, 12)

if st.button("Générer le mois suivant"):
    # On passe les stats actuelles (historique) au moteur
    df = generate_schedule(nurses, year, month, st.session_state['stats'], [])
    if df is not None:
        st.session_state['current_df'] = df
    else:
        st.error("Pas de solution possible respectant les 48h.")

if 'current_df' in st.session_state:
    st.subheader(f"Planning de {month}/{year}")
    # TABLEAU ÉDITABLE : C'est ici que vous modifiez les noms à la main
    edited_df = st.data_editor(st.session_state['current_df'])
    
    if st.button("Valider ce mois et mettre à jour les statistiques"):
        # Logique pour recalculer les stats en fonction du tableau édité
        # (Chaque ligne = 12h pour celui de jour, 12h pour celui de nuit)
        for n in nurses:
            count_j = len(edited_df[edited_df['Jour'] == n])
            count_n = len(edited_df[edited_df['Nuit'] == n])
            # Simplification : 12h par shift
            st.session_state['stats'][n] += (count_j + count_n) * 12
        
        st.success("Statistiques enregistrées ! Le prochain mois en tiendra compte.")

st.sidebar.subheader("Compteur Heures Cumulées")
st.sidebar.write(st.session_state['stats'])
