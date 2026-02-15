"""Vista POS — Registrar ventas. Mobile-first. v1.2"""
import streamlit as st
import pandas as pd
from datetime import date, datetime

from app.models import (
    registrar_venta, anular_venta, get_ventas_dia, get_productos,
    registrar_gasto, get_estado_caja, abrir_caja, cerrar_caja,
)
from app.components.helpers import fmt_cop, METODOS_PAGO, VENDEDORES, CATEGORIAS_GASTO


def render():
    hoy = date.today()

    # ── Resumen del día (ARRIBA de todo) ──
    data = get_ventas_dia()
    caja = get_estado_caja()

    st.markdown(f"## 🛒 Vender — {hoy.strftime('%d %b %Y')}")

    # Métricas rápidas del día
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ventas hoy", fmt_cop(data['total']))
    with col2:
        st.metric("Unidades", data['unidades'])
    with col3:
        st.metric("Efectivo", fmt_cop(caja['ventas_efectivo']))
    with col4:
        st.metric("En caja", fmt_cop(caja['efectivo_esperado']))

    # Totales por método (si hay ventas)
    if data['totales_metodo']:
        met_cols = st.columns(len(data['totales_metodo']))
        for i, (met, total) in enumerate(data['totales_metodo'].items()):
            with met_cols[i]:
                st.caption(f"{met}: {fmt_cop(total)}")

    # ── Caja del día ──
    if not caja['caja_abierta']:
        with st.expander("💰 Abrir Caja", expanded=True):
            with st.form("form_abrir_caja"):
                efectivo_ini = st.number_input("Efectivo inicial en caja", min_value=0, value=0, step=10000)
                if st.form_submit_button("Abrir Caja", use_container_width=True):
                    abrir_caja(efectivo_inicio=efectivo_ini)
                    st.success(f"Caja abierta con {fmt_cop(efectivo_ini)}")
                    st.rerun()

    st.markdown("---")

    # ── Formulario de venta ──
    productos = get_productos()
    opciones = []
    productos_dict = {}
    for p in productos:
        label = f"{p['sku']} | {p['nombre']} | {fmt_cop(p['precio_venta'])} | Stock: {p['stock']}"
        opciones.append(label)
        productos_dict[label] = p

    with st.form("form_venta", clear_on_submit=True):
        seleccion = st.selectbox(
            "Buscar producto",
            options=opciones,
            index=None,
            placeholder="Escribe SKU o nombre...",
        )

        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        with col2:
            precio_default = 0
            if seleccion and seleccion in productos_dict:
                precio_default = int(productos_dict[seleccion]['precio_venta'])
            precio = st.number_input("Precio unitario", min_value=0, value=precio_default, step=1000)

        col3, col4 = st.columns(2)
        with col3:
            metodo = st.selectbox("Método de pago", METODOS_PAGO)
        with col4:
            vendedor = st.selectbox("Vendedor", VENDEDORES)

        # Opciones adicionales en expander
        with st.expander("Opciones adicionales"):
            cliente = st.text_input("Cliente (obligatorio si es crédito)")
            descuento = st.number_input("Descuento %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
            notas = st.text_input("Notas (opcional)")

        submitted = st.form_submit_button("Registrar Venta", use_container_width=True)

    # ── Procesar venta ──
    if submitted:
        # Obtener cliente/descuento/notas (pueden no existir si expander no abierto)
        _cliente = cliente if 'cliente' in dir() else ''
        _descuento = descuento if 'descuento' in dir() else 0
        _notas = notas if 'notas' in dir() else ''

        if not seleccion:
            st.error("Selecciona un producto")
        else:
            prod = productos_dict[seleccion]
            if prod['stock'] <= 0:
                st.error(f"Sin stock para {prod['nombre']}")
            elif prod['stock'] < cantidad:
                st.error(f"Stock insuficiente: {prod['stock']} disponibles")
            elif metodo == 'Crédito' and not cliente.strip():
                st.error("Venta a crédito requiere nombre de cliente")
            else:
                try:
                    venta_id = registrar_venta(
                        sku=prod['sku'],
                        cantidad=cantidad,
                        precio=precio,
                        metodo_pago=metodo,
                        cliente=cliente.strip() or None,
                        vendedor=vendedor,
                        descuento=descuento,
                        notas=notas.strip() or None,
                    )
                    total = precio * cantidad * (1 - descuento / 100)
                    st.success(
                        f"Venta #{venta_id} — {prod['nombre']} x{cantidad} — "
                        f"{fmt_cop(total)} ({metodo})"
                    )
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # ── Ventas del día (tabla) ──
    st.markdown("---")
    st.markdown("### Ventas de hoy")

    if data['ventas']:
        df = pd.DataFrame(data['ventas'])
        cols_show = ['id', 'hora', 'producto_nombre', 'cantidad', 'total', 'metodo_pago', 'vendedor']
        cols_exist = [c for c in cols_show if c in df.columns]
        display = df[cols_exist].copy()
        display['total'] = display['total'].apply(lambda x: fmt_cop(x))
        st.dataframe(
            display.rename(columns={
                'id': 'ID', 'hora': 'Hora', 'producto_nombre': 'Producto',
                'cantidad': 'Cant.', 'total': 'Total',
                'metodo_pago': 'Método', 'vendedor': 'Vendedor',
            }),
            use_container_width=True, hide_index=True,
        )

        # ── Anular venta ──
        with st.expander("Anular venta"):
            ultima = data['ventas'][0]
            st.warning(
                f"**Última:** #{ultima['id']} — {ultima.get('producto_nombre', ultima['sku'])} "
                f"x{ultima['cantidad']} — {fmt_cop(ultima['total'])} ({ultima['metodo_pago']})"
            )
            anular_id = st.number_input("ID de venta a anular", min_value=1, value=int(ultima['id']), step=1)
            if st.button("Anular venta", key="btn_anular"):
                try:
                    anulada = anular_venta(anular_id)
                    st.success(f"Venta #{anular_id} anulada. Stock devuelto: {anulada['sku']} +{anulada['cantidad']}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.info("No hay ventas registradas hoy")

    # ── Gasto rápido ──
    st.markdown("---")
    with st.expander("💸 Registrar gasto rápido"):
        with st.form("form_gasto_rapido", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                cat_gasto = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gasto_rapido_cat")
            with col_g2:
                monto_gasto = st.number_input("Monto", min_value=0, value=0, step=1000, key="gasto_rapido_monto")

            col_g3, col_g4 = st.columns(2)
            with col_g3:
                pagador = st.selectbox("Pagado por", VENDEDORES, key="gasto_rapido_pagador")
            with col_g4:
                metodo_gasto = st.selectbox("Método", ['Efectivo', 'Transferencia', 'Datáfono'], key="gasto_rapido_metodo")

            desc_gasto = st.text_input("Descripción", key="gasto_rapido_desc")
            submit_gasto = st.form_submit_button("Registrar gasto", use_container_width=True)

        if submit_gasto and monto_gasto > 0 and desc_gasto:
            registrar_gasto(
                fecha=date.today().isoformat(),
                categoria=cat_gasto,
                monto=monto_gasto,
                descripcion=desc_gasto,
                pagado_por=pagador,
                metodo_pago=metodo_gasto,
            )
            st.success(f"Gasto registrado: {fmt_cop(monto_gasto)} — {desc_gasto} ({pagador})")
            st.rerun()

    # ── Cerrar caja ──
    if caja['caja_abierta'] and not caja['cerrada']:
        st.markdown("---")
        with st.expander("🔒 Cerrar Caja"):
            st.markdown(f"**Efectivo esperado:** {fmt_cop(caja['efectivo_esperado'])}")
            st.markdown(f"Ventas efectivo: {fmt_cop(caja['ventas_efectivo'])} | Gastos efectivo: {fmt_cop(caja['gastos_efectivo'])}")
            with st.form("form_cerrar_caja"):
                efectivo_real = st.number_input("Efectivo real en caja", min_value=0, value=0, step=1000)
                notas_caja = st.text_input("Notas de cierre")
                if st.form_submit_button("Cerrar Caja", use_container_width=True):
                    result = cerrar_caja(hoy.isoformat(), efectivo_real, notas_caja.strip() or None)
                    dif = result['diferencia']
                    if abs(dif) < 1:
                        st.success("Caja cuadrada")
                    elif dif > 0:
                        st.warning(f"Sobrante: {fmt_cop(dif)}")
                    else:
                        st.error(f"Faltante: {fmt_cop(abs(dif))}")
                    st.rerun()
    elif caja['cerrada']:
        st.markdown("---")
        st.success(f"Caja cerrada — Efectivo real: {fmt_cop(caja['efectivo_cierre_real'] or 0)}")
