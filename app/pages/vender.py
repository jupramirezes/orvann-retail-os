"""Vista POS — Registrar ventas. Mobile-first."""
import streamlit as st
import pandas as pd
from datetime import date

from app.models import registrar_venta, get_ventas_dia, get_productos
from app.components.helpers import fmt_cop, METODOS_PAGO, VENDEDORES


def render():
    st.markdown("## Registrar Venta")

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
        # Buscador de producto
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
            # Pre-llenar precio si hay producto seleccionado
            precio_default = 0
            if seleccion and seleccion in productos_dict:
                precio_default = int(productos_dict[seleccion]['precio_venta'])
            precio = st.number_input("Precio unitario", min_value=0, value=precio_default, step=1000)

        col3, col4 = st.columns(2)
        with col3:
            metodo = st.selectbox("Método de pago", METODOS_PAGO)
        with col4:
            vendedor = st.selectbox("Vendedor", VENDEDORES)

        # Campo cliente (obligatorio para crédito)
        cliente = st.text_input("Cliente (obligatorio si es crédito)")

        descuento = st.number_input("Descuento %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
        notas = st.text_input("Notas (opcional)")

        submitted = st.form_submit_button("Registrar Venta", use_container_width=True)

    # ── Procesar venta ──
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
                # Confirmación
                total = precio * cantidad * (1 - descuento / 100)
                st.warning(
                    f"**Confirmar venta:**\n\n"
                    f"Producto: {prod['nombre']}\n\n"
                    f"Cantidad: {cantidad} | Precio: {fmt_cop(precio)} | Descuento: {descuento}%\n\n"
                    f"**Total: {fmt_cop(total)}**\n\n"
                    f"Método: {metodo} | Vendedor: {vendedor}"
                )
                if st.button("Confirmar venta", key="confirmar_venta"):
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
                        st.success(f"Venta #{venta_id} registrada — {fmt_cop(total)}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    # ── Ventas del día ──
    st.markdown("---")
    st.markdown("### Ventas de hoy")

    data = get_ventas_dia()
    if data['ventas']:
        df = pd.DataFrame(data['ventas'])
        cols_show = ['hora', 'sku', 'producto_nombre', 'cantidad', 'precio_unitario', 'total', 'metodo_pago', 'cliente', 'vendedor']
        cols_exist = [c for c in cols_show if c in df.columns]
        st.dataframe(
            df[cols_exist].rename(columns={
                'hora': 'Hora',
                'sku': 'SKU',
                'producto_nombre': 'Producto',
                'cantidad': 'Cant.',
                'precio_unitario': 'Precio',
                'total': 'Total',
                'metodo_pago': 'Método',
                'cliente': 'Cliente',
                'vendedor': 'Vendedor',
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Totales por método
        st.markdown("#### Totales por método")
        met_cols = st.columns(len(data['totales_metodo']) + 1)
        for i, (metodo, total) in enumerate(data['totales_metodo'].items()):
            with met_cols[i]:
                st.metric(metodo, fmt_cop(total))
        with met_cols[-1]:
            st.metric("TOTAL DÍA", fmt_cop(data['total']))
    else:
        st.info("No hay ventas registradas hoy")
