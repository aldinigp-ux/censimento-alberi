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
        st.success(f"📍 GPS Pronto: {lat:.4f}, {lon:.4f}")
        
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
                    # Legge i dati esistenti e pulisce le righe vuote
                    df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                    
                    # Crea la nuova riga
                    nuova_riga = pd.DataFrame([{
                        "Specie": specie, 
                        "latitude": lat, 
                        "longitude": lon, 
                        "Foto_URL": st.session_state['last_foto']
                    }])
                    
                    # Unisce i dati (appende in coda)
                    df_finale = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                    
                    # Aggiorna il foglio Google
                    conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
                    
                    st.balloons()
                    st.success(f"Salvato: {specie}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")
            else:
                st.warning("⚠️ Inserisci il nome e scatta una foto prima di salvare!")
else:
    st.warning("Ricerca GPS in corso... Assicurati di aver dato i permessi di posizione al browser.")

# --- VISUALIZZAZIONE DATI (HOME) ---
st.divider()
try:
    df = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
    if not df.empty:
        col_map, col_list = st.columns([0.6, 0.4])
        
        with col_map:
            st.subheader("Mappa dei ritrovamenti")
            st.map(df)
        
        with col_list:
            st.subheader("Ultimi inserimenti")
            for i, row in df.iloc[::-1].iterrows(): # Mostra i più recenti in alto
                with st.expander(f"🌳 {row['Specie']}"):
                    path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                    if os.path.exists(path_img):
                        st.image(path_img, width=200)
                    st.write(f"📍 Lat: {row['latitude']} | Lon: {row['longitude']}")
except Exception as e:
    st.info("Nessun dato trovato o errore di caricamento. Inizia a mappare!")