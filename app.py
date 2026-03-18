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

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- GESTIONE COUNTER PER RESET ---
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def reset_campi():
    st.session_state.reset_counter += 1
    if 'off_coords' in st.session_state: del st.session_state['off_coords']
    if 'def_tiro_coords' in st.session_state: del st.session_state['def_tiro_coords']

# --- CSS ESSENZIALE (VERSIONE ORIGINALE) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #0e1117; color: white; }
    
    .logo-container {
        position: absolute;
        top: -35px;   
        right: -80px;  
        z-index: 999;
    }
    .block-container { 
        padding-top: 1.5rem !important; 
        position: relative; 
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        background-color: #1f67b5;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INSERIMENTO LOGO ---
logo_path = "logo.png"
if os.path.exists(logo_path):
    img_base64 = base64.b64encode(open(logo_path, "rb").read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_base64}" width="80"></div>', unsafe_allow_html=True)

# --- SIDEBAR DI NAVIGAZIONE (VERSIONE ORIGINALE) ---
with st.sidebar:
    st.markdown("### 🏟️ DASHBOARD")
    tipo_analisi = st.radio(
        "COSA VUOI ANALIZZARE?",
        ["👥 Analisi Squadra", "👤 Analisi Individuale"],
        index=0
    )
    st.divider()
    st.info("Seleziona la modalità per visualizzare i relativi form di inserimento.")

# --- HEADER DINAMICO ---
st.markdown(f"## {tipo_analisi.upper()}")
st.markdown(f"<p style='color: #8b949e;'>Pro Palazzolo U16 - {tipo_analisi}</p>", unsafe_allow_html=True)

# --- [RESTO DEL TUO CODICE PER INFO PARTITA E TABS...] ---
