"""Vista Admin — Gastos, liquidación, caja, créditos, pedidos."""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    registrar_gasto, get_gastos_mes,
    calcular_liquidacion_socios,
    get_estado_caja, cerrar_caja,
    get_creditos_pendientes, registrar_pago_credito,
    get_pedidos_pendientes, get_total_deuda_proveedores,
)
from app.database import query
from app.components.helpers import (
    fmt_cop, CATEGORIAS_GASTO, METODOS_PAGO, VENDEDORES,
)


def render():
    st.markdown("## Administración")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Gastos", "Liquidación Socios", "Cierre de Caja", "Créditos", "Pedidos"
    ])

    # ── Tab 1: Gastos ──
    with tab1:
        render_gastos()

    # ── Tab 2: Liquidación Socios ──
    with tab2:
        render_liquidacion()

    # ── Tab 3: Cierre de Caja ──
    with tab3:
        render_caja()

    # ── Tab 4: Créditos ──
    with tab4:
        render_creditos()

    # ── Tab 5: Pedidos ──
    with tab5:
        render_pedidos()


def render_gastos():
    st.markdown("### Registrar Gasto")

    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today())
        with col2:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO)

        col3, col4 = st.columns(2)
        with col3:
            monto = st.number_input("Monto", min_value=0, value=0, step=1000)
        with col4:
            pagado_por = st.selectbox("Pagado por", ['ORVANN'] + VENDEDORES)

        descripcion = st.text_input("Descripción")
        metodo_pago = st.selectbox("Método de pago", METODOS_PAGO[:3])  # Sin crédito
        notas = st.text_input("Notas (opcional)")
        es_inversion = st.checkbox("Es inversión inicial")

        submit = st.form_submit_button("Registrar Gasto", use_container_width=True)

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
        st.success(f"Gasto registrado: {fmt_cop(monto)} — {descripcion}")
        st.rerun()

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


def render_liquidacion():
    st.markdown("### Liquidación de Socios")
    liq = calcular_liquidacion_socios()

    st.markdown(f"**Total gastos reales:** {fmt_cop(liq['total_real'])}")
    st.markdown(f"**Parte por socio (33.3%):** {fmt_cop(liq['parte_cada_uno'])}")

    # Tabla de saldos
    rows = []
    for socio in ['JP', 'KATHE', 'ANDRES']:
        s = liq['saldos'][socio]
        saldo_txt = fmt_cop(abs(s['saldo']))
        if s['saldo'] > 0:
            estado = f"Le deben {saldo_txt}"
        elif s['saldo'] < 0:
            estado = f"Debe {saldo_txt}"
        else:
            estado = "A paz y salvo"
        rows.append({
            'Socio': socio,
            'Aportado': fmt_cop(s['aportado']),
            'Le corresponde': fmt_cop(s['le_corresponde']),
            'Saldo': estado,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Detalle por categoría
    with st.expander("Detalle por categoría"):
        for cat, total in sorted(liq['por_categoria'].items(), key=lambda x: -x[1]):
            st.text(f"  {cat}: {fmt_cop(total)}")


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
