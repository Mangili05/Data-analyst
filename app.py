import streamlit as st
import pandas as pd
import os
import base64
import plotly.graph_objects as go
from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
from streamlit_gsheets import GSheetsConnection

st.markdown("""
    <style>
    /* Forza il colore del testo nei bottoni e nei controlli segmentati */
    div.stButton > button, 
    div[data-baseweb="segmented-control"] button {
        color: #ffffff !important; /* Testo bianco */
        background-color: #262730; /* Sfondo scuro per contrasto, personalizzabile */
        border: 1px solid #4b4b4b;
    }

    /* Assicura che il testo rimanga visibile anche negli stati attivi/selezionati */
    div[data-baseweb="segmented-control"] button[aria-checked="true"] {
        color: #ffffff !important;
        background-color: #1f67b5 !important; /* Blu per l'opzione selezionata */
    }

    /* Colore del testo nelle etichette dei radio button e checkbox */
    .stMarkdown p, .stRadio label {
        color: #ffffff !important;
    }
    
    /* Forza visibilità scritte dentro i widget di input */
    input {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

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
# LOGICA MATCH ANALYST (RACCOLTA + VISUALIZZAZIONE)
# =========================================================
if ruolo == "Match Analyst":
    st.markdown("## 🛠️ CONSOLE MATCH ANALYST")
    st.markdown("<p style='color: #8b949e;'>Inserimento dati e gestione database</p>", unsafe_allow_html=True)

    # Nota: segmented_control è disponibile nelle versioni recenti di Streamlit
    scelta_analisi = st.segmented_control("MODALITÀ INSERIMENTO", ["Squadra", "Individuale"], default="Squadra")
    st.divider()

    if scelta_analisi == "Squadra":
        # --- PARTE SQUADRA ---
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

        # Funzione interna per il salvataggio
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
                    nome_foglio = "Costruzione"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipologia", "Modalità", "Esito finale"]
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite,
                        "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Inizio": st.session_state.get(f't_in{s}'), "Fine": st.session_state.get(f't_fi{s}'),
                        "Tipologia": st.session_state.get(f'tipo_rad{s}'), "Modalità": st.session_state.get(f'mod_rad{s}'), "Esito finale": st.session_state.get(f'esito_rad{s}')
                    }
                elif fase == "Azione Offensiva":
                    nome_foglio = "Offensiva"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Giocatore", "Coord_X", "Coord_Y"]
                    coords = st.session_state.get('off_coords')
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite, "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Inizio": st.session_state.get(f'off_in{s}'), "Fine": st.session_state.get(f'off_fi{s}'), "Tipo di azione": st.session_state.get(f'off_tipo_azione{s}'),
                        "Canale": st.session_state.get(f'off_canale{s}'), "Rifinitura": st.session_state.get(f'off_rif{s}'), "Esito finale": st.session_state.get(f'off_esito{s}'),
                        "Giocatore": st.session_state.get(f'off_giocatore{s}', ""), "Coord_X": coords['x'] if coords else "", "Coord_Y": coords['y'] if coords else ""
                    }
                elif fase == "Azione Difensiva":
                    nome_foglio = "Difensiva"
                    cols = ["Giornata", "Data", "Squadra casa", "Squadra ospite", "Gol casa", "Gol ospite", "Inizio", "Fine", "Tipo di azione", "Canale", "Rifinitura", "Esito finale", "Coord_X", "Coord_Y"]
                    coords = st.session_state.get('def_tiro_coords')
                    record = {
                        "Giornata": giornata, "Data": data_str, "Squadra casa": s_casa, "Squadra ospite": s_ospite, "Gol casa": st.session_state.get('gh_key'), "Gol ospite": st.session_state.get('ga_key'),
                        "Inizio": st.session_state.get(f'def_in{s}'), "Fine": st.session_state.get(f'def_fi{s}'), "Tipo di azione": st.session_state.get(f'def_tipo_azione{s}'),
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

        if "mostra_toast" in st.session_state:
            st.toast(st.session_state["mostra_toast"])
            del st.session_state["mostra_toast"]

        suffix = f"_{st.session_state.reset_counter}"
        tabs = st.tabs(["⚽ Costruzione", "⚔️ Azione Offensiva", "🛡️ Azione Difensiva"])

        with tabs[0]:
            rc1, rc2 = st.columns(2)
            with rc1: st.text_input("Inizio", placeholder="min:sec", key=f"t_in{suffix}")
            with rc2: st.text_input("Fine", placeholder="min:sec", key=f"t_fi{suffix}")
            c_sx, c_cent, c_dx = st.columns([1, 2.5, 1])
            with c_sx: st.radio("Tipologia", ["Statica", "Dinamica"], key=f"tipo_rad{suffix}", horizontal=True)
            with c_cent:
                _, inner_c, _ = st.columns([1, 2, 1])
                with inner_c: st.radio("Modalità", ["Bassa", "Manovrata", "Diretta"], key=f"mod_rad{suffix}", horizontal=True)
            with c_dx: st.radio("Esito finale", ["Positivo", "Negativo"], key=f"esito_rad{suffix}", horizontal=True)
            if st.button("💾 Salva Costruzione"): esegui_salvataggio("Costruzione dal Basso")

        with tabs[1]:
            co1, co2 = st.columns(2)
            with co1:
                st.text_input("Inizio", placeholder="min:sec", key=f"off_in{suffix}")
                st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione offensiva", "Palla inattiva"], key=f"off_tipo_azione{suffix}")
            with co2:
                st.text_input("Fine", placeholder="min:sec", key=f"off_fi{suffix}")
                st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"off_canale{suffix}")
            co3, co4 = st.columns(2)
            with co3: st.selectbox("Rifinitura", ["Seleziona", "Cross/Trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "altro"], key=f"off_rif{suffix}")
            with co4: st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla persa", "Altro"], key=f"off_esito{suffix}")
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
            if st.button("💾 Salva Azione Offensiva"): esegui_salvataggio("Azione Offensiva")

        with tabs[2]:
            cd1, cd2 = st.columns(2)
            with cd1:
                st.text_input("Inizio", placeholder="min:sec", key=f"def_in{suffix}")
                st.selectbox("Tipo di azione", ["Seleziona", "Azione manovrata", "Transizione difensiva", "Palla inattiva"], key=f"def_tipo_azione{suffix}")
            with cd2:
                st.text_input("Fine", placeholder="min:sec", key=f"def_fi{suffix}")
                st.selectbox("Canale", ["Seleziona", "Fascia sx", "Centro", "Fascia dx"], key=f"def_canale_sviluppo{suffix}")
            cd3, cd4 = st.columns(2)
            with cd3: st.selectbox("Rifinitura", ["Seleziona", "Cross/trav.", "Pass. filtrante", "Az. individuale", "Scarico", "Palla sopra", "Altro"], key=f"def_rif{suffix}")
            with cd4: st.selectbox("Esito finale", ["Seleziona", "Gol", "Tiro in porta", "Tiro fuori", "Palla riconquistata", "Altro"], key=f"def_esito{suffix}")
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
            if st.button("💾 Salva Azione Difensiva"): esegui_salvataggio("Azione Difensiva")

    else:
        # --- PARTE INDIVIDUALE (MATCH ANALYST) ---
        st.markdown("### 👤 VALUTAZIONE INDIVIDUALE")
        if "reset_ind" not in st.session_state: st.session_state.reset_ind = 0
        suffix_ind = f"_ind_{st.session_state.reset_ind}"

        ci1, ci2, ci3 = st.columns([1, 1, 2])
        with ci1: g_ind = st.selectbox("Giornata", ["Seleziona"] + list(range(1, 31)), key="g_ind_key")
        with ci2: t_ind = st.text_input("Minuto", placeholder="mm:ss", key=f"t_ind{suffix_ind}")
        with ci3: p_ind = st.selectbox("Calciatore", lista_calciatori, key=f"p_ind{suffix_ind}")
        
        st.divider()
        mappa_voti = {"N.D.": None, "🟢 Verde": 1.0, "🟡 Giallo": 0.5, "🔴 Rosso": 0.0}
        opts = list(mappa_voti.keys())
        
        col_ind1, col_ind2 = st.columns(2)
        with col_ind1:
            v_res = st.radio("Resilienza all'Errore", opts, index=0, horizontal=True, key=f"v_res{suffix_ind}")
            v_com = st.radio("Comunicazione Proattiva", opts, index=0, horizontal=True, key=f"v_com{suffix_ind}")
            v_int = st.radio("Intensità Mentale", opts, index=0, horizontal=True, key=f"v_int{suffix_ind}")
        with col_ind2:
            v_acc = st.radio("Accettazione delle Scelte", opts, index=0, horizontal=True, key=f"v_acc{suffix_ind}")
            v_lea = st.radio("Leadership / Spirito di Sacrificio", opts, index=0, horizontal=True, key=f"v_lea{suffix_ind}")
        
        note_txt = st.text_area("Note Tecnico/Comportamentali", placeholder="Inserisci osservazioni specifiche...", key=f"note{suffix_ind}")
        
        if st.button("💾 Salva Analisi Individuale"):
            if g_ind == "Seleziona" or p_ind == "Seleziona" or len(t_ind) < 5:
                st.error("⚠️ Compila tutti i campi correttamente.")
            else:
                try:
                    voti_validi = [mappa_voti[st.session_state[f"v_res{suffix_ind}"]], mappa_voti[st.session_state[f"v_com{suffix_ind}"]], mappa_voti[st.session_state[f"v_int{suffix_ind}"]], mappa_voti[st.session_state[f"v_acc{suffix_ind}"]], mappa_voti[st.session_state[f"v_lea{suffix_ind}"]]]
                    voti_filtrati = [v for v in voti_validi if v is not None]
                    totale_punti = sum(voti_filtrati) if voti_filtrati else 0
                    rec_ind = {"Giornata": g_ind, "Minuto": t_ind, "Calciatore": p_ind, "Resilienza": mappa_voti[st.session_state[f"v_res{suffix_ind}"]], "Comunicazione": mappa_voti[st.session_state[f"v_com{suffix_ind}"]], "Intensità": mappa_voti[st.session_state[f"v_int{suffix_ind}"]], "Accettazione": mappa_voti[st.session_state[f"v_acc{suffix_ind}"]], "Leadership": mappa_voti[st.session_state[f"v_lea{suffix_ind}"]], "Totale": totale_punti, "Note": note_txt}
                    df_ordine = ["Giornata", "Minuto", "Calciatore", "Resilienza", "Comunicazione", "Intensità", "Accettazione", "Leadership", "Totale", "Note"]
                    df_nuovo = pd.DataFrame([rec_ind]).reindex(columns=df_ordine)
                    st.cache_data.clear()
                    df_esistente = conn.read(worksheet="Individuale", ttl=0)
                    df_finale = pd.concat([df_esistente, df_nuovo], ignore_index=True)
                    conn.update(worksheet="Individuale", data=df_finale)
                    st.session_state["mostra_toast"] = f"✅ Analisi di {p_ind} salvata!"
                    st.session_state.reset_ind += 1
                    st.rerun()
                except Exception as e: st.error(f"❌ Errore: {e}")

# =========================================================
# LOGICA STAFF TECNICO (SOLO VISUALIZZAZIONE)
# =========================================================
elif ruolo == "Staff Tecnico":
    st.markdown("## 📊 DASHBOARD PERFORMANCE")
    st.markdown("<p style='color: #8b949e;'>Pro Palazzolo U16 - Area Consultazione Staff</p>", unsafe_allow_html=True)
    
    t_squadra, t_individuo = st.tabs(["📈 Analisi Collettiva", "👤 Profilo Calciatore"])

    with t_squadra:
        st.markdown("### 🏟️ Mappa Tiri Dinamica (Generata in Python)")
    
    try:
        import plotly.graph_objects as go

        # 1. Caricamento e Pulizia Dati
        df_off = conn.read(worksheet="Offensiva", ttl=0)
        
        # Convertiamo in numerico e rimuoviamo i missing
        df_off['Coord_X'] = pd.to_numeric(df_off['Coord_X'], errors='coerce')
        df_off['Coord_Y'] = pd.to_numeric(df_off['Coord_Y'], errors='coerce')
        df_shots = df_off.dropna(subset=['Coord_X', 'Coord_Y'])

        # Se usi segmented_control per filtrare per partita, fallo qui
        # df_shots = df_shots[df_shots['Giornata'] == giornata_selezionata]

        # Creazione Figura Plotly
        fig_pitch = go.Figure()

        # =========================================================
        # 2. DISEGNO DEL CAMPO (Coordinate 0-100)
        # Sfondo verde, linee bianche
        # =========================================================
        
        # Colore del campo e delle linee
        pitch_color = "#228B22" # Forest Green
        line_color = "#ffffff"   # Bianco

        # Rettangolo principale (Metà campo)
        # X: 0 (sinistra) a 100 (destra)
        # Y: 0 (linea di metà campo) a 100 (linea di porta)
        fig_pitch.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color=line_color, width=3), fillcolor=pitch_color, layer="below")

        # Area di Rigore
        # Grande: Larga 60% (da 20 a 80), Profonda 16.5% (da 83.5 a 100)
        fig_pitch.add_shape(type="rect", x0=20, y0=83.5, x1=80, y1=100, line=dict(color=line_color, width=3), fillcolor=pitch_color, layer="below")

        # Area di Porta (Area piccola)
        # Larga 30% (da 35 a 65), Profonda 5.5% (da 94.5 a 100)
        fig_pitch.add_shape(type="rect", x0=35, y0=94.5, x1=65, y1=100, line=dict(color=line_color, width=3), fillcolor=pitch_color, layer="below")

        # La Porta (esterna alla linea)
        fig_pitch.add_shape(type="rect", x0=42, y0=100, x1=58, y1=102, line=dict(color="#333333", width=4), fillcolor="#dddddd", layer="below")

        # Dischetto del Rigore (Punto a 11m -> 11% dalla porta)
        fig_pitch.add_shape(type="circle", x0=49.5, y0=88.5, x1=50.5, y1=89.5, line=dict(color=line_color), fillcolor=line_color)

        # Lunetta dell'Area di Rigore (Arco)
        fig_pitch.add_shape(type="path", path="M 35 83.5 C 40 78, 60 78, 65 83.5", line=dict(color=line_color, width=3), fillcolor=pitch_color, layer="below")

        # Cerchio di Centrocampo (Arco inferiore)
        fig_pitch.add_shape(type="path", path="M 40 0 C 42 7, 58 7, 60 0", line=dict(color=line_color, width=3), fillcolor=pitch_color, layer="below")


        # =========================================================
        # 3. PLOT DEI PUNTI (TIRI)
        # =========================================================
        esiti_config = {
            "Gol": {"color": "#FFD700", "symbol": "circle", "name": "⚽ Gol", "size": 18},
            "Tiro in porta": {"color": "#00FF00", "symbol": "diamond", "name": "✅ In Porta", "size": 14},
            "Tiro fuori": {"color": "#FF0000", "symbol": "x", "name": "❌ Fuori", "size": 14}
        }

        for esito, stile in esiti_config.items():
            mask = df_shots['Esito finale'] == esito
            df_filtered = df_shots[mask]
            
            if not df_filtered.empty:
                fig_pitch.add_trace(go.Scatter(
                    x=df_filtered['Coord_X'], 
                    y=df_filtered['Coord_Y'], 
                    mode='markers',
                    name=stile['name'],
                    marker=dict(
                        size=stile['size'],
                        color=stile['color'],
                        symbol=stile['symbol'],
                        line=dict(width=2, color='white')
                    ),
                    text=df_filtered['Giocatore'],
                    hoverinfo='text+name'
                ))

        # =========================================================
        # 4. LAYOUT E PROPORZIONI (Aspect Ratio fissa)
        # =========================================================
        fig_pitch.update_layout(
            # Nascondiamo assi e griglia
            xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-5, 105]), # Un po' di margine ai lati
            yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-5, 105]),
            
            # --- IL SEGRETO PER LE PROPORZIONI CORRETTE ---
            # Forziamo il grafico ad essere un quadrato perfetto (1:1) o rettangolo fisso
            yaxis_scaleanchor="x", # Y si adatta a X
            yaxis_scaleratio=1,    # Rapporto 1:1
            
            margin=dict(l=10, r=10, t=50, b=10),
            height=650, # Altezza generosa
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig_pitch, use_container_width=True)

    except Exception as e:
        st.error(f"Errore nella generazione della mappa dinamica: {e}")
