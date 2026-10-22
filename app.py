"""Punto de entrada de la aplicación Streamlit."""

import streamlit as st

from simulador.interfaz import mostrar_aplicacion


st.set_page_config(
    page_title="Simulador de Entrevistas Técnicas",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded",
)

mostrar_aplicacion()
