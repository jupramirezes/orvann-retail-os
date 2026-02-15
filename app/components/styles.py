"""CSS dark theme ORVANN v1.1 — tema cálido, aplicar desde main.py."""

ORVANN_CSS = """
<style>
    /* ── Variables globales ────────────────── */
    :root {
        --bg-primary: #161618;
        --bg-card: #1e1e22;
        --bg-input: #28282e;
        --text-primary: #e8e6e3;
        --text-secondary: #a09c97;
        --accent: #d4a843;
        --accent-dark: #a8832f;
        --accent-light: #e8c76a;
        --success: #5a9e6f;
        --danger: #c45c5c;
        --warning: #c9a84c;
        --info: #5b8fb9;
        --border: #3a3a40;
    }

    /* ── Base ──────────────────────────────── */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: system-ui, 'Inter', -apple-system, sans-serif !important;
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
    h1, h2, h3, h4 {
        color: var(--accent) !important;
        font-weight: 700 !important;
    }
    h1 { font-size: 1.8rem !important; }

    /* ── Metric cards ─────────────────────── */
    div[data-testid="stMetric"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] svg {
        display: inline !important;
    }

    /* ── Inputs & Selects ─────────────────── */
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stDateInput > div > div {
        background-color: var(--bg-input) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    .stTextInput input,
    .stNumberInput input {
        color: var(--text-primary) !important;
    }

    /* ── Buttons ──────────────────────────── */
    .stButton > button {
        background-color: var(--accent) !important;
        color: #161618 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 24px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: var(--accent-light) !important;
        color: #161618 !important;
    }
    .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* ── Secondary buttons ────────────────── */
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--accent) !important;
        color: var(--accent) !important;
    }

    /* ── Tables / Dataframes ──────────────── */
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .stDataFrame thead th {
        background-color: var(--bg-card) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
    }
    .stDataFrame tbody td {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
    }

    /* ── Tabs ─────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px !important;
        background-color: var(--bg-card) !important;
        border-radius: 8px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: #161618 !important;
    }

    /* ── Alerts ───────────────────────────── */
    .stAlert {
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"][data-baseweb] {
        background-color: var(--bg-card) !important;
    }

    /* ── Progress bar ─────────────────────── */
    .stProgress > div > div > div {
        background-color: var(--accent) !important;
    }

    /* ── Expander ─────────────────────────── */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    /* ── Dividers ─────────────────────────── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── Charts ───────────────────────────── */
    .stPlotlyChart, .stAltairChart, .stBarChart {
        background-color: var(--bg-card) !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }

    /* ── Mobile adjustments ───────────────── */
    @media (max-width: 768px) {
        .stApp > header { display: none !important; }
        .block-container {
            padding: 1rem 0.5rem !important;
            max-width: 100% !important;
        }
        h1 { font-size: 1.4rem !important; }
        div[data-testid="stMetric"] {
            padding: 10px !important;
        }
    }

    /* ── Hide Streamlit extras ────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background-color: var(--bg-primary) !important; }

    /* ── Stock colors (classes for inventory) ─ */
    .stock-zero { color: var(--danger) !important; font-weight: bold; }
    .stock-low { color: var(--warning) !important; font-weight: bold; }
    .stock-ok { color: var(--success) !important; }

    /* ── ORVANN Logo text ─────────────────── */
    .orvann-logo {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0.3em;
        color: var(--accent);
        text-align: center;
        padding: 1rem 0;
    }

    /* ── Nav buttons at top ───────────────── */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        font-size: 0.9rem !important;
    }
</style>
"""


def apply_theme():
    """Aplica el tema ORVANN. Llamar desde main.py."""
    import streamlit as st
    st.markdown(ORVANN_CSS, unsafe_allow_html=True)
