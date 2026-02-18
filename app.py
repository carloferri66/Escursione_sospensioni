import streamlit as st
import pandas as pd
import requests
import altair as alt
import time
import random
from io import StringIO

# --- 1. CONFIGURAZIONE ---
# Inserisci l'ID che trovi tra /d/ e /edit nell'indirizzo del tuo foglio Google
ID_FOGLIO = "14VvmeQ_U8ka6SeQdbwJ98u_Squ4ENdQngSRph6PkaVQ" 
URL_LETTURA = f"https://docs.google.com/spreadsheets/d/{ID_FOGLIO}/export?format=csv"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbwNMG9zi-evudSuDwy0qCg44pG0smv1A7eDgEXrFDA7lSTz5vyULtkCroQcKV1xschvKQ/exec"
URL_LOGO = "https://github.com/carloferri66/Escursione_sospensioni/blob/main/LOGO%20.jpg?raw=true" 

st.set_page_config(page_title="MTB Setup Pro", layout="centered", page_icon="🚵‍♂️")

# --- 2. FUNZIONE LETTURA ISTANTANEA ---
def carica_dati_istantanei(url):
    # Aggiungiamo un parametro casuale per bypassare ogni cache di rete
    response = requests.get(f"{url}&t={time.time()}")
    if response.status_code == 200:
        # Leggiamo il testo CSV direttamente dalla risposta
        df = pd.read_csv(StringIO(response.text))
        df.columns = [c.strip() for c in df.columns]
        if 'Delta' in df.columns:
            df['Delta'] = df['Delta'].astype(str).str.replace('%', '').str.replace(',', '.')
            df['Delta'] = pd.to_numeric(df['Delta'], errors='coerce')
        return df
    else:
        return pd.DataFrame()

# --- 3. LOGO E TITOLO ---
col1, col2 = st.columns([1, 3])
with col1:
    try: st.image(URL_LOGO, width=100)
    except: st.subheader("🚲 MyEbike")
with col2:
    st.title("Registro Sospensioni Pro")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Nuova Registrazione")
    with st.form("dati_sospensioni", clear_on_submit=True):
        tipo = st.selectbox("Percorso", ["Gara", "Gara fango", "Pietraia", "Sterrato", "Asfalto", "Sterrato Soft"])
        ant = st.number_input("Escursione Ant (mm)", 0, 100, 85)
        psi_a = st.number_input("PSI Ant", 0, 150, 100)
        post = st.number_input("Escursione Post (mm)", 0, 40, 28)
        psi_p = st.number_input("PSI Post", 0, 300, 190)
        submit = st.form_submit_button("SALVA SUL CLOUD")

    if submit:
        p_ant = round(ant / 100, 2)
        p_post = round(post / 40, 2)
        delta = round(p_ant - p_post, 3)
        bilancio = "OK" if abs(delta) <= 0.05 else ("ANT" if delta > 0 else "POST")
        payload = {"tipo": tipo, "ant": ant, "p_ant": p_ant, "post": post, "p_post": p_post, "delta": delta, "bilancio": bilancio, "psi_a": psi_a, "psi_p": psi_p}
        try:
            r = requests.get(URL_SCRITTURA, params=payload)
            if r.status_code == 200:
                st.success("✅ Inviato!")
                time.sleep(1.5) # Pausa per dare tempo a Google di scrivere
                st.rerun()
        except Exception as e: st.error(f"Errore: {e}")

    st.divider()
    if st.button("🗑️ CANCELLA ULTIMA RIGA"):
        try:
            r = requests.get(URL_SCRITTURA, params={"delete_last": "true"})
            if r.status_code == 200:
                st.warning("⚠️ Cancellata!")
                time.sleep(1.5)
                st.rerun()
        except Exception as e: st.error(f"Errore: {e}")

# --- 5. VISUALIZZAZIONE ---
try:
    df_originale = carica_dati_istantanei(URL_LETTURA)
    
    if not df_originale.empty:
        opzioni = ["Tutti"] + list(df_originale['Tipo percorso'].unique())
        scelta = st.selectbox("Filtra per terreno:", opzioni)
        df_filtrato = df_originale if scelta == "Tutti" else df_originale[df_originale['Tipo percorso'] == scelta]

        # KPI
        u_delta = df_filtrato['Delta'].iloc[-1]
        st.metric(label="Ultimo Delta", value=f"{u_delta:.3f}", delta=scelta)

        # Tabella
        st.write("### Storico")
        st.dataframe(df_filtrato.iloc[::-1], use_container_width=True, height=200)

        # Grafico
        if 'Delta' in df_filtrato.columns and 'Data' in df_filtrato.columns:
            base = alt.Chart(df_filtrato).encode(x='Data:T', y='Delta:Q')
            linea = base.mark_line(color="#888888")
            punti = base.mark_circle(size=100).encode(
                color=alt.condition("abs(datum.Delta) <= 0.05", alt.value("#29b09d"), alt.value("#ff4b4b")),
                tooltip=['Data', 'Delta', 'Tipo percorso']
            )
            st.altair_chart((linea + punti).properties(height=350).interactive(bind_y=False), use_container_width=True)
    else:
        st.warning("Nessun dato trovato nel foglio.")

except Exception as e:
    st.info(f"Connessione in corso... ({e})")



