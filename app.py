import streamlit as st
import pandas as pd
import requests
import altair as alt
import time

# --- CONFIGURAZIONE ---
URL_LETTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTFgpcODvT-wUcvQX4zVWe_8GtDbpPL8DL3wbc-KPObAJZmgdc5vwpNT694VZGi4LY8iIhJD4YIqWWd/pub?output=csv"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbwNMG9zi-evudSuDwy0qCg44pG0smv1A7eDgEXrFDA7lSTz5vyULtkCroQcKV1xschvKQ/exec"
URL_LOGO = "https://github.com/carloferri66/Escursione_sospensioni/blob/main/LOGO%20.jpg?raw=true"


st.set_page_config(page_title="MTB Setup Pro", layout="centered", page_icon="🚵‍♂️💨")

# --- 2. FUNZIONE CARICAMENTO DATI (Anti-Cache) ---
@st.cache_data(ttl=5)  # La cache scade ogni 5 secondi per dati sempre freschi
def carica_dati(url):
    # Aggiungiamo un parametro temporale unico per forzare Google Sheets a inviare i dati nuovi
    url_fresh = f"{url}&nocache={time.time()}"
    df = pd.read_csv(url_fresh)
    # Pulizia nomi colonne
    df.columns = [c.strip() for c in df.columns]
    # Conversione Delta (gestione virgole, percentuali e numeri)
    if 'Delta' in df.columns:
        df['Delta'] = df['Delta'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['Delta'] = pd.to_numeric(df['Delta'], errors='coerce')
    return df

# --- 3. LOGO E TITOLO ---
col1, col2 = st.columns([1, 3])
with col1:
    try:
        st.image(URL_LOGO, width=100)
    except:
        st.subheader("🚲 MyEbike")
with col2:
    st.title("Registro Sospensioni Pro")

# --- 4. SIDEBAR (Inserimento e Manutenzione) ---
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
        p_ant = round((ant / 100) * 100, 2)
        p_post = round((post / 40) * 100, 2)
        delta = round(p_ant - p_post, 3)
        bilancio = "OK" if abs(delta) <= 0.05 else ("ANT" if delta > 0 else "POST")
        
        payload = {
            "tipo": tipo, "ant": ant, "p_ant": p_ant, 
            "post": post, "p_post": p_post, "delta": delta, 
            "bilancio": bilancio, "psi_a": psi_a, "psi_p": psi_p
        }
        
        try:
            r = requests.get(URL_SCRITTURA, params=payload)
            if r.status_code == 200:
                st.success("✅ Dati inviati!")
                st.cache_data.clear() # Svuota cache locale
                time.sleep(1) # Aspetta un secondo per il refresh di Google
                st.rerun()
        except Exception as e:
            st.error(f"Errore invio: {e}")

    st.divider()
    st.subheader("Manutenzione")
    # Tasto per cancellare l'ultima riga
    if st.button("🗑️ CANCELLA ULTIMA RIGA"):
        try:
            r = requests.get(URL_SCRITTURA, params={"delete_last": "true"})
            if r.status_code == 200:
                st.warning("⚠️ Ultima riga eliminata dal foglio.")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error("Errore nella cancellazione.")
        except Exception as e:
            st.error(f"Errore connessione: {e}")

# --- 5. VISUALIZZAZIONE DATI (Tabella e Grafico) ---
try:
    # Caricamento effettivo
    df_originale = carica_dati(URL_LETTURA)
    
    # Filtro Percorso
    opzioni = ["Tutti"] + list(df_originale['Tipo percorso'].unique())
    scelta = st.selectbox("Filtra storico per terreno:", opzioni)
    
    if scelta == "Tutti":
        df_filtrato = df_originale
    else:
        df_filtrato = df_originale[df_originale['Tipo percorso'] == scelta]

    # KPI Ultimo Bilanciamento
    if not df_filtrato.empty:
        u_delta = df_filtrato['Delta'].iloc[-1]
        if abs(u_delta) <= 0.03: label, colore = "PERFETTO 🎯", "normal"
        elif abs(u_delta) <= 0.06: label, colore = "ACCETTABILE ⚠️", "off"
        else: label, colore = "SBILANCIATO 🚨", "inverse"
        
        st.metric(label=label, value=f"{u_delta:.3f}", delta=f"Terreno: {scelta}", delta_color=colore)

    # Tabella Dati
    st.write("### Storico Registrazioni")
    st.dataframe(df_filtrato.iloc[::-1], use_container_width=True, height=200)

    # Grafico Interattivo
    st.write("### Analisi Grafica Delta")
    if 'Delta' in df_filtrato.columns and 'Data' in df_filtrato.columns:
        base = alt.Chart(df_filtrato).encode(
            x=alt.X('Data:T', title='Data Uscita'),
            y=alt.Y('Delta:Q', title='Bilanciamento (Delta)')
        )
        
        linea = base.mark_line(color="#888888", strokeWidth=1.5, opacity=0.7)
        
        punti = base.mark_circle(size=100, opacity=1).encode(
            color=alt.condition(
                "abs(datum.Delta) <= 0.05",
                alt.value("#29b09d"), # Verde
                alt.value("#ff4b4b")  # Rosso
            ),
            tooltip=['Data', 'Delta', 'Tipo percorso', 'PSI - A', 'PSI - P']
        )
        
        zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='white', strokeDash=[3,3]).encode(y='y')
        
        grafico_finale = (linea + punti + zero_line).properties(height=350).interactive(bind_y=False)
        st.altair_chart(grafico_finale, use_container_width=True)
        st.caption("🖱️ Trascina per scorrere le date, usa la rotellina per zoomare.")

except Exception as e:
    st.info("In attesa di connessione ai dati... Assicurati che i link siano corretti.")
