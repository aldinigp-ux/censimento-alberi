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

# Inizializziamo la memoria se non esiste
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
        st.success(f"📍 GPS Pronto")
        
        # Salviamo il nome nella memoria mentre scrivi
        specie = st.text_input("Specie:", value=st.session_state['specie_salvata'], placeholder="Es: Quercus robur")
        st.session_state['specie_salvata'] = specie
        
        foto_file = st.camera_input("Scatta una foto")
        
        if foto_file:
            nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            path_foto = os.path.join(CARTELLA_FOTO, nome_f)
            with open(path_foto, "wb") as f:
                f.write(foto_file.getbuffer())
            st.session_state['last_foto'] = nome_f
            st.info("Foto acquisita correttamente!")

        # Ora il controllo è più robusto
        if st.button("🚀 Registra e Salva Online"):
            nome_da_salvare = st.session_state['specie_salvata']
            foto_da_salvare = st.session_state['last_foto']
            
            if nome_da_salvare and foto_da_salvare:
                try:
                    # Leggiamo e puliamo
                    df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                    
                    nuova_riga = pd.DataFrame([{
                        "Specie": nome_da_salvare, 
                        "latitude": lat, 
                        "longitude": lon, 
                        "Foto_URL": foto_da_salvare
                    }])
                    
                    df_finale = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                    conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
                    
                    # Puliamo la memoria dopo il successo
                    st.session_state['last_foto'] = None
                    st.session_state['specie_salvata'] = ""
                    
                    st.balloons()
                    st.success(f"Salvato con successo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore tecnico: {e}")
            else:
                st.warning("⚠️ Assicurati di aver scritto il nome E scattato la foto!")
else:
    st.warning("Ricerca GPS in corso...")

# --- VISUALIZZAZIONE DATI ---
st.divider()
try:
    df = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
    if not df.empty:
        st.subheader("Mappa dei ritrovamenti")
        st.map(df)
        
        st.subheader("Archivio Storico")
        # Invertiamo l'ordine per vedere gli ultimi inseriti in alto
        for i, row in df.iloc[::-1].iterrows():
            with st.expander(f"🌳 {row['Specie']}"):
                path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                if os.path.exists(path_img):
                    st.image(path_img, width=300)
                st.write(f"Data: {row['Foto_URL'].split('_')[1] if '_' in row['Foto_URL'] else ''}")
                st.write(f"Posizione: {row['latitude']}, {row['longitude']}")
except:
    st.info("Inizia a mappare i tuoi alberi!")