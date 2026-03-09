import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Erbario Digitale", page_icon="🌳", layout="wide")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1NP6G6MGH2NTXlEJ8MsR0f5RsLW_oxYZRCpBj6NsUG6w/edit"

CARTELLA_FOTO = "foto_alberi"
if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)
st.title("🌳 Registro Alberi di Al-din")

loc = get_geolocation()

# --- SIDEBAR PER INSERIMENTO ---
if loc is not None and 'coords' in loc:
    with st.sidebar:
        st.header("Nuova Rilevazione")
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success(f"📍 GPS Pronto")
        
        # USIAMO UN FORM: Questo "blocca" i dati finché non premi il tasto
        with st.form("modulo_inserimento", clear_on_submit=True):
            specie = st.text_input("Specie:", placeholder="Es: Quercus robur")
            foto_file = st.camera_input("Scatta una foto")
            
            submit = st.form_submit_button("🚀 Registra e Salva Online")
            
            if submit:
                if specie and foto_file:
                    try:
                        # 1. Salvataggio locale della foto
                        nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        path_foto = os.path.join(CARTELLA_FOTO, nome_f)
                        with open(path_foto, "wb") as f:
                            f.write(foto_file.getbuffer())
                        
                        # 2. Preparazione dati per Google
                        nuovi_dati = [specie, lat, lon, nome_f]
                        
                        # 3. Invio diretto (APPEND)
                        client = conn._instance
                        sheet = client.open_by_url(URL_FOGLIO).sheet1
                        sheet.append_row(nuovi_dati)
                        
                        st.balloons()
                        st.success(f"Salvato con successo: {specie}")
                        # Non serve rerun qui, il form si pulisce da solo
                    except Exception as e:
                        st.error(f"Errore tecnico: {e}")
                else:
                    st.error("⚠️ Errore: Devi scrivere il nome E scattare la foto!")
else:
    st.warning("Ricerca GPS in corso... Assicurati di aver dato i permessi di posizione.")

# --- VISUALIZZAZIONE DATI (HOME) ---
st.divider()
try:
    # Leggiamo i dati per la mappa e la lista (senza cache per vedere subito l'aggiornamento)
    df = conn.read(spreadsheet=URL_FOGLIO, ttl=0).dropna(how='all')
    if not df.empty:
        col_mappa, col_lista = st.columns([0.6, 0.4])
        
        with col_mappa:
            st.subheader("Mappa")
            st.map(df)
            
        with col_lista:
            st.subheader("Archivio")
            for i, row in df.iloc[::-1].iterrows():
                with st.expander(f"🌳 {row['Specie']}"):
                    path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                    if os.path.exists(path_img):
                        st.image(path_img, width=200)
                    st.write(f"Posizione: {row['latitude']}, {row['longitude']}")
except:
    st.info("Inizia a mappare i tuoi alberi!")