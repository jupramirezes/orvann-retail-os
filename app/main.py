"""ORVANN Retail OS — Entry point. v1.5"""
import streamlit as st
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.components.styles import apply_theme

# Logo ORVANN como page icon (favicon)
_LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'ORVANN.png')
_page_icon = _LOGO_PATH if os.path.exists(_LOGO_PATH) else "🖤"

st.set_page_config(
    page_title="ORVANN Retail OS",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

# ── Navegación con session_state (TAREA 1 — fix nav bug) ──
PAGES = {
    "vender": {"label": "🛒 Vender", "module": "app.pages.vender"},
    "dashboard": {"label": "📊 Dashboard", "module": "app.pages.dashboard"},
    "inventario": {"label": "📦 Inventario", "module": "app.pages.inventario"},
    "historial": {"label": "📜 Historial", "module": "app.pages.historial"},
    "admin": {"label": "⚙️ Admin", "module": "app.pages.admin"},
}

# Inicializar estado de navegación
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'vender'


def nav_to(page_key):
    """Callback para cambiar de página sin perder el estado."""
    st.session_state.current_page = page_key


# ── Sidebar ──
with st.sidebar:
    st.markdown('<div class="orvann-logo">ORVANN</div>', unsafe_allow_html=True)
    st.markdown("---")
    for key, info in PAGES.items():
        is_active = st.session_state.current_page == key
        btn_type = "primary" if is_active else "secondary"
        st.button(
            info['label'],
            key=f"side_{key}",
            use_container_width=True,
            type=btn_type,
            on_click=nav_to,
            args=(key,),
        )
    st.markdown("---")
    st.caption("ORVANN Retail OS v1.5")
    st.caption("Streetwear Premium — Medellín")

# ── Logo ORVANN en header ──
st.markdown('<div class="orvann-header">ORVANN</div>', unsafe_allow_html=True)

# ── Mobile-friendly nav tabs at top ──
cols = st.columns(len(PAGES))
for i, (key, info) in enumerate(PAGES.items()):
    with cols[i]:
        is_active = st.session_state.current_page == key
        btn_type = "primary" if is_active else "secondary"
        st.button(
            info['label'],
            key=f"nav_{key}",
            use_container_width=True,
            type=btn_type,
            on_click=nav_to,
            args=(key,),
        )

# ── Cargar la página seleccionada ──
page_key = st.session_state.current_page

if page_key == "vender":
    from app.pages.vender import render
    render()
elif page_key == "dashboard":
    from app.pages.dashboard import render
    render()
elif page_key == "inventario":
    from app.pages.inventario import render
    render()
elif page_key == "historial":
    from app.pages.historial import render
    render()
elif page_key == "admin":
    from app.pages.admin import render
    render()
