"""Vista POS — Registrar ventas. Mobile-first, mínimo clicks. v1.3"""
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
    data = get_ventas_dia()
    caja = get_estado_caja()

    # ── Header con fecha ──
    st.markdown(f"**ORVANN** — {hoy.strftime('%a %d %b %Y')}")

    # ── Métricas rápidas ──
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Ventas hoy", fmt_cop(data['total']), f"{data['unidades']} uds")
    with c2:
        st.metric("Efectivo caja", fmt_cop(caja['efectivo_esperado']))

    # ── Abrir caja (si no está abierta) ──
    if not caja['caja_abierta']:
        st.markdown("---")
        with st.form("form_abrir_caja"):
            st.markdown("#### 💰 Abrir Caja")
            efectivo_ini = st.number_input("Efectivo inicial", min_value=0, value=0, step=10000)
            if st.form_submit_button("Abrir Caja", use_container_width=True):
                abrir_caja(efectivo_inicio=efectivo_ini)
                st.rerun()

    st.markdown("---")

    # ── Formulario de venta (COMPACTO) ──
    st.markdown("### Registrar Venta")

    productos = get_productos()
    opciones = []
    productos_dict = {}
    for p in productos:
        if p['stock'] > 0:
            label = f"{p['nombre']} — {fmt_cop(p['precio_venta'])} ({p['stock']})"
            opciones.append(label)
            productos_dict[label] = p

    with st.form("form_venta", clear_on_submit=True):
        seleccion = st.selectbox(
            "Producto",
            options=opciones,
            index=None,
            placeholder="Buscar por nombre...",
        )

        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        with col2:
            precio_default = 0
            if seleccion and seleccion in productos_dict:
                precio_default = int(productos_dict[seleccion]['precio_venta'])
            precio = st.number_input("Precio", min_value=0, value=precio_default, step=1000)

        col3, col4 = st.columns(2)
        with col3:
            metodo = st.selectbox("Método", METODOS_PAGO)
        with col4:
            vendedor = st.selectbox("Vendedor", VENDEDORES)

        # Cliente solo si crédito
        cliente = ""
        if metodo == 'Crédito':
            cliente = st.text_input("Nombre del cliente")

        # Calcular total para el botón
        total_venta = precio * cantidad
        label_btn = f"REGISTRAR VENTA — {fmt_cop(total_venta)}" if total_venta > 0 else "REGISTRAR VENTA"
        submitted = st.form_submit_button(label_btn, use_container_width=True, type="primary")

    # ── Procesar venta ──
    if submitted:
        if not seleccion:
            st.error("Selecciona un producto")
        else:
            prod = productos_dict[seleccion]
            if prod['stock'] < cantidad:
                st.error(f"Stock insuficiente: {prod['stock']} disponibles")
            elif metodo == 'Crédito' and not cliente.strip():
                st.error("Crédito requiere nombre de cliente")
            else:
                try:
                    venta_id = registrar_venta(
                        sku=prod['sku'],
                        cantidad=cantidad,
                        precio=precio,
                        metodo_pago=metodo,
                        cliente=cliente.strip() or None,
                        vendedor=vendedor,
                    )
                    st.success(f"✅ #{venta_id} — {prod['nombre']} x{cantidad} — {fmt_cop(total_venta)} ({metodo})")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # ── Ventas del día ──
    st.markdown("---")
    st.markdown("### Ventas de hoy")

    if data['ventas']:
        # Tabla compacta: hora | producto | total | método (1 letra) | vendedor
        rows = []
        for v in data['ventas']:
            met_letra = v['metodo_pago'][0] if v['metodo_pago'] else '?'  # E, T, D, C
            nombre_corto = (v.get('producto_nombre') or v['sku'])[:25]
            rows.append({
                'Hora': v['hora'][:5] if v.get('hora') else '',
                'Producto': nombre_corto,
                'Total': fmt_cop(v['total']),
                'M': met_letra,
                'Quien': v.get('vendedor', ''),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Resumen por método
        met_parts = []
        for met, total in data['totales_metodo'].items():
            met_parts.append(f"{met[0]}: {fmt_cop(total)}")
        st.caption(" | ".join(met_parts) + f" | **TOTAL: {fmt_cop(data['total'])}**")

        # ── Anular venta ──
        with st.expander("Anular venta"):
            ultima = data['ventas'][0]
            st.warning(
                f"**Última:** #{ultima['id']} — {(ultima.get('producto_nombre') or ultima['sku'])[:30]} "
                f"x{ultima['cantidad']} — {fmt_cop(ultima['total'])}"
            )
            anular_id = st.number_input("ID de venta a anular", min_value=1, value=int(ultima['id']), step=1)
            if st.button("Anular venta", key="btn_anular"):
                try:
                    anulada = anular_venta(anular_id)
                    st.success(f"Anulada #{anular_id}. Stock devuelto: +{anulada['cantidad']}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.info("No hay ventas hoy")

    # ── Gasto rápido ──
    st.markdown("---")
    with st.expander("💸 Gasto rápido"):
        with st.form("form_gasto_rapido", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                cat_gasto = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gr_cat")
            with col_g2:
                monto_gasto = st.number_input("Monto", min_value=0, value=0, step=1000, key="gr_monto")

            col_g3, col_g4 = st.columns(2)
            with col_g3:
                pagador = st.selectbox("Pagó", VENDEDORES, key="gr_pagador")
            with col_g4:
                metodo_gasto = st.selectbox("Método", ['Efectivo', 'Transferencia', 'Datáfono'], key="gr_metodo")

            desc_gasto = st.text_input("Descripción", key="gr_desc")
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
            st.success(f"Gasto: {fmt_cop(monto_gasto)} — {desc_gasto} ({pagador})")
            st.rerun()

    # ── Cerrar caja ──
    if caja['caja_abierta'] and not caja['cerrada']:
        st.markdown("---")
        with st.expander("🔒 Cerrar Caja"):
            st.markdown(f"**Efectivo esperado:** {fmt_cop(caja['efectivo_esperado'])}")
            with st.form("form_cerrar_caja"):
                efectivo_real = st.number_input("Efectivo real en caja", min_value=0, value=0, step=1000)
                notas_caja = st.text_input("Notas de cierre")
                if st.form_submit_button("Cerrar Caja", use_container_width=True):
                    result = cerrar_caja(hoy.isoformat(), efectivo_real, notas_caja.strip() or None)
                    dif = result['diferencia']
                    if abs(dif) < 1:
                        st.success("Caja cuadrada ✅")
                    elif dif > 0:
                        st.warning(f"Sobrante: {fmt_cop(dif)}")
                    else:
                        st.error(f"Faltante: {fmt_cop(abs(dif))}")
                    st.rerun()
    elif caja['cerrada']:
        st.markdown("---")
        st.success(f"Caja cerrada — {fmt_cop(caja['efectivo_cierre_real'] or 0)}")
