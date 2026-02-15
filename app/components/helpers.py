"""Utilidades de formateo y helpers para ORVANN Retail OS. v1.6
Incluye render_table() — HTML puro para tablas (bypass Glide DataGrid canvas).
"""
import streamlit as st
import pandas as pd


def render_table(df, max_height: int = 0):
    """Renderiza un DataFrame como tabla HTML pura con estilos ORVANN.

    Esto reemplaza st.dataframe() porque Glide DataGrid dibuja texto en
    canvas y el tema no lo afecta en producción (Railway).
    st.table() no soporta scroll ni height, así que usamos HTML directo.

    Args:
        df: pandas DataFrame (ya formateado para mostrar).
        max_height: si > 0, limita la altura del contenedor con scroll.
    """
    if df is None or df.empty:
        st.info("Sin datos")
        return

    # Generar HTML de la tabla
    height_css = f"max-height: {max_height}px; overflow-y: auto;" if max_height > 0 else ""
    html = f'<div class="orvann-table-wrap" style="{height_css}">'
    html += '<table class="orvann-table">'

    # Headers
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead>'

    # Body
    html += '<tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for val in row:
            cell_val = '' if pd.isna(val) else str(val)
            html += f'<td>{cell_val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'

    st.markdown(html, unsafe_allow_html=True)


def fmt_cop(valor):
    """Formatea un número como pesos colombianos: $1.234.567"""
    if valor is None:
        return "$0"
    if valor < 0:
        return f"-${abs(valor):,.0f}".replace(",", ".")
    return f"${valor:,.0f}".replace(",", ".")


def fmt_pct(valor):
    """Formatea un porcentaje: 50.7%"""
    if valor is None:
        return "0%"
    return f"{valor:.1f}%"


def color_stock(stock, minimo=3):
    """Retorna emoji/indicador según nivel de stock."""
    if stock <= 0:
        return "🔴"
    elif stock <= minimo:
        return "🟡"
    return "🟢"


def color_pe(progreso_pct):
    """Color para barra de punto de equilibrio."""
    if progreso_pct >= 100:
        return "green"
    elif progreso_pct >= 50:
        return "orange"
    return "red"


CATEGORIAS_GASTO = [
    'Arriendo',
    'Servicios (Agua, Luz, Gas)',
    'Internet',
    'Nómina/Vendedor',
    'Publicidad/Marketing',
    'Empaque (Bolsas, Etiquetas)',
    'Aseo/Mantenimiento',
    'Transporte',
    'Ilustraciones/Diseño',
    'Dotación local',
    'Mercancía',
    'Imprevistos',
    'Comisiones datáfono',
    'Contador',
    'Otro',
]

METODOS_PAGO = ['Efectivo', 'Transferencia', 'Datáfono', 'Crédito']
VENDEDORES = ['JP', 'KATHE', 'ANDRES']
