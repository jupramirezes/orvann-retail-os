"""ORVANN Retail OS — Entry point."""
import streamlit as st
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.components.styles import apply_theme

st.set_page_config(
    page_title="ORVANN Retail OS",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

# ── Navegación ──
PAGES = {
    "Vender": "vender",
    "Dashboard": "dashboard",
    "Inventario": "inventario",
    "Admin": "admin",
}

# Sidebar
with st.sidebar:
    st.markdown('<div class="orvann-logo">ORVANN</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navegación", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.caption("ORVANN Retail OS v1.0")
    st.caption("Streetwear Premium — Medellín")

# Mobile-friendly tabs at the top
cols = st.columns(len(PAGES))
for i, (name, key) in enumerate(PAGES.items()):
    with cols[i]:
        if st.button(name, use_container_width=True, key=f"nav_{key}"):
            page = name

# Cargar la página seleccionada
if page == "Vender":
    from app.pages.vender import render
    render()
elif page == "Dashboard":
    from app.pages.dashboard import render
    render()
elif page == "Inventario":
    from app.pages.inventario import render
    render()
elif page == "Admin":
    from app.pages.admin import render
    render()
