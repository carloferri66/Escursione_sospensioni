import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- CONFIGURAZIONE ---
URL_LETTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTFgpcODvT-wUcvQX4zVWe_8GtDbpPL8DL3wbc-KPObAJZmgdc5vwpNT694VZGi4LY8iIhJD4YIqWWd/pub?output=csv"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzBUn67Nv4-GVNmmsEsrVjdQINKSM0be2Ae2pY3jleXu79IE4krgDgSlwj1X4cWUMIq7w/exec"
URL_LOGO = "https://github.com/carloferri66/Escursione_sospensioni/blob/main/LOGO%20.jpg?raw=true"


st.set_page_config(page_title="MTB Setup Pro", layout="centered", page_icon="🚵‍♂️")

# --- LOGO E TITOLO ---
col1, col2 = st.columns([1, 3])
with col1:
    # Mostriamo il TUO logo caricato su GitHub
    st.image(URL_LOGO, width=120) 
with col2:
    st.title("Registro Sospensioni Pro")
    st.write("Cannondale Scalpel Hi Mod 1 di Aziz")


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
    except Exception as e: st.error(f"Errore invio: {e}")

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
    # Carichiamo i dati
    df_originale = carica_dati(f"{URL_LETTURA}&nocache={pd.Timestamp.now().timestamp()}")
    
    # Filtro percorso
    opzioni_percorso = ["Tutti"] + list(df_originale['Tipo percorso'].unique())
    scelta_percorso = st.selectbox("Analizza storico per tipo percorso:", opzioni_percorso)
    df_filtrato = df_originale if scelta_percorso == "Tutti" else df_originale[df_originale['Tipo percorso'] == scelta_percorso]

    # Visualizzazione KPI
    if not df_filtrato.empty:
        ultimo_delta = df_filtrato['Delta'].iloc[-1]
        if abs(ultimo_delta) <= 0.03: label, colore = "PERFETTO 🎯", "normal"
        elif abs(ultimo_delta) <= 0.06: label, colore = "ACCETTABILE ⚠️", "off"
        else: label, colore = "SBILANCIATO 🚨", "inverse"
        st.metric(label=label, value=f"{ultimo_delta:.3f}", delta=scelta_percorso, delta_color=colore)

    # Tabella storico
    st.write("### Storico Dati")
    st.dataframe(df_filtrato.iloc[::-1], use_container_width=True, height=250)

  # --- SEZIONE 3: GRAFICO INTERATTIVO CON SCROLL ---
    st.write("### Evoluzione Bilanciamento (Delta)")
    if 'Delta' in df_filtrato.columns and 'Data' in df_filtrato.columns:
        
        # Base del grafico
        # Usiamo :T (temporale) per permettere lo scroll fluido nel tempo
        base = alt.Chart(df_filtrato).encode(
            x=alt.X('Data:T', title='Data (Scorri per vedere tutto lo storico)'),
            y=alt.Y('Delta:Q', title='Delta (Bilanciamento)')
        )

        # 1. La linea
        linea = base.mark_line(color="#888888", strokeWidth=1.5, opacity=0.7)

        # 2. I punti colorati
        punti = base.mark_circle(size=100, opacity=1).encode(
            color=alt.condition(
                "abs(datum.Delta) <= 0.05",
                alt.value("#29b09d"), # Verde
                alt.value("#ff4b4b")  # Rosso
            ),
            tooltip=['Data', 'Delta', 'Tipo percorso', 'PSI - A', 'PSI - P']
        )

        # 3. Linea dello zero
        zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='white', strokeDash=[3,3]).encode(y='y')

        # COMBINAZIONE E INTERATTIVITÀ
        # .interactive() abilita lo scroll del mouse e il trascinamento (pan)
        grafico_interattivo = (linea + punti + zero_line).properties(
            height=350,
            width=600 # Impostiamo una larghezza base che può essere superata con lo scroll
        ).interactive(bind_y=False) # Permettiamo lo scroll solo sull'asse X (date)

        st.altair_chart(grafico_interattivo, use_container_width=True)
        st.caption("🖱️ **Mouse/Touch**: Usa la rotellina per zoomare e trascina per spostarti tra le date.")


# ---SEZIONE 4  AGGIUNTA NELLA SIDEBAR: CANCELLAZIONE ---
st.sidebar.divider()
st.sidebar.subheader("Gestione Errori")
if st.sidebar.button("🗑️ CANCELLA ULTIMA RIGA"):
    # Carichiamo i dati correnti
    try:
        # Recuperiamo il DataFrame originale (senza filtri)
        df_temp = carica_dati(URL_LETTURA)
        
        if not df_temp.empty:
            # Rimuoviamo l'ultima riga
            df_nuovo = df_temp.drop(df_temp.index[-1])
            
            # Qui abbiamo bisogno di un comando per dire a Google di cancellare.
            # Dato che usiamo Apps Script per scrivere, il modo più semplice 
            # è aggiungere un payload speciale al tuo script esistente.
            
            payload_delete = {"delete_last": "true"}
            r = requests.get(URL_SCRITTURA, params=payload_delete)
            
            if r.status_code == 200:
                st.sidebar.success("Ultima riga rimossa!")
                st.cache_data.clear() # Svuota la cache per aggiornare subito tabella e grafico
                st.rerun() # Riavvia l'app per mostrare i dati aggiornati
            else:
                st.sidebar.error("Errore durante la cancellazione.")
        else:
            st.sidebar.warning("Il foglio è già vuoto.")
    except Exception as e:
        st.sidebar.error(f"Errore: {e}")


except Exception as e:
    st.info(f"In attesa di dati... ({e})")







