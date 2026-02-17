import streamlit as st
import pandas as pd
import requests

# --- CONFIGURAZIONE (INCOLLA I TUOI LINK QUI SOTTO) ---
# Il link che finisce con ...output=csv
URL_LETTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTFgpcODvT-wUcvQX4zVWe_8GtDbpPL8DL3wbc-KPObAJZmgdc5vwpNT694VZGi4LY8iIhJD4YIqWWd/pub?output=csv"

# Il link che finisce con .../exec
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzBUn67Nv4-GVNmmsEsrVjdQINKSM0be2Ae2pY3jleXu79IE4krgDgSlwj1X4cWUMIq7w/exec"

st.set_page_config(page_title="MTB Setup", layout="centered", page_icon="🚵‍♂️")

st.title("🚵‍♂️ Registro Sospensioni")

# --- SEZIONE 1: INSERIMENTO DATI ---
with st.sidebar:
    st.header("Nuova Uscita")
    with st.form("dati_sospensioni", clear_on_submit=True):
        tipo = st.selectbox("Percorso", ["Gara", "Gara fango", "Pietraia", "Sterrato", "Asfalto", "Sterrato Soft"])
        ant = st.number_input("Escursione Ant (mm)", 0, 100, 85)
        psi_a = st.number_input("PSI Ant", 0, 150, 100)
        post = st.number_input("Escursione Post (mm)", 0, 40, 28)
        psi_p = st.number_input("PSI Post", 0, 300, 190)
        
        submit = st.form_submit_button("SALVA SUL CLOUD")

if submit:
    # Calcoli logici (così non devi farli tu a mano)
    p_ant = round((ant / 100) * 100, 2)
    p_post = round((post / 40) * 100, 2)
    delta = round(p_ant - p_post, 3)
    bilancio = "OK" if abs(delta) <= 0.05 else ("ANT" if delta > 0 else "POST")
    
    # Parametri da inviare al "Postino" Apps Script
    payload = {
        "tipo": tipo, "ant": ant, "p_ant": p_ant, 
        "post": post, "p_post": p_post, "delta": delta, 
        "bilancio": bilancio, "psi_a": psi_a, "psi_p": psi_p
    }
    
    # Invio effettivo
    try:
        r = requests.get(URL_SCRITTURA, params=payload)
        if r.status_code == 200:
            st.success(f"✅ Salvataggio riuscito! Setup: {bilancio}")
            st.balloons()
            # Puliamo la cache per vedere subito i nuovi dati nella tabella
            st.cache_data.clear()
        else:
            st.error("❌ Errore durante il salvataggio. Verifica l'URL di scrittura.")
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
# --- SEZIONE 2: STORICO DATI ---
st.subheader("Storico Registrazioni Completo")

@st.cache_data(ttl=60)
def carica_dati(url):
    # Leggiamo tutto il file
    return pd.read_csv(url)

try:
    # Carichiamo i dati
    df = carica_dati(f"{URL_LETTURA}&nocache={pd.Timestamp.now().timestamp()}")
    
    # 1. Ordiniamo i dati per mostrare i più recenti in alto (facoltativo ma comodo)
    # Se la colonna si chiama DATA, mettiamo l'ultima inserita per prima
    df_visualizzazione = df.iloc[::-1] 
    
    # 2. Mostriamo la tabella COMPLETA
    # Togliamo .tail(10) così carichiamo tutto. 
    # Streamlit aggiungerà automaticamente la barra di scorrimento.
    st.dataframe(df_visualizzazione, use_container_width=True, height=400)
    
   # --- SEZIONE 3: GRAFICO BILANCIAMENTO ---
    st.divider()
    st.subheader("Analisi Bilanciamento (Delta)")
    
    # Prepariamo i dati per il grafico
    # Usiamo la colonna Delta e come indice la DATA
    if 'Delta' in df.columns and 'DATA' in df.columns:
        chart_data = df[['DATA', 'Delta']].copy()
        
        # Creiamo un grafico ad area o linee
        # Streamlit permette di scorrere e zoomare con le dita/mouse
        st.area_chart(chart_data.set_index('DATA'), use_container_width=True)
        
        st.caption("💡 Se il grafico è vicino alla linea centrale (0), la bici è bilanciata. Punti in alto = Ant più rigido, Punti in basso = Post più rigido.")
    
except Exception as e:
    st.info("In attesa di dati per generare il grafico...")
