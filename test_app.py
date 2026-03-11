import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pydeck as pdk

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Erbario Digitale Haldin", page_icon="🌳", layout="wide")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1NP6G6MGH2NTXlEJ8MsR0f5RsLW_oxYZRCpBj6NsUG6w/edit"
CARTELLA_FOTO = "foto_alberi"

if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# --- RECUPERO DATI E TITOLO COMPATTO ---
try:
    df_raw = conn.read(spreadsheet=URL_FOGLIO, ttl=0).dropna(how='all')
    totale = len(df_raw) if not df_raw.empty else 0
except:
    totale = 0
    df_raw = pd.DataFrame()

# Titolo e Contatore sulla stessa riga
st.markdown(f"""
    <div style='display: flex; align-items: baseline;'>
        <h6 style='margin: 0; padding-right: 8px;'>🌳 Registro Haldin</h6>
        <span style='color: #2e7d32; font-weight: bold; font-size: 0.9em;'>({totale} alberi)</span>
    </div>
    <hr style='margin: 8px 0;'>
""", unsafe_allow_html=True)

loc = get_geolocation()

# --- SIDEBAR PER INSERIMENTO ---
if loc is not None and 'coords' in loc:
    with st.sidebar:
        st.header("📝 Nuova Rilevazione")
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success("📍 GPS Pronto")
        
        with st.form("modulo_inserimento", clear_on_submit=True):
            specie = st.text_input("Specie (Genere e Specie):", placeholder="Es: Quercus robur")
            stato = st.selectbox("Stato dell'albero:", 
                                ["🟢 Ottimo", "🟡 Da monitorare", "🔴 Malato/Danneggiato", "⚪ Solo tronco"])
            foto_file = st.camera_input("Scatta una foto")
            submit = st.form_submit_button("🚀 Registra e Salva")
            
            if submit:
                if specie and foto_file:
                    try:
                        nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        path_foto = os.path.join(CARTELLA_FOTO, nome_f)
                        with open(path_foto, "wb") as f:
                            f.write(foto_file.getbuffer())
                        
                        df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                        nuova_riga = pd.DataFrame([{
                            "Specie": specie, "Stato": stato,
                            "latitude": lat, "longitude": lon, "Foto_URL": nome_f
                        }])
                        df_aggiornato = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                        
                        st.balloons()
                        st.toast("✅ Salvato!") 
                    except Exception as e:
                        st.error(f"Errore: {e}")
                else:
                    st.warning("⚠️ Manca specie o foto!")
else:
    st.info("Attivare il GPS per inserire nuovi alberi.")

# --- CORPO CENTRALE: FILTRI E MAPPA ---
if not df_raw.empty:
    ricerca = st.text_input("", placeholder="🔍 Cerca specie o stato...", label_visibility="collapsed").strip().lower()
    
    if ricerca:
        df_visualizza = df_raw[df_raw['Specie'].str.lower().str.contains(ricerca) | 
                               df_raw['Stato'].str.lower().str.contains(ricerca)]
    else:
        df_visualizza = df_raw

    tab_mappa, tab_lista = st.tabs(["📍 Mappa", "📜 Lista"])

    with tab_mappa:
        # Configurazione del fumetto (Tooltip)
        tooltip = {
            "html": "<b>Albero:</b> {Specie}<br/><b>Stato:</b> {Stato}",
            "style": {"backgroundColor": "#2e7d32", "color": "white", "fontSize": "12px"}
        }

        # Strato dei punti
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_visualizza,
            get_position='[longitude, latitude]',
            get_color='[46, 125, 50, 160]',
            get_radius=15,
            pickable=True,
        )

        # Visualizzazione Mappa Interattiva
        st.pydeck_chart(p