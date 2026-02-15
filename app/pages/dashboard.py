"""Vista Dashboard — Metricas esenciales, PE, resultado mensual. v1.6"""
import streamlit as st
from datetime import date

from app.models import (
    get_ventas_mes, get_ventas_semana,
    calcular_punto_equilibrio,
    get_resumen_inventario, get_total_deuda_proveedores,
    get_creditos_pendientes, get_alertas_stock,
    get_gastos_mes,
)
from app.components.helpers import fmt_cop, fmt_pct


def render():
    hoy = date.today()
    st.markdown(f"**ORVANN** — {hoy.strftime('%B %Y')}")

    # ── Punto de Equilibrio ──────────────────────────────
    st.markdown("### Punto de Equilibrio")

    pe = calcular_punto_equilibrio()
    progreso = min(pe['progreso_pct'], 100)

    st.progress(progreso / 100)

    if pe['progreso_pct'] >= 100:
        st.success(f"META ALCANZADA — {fmt_cop(pe['ventas_acumuladas'])} de {fmt_cop(pe['pe_pesos'])}")
    else:
        faltante = pe['pe_pesos'] - pe['ventas_acumuladas']
        st.markdown(
            f"Llevas **{fmt_cop(pe['ventas_acumuladas'])}** de **{fmt_cop(pe['pe_pesos'])}** "
            f"— Faltan {fmt_cop(faltante)} ({pe['dias_restantes']} dias)"
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Costos fijos/mes", fmt_cop(pe['cf']))
    with c2:
        st.metric("Margen promedio", fmt_pct(pe['margen_prom'] * 100))
    with c3:
        st.metric("Meta diaria", f"{pe['pe_diario']:.1f} uds/dia")

    # ── Semana actual ────────────────────────────────────
    st.markdown("---")
    st.markdown("### Esta Semana")

    semana = get_ventas_semana()
    dias_semana = (hoy - date.fromisoformat(semana['fecha_inicio'])).days + 1
    prom_diario = semana['total'] / dias_semana if dias_semana > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Ventas", fmt_cop(semana['total']))
    with c2:
        st.metric("Unidades", semana['unidades'])
    with c3:
        st.metric("Promedio/dia", fmt_cop(prom_diario))

    # ── Resultado mensual ────────────────────────────────
    st.markdown("---")
    st.markdown("### Resultado del Mes")

    ventas_mes = get_ventas_mes(hoy.year, hoy.month)
    gastos_mes = get_gastos_mes(hoy.year, hoy.month)

    ingreso = ventas_mes['total_ventas']
    costo_merc = ventas_mes['total_costo']
    utilidad_bruta = ventas_mes['utilidad_bruta']
    gastos_op = gastos_mes['total']
    utilidad_op = utilidad_bruta - gastos_op

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Ingresos", fmt_cop(ingreso))
        st.metric("Costo mercancia", fmt_cop(costo_merc))
    with c2:
        st.metric("Gastos operativos", fmt_cop(gastos_op))
        if utilidad_op >= 0:
            st.metric("Utilidad operativa", fmt_cop(utilidad_op))
        else:
            st.metric("Perdida operativa", fmt_cop(utilidad_op))

    st.caption(f"Utilidad bruta: {fmt_cop(utilidad_bruta)} | Uds vendidas: {ventas_mes['total_unidades']}")

    # ── Inventario + Finanzas ────────────────────────────
    st.markdown("---")
    st.markdown("### Situacion Actual")

    inventario = get_resumen_inventario()
    deuda = get_total_deuda_proveedores()
    creditos = get_creditos_pendientes()
    total_creditos = sum(c['monto'] for c in creditos)
    total_info = inventario.get('total', {})

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Inventario (costo)", fmt_cop(total_info.get('valor_costo', 0)))
        st.metric("Deuda proveedores", fmt_cop(deuda))
    with c2:
        st.metric("Inventario (venta)", fmt_cop(total_info.get('valor_venta', 0)))
        st.metric("Creditos por cobrar", fmt_cop(total_creditos))

    uds_total = total_info.get('total_unidades', 0) or 0
    skus_total = total_info.get('total_skus', 0) or 0
    st.caption(f"{skus_total} SKUs | {uds_total} unidades en stock")

    # ── Alertas ──────────────────────────────────────────
    alertas = get_alertas_stock()
    agotados = [a for a in alertas if a['stock'] <= 0]
    stock_bajo = [a for a in alertas if a['stock'] > 0]

    if agotados or stock_bajo or creditos:
        st.markdown("---")
        st.markdown("### Alertas")

        if agotados:
            nombres = ", ".join(a['nombre'][:20] for a in agotados[:5])
            st.error(f"**{len(agotados)} agotados:** {nombres}")
        if stock_bajo:
            nombres = ", ".join(f"{a['nombre'][:15]}({a['stock']})" for a in stock_bajo[:5])
            st.warning(f"**{len(stock_bajo)} stock bajo:** {nombres}")
        if creditos:
            st.warning(f"**{len(creditos)} creditos pendientes** — {fmt_cop(total_creditos)}")
