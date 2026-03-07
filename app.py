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
    
    /* Rimuove l'icona del link/graffetta accanto ai titoli ## */
    .element-container:has(#football-data-analyst) a {
        display: none;
    }
    .stMarkdown h2 a {
        display: none !important;
    }
    
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
st.markdown("## FOOTBALL DATA ANALYST", help=None)
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

# --- FUNZIONE SALVATAGGIO GOOGLE SHEETS AGGIORNATA ---
def esegui_salvataggio(fase):
    s = f"_{st.session_state.reset_counter}"
    
    # --- RECUPERO VALORI TEMPORALI PER VALIDAZIONE ---
    if fase == "Costruzione dal Basso":
        ini_v = st.session_state.get(f"t_in{s}", "")
        fin_v = st.session_state.get(f"t_fi{s}", "")
    elif fase == "Azione Offensiva":
        ini_v = st.session_state.get(f"off_in{s}", "")
        fin_v = st.session_state.get(f"off_fi{s}", "")
    elif fase == "Azione Difensiva":
        ini_v = st.session_state.get(f"def_in{s}", "")
        fin_v = st.session_state.get(f"def_fi{s}", "")
    
    # Se meno di 5 caratteri, esce senza salvare
    if len(ini_v) < 5 or len(fin_v) < 5:
        return

    # Prosegue con i controlli normali
    g = st.session_state.get('g_key')
    h = st.session_state.get('h_key')
    a = st.session_state.get('a_key')
    
    if g == "Seleziona giornata" or h == "Seleziona squadra" or a == "Seleziona squadra":
        st.warning("Compila le info partita!")
        return

    # ... (Resto del codice: record, reindex, cache_clear, concat e update) ...

    # --- CONTROLLO INFO PARTITA ---
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

    # ... da qui in poi prosegue con i blocchi 'if fase ==' per la creazione del record ...

    if fase == "Costruzione dal Basso":
        nome_foglio = "Costruzione"
        cols_order = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo", "Modalità", "Esito"]
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f't_in{s}'), 
            "Fine": st.session_state.get(f't_fi{s}'),
            "Tipo": st.session_state.get(f'tipo_rad{s}'), 
            "Modalità": st.session_state.get(f'mod_sel{s}'),
            "Esito": st.session_state.get(f'esito_rad{s}')
        }

    elif fase == "Azione Offensiva":
        nome_foglio = "Offensiva"
        coords = st.session_state.get('off_coords')
        # ORDINE COLONNE RICHIESTO DA TE
        cols_order = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Canale", "Rifinitura", "Esito", "Giocatore", "Coord_X", "Coord_Y"]
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f'off_in{s}'), 
            "Fine": st.session_state.get(f'off_fi{s}'),
            "Canale": st.session_state.get(f'off_canale{s}'), 
            "Rifinitura": st.session_state.get(f'off_rif{s}'),
            "Esito": st.session_state.get(f'off_esito{s}'), 
            "Giocatore": st.session_state.get(f'off_giocatore{s}') if st.session_state.get(f'off_giocatore{s}') != "Seleziona" else "",
            "Coord_X": coords['x'] if coords else "", 
            "Coord_Y": coords['y'] if coords else ""
        }

    elif fase == "Azione Difensiva":
        nome_foglio = "Difensiva"
        tiro_coords = st.session_state.get('def_tiro_coords')
        cols_order = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo", "Provenienza", "Esito", "Causa", "Giocatore", "Esito Tiro", "Tiro_Coord_X", "Tiro_Coord_Y"]
        record = {
            "Giornata": giornata, "Data": data, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
            "Gol casa": g_casa, "Gol ospite": g_ospite,
            "Inizio": st.session_state.get(f'def_in{s}'), 
            "Fine": st.session_state.get(f'def_fi{s}'),
            "Tipo": st.session_state.get(f'def_tipo{s}'), 
            "Provenienza": st.session_state.get(f'def_prov{s}'),
            "Esito": st.session_state.get(f'def_esito{s}'), 
            "Causa": st.session_state.get(f'def_causa{s}'),
            "Giocatore": st.session_state.get(f'def_giocatore{s}') if st.session_state.get(f'def_giocatore{s}') != "Seleziona" else "",
            "Esito Tiro": st.session_state.get(f'def_esito_tiro{s}'),
            "Tiro_Coord_X": tiro_coords['x'] if tiro_coords else "", 
            "Tiro_Coord_Y": tiro_coords['y'] if tiro_coords else ""
        }

    try:
        # 1. Creiamo il DataFrame dal record appena creato
        df_new = pd.DataFrame([record])
        
        # 2. Riordiniamo le colonne del nuovo record secondo la lista cols_order
        df_new = df_new.reindex(columns=cols_order)
        
        # --- MODIFICA FONDAMENTALE ---
        # Puliamo la cache per assicurarci di leggere i dati aggiornati dal cloud
        st.cache_data.clear()
        
        # 3. Leggiamo i dati esistenti (ora leggerà sempre l'ultima riga salvata)
        existing_data = conn.read(worksheet=nome_foglio)
        
        # 4. Se il foglio è vuoto o ha colonne diverse, lo forziamo a seguire cols_order
        if existing_data.empty:
            updated_df = df_new
        else:
            # Assicuriamoci che anche i dati vecchi seguano lo stesso ordine prima di unire
            existing_data = existing_data.reindex(columns=cols_order)
            updated_df = pd.concat([existing_data, df_new], ignore_index=True)
        
        # 5. INVIO FINALE
        conn.update(worksheet=nome_foglio, data=updated_df)
        
        st.session_state["messaggio_successo"] = f"✅ Salvato correttamente in {nome_foglio}!"
        reset_campi()
        
        # NON mettiamo st.rerun() qui per evitare il messaggio giallo
        
    except Exception as e:
        st.error(f"Errore: {e}")

# Questo blocco fuori dalla funzione gestirà la notifica visiva
if "messaggio_successo" in st.session_state:
    st.toast(st.session_state["messaggio_successo"])
    del st.session_state["messaggio_successo"]

# --- TABS ---
suffix = f"_{st.session_state.reset_counter}"
tabs = st.tabs(["⚽ Costruzione", "⚔️ Offensiva", "🛡️ Difensiva"])

# --- TAB 1: COSTRUZIONE ---
with tabs[0]:
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.text_input("Inizio", placeholder="min:sec", key=f"t_in{suffix}")
        st.text_input("Fine", placeholder="min:sec", key=f"t_fi{suffix}")
    with r1c2:
        st.radio("Tipo", ["Statica", "Dinamica"], key=f"tipo_rad{suffix}")
        st.radio("Esito", ["Positivo", "Negativo"], key=f"esito_rad{suffix}")
    st.selectbox("Modalità", ["Seleziona", "Bassa", "Manovrata", "Diretta"], key=f"mod_sel{suffix}")
    btn_cost = st.button("💾 Salva Costruzione", on_click=esegui_salvataggio, args=("Costruzione dal Basso",))
    if st.button("💾 Salva Costruzione"):
        ini_c = st.session_state.get(f"t_in{suffix}", "")
        fin_c = st.session_state.get(f"t_fi{suffix}", "")
        if len(ini_c) < 5 or len(fin_c) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Costruzione dal Basso")

# --- TAB 2: OFFENSIVA ---
with tabs[1]:
    co1, co2 = st.columns(2)
    with co1:
        st.text_input("Inizio", placeholder="min:sec", key=f"off_in{suffix}")
        st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"off_canale{suffix}")
    with co2:
        st.text_input("Fine", placeholder="min:sec", key=f"off_fi{suffix}")
        st.selectbox("Rifinitura", ["Seleziona", "Cross/Trav.", "Filtrante", "Individuale", "Scarico", "Palla sopra"], key=f"off_rif{suffix}")
    
    es_off = st.selectbox("Esito Finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa", "Altro"], key=f"off_esito{suffix}")
    
    if es_off in ["Gol", "Tiro in porta", "Tiro fuori"]:
        st.selectbox("Giocatore", lista_calciatori, key=f"off_giocatore{suffix}")
        st.write("🎯 **Posizione Conclusione**")
        img_path = "campo.jpg"
        img = Image.open(img_path)
        img_res = img.resize((500, int(img.size[1]*(500/img.size[0]))))
        if "off_coords" in st.session_state:
            draw = ImageDraw.Draw(img_res); x, y = st.session_state["off_coords"]["x"], st.session_state["off_coords"]["y"]
            draw.ellipse([x-5, y-5, x+5, y+5], fill="red", outline="white")
        val = streamlit_image_coordinates(img_res, key=f"campetto_off{suffix}")
        if val and (st.session_state.get("off_coords") != val):
            st.session_state["off_coords"] = val; st.rerun()
    btn_off = st.button("💾 Salva Offensiva", on_click=esegui_salvataggio, args=("Azione Offensiva",))
    if st.button("💾 Salva Offensiva"):
        ini_o = st.session_state.get(f"off_in{suffix}", "")
        fin_o = st.session_state.get(f"off_fi{suffix}", "")
        if len(ini_o) < 5 or len(fin_o) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Azione Offensiva")

# --- TAB 3: DIFENSIVA ---
with tabs[2]:
    cd1, cd2 = st.columns(2)
    with cd1:
        st.text_input("Inizio", placeholder="min:sec", key=f"def_in{suffix}")
        st.selectbox("Tipo", ["Seleziona", "Azione manovrata", "Palla persa"], key=f"def_tipo{suffix}")
    with cd2:
        st.text_input("Fine", placeholder="min:sec", key=f"def_fi{suffix}")
        st.selectbox("Prov.", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"def_prov{suffix}")

    es_def = st.selectbox("Esito Difensivo", ["Seleziona", "Recuperata", "Tiro subito", "Gol subito"], key=f"def_esito{suffix}")

    if st.session_state.get(f"def_tipo{suffix}") == "Palla persa":
        st.selectbox("Chi ha sbagliato?", lista_calciatori, key=f"def_giocatore{suffix}")
        st.radio("Causa", ["Tecnico", "Scelta"], key=f"def_causa{suffix}", horizontal=True)

    if es_def in ["Tiro subito", "Gol subito"]:
        st.selectbox("Esito Tiro", ["Porta", "Fuori", "Respinto"], key=f"def_esito_tiro{suffix}")
        st.write("📍 **Punto del tiro**")
        img_d_path = "campo.jpg"
        img_d = Image.open(img_d_path)
        img_d_res = img_d.resize((500, int(img_d.size[1]*(500/img_d.size[0]))))
        if "def_tiro_coords" in st.session_state:
            draw_d = ImageDraw.Draw(img_d_res); x_d, y_d = st.session_state["def_tiro_coords"]["x"], st.session_state["def_tiro_coords"]["y"]
            draw_d.ellipse([x_d-5, y_d-5, x_d+5, y_d+5], fill="yellow", outline="black")
        val_d = streamlit_image_coordinates(img_d_res, key=f"campetto_def{suffix}")
        if val_d and (st.session_state.get("def_tiro_coords") != val_d):
            st.session_state["def_tiro_coords"] = val_d; st.rerun()
            
    btn_def = st.button("💾 Salva Difensiva", on_click=esegui_salvataggio, args=("Azione Difensiva",))
    if st.button("💾 Salva Difensiva"):
        ini_d = st.session_state.get(f"def_in{suffix}", "")
        fin_d = st.session_state.get(f"def_fi{suffix}", "")
        if len(ini_d) < 5 or len(fin_d) < 5:
            st.error("⚠️ Errore: Inserire il formato mm:ss (es. 04:10)")
        else:
            esegui_salvataggio("Azione Difensiva")





















