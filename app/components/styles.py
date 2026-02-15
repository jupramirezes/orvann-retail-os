"""CSS tema limpio ORVANN v1.6 — fondo blanco, estilo Apple, mobile-first.
Fix: inputs legibles, botón dorado, alertas visibles, charts blancos.
Fix v1.6: tablas 100% HTML puro (bypass Glide DataGrid canvas), sidebar fix.
"""

ORVANN_CSS = """
<style>
    /* ── Variables globales ────────────────── */
    :root {
        --bg-primary: #FFFFFF;
        --bg-secondary: #F5F5F7;
        --bg-card: #FFFFFF;
        --bg-input: #F5F5F7;
        --bg-hover: #E8E8ED;
        --text-primary: #1D1D1F;
        --text-secondary: #86868B;
        --text-muted: #AEAEB2;
        --accent: #B8860B;
        --accent-light: #DAA520;
        --accent-hover: #966F09;
        --accent-bg: #FFF8E7;
        --success: #34C759;
        --danger: #FF3B30;
        --warning: #FF9500;
        --info: #007AFF;
        --border: #E5E5EA;
        --border-light: #F2F2F7;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.08);

    }

    /* ── Base ──────────────────────────────── */
    .stApp {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, 'SF Pro Display', system-ui, sans-serif !important;
        font-size: 16px !important;
    }

    /* ── Texto base más legible ────────────── */
    .stMarkdown p, .stMarkdown li {
        font-size: 1rem !important;
        line-height: 1.5 !important;
        color: var(--text-primary) !important;
    }
    .stCaption, small {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
    }
    /* st.text() — FIX v1.5: era invisible (heredaba blanco) */
    .stText, [data-testid="stText"],
    .stMarkdown, .element-container {
        color: var(--text-primary) !important;
    }
    pre {
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }

    /* ── Sidebar ──────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-card) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--text-primary) !important;
    }

    /* ── Headers ──────────────────────────── */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
    }
    h2 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
    }
    h3, h4 {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
    }

    /* ── Metric cards ─────────────────────── */
    div[data-testid="stMetric"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: var(--shadow-sm) !important;
    }
    div[data-testid="stMetric"] label,
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* ── 1.1 INPUTS: FONDO CLARO, TEXTO NEGRO — FIX CRITICO ── */
    /* Contenedores de inputs */
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stDateInput > div > div {
        background-color: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    /* Inputs directos — el fix real para fondo negro */
    input,
    textarea,
    .stTextInput input,
    .stNumberInput input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-baseweb="input"] input {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }

    /* Selectbox y dropdown */
    [data-baseweb="select"] > div,
    .stSelectbox > div > div > div {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
    }
    [data-baseweb="select"] [data-baseweb="popover"],
    [role="listbox"],
    [role="option"] {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }
    [role="option"]:hover {
        background-color: var(--bg-hover) !important;
    }

    /* Number input buttons (+/-) */
    .stNumberInput button,
    [data-testid="stNumberInput"] button {
        background-color: var(--bg-hover) !important;
        color: var(--text-primary) !important;
        border: none !important;
    }

    /* Labels de form más visibles */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stDateInput label,
    .stMultiSelect label {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--text-primary) !important;
    }

    /* ── 1.2 BOTON PRIMARIO: DORADO ORVANN — FIX CRITICO ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.15s ease !important;
    }
    /* Primario y form submit — DORADO */
    .stButton > button[kind="primary"],
    .stButton > button:not([kind]),
    button[data-testid="stFormSubmitButton"],
    .stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind]):hover,
    .stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: var(--accent-hover) !important;
        color: white !important;
    }
    /* Secundario */
    .stButton > button[kind="secondary"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-hover) !important;
    }

    /* ── 1.3 ALERTAS: TEXTO OSCURO SIEMPRE — FIX CRITICO ── */
    .stAlert,
    [data-testid="stAlert"] {
        border-radius: 10px !important;
    }
    .stAlert p, .stAlert span, .stAlert div, .stAlert strong,
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span,
    [data-testid="stAlert"] div,
    [data-testid="stAlert"] strong,
    [data-testid="stAlert"] a {
        color: var(--text-primary) !important;
    }
    /* Fondos pastel claros */
    .stSuccess, div[data-testid="stAlert"].stSuccess {
        background-color: #F0FFF4 !important;
        border: 1px solid var(--success) !important;
        border-radius: 10px !important;
    }
    .stError, div[data-testid="stAlert"].stError {
        background-color: #FFF5F5 !important;
        border: 1px solid var(--danger) !important;
        border-radius: 10px !important;
    }
    .stWarning, div[data-testid="stAlert"].stWarning {
        background-color: #FFFBF0 !important;
        border: 1px solid var(--warning) !important;
        border-radius: 10px !important;
    }
    .stInfo, div[data-testid="stAlert"].stInfo {
        background-color: #F0F8FF !important;
        border: 1px solid var(--info) !important;
        border-radius: 10px !important;
    }
    /* Forzar texto oscuro en todas las variantes de alerta */
    [data-baseweb*="notification"] div,
    [data-baseweb*="notification"] p,
    [data-baseweb*="notification"] span {
        color: var(--text-primary) !important;
    }

    /* ── 1.4 CHARTS: FONDO BLANCO + TEXTO OSCURO — FIX v1.5 ── */
    .stPlotlyChart,
    .stAltairChart,
    .stBarChart,
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stVegaLiteChart"] {
        background-color: var(--bg-card) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        box-shadow: var(--shadow-sm) !important;
    }
    /* canvas background solo para charts, NO para DataGrid */
    .stAltairChart canvas,
    .stBarChart canvas,
    .stPlotlyChart canvas,
    [data-testid="stArrowVegaLiteChart"] canvas,
    [data-testid="stVegaLiteChart"] canvas {
        background-color: var(--bg-card) !important;
    }
    /* FIX v1.5: Texto SVG dentro de gráficas Altair/Vega */
    .vega-embed text,
    [data-testid="stArrowVegaLiteChart"] text,
    [data-testid="stVegaLiteChart"] text,
    .stAltairChart text,
    .marks text {
        fill: var(--text-primary) !important;
    }
    .vega-embed .vega-bind label,
    .vega-embed .chart-wrapper text {
        fill: var(--text-primary) !important;
        color: var(--text-primary) !important;
    }

    /* ── 1.5 TABLAS HTML PURAS (render_table) — FIX v1.6 ── */
    .orvann-table-wrap {
        border-radius: 12px !important;
        overflow: auto !important;
        box-shadow: var(--shadow-sm) !important;
        background-color: var(--bg-card) !important;
        margin-bottom: 1rem !important;
    }
    .orvann-table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-size: 0.9rem !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }
    .orvann-table thead th {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        padding: 10px 12px !important;
        text-align: left !important;
        border-bottom: 2px solid var(--border) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 1 !important;
        white-space: nowrap !important;
    }
    .orvann-table tbody td {
        color: var(--text-primary) !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid var(--border-light) !important;
        white-space: nowrap !important;
    }
    .orvann-table tbody tr:nth-child(even) {
        background-color: #FAFAFA !important;
    }
    .orvann-table tbody tr:hover {
        background-color: var(--bg-secondary) !important;
    }
    /* Mobile: allow horizontal scroll */
    @media (max-width: 768px) {
        .orvann-table {
            font-size: 0.8rem !important;
        }
        .orvann-table thead th,
        .orvann-table tbody td {
            padding: 6px 8px !important;
        }
    }

    /* ── 1.6 TABS: MAS GRANDES EN MOBILE ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        background-color: var(--bg-card) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* ── Progress bar ─────────────────────── */
    .stProgress > div > div > div {
        background-color: var(--accent) !important;
    }
    .stProgress > div > div {
        background-color: var(--border) !important;
    }

    /* ── Expander ─────────────────────────── */
    [data-testid="stExpander"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .streamlit-expanderHeader {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* ── Forms ────────────────────────────── */
    [data-testid="stForm"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 1rem !important;
    }

    /* ── Dividers ─────────────────────────── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── Mobile adjustments ───────────────── */
    @media (max-width: 768px) {
        .stApp > header { display: none !important; }
        .block-container {
            padding: 0.75rem 0.5rem !important;
            max-width: 100% !important;
        }
        h1 { font-size: 1.3rem !important; }
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        div[data-testid="stMetric"] {
            padding: 10px !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 10px !important;
            font-size: 0.85rem !important;
        }
    }

    /* ── Hide Streamlit extras + multipage auto-nav ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] {
        background-color: var(--bg-card) !important;
        border-bottom: 1px solid var(--border) !important;
    }
    /* Ocultar nav multipage auto-detectada por Streamlit */
    [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] ul {
        display: none !important;
    }

    /* ── Stock colors ────────────────────── */
    .stock-zero { color: var(--danger) !important; font-weight: bold; }
    .stock-low { color: var(--warning) !important; font-weight: bold; }
    .stock-ok { color: var(--success) !important; }

    /* ── ORVANN Logo ─────────────────────── */
    .orvann-logo {
        font-family: -apple-system, system-ui, sans-serif !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        letter-spacing: 3px !important;
        color: var(--accent) !important;
        text-align: center !important;
        padding: 0.5rem 0 !important;
    }
    .orvann-header {
        font-family: -apple-system, system-ui, sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        letter-spacing: 6px !important;
        color: var(--text-primary) !important;
        text-align: center !important;
        padding: 8px 0 !important;
        margin-bottom: 8px !important;
    }

    /* ── Nav buttons ─────────────────────── */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        font-size: 0.85rem !important;
    }
</style>
"""


def apply_theme():
    """Aplica el tema ORVANN limpio. Llamar desde main.py."""
    import streamlit as st
    st.markdown(ORVANN_CSS, unsafe_allow_html=True)
