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
        
        with st.form("modulo_inserimento", clear_on_submit=True):
            specie = st.text_input("Specie:", placeholder="Es: Quercus robur")
            foto_file = st.camera_input("Scatta una foto")
            
            submit = st.form_submit_button("🚀 Registra e Salva Online")
            
            if submit:
                if specie and foto_file:
                    try:
                        # 1. Foto
                        nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        path_foto = os.path.join(CARTELLA_FOTO, nome_f)
                        with open(path_foto, "wb") as f:
                            f.write(foto_file.getbuffer())
                        
                        # 2. Leggiamo i dati attuali (fondamentale per non sovrascrivere)
                        df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                        
                        # 3. Creiamo la nuova riga
                        nuova_riga = pd.DataFrame([{
                            "Specie": specie, 
                            "latitude": lat, 
                            "longitude": lon, 
                            "Foto_URL": nome_f
                        }])
                        
                        # 4. Uniamo i dati: i vecchi + il nuovo
                        df_aggiornato = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                        
                        # 5. Salviamo tutto il blocco aggiornato
                        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                        
                        st.balloons()
                        st.success(f"Salvato con successo!")
                    except Exception as e:
                        st.error(f"Errore durante il salvataggio: {e}")
                else:
                    st.warning("⚠️ Scrivi il nome e scatta la foto!")
else:
    st.warning("Ricerca GPS in corso... Attiva la posizione sul telefono.")

# --- VISUALIZZAZIONE ---
st.divider()
try:
    df_visualizza = conn.read(spreadsheet=URL_FOGLIO, ttl=0).dropna(how='all')
    if not df_visualizza.empty:
        st.subheader("Mappa dei ritrovamenti")
        st.map(df_visualizza)
        
        st.subheader("Archivio")
        for i, row in df_visualizza.iloc[::-1].iterrows():
            with st.expander(f"🌳 {row['Specie']}"):
                path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                if os.path.exists(path_img):
                    st.image(path_img, width=250)
                st.write(f"Posizione: {row['latitude']}, {row['longitude']}")
except:
    st.info("Nessun dato ancora presente.")