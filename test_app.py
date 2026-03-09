import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE INIZIALE ---
st.set_page_config(page_title="Erbario Digitale Online", page_icon="🌳", layout="wide")

# Incolla qui il link del tuo foglio Google (deve essere condiviso come EDITOR)
URL_FOGLIO = "Ihttps://docs.google.com/spreadsheets/d/1NP6G6MGH2NTXlEJ8MsR0f5RsLW_oxYZRCpBj6NsUG6w/edit?gid=0#gid=0"

FILE_DATI = "Posizioni_Alberi.csv"
CARTELLA_FOTO = "foto_alberi"

if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

# Inizializza connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🌳 Registro Alberi con Google Sheets")

# --- 1. RILEVAMENTO POSIZIONE (Sidebar) ---
loc = get_geolocation()

with st.sidebar:
    st.header("Nuova Rilevazione")
    if loc is not None and 'coords' in loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success("📍 GPS Pronto")
        
        nome_scientifico = st.text_input("Nome Scientifico:", placeholder="Es: Quercus robur")
        foto_file = st.camera_input("Scatta una foto")
        
        if st.button("Registra e Salva Online"):
            if nome_scientifico and foto_file:
                # Gestione Foto
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_foto = f"{nome_scientifico.replace(' ', '_')}_{timestamp}.jpg"
                path_foto = os.path.join(CARTELLA_FOTO, nome_foto)
                
                with open(path_foto, "wb") as f:
                    f.write(foto_file.getbuffer())
                
                # Prepara riga per Google Sheets
                nuova_riga = pd.DataFrame([[nome_scientifico, lat, lon, nome_foto]], 
                                         columns=['Specie', 'latitude', 'longitude', 'Foto_URL'])
                
                try:
                    # Legge dati attuali, aggiunge il nuovo e aggiorna il foglio
                    df_esistente = conn.read(spreadsheet=URL_FOGLIO)
                    df_aggiornato = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                    conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                    
                    st.balloons()
                    st.success("✅ Salvato su Google Sheets!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore Google Sheets: {e}")
            else:
                st.error("Manca il nome o la foto!")
    else:
        st.warning("Ricerca segnale GPS... Assicurati di aver dato i permessi al browser.")

# --- 2. MAPPA E GALLERIA (Corpo Centrale) ---
try:
    # Leggiamo i dati direttamente dal foglio Google
    df = conn.read(spreadsheet=URL_FOGLIO)
    
    if not df.empty:
        st.subheader("Mappa degli Esemplari Registrati")
        # Mostra la mappa usando le colonne latitude e longitude
        st.map(df)
        
        st.divider()
        st.subheader("Galleria Fotografica")
        
        # Mostra i record in una griglia
        for i, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([0.4, 0.6])
                
                # Visualizzazione foto (se presente nella cartella locale/cloud)
                path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                if os.path.exists(path_img):
                    col1.image(path_img, width=250)
                else:
                    col1.info("Foto non disponibile su questo dispositivo")
                
                col2.write(f"### {row['Specie']}")
                col2.write(f"📍 Lat: {row['latitude']} | Lon: {row['longitude']}")
                
                # Link per navigare all'albero
                g_maps = f"https://www.google.com/maps?q={row['latitude']},{row['longitude']}"
                col2.markdown(f"[➡️ Apri in Google Maps]({g_maps})")
                st.divider()
    else:
        st.info("Il database è vuoto. Registra il primo albero dalla barra laterale!")
        
except Exception as e:
    st.warning("Collega il foglio Google per vedere la mappa.")