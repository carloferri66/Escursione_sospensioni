import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- CONFIGURAZIONE ---
URL_LETTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTFgpcODvT-wUcvQX4zVWe_8GtDbpPL8DL3wbc-KPObAJZmgdc5vwpNT694VZGi4LY8iIhJD4YIqWWd/pub?output=csv"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzBUn67Nv4-GVNmmsEsrVjdQINKSM0be2Ae2pY3jleXu79IE4krgDgSlwj1X4cWUMIq7w/exec"
LOGO_URL = "https://raw.githubusercontent.com/tuo-username/tuo-repo/main/logo.png" # O il link diretto all'immagine

st.set_page_config(page_title="MTB Setup Pro", layout="centered", page_icon="🚵‍♂️")

# --- LOGO E TITOLO ---
col1, col2 = st.columns([1, 4])
with col1:
    # Mostra il logo ridotto
    st.image("https://i.postimg.cc/85M6Xm90/logo-ebike.png", width=80) 
with col2:
    st.title("Registro Sospensioni Pro")

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
            st.cache_data.clear()
        else: st.error("❌ Errore scrittura")
    except Exception as e: st.error(f"Errore: {e}")

# --- SEZIONE 2: FILTRO E CARICAMENTO ---
@st.cache_data(ttl=60)
def carica_dati(url):
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    if 'Delta' in df.columns:
        df['Delta'] = df['Delta'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['Delta'] = pd.to_numeric(df['Delta'], errors='coerce')
    return df

try:
    df_originale = carica_dati(f"{URL_LETTURA}&nocache={pd.Timestamp.now().timestamp()}")
    
    # Filtro
    opzioni_percorso = ["Tutti"] + list(df_originale['Tipo percorso'].unique())
    scelta_percorso = st.selectbox("Analizza storico per tipo percorso:", opzioni_percorso)
    df_filtrato = df_originale if scelta_percorso == "Tutti" else df_originale[df_originale['Tipo percorso'] == scelta_percorso]

    # Punto 3: KPI a colori
    if not df_filtrato.empty:
        ultimo_delta = df_filtrato['Delta'].iloc[-1]
        if abs(ultimo_delta) <= 0.03: label, colore = "PERFETTO 🎯", "normal"
        elif abs(ultimo_delta) <= 0.06: label, colore = "ACCETTABILE ⚠️", "off"
        else: label, colore = "SBILANCIATO 🚨", "inverse"
        st.metric(label=label, value=f"{ultimo_delta:.3f}", delta=scelta_percorso, delta_color=colore)

    # Tabella
    st.dataframe(df_filtrato.iloc[::-1], use_container_width=True, height=250)

    # --- GRAFICO AVANZATO A COLORI ---
    st.write("### Analisi Grafica Delta")
    if 'Delta' in df_filtrato.columns and 'Data' in df_filtrato.columns:
        # Creazione grafico con Altair per colori condizionali
        chart = alt.Chart(df_filtrato).mark_bar().encode(
            x='Data:T',
            y='Delta:Q',
            color=alt.condition(
                alt.datum.Delta > 0.05, alt.value('#ff4b4b'),  # Rosso se troppo ANT
                alt.condition(
                    alt.datum.Delta < -0.05, alt.value('#31333f'), # Grigio scuro se troppo POST
                    alt.value('#29b09d') # Verde se OK
                )
            ),
            tooltip=['Data', 'Delta', 'Tipo percorso']
        ).properties(height=300)
        
        # Linea dello zero
        zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='white').encode(y='y')
        
        st.altair_chart(chart + zero_line, use_container_width=True)
        st.caption("🟢 Verde = Bilanciato | 🔴 Rosso = Anteriore rigido | ⚫ Grigio = Posteriore rigido")

except Exception as e:
    st.info(f"In attesa di dati... {e}")
