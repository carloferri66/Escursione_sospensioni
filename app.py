import streamlit as st
import pandas as pd
import requests

# --- CONFIGURAZIONE (INCOLLA I TUOI LINK QUI SOTTO) ---
# Il link che finisce con ...output=csv
URL_LETTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTFgpcODvT-wUcvQX4zVWe_8GtDbpPL8DL3wbc-KPObAJZmgdc5vwpNT694VZGi4LY8iIhJD4YIqWWd/pub?output=csv"

# Il link che finisce con .../exec
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzBUn67Nv4-GVNmmsEsrVjdQINKSM0be2Ae2pY3jleXu79IE4krgDgSlwj1X4cWUMIq7w/exec"


st.set_page_config(page_title="MTB Setup Pro", layout="centered", page_icon="🚵‍♂️")

st.title("🚵‍♂️ Registro Sospensioni Pro")

# --- SEZIONE 1: INSERIMENTO DATI (Sidebar) ---
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
            st.success(f"✅ Salvato! Setup: {bilancio}")
            st.balloons()
            st.cache_data.clear()
        else:
            st.error("❌ Errore di scrittura.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- SEZIONE 2: FILTRO E VISUALIZZAZIONE ---
@st.cache_data(ttl=60)
def carica_dati(url):
    df = pd.read_csv(url)
    # Pulizia nomi colonne
    df.columns = [c.strip() for c in df.columns]
    # Pulizia Delta (gestione virgole e simboli)
    if 'Delta' in df.columns:
        df['Delta'] = df['Delta'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['Delta'] = pd.to_numeric(df['Delta'], errors='coerce')
    return df

try:
    df_originale = carica_dati(f"{URL_LETTURA}&nocache={pd.Timestamp.now().timestamp()}")
    
    # --- PUNTO 2: FILTRO PERCORSO ---
    st.subheader("Filtra per Terreno")
    opzioni_percorso = ["Tutti"] + list(df_originale['Tipo percorso'].unique())
    scelta_percorso = st.selectbox("Seleziona tipo di percorso per analizzare lo storico:", opzioni_percorso)
    
    if scelta_percorso == "Tutti":
        df_filtrato = df_originale
    else:
        df_filtrato = df_originale[df_originale['Tipo percorso'] == scelta_percorso]

    # --- PUNTO 3: COLORI BILANCIAMENTO (KPI) ---
    if not df_filtrato.empty:
        ultimo_delta = df_filtrato['Delta'].iloc[-1]
        
        # Logica Colori
        if abs(ultimo_delta) <= 0.03:
            colore = "normal"
            label = "PERFETTO 🎯"
        elif abs(ultimo_delta) <= 0.06:
            colore = "off"
            label = "ACCETTABILE ⚠️"
        else:
            colore = "inverse"
            label = "SBILANCIATO 🚨"

        st.metric(label="Stato Ultimo Bilanciamento", value=ultimo_delta, delta=f"{scelta_percorso}", delta_color=colore)

    # Tabella Storico (Invertita per vedere i recenti in alto)
    st.write("### Storico Dati")
    st.dataframe(df_filtrato.iloc[::-1], use_container_width=True, height=300)

    # --- GRAFICO ANALISI ---
    st.write("### Grafico Evoluzione Delta")
    if 'Delta' in df_filtrato.columns and 'Data' in df_filtrato.columns:
        chart_data = df_filtrato[['Data', 'Delta']].dropna()
        st.line_chart(chart_data.set_index('Data'))

except Exception as e:
    st.info(f"In attesa di dati... ({e})")
