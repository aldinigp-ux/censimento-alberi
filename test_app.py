import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Erbario Digitale", page_icon="🌳", layout="wide")

st.title("🌳 Registro Fotografico Alberi")

# Configurazione cartelle e file
FILE_DATI = "Posizioni_Alberi.csv"
CARTELLA_FOTO = "foto_alberi"

if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

# 1. RILEVAMENTO POSIZIONE E FOTO (Sidebar)
loc = get_geolocation()

with st.sidebar:
    st.header("Nuova Rilevazione")
    if loc is not None and 'coords' in loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success("📍 GPS Pronto")
        
        nome_scientifico = st.text_input("Nome Scientifico:", placeholder="Es: Quercus robur")
        
        # AGGIUNTA FOTO: attiva la fotocamera dello smartphone
        foto_file = st.camera_input("Scatta una foto all'albero")
        
        if st.button("Registra Albero e Salva Foto"):
            if nome_scientifico and foto_file:
                # Creiamo un nome unico per la foto usando data e ora
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_foto = f"{nome_scientifico.replace(' ', '_')}_{timestamp}.jpg"
                path_foto = os.path.join(CARTELLA_FOTO, nome_foto)
                
                # Salviamo la foto fisicamente sul tuo PC
                with open(path_foto, "wb") as f:
                    f.write(foto_file.getbuffer())
                
                # Salviamo i dati nel CSV aggiungendo il nome della foto
                nuova_riga = pd.DataFrame([[nome_scientifico, lat, lon, nome_foto]], 
                                         columns=['Specie', 'latitude', 'longitude', 'Foto'])
                nuova_riga.to_csv(FILE_DATI, mode='a', index=False, header=not os.path.exists(FILE_DATI))
                
                st.balloons()
                st.rerun()
            else:
                st.error("Inserisci il nome e scatta una foto!")
    else:
        st.warning("Ricerca segnale GPS...")

# 2. VISUALIZZAZIONE, MAPPA E GALLERIA
if os.path.exists(FILE_DATI):
    df = pd.read_csv(FILE_DATI)
    
    st.subheader("Mappa degli Esemplari")
    st.map(df)
    
    st.divider()
    
    st.subheader("Galleria dell'Erbario")
    for i, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
            
            # Mostra la foto salvata
            path_foto_visualizza = os.path.join(CARTELLA_FOTO, row['Foto'])
            if os.path.exists(path_foto_visualizza):
                col1.image(path_foto_visualizza, width=200)
            
            # Dati dell'albero
            col2.write(f"### {row['Specie']}")
            col2.write(f"📍 {row['latitude']:.5f}, {row['longitude']:.5f}")
            
            # Link a Google Maps
            g_maps_url = f"https://www.google.com/maps?q={row['latitude']},{row['longitude']}"
            col3.markdown(f"<br><br>[📍 Naviga verso l'albero]({g_maps_url})", unsafe_allow_html=True)
            st.divider()
else:
    st.info("Nessun albero nel database. Inizia a mappare!")