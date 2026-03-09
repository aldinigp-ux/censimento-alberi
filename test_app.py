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
st.title("🌳 Registro Alberi di Haldin")

loc = get_geolocation()

# --- SIDEBAR PER INSERIMENTO ---
if loc is not None and 'coords' in loc:
    with st.sidebar:
        st.header("Nuova Rilevazione")
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success(f"📍 GPS Pronto")
        
        specie = st.text_input("Specie:", placeholder="Es: Quercus robur")
        foto_file = st.camera_input("Scatta una foto")
        
        if foto_file:
            nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            path_foto = os.path.join(CARTELLA_FOTO, nome_f)
            with open(path_foto, "wb") as f:
                f.write(foto_file.getbuffer())
            st.session_state['last_foto'] = nome_f
            st.image(foto_file, caption="Anteprima foto", width=150)

        if st.button("🚀 Registra e Salva Online"):
            if specie and 'last_foto' in st.session_state:
                try:
                    # METODO APPEND: Aggiunge in coda senza sovrascrivere
                    nuovi_dati = pd.DataFrame([{
                        "Specie": specie, 
                        "latitude": lat, 
                        "longitude": lon, 
                        "Foto_URL": st.session_state['last_foto']
                    }])
                    
                    # Leggiamo il foglio esistente
                    df_esistente = conn.read(spreadsheet=URL_FOGLIO)
                    
                    # Uniamo i dati assicurandoci di ignorare righe vuote
                    if df_esistente is not None:
                        df_esistente = df_esistente.dropna(how='all')
                        df_finale = pd.concat([df_esistente, nuovi_dati], ignore_index=True)
                    else:
                        df_finale = nuovi_dati
                    
                    # Aggiorniamo l'intero foglio con la lista completa
                    conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
                    
                    st.balloons()
                    st.success(f"Salvato: {specie}")
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
    df = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
    if not df.empty:
        st.subheader("Mappa dei ritrovamenti")
        st.map(df)
        
        st.subheader("Archivio")
        for i, row in df.iterrows():
            with st.expander(f"🌳 {row['Specie']}"):
                path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                if os.path.exists(path_img):
                    st.image(path_img, width=200)
                st.write(f"Coordinate: {row['latitude']}, {row['longitude']}")
except:
    st.info("Inizia a mappare i tuoi alberi!")