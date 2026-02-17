import streamlit as st
import pandas as pd

st.title("Test di Connessione Rapida 🚵‍♂️")

# INCOLLA QUI IL LINK CHE HAI COPIATO DOPO AVER PUBBLICATO SUL WEB
URL_PUBBLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQWs2Kdjudkb5H16vvEFDuZ7BA4Nmh7oowDZy29W1JFfExJM5BhZwHDQsjoKU82mQ/pub?output=csv"

try:
    # Proviamo a leggere direttamente il CSV dal link pubblico
    df = pd.read_csv(URL_PUBBLICO)
    st.success("SÌ! I dati sono stati letti correttamente!")
    st.dataframe(df.head())
except Exception as e:
    st.error(f"Ancora errore: {e}")
    st.info("Se vedi ancora 404, il link che hai incollato non è corretto o il file non è pubblicato.")

