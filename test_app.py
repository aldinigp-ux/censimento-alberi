import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Erbario Digitale", page_icon="🌳", layout="wide")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1NP6G6MGH2NTXlEJ8MsR0f5RsLW_oxYZRCpBj6NsUG6w/edit"

CARTELLA_FOTO = "foto_alberi"
if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)
st.title("🌳 Registro Alberi di Haldin")

loc = get_geolocation()

if loc is not None and 'coords' in loc:
    with st.sidebar:
        st.header("Nuova Rilevazione")
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success("📍 GPS Pronto")
        specie = st.text_input("Specie:", placeholder="Es: Quercus robur")
        foto_file = st.camera_input("Scatta una foto")
        
        if foto_file:
            nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(os.path.join(CARTELLA_FOTO, nome_f), "wb") as f:
                f.write(foto_file.getbuffer())
                st.session_state['last_foto'] = nome_f

if st.button("🚀 Registra e Salva Online"):
            if specie and 'last_foto' in st.session_state:
                try:
                    # 1. Creiamo la riga da aggiungere (una lista di valori)
                    nuovi_dati = [specie, lat, lon, st.session_state['last_foto']]
                    
                    # 2. Usiamo la funzione 'append_row' per aggiungere in coda
                    # Accediamo direttamente al client gspread sottostante
                    client = conn._instance
                    sheet = client.open_by_url(URL_FOGLIO).sheet1
                    sheet.append_row(nuovi_dati)
                    
                    st.balloons()
                    st.success(f"Salvato correttamente: {specie}")
                    st.rerun()
                except Exception as e:
                    # Se il metodo sopra fallisce, usiamo quello classico ma corretto
                    try:
                        df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                        nuova_riga = pd.DataFrame([{"Specie": specie, "latitude": lat, "longitude": lon, "Foto_URL": st.session_state['last_foto']}])
                        df_finale = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                        conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
                        st.balloons()
                        st.rerun()
                    except Exception as e2:
                        st.error(f"Errore tecnico: {e2}")
else:
    st.warning("Ricerca GPS in corso...")

try:
    df = conn.read(spreadsheet=URL_FOGLIO)
    if not df.empty:
        st.map(df)
        for i, row in df.iterrows():
            st.write(f"### {row['Specie']}")
            path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
            if os.path.exists(path_img):
                st.image(path_img, width=250)
            st.divider()
except:
    st.info("In attesa di dati...")
