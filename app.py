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

# --- CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMarkdown h2 a { display: none !important; }
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

# --- HEADER ---
st.markdown("## FOOTBALL DATA ANALYST")
st.markdown("<p style='color: #8b949e;'>Pro Palazzolo U16 - Match Analysis</p>", unsafe_allow_html=True)

# --- INFO PARTITA ---
squadre_campionato = ["Breno", "Calcio Brusaporto", "Caravaggio", "Crema 1908", "FC Voluntas", "Leon", "Mario Rigamonti", "Ponte SP Mapello", "Pro Palazzolo", "Real Calepina", "Scanzorosciate", "Speranza Agrate", "Uesse Sarnico 1908", "Vighenzi Calcio", "Villa Valle", "Virtus CiseranoBergamo"]

with st.expander("ℹ️ Informazioni partita", expanded=True):
    c1, c2 = st.columns(2)
    with c1: 
        st.selectbox("Giornata", ["Seleziona giornata"] + list(range(1, 31)), key="g_key")
        st.date_input("Data", value=None, format="DD/MM/YYYY", key="d_key")
    with c2:
        st.selectbox("Squadra di casa", ["Seleziona squadra"] + squadre_campionato, key="h_key")
        st.selectbox("Squadra Ospite", ["Seleziona squadra"] + squadre_campionato, key="a_key")
    
    gc1, gc2 = st.columns(2)
    with gc1: st.number_input("Gol casa", min_value=0, step=1, key="gh_key")
    with gc2: st.number_input("Gol ospite", min_value=0, step=1, key="ga_key")

st.divider()

# --- LISTA CALCIATORI ---
lista_calciatori = ["Seleziona", "Betti Alessandro", "Bombardieri Lorenzo", "Bosetti Davide", "Calimeri Guido", "Colombo Lorenzo", "Dotti Alessandro", "Kala Gabriel", "Koxha Brajan", "Lancini Tommaso", "Membrini Luca", "Moretti Jacopo", "Palladio Andrea", "Pasqua Alberto", "Pelucchi Tommaso", "Pennacchio Stefano", "Pensa Maikol", "Piscitello Filippo", "Romualdi Gianmarco", "Scaglia Matteo", "Turelli Alessandro", "Zerbini Giorgio"]

# --- FUNZIONE SALVATAGGIO ---
def esegui_salvataggio(fase):
    s = f"_{st.session_state.reset_counter}"
    g = st.session_state.get('g_key')
    h = st.session_state.get('h_key')
    a = st.session_state.get('a_key')
    
    if g == "Seleziona giornata" or h == "Seleziona squadra" or a == "Seleziona squadra":
        st.warning("Compila le info partita!")
        return

    # Info comuni
    giornata = g
    data = st.session_state.get('d_key').strftime("%d/%m/%Y") if st.session_state.get('d_key') else ""
    s_casa = h
    s_ospite = a
    g_casa = st.session_state.get('gh_key')
    g_ospite = st.session_state.get('ga_key')

    # ORDINE COLONNE UNIFICATO (come da tua richiesta)
    cols_order = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Coord_X", "Coord_Y"]

    if fase == "Costruzione dal Basso":
        nome_foglio = "Costruzione"
        # Ordine colonne per GSheets (Tipologia, Modalità, Esito finale)
        cols_order_costr = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipologia", "Modalità", "Esito finale"]
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f't_in{s}'), 
            "Fine": st.session_state.get(f't_fi{s}'),
            "Tipologia": st.session_state.get(f'tipo_rad{s}'), 
            "Modalità": st.session_state.get(f'mod_rad{s}'), # Cambiato in radio
            "Esito finale": st.session_state.get(f'esito_rad{s}')
        }
        current_cols = cols_order_costr
    elif fase == "Azione Offensiva":
        nome_foglio = "Offensiva"
        coords = st.session_state.get('off_coords')
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f'off_in{s}'), "Fine": st.session_state.get(f'off_fi{s}'),
            "Tipo di azione": st.session_state.get(f'off_tipo_azione{s}'),
            "Canale": st.session_state.get(f'off_canale{s}'), 
            "Rifinitura": st.session_state.get(f'off_rif{s}'),
            "Esito finale": st.session_state.get(f'off_esito{s}'), 
            "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
        }
        current_cols = cols_order
    elif fase == "Azione Difensiva":
        nome_foglio = "Difensiva"
        coords = st.session_state.get('def_tiro_coords')
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f'def_in{s}'), "Fine": st.session_state.get(f'def_fi{s}'),
            "Tipo di azione": st.session_state.get(f'def_tipo_azione{s}'), 
            "Canale": st.session_state.get(f'def_canale_sviluppo{s}'),
            "Rifinitura": st.session_state.get(f'def_rif{s}'),
            "Esito finale": st.session_state.get(f'def_esito{s}'),
            "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
        }
        current_cols = cols_order

    try:
        df_new = pd.DataFrame([record]).reindex(columns=current_cols)
        st.cache_data.clear()
        existing_data = conn.read(worksheet=nome_foglio)
        updated_df = pd.concat([existing_data, df_new], ignore_index=True)
        conn.update(worksheet=nome_foglio, data=updated_df)
        st.session_state["messaggio_successo"] = f"✅ Salvato in {nome_foglio}!"
        reset_campi()
        st.rerun()
    except Exception as e:
        st.error(f"Errore: {e}")

if "messaggio_successo" in st.session_state:
    st.toast(st.session_state["messaggio_successo"])
    del st.session_state["messaggio_successo"]

# --- TABS ---
suffix = f"_{st.session_state.reset_counter}"
tabs = st.tabs(["⚽ Costruzione", "⚔️ Azione Offensiva", "🛡️ Azione Difensiva"])

# --- TAB 1: COSTRUZIONE ---
with tabs[0]:
    # Riga 1: Tempi
    rc1, rc2 = st.columns(2)
    with rc1:
        st.text_input("Inizio", placeholder="min:sec", key=f"t_in{suffix}")
    with rc2:
        st.text_input("Fine", placeholder="min:sec", key=f"t_fi{suffix}")
    
    st.divider()

    # Riga 2: Layout a "spinta esterna"
    # La colonna centrale larga (2.5) spinge le laterali verso i bordi
    c_sx, c_cent, c_dx = st.columns([1, 2.5, 1])
    
    with c_sx:
        # Allineato a sinistra sotto 'Inizio'
        st.radio("Tipologia", ["Statica", "Dinamica"], key=f"tipo_rad{suffix}", horizontal=True)
    
    with c_cent:
        # Modalità al centro esatto della pagina
        # Usiamo colonne interne per centrare i pallini nel grande spazio centrale
        _, inner_c, _ = st.columns([1, 2, 1])
        with inner_c:
            st.radio("Modalità", ["Bassa", "Manovrata", "Diretta"], key=f"mod_rad{suffix}", horizontal=True)
    
    with c_dx:
        # Esito finale forzato verso destra
        # Usiamo un allineamento interno che non lascia spazio a destra
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
        st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Palla recuperata", "Transizione offensiva", "Palla inattiva"], key=f"off_tipo_azione{suffix}")
    with co2:
        st.text_input("Fine", placeholder="min:sec", key=f"off_fi{suffix}")
        st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"off_canale{suffix}")
    
    co3, co4 = st.columns(2)
    with co3:
        # Rifinitura a SINISTRA
        st.selectbox("Rifinitura", ["Seleziona", "Cross/Trav.", "Filtrante", "Individuale", "Scarico", "Palla sopra"], key=f"off_rif{suffix}")
    with co4:
        # Esito Finale a DESTRA
        st.selectbox("Esito Finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa", "Altro"], key=f"off_esito{suffix}")

    # Recuperiamo il valore aggiornato per far apparire i campi condizionali
    es_off_val = st.session_state.get(f"off_esito{suffix}")

    # Logica condizionale: ora punta correttamente al valore della selectbox
    if es_off_val in ["Gol", "Tiro in porta", "Tiro fuori"]:
        st.selectbox("Giocatore", lista_calciatori, key=f"off_giocatore{suffix}")
        st.write("🎯 **Posizione Conclusione**")
        img_path = "campo.jpg"
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img_res = img.resize((500, int(img.size[1]*(500/img.size[0]))))
            
            # Gestione coordinate
            if "off_coords" in st.session_state:
                draw = ImageDraw.Draw(img_res)
                x, y = st.session_state["off_coords"]["x"], st.session_state["off_coords"]["y"]
                draw.ellipse([x-5, y-5, x+5, y+5], fill="red", outline="white")
            
            val = streamlit_image_coordinates(img_res, key=f"campetto_off{suffix}")
            if val and (st.session_state.get("off_coords") != val):
                st.session_state["off_coords"] = val
                st.rerun()
    
    # Bottone di salvataggio
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
        st.selectbox("Canale di sviluppo", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"def_canale_sviluppo{suffix}")

    cd3, cd4 = st.columns(2)
    with cd3:
        # Rifinitura a sinistra (sotto Tipo di azione)
        st.selectbox("Rifinitura", ["Seleziona", "Cross/trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "Altro"], key=f"def_rif{suffix}")
    with cd4:
        # Esito Finale a destra (sotto Canale di sviluppo)
        st.selectbox("Esito Finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla guadagnata", "Altro"], key=f"def_esito{suffix}")

    # Recupero valore per logica condizionale campetto
    es_def_val = st.session_state.get(f"def_esito{suffix}")

    if es_def_val in ["Gol", "Tiro in porta", "Tiro fuori"]:
        st.write("📍 **Punto del tiro subito**")
        img_d_path = "campo.jpg"
        if os.path.exists(img_d_path):
            img_d = Image.open(img_d_path)
            img_d_res = img_d.resize((500, int(img_d.size[1]*(500/img_d.size[0]))))
            
            if "def_tiro_coords" in st.session_state:
                draw_d = ImageDraw.Draw(img_d_res)
                x_d, y_d = st.session_state["def_tiro_coords"]["x"], st.session_state["def_tiro_coords"]["y"]
                draw_d.ellipse([x_d-5, y_d-5, x_d+5, y_d+5], fill="yellow", outline="black")
            
            val_d = streamlit_image_coordinates(img_d_res, key=f"campetto_def{suffix}")
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
















