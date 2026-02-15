"""Vista Dashboard — Métricas y punto de equilibrio."""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    get_ventas_dia, get_ventas_mes, calcular_punto_equilibrio,
    get_resumen_inventario, get_total_deuda_proveedores,
    get_creditos_pendientes, get_alertas_stock, get_estado_caja,
)
from app.components.helpers import fmt_cop, fmt_pct, color_pe


def render():
    st.markdown("## Dashboard ORVANN")

    hoy = date.today()

    # ── Métricas del día ──
    st.markdown("### Hoy")
    ventas_hoy = get_ventas_dia()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ventas hoy", fmt_cop(ventas_hoy['total']))
    with col2:
        st.metric("Unidades", ventas_hoy['unidades'])
    with col3:
        caja = get_estado_caja()
        st.metric("Efectivo en caja", fmt_cop(caja['efectivo_esperado']))

    # ── Punto de Equilibrio ──
    st.markdown("---")
    st.markdown("### Punto de Equilibrio — Mes actual")

    pe = calcular_punto_equilibrio()
    progreso = min(pe['progreso_pct'], 100)
    color = color_pe(pe['progreso_pct'])

    # Barra de progreso
    st.progress(progreso / 100)

    if pe['progreso_pct'] >= 100:
        st.success(f"**META ALCANZADA** — Ventas: {fmt_cop(pe['ventas_acumuladas'])} de {fmt_cop(pe['pe_pesos'])}")
    elif pe['progreso_pct'] >= 50:
        st.warning(
            f"Llevas {fmt_cop(pe['ventas_acumuladas'])} de {fmt_cop(pe['pe_pesos'])} — "
            f"Te faltan ~{pe['unidades_faltantes']:.0f} prendas en {pe['dias_restantes']} días"
        )
    else:
        st.error(
            f"Llevas {fmt_cop(pe['ventas_acumuladas'])} de {fmt_cop(pe['pe_pesos'])} — "
            f"Te faltan ~{pe['unidades_faltantes']:.0f} prendas en {pe['dias_restantes']} días"
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Costos fijos", fmt_cop(pe['cf']))
    with col2:
        st.metric("Margen promedio", fmt_pct(pe['margen_prom'] * 100))
    with col3:
        st.metric("PE mensual", fmt_cop(pe['pe_pesos']))
    with col4:
        st.metric("PE diario", f"{pe['pe_diario']:.1f} uds/día")

    # ── Salud Financiera ──
    st.markdown("---")
    st.markdown("### Salud Financiera")

    inventario = get_resumen_inventario()
    deuda = get_total_deuda_proveedores()
    creditos = get_creditos_pendientes()
    total_creditos = sum(c['monto'] for c in creditos)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_info = inventario.get('total', {})
        st.metric("Inventario (costo)", fmt_cop(total_info.get('valor_costo', 0)))
    with col2:
        st.metric("Inventario (venta)", fmt_cop(total_info.get('valor_venta', 0)))
    with col3:
        st.metric("Deuda proveedores", fmt_cop(deuda))
    with col4:
        st.metric("Créditos por cobrar", fmt_cop(total_creditos))

    # ── Top productos del mes ──
    st.markdown("---")
    st.markdown("### Top Productos del Mes")

    ventas_mes = get_ventas_mes(hoy.year, hoy.month)
    if ventas_mes['top_productos']:
        df_top = pd.DataFrame(ventas_mes['top_productos'], columns=['Producto', 'Unidades'])
        st.dataframe(df_top, use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas este mes")

    # ── Alertas ──
    st.markdown("---")
    st.markdown("### Alertas")

    alertas = get_alertas_stock()
    stock_bajo = [a for a in alertas if a['stock'] > 0]
    agotados = [a for a in alertas if a['stock'] <= 0]

    if agotados:
        st.error(f"**{len(agotados)} productos agotados**")
    if stock_bajo:
        st.warning(f"**{len(stock_bajo)} productos con stock bajo**")
    if creditos:
        st.warning(f"**{len(creditos)} créditos pendientes** — {fmt_cop(total_creditos)}")

    caja = get_estado_caja()
    if not caja['cerrada']:
        st.info("Caja de hoy sin cerrar")

    if not agotados and not stock_bajo and not creditos:
        st.success("Todo en orden")
