"""Vista Dashboard — Métricas, PE, weekly stats, charts. v1.1"""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    get_ventas_dia, get_ventas_mes, get_ventas_diarias_mes,
    get_ventas_semana, get_ventas_semana_anterior,
    calcular_punto_equilibrio,
    get_resumen_inventario, get_total_deuda_proveedores,
    get_creditos_pendientes, get_alertas_stock, get_estado_caja,
    get_gastos_mes,
)
from app.components.helpers import fmt_cop, fmt_pct, color_pe


def render():
    st.markdown("## 📊 Dashboard ORVANN")

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

    # ── Métricas semanales ──
    st.markdown("---")
    st.markdown("### Esta Semana")

    semana = get_ventas_semana()
    semana_ant = get_ventas_semana_anterior()

    # Calcular deltas
    delta_ventas = semana['total'] - semana_ant['total'] if semana_ant['total'] else None
    delta_uds = semana['unidades'] - semana_ant['unidades'] if semana_ant['unidades'] else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Ventas semana",
            fmt_cop(semana['total']),
            delta=fmt_cop(delta_ventas) if delta_ventas is not None else None,
        )
    with col2:
        st.metric(
            "Unidades semana",
            semana['unidades'],
            delta=delta_uds,
        )
    with col3:
        st.metric("Utilidad bruta semana", fmt_cop(semana['utilidad']))
    with col4:
        dias_semana = (hoy - date.fromisoformat(semana['fecha_inicio'])).days + 1
        promedio_diario = semana['total'] / dias_semana if dias_semana > 0 else 0
        st.metric("Promedio diario", fmt_cop(promedio_diario))

    # ── Punto de Equilibrio ──
    st.markdown("---")
    st.markdown("### Punto de Equilibrio — Mes actual")

    pe = calcular_punto_equilibrio()
    progreso = min(pe['progreso_pct'], 100)

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

    # ── Utilidad Operativa del Mes ──
    st.markdown("---")
    st.markdown("### Utilidad Operativa — Mes actual")

    ventas_mes_data = get_ventas_mes(hoy.year, hoy.month)
    gastos_mes_data = get_gastos_mes(hoy.year, hoy.month)

    ingreso_bruto = ventas_mes_data['total_ventas']
    costo_mercancia = ventas_mes_data['total_costo']
    utilidad_bruta = ventas_mes_data['utilidad_bruta']
    gastos_operativos = gastos_mes_data['total']
    utilidad_operativa = utilidad_bruta - gastos_operativos

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ingresos brutos", fmt_cop(ingreso_bruto))
    with col2:
        st.metric("Utilidad bruta", fmt_cop(utilidad_bruta))
    with col3:
        st.metric("Gastos operativos", fmt_cop(gastos_operativos))
    with col4:
        st.metric(
            "Utilidad operativa",
            fmt_cop(utilidad_operativa),
            delta=fmt_cop(utilidad_operativa),
        )

    # ── Gráfico de ventas diarias del mes ──
    st.markdown("---")
    st.markdown("### Ventas diarias del mes")

    ventas_diarias = get_ventas_diarias_mes(hoy.year, hoy.month)
    if ventas_diarias:
        df_chart = pd.DataFrame(ventas_diarias)
        df_chart['fecha'] = pd.to_datetime(df_chart['fecha'])
        df_chart = df_chart.set_index('fecha')
        st.bar_chart(df_chart['total_dia'], use_container_width=True)
    else:
        st.info("No hay ventas este mes para graficar")

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

    if ventas_mes_data['top_productos']:
        df_top = pd.DataFrame(ventas_mes_data['top_productos'], columns=['Producto', 'Unidades'])
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

    caja_hoy = get_estado_caja()
    if not caja_hoy['cerrada']:
        st.info("Caja de hoy sin cerrar")

    if not agotados and not stock_bajo and not creditos:
        st.success("Todo en orden")
