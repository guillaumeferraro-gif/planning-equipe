import streamlit as st
import pandas as pd
from solver_logic import generate_schedule
import datetime

st.set_page_config(page_title="Planning IDE", layout="wide")
st.title("🗓️ Gestion du Planning Infirmières")

# Initialisation des stats (en HEURES)
if 'stats' not in st.session_state:
    st.session_state['stats'] = {"Alice": 0.0, "Bob": 0.0, "Clara": 0.0, "David": 0.0, "Eve": 0.0}

nurses = list(st.session_state['stats'].keys())

# Menu latéral
st.sidebar.header("Paramètres")
year = st.sidebar.selectbox("Année", [2024, 2025, 2026])
month = st.sidebar.slider("Mois", 1, 12, value=datetime.datetime.now().month)

if st.button("Générer le mois"):
    with st.spinner('Calcul du planning optimal en cours...'):
        df = generate_schedule(nurses, year, month, st.session_state['stats'], [])
        if df is not None:
            st.session_state['current_df'] = df
        else:
            st.error("❌ Pas de solution trouvée. Essayez d'alléger les contraintes ou de vérifier les 48h.")

if 'current_df' in st.session_state:
    st.subheader(f"Planning pour {month}/{year}")
    st.info("Vous pouvez modifier les noms directement dans le tableau ci-dessous.")
    
    # Affichage du tableau éditable
    edited_df = st.data_editor(st.session_state['current_df'], use_container_width=True)
    
    if st.button("✅ Valider ce planning et mettre à jour les compteurs"):
        # Recalcul des heures à partir du tableau (éventuellement modifié à la main)
        new_stats = st.session_state['stats'].copy()
        
        # Liste des jours TIIH pour le calcul des heures
        tiih_days = []
        for d in range(1, len(edited_df) + 1):
            if datetime.date(year, month, d).weekday() in [1, 3, 4]:
                tiih_days.append(f"{d}/{month}")

        for n in nurses:
            # On compte les jours et les nuits
            jours = len(edited_df[edited_df['Jour'] == n])
            nuits = len(edited_df[edited_df['Nuit'] == n])
            
            # On compte si certains de ces jours étaient des TIIH
            tiih_count = len(edited_df[(edited_df['Jour'] == n) & (edited_df['Date'].isin(tiih_days))])
            
            # Calcul total : (Jours * 12h) + (Nuits * 12h) + (TIIH * 7.7h)
            total_hours = (jours * 12) + (nuits * 12) + (tiih_count * 7.7)
            new_stats[n] += total_hours
        
        st.session_state['stats'] = new_stats
        st.success("Statistiques mises à jour ! Le mois prochain sera équilibré en fonction de ces nouveaux totaux.")

# Affichage des compteurs
st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Heures cumulées")
for n, h in st.session_state['stats'].items():
    st.sidebar.write(f"**{n}** : {round(h, 1)} h")
