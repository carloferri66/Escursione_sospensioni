import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Suspension Cloud Log", layout="centered")

st.title("🚵‍♂️ Registro Sospensioni Cloud")

# 1. Creiamo la connessione con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Leggiamo i dati (questa funzione legge sempre l'ultima versione online)
try:
    df = conn.read()
except Exception as e:
    st.error("Errore di connessione al foglio Google. Controlla i Secrets!")
    st.stop()

# 3. Interfaccia di inserimento
with st.sidebar:
    st.header("Nuova Uscita")
    tipo = st.selectbox("Percorso", ["Gara", "Gara fango", "Pietraia", "Sterrato", "Asfalto", "Sterrato Soft"])
    ant = st.number_input("Escursione Ant (mm)", 0, 100, 80)
    psi_a = st.number_input("PSI Ant", 0, 150, 100)
    post = st.number_input("Escursione Post (mm)", 0, 40, 25)
    psi_p = st.number_input("PSI Post", 0, 300, 190)
    
    salva = st.button("SALVA PERMANENTEMENTE")

if salva:
    # Calcoli logici
    p_ant = round((ant / 100) * 100, 2)
    p_post = round((post / 40), * 100, 2)
    diff = round(p_ant - p_post, 3)
    bilancio = "OK" if abs(diff) <= 0.05 else ("ANT" if diff > 0 else "POST")
    
    # Prepariamo la nuova riga
    nuova_riga = pd.DataFrame([{
        "Tipo percorso": tipo, "Escursione Ant": ant, "%": p_ant,
        "Escursione Post": post, "% ": p_post, "Delta": diff,
        "Bilanciato": bilancio, "PSI - A": psi_a, "PSI - P": psi_p
    }])
    
    # Uniamo i vecchi dati con la nuova riga
    df_aggiornato = pd.concat([df, nuova_riga], ignore_index=True)
    
    # 4. AGGIORNAMENTO ONLINE: Questa riga salva i dati per sempre
    conn.update(worksheet="120 - 210", data=df_aggiornato)
    
    st.success(f"Dati salvati su Google Sheets! Setup: {bilancio}")
    st.balloons()

# 5. Visualizzazione (aggiornata in tempo reale)
st.subheader("Storico Registrazioni (Cloud)")
st.dataframe(df.tail(15), use_container_width=True)


