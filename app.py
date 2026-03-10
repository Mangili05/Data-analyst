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

# --- CSS PERSONALIZZATO (AGGIORNATO PER NASCONDERE "RUNNING") ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMarkdown h2 a { display: none !important; }
    .main { background-color: #0e1117; color: white; }
    
    /* NASCONDE LO STATUS "RUNNING" E GLI SPINNER */
    [data-testid="stStatusWidget"] {
        visibility: hidden;
        display: none;
    }
    
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

# --- HEADER ---
st.markdown("## FOOTBALL DATA ANALYST")
st.markdown("<p style='color: #8b949e;'>Pro Palazzolo U16 - Match Analysis</p>", unsafe_allow_html=True)

# --- INFO PARTITA ---
squadre_campionato = ["Breno", "Calcio Brusaporto", "Caravaggio", "Crema 1908", "FC Voluntas", "Leon", "Mario Rigamonti", "Ponte SP Mapello", "Pro Palazzolo", "Real Calepina", "Scanzorosciate", "Speranza Agrate", "Uesse Sarnico 1908", "Vighenzi Calcio", "Villa Valle", "Virtus CiseranoBergamo"]

with st.expander("ℹ️ Informazioni partita", expanded=True):
    c1, c2 = st.columns(2)
    with c1: 
        st.selectbox("Giornata", ["Seleziona giornata"] + list(range(1, 31)), key="g_key")
    with c2:
        st.date_input("Data", value=None, format="DD/MM/YYYY", key="d_key")
    
    c3, c4 = st.columns(2)
    with c3:
        st.selectbox("Squadra di casa", ["Seleziona squadra"] + squadre_campionato, key="h_key")
    with c4:
        st.selectbox("Squadra Ospite", ["Seleziona squadra"] + squadre_campionato, key="a_key")
    
    gc1, gc2 = st.columns(2)
    with gc1: 
        st.number_input("Gol casa", min_value=0, step=1, key="gh_key")
    with gc2: 
        st.number_input("Gol ospite", min_value=0, step=1, key="ga_key")

st.divider()

# --- LISTA CALCIATORI ---
lista_calciatori = ["Seleziona", "Betti Alessandro", "Bombardieri Lorenzo", "Bosetti Davide", "Calimeri Guido", "Colombo Lorenzo", "Dotti Alessandro", "Kala Gabriel", "Koxha Brajan", "Lancini Tommaso", "Membrini Luca", "Moretti Jacopo", "Palladio Andrea", "Pasqua Alberto", "Pelucchi Tommaso", "Pennacchio Stefano", "Pensa Maikol", "Piscitello Filippo", "Romualdi Gianmarco", "Scaglia Matteo", "Turelli Alessandro", "Zerbini Giorgio"]

# --- FUNZIONE SALVATAGGIO ---
def esegui_salvataggio(fase):
    s = f"_{st.session_state.reset_counter}"
    
    giornata = st.session_state.get('g_key')
    data_val = st.session_state.get('d_key')
    data_str = data_val.strftime("%d/%m/%Y") if data_val else ""
    s_casa = st.session_state.get('h_key')
    s_ospite = st.session_state.get('a_key')
    g_casa = st.session_state.get('gh_key')
    g_ospite = st.session_state.get('ga_key')
    
    if giornata == "Seleziona giornata" or s_casa == "Seleziona squadra" or s_ospite == "Seleziona squadra":
        st.error("⚠️ Compila i dati della partita in alto!")
        return

    try:
        if fase == "Costruzione dal Basso":
            nome_foglio = "Costruzione"
            cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipologia", "Modalità", "Esito finale"]
            record = {
                "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                "Gol casa": g_casa, "Gol ospite": g_ospite,
                "Inizio": st.session_state.get(f't_in{s}'), "Fine": st.session_state.get(f't_fi{s}'),
                "Tipologia": st.session_state.get(f'tipo_rad{s}'), "Modalità": st.session_state.get(f'mod_rad{s}'),
                "Esito finale": st.session_state.get(f'esito_rad{s}')
            }
        elif fase == "Azione Offensiva":
            nome_foglio = "Offensiva"
            cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Giocatore", "Coord_X", "Coord_Y"]
            coords = st.session_state.get('off_coords')
            record = {
                "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                "Gol casa": g_casa, "Gol ospite": g_ospite,
                "Inizio": st.session_state.get(f'off_in{s}'), "Fine": st.session_state.get(f'off_fi{s}'),
                "Tipo di azione": st.session_state.get(f'off_tipo_azione{s}'), "Canale": st.session_state.get(f'off_canale{s}'), 
                "Rifinitura": st.session_state.get(f'off_rif{s}'), "Esito finale": st.session_state.get(f'off_esito{s}'),
                "Giocatore": st.session_state.get(f'off_giocatore{s}', ""), "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
            }
        elif fase == "Azione Difensiva":
            nome_foglio = "Difensiva"
            cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Coord_X", "Coord_Y"]
            coords = st.session_state.get('def_tiro_coords')
            record = {
                "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                "Gol casa": g_casa, "Gol ospite": g_ospite,
                "Inizio": st.session_state.get(f'def_in{s}'), "Fine": st.session_state.get(f'def_fi{s}'),
                "Tipo di azione": st.session_state.get(f'def_tipo_azione{s}'), "Canale": st.session_state.get(f'def_canale_sviluppo{s}'),
                "Rifinitura": st.session_state.get(f'def_rif{s}'), "Esito finale": st.session_state.get(f'def_esito{s}'),
                "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
            }

        df_new = pd.DataFrame([record]).reindex(columns=cols)
        
        # OPERAZIONE SILENZIOSA
        with st.empty():
            st.cache_data.clear()
            existing_df = conn.read(worksheet=nome_foglio, ttl=0)
            updated_df = pd.concat([existing_df, df_new], ignore_index=True)
            conn.update(worksheet=nome_foglio, data=updated_df)

        st.session_state["mostra_toast"] = f"✅ Dati salvati in {nome_foglio}!"
        reset_campi()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Errore critico: {e}")

# --- LOGICA NOTIFICA (SOLO TOAST) ---
if "mostra_toast" in st.session_state:
    st.toast(st.session_state["mostra_toast"])
    del st.session_state["mostra_toast"]

# --- TABS ---
suffix = f"_{st.session_state.reset_counter}"
tabs = st.tabs(["⚽ Costruzione", "⚔️ Azione Offensiva", "🛡️ Azione Difensiva"])
    
# --- TAB 1: COSTRUZIONE ---
with tabs[0]:
    rc1, rc2 = st.columns(2)
    with rc1:
        st.text_input("Inizio", placeholder="min:sec", key=f"t_in{suffix}")
    with rc2:
        st.text_input("Fine", placeholder="min:sec", key=f"t_fi{suffix}")
    st.divider()
    c_sx, c_cent, c_dx = st.columns([1, 2.5, 1])
    with c_sx:
        st.radio("Tipologia", ["Statica", "Dinamica"], key=f"tipo_rad{suffix}", horizontal=True)
    with c_cent:
        _, inner_c, _ = st.columns([1, 2, 1])
        with inner_c:
            st.radio("Modalità", ["Bassa", "Manovrata", "Diretta"], key=f"mod_rad{suffix}", horizontal=True)
    with c_dx:
        st.radio("Esito finale", ["Positivo", "Negativo"], key=f"esito_rad{suffix}", horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Salva Costruzione"):
        ini_c = st.session_state.get(f"t_in{suffix}", "")
        fin_c = st.session_state.get(f"t_fi{suffix}", "")
        if len(ini_c) < 5 or len(fin_c) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Costruzione dal Basso")

# --- TAB 2: AZIONE OFFENSIVA ---
with tabs[1]:
    co1, co2 = st.columns(2)
    with co1:
        st.text_input("Inizio", placeholder="min:sec", key=f"off_in{suffix}")
        st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione offensiva", "Palla inattiva"], key=f"off_tipo_azione{suffix}")
    with co2:
        st.text_input("Fine", placeholder="min:sec", key=f"off_fi{suffix}")
        st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"off_canale{suffix}")
    
    co3, co4 = st.columns(2)
    with co3:
        st.selectbox("Rifinitura", ["Seleziona", "Cross/Trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "altro"], key=f"off_rif{suffix}")
    with co4:
        st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa", "Altro"], key=f"off_esito{suffix}")

    es_off_val = st.session_state.get(f"off_esito{suffix}")
    if es_off_val in ["Gol", "Tiro in porta", "Tiro fuori"]:
        st.selectbox("Giocatore", lista_calciatori, key=f"off_giocatore{suffix}")
        st.write("🎯 **Posizione Conclusione**")
        img_path = "campo.jpg"
        # --- Nella Tab 2 (Offensiva) ---
if os.path.exists(img_path):
    img = Image.open(img_path)
    
    # Calcoliamo l'altezza proporzionale per evitare lo schiacciamento
    larghezza_display = 408
    ratio = larghezza_display / img.size[0]
    altezza_proporzionale = int(img.size[1] * ratio)
    
    # Resize mantenendo le proporzioni originali
    img_res = img.resize((larghezza_display, altezza_proporzionale)) 
    
    if "off_coords" in st.session_state:
        draw = ImageDraw.Draw(img_res)
        x, y = st.session_state["off_coords"]["x"], st.session_state["off_coords"]["y"]
        draw.ellipse([x-5, y-5, x+5, y+5], fill="red", outline="white")
    
    # Visualizziamo con la larghezza corretta
    val = streamlit_image_coordinates(img_res, width=larghezza_display, key=f"campetto_off{suffix}")
            
            if val and (st.session_state.get("off_coords") != val):
                st.session_state["off_coords"] = val
                st.rerun()
    
    if st.button("💾 Salva Azione Offensiva"):
        ini_o = st.session_state.get(f"off_in{suffix}", "")
        fin_o = st.session_state.get(f"off_fi{suffix}", "")
        if len(ini_o) < 5 or len(fin_o) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Azione Offensiva")

# --- TAB 3: AZIONE DIFENSIVA ---
with tabs[2]:
    cd1, cd2 = st.columns(2)
    with cd1:
        st.text_input("Inizio", placeholder="min:sec", key=f"def_in{suffix}")
        st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione difensiva", "Palla inattiva"], key=f"def_tipo_azione{suffix}")
    with cd2:
        st.text_input("Fine", placeholder="min:sec", key=f"def_fi{suffix}")
        st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"def_canale_sviluppo{suffix}")

    cd3, cd4 = st.columns(2)
    with cd3:
        st.selectbox("Rifinitura", ["Seleziona", "Cross/trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "Altro"], key=f"def_rif{suffix}")
    with cd4:
        st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla riconquistata", "Altro"], key=f"def_esito{suffix}")

    es_def_val = st.session_state.get(f"def_esito{suffix}")
    if es_def_val in ["Gol", "Tiro in porta", "Tiro fuori"]:
        st.write("📍 **Punto del tiro subito**")
        img_d_path = "campo.jpg"
        # --- Nella Tab 2 (Offensiva) ---
if os.path.exists(img_path):
    img = Image.open(img_path)
    
    # Calcoliamo l'altezza proporzionale per evitare lo schiacciamento
    larghezza_display = 408
    ratio = larghezza_display / img.size[0]
    altezza_proporzionale = int(img.size[1] * ratio)
    
    # Resize mantenendo le proporzioni originali
    img_res = img.resize((larghezza_display, altezza_proporzionale)) 
    
    if "off_coords" in st.session_state:
        draw = ImageDraw.Draw(img_res)
        x, y = st.session_state["off_coords"]["x"], st.session_state["off_coords"]["y"]
        draw.ellipse([x-5, y-5, x+5, y+5], fill="red", outline="white")
    
    # Visualizziamo con la larghezza corretta
    val = streamlit_image_coordinates(img_res, width=larghezza_display, key=f"campetto_off{suffix}")
            
            if val_d and (st.session_state.get("def_tiro_coords") != val_d):
                st.session_state["def_tiro_coords"] = val_d
                st.rerun()
            
    if st.button("💾 Salva Azione Difensiva"):
        ini_d = st.session_state.get(f"def_in{suffix}", "")
        fin_d = st.session_state.get(f"def_fi{suffix}", "")
        if len(ini_d) < 5 or len(fin_d) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Azione Difensiva")







