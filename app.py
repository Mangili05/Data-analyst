import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
from streamlit_gsheets import GSheetsConnection

# CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Football Data Analyst", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# INIZIALIZZAZIONE STATO
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def reset_campi():
    st.session_state.reset_counter += 1
    if 'off_coords' in st.session_state: del st.session_state['off_coords']
    if 'def_tiro_coords' in st.session_state: del st.session_state['def_tiro_coords']

# STYLE CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #0e1117; color: white; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1f67b5; color: white; }
    .logo-container { position: absolute; top: -35px; right: -80px; z-index: 999; }
    div[data-testid="stSegmentedControl"] { display: flex; justify-content: center; background-color: #1e2129; padding: 5px; border-radius: 12px; margin-bottom: 25px; }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] { background-color: #1f67b5 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# LOGO
logo_path = "logo.png"
if os.path.exists(logo_path):
    img_base64 = base64.b64encode(open(logo_path, "rb").read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_base64}" width="80"></div>', unsafe_allow_html=True)

st.markdown("## FOOTBALL DATA ANALYST")
st.markdown("<p style='color: #8b949e;'>Pro Palazzolo U16 - Match Analysis</p>", unsafe_allow_html=True)

# NAVIGAZIONE PRINCIPALE
tipo_analisi = st.segmented_control("NAVIGAZIONE", options=["Analisi Squadra", "Analisi Individuale"], default="Analisi Squadra", label_visibility="collapsed")
st.divider()

squadre_campionato = ["Breno", "Calcio Brusaporto", "Caravaggio", "Crema 1908", "FC Voluntas", "Leon", "Mario Rigamonti", "Ponte SP Mapello", "Pro Palazzolo", "Real Calepina", "Scanzorosciate", "Speranza Agrate", "Uesse Sarnico 1908", "Vighenzi Calcio", "Villa Valle", "Virtus Ciserano Bergamo"]
lista_calciatori = ["Seleziona", "Betti Alessandro", "Bombardieri Lorenzo", "Bosetti Davide", "Calimeri Guido", "Colombo Lorenzo", "Dotti Alessandro", "Kala Gabriel", "Koxha Brajan", "Lancini Tommaso", "Membrini Luca", "Moretti Jacopo", "Palladio Andrea", "Pasqua Alberto", "Pelucchi Tommaso", "Pennacchio Stefano", "Pensa Maikol", "Piscitello Filippo", "Romualdi Gianmarco", "Scaglia Matteo", "Turelli Alessandro", "Zerbini Giorgio"]

# --- LOGICA ANALISI SQUADRA ---
if tipo_analisi == "Analisi Squadra":
    with st.expander("ℹ️ Informazioni partita", expanded=True):
        c1, c2 = st.columns(2)
        with c1: st.selectbox("Giornata", ["Seleziona giornata"] + list(range(1, 31)), key="g_key")
        with c2: st.date_input("Data", value=None, format="DD/MM/YYYY", key="d_key")
        c3, c4 = st.columns(2)
        with c3: st.selectbox("Squadra di casa", ["Seleziona squadra"] + squadre_campionato, key="h_key")
        with c4: st.selectbox("Squadra Ospite", ["Seleziona squadra"] + squadre_campionato, key="a_key")
        gc1, gc2 = st.columns(2)
        with gc1: st.number_input("Gol casa", min_value=0, step=1, key="gh_key")
        with gc2: st.number_input("Gol ospite", min_value=0, step=1, key="ga_key")
    
    st.divider()

    def esegui_salvataggio(fase):
        s = f"_{st.session_state.reset_counter}"
        giornata = st.session_state.get('g_key')
        data_val = st.session_state.get('d_key')
        data_str = data_val.strftime("%d/%m/%Y") if data_val else ""
        s_casa = st.session_state.get('h_key')
        s_ospite = st.session_state.get('a_key')
        
        if giornata == "Seleziona giornata" or s_casa == "Seleziona squadra":
            st.error("⚠️ Compila i dati della partita!")
            return

        try:
            if fase == "Costruzione dal Basso":
                nome_foglio, cols = "Costruzione", ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipologia", "Modalità", "Esito finale"]
                record = {
                    "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": st.session_state.get('a_key'),
                    "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                    "Inizio": st.session_state.get(f't_in{s}'), "Fine": st.session_state.get(f't_fi{s}'),
                    "Tipologia": st.session_state.get(f'tipo_rad{s}'), "Modalità": st.session_state.get(f'mod_rad{s}'), "Esito finale": st.session_state.get(f'esito_rad{s}')
                }
            elif fase == "Azione Offensiva":
                nome_foglio, cols = "Offensiva", ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Giocatore", "Coord_X", "Coord_Y"]
                coords = st.session_state.get('off_coords')
                record = {
                    "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": st.session_state.get('a_key'),
                    "Inizio": st.session_state.get(f'off_in{s}'), "Fine": st.session_state.get(f'off_fi{s}'),
                    "Tipo di azione": st.session_state.get(f'off_tipo_azione{s}'), "Canale": st.session_state.get(f'off_canale{s}'),
                    "Esito finale": st.session_state.get(f'off_esito{s}'), "Giocatore": st.session_state.get(f'off_giocatore{s}', ""),
                    "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
                }
            elif fase == "Azione Difensiva":
                nome_foglio, cols = "Difensiva", ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Coord_X", "Coord_Y"]
                coords = st.session_state.get('def_tiro_coords')
                record = {
                    "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": st.session_state.get('a_key'),
                    "Inizio": st.session_state.get(f'def_in{s}'), "Fine": st.session_state.get(f'def_fi{s}'),
                    "Tipo di azione": st.session_state.get(f'def_tipo_azione{s}'), "Esito finale": st.session_state.get(f'def_esito{s}'),
                    "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
                }

            st.cache_data.clear()
            existing_df = conn.read(worksheet=nome_foglio, ttl=0)
            updated_df = pd.concat([existing_df, pd.DataFrame([record])], ignore_index=True)
            conn.update(worksheet=nome_foglio, data=updated_df)
            st.toast(f"✅ Salvato in {nome_foglio}")
            reset_campi()
            st.rerun()
        except Exception as e: st.error(f"Errore: {e}")

    suffix = f"_{st.session_state.reset_counter}"
    tabs = st.tabs(["⚽ Costruzione", "⚔️ Azione Offensiva", "🛡️ Azione Difensiva"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1: st.text_input("Inizio", key=f"t_in{suffix}")
        with c2: st.text_input("Fine", key=f"t_fi{suffix}")
        st.radio("Modalità", ["Bassa", "Manovrata", "Diretta"], key=f"mod_rad{suffix}", horizontal=True)
        if st.button("💾 Salva Costruzione"): esegui_salvataggio("Costruzione dal Basso")

    with tabs[1]:
        co1, co2 = st.columns(2)
        with co1: st.text_input("Inizio", key=f"off_in{suffix}")
        with co2: st.text_input("Fine", key=f"off_fi{suffix}")
        esito_off = st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa"], key=f"off_esito{suffix}")
        if esito_off in ["Gol", "Tiro in porta", "Tiro fuori"]:
            st.selectbox("Giocatore", lista_calciatori, key=f"off_giocatore{suffix}")
            img = Image.open("campo.jpg").resize((358, 283))
            val = streamlit_image_coordinates(img, key=f"c_off{suffix}")
            if val: st.session_state["off_coords"] = val
        if st.button("💾 Salva Offensiva"): esegui_salvataggio("Azione Offensiva")

    with tabs[2]:
        cd1, cd2 = st.columns(2)
        with cd1: st.text_input("Inizio", key=f"def_in{suffix}")
        with cd2: st.text_input("Fine", key=f"def_fi{suffix}")
        esito_def = st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Recuperata"], key=f"def_esito{suffix}")
        if esito_def in ["Gol", "Tiro in porta", "Tiro fuori"]:
            img = Image.open("campo.jpg").resize((358, 283))
            val_d = streamlit_image_coordinates(img, key=f"c_def{suffix}")
            if val_d: st.session_state["def_tiro_coords"] = val_d
        if st.button("💾 Salva Difensiva"): esegui_salvataggio("Azione Difensiva")

# --- LOGICA ANALISI INDIVIDUALE ---
else:
    st.markdown("### 👤 VALUTAZIONE INDIVIDUALE")
    ci1, ci2, ci3 = st.columns([1, 2, 1])
    with ci1: g_ind = st.selectbox("Giornata", ["Seleziona"] + list(range(1, 31)), key="g_ind_key")
    with ci2: p_ind = st.selectbox("Calciatore", lista_calciatori, key="p_ind_key")
    with ci3: t_ind = st.text_input("Minuto", key="t_ind_key")
    
    mappa_voti = {"N.D.": None, "🟢 Verde": 1.0, "🟡 Giallo": 0.5, "🔴 Rosso": 0.0}
    opts = list(mappa_voti.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        v_res = st.radio("Resilienza all'Errore", opts, index=0, horizontal=True, key="v_res")
        v_com = st.radio("Comunicazione Proattiva", opts, index=0, horizontal=True, key="v_com")
    with col2:
        v_acc = st.radio("Accettazione delle Scelte", opts, index=0, horizontal=True, key="v_acc")
        v_lea = st.radio("Leadership", opts, index=0, horizontal=True, key="v_lea")

    if st.button("💾 Salva Analisi Individuale"):
        if g_ind != "Seleziona" and p_ind != "Seleziona":
            try:
                rec = {"Giornata": g_ind, "Calciatore": p_ind, "Minuto": t_ind, "Resilienza": mappa_voti[v_res], "Comunicazione": mappa_voti[v_com], "Accettazione": mappa_voti[v_acc], "Leadership": mappa_voti[v_lea]}
                df_old = conn.read(worksheet="Individuale", ttl=0)
                df_up = pd.concat([df_old, pd.DataFrame([rec])], ignore_index=True)
                conn.update(worksheet="Individuale", data=df_up)
                st.success("Salvato!"); st.rerun()
            except Exception as e: st.error(f"Errore: {e}")
