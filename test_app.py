import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Erbario Digitale Haldin", page_icon="🌳", layout="wide")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1NP6G6MGH2NTXlEJ8MsR0f5RsLW_oxYZRCpBj6NsUG6w/edit"
CARTELLA_FOTO = "foto_alberi"

if not os.path.exists(CARTELLA_FOTO):
    os.makedirs(CARTELLA_FOTO)

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)
st.markdown("### 🌳 Registro Alberi di Haldin")

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
            
            # Nuova funzione: Stato dell'albero
            stato = st.selectbox("Stato dell'albero:", 
                                ["🟢 Ottimo", "🟡 Da monitorare", "🔴 Malato/Danneggiato", "⚪ Solo tronco"])
            
            foto_file = st.camera_input("Scatta una foto")
            
            submit = st.form_submit_button("🚀 Registra e Salva Online")
            
            if submit:
                if specie and foto_file:
                    try:
                        nome_f = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        path_foto = os.path.join(CARTELLA_FOTO, nome_f)
                        with open(path_foto, "wb") as f:
                            f.write(foto_file.getbuffer())
                        
                        df_esistente = conn.read(spreadsheet=URL_FOGLIO).dropna(how='all')
                        
                        nuova_riga = pd.DataFrame([{
                            "Specie": specie, 
                            "Stato": stato,
                            "latitude": lat, 
                            "longitude": lon, 
                            "Foto_URL": nome_f
                        }])
                        
                        df_aggiornato = pd.concat([df_esistente, nuova_riga], ignore_index=True)
                        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                        
                        st.balloons()
                        st.toast("✅ Posizione salvata correttamente!") # Messaggio temporaneo che scompare
                    except Exception as e:
                        st.error(f"Errore: {e}")
                else:
                    st.warning("⚠️ Compila tutti i campi!")
else:
    st.warning("Ricerca GPS in corso... Attiva la posizione.")

# --- CORPO CENTRALE: CONTATORE E FILTRI ---
try:
    df_raw = conn.read(spreadsheet=URL_FOGLIO, ttl=0).dropna(how='all')
    
    if not df_raw.empty:
        # 1. Contatore e Ricerca (sempre visibili)
        st.metric("Alberi nell'Erbario", len(df_raw))
        
        ricerca = st.text_input("🔍 Filtra per nome o stato:", "").strip().lower()
        
        if ricerca:
            df_visualizza = df_raw[df_raw['Specie'].str.lower().str.contains(ricerca) | 
                                   df_raw['Stato'].str.lower().str.contains(ricerca)]
        else:
            df_visualizza = df_raw

        # 2. CREAZIONE DELLE SCHEDE (TABS) per salvare spazio sul telefono
        tab_mappa, tab_lista = st.tabs(["📍 Mappa Grande", "📜 Lista Dettagliata"])

        with tab_mappa:
            # Etichetta per la mappa
            df_visualizza['Etichetta'] = df_visualizza['Specie'] + " (" + df_visualizza['Stato'] + ")"
            st.map(df_visualizza, size=20, color="#2e7d32")
            
        with tab_lista:
            for i, row in df_visualizza.iloc[::-1].iterrows():
                with st.expander(f"🌳 {row['Specie']}"):
                    path_img = os.path.join(CARTELLA_FOTO, str(row['Foto_URL']))
                    if os.path.exists(path_img):
                        st.image(path_img, use_container_width=True) # Foto larga quanto il telefono
                    st.write(f"**Stato:** {row['Stato']}")
                    st.caption(f"Coordinate: {row['latitude']}, {row['longitude']}")
    else:
        st.info("L'erbario è vuoto. Registra il tuo primo albero!")
except Exception as e:
    st.error(f"Errore visualizzazione: {e}")