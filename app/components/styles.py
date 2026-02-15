"""CSS tema limpio ORVANN v1.3 — fondo blanco, estilo Apple, mobile-first."""

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

    /* ── Inputs & Selects ─────────────────── */
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
    .stTextInput input,
    .stNumberInput input {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
    }
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stDateInput label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    /* ── Buttons ──────────────────────────── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button:not([kind]) {
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind]):hover {
        background-color: var(--accent-light) !important;
        color: white !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-hover) !important;
    }

    /* ── Tables / Dataframes ──────────────── */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stDataFrame thead th {
        background-color: var(--bg-secondary) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
    }
    .stDataFrame tbody td {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-light) !important;
    }
    .stDataFrame tbody tr:hover td {
        background-color: var(--bg-secondary) !important;
    }

    /* ── Tabs ─────────────────────────────── */
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
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* ── Alerts ───────────────────────────── */
    .stAlert {
        border-radius: 10px !important;
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

    /* ── Charts ───────────────────────────── */
    .stPlotlyChart, .stAltairChart, .stBarChart {
        background-color: var(--bg-card) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        box-shadow: var(--shadow-sm) !important;
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
            font-size: 0.8rem !important;
        }
    }

    /* ── Hide Streamlit extras ────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] {
        background-color: var(--bg-card) !important;
        border-bottom: 1px solid var(--border) !important;
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

    /* ── Nav buttons ─────────────────────── */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        font-size: 0.85rem !important;
    }

    /* ── Success/error toasts ────────────── */
    .stSuccess {
        background-color: #F0FFF4 !important;
        border: 1px solid var(--success) !important;
        border-radius: 10px !important;
    }
    .stError {
        background-color: #FFF5F5 !important;
        border: 1px solid var(--danger) !important;
        border-radius: 10px !important;
    }
    .stWarning {
        background-color: #FFFBF0 !important;
        border: 1px solid var(--warning) !important;
        border-radius: 10px !important;
    }
    .stInfo {
        background-color: #F0F8FF !important;
        border: 1px solid var(--info) !important;
        border-radius: 10px !important;
    }
</style>
"""


def apply_theme():
    """Aplica el tema ORVANN limpio. Llamar desde main.py."""
    import streamlit as st
    st.markdown(ORVANN_CSS, unsafe_allow_html=True)
