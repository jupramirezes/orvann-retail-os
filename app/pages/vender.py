"""Vista POS — Registrar ventas. Mobile-first. v1.1"""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    registrar_venta, anular_venta, get_ventas_dia, get_productos,
    registrar_gasto,
)
from app.components.helpers import fmt_cop, METODOS_PAGO, VENDEDORES, CATEGORIAS_GASTO


def render():
    st.markdown("## 🛒 Registrar Venta")

    # ── Cargar productos disponibles ──
    productos = get_productos()
    opciones = []
    productos_dict = {}
    for p in productos:
        label = f"{p['sku']} | {p['nombre']} | {fmt_cop(p['precio_venta'])} | Stock: {p['stock']}"
        opciones.append(label)
        productos_dict[label] = p

    # ── Formulario de venta ──
    with st.form("form_venta", clear_on_submit=True):
        seleccion = st.selectbox(
            "Buscar producto",
            options=opciones,
            index=None,
            placeholder="Escribe SKU o nombre del producto...",
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

        cliente = st.text_input("Cliente (obligatorio si es crédito)")
        descuento = st.number_input("Descuento %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
        notas = st.text_input("Notas (opcional)")

        submitted = st.form_submit_button("Registrar Venta", use_container_width=True)

    # ── Procesar venta directamente (sin segundo botón) ──
    if submitted:
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
                        f"Venta #{venta_id} registrada — {prod['nombre']} x{cantidad} — "
                        f"{fmt_cop(total)} ({metodo})"
                    )
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # ── Ventas del día ──
    st.markdown("---")
    st.markdown("### Ventas de hoy")

    data = get_ventas_dia()
    if data['ventas']:
        df = pd.DataFrame(data['ventas'])
        cols_show = ['id', 'hora', 'sku', 'producto_nombre', 'cantidad', 'precio_unitario', 'total', 'metodo_pago', 'vendedor', 'cliente']
        cols_exist = [c for c in cols_show if c in df.columns]
        st.dataframe(
            df[cols_exist].rename(columns={
                'id': 'ID',
                'hora': 'Hora',
                'sku': 'SKU',
                'producto_nombre': 'Producto',
                'cantidad': 'Cant.',
                'precio_unitario': 'Precio',
                'total': 'Total',
                'metodo_pago': 'Método',
                'vendedor': 'Vendedor',
                'cliente': 'Cliente',
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Totales por método
        st.markdown("#### Totales por método")
        met_cols = st.columns(len(data['totales_metodo']) + 1)
        for i, (met, total) in enumerate(data['totales_metodo'].items()):
            with met_cols[i]:
                st.metric(met, fmt_cop(total))
        with met_cols[-1]:
            st.metric("TOTAL DÍA", fmt_cop(data['total']))

        # ── Anular última venta ──
        with st.expander("Anular venta"):
            ultima = data['ventas'][0]  # La más reciente (ORDER BY hora DESC)
            st.warning(
                f"**Última venta:** #{ultima['id']} — {ultima.get('producto_nombre', ultima['sku'])} "
                f"x{ultima['cantidad']} — {fmt_cop(ultima['total'])} ({ultima['metodo_pago']})"
            )
            anular_id = st.number_input("ID de venta a anular", min_value=1, value=int(ultima['id']), step=1)
            if st.button("Anular venta", key="btn_anular"):
                try:
                    anulada = anular_venta(anular_id)
                    st.success(
                        f"Venta #{anular_id} anulada. Stock devuelto: "
                        f"{anulada['sku']} +{anulada['cantidad']}"
                    )
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.info("No hay ventas registradas hoy")

    # ── Gasto rápido (TAREA 8) ──
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
