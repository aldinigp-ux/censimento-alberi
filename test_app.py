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

# Memoria di sessione
if 'last_foto' not in st.session_state:
    st.session_state['last_foto'] = None
if 'specie_salvata' not in st.session_state:
    st.session_state['specie_salvata'] = ""

loc = get_geolocation()

# --- SIDEBAR PER INSERIMENTO ---
if loc is not None and 'coords' in loc:
    with st.sidebar:
        st.header("Nuova Rilevazione")
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success("📍 GPS Pronto")
        
        specie = st.text_input("Specie:", value=st.session_state['specie_salvata'], placeholder="Es: Quercus robur")
        st.session_state['specie_salvata'] = specie
        
        foto_file = st.camera_input("Scatta una foto")
        
        if foto_file:
            nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            path_foto = os.path.join(CARTELLA_FOTO, nome_f)
            with open(path_foto, "wb") as f:
                f.write(foto_file.getbuffer())
            st.session_state['last_foto'] = nome_f

        if st.button("🚀 Registra e Salva Online"):
            if st.session_state['specie_salvata'] and st.session_state['last_foto']:
                try:
                    # --- LA SOLUZIONE DEFINITIVA ---
                    # Invece di update(), usiamo la connessione diretta per fare un append
                    nuovi_dati = [
                        st.session_state['specie_salvata'], 
                        lat, 
                        lon, 
                        st.session_state['last_foto']
                    ]
                    
                    # Accediamo al foglio tramite il client interno (metodo infallibile)
                    client = conn._instance
                    sheet = client.open_by_url(URL_FOGLIO).sheet1
                    
                    # Questo comando aggiunge SEMPRE una riga in fondo
                    sheet.append_row(nuovi_dati)
                    
                    # Pulizia memoria
                    st.session_state['last_foto'] = None
                    st.session_state['specie_salvata'] = ""
                    
                    st.balloons()
                    st.success("Salvato correttamente in coda!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
            else:
                st.warning("⚠️ Manca il nome o la foto!")
else:
    st.warning("Ricerca GPS in corso...")

# --- VISUALIZZAZIONE DATI ---
st.divider()
try:
    # Leggiamo i dati per la mappa e la lista
    df = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
    if not df.empty:
        st.subheader("Mappa dei ritrovamenti")
        st.map(df)
        
        st.subheader("Archivio")
        for i, row in df.iloc[::-1].iterrows():
            with st.expander(f"🌳 {row['Specie']}"):
                path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                if os.path.exists(path_img):
                    st.image(path_img, width=250)
                st.write(f"Posizione: {row['latitude']}, {row['longitude']}")
except:
    st.info("Inizia a mappare!")