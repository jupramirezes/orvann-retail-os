"""Vista Admin — Gastos, liquidación, caja, créditos, pedidos, costos fijos, productos. v1.2"""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import (
    registrar_gasto, registrar_gasto_parejo, registrar_gasto_personalizado,
    editar_gasto, eliminar_gasto, get_gastos_mes,
    calcular_liquidacion_socios,
    get_estado_caja, abrir_caja, cerrar_caja,
    get_creditos_pendientes, registrar_pago_credito,
    get_pedidos, get_pedidos_pendientes, get_total_deuda_proveedores,
    registrar_pedido, pagar_pedido, recibir_mercancia, eliminar_pedido,
    get_costos_fijos, crear_costo_fijo, editar_costo_fijo, eliminar_costo_fijo,
    get_productos, crear_producto, editar_producto, eliminar_producto,
    agregar_stock,
)
from app.database import query
from app.components.helpers import (
    fmt_cop, CATEGORIAS_GASTO, METODOS_PAGO, VENDEDORES,
)

SOCIOS = ['JP', 'KATHE', 'ANDRES']
PROVEEDORES = ['YOUR BRAND', 'BRACOR', 'AUREN', 'Otro']


def render():
    st.markdown("## ⚙️ Administración")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💸 Gastos", "🤝 Liquidación", "💰 Caja",
        "📋 Créditos", "📦 Pedidos", "📊 Costos Fijos", "🏷️ Productos"
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
    with tab6:
        render_costos_fijos()
    with tab7:
        render_productos()


# ══════════════════════════════════════════════════════════
# GASTOS
# ══════════════════════════════════════════════════════════

def render_gastos():
    st.markdown("### Registrar Gasto")

    modo = st.radio(
        "Modo de registro",
        ["Parejo (dividir entre 3)", "Personalizado (montos diferentes)", "Solo uno (un socio)"],
        horizontal=True, key="modo_gasto",
    )

    if "Parejo" in modo:
        _form_gasto_parejo()
    elif "Personalizado" in modo:
        _form_gasto_personalizado()
    else:
        _form_gasto_individual()

    # Gastos del mes con edit/delete
    st.markdown("---")
    st.markdown("### Gastos del Mes")
    hoy = date.today()
    data = get_gastos_mes(hoy.year, hoy.month)

    if data['gastos']:
        for g in data['gastos']:
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                st.markdown(
                    f"**{g['categoria']}** — {fmt_cop(g['monto'])} — {g.get('descripcion', '')} "
                    f"({g['pagado_por']}) — {g['fecha']}"
                )
            with col2:
                if st.button("✏️", key=f"edit_g_{g['id']}", help="Editar"):
                    st.session_state[f'editing_gasto_{g["id"]}'] = True
            with col3:
                if st.button("🗑️", key=f"del_g_{g['id']}", help="Eliminar"):
                    eliminar_gasto(g['id'])
                    st.success(f"Gasto #{g['id']} eliminado")
                    st.rerun()

            # Inline edit form
            if st.session_state.get(f'editing_gasto_{g["id"]}'):
                with st.form(f"form_edit_gasto_{g['id']}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_monto = st.number_input("Monto", value=int(g['monto']), step=1000, key=f"eg_m_{g['id']}")
                    with ec2:
                        new_pagado = st.selectbox("Pagado por", SOCIOS,
                                                  index=SOCIOS.index(g['pagado_por']) if g['pagado_por'] in SOCIOS else 0,
                                                  key=f"eg_p_{g['id']}")
                    new_desc = st.text_input("Descripción", value=g.get('descripcion', ''), key=f"eg_d_{g['id']}")
                    ec3, ec4 = st.columns(2)
                    with ec3:
                        if st.form_submit_button("Guardar"):
                            editar_gasto(g['id'], monto=new_monto, pagado_por=new_pagado, descripcion=new_desc)
                            del st.session_state[f'editing_gasto_{g["id"]}']
                            st.success("Gasto actualizado")
                            st.rerun()
                    with ec4:
                        if st.form_submit_button("Cancelar"):
                            del st.session_state[f'editing_gasto_{g["id"]}']
                            st.rerun()

        st.markdown(f"**Total mes: {fmt_cop(data['total'])}**")
    else:
        st.info("No hay gastos este mes")


def _form_gasto_parejo():
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
            metodo_pago = st.selectbox("Método", ['Efectivo', 'Transferencia', 'Datáfono'], key="gp_metodo")
        descripcion = st.text_input("Descripción", key="gp_desc")
        es_inversion = st.checkbox("Es inversión inicial", key="gp_inv")
        submit = st.form_submit_button("Registrar gasto parejo", use_container_width=True)

    if submit and monto_total > 0 and descripcion:
        registrar_gasto_parejo(
            fecha=fecha.isoformat(), categoria=categoria, monto_total=monto_total,
            descripcion=descripcion, metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
        )
        st.success(f"Gasto parejo: {fmt_cop(monto_total)} dividido entre 3")
        st.rerun()


def _form_gasto_personalizado():
    with st.form("form_gasto_personalizado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gc_fecha")
        with col2:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gc_cat")
        col_jp, col_ka, col_an = st.columns(3)
        with col_jp:
            monto_jp = st.number_input("JP", min_value=0, value=0, step=1000, key="gc_jp")
        with col_ka:
            monto_kathe = st.number_input("KATHE", min_value=0, value=0, step=1000, key="gc_kathe")
        with col_an:
            monto_andres = st.number_input("ANDRES", min_value=0, value=0, step=1000, key="gc_andres")
        metodo_pago = st.selectbox("Método", ['Efectivo', 'Transferencia', 'Datáfono'], key="gc_metodo")
        descripcion = st.text_input("Descripción", key="gc_desc")
        es_inversion = st.checkbox("Es inversión inicial", key="gc_inv")
        submit = st.form_submit_button("Registrar personalizado", use_container_width=True)

    if submit and descripcion and (monto_jp + monto_kathe + monto_andres) > 0:
        montos = {'JP': monto_jp, 'KATHE': monto_kathe, 'ANDRES': monto_andres}
        registrar_gasto_personalizado(
            fecha=fecha.isoformat(), categoria=categoria, montos_por_socio=montos,
            descripcion=descripcion, metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
        )
        st.success(f"Gasto personalizado registrado")
        st.rerun()


def _form_gasto_individual():
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
        metodo_pago = st.selectbox("Método", ['Efectivo', 'Transferencia', 'Datáfono'], key="gi_metodo")
        es_inversion = st.checkbox("Es inversión inicial", key="gi_inv")
        submit = st.form_submit_button("Registrar gasto", use_container_width=True)

    if submit and monto > 0 and descripcion:
        registrar_gasto(
            fecha=fecha.isoformat(), categoria=categoria, monto=monto,
            descripcion=descripcion, pagado_por=pagado_por, metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
        )
        st.success(f"Gasto: {fmt_cop(monto)} — {descripcion} ({pagado_por})")
        st.rerun()


# ══════════════════════════════════════════════════════════
# LIQUIDACIÓN
# ══════════════════════════════════════════════════════════

def render_liquidacion():
    st.markdown("### Liquidación de Socios")
    liq = calcular_liquidacion_socios()

    st.markdown(f"**Total gastos reales:** {fmt_cop(liq['total_real'])}")
    st.markdown(f"**Parte por socio (33.3%):** {fmt_cop(liq['parte_cada_uno'])}")

    rows = []
    for socio in SOCIOS:
        s = liq['saldos'][socio]
        saldo_val = s['saldo']
        estado = f"Le deben {fmt_cop(saldo_val)}" if saldo_val > 0 else (
            f"Debe {fmt_cop(abs(saldo_val))}" if saldo_val < 0 else "A paz y salvo"
        )
        rows.append({
            'Socio': socio, 'Aportado': fmt_cop(s['aportado']),
            'Le corresponde': fmt_cop(s['le_corresponde']), 'Saldo': estado,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Detalle por socio y categoría"):
        for socio in SOCIOS:
            st.markdown(f"**{socio}** — Total: {fmt_cop(liq['aportes'][socio])}")
            cats = liq['por_socio_categoria'].get(socio, {})
            for cat, total in sorted(cats.items(), key=lambda x: -x[1]):
                st.text(f"  {cat}: {fmt_cop(total)}")


# ══════════════════════════════════════════════════════════
# CAJA
# ══════════════════════════════════════════════════════════

def render_caja():
    st.markdown("### Gestión de Caja")

    fecha_caja = st.date_input("Fecha", value=date.today(), key="fecha_caja_admin")
    estado = get_estado_caja(fecha_caja.isoformat())

    if not estado['caja_abierta']:
        st.warning("Caja no abierta para esta fecha")
        with st.form("form_abrir_caja_admin"):
            efectivo_ini = st.number_input("Efectivo inicial", min_value=0, value=0, step=10000)
            if st.form_submit_button("Abrir Caja", use_container_width=True):
                abrir_caja(fecha_caja.isoformat(), efectivo_ini)
                st.success(f"Caja abierta con {fmt_cop(efectivo_ini)}")
                st.rerun()
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Efectivo inicio", fmt_cop(estado['efectivo_inicio']))
    with col2:
        st.metric("Ventas efectivo", fmt_cop(estado['ventas_efectivo']))
    with col3:
        st.metric("Gastos efectivo", fmt_cop(estado['gastos_efectivo']))

    st.metric("Efectivo esperado", fmt_cop(estado['efectivo_esperado']))

    if estado['totales_ventas']:
        st.markdown("**Ventas por método:**")
        for met, total in estado['totales_ventas'].items():
            st.text(f"  {met}: {fmt_cop(total)}")

    if estado['cerrada']:
        st.success(f"Caja cerrada — Efectivo real: {fmt_cop(estado['efectivo_cierre_real'] or 0)}")
    else:
        with st.form("form_cierre_caja_admin"):
            efectivo_real = st.number_input("Efectivo real en caja", min_value=0, value=0, step=1000)
            notas_caja = st.text_input("Notas")
            if st.form_submit_button("Cerrar Caja", use_container_width=True):
                result = cerrar_caja(fecha_caja.isoformat(), efectivo_real, notas_caja.strip() or None)
                dif = result['diferencia']
                if abs(dif) < 1:
                    st.success("Caja cuadrada")
                elif dif > 0:
                    st.warning(f"Sobrante: {fmt_cop(dif)}")
                else:
                    st.error(f"Faltante: {fmt_cop(abs(dif))}")
                st.rerun()


# ══════════════════════════════════════════════════════════
# CRÉDITOS
# ══════════════════════════════════════════════════════════

def render_creditos():
    st.markdown("### Créditos Pendientes")

    creditos = get_creditos_pendientes()
    if not creditos:
        st.success("No hay créditos pendientes")
        return

    total = sum(c['monto'] for c in creditos)
    st.metric("Total por cobrar", fmt_cop(total))

    for c in creditos:
        col1, col2 = st.columns([4, 1])
        with col1:
            nombre_prod = c.get('producto_nombre') or c.get('sku', '')
            st.markdown(f"**{c['cliente']}** — {fmt_cop(c['monto'])} — {nombre_prod} ({c['fecha_credito']})")
        with col2:
            if st.button("Pagado", key=f"pagar_{c['id']}"):
                registrar_pago_credito(c['id'])
                st.success(f"Crédito de {c['cliente']} pagado")
                st.rerun()


# ══════════════════════════════════════════════════════════
# PEDIDOS (TAREA 4 — CRUD completo)
# ══════════════════════════════════════════════════════════

def render_pedidos():
    st.markdown("### Pedidos a Proveedores")

    total_pendiente = get_total_deuda_proveedores()
    st.metric("Total pendiente de pago", fmt_cop(total_pendiente))

    # ── Nuevo pedido ──
    with st.expander("Nuevo Pedido", expanded=False):
        with st.form("form_nuevo_pedido", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha_ped = st.date_input("Fecha pedido", value=date.today(), key="np_fecha")
            with col2:
                proveedor = st.selectbox("Proveedor", PROVEEDORES, key="np_prov")
            descripcion = st.text_input("Descripción", key="np_desc")
            col3, col4 = st.columns(2)
            with col3:
                unidades = st.number_input("Unidades", min_value=1, value=1, step=1, key="np_uds")
            with col4:
                costo_unit = st.number_input("Costo unitario", min_value=0, value=0, step=1000, key="np_costo")
            notas_ped = st.text_input("Notas (opcional)", key="np_notas")
            if st.form_submit_button("Registrar Pedido", use_container_width=True):
                if descripcion and costo_unit > 0:
                    registrar_pedido(
                        fecha_pedido=fecha_ped.isoformat(), proveedor=proveedor,
                        descripcion=descripcion, unidades=unidades,
                        costo_unitario=costo_unit, notas=notas_ped.strip() or None,
                    )
                    st.success(f"Pedido registrado: {descripcion} ({unidades} uds x {fmt_cop(costo_unit)})")
                    st.rerun()

    # ── Lista de pedidos con acciones ──
    pedidos = get_pedidos()
    if not pedidos:
        st.info("No hay pedidos registrados")
        return

    for p in pedidos:
        estado_color = {"Pendiente": "🟡", "Pagado": "🔵", "Completo": "🟢"}.get(p['estado'], "⚪")
        with st.expander(f"{estado_color} {p['proveedor']} — {p.get('descripcion', '')} — {fmt_cop(p['total'] or 0)} ({p['estado']})"):
            st.markdown(f"**Fecha:** {p['fecha_pedido']} | **Unidades:** {p.get('unidades', 0)} | **Costo unit:** {fmt_cop(p.get('costo_unitario', 0))}")
            if p.get('notas'):
                st.caption(f"Notas: {p['notas']}")

            col_a1, col_a2, col_a3 = st.columns(3)

            # Pagar pedido (Pendiente → Pagado)
            if p['estado'] == 'Pendiente':
                with col_a1:
                    with st.form(f"form_pagar_{p['id']}"):
                        pagador = st.selectbox("Pagado por", SOCIOS, key=f"pp_pagador_{p['id']}")
                        metodo = st.selectbox("Método", ['Transferencia', 'Efectivo', 'Datáfono'], key=f"pp_met_{p['id']}")
                        if st.form_submit_button("Marcar como Pagado"):
                            try:
                                pagar_pedido(p['id'], pagador, metodo_pago=metodo)
                                st.success(f"Pedido #{p['id']} pagado por {pagador}")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))

            # Recibir mercancía (Pagado → Completo)
            if p['estado'] == 'Pagado':
                with col_a1:
                    st.info("Pedido pagado. Registra recepción de mercancía.")
                    if st.button("Marcar como Recibido (sin stock)", key=f"recibir_simple_{p['id']}"):
                        recibir_mercancia(p['id'], [])
                        st.success(f"Pedido #{p['id']} completado")
                        st.rerun()
                with col_a2:
                    with st.form(f"form_recibir_{p['id']}"):
                        st.markdown("**Agregar stock por SKU:**")
                        sku_add = st.text_input("SKU", key=f"rs_sku_{p['id']}")
                        cant_add = st.number_input("Cantidad", min_value=1, value=int(p.get('unidades', 1) or 1), step=1, key=f"rs_cant_{p['id']}")
                        if st.form_submit_button("Recibir + Stock"):
                            if sku_add:
                                try:
                                    recibir_mercancia(p['id'], [(sku_add, cant_add)])
                                    st.success(f"Pedido #{p['id']} completado. +{cant_add} uds a {sku_add}")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))

            # Eliminar pedido
            with col_a3:
                if st.button("🗑️ Eliminar", key=f"del_ped_{p['id']}"):
                    eliminar_pedido(p['id'])
                    st.success(f"Pedido #{p['id']} eliminado")
                    st.rerun()


# ══════════════════════════════════════════════════════════
# COSTOS FIJOS (TAREA 5)
# ══════════════════════════════════════════════════════════

def render_costos_fijos():
    st.markdown("### Costos Fijos Mensuales")

    costos = get_costos_fijos()
    total = sum(c['monto_mensual'] for c in costos if c.get('activo'))
    st.metric("Total costos fijos activos", fmt_cop(total))

    # Lista con edit/delete
    for c in costos:
        estado = "✅" if c.get('activo') else "❌"
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(f"{estado} **{c['concepto']}** — {fmt_cop(c['monto_mensual'])}")
        with col2:
            if st.button("✏️", key=f"edit_cf_{c['id']}"):
                st.session_state[f'editing_cf_{c["id"]}'] = True
        with col3:
            if st.button("🗑️", key=f"del_cf_{c['id']}"):
                eliminar_costo_fijo(c['id'])
                st.success(f"Costo fijo eliminado")
                st.rerun()

        if st.session_state.get(f'editing_cf_{c["id"]}'):
            with st.form(f"form_edit_cf_{c['id']}"):
                nc = st.text_input("Concepto", value=c['concepto'], key=f"ecf_c_{c['id']}")
                nm = st.number_input("Monto mensual", value=int(c['monto_mensual']), step=1000, key=f"ecf_m_{c['id']}")
                na = st.checkbox("Activo", value=bool(c.get('activo', 1)), key=f"ecf_a_{c['id']}")
                if st.form_submit_button("Guardar"):
                    editar_costo_fijo(c['id'], concepto=nc, monto_mensual=nm, activo=1 if na else 0)
                    del st.session_state[f'editing_cf_{c["id"]}']
                    st.success("Actualizado")
                    st.rerun()

    # Nuevo costo fijo
    st.markdown("---")
    with st.form("form_nuevo_cf", clear_on_submit=True):
        st.markdown("**Agregar costo fijo**")
        col1, col2 = st.columns(2)
        with col1:
            new_concepto = st.text_input("Concepto", key="ncf_concepto")
        with col2:
            new_monto = st.number_input("Monto mensual", min_value=0, value=0, step=1000, key="ncf_monto")
        if st.form_submit_button("Agregar", use_container_width=True):
            if new_concepto and new_monto > 0:
                crear_costo_fijo(new_concepto, new_monto)
                st.success(f"Costo fijo agregado: {new_concepto} — {fmt_cop(new_monto)}")
                st.rerun()


# ══════════════════════════════════════════════════════════
# PRODUCTOS (TAREA 5 — crear, editar, eliminar)
# ══════════════════════════════════════════════════════════

CATEGORIAS_PRODUCTO = ['Camisa', 'Hoodie', 'Buzo', 'Chaqueta', 'Chompa', 'Jogger', 'Sudadera', 'Pantaloneta', 'Otro']
TALLAS = ['S', 'M', 'L', 'XL', '2XL']

def render_productos():
    st.markdown("### Gestión de Productos")

    productos = get_productos()
    st.metric("Total productos", len(productos))

    # Nuevo producto
    with st.expander("Nuevo Producto"):
        with st.form("form_nuevo_prod", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("SKU", key="np_sku", placeholder="CAM-OVS-NEG-S")
            with col2:
                nombre = st.text_input("Nombre", key="np_nombre")
            col3, col4, col5 = st.columns(3)
            with col3:
                categoria = st.selectbox("Categoría", CATEGORIAS_PRODUCTO, key="np_cat")
            with col4:
                talla = st.selectbox("Talla", TALLAS, key="np_talla")
            with col5:
                color = st.text_input("Color", key="np_color")
            col6, col7, col8 = st.columns(3)
            with col6:
                costo = st.number_input("Costo", min_value=0, value=0, step=1000, key="np_costo_prod")
            with col7:
                precio_venta = st.number_input("Precio venta", min_value=0, value=0, step=1000, key="np_precio")
            with col8:
                stock_ini = st.number_input("Stock inicial", min_value=0, value=0, step=1, key="np_stock")
            proveedor = st.selectbox("Proveedor", PROVEEDORES + [''], key="np_prov_prod")
            if st.form_submit_button("Crear Producto", use_container_width=True):
                if sku and nombre and costo > 0 and precio_venta > 0:
                    try:
                        crear_producto(
                            sku=sku.strip().upper(), nombre=nombre, categoria=categoria,
                            talla=talla, color=color, costo=costo, precio_venta=precio_venta,
                            stock=stock_ini, proveedor=proveedor or None,
                        )
                        st.success(f"Producto {sku} creado")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # Lista de productos con edit
    st.markdown("---")
    for p in productos:
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(f"**{p['sku']}** — {p['nombre']} — {fmt_cop(p['precio_venta'])} — Stock: {p['stock']}")
        with col2:
            if st.button("✏️", key=f"edit_p_{p['sku']}"):
                st.session_state[f'editing_prod_{p["sku"]}'] = True
        with col3:
            if st.button("🗑️", key=f"del_p_{p['sku']}"):
                try:
                    eliminar_producto(p['sku'])
                    st.success(f"Producto {p['sku']} eliminado")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        if st.session_state.get(f'editing_prod_{p["sku"]}'):
            with st.form(f"form_edit_prod_{p['sku']}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_costo = st.number_input("Costo", value=int(p['costo']), step=1000, key=f"ep_c_{p['sku']}")
                with ec2:
                    new_precio = st.number_input("Precio venta", value=int(p['precio_venta']), step=1000, key=f"ep_p_{p['sku']}")
                ec3, ec4 = st.columns(2)
                with ec3:
                    new_stock = st.number_input("Stock", value=int(p['stock']), step=1, key=f"ep_s_{p['sku']}")
                with ec4:
                    new_min = st.number_input("Stock mínimo", value=int(p.get('stock_minimo', 3)), step=1, key=f"ep_m_{p['sku']}")
                if st.form_submit_button("Guardar"):
                    editar_producto(p['sku'], costo=new_costo, precio_venta=new_precio,
                                    stock=new_stock, stock_minimo=new_min)
                    del st.session_state[f'editing_prod_{p["sku"]}']
                    st.success(f"Producto {p['sku']} actualizado")
                    st.rerun()
