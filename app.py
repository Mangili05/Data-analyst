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
        # ---------------------------------------------------------
        # 1️⃣ SEZIONE: COSTRUZIONI
        # ---------------------------------------------------------
        st.subheader("1️⃣ SEZIONE: COSTRUZIONI")
        try:
            df_cost = conn.read(worksheet="Costruzione", ttl=0)
            if df_cost.empty:
                st.warning("Nessun dato di costruzione disponibile.")
            else:
                import plotly.express as px
                
                g_filtro = st.selectbox("Seleziona Partita (Costruzione)", ["Tutte"] + sorted(df_cost['Giornata'].unique().tolist()), key="f_giornata_cost")
                if g_filtro != "Tutte":
                    df_cost = df_cost[df_cost['Giornata'] == g_filtro]

                st.markdown("#### Efficacia Generale Costruzioni")
                fig_pie = px.pie(df_cost, names='Esito finale', color='Esito finale',
                                 color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'}, hole=0.4)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_pie, use_container_width=True)

                st.markdown("#### Efficacia per Modalità")
                tipo_filtro = st.radio("Filtra per Tipologia:", ["Totale", "Statica", "Dinamica"], horizontal=True, key="f_tipo_cost")
                df_bar_data = df_cost.copy()
                if tipo_filtro != "Totale":
                    df_bar_data = df_bar_data[df_bar_data['Tipologia'] == tipo_filtro]

                df_grouped = df_bar_data.groupby(['Modalità', 'Esito finale']).size().reset_index(name='Conteggio')
                fig_bar = px.bar(df_grouped, x='Modalità', y='Conteggio', color='Esito finale', barmode='group',
                                 color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'},
                                 category_orders={"Modalità": ["Bassa", "Manovrata", "Diretta"]})
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_bar, use_container_width=True)

                st.markdown("#### Confronto Ritmo: Statica vs Dinamica")
                df_stacked = df_cost.groupby(['Tipologia', 'Esito finale']).size().reset_index(name='Conteggio')
                fig_stacked = px.bar(df_stacked, x='Tipologia', y='Conteggio', color='Esito finale',
                                     color_discrete_map={'Positivo': '#00FF00', 'Negativo': '#FF0000'})
                fig_stacked.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_stacked, use_container_width=True)

        except Exception as e:
            st.error(f"Errore Sezione Costruzioni: {e}")

        st.divider()

        # ---------------------------------------------------------
        # 2️⃣ SEZIONE: AZIONI OFFENSIVE
        # ---------------------------------------------------------
        st.subheader("2️⃣ SEZIONE: AZIONI OFFENSIVE")
        try:
            df_off = conn.read(worksheet="Offensiva", ttl=0)
            if df_off.empty:
                st.warning("Nessun dato offensivo disponibile.")
            else:
                import plotly.graph_objects as go

                # --- FILTRO GIORNATA ---
                g_off_filtro = st.selectbox("Seleziona Partita (Offensiva)", ["Tutte"] + sorted(df_off['Giornata'].unique().tolist()), key="f_giornata_off")
                df_off_filt = df_off.copy()
                if g_off_filtro != "Tutte":
                    df_off_filt = df_off_filt[df_off_filt['Giornata'] == g_off_filtro]

                # --- 1. MAPPA DEI TIRI DINAMICA (VERSIONE COMPATTA) ---
                st.markdown("#### 🏟️ Mappa dei Tiri")
                
                campo_visuale_height = 680 
                fig_pitch = go.Figure()
                
                pitch_green = "#228B22" 
                line_white = "#ffffff"

                # NOTA: Ora il campo "reale" parte da Y=30 per eliminare il vuoto a centrocampo
                y_inizio = 30 

                # 1. Rettangolo principale (Metà campo "tagliata")
                fig_pitch.add_shape(type="rect", x0=0, y0=y_inizio, x1=100, y1=100, 
                                    line=dict(color=line_white, width=3), fillcolor=pitch_green, layer="below")
                
                # 2. Area Grande (Y da 83.5 a 100)
                fig_pitch.add_shape(type="rect", x0=20, y0=83.5, x1=80, y1=100, line=dict(color=line_white, width=3)) 
                
                # 3. Area Piccola
                fig_pitch.add_shape(type="rect", x0=35, y0=94.5, x1=65, y1=100, line=dict(color=line_white, width=3)) 
                
                # 4. Dischetto
                fig_pitch.add_shape(type="circle", x0=49.2, y0=88.5, x1=50.8, y1=90.1, fillcolor=line_white, line=dict(color=line_white)) 
                
                # 5. Lunetta area di rigore
                fig_pitch.add_shape(type="path", path="M 35 83.5 C 40 78, 60 78, 65 83.5", line=dict(color=line_white, width=3))
                
                # 6. Lunetta centrocampo (posizionata ora su Y = y_inizio)
                # Abbiamo alzato la lunetta per farla apparire subito all'inizio del rettangolo
                fig_pitch.add_shape(type="path", path=f"M 37 {y_inizio} C 40 {y_inizio+8}, 60 {y_inizio+8}, 63 {y_inizio}", 
                                    line=dict(color=line_white, width=3))

                # 7. Porta
                fig_pitch.add_shape(type="rect", x0=42, y0=100, x1=58, y1=102, line=dict(color="#333333", width=4), fillcolor="#dddddd")

                esiti_map = {"Gol": "#FFD700", "Tiro in porta": "#00FF00", "Tiro fuori": "#FF0000"}
                symbols = {"Gol": "circle", "Tiro in porta": "diamond", "Tiro fuori": "x"}
                
                for esito, color in esiti_map.items():
                    df_e = df_off_filt[df_off_filt['Esito finale'] == esito]
                    if not df_e.empty:
                        fig_pitch.add_trace(go.Scatter(
                            x=df_e['Coord_X'], 
                            y=df_e['Coord_Y'], 
                            mode='markers', 
                            name=esito,
                            marker=dict(size=16, color=color, symbol=symbols[esito], line=dict(width=1.5, color="white")),
                            text=df_e['Giocatore'], 
                            hoverinfo='text+name'
                        ))
                
                # --- AGGIUSTAMENTO LAYOUT ---
                fig_pitch.update_layout(
                    xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, 101]), 
                    # Impostiamo il range della Y da 28 a 103 per centrare la vista sulla trequarti
                    yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[28, 103]), 
                    
                    yaxis_scaleanchor="x",
                    yaxis_scaleratio=1,
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=campo_visuale_height, 
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(
                        font=dict(color="white", size=14), 
                        orientation="v",
                        bgcolor='rgba(0,0,0,0.5)',
                        yanchor="bottom", y=0.02,
                        xanchor="right", x=0.98
                    )
                )
                
                # Visualizzazione a tutta larghezza
                st.plotly_chart(fig_pitch, use_container_width=True, config={'displayModeBar': False})

                col_off1, col_off2 = st.columns(2)

                with col_off1:
                    # --- 2. CANALI DI SVILUPPO (Barre Orizzontali) ---
                    st.markdown("#### Canali di Sviluppo")
                    df_canali = df_off_filt.groupby('Sviluppo').size().reset_index(name='Conteggio')
                    fig_canali = px.bar(df_canali, y='Sviluppo', x='Conteggio', orientation='h',
                                        color_discrete_sequence=['#1f67b5'])
                    fig_canali.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                    st.plotly_chart(fig_canali, use_container_width=True)

                with col_off2:
                    # --- 3. EFFICACIA RIFINITURA (Funnel) ---
                    st.markdown("#### Efficacia Rifinitura")
                    df_rif = df_off_filt.groupby(['Tipologia rifinitura', 'Esito finale']).size().reset_index(name='Conteggio')
                    fig_rif = px.funnel(df_rif, x='Conteggio', y='Tipologia rifinitura', color='Esito finale',
                                        color_discrete_map={'Gol': '#FFD700', 'Tiro in porta': '#00FF00', 'Tiro fuori': '#FF0000'})
                    fig_rif.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                    st.plotly_chart(fig_rif, use_container_width=True)

                # --- 4. CLASSIFICA MARCATORI / TIRATORI ---
                st.markdown("#### Performance Individuale (Tiri e Gol)")
                df_players = df_off_filt.groupby(['Giocatore', 'Esito finale']).size().reset_index(name='Tiri')
                fig_players = px.bar(df_players, x='Giocatore', y='Tiri', color='Esito finale',
                                     color_discrete_map={'Gol': '#FFD700', 'Tiro in porta': '#00FF00', 'Tiro fuori': '#FF0000'},
                                     barmode='stack')
                fig_players.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_players, use_container_width=True)

        except Exception as e:
            st.error(f"Errore Sezione Offensiva: {e}")

    # ---------------------------------------------------------
    # TAB PROFILO CALCIATORE (Invariata)
    # ---------------------------------------------------------
    with t_individuo:
        st.markdown("### Analisi Radar Comportamentale")
        c_rep1, c_rep2 = st.columns(2)
        with c_rep1: p_sel = st.selectbox("Seleziona Calciatore", lista_calciatori, key="p_radar_staff")
        with c_rep2: g_sel = st.selectbox("Filtro Sessione", ["Tutte le giornate"] + list(range(1, 31)), key="g_radar_staff")

        if p_sel != "Seleziona":
            try:
                df_ind = conn.read(worksheet="Individuale", ttl=0)
                df_player = df_ind[df_ind['Calciatore'] == p_sel]
                if g_sel != "Tutte le giornate": df_player = df_player[df_player['Giornata'] == g_sel]
                
                if df_player.empty:
                    st.warning(f"Nessun dato trovato per {p_sel}.")
                else:
                    import plotly.graph_objects as go
                    categorie = ['Resilienza', 'Comunicazione', 'Intensità', 'Accettazione', 'Leadership']
                    valori = [df_player[cat].mean() for cat in categorie]
                    media_squadra = [df_ind[cat].mean() for cat in categorie]

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(r=valori + [valori[0]], theta=categorie + [categorie[0]], fill='toself', name=f'Media {p_sel}', line=dict(color='#1f67b5')))
                    fig_radar.add_trace(go.Scatterpolar(r=media_squadra + [media_squadra[0]], theta=categorie + [categorie[0]], mode='lines', name='Media Squadra', line=dict(color='rgba(200, 200, 200, 0.5)', dash='dash')))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_radar, use_container_width=True)
                    st.button("🖨️ Stampa Report PDF (Browser)")
            except Exception as e:
                st.error(f"Errore caricamento radar: {e}")
