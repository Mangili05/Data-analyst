import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Football Data Analyst", layout="wide")

# --- CONFIGURAZIONE STILE CSS (Unificato) ---
st.markdown("""
    <style>
    .stApp { background-color: #1E3A8A; }
    
    /* Testi bianchi ovunque */
    h1, h2, h3, p, label, .stMarkdown { color: white !important; }
    .stSelectbox label p { color: white !important; }

    /* Logo in alto a destra */
    .logo-top-right {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }

    /* Bottoni bianchi (Landing Page) */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #ffffff;
        color: #1E3A8A !important;
        font-weight: bold;
        border: none;
    }
    
    /* Pulizia Sidebar */
    [data-testid="stSidebar"] { background-color: #112244; }
    
    /* Nascondi header Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- GESTIONE COUNTER PER RESET ---
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def reset_campi():
    st.session_state.reset_counter += 1
    if 'off_coords' in st.session_state: del st.session_state['off_coords']
    if 'def_tiro_coords' in st.session_state: del st.session_state['def_tiro_coords']

# --- DATI COMUNI ---
squadre_campionato = ["Breno", "Calcio Brusaporto", "Caravaggio", "Crema 1908", "FC Voluntas", "Leon", "Mario Rigamonti", "Ponte SP Mapello", "Pro Palazzolo", "Real Calepina", "Scanzorosciate", "Speranza Agrate", "Uesse Sarnico 1908", "Vighenzi Calcio", "Villa Valle", "Virtus CiseranoBergamo"]
lista_calciatori = ["Seleziona", "Betti Alessandro", "Bombardieri Lorenzo", "Bosetti Davide", "Calimeri Guido", "Colombo Lorenzo", "Dotti Alessandro", "Kala Gabriel", "Koxha Brajan", "Lancini Tommaso", "Membrini Luca", "Moretti Jacopo", "Palladio Andrea", "Pasqua Alberto", "Pelucchi Tommaso", "Pennacchio Stefano", "Pensa Maikol", "Piscitello Filippo", "Romualdi Gianmarco", "Scaglia Matteo", "Turelli Alessandro", "Zerbini Giorgio"]

# --- LOGICA DI ACCESSO ---
if "autenticato" not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.profilo = None

if not st.session_state.autenticato:
    # Logo in alto a destra solo nella landing
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(f'<div class="logo-top-right"><img src="data:image/png;base64,{data}" width="120"></div>', unsafe_allow_html=True)

    _, col_main, _ = st.columns([1, 2, 1])
    with col_main:
        st.markdown("<br><br><h1 style='text-align: center;'>⚽ ANALISI DATI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Benvenuto. Seleziona il tuo profilo per continuare.</p>", unsafe_allow_html=True)
        ruolo_scelto = st.selectbox("Chi sta accedendo?", ["Seleziona...", "Match Analyst", "Staff Tecnico"])
        
        permesso = False
        if ruolo_scelto == "Match Analyst":
            pwd = st.text_input("Codice Accesso", type="password")
            if pwd == "1234": permesso = True
        elif ruolo_scelto == "Staff Tecnico":
            permesso = True

        if st.button("ENTRA NELL'APP"):
            if ruolo_scelto != "Seleziona..." and permesso:
                st.session_state.autenticato = True
                st.session_state.profilo = ruolo_scelto
                st.rerun()
    st.stop()

# --- SIDEBAR (DOPO LOGIN - UNICA) ---
st.sidebar.image("logo.png", width=120)
st.sidebar.write(f"Utente: **{st.session_state.profilo}**")
if st.sidebar.button("⬅️ LOGOUT"):
    st.session_state.autenticato = False
    st.rerun()

ruolo = st.session_state.profilo

# =========================================================
# AREA DI LAVORO
# =========================================================
if ruolo == "Match Analyst":
    st.markdown("## 🛠️ CONSOLE MATCH ANALYST")
    scelta_analisi = st.segmented_control("MODALITÀ INSERIMENTO", ["Squadra", "Individuale"], default="Squadra")
    
    if scelta_analisi == "Squadra":
        # ... qui incolla la tua logica "SQUADRA" che avevi (Expander e Tabs) ...
        # (Per brevità non la reinserisco tutta, ma il tuo codice originale qui va bene)
        st.write("Area Inserimento Squadra caricata.")
    
    else:
        st.markdown("### 👤 VALUTAZIONE INDIVIDUALE")
        # ... qui incolla la tua logica "INDIVIDUALE" ...
        st.write("Area Inserimento Individuale caricata.")

elif ruolo == "Staff Tecnico":
    st.markdown("## 📊 DASHBOARD PERFORMANCE")
    # ... qui incolla la tua logica Radar/Looker Studio ...
    st.write("Area Visualizzazione Staff caricata.")
