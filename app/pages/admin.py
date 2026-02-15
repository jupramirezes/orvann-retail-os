"""Vista Admin — Gastos (parejo/personalizado/solo), liquidación, caja, créditos, pedidos. v1.1"""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    registrar_gasto, registrar_gasto_parejo, registrar_gasto_personalizado,
    get_gastos_mes,
    calcular_liquidacion_socios,
    get_estado_caja, cerrar_caja,
    get_creditos_pendientes, registrar_pago_credito,
    get_pedidos_pendientes, get_total_deuda_proveedores,
)
from app.database import query
from app.components.helpers import (
    fmt_cop, CATEGORIAS_GASTO, METODOS_PAGO, VENDEDORES,
)

SOCIOS = ['JP', 'KATHE', 'ANDRES']


def render():
    st.markdown("## ⚙️ Administración")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💸 Gastos", "🤝 Liquidación Socios", "💰 Cierre de Caja", "📋 Créditos", "📦 Pedidos"
    ])

    with tab1:
        render_gastos()
    with tab2:
        render_liquidacion()
    with tab3:
        render_caja()
    with tab4:
        render_creditos()
    with tab5:
        render_pedidos()


def render_gastos():
    st.markdown("### Registrar Gasto")

    modo = st.radio(
        "Modo de registro",
        ["Parejo (dividir entre 3)", "Personalizado (montos diferentes)", "Solo uno (un socio)"],
        horizontal=True,
        key="modo_gasto",
    )

    if "Parejo" in modo:
        _form_gasto_parejo()
    elif "Personalizado" in modo:
        _form_gasto_personalizado()
    else:
        _form_gasto_individual()

    # Gastos del mes
    st.markdown("---")
    st.markdown("### Gastos del Mes")
    hoy = date.today()
    data = get_gastos_mes(hoy.year, hoy.month)

    if data['gastos']:
        df = pd.DataFrame(data['gastos'])
        cols = ['fecha', 'categoria', 'monto', 'descripcion', 'pagado_por', 'metodo_pago']
        cols_exist = [c for c in cols if c in df.columns]
        display = df[cols_exist].copy()
        display['monto'] = display['monto'].apply(fmt_cop)
        st.dataframe(
            display.rename(columns={
                'fecha': 'Fecha', 'categoria': 'Categoría', 'monto': 'Monto',
                'descripcion': 'Descripción', 'pagado_por': 'Pagado por', 'metodo_pago': 'Método',
            }),
            use_container_width=True, hide_index=True,
        )

        st.markdown("**Totales por categoría:**")
        for cat, total in sorted(data['por_categoria'].items(), key=lambda x: -x[1]):
            st.text(f"  {cat}: {fmt_cop(total)}")
        st.markdown(f"**Total: {fmt_cop(data['total'])}**")
    else:
        st.info("No hay gastos este mes")


def _form_gasto_parejo():
    """Gasto dividido parejo entre los 3 socios."""
    with st.form("form_gasto_parejo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gp_fecha")
        with col2:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gp_cat")

        col3, col4 = st.columns(2)
        with col3:
            monto_total = st.number_input("Monto total", min_value=0, value=0, step=1000, key="gp_monto")
        with col4:
            metodo_pago = st.selectbox("Método de pago", ['Efectivo', 'Transferencia', 'Datáfono'], key="gp_metodo")

        descripcion = st.text_input("Descripción", key="gp_desc")
        notas = st.text_input("Notas (opcional)", key="gp_notas")
        es_inversion = st.checkbox("Es inversión inicial", key="gp_inv")

        submit = st.form_submit_button("Registrar gasto parejo", use_container_width=True)

    if submit and monto_total > 0 and descripcion:
        parte = round(monto_total / 3)
        st.info(f"Cada socio: {fmt_cop(parte)} (total: {fmt_cop(monto_total)})")
        registrar_gasto_parejo(
            fecha=fecha.isoformat(),
            categoria=categoria,
            monto_total=monto_total,
            descripcion=descripcion,
            metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
            notas=notas.strip() or None,
        )
        st.success(f"Gasto parejo registrado: {fmt_cop(monto_total)} dividido entre JP, KATHE, ANDRES")
        st.rerun()


def _form_gasto_personalizado():
    """Gasto con montos diferentes por socio."""
    with st.form("form_gasto_personalizado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gc_fecha")
        with col2:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gc_cat")

        st.markdown("**Montos por socio:**")
        col_jp, col_ka, col_an = st.columns(3)
        with col_jp:
            monto_jp = st.number_input("JP", min_value=0, value=0, step=1000, key="gc_jp")
        with col_ka:
            monto_kathe = st.number_input("KATHE", min_value=0, value=0, step=1000, key="gc_kathe")
        with col_an:
            monto_andres = st.number_input("ANDRES", min_value=0, value=0, step=1000, key="gc_andres")

        metodo_pago = st.selectbox("Método de pago", ['Efectivo', 'Transferencia', 'Datáfono'], key="gc_metodo")
        descripcion = st.text_input("Descripción", key="gc_desc")
        notas = st.text_input("Notas (opcional)", key="gc_notas")
        es_inversion = st.checkbox("Es inversión inicial", key="gc_inv")

        submit = st.form_submit_button("Registrar gasto personalizado", use_container_width=True)

    if submit and descripcion and (monto_jp + monto_kathe + monto_andres) > 0:
        montos = {'JP': monto_jp, 'KATHE': monto_kathe, 'ANDRES': monto_andres}
        total = sum(montos.values())
        registrar_gasto_personalizado(
            fecha=fecha.isoformat(),
            categoria=categoria,
            montos_por_socio=montos,
            descripcion=descripcion,
            metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
            notas=notas.strip() or None,
        )
        detalle = ", ".join(f"{s}: {fmt_cop(m)}" for s, m in montos.items() if m > 0)
        st.success(f"Gasto personalizado: {fmt_cop(total)} — {detalle}")
        st.rerun()


def _form_gasto_individual():
    """Gasto pagado por un solo socio."""
    with st.form("form_gasto_individual", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gi_fecha")
        with col2:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gi_cat")

        col3, col4 = st.columns(2)
        with col3:
            monto = st.number_input("Monto", min_value=0, value=0, step=1000, key="gi_monto")
        with col4:
            pagado_por = st.selectbox("Pagado por", VENDEDORES, key="gi_pagador")

        descripcion = st.text_input("Descripción", key="gi_desc")
        metodo_pago = st.selectbox("Método de pago", ['Efectivo', 'Transferencia', 'Datáfono'], key="gi_metodo")
        notas = st.text_input("Notas (opcional)", key="gi_notas")
        es_inversion = st.checkbox("Es inversión inicial", key="gi_inv")

        submit = st.form_submit_button("Registrar gasto", use_container_width=True)

    if submit and monto > 0 and descripcion:
        registrar_gasto(
            fecha=fecha.isoformat(),
            categoria=categoria,
            monto=monto,
            descripcion=descripcion,
            pagado_por=pagado_por,
            metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
            notas=notas.strip() or None,
        )
        st.success(f"Gasto registrado: {fmt_cop(monto)} — {descripcion} ({pagado_por})")
        st.rerun()


def render_liquidacion():
    st.markdown("### Liquidación de Socios")
    liq = calcular_liquidacion_socios()

    st.markdown(f"**Total gastos reales:** {fmt_cop(liq['total_real'])}")
    st.markdown(f"**Parte por socio (33.3%):** {fmt_cop(liq['parte_cada_uno'])}")

    # Tabla de saldos
    rows = []
    for socio in SOCIOS:
        s = liq['saldos'][socio]
        saldo_val = s['saldo']
        if saldo_val > 0:
            estado = f"Le deben {fmt_cop(saldo_val)}"
        elif saldo_val < 0:
            estado = f"Debe {fmt_cop(abs(saldo_val))}"
        else:
            estado = "A paz y salvo"
        rows.append({
            'Socio': socio,
            'Aportado': fmt_cop(s['aportado']),
            'Le corresponde': fmt_cop(s['le_corresponde']),
            'Saldo': estado,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Detalle por socio por categoría
    with st.expander("Detalle por socio y categoría"):
        for socio in SOCIOS:
            st.markdown(f"**{socio}** — Total: {fmt_cop(liq['aportes'][socio])}")
            cats = liq['por_socio_categoria'].get(socio, {})
            if cats:
                for cat, total in sorted(cats.items(), key=lambda x: -x[1]):
                    st.text(f"  {cat}: {fmt_cop(total)}")
            else:
                st.text("  (sin gastos)")
            st.markdown("")

    # Detalle cronológico
    with st.expander("Detalle cronológico de gastos"):
        gastos = liq.get('gastos', [])
        if gastos:
            df_gastos = pd.DataFrame(gastos)
            cols = ['fecha', 'categoria', 'monto', 'descripcion', 'pagado_por']
            cols_exist = [c for c in cols if c in df_gastos.columns]
            display = df_gastos[cols_exist].copy()
            display['monto'] = display['monto'].apply(fmt_cop)
            st.dataframe(
                display.rename(columns={
                    'fecha': 'Fecha', 'categoria': 'Categoría', 'monto': 'Monto',
                    'descripcion': 'Descripción', 'pagado_por': 'Pagado por',
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No hay gastos registrados")


def render_caja():
    st.markdown("### Cierre de Caja")

    fecha_caja = st.date_input("Fecha", value=date.today(), key="fecha_caja")
    estado = get_estado_caja(fecha_caja.isoformat())

    # Ventas del día
    st.markdown("**Ventas del día por método:**")
    if estado['totales_ventas']:
        for metodo, total in estado['totales_ventas'].items():
            st.text(f"  {metodo}: {fmt_cop(total)}")
    else:
        st.text("  Sin ventas")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Efectivo inicio", fmt_cop(estado['efectivo_inicio']))
    with col2:
        st.metric("Ventas efectivo", fmt_cop(estado['ventas_efectivo']))
    with col3:
        st.metric("Gastos efectivo", fmt_cop(estado['gastos_efectivo']))

    st.metric("Efectivo esperado", fmt_cop(estado['efectivo_esperado']))

    if estado['cerrada']:
        st.success("Caja cerrada")
        st.metric("Efectivo real", fmt_cop(estado['efectivo_cierre_real'] or 0))
    else:
        with st.form("form_cierre_caja"):
            efectivo_real = st.number_input("Efectivo real en caja", min_value=0, value=0, step=1000)
            notas_caja = st.text_input("Notas")
            submit_caja = st.form_submit_button("Cerrar Caja", use_container_width=True)

        if submit_caja:
            result = cerrar_caja(fecha_caja.isoformat(), efectivo_real, notas_caja.strip() or None)
            dif = result['diferencia']
            if abs(dif) < 1:
                st.success("Caja cuadrada")
            elif dif > 0:
                st.warning(f"Sobrante: {fmt_cop(dif)}")
            else:
                st.error(f"Faltante: {fmt_cop(abs(dif))}")
            st.rerun()


def render_creditos():
    st.markdown("### Créditos Pendientes")

    creditos = get_creditos_pendientes()
    if not creditos:
        st.success("No hay créditos pendientes")
        return

    total = sum(c['monto'] for c in creditos)
    st.metric("Total por cobrar", fmt_cop(total))

    for c in creditos:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            nombre_prod = c.get('producto_nombre') or c.get('sku', '')
            st.markdown(f"**{c['cliente']}** — {fmt_cop(c['monto'])} — {nombre_prod}")
            st.caption(f"Fecha: {c['fecha_credito']}")
        with col2:
            st.text(fmt_cop(c['monto']))
        with col3:
            if st.button("Pagado", key=f"pagar_{c['id']}"):
                registrar_pago_credito(c['id'])
                st.success(f"Crédito de {c['cliente']} marcado como pagado")
                st.rerun()


def render_pedidos():
    st.markdown("### Pedidos a Proveedores")

    pedidos = query("SELECT * FROM pedidos_proveedores ORDER BY fecha_pedido DESC")
    if not pedidos:
        st.info("No hay pedidos registrados")
        return

    total_pendiente = get_total_deuda_proveedores()
    st.metric("Total pendiente de pago", fmt_cop(total_pendiente))

    df = pd.DataFrame(pedidos)
    cols = ['fecha_pedido', 'proveedor', 'descripcion', 'unidades', 'costo_unitario', 'total', 'estado', 'notas']
    cols_exist = [c for c in cols if c in df.columns]
    display = df[cols_exist].copy()
    if 'total' in display.columns:
        display['total'] = display['total'].apply(lambda x: fmt_cop(x or 0))
    if 'costo_unitario' in display.columns:
        display['costo_unitario'] = display['costo_unitario'].apply(lambda x: fmt_cop(x or 0))

    st.dataframe(
        display.rename(columns={
            'fecha_pedido': 'Fecha', 'proveedor': 'Proveedor', 'descripcion': 'Descripción',
            'unidades': 'Uds.', 'costo_unitario': 'Costo Unit.', 'total': 'Total',
            'estado': 'Estado', 'notas': 'Notas',
        }),
        use_container_width=True, hide_index=True,
    )
