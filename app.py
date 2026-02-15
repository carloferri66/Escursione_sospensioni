import streamlit as st
import pandas as pd
import os

# Configurazione grafica per mobile
st.set_page_config(page_title="Suspension Tuner", layout="centered")

# Costanti basate sui tuoi riferimenti
MAX_ANT = 100
MAX_POST = 40
FILE_DATI = "Escursione sospensioni NEW.xlsx"

# Inizializzazione del database (se non esiste, lo crea)
if not os.path.exists(FILE_DATI):
    df_vuoto = pd.DataFrame(columns=['Tipo percorso', 'Escursione Ant', '%', 'Escursione Post', '% ', 'Delta', 'Bilanciato', 'PSI - A', 'PSI - P'])
    df_vuoto.to_csv(FILE_DATI, index=False)

def salva_dati(tipo, ant, post, psi_a, psi_p):
    df = pd.read_csv(FILE_DATI)
    
    # Calcoli automatici
    perc_ant = round((ant / MAX_ANT) * 100, 2)
    perc_post = round((post / MAX_POST) * 100, 2)
    delta = round(perc_ant - perc_post, 3)
    
    # Logica di bilanciamento (tolleranza 0.05)
    if abs(delta) <= 0.05:
        bilancio = "OK"
    elif delta > 0:
        bilancio = "ANT"
    else:
        bilancio = "POST"
        
    nuova_riga = {
        'Tipo percorso': tipo, 'Escursione Ant': ant, '%': perc_ant,
        'Escursione Post': post, '% ': perc_post, 'Delta': delta,
        'Bilanciato': bilancio, 'PSI - A': psi_a, 'PSI - P': psi_p
    }
    
    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
    df.to_csv(FILE_DATI, index=False)
    return bilancio

# --- INTERFACCIA UTENTE ---
st.title("🚵‍♂️ Setup Sospensioni")
st.write("Registra i dati della tua uscita:")

with st.container():
    tipo = st.selectbox("Percorso", ["Gara", "Gara fango", "Pietraia", "Sterrato", "Sterrato Soft", "Asfalto"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Anteriore")
        ant = st.number_input("Escursione (mm)", 0, 100, 80)
        psi_a = st.number_input("Pressione (PSI)", 0, 150, 100, key="psi_a")
        
    with col2:
        st.subheader("Posteriore")
        post = st.number_input("Escursione (mm) ", 0, 40, 25)
        psi_p = st.number_input("Pressione (PSI) ", 0, 300, 190, key="psi_p")

    if st.button("SALVA REGISTRAZIONE", use_container_width=True):
        risultato = salva_dati(tipo, ant, post, psi_a, psi_p)
        st.success(f"Dati salvati! Setup: **{risultato}**")

st.divider()
st.subheader("Storico Ultime Uscite")
df_visualizza = pd.read_csv(FILE_DATI)

st.dataframe(df_visualizza.tail(10), use_container_width=True)

