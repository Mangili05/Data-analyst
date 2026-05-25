import streamlit as st
import pandas as pd
import os
import base64
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Football Data Analyst", layout="wide")

# --- 1. STILE CSS GLOBALE ---
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    footer {display: none !important;}
    
    .stApp { background-color: #1E3A8A; }
    h1, h2, h3, p, label, .stMarkdown { color: white !important; }
    div.stButton > button, div[data-baseweb="segmented-control"] button {
        color: #ffffff !important;
        background-color: #262730;
        border: 1px solid #4b4b4b;
    }
    div[data-baseweb="segmented-control"] button[aria-checked="true"] {
        color: #ffffff !important;
        background-color: #1f67b5 !important;
    }
    .block-container { padding-top: 130px !important; }
    .centered-header {
        position: fixed; top: 0; left: 0; right: 0;
        width: 100%; height: 110px; background-color: #1E3A8A;
        z-index: 9999; text-align: center; display: flex;
        align-items: center; justify-content: center;
        border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    .header-text { font-family: 'Inter', sans-serif !important; font-size: 50px !important; font-weight: 900 !important; text-transform: uppercase; }
    .fixed-logo-container { position: fixed; top: 10px; right: 25px; z-index: 10000; }
    .fixed-logo-img { width: 90px; height: auto; }
    @media (max-width: 768px) {
        .header-text { font-size: 26px !important; }
        .fixed-logo-img { width: 60px; }
        .centered-header { height: 80px; }
        .block-container { padding-top: 100px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER E LOGO ---
logo_base64 = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")

st.markdown(f"""
    <div class="centered-header">
        <h1 class="header-text"><span style="color: #ffffff;">#WEARE</span><span style="color: #D4AF37;">PRO</span></h1>
    </div>
    <div class="fixed-logo-container"><img src="data:image/png;base64,{logo_base64}" class="fixed-logo-img"></div>
""", unsafe_allow_html=True)

# --- CONNESSIONE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- VARIABILI DI STATO E DATI ---
if "reset_counter" not in st.session_state: st.session_state.reset_counter = 0
if "autenticato" not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.profilo = None

def reset_campi():
    st.session_state.reset_counter += 1
    for key in ['off_coords', 'def_tiro_coords']:
        if key in st.session_state: del st.session_state[key]

squadre_campionato = ["Breno", "Calcio Brusaporto", "Caravaggio", "Crema 1908", "FC Voluntas", "Leon", "Mario Rigamonti", "Ponte SP Mapello", "Pro Palazzolo", "Real Calepina", "Scanzorosciate", "Speranza Agrate", "Uesse Sarnico 1908", "Vighenzi Calcio", "Villa Valle", "Virtus CiseranoBergamo"]
lista_calciatori = ["Seleziona", "Betti Alessandro", "Bombardieri Lorenzo", "Bosetti Davide", "Calimeri Guido", "Colombo Lorenzo", "Dotti Alessandro", "Kala Gabriel", "Koxha Brajan", "Lancini Tommaso", "Membrini Luca", "Moretti Jacopo", "Palladio Andrea", "Pasqua Alberto", "Pelucchi Tommaso", "Pennacchio Stefano", "Pensa Maikol", "Piscitello Filippo", "Romualdi Gianmarco", "Scaglia Matteo", "Turelli Alessandro", "Zerbini Giorgio"]

# --- LOGIN ---
if not st.session_state.autenticato:
    _, col_main, _ = st.columns([1, 2, 1])
    with col_main:
        st.markdown("<h1 style='text-align: center;'>⚽ ANALISI DATI</h1>", unsafe_allow_html=True)
        ruolo_scelto = st.selectbox("Chi sta accedendo?", ["Seleziona...", "Match Analyst", "Staff Tecnico"])
        permesso = False
        if ruolo_scelto == "Match Analyst":
            pwd = st.text_input("Codice Accesso", type="password")
            if pwd == "1234": permesso = True
        elif ruolo_scelto == "Staff Tecnico": permesso = True

        if st.button("ENTRA NELL'APP"):
            if ruolo_scelto != "Seleziona..." and permesso:
                st.session_state.autenticato = True
                st.session_state.profilo = ruolo_scelto
                st.rerun()
    st.stop()

# =========================================================
# 1. LOGICA MATCH ANALYST
# =========================================================
if st.session_state.profilo == "Match Analyst":
    
    if st.button("⬅️ Torna alla Home"):
        st.session_state.autenticato = False
        st.session_state.profilo = None
        st.rerun()
    
    st.markdown("## 🛠️ CONSOLE MATCH ANALYST")
    scelta_analisi = st.segmented_control("OGGETTO DI ANALISI", ["Squadra", "Individuale"], default="Squadra")
    
    if scelta_analisi == "Squadra":
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

        # --- FUNZIONE DI SALVATAGGIO AGGIORNATA ---
        def esegui_salvataggio(fase):
            s = f"_{st.session_state.reset_counter}"
            giornata = st.session_state.get('g_key')
            data_val = st.session_state.get('d_key')
            data_str = data_val.strftime("%d/%m/%Y") if data_val else ""
            s_casa = st.session_state.get('h_key')
            s_ospite = st.session_state.get('a_key')
            frazione = st.session_state.get(f"frazione{s}")
            
            if frazione == "- Seleziona la frazione di gioco -" or giornata == "Seleziona giornata" or s_casa == "Seleziona squadra":
                st.error("⚠️ Compila tutti i dati (Partita e Frazione)!")
                return

            try:
                if fase == "Costruzione dal Basso":
                    nome_foglio = "Costruzione"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Frazione", "Inizio", "Tipologia", "Modalità", "Esito finale"]
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                        "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Frazione": frazione, "Inizio": st.session_state.get(f't_in{s}'),
                        "Tipologia": st.session_state.get(f'tipo_rad{s}'), "Modalità": st.session_state.get(f'mod_rad{s}'), "Esito finale": st.session_state.get(f'esito_rad{s}')
                    }
                elif fase == "Azione Offensiva":
                    nome_foglio = "Offensiva"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Frazione", "Inizio", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Giocatore", "Coord_X", "Coord_Y"]
                    coords = st.session_state.get('off_coords')
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite, "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Frazione": frazione, "Inizio": st.session_state.get(f'off_in{s}'), "Tipo di azione": st.session_state.get(f'off_tipo_azione{s}'),
                        "Canale": st.session_state.get(f'off_canale{s}'), "Rifinitura": st.session_state.get(f'off_rif{s}'), "Esito finale": st.session_state.get(f'off_esito{s}'),
                        "Giocatore": st.session_state.get(f'off_giocatore{s}', ""), "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
                    }
                elif fase == "Prima Pressione":
                    nome_foglio = "Pressione"
                    # Aggiunta la colonna "Tipologia di pressing"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Frazione", "Inizio", "Tipologia", "Tipo Costruzione", "Tipologia di pressing", "Esito finale"]
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                        "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Frazione": frazione, "Inizio": st.session_state.get(f'pp_in{s}'),
                        "Tipologia": st.session_state.get(f'pp_tipo{s}'), 
                        "Tipo Costruzione": st.session_state.get(f'pp_costruzione{s}'),
                        "Tipologia di pressing": st.session_state.get(f'pp_altezza{s}'), # Nuovo campo
                        "Esito finale": st.session_state.get(f'pp_esito{s}')
                    }
                elif fase == "Azione Difensiva":
                    nome_foglio = "Difensiva"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Frazione", "Inizio", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Coord_X", "Coord_Y"]
                    coords = st.session_state.get('def_tiro_coords')
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite, "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Frazione": frazione, "Inizio": st.session_state.get(f'def_in{s}'), "Tipo di azione": st.session_state.get(f'def_tipo_azione{s}'),
                        "Canale": st.session_state.get(f'def_canale_sviluppo{s}'), "Rifinitura": st.session_state.get(f'def_rif{s}'), "Esito finale": st.session_state.get(f'def_esito{s}'),
                        "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
                    }

                st.cache_data.clear()
                existing_df = conn.read(worksheet=nome_foglio, ttl=0)
                updated_df = pd.concat([existing_df, pd.DataFrame([record]).reindex(columns=cols)], ignore_index=True)
                conn.update(worksheet=nome_foglio, data=updated_df)
                st.session_state["mostra_toast"] = f"✅ Salvato in {nome_foglio}!"
                reset_campi()
                st.rerun()
            except Exception as e: st.error(f"❌ Errore: {e}")

        # --- SEZIONE UI TABS ---
        suffix = f"_{st.session_state.reset_counter}"
        tabs = st.tabs(["⚽ Costruzione", "⚔️ Azione Offensiva", "⚡ Prima Pressione", "🛡️ Azione Difensiva"])
        opzioni_frazione = ["- Seleziona la frazione di gioco -", "1° Tempo", "2° Tempo"]

        with tabs[0]:
            st.selectbox("Frazione di gioco", opzioni_frazione, key=f"frazione{suffix}")
            val_in = st.text_input("Inizio (Minuto Video)", placeholder="mm:ss", key=f"t_in{suffix}")
            if val_in and len(val_in) not in [5, 6]: st.caption(":red[Inserire 5 o 6 caratteri]")
            
            c_sx, c_cent, c_dx = st.columns([1, 2.5, 1])
            with c_sx: st.radio("Tipologia", ["Statica", "Dinamica"], key=f"tipo_rad{suffix}", horizontal=True)
            with c_cent:
                _, inner_c, _ = st.columns([1, 2, 1])
                with inner_c: st.radio("Modalità", ["Bassa", "Manovrata", "Diretta"], key=f"mod_rad{suffix}", horizontal=True)
            with c_dx: st.radio("Esito finale", ["Positivo", "Negativo"], key=f"esito_rad{suffix}", horizontal=True)
            
            if st.button("💾 Salva Costruzione"):
                if len(val_in) in [5, 6]: esegui_salvataggio("Costruzione dal Basso")
                else: st.error("⚠️ Inserire il minuto d'inizio (5 o 6 caratteri)!")

        with tabs[1]:
            st.selectbox("Frazione di gioco", opzioni_frazione, key=f"frazione{suffix}_off", on_change=lambda: st.session_state.update({f"frazione{suffix}": st.session_state[f"frazione{suffix}_off"]}))
            co1, co2 = st.columns(2)
            with co1:
                off_in = st.text_input("Inizio (Minuto Video)", placeholder="mm:ss", key=f"off_in{suffix}")
                if off_in and len(off_in) not in [5, 6]: st.caption(":red[Inserire 5 o 6 caratteri]")
                st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione offensiva", "Palla inattiva"], key=f"off_tipo_azione{suffix}")
            with co2:
                st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"off_canale{suffix}")
                st.selectbox("Rifinitura", ["Seleziona", "Cross/Trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "altro"], key=f"off_rif{suffix}")
            
            st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa", "Altro"], key=f"off_esito{suffix}")
            
            if st.session_state.get(f"off_esito{suffix}") in ["Gol", "Tiro in porta", "Tiro fuori"]:
                st.selectbox("Giocatore", lista_calciatori, key=f"off_giocatore{suffix}")
                if os.path.exists("campo.jpg"):
                    img = Image.open("campo.jpg").resize((358, 283))
                    if "off_coords" in st.session_state:
                        draw = ImageDraw.Draw(img)
                        x, y = st.session_state["off_coords"]["x"], st.session_state["off_coords"]["y"]
                        draw.ellipse([x-3, y-3, x+3, y+3], fill="red", outline="white")
                    val = streamlit_image_coordinates(img, key=f"campetto_off{suffix}")
                    if val and (st.session_state.get("off_coords") != val):
                        st.session_state["off_coords"] = val
                        st.rerun()
            
            if st.button("💾 Salva Azione Offensiva"):
                if len(off_in) in [5, 6]: esegui_salvataggio("Azione Offensiva")
                else: st.error("⚠️ Inserire il minuto d'inizio!")

        with tabs[2]: # --- TAB PRIMA PRESSIONE ORIZZONTALE ---
            st.selectbox("Frazione di gioco", opzioni_frazione, key=f"frazione{suffix}_pp", on_change=lambda: st.session_state.update({f"frazione{suffix}": st.session_state[f"frazione{suffix}_pp"]}))
            pp_in = st.text_input("Inizio (Minuto Video)", placeholder="mm:ss", key=f"pp_in{suffix}")
            if pp_in and len(pp_in) not in [5, 6]: st.caption(":red[Inserire 5 o 6 caratteri]")
            
            # Ho allargato un po' le proporzioni delle colonne per far stare i radio in orizzontale
            c_tipo, c_costr, c_press, c_esito = st.columns([1.2, 1.5, 2.5, 1.2])
            
            with c_tipo: 
                st.radio("Tipologia", ["Pressing", "Pressione"], key=f"pp_tipo{suffix}", horizontal=True)
            
            with c_costr:
                st.radio("Tipo di Costruzione", ["Statica", "Dinamica"], key=f"pp_costruzione{suffix}", horizontal=True)
            
            with c_press:
                st.radio("Tipologia di pressing", ["Ultra-offensiva", "Offensiva", "Difensiva"], key=f"pp_altezza{suffix}", horizontal=True)
            
            with c_esito: 
                st.radio("Esito finale", ["Positivo", "Negativo"], key=f"pp_esito{suffix}", horizontal=True)
            
            if st.button("💾 Salva Prima Pressione"):
                if len(pp_in) in [5, 6]: esegui_salvataggio("Prima Pressione")
                else: st.error("⚠️ Inserire il minuto d'inizio!")

        with tabs[3]:
            st.selectbox("Frazione di gioco", opzioni_frazione, key=f"frazione{suffix}_def", on_change=lambda: st.session_state.update({f"frazione{suffix}": st.session_state[f"frazione{suffix}_def"]}))
            cd1, cd2 = st.columns(2)
            with cd1:
                def_in = st.text_input("Inizio (Minuto Video)", placeholder="mm:ss", key=f"def_in{suffix}")
                if def_in and len(def_in) not in [5, 6]: st.caption(":red[Inserire 5 o 6 caratteri]")
                st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione difensiva", "Palla inattiva"], key=f"def_tipo_azione{suffix}")
            with cd2:
                st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"def_canale_sviluppo{suffix}")
                st.selectbox("Rifinitura", ["Seleziona", "Cross/trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "Altro"], key=f"def_rif{suffix}")
            
            st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla riconquistata", "Altro"], key=f"def_esito{suffix}")
            
            if st.session_state.get(f"def_esito{suffix}") in ["Gol", "Tiro in porta", "Tiro fuori"]:
                if os.path.exists("campo.jpg"):
                    img = Image.open("campo.jpg").resize((358, 283))
                    if "def_tiro_coords" in st.session_state:
                        draw = ImageDraw.Draw(img)
                        x, y = st.session_state["def_tiro_coords"]["x"], st.session_state["def_tiro_coords"]["y"]
                        draw.ellipse([x-3, y-3, x+3, y+3], fill="red", outline="white")
                    val_d = streamlit_image_coordinates(img, key=f"campetto_def{suffix}")
                    if val_d and (st.session_state.get("def_tiro_coords") != val_d):
                        st.session_state["def_tiro_coords"] = val_d
                        st.rerun()
            
            if st.button("💾 Salva Azione Difensiva"):
                if len(def_in) in [5, 6]: esegui_salvataggio("Azione Difensiva")
                else: st.error("⚠️ Inserire il minuto d'inizio!")

# =========================================================
# NUOVA LOGICA: ANALISI INDIVIDUALE (Sostituire la precedente)
# =========================================================
    else:
        st.markdown("### 🧠 MONITORAGGIO ATTITUDINALE PROIETTIVO")
        
        if "reset_ind" not in st.session_state: st.session_state.reset_ind = 0
        suffix_ind = f"_ind_{st.session_state.reset_ind}"
    
        # 1. SETUP SESSIONE
        ci1, ci2, ci3 = st.columns([1, 1, 2])
        with ci1: 
            tipo_sessione = st.radio("Contesto", ["Allenamento", "Partita"], horizontal=True, key=f"tipo_sess{suffix_ind}")
        with ci2: 
            data_sess = st.date_input("Data Osservazione", key=f"date_sess{suffix_ind}")
        with ci3: 
            ragazzi_focus = st.multiselect("Calciatori", lista_calciatori[1:], max_selections=4, key=f"focus_players{suffix_ind}")
    
        st.divider()
    
        if not ragazzi_focus:
            st.warning("Seleziona almeno un ragazzo.")
        else:
            dati_da_salvare = []
            
            for p_name in ragazzi_focus:
                with st.expander(f"Valutazione: {p_name}", expanded=True):
                    col_kpi, col_note = st.columns([2, 1])
                    with col_kpi:
                        if "Allenamento" in tipo_sessione:
                            k1 = st.slider(f"Intensità", 1, 5, 3, key=f"k1_{p_name}{suffix_ind}")
                            k2 = st.slider(f"Attenzione", 1, 5, 3, key=f"k2_{p_name}{suffix_ind}")
                            k3 = st.slider(f"Atteggiamento", 1, 5, 3, key=f"k3_{p_name}{suffix_ind}")
                            valori_riga = [k1, k2, k3, 0, 0, 0]
                        else:
                            k4 = st.slider(f"Efficacia Scelte", 1, 5, 3, key=f"k4_{p_name}{suffix_ind}")
                            k5 = st.slider(f"Leadership/Sacrificio", 1, 5, 3, key=f"k5_{p_name}{suffix_ind}")
                            k6 = st.slider(f"Resilienza Errore", 1, 5, 3, key=f"k6_{p_name}{suffix_ind}")
                            valori_riga = [0, 0, 0, k4, k5, k6]
    
                    with col_note:
                        nota = st.text_area("Note", key=f"nota_{p_name}{suffix_ind}")
    
                    dati_da_salvare.append({
                        "Giocatore": p_name,
                        "Contesto": tipo_sessione,
                        "Data": data_sess.strftime("%d/%m/%Y"),
                        "Intensità": valori_riga[0],
                        "Attenzione": valori_riga[1],
                        "Atteggiamento": valori_riga[2],
                        "Eff. scelte": valori_riga[3],
                        "Leadership": valori_riga[4],
                        "Resil. errore": valori_riga[5],
                        "Note": nota
                    })
    
            if st.button("💾 SALVA VALUTAZIONE", use_container_width=True):
                try:
                    st.cache_data.clear()
                    # 1. Creiamo il nuovo DataFrame
                    df_nuovo = pd.DataFrame(dati_da_salvare)
                    ordine_esatto = ["Giocatore", "Contesto", "Data", "Intensità", "Attenzione", "Atteggiamento", "Eff. scelte", "Leadership", "Resil. errore", "Note"]
                    df_nuovo = df_nuovo[ordine_esatto]
    
                    # 2. Leggiamo il database esistente
                    df_esistente = conn.read(worksheet="Individuale", ttl=0)
                    
                    # --- IL FIX CRUCIALE ---
                    # Tagliamo via qualsiasi colonna extra oltre la decima (Note) 
                    # e rinominiamo forzatamente le colonne per farle coincidere al 100%
                    df_esistente = df_esistente.iloc[:, :10] 
                    df_esistente.columns = ordine_esatto 
                    # -----------------------
    
                    # 3. Concateniamo e aggiorniamo
                    df_finale = pd.concat([df_esistente, df_nuovo], ignore_index=True)
                    conn.update(worksheet="Individuale", data=df_finale)
                    
                    st.success("✅ Salvataggio completato con successo nell'ordine corretto!")
                    st.session_state.reset_ind += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")

# --- QUI DEVE ESSERE ALLINEATO AL BORDO SINISTRO (o al livello del tuo IF iniziale) ---
elif st.session_state.profilo == "Staff Tecnico":
    if st.button("⬅️ Torna alla Home"):
        st.session_state.autenticato = False
        st.rerun()
    
    st.markdown("## 📊 DASHBOARD PERFORMANCE")
    st.markdown("<p style='color: #8b949e;'>Pro Palazzolo U16 - Area Consultazione Staff</p>", unsafe_allow_html=True)

    t_squadra, t_individuo = st.tabs(["📈 Analisi Collettiva", "👤 Profilo Calciatore"])

    with t_squadra:
        # 1. CARICAMENTO DATI (Con i nomi dei fogli corretti)
        try:
            df_cost = conn.read(worksheet="Costruzione", ttl=0)
            df_off = conn.read(worksheet="Offensiva", ttl=0)
            df_press = conn.read(worksheet="Pressione", ttl=0)
            df_dif = conn.read(worksheet="Difensiva", ttl=0)
        except Exception as e:
            st.error(f"Errore nel caricamento dei dati dal database: {e}")
            df_cost, df_off, df_press, df_dif = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # --- MODIFICA 1: SELEZIONE SEZIONE INTERFACCIA MATCH ANALYST ---
        opzioni_sezione = [
            "⚽ Costruzione", 
            "⚔️ Azione Offensiva", 
            "⚡ Prima Pressione", 
            "🛡️ Azione Difensiva"
        ]
        # Sostituisce il vecchio selectbox con pulsanti radio orizzontali e icone corrette
        fase_selezionata = st.radio(
            "📋 Seleziona la fase di gioco da analizzare", 
            opzioni_sezione, 
            horizontal=True,
            key="sezione_match_analyst"
        )


        # --- MODIFICA 2: SELEZIONE PARTITE FORMATTATA (Giornata X - Casa vs Ospiti) ---
        mappa_partite = {}
        
        # Estraiamo in modo dinamico le info combinando i fogli caricati correttamente
        for df in [df_cost, df_off, df_press, df_dif]:
            colonne_necessarie = ['Giornata', 'Squadra casa', 'Squadra ospite', 'Gol casa', 'Gol ospite']
            if not df.empty and all(col in df.columns for col in colonne_necessarie):
                # Rimuoviamo righe dove manca la Giornata
                df_valido = df.dropna(subset=['Giornata'])
                
                for _, row in df_valido.iterrows():
                    try:
                        # Pulizia del float (es. da 1.0 a 1)
                        giornata_num = int(float(row['Giornata']))
                        sq_casa = str(row['Squadra casa']).strip()
                        sq_ospite = str(row['Squadra ospite']).strip()
                        
                        # Gestione sicura dei gol (evita crash se il dato è momentaneamente vuoto)
                        g_casa = int(float(row['Gol casa'])) if pd.notna(row['Gol casa']) else 0
                        g_ospite = int(float(row['Gol ospite'])) if pd.notna(row['Gol ospite']) else 0
                        
                        # Creiamo la stringa leggibile richiesta
                        etichetta_visibile = f"Giornata {giornata_num} - {sq_casa} {g_casa}-{g_ospite} {sq_ospite}"
                        
                        # Mappiamo l'etichetta al VALORE ORIGINALE del foglio per non rompere i filtri successivi
                        mappa_partite[etichetta_visibile] = row['Giornata']
                    except:
                        continue
        
        # Ordiniamo l'elenco in base al numero reale della giornata (evita che la Giornata 10 appaia prima della 2)
        elenco_partite_formattato = sorted(
            list(mappa_partite.keys()), 
            key=lambda x: int(x.split("Giornata ")[1].split(" -")[0])
        )
        
        # Mostriamo la selectbox con i nomi delle gare reali e formattati
        scelta_partita = st.selectbox(
            "🎯 Seleziona la Partita da analizzare", 
            ["Tutte le Gare"] + elenco_partite_formattato, 
            key="filtro_global_staff"
        )

        # Recuperiamo il valore di filtro corretto (originale) associato alla stringa selezionata
        if scelta_partita != "Tutte le Gare":
            g_filtro = mappa_partite[scelta_partita]
        else:
            g_filtro = "Tutte le Gare"

        # Applicazione del filtro globale sui DataFrame
        if g_filtro != "Tutte le Gare":
            if not df_cost.empty and 'Giornata' in df_cost.columns: df_cost = df_cost[df_cost['Giornata'] == g_filtro]
            if not df_off.empty and 'Giornata' in df_off.columns: df_off = df_off[df_off['Giornata'] == g_filtro]
            if not df_press.empty and 'Giornata' in df_press.columns: df_press = df_press[df_press['Giornata'] == g_filtro]
            if not df_dif.empty and 'Giornata' in df_dif.columns: df_dif = df_dif[df_dif['Giornata'] == g_filtro]

        
        # ---------------------------------------------------------
        # SEZIONE: COSTRUZIONE (VERSIONE OTTIMIZZATA PER IL MISTER)
        # ---------------------------------------------------------
        if fase_selezionata == "⚽ Costruzione":
            st.subheader("⚽ ANALISI FASE DI COSTRUZIONE")
            
            if df_cost.empty:
                st.warning("Nessun dato di costruzione disponibile per questa selezione.")
            else:
                # --- FILTRO MACRO: FRAZIONE DI GIOCO ---
                # Questo filtro impatta TUTTI i grafici della sezione costruzione
                frazione_gioco = st.radio(
                    "Seleziona la frazione di gioco:", 
                    ["Tutta la Partita", "1° Tempo", "2° Tempo"], 
                    horizontal=True, 
                    key="f_tempo_costruzione"
                )
                
                # Identificazione dinamica della colonna del tempo/frazione per evitare KeyError
                colonna_tempo = None
                for col in ['Frazione', 'Tempo', 'frazione', 'tempo']:
                    if col in df_cost.columns:
                        colonna_tempo = col
                        break
                
                # Se non trova i nomi standard, fa un controllo più ampio
                if not colonna_tempo:
                    for col in df_cost.columns:
                        if 'fraz' in col.lower() or 'temp' in col.lower():
                            colonna_tempo = col
                            break
                
                # Creiamo il dataframe filtrato in base al tempo selezionato
                df_cost_filtrato = df_cost.copy()
                
                if colonna_tempo and frazione_gioco != "Tutta la Partita":
                    if frazione_gioco == "1° Tempo":
                        df_cost_filtrato = df_cost_filtrato[df_cost_filtrato[colonna_tempo].astype(str).str.contains('1')]
                    elif frazione_gioco == "2° Tempo":
                        df_cost_filtrato = df_cost_filtrato[df_cost_filtrato[colonna_tempo].astype(str).str.contains('2')]
                elif not colonna_tempo and frazione_gioco != "Tutta la Partita":
                    st.sidebar.error("⚠️ Colonna delle frazioni non trovata nel database Costruzione.")

                if df_cost_filtrato.empty:
                    st.warning(f"Nessun dato registrato per il {frazione_gioco} con la selezione attuale.")
                else:
                    # --- CALCOLO METRICHE FLASH ---
                    tot_cost = len(df_cost_filtrato)
                    pos_cost = len(df_cost_filtrato[df_cost_filtrato['Esito finale'] == 'Positivo'])
                    neg_cost = len(df_cost_filtrato[df_cost_filtrato['Esito finale'] == 'Negativo'])
                    
                    # Utilizzo di round() per l'arrotondamento matematico corretto
                    percentuale_successo = round((pos_cost / tot_cost) * 100) if tot_cost > 0 else 0
                    percentuale_perse = round((neg_cost / tot_cost) * 100) if tot_cost > 0 else 0

                    # Visualizzazione KPI veloci in alto
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Costruzioni Totali", tot_cost)
                    with col_m2:
                        st.metric("Efficaci (Positive) ✔️", f"{pos_cost} ({percentuale_successo}%)")
                    with col_m3:
                        st.metric("Perse (Negative) ❌", f"{neg_cost} ({percentuale_perse}%)")
                    
                    st.write("---")

                    # --- ROW 1: VISIONE GENERALE E CONTESTO (AFFIANCATI) ---
                    col_grafico1, col_grafico2 = st.columns(2)

                    with col_grafico1:
                        st.markdown("#### 📊 Efficacia Generale")
                        fig_pie = px.pie(df_cost_filtrato, names='Esito finale', color='Esito finale',
                                         color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'}, hole=0.4)
                        fig_pie.update_traces(textinfo='value+percent', textfont_size=14, 
                                              hovertemplate="<b>%{label}</b><br>Conteggio: %{value}<br>Percentuale: %{percent}")
                        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color="white"), dragmode=False,
                                              margin=dict(l=10, r=10, t=50, b=10),
                                              legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
                        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    with col_grafico2:
                        st.markdown("#### 🔄 Statica vs Dinamica")
                        df_tipo_grouped = df_cost_filtrato.groupby(['Tipologia', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_tipo = px.bar(df_tipo_grouped, x='Tipologia', y='Conteggio', color='Esito finale', barmode='group',
                                          color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'},
                                          category_orders={"Tipologia": ["Statica", "Dinamica"]})
                        fig_tipo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                               font=dict(color="white"), dragmode=False,
                                               xaxis_title=None, yaxis_title="Numero di Azioni",
                                               showlegend=True, 
                                               margin=dict(l=10, r=10, t=30, b=60),
                                               legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_tipo, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    st.write("---")

                    # --- ROW 2: IL DETTAGLIO DELLE MODALITÀ (CON FILTRO) ---
                    st.markdown("#### 🎯 Dettaglio per Modalità di Sviluppo")
                    
                    tipo_filtro = st.radio("Filtra il grafico sottostante per Tipo Sviluppo:", ["Totale", "Statica", "Dinamica"], horizontal=True, key="f_tipo_cost")
                    
                    df_bar_data = df_cost_filtrato.copy()
                    if tipo_filtro != "Totale":
                        df_bar_data = df_bar_data[df_bar_data['Tipologia'] == tipo_filtro]

                    if not df_bar_data.empty:
                        df_grouped = df_bar_data.groupby(['Modalità', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_bar = px.bar(df_grouped, x='Modalità', y='Conteggio', color='Esito finale', barmode='group',
                                         color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'},
                                         category_orders={"Modalità": ["Bassa", "Manovrata", "Diretta"]})
                        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color="white"), dragmode=False,
                                              xaxis_title=None, yaxis_title="Numero di Azioni",
                                              showlegend=True, 
                                              margin=dict(l=10, r=10, t=30, b=60),
                                              legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
                    else:
                        st.caption(f"Nessun dato registrato per la modalità {tipo_filtro} in questa selezione.")

        # ---------------------------------------------------------
        # SEZIONE: AZIONE OFFENSIVA
        # ---------------------------------------------------------
        elif fase_selezionata == "⚔️ Azione Offensiva":
            st.subheader("⚔️ ANALISI AZIONE OFFENSIVA")
            
            if df_off.empty:
                st.warning("Nessun dato offensivo disponibile per questa selezione.")
            else:
                # --- FILTRO MACRO: FRAZIONE DI GIOCO ---
                frazione_gioco = st.radio(
                    "Seleziona la frazione di gioco:", 
                    ["Tutta la Partita", "1° Tempo", "2° Tempo"], 
                    horizontal=True, 
                    key="f_tempo_offensiva"
                )
                
                # Controllo anti-crash colonna tempo/frazione
                colonna_tempo = None
                for col in ['Frazione', 'Tempo', 'frazione', 'tempo']:
                    if col in df_off.columns:
                        colonna_tempo = col
                        break
                
                # Creiamo il dataframe filtrato
                df_off_filtrato = df_off.copy()
                if colonna_tempo and frazione_gioco != "Tutta la Partita":
                    if frazione_gioco == "1° Tempo":
                        df_off_filtrato = df_off_filtrato[df_off_filtrato[colonna_tempo].astype(str).str.contains('1')]
                    elif frazione_gioco == "2° Tempo":
                        df_off_filtrato = df_off_filtrato[df_off_filtrato[colonna_tempo].astype(str).str.contains('2')]

                if df_off_filtrato.empty:
                    st.warning(f"Nessun dato registrato per il {frazione_gioco} con la selezione attuale.")
                else:
                    # --- CALCOLO METRICHE FLASH ---
                    tot_attacchi = len(df_off_filtrato)
                    
                    # Azioni concluse: Gol + Tiri in porta + Tiri fuori
                    df_concluse = df_off_filtrato[df_off_filtrato['Esito finale'].isin(['Gol', 'Tiro in porta', 'Tiro fuori'])]
                    num_concluse = len(df_concluse)
                    
                    # Gol segnati
                    num_gol = len(df_off_filtrato[df_off_filtrato['Esito finale'] == 'Gol'])
                    
                    # Percentuale di pericolosità (conversioni in tiro)
                    perc_conclusione = round((num_concluse / tot_attacchi) * 100) if tot_attacchi > 0 else 0

                    # Visualizzazione KPI
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Attacchi Totali", tot_attacchi)
                    with col_m2:
                        st.metric("Azioni Concluse (Tiri) 🎯", f"{num_concluse} ({perc_conclusione}%)")
                    with col_m3:
                        st.metric("Gol Segnati ⚽", num_gol)
                    
                    st.write("---")

                    # --- ROW 1: VISIONE GENERALE ED ESITI (AFFIANCATI) ---
                    col_grafico1, col_grafico2 = st.columns(2)

                    with col_grafico1:
                        st.markdown("#### 📊 Efficacia Finale")
                        fig_pie = px.pie(df_off_filtrato, names='Esito finale', color='Esito finale',
                                         color_discrete_map={
                                             'Gol': '#FFD700', 
                                             'Tiro in porta': '#00FF00', 
                                             'Tiro fuori': '#FF0000',
                                             'Palla persa': '#FF4500',
                                             'Altro': '#808080'
                                         }, hole=0.4)
                        fig_pie.update_traces(textinfo='value+percent', textfont_size=14, 
                                              hovertemplate="<b>%{label}</b><br>Conteggio: %{value}<br>Percentuale: %{percent}")
                        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color="white"), dragmode=False,
                                              margin=dict(l=10, r=10, t=50, b=10),
                                              legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
                        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    with col_grafico2:
                        st.markdown("#### 🔄 Sviluppo per Canale")
                        df_canali_grouped = df_off_filtrato.groupby(['Canale', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_canali = px.bar(df_canali_grouped, x='Canale', y='Conteggio', color='Esito finale', barmode='group',
                                            color_discrete_map={
                                                'Gol': '#FFD700', 'Tiro in porta': '#00FF00', 
                                                'Tiro fuori': '#FF0000', 'Palla persa': '#FF4500', 'Altro': '#808080'
                                            })
                        fig_canali.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                                 font=dict(color="white"), dragmode=False,
                                                 xaxis_title=None, yaxis_title="Numero di Azioni",
                                                 margin=dict(l=10, r=10, t=30, b=60),
                                                 legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_canali, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    st.write("---")

                    # --- ROW 2: DETTAGLIO TIPOLOGIA DI AZIONE (CON FILTRO) ---
                    st.markdown("#### 🎯 Dettaglio per Tipo di Azione")
                    
                    canale_selezionato = st.radio(
                        "Filtra il grafico sottostante per Canale di Sviluppo:", 
                        ["Totale"] + sorted(list(df_off_filtrato['Canale'].dropna().unique())), 
                        horizontal=True, 
                        key="f_canale_offensiva"
                    )
                    
                    df_azione_data = df_off_filtrato.copy()
                    if canale_selezionato != "Totale":
                        df_azione_data = df_azione_data[df_azione_data['Canale'] == canale_selezionato]

                    if not df_azione_data.empty:
                        df_az_grouped = df_azione_data.groupby(['Tipo di azione', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_azione = px.bar(df_az_grouped, x='Tipo di azione', y='Conteggio', color='Esito finale', barmode='group',
                                            color_discrete_map={
                                                'Gol': '#FFD700', 'Tiro in porta': '#00FF00', 
                                                'Tiro fuori': '#FF0000', 'Palla persa': '#FF4500', 'Altro': '#808080'
                                            })
                        fig_azione.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                                 font=dict(color="white"), dragmode=False,
                                                 xaxis_title=None, yaxis_title="Numero di Azioni",
                                                 margin=dict(l=10, r=10, t=30, b=60),
                                                 legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_azione, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
                    else:
                        st.caption(f"Nessun dato registrato per il canale {canale_selezionato} in questa selezione.")

                    st.write("---")

                    # --- ROW 3: MAPPA DEI TIRI (COORDINATE CORRETTE E MILLIMETRICHE) ---
                    st.markdown("#### 🏟️ Mappa dei Tiri e Pericolosità")
                    campo_visuale_height = 680 
                    fig_pitch = go.Figure()
                    pitch_green = "#228B22" 
                    line_white = "#ffffff"
                    y_inizio = 30 

                    # Disegno dello sfondo del campo (invariato)
                    fig_pitch.add_shape(type="rect", x0=0, y0=y_inizio, x1=100, y1=100, line=dict(color=line_white, width=3), fillcolor=pitch_green, layer="below")
                    fig_pitch.add_shape(type="rect", x0=20, y0=83.5, x1=80, y1=100, line=dict(color=line_white, width=3), layer="below") 
                    fig_pitch.add_shape(type="rect", x0=35, y0=94.5, x1=65, y1=100, line=dict(color=line_white, width=3), layer="below") 
                    fig_pitch.add_shape(type="circle", x0=49.2, y0=88.5, x1=50.8, y1=90.1, fillcolor=line_white, line=dict(color=line_white), layer="below") 
                    fig_pitch.add_shape(type="path", path="M 35 83.5 C 40 78, 60 78, 65 83.5", line=dict(color=line_white, width=3), layer="below")
                    fig_pitch.add_shape(type="path", path=f"M 37 {y_inizio} C 40 {y_inizio+8}, 60 {y_inizio+8}, 63 {y_inizio}", line=dict(color=line_white, width=3), layer="below")
                    fig_pitch.add_shape(type="rect", x0=42, y0=100, x1=58, y1=102, line=dict(color="#333333", width=4), fillcolor="#dddddd", layer="below")

                    esiti_map = {"Gol": "#FFD700", "Tiro in porta": "#00FF00", "Tiro fuori": "#FF0000"}
                    symbols = {"Gol": "circle", "Tiro in porta": "diamond", "Tiro fuori": "x"}
                    
                    for esito, color in esiti_map.items():
                        # Lavoriamo sul dataframe filtrato per il tempo corretto
                        df_e = df_off_filtrato[df_off_filtrato['Esito finale'] == esito].copy()
                        if not df_e.empty:
                            df_e['Coord_X'] = pd.to_numeric(df_e['Coord_X'], errors='coerce')
                            df_e['Coord_Y'] = pd.to_numeric(df_e['Coord_Y'], errors='coerce')
                            
                            # --- CALIBRAZIONE MATEMATICA DEFINITIVA ---
                            
                            # Scala X: Con 180 sul foglio, Plotly_X diventa esattamente 50.0 (centro perfetto)
                            df_e['Plotly_X'] = (df_e['Coord_X'] / 360) * 100
                            
                            # Scala Y: Con 75 sul foglio, Plotly_Y diventa esattamente 89.3 (centro del dischetto)
                            df_e['Plotly_Y'] = 100 - ((df_e['Coord_Y'] / 283) * 40.4)
                    
                            fig_pitch.add_trace(go.Scatter(
                                x=df_e['Plotly_X'], y=df_e['Plotly_Y'], mode='markers', name=esito,
                                marker=dict(size=18, color=color, symbol=symbols[esito], line=dict(width=2, color="white")),
                                text=(
                                    df_e['Giocatore'].astype(str) + "<br>" +
                                    "Azione: " + df_e['Tipo di azione'].astype(str) + "<br>" +
                                    "Via: " + df_e['Canale'].astype(str) + "<br>" +
                                    "Rif: " + df_e['Rifinitura'].astype(str)
                                ),
                                hoverinfo='text+name'
                            ))
                    
                    fig_pitch.update_layout(
                        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, 101]), 
                        # Range Y confermato: da 28 (visibile centrocampo) a 103 (linea di porta)
                        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[28, 103]), 
                        yaxis_scaleanchor="x", yaxis_scaleratio=1, margin=dict(l=0, r=0, t=10, b=0),
                        height=campo_visuale_height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=True, dragmode=False,
                        legend=dict(font=dict(color="white", size=14), orientation="h", bgcolor='rgba(0,0,0,0.5)', yanchor="top", y=-0.02, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_pitch, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

        # ---------------------------------------------------------
        # SEZIONE: PRIMA PRESSIONE (STRUTTURATA PER IL MISTER)
        # ---------------------------------------------------------
        elif fase_selezionata == "⚡ Prima Pressione":
            st.subheader("⚡ ANALISI PRIMA PRESSIONE")
            
            if df_press.empty:
                st.warning("Nessun dato di prima pressione disponibile per questa selezione.")
            else:
                # --- FILTRO MACRO: FRAZIONE DI GIOCO ---
                # Questo filtro impatta TUTTI i grafici della sezione prima pressione
                frazione_gioco = st.radio(
                    "Seleziona la frazione di gioco:", 
                    ["Tutta la Partita", "1° Tempo", "2° Tempo"], 
                    horizontal=True, 
                    key="f_tempo_pressione"
                )
                
                # Creiamo il dataframe filtrato in base al tempo selezionato
                df_press_filtrato = df_press.copy()
                if frazione_gioco == "1° Tempo":
                    # Gestisce sia se nel DB hai '1° Tempo' sia se hai solo il numero 1 o stringhe simili
                    df_press_filtrato = df_press_filtrato[df_press_filtrato['Frazione'].astype(str).str.contains('1')]
                elif frazione_gioco == "2° Tempo":
                    df_press_filtrato = df_press_filtrato[df_press_filtrato['Frazione'].astype(str).str.contains('2')]

                if df_press_filtrato.empty:
                    st.warning(f"Nessun dato registrato per il {frazione_gioco} con la selezione attuale.")
                else:
                    # --- CALCOLO METRICHE FLASH ---
                    tot_press = len(df_press_filtrato)
                    pos_press = len(df_press_filtrato[df_press_filtrato['Esito finale'] == 'Positivo'])
                    neg_press = len(df_press_filtrato[df_press_filtrato['Esito finale'] == 'Negativo'])
                    
                    # Arrotondamento matematico corretto come richiesto
                    percentuale_successo = round((pos_press / tot_press) * 100) if tot_press > 0 else 0
                    percentuale_perse = round((neg_press / tot_press) * 100) if tot_press > 0 else 0

                    # Visualizzazione KPI veloci in alto
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Pressioni Totali", tot_press)
                    with col_m2:
                        st.metric("Efficaci (Positive) ✔️", f"{pos_press} ({percentuale_successo}%)")
                    with col_m3:
                        st.metric("Inefficaci (Negative) ❌", f"{neg_press} ({percentuale_perse}%)")
                    
                    st.write("---")

                    # --- ROW 1: VISIONE GENERALE E CONTESTO (AFFIANCATI) ---
                    col_grafico1, col_grafico2 = st.columns(2)

                    with col_grafico1:
                        st.markdown("#### 📊 Efficacia Generale")
                        fig_pie = px.pie(df_press_filtrato, names='Esito finale', color='Esito finale',
                                         color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'}, hole=0.4)
                        fig_pie.update_traces(textinfo='value+percent', textfont_size=14, 
                                              hovertemplate="<b>%{label}</b><br>Conteggio: %{value}<br>Percentuale: %{percent}")
                        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color="white"), dragmode=False,
                                              margin=dict(l=10, r=10, t=50, b=10),
                                              legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
                        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    with col_grafico2:
                        st.markdown("#### 🔄 Statica vs Dinamica")
                        # Analisi basata sul tipo di costruzione avversaria ('Tipo Costruzione')
                        df_tipo_grouped = df_press_filtrato.groupby(['Tipo Costruzione', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_tipo = px.bar(df_tipo_grouped, x='Tipo Costruzione', y='Conteggio', color='Esito finale', barmode='group',
                                          color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'},
                                          category_orders={"Tipo Construction": ["Statica", "Dinamica"]})
                        fig_tipo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                               font=dict(color="white"), dragmode=False,
                                               xaxis_title=None, yaxis_title="Numero di Azioni",
                                               showlegend=True, 
                                               margin=dict(l=10, r=10, t=30, b=60),
                                               legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_tipo, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

                    st.write("---")

                    # --- ROW 2: DETTAGLIO TIPOLOGIA DI PRESSING (CON FILTRO) ---
                    st.markdown("#### 🎯 Dettaglio per Tipologia di Pressing")
                    
                    # Filtro locale per isolare l'altezza del pressing in base allo sviluppo avversario
                    tipo_cost_filtro = st.radio("Filtra il grafico sottostante per Costruzione Avversaria:", ["Totale", "Statica", "Dinamica"], horizontal=True, key="f_tipo_cost_press")
                    
                    df_bar_data = df_press_filtrato.copy()
                    if tipo_cost_filtro != "Totale":
                        df_bar_data = df_bar_data[df_bar_data['Tipo Costruzione'] == tipo_cost_filtro]

                    if not df_bar_data.empty:
                        df_grouped = df_bar_data.groupby(['Tipologia di pressing', 'Esito finale']).size().reset_index(name='Conteggio')
                        fig_bar = px.bar(df_grouped, x='Tipologia di pressing', y='Conteggio', color='Esito finale', barmode='group',
                                         color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'},
                                         category_orders={"Tipologia di pressing": ["Ultra-offensiva", "Offensiva", "Difensiva"]})
                        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color="white"), dragmode=False,
                                              xaxis_title=None, yaxis_title="Numero di Pressioni",
                                              showlegend=True, 
                                              margin=dict(l=10, r=10, t=30, b=60),
                                              legend=dict(orientation="h", title_text="", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
                    else:
                        st.caption(f"Nessun dato registrato per la tipologia {tipo_cost_filtro} in questa selezione.")

        # ==========================================
        # FASE 4: AZIONE DIFENSIVA
        # ==========================================
        elif fase_selezionata == "🛡️ Azione Difensiva":  
            st.markdown("### 🛡️ ANALISI FASE DI AZIONE DIFENSIVA")
            
            # --- 1. DEFINIZIONE DEL DATAFRAME DI BASE ---
            # Verifichiamo quale variabile usi nel tuo progetto per i dati difensivi
            if 'df_def' in locals() or 'df_def' in globals():
                df_base_def = df_def.copy()
            elif 'df_partita' in locals() or 'df_partita' in globals():
                # Se usi il df generale filtrato per la fase difensiva
                df_base_def = df_partita[df_partita['Fase di gioco'] == 'Azione Difensiva'].copy()
            else:
                # Fallback di sicurezza se la variabile ha un altro nome (es. df)
                df_base_def = df.copy() if 'df' in locals() else pd.DataFrame()

            if df_base_def.empty:
                st.warning("Nessun dato di azione difensiva disponibile per questa selezione.")
            else:
                # --- 2. FILTRO MACRO: FRAZIONE DI GIOCO (Coerente con Prima Pressione) ---
                frazione_gioco_def = st.radio(
                    "Seleziona la frazione di gioco:", 
                    ["Tutta la Partita", "1° Tempo", "2° Tempo"], 
                    horizontal=True, 
                    key="f_tempo_difensiva"
                )
                
                # Creazione del dataframe filtrato richiesto per far funzionare i grafici successivi
                df_def_filtrato = df_base_def.copy()
                if frazione_gioco_def == "1° Tempo":
                    df_def_filtrato = df_def_filtrato[df_def_filtrato['Frazione'].astype(str).str.contains('1')]
                elif frazione_gioco_def == "2° Tempo":
                    df_def_filtrato = df_def_filtrato[df_def_filtrato['Frazione'].astype(str).str.contains('2')]

                # Controllo finale sul DataFrame filtrato prima di mostrare i KPI
                if df_def_filtrato.empty:
                    st.warning(f"Nessun dato registrato per il {frazione_gioco_def} con la selezione attuale.")
                else:
                    # --- ROW 1: KPI CARDS ---
                    def_totati = len(df_def_filtrato)
                    def_positive = len(df_def_filtrato[df_def_filtrato['Esito finale'].isin(['Tiro fuori', 'Positivo'])]) 
                    def_negative = def_totati - def_positive
                    perc_efficacia = round((def_positive / def_totati) * 100) if def_totati > 0 else 0
            
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Azioni Difensive Totali", def_totati)
                    with col2:
                        st.metric("Efficaci (Positive) ✔️", f"{def_positive} ({perc_efficacia}%)")
                    with col3:
                        st.metric("Subite (Negative) ❌", def_negative)
            
                    st.write("---")
            
                    # --- ROW 2: GRAFICO A CIAMBELLA (EFFICACIA GENERALE) ---
                    st.markdown("#### 📊 Efficacia Generale")
                    df_eff = df_def_filtrato['Esito finale'].value_counts().reset_index()
                    df_eff.columns = ['Esito', 'Conteggio']
                    
                    color_colors = {'Positivo': '#00FF00', 'Negativo': '#FF0000', 'Tiro fuori': '#00FF00', 'Gol': '#FF0000', 'Tiro in porta': '#FFA500'}
                    colors_pie = [color_colors.get(x, '#FFFFFF') for x in df_eff['Esito']]
            
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=df_eff['Esito'], values=df_eff['Conteggio'], hole=.4,
                        marker=dict(colors=colors_pie, line=dict(color='#1e293b', width=2))
                    )])
                    fig_pie.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"), showlegend=True, height=350,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
                    st.write("---")
            
                    # --- ROW 3: GRAFICO A BARRE (STATICA VS DINAMICA) ---
                    st.markdown("#### 🔄 Statica vs Dinamica")
                    df_sd = df_def_filtrato.groupby(['Tipo di azione', 'Esito finale']).size().unstack(fill_value=0).reset_index()
                    
                    fig_bar_sd = go.Figure()
                    for col_esito in df_sd.columns[1:]:
                        fig_bar_sd.add_trace(go.Bar(
                            name=col_esito, x=df_sd['Tipo di azione'], y=df_sd[col_esito],
                            marker_color=color_colors.get(col_esito, '#FFFFFF')
                        ))
                    fig_bar_sd.update_layout(
                        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"), xaxis=dict(title="Modalità"), yaxis=dict(title="Numero di Azioni"),
                        height=350, margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig_bar_sd, use_container_width=True)
            
                    st.write("---")
            
                    # --- ROW 4: DETTAGLIO MODALITÀ DI SVILUPPO (CON FILTRO RADIO) ---
                    st.markdown("#### 🎯 Dettaglio per Modalità di Sviluppo")
                    scelta_sviluppo = st.radio("Filtra il grafico sottostante per Tipo Sviluppo:", ["Totale", "Statica", "Dinamica"], horizontal=True, key="radio_def")
                    
                    df_sviluppo = df_def_filtrato.copy()
                    if scelta_sviluppo != "Totale":
                        df_sviluppo = df_sviluppo[df_sviluppo['Tipo Sviluppo'] == scelta_sviluppo]
                        
                    if not df_sviluppo.empty and 'Modalità Sviluppo' in df_sviluppo.columns:
                        df_mod = df_sviluppo.groupby(['Modalità Sviluppo', 'Esito finale']).size().unstack(fill_value=0).reset_index()
                        
                        fig_bar_mod = go.Figure()
                        for col_esito in df_mod.columns[1:]:
                            fig_bar_mod.add_trace(go.Bar(
                                name=col_esito, x=df_mod['Modalità Sviluppo'], y=df_mod[col_esito],
                                marker_color=color_colors.get(col_esito, '#FFFFFF')
                            ))
                        fig_bar_mod.update_layout(
                            barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="white"), xaxis=dict(title="Sviluppo"), yaxis=dict(title="Numero di Azioni"),
                            height=400, margin=dict(l=20, r=20, t=20, b=20)
                        )
                        st.plotly_chart(fig_bar_mod, use_container_width=True)
                    else:
                        st.caption("Nessun dato disponibile per la modalità di sviluppo selezionata.")
            
                    st.write("---")
            
                    # --- ROW 5: MAPPA DEGLI EVENTI DIFENSIVI (CALIBRAZIONE PRECISA) ---
                    st.markdown("#### 🏟️ Mappa dei Tiri e Misure Difensive Subite")
                    campo_visuale_height = 680 
                    fig_pitch = go.Figure()
                    pitch_green = "#228B22" 
                    line_white = "#ffffff"
                    y_inizio = 30 
            
                    fig_pitch.add_shape(type="rect", x0=0, y0=y_inizio, x1=100, y1=100, line=dict(color=line_white, width=3), fillcolor=pitch_green, layer="below")
                    fig_pitch.add_shape(type="rect", x0=20, y0=83.5, x1=80, y1=100, line=dict(color=line_white, width=3), layer="below") 
                    fig_pitch.add_shape(type="rect", x0=35, y0=94.5, x1=65, y1=100, line=dict(color=line_white, width=3), layer="below") 
                    fig_pitch.add_shape(type="circle", x0=49.2, y0=88.5, x1=50.8, y1=90.1, fillcolor=line_white, line=dict(color=line_white), layer="below") 
                    fig_pitch.add_shape(type="path", path="M 35 83.5 C 40 78, 60 78, 65 83.5", line=dict(color=line_white, width=3), layer="below")
                    fig_pitch.add_shape(type="path", path=f"M 37 {y_inizio} C 40 {y_inizio+8}, 60 {y_inizio+8}, 63 {y_inizio}", line=dict(color=line_white, width=3), layer="below")
                    fig_pitch.add_shape(type="rect", x0=42, y0=100, x1=58, y1=102, line=dict(color="#333333", width=4), fillcolor="#dddddd", layer="below")
            
                    esiti_map = {"Gol": "#FFD700", "Tiro in porta": "#00FF00", "Tiro fuori": "#FF0000", "Positivo": "#00FF00", "Negativo": "#FF0000"}
                    symbols = {"Gol": "circle", "Tiro in porta": "diamond", "Tiro fuori": "x", "Positivo": "circle", "Negativo": "x"}
                    
                    for esito, color in esiti_map.items():
                        df_e = df_def_filtrato[df_def_filtrato['Esito finale'] == esito].copy()
                        if not df_e.empty:
                            df_e['Coord_X'] = pd.to_numeric(df_e['Coord_X'], errors='coerce')
                            df_e['Coord_Y'] = pd.to_numeric(df_e['Coord_Y'], errors='coerce')
                            
                            df_e['Plotly_X'] = (df_e['Coord_X'] / 360) * 100
                            df_e['Plotly_Y'] = 100 - ((df_e['Coord_Y'] / 283) * 40.4)
                    
                            fig_pitch.add_trace(go.Scatter(
                                x=df_e['Plotly_X'], y=df_e['Plotly_Y'], mode='markers', name=esito,
                                marker=dict(size=18, color=color, symbol=symbols.get(esito, "circle"), line=dict(width=2, color="white")),
                                text=(
                                    df_e['Giocatore'].astype(str) + "<br>" +
                                    "Azione: " + df_e['Tipo di azione'].astype(str) + "<br>" +
                                    "Via: " + df_e['Canale'].astype(str) + "<br>" +
                                    "Rif: " + df_e['Rifinitura'].astype(str)
                                ),
                                hoverinfo='text+name'
                            ))
                    
                    fig_pitch.update_layout(
                        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, 101]), 
                        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[28, 103]), 
                        yaxis_scaleanchor="x", yaxis_scaleratio=1, margin=dict(l=0, r=0, t=10, b=0),
                        height=campo_visuale_height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=True, dragmode=False,
                        legend=dict(font=dict(color="white", size=14), orientation="h", bgcolor='rgba(0,0,0,0.5)', yanchor="top", y=-0.02, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_pitch, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

# ---------------------------------------------------------
# TAB PROFILO CALCIATORE (Invariata come richiesto)
# ---------------------------------------------------------
    with t_individuo:
        st.markdown("### 🎯 Analisi Delle Prestazioni Individuali")
        
        try:
            # 1. Caricamento e Pulizia
            df_ind = conn.read(worksheet="Individuale", ttl=0)
            df_ind_clean = df_ind.copy()
            
            kpi_all = ['Intensità', 'Attenzione', 'Atteggiamento']
            kpi_gara = ['Eff. scelte', 'Leadership', 'Resil. errore']
            kpi_totali = kpi_all + kpi_gara
            
            df_ind_clean['Data'] = pd.to_datetime(df_ind_clean['Data'], dayfirst=True).dt.date
            for col in kpi_totali:
                df_ind_clean[col] = pd.to_numeric(df_ind_clean[col], errors='coerce').replace(0, pd.NA)

            # --- Funzione helper per le date con i giorni in italiano ---
            def formatta_data_ita(d):
                giorni_ita = {0: "lunedì", 1: "martedì", 2: "mercoledì", 3: "giovedì", 4: "venerdì", 5: "sabato", 6: "domenica"}
                return f"{d.strftime('%d-%m-%y')}, {giorni_ita[d.weekday()]}"

            # 2. Selezione Giocatori
            p_focus = st.multiselect("Seleziona uno o più atleti da analizzare", 
                                   lista_calciatori[1:], 
                                   max_selections=3,
                                   key="p_multi_staff")

            if not p_focus:
                st.info("💡 Seleziona uno o più calciatori per visualizzare l'analisi.")
            else:
                # --- 1. RADAR CHARTS CON LOGICA DI VISIBILITÀ ---
                st.markdown("#### 📊 Skill Set: Allenamento vs Partita")
                
                # Liste date separate per Allenamento e Partita
                date_all = sorted(df_ind_clean[df_ind_clean['Contesto'].str.contains("Allenamento", na=False)]['Data'].unique(), reverse=True)
                date_gara = sorted(df_ind_clean[df_ind_clean['Contesto'].str.contains("Partita", na=False)]['Data'].unique(), reverse=True)
                
                # Filtri separati per Radar Allenamento e Radar Partita
                c_rad1, c_rad2 = st.columns(2)
                with c_rad1:
                    sel_date_radar_all = st.multiselect("📅 Date Allenamento (vuoto = Totale)", 
                                                       options=date_all,
                                                       format_func=formatta_data_ita,
                                                       key="filter_date_radar_all")
                with c_rad2:
                    sel_date_radar_gara = st.multiselect("📅 Date Partita (vuoto = Totale)", 
                                                        options=date_gara,
                                                        format_func=formatta_data_ita,
                                                        key="filter_date_radar_gara")

                col_r1, col_r2 = st.columns(2)
                colori = ['#FFD700', '#00BFFF', '#FF4500'] 

                # Funzione interna per verificare se ci sono dati per quel contesto/data
                def get_filtered_data(contesto_filtro, date_filtro):
                    mask = (df_ind_clean['Giocatore'].isin(p_focus)) & \
                           (df_ind_clean['Contesto'].str.contains(contesto_filtro, na=False))
                    if date_filtro:
                        mask = mask & (df_ind_clean['Data'].isin(date_filtro))
                    return df_ind_clean[mask]

                # Dati filtrati per i due radar
                df_radar_all = get_filtered_data("Allenamento", sel_date_radar_all)
                df_radar_gara = get_filtered_data("Partita", sel_date_radar_gara)

                def create_radar_fig(df_filtered, kpis, titolo):
                    fig = go.Figure()
                    for i, p in enumerate(p_focus):
                        d_p = df_filtered[df_filtered['Giocatore'] == p]
                        if not d_p.empty:
                            valori = [d_p[k].mean() for k in kpis]
                            valori = [v if pd.notna(v) else 0 for v in valori]
                            fig.add_trace(go.Scatterpolar(
                                r=valori + [valori[0]], theta=kpis + [kpis[0]],
                                fill='toself', name=p,
                                line=dict(color=colori[i % len(colori)], width=2)
                            ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor="gray")),
                        template="plotly_dark", title=titolo, margin=dict(t=60, b=40, l=40, r=40),
                        paper_bgcolor='rgba(0,0,0,0)', showlegend=True if len(p_focus)>1 else False
                    )
                    return fig

                # Visualizzazione condizionale Radar
                with col_r1:
                    if not df_radar_all.empty:
                        st.plotly_chart(create_radar_fig(df_radar_all, kpi_all, "Focus Allenamento"), 
                                        use_container_width=True, config={'staticPlot': True})
                with col_r2:
                    if not df_radar_gara.empty:
                        st.plotly_chart(create_radar_fig(df_radar_gara, kpi_gara, "Focus Gara"), 
                                        use_container_width=True, config={'staticPlot': True})

                st.divider()

                # --- 2. BAR CHART COMPARATIVO ---
                st.markdown("#### ⚖️ Bilanciamento Attitudine vs Performance")
                
                c_date1, c_date2 = st.columns(2)
                with c_date1:
                    sel_date_all_bar = st.multiselect("📅 Date Allenamento", options=date_all, format_func=formatta_data_ita, key="bar_date_all")
                with c_date2:
                    sel_date_gara_bar = st.multiselect("📅 Date Partita", options=date_gara, format_func=formatta_data_ita, key="bar_date_gara")

                bar_data = []
                for p in p_focus:
                    d_p = df_ind_clean[df_ind_clean['Giocatore'] == p]
                    # Allenamento
                    m_all = d_p[(d_p['Contesto'].str.contains("Allenamento")) & (d_p['Data'].isin(sel_date_all_bar) if sel_date_all_bar else True)][kpi_all].mean().mean()
                    # Partita
                    m_gara = d_p[(d_p['Contesto'].str.contains("Partita")) & (d_p['Data'].isin(sel_date_gara_bar) if sel_date_gara_bar else True)][kpi_gara].mean().mean()
                    
                    if pd.notna(m_all): bar_data.append({"Calciatore": p, "Tipo": "Allenamento", "Valore": m_all})
                    if pd.notna(m_gara): bar_data.append({"Calciatore": p, "Tipo": "Partita", "Valore": m_gara})
                
                # Mostra il Bar Chart solo se ci sono dati
                if bar_data:
                    df_bar = pd.DataFrame(bar_data)
                    fig_bar = px.bar(df_bar, x="Calciatore", y="Valore", color="Tipo", barmode="group",
                                     color_discrete_map={"Allenamento": "#00CC96", "Partita": "#636EFA"},
                                     range_y=[0, 5], template="plotly_dark", text_auto='.1f')
                    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_bar, use_container_width=True, config={'staticPlot': True})

                st.divider()

                # --- 3. TIMELINE DI CRESCITA ---
                st.markdown("#### 📈 Timeline Evolutiva")
                
                # Setup Date per il filtro Timeline
                min_date = df_ind_clean['Data'].min()
                max_date = df_ind_clean['Data'].max()
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    filtro_time = st.radio("Mostra andamento per:", ["Entrambi", "Allenamento", "Partita"], horizontal=True)
                with col_t2:
                    if pd.isna(min_date) or pd.isna(max_date):
                        import datetime
                        min_date, max_date = datetime.date.today(), datetime.date.today()
                        
                    date_range = st.date_input("🗓️ Seleziona il periodo (Da - A)", 
                                               value=(min_date, max_date),
                                               min_value=min_date,
                                               max_value=max_date,
                                               format="DD/MM/YYYY",
                                               key="timeline_date_range")
                
                fig_time = go.Figure()
                any_data_timeline = False

                for i, p in enumerate(p_focus):
                    d_p = df_ind_clean[df_ind_clean['Giocatore'] == p].copy()
                    d_p = d_p.sort_values('Data')
                    
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_date, end_date = date_range
                        d_p = d_p[(d_p['Data'] >= start_date) & (d_p['Data'] <= end_date)]
                    elif isinstance(date_range, tuple) and len(date_range) == 1:
                        d_p = d_p[d_p['Data'] == date_range[0]]
                        
                    d_p['Media_Sessione'] = d_p[kpi_totali].mean(axis=1)
                    
                    if filtro_time != "Entrambi":
                        d_p = d_p[d_p['Contesto'].str.contains(filtro_time, na=False)]
                    
                    if not d_p.empty:
                        any_data_timeline = True
                        fig_time.add_trace(go.Scatter(x=d_p['Data'], y=d_p['Media_Sessione'],
                                                    mode='lines+markers', name=p,
                                                    line=dict(color=colori[i % len(colori)], width=3),
                                                    marker=dict(size=10)))

                if any_data_timeline:
                    fig_time.update_layout(
                        template="plotly_dark", 
                        yaxis_range=[0, 5.2],
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_title="Data Osservazione", 
                        yaxis_title="Valutazione Media",
                        hovermode="x unified",
                        xaxis=dict(
                            type='date',           
                            tickformat="%d-%m-%Y", 
                            hoverformat="%d-%m-%Y" 
                        )
                    )
                    st.plotly_chart(fig_time, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            st.error(f"Errore nella generazione dei grafici individuali: {e}")
