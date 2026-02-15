"""Vista Admin — 5 tabs: Gastos, Socios, Pedidos, Caja, Config. v1.3"""
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
CATEGORIAS_PRODUCTO = ['Camisa', 'Hoodie', 'Buzo', 'Chaqueta', 'Chompa', 'Jogger', 'Sudadera', 'Pantaloneta', 'Otro']
TALLAS = ['S', 'M', 'L', 'XL', '2XL']
# Mapa para auto-SKU: primeras 3 letras de categoría
CAT_PREFIX = {
    'Camisa': 'CAM', 'Hoodie': 'HOO', 'Buzo': 'BUZ', 'Chaqueta': 'CHQ',
    'Chompa': 'CHO', 'Jogger': 'JOG', 'Sudadera': 'SUD', 'Pantaloneta': 'PAN', 'Otro': 'OTR',
}


def render():
    st.markdown("## Administracion")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Gastos", "Socios", "Pedidos", "Caja", "Config"
    ])

    with tab1:
        render_gastos()
    with tab2:
        render_liquidacion()
    with tab3:
        render_pedidos()
    with tab4:
        render_caja()
    with tab5:
        render_config()


# ══════════════════════════════════════════════════════════
# TAB 1: GASTOS
# ══════════════════════════════════════════════════════════

def render_gastos():
    st.markdown("### Registrar Gasto")

    modo = st.radio(
        "Modo",
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
        rows = []
        for g in data['gastos']:
            rows.append({
                'Fecha': g['fecha'],
                'Cat': g['categoria'][:15],
                'Monto': fmt_cop(g['monto']),
                'Desc': (g.get('descripcion') or '')[:30],
                'Quien': g['pagado_por'],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"**Total mes: {fmt_cop(data['total'])}**")

        # Edit/delete en expander
        with st.expander("Editar / Eliminar gasto"):
            gasto_opciones = [
                f"#{g['id']} — {g['fecha']} — {fmt_cop(g['monto'])} — {(g.get('descripcion') or '')[:25]} ({g['pagado_por']})"
                for g in data['gastos']
            ]
            sel_idx = st.selectbox("Seleccionar gasto", range(len(gasto_opciones)),
                                   format_func=lambda i: gasto_opciones[i], key="sel_gasto_edit")
            g = data['gastos'][sel_idx]

            with st.form(f"form_edit_gasto"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_monto = st.number_input("Monto", value=int(g['monto']), step=1000, key="eg_monto")
                with ec2:
                    new_pagado = st.selectbox("Pagado por", SOCIOS,
                                              index=SOCIOS.index(g['pagado_por']) if g['pagado_por'] in SOCIOS else 0,
                                              key="eg_pagador")
                new_desc = st.text_input("Descripcion", value=g.get('descripcion', ''), key="eg_desc")

                col_save, col_del = st.columns(2)
                with col_save:
                    if st.form_submit_button("Guardar cambios", use_container_width=True):
                        editar_gasto(g['id'], monto=new_monto, pagado_por=new_pagado, descripcion=new_desc)
                        st.success("Gasto actualizado")
                        st.rerun()
                with col_del:
                    if st.form_submit_button("Eliminar gasto", use_container_width=True):
                        eliminar_gasto(g['id'])
                        st.success(f"Gasto #{g['id']} eliminado")
                        st.rerun()
    else:
        st.info("No hay gastos este mes")


def _form_gasto_parejo():
    with st.form("form_gasto_parejo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gp_fecha")
        with col2:
            categoria = st.selectbox("Categoria", CATEGORIAS_GASTO, key="gp_cat")
        col3, col4 = st.columns(2)
        with col3:
            monto_total = st.number_input("Monto total", min_value=0, value=0, step=1000, key="gp_monto")
        with col4:
            metodo_pago = st.selectbox("Metodo", ['Efectivo', 'Transferencia', 'Datafono'], key="gp_metodo")
        descripcion = st.text_input("Descripcion", key="gp_desc")
        es_inversion = st.checkbox("Es inversion inicial", key="gp_inv")
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
            categoria = st.selectbox("Categoria", CATEGORIAS_GASTO, key="gc_cat")
        col_jp, col_ka, col_an = st.columns(3)
        with col_jp:
            monto_jp = st.number_input("JP", min_value=0, value=0, step=1000, key="gc_jp")
        with col_ka:
            monto_kathe = st.number_input("KATHE", min_value=0, value=0, step=1000, key="gc_kathe")
        with col_an:
            monto_andres = st.number_input("ANDRES", min_value=0, value=0, step=1000, key="gc_andres")
        metodo_pago = st.selectbox("Metodo", ['Efectivo', 'Transferencia', 'Datafono'], key="gc_metodo")
        descripcion = st.text_input("Descripcion", key="gc_desc")
        es_inversion = st.checkbox("Es inversion inicial", key="gc_inv")
        submit = st.form_submit_button("Registrar personalizado", use_container_width=True)

    if submit and descripcion and (monto_jp + monto_kathe + monto_andres) > 0:
        montos = {'JP': monto_jp, 'KATHE': monto_kathe, 'ANDRES': monto_andres}
        registrar_gasto_personalizado(
            fecha=fecha.isoformat(), categoria=categoria, montos_por_socio=montos,
            descripcion=descripcion, metodo_pago=metodo_pago,
            es_inversion=1 if es_inversion else 0,
        )
        st.success("Gasto personalizado registrado")
        st.rerun()


def _form_gasto_individual():
    with st.form("form_gasto_individual", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today(), key="gi_fecha")
        with col2:
            categoria = st.selectbox("Categoria", CATEGORIAS_GASTO, key="gi_cat")
        col3, col4 = st.columns(2)
        with col3:
            monto = st.number_input("Monto", min_value=0, value=0, step=1000, key="gi_monto")
        with col4:
            pagado_por = st.selectbox("Pagado por", VENDEDORES, key="gi_pagador")
        descripcion = st.text_input("Descripcion", key="gi_desc")
        metodo_pago = st.selectbox("Metodo", ['Efectivo', 'Transferencia', 'Datafono'], key="gi_metodo")
        es_inversion = st.checkbox("Es inversion inicial", key="gi_inv")
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
# TAB 2: SOCIOS (Liquidacion)
# ══════════════════════════════════════════════════════════

def render_liquidacion():
    st.markdown("### Liquidacion de Socios")
    liq = calcular_liquidacion_socios()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total gastos", fmt_cop(liq['total_real']))
    with c2:
        st.metric("Parte por socio (33.3%)", fmt_cop(liq['parte_cada_uno']))

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
            'Corresponde': fmt_cop(s['le_corresponde']),
            'Saldo': estado,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Detalle por socio y categoria"):
        for socio in SOCIOS:
            st.markdown(f"**{socio}** — Total: {fmt_cop(liq['aportes'][socio])}")
            cats = liq['por_socio_categoria'].get(socio, {})
            for cat, total in sorted(cats.items(), key=lambda x: -x[1]):
                st.text(f"  {cat}: {fmt_cop(total)}")


# ══════════════════════════════════════════════════════════
# TAB 3: PEDIDOS
# ══════════════════════════════════════════════════════════

def render_pedidos():
    st.markdown("### Pedidos a Proveedores")

    total_pendiente = get_total_deuda_proveedores()
    st.metric("Pendiente de pago", fmt_cop(total_pendiente))

    # ── Nuevo pedido ──
    with st.expander("Nuevo Pedido"):
        with st.form("form_nuevo_pedido", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha_ped = st.date_input("Fecha", value=date.today(), key="np_fecha")
            with col2:
                proveedor = st.selectbox("Proveedor", PROVEEDORES, key="np_prov")
            descripcion = st.text_input("Descripcion", key="np_desc")
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
                    st.success(f"Pedido: {descripcion} ({unidades} x {fmt_cop(costo_unit)})")
                    st.rerun()

    # ── Lista de pedidos ──
    pedidos = get_pedidos()
    if not pedidos:
        st.info("No hay pedidos registrados")
        return

    for p in pedidos:
        estado_icon = {"Pendiente": "🟡", "Pagado": "🔵", "Completo": "🟢"}.get(p['estado'], "")
        label = f"{estado_icon} {p['proveedor']} — {(p.get('descripcion') or '')[:30]} — {fmt_cop(p['total'] or 0)} ({p['estado']})"
        with st.expander(label):
            st.markdown(f"**Fecha:** {p['fecha_pedido']} | **Uds:** {p.get('unidades', 0)} | **C/u:** {fmt_cop(p.get('costo_unitario', 0))}")
            if p.get('notas'):
                st.caption(f"Notas: {p['notas']}")

            # Pagar (Pendiente -> Pagado)
            if p['estado'] == 'Pendiente':
                with st.form(f"form_pagar_{p['id']}"):
                    cp1, cp2 = st.columns(2)
                    with cp1:
                        pagador = st.selectbox("Pagado por", SOCIOS, key=f"pp_pag_{p['id']}")
                    with cp2:
                        metodo = st.selectbox("Metodo", ['Transferencia', 'Efectivo', 'Datafono'], key=f"pp_met_{p['id']}")
                    if st.form_submit_button("Marcar como Pagado", use_container_width=True):
                        try:
                            pagar_pedido(p['id'], pagador, metodo_pago=metodo)
                            st.success(f"Pedido #{p['id']} pagado por {pagador}")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

            # Recibir (Pagado -> Completo)
            if p['estado'] == 'Pagado':
                st.info("Pedido pagado. Registra recepcion:")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("Completar sin stock", key=f"recibir_simple_{p['id']}"):
                        recibir_mercancia(p['id'], [])
                        st.success(f"Pedido #{p['id']} completado")
                        st.rerun()
                with col_r2:
                    with st.form(f"form_recibir_{p['id']}"):
                        sku_add = st.text_input("SKU", key=f"rs_sku_{p['id']}")
                        cant_add = st.number_input("Cantidad", min_value=1, value=int(p.get('unidades', 1) or 1), step=1, key=f"rs_cant_{p['id']}")
                        if st.form_submit_button("Recibir + Stock"):
                            if sku_add:
                                try:
                                    recibir_mercancia(p['id'], [(sku_add.strip().upper(), cant_add)])
                                    st.success(f"+{cant_add} uds a {sku_add}")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))

            # Eliminar
            if st.button("Eliminar pedido", key=f"del_ped_{p['id']}"):
                eliminar_pedido(p['id'])
                st.success(f"Pedido #{p['id']} eliminado")
                st.rerun()


# ══════════════════════════════════════════════════════════
# TAB 4: CAJA + CREDITOS
# ══════════════════════════════════════════════════════════

def render_caja():
    st.markdown("### Caja del Dia")

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
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Inicio", fmt_cop(estado['efectivo_inicio']))
        with c2:
            st.metric("+ Ventas ef.", fmt_cop(estado['ventas_efectivo']))
        with c3:
            st.metric("- Gastos ef.", fmt_cop(estado['gastos_efectivo']))

        st.metric("Efectivo esperado", fmt_cop(estado['efectivo_esperado']))

        if estado['totales_ventas']:
            parts = [f"{m}: {fmt_cop(t)}" for m, t in estado['totales_ventas'].items()]
            st.caption("Ventas: " + " | ".join(parts))

        if estado['cerrada']:
            st.success(f"Caja cerrada — Real: {fmt_cop(estado['efectivo_cierre_real'] or 0)}")
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

    # ── Creditos pendientes (dentro de tab Caja) ──
    st.markdown("---")
    st.markdown("### Creditos Pendientes")

    creditos = get_creditos_pendientes()
    if not creditos:
        st.success("No hay creditos pendientes")
    else:
        total_cred = sum(c['monto'] for c in creditos)
        st.metric("Total por cobrar", fmt_cop(total_cred))

        for c in creditos:
            col1, col2 = st.columns([4, 1])
            with col1:
                nombre_prod = c.get('producto_nombre') or c.get('sku', '')
                st.markdown(f"**{c['cliente']}** — {fmt_cop(c['monto'])} — {nombre_prod} ({c['fecha_credito']})")
            with col2:
                if st.button("Pagado", key=f"pagar_{c['id']}"):
                    registrar_pago_credito(c['id'])
                    st.success(f"Credito de {c['cliente']} pagado")
                    st.rerun()


# ══════════════════════════════════════════════════════════
# TAB 5: CONFIG (Costos Fijos + Productos)
# ══════════════════════════════════════════════════════════

def render_config():
    sub1, sub2 = st.tabs(["Costos Fijos", "Productos"])

    with sub1:
        _render_costos_fijos()
    with sub2:
        _render_productos()


def _render_costos_fijos():
    st.markdown("### Costos Fijos Mensuales")

    costos = get_costos_fijos()
    total = sum(c['monto_mensual'] for c in costos if c.get('activo'))
    st.metric("Total activos", fmt_cop(total))

    if costos:
        rows = []
        for c in costos:
            rows.append({
                'Estado': "Activo" if c.get('activo') else "Inactivo",
                'Concepto': c['concepto'],
                'Monto': fmt_cop(c['monto_mensual']),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Edit/delete en expander
        with st.expander("Editar / Eliminar"):
            cf_opciones = [f"#{c['id']} — {c['concepto']} — {fmt_cop(c['monto_mensual'])}" for c in costos]
            sel_cf = st.selectbox("Seleccionar", range(len(cf_opciones)),
                                  format_func=lambda i: cf_opciones[i], key="sel_cf_edit")
            c = costos[sel_cf]

            with st.form("form_edit_cf"):
                nc = st.text_input("Concepto", value=c['concepto'], key="ecf_concepto")
                nm = st.number_input("Monto mensual", value=int(c['monto_mensual']), step=1000, key="ecf_monto")
                na = st.checkbox("Activo", value=bool(c.get('activo', 1)), key="ecf_activo")

                col_s, col_d = st.columns(2)
                with col_s:
                    if st.form_submit_button("Guardar", use_container_width=True):
                        editar_costo_fijo(c['id'], concepto=nc, monto_mensual=nm, activo=1 if na else 0)
                        st.success("Actualizado")
                        st.rerun()
                with col_d:
                    if st.form_submit_button("Eliminar", use_container_width=True):
                        eliminar_costo_fijo(c['id'])
                        st.success("Eliminado")
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
            if new_concepto and new_monto >= 0:
                crear_costo_fijo(new_concepto, new_monto)
                st.success(f"Agregado: {new_concepto} — {fmt_cop(new_monto)}")
                st.rerun()


def _generar_sku(categoria, color, talla):
    """Genera SKU automatico: CAT-COL-TALLA (ej: CAM-NEG-S)."""
    cat_code = CAT_PREFIX.get(categoria, categoria[:3].upper())
    color_code = color.strip().upper()[:3] if color else 'XXX'
    talla_code = talla.strip().upper()
    return f"{cat_code}-{color_code}-{talla_code}"


def _render_productos():
    st.markdown("### Productos")

    productos = get_productos()
    st.metric("Total SKUs", len(productos))

    # Nuevo producto con auto-SKU
    with st.expander("Nuevo Producto"):
        with st.form("form_nuevo_prod", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre", key="np_nombre")
            with col2:
                categoria = st.selectbox("Categoria", CATEGORIAS_PRODUCTO, key="np_cat")
            col3, col4, col5 = st.columns(3)
            with col3:
                talla = st.selectbox("Talla", TALLAS, key="np_talla")
            with col4:
                color = st.text_input("Color", key="np_color")
            with col5:
                proveedor = st.selectbox("Proveedor", PROVEEDORES + [''], key="np_prov_prod")
            col6, col7, col8 = st.columns(3)
            with col6:
                costo = st.number_input("Costo", min_value=0, value=0, step=1000, key="np_costo_prod")
            with col7:
                precio_venta = st.number_input("Precio venta", min_value=0, value=0, step=1000, key="np_precio")
            with col8:
                stock_ini = st.number_input("Stock inicial", min_value=0, value=0, step=1, key="np_stock")

            # Mostrar SKU auto-generado
            sku_auto = _generar_sku(categoria, color or 'XXX', talla)
            sku_override = st.text_input("SKU (auto-generado, editable)", value=sku_auto, key="np_sku")

            if st.form_submit_button("Crear Producto", use_container_width=True):
                final_sku = sku_override.strip().upper() if sku_override.strip() else sku_auto
                if nombre and costo > 0 and precio_venta > 0:
                    try:
                        crear_producto(
                            sku=final_sku, nombre=nombre, categoria=categoria,
                            talla=talla, color=color, costo=costo, precio_venta=precio_venta,
                            stock=stock_ini, proveedor=proveedor or None,
                        )
                        st.success(f"Producto {final_sku} creado")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # Lista de productos — tabla compacta
    st.markdown("---")
    if productos:
        rows = []
        for p in productos:
            rows.append({
                'SKU': p['sku'],
                'Nombre': p['nombre'][:30],
                'Precio': fmt_cop(p['precio_venta']),
                'Costo': fmt_cop(p['costo']),
                'Stock': p['stock'],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Edit/delete en expander
        with st.expander("Editar / Eliminar producto"):
            prod_opciones = [f"{p['sku']} — {p['nombre'][:25]} — Stock: {p['stock']}" for p in productos]
            sel_prod = st.selectbox("Seleccionar producto", range(len(prod_opciones)),
                                    format_func=lambda i: prod_opciones[i], key="sel_prod_edit")
            p = productos[sel_prod]

            with st.form("form_edit_prod"):
                ep1, ep2 = st.columns(2)
                with ep1:
                    new_costo = st.number_input("Costo", value=int(p['costo']), step=1000, key="ep_costo")
                with ep2:
                    new_precio = st.number_input("Precio venta", value=int(p['precio_venta']), step=1000, key="ep_precio")
                ep3, ep4 = st.columns(2)
                with ep3:
                    new_stock = st.number_input("Stock", value=int(p['stock']), step=1, key="ep_stock")
                with ep4:
                    new_min = st.number_input("Stock minimo", value=int(p.get('stock_minimo', 3)), step=1, key="ep_min")

                col_s, col_d = st.columns(2)
                with col_s:
                    if st.form_submit_button("Guardar", use_container_width=True):
                        editar_producto(p['sku'], costo=new_costo, precio_venta=new_precio,
                                        stock=new_stock, stock_minimo=new_min)
                        st.success(f"{p['sku']} actualizado")
                        st.rerun()
                with col_d:
                    if st.form_submit_button("Eliminar", use_container_width=True):
                        try:
                            eliminar_producto(p['sku'])
                            st.success(f"{p['sku']} eliminado")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
