"""Vista Inventario — Stock con filtros y alertas. v1.6"""
import streamlit as st
import pandas as pd

from app.models import get_productos, get_resumen_inventario, agregar_stock
from app.components.helpers import fmt_cop, color_stock, render_table


def render():
    st.markdown("## Inventario")

    productos = get_productos()
    if not productos:
        st.info("No hay productos en el inventario")
        return

    df = pd.DataFrame(productos)

    # ── Filtros ──
    st.markdown("### Filtros")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        categorias = ['Todas'] + sorted(df['categoria'].dropna().unique().tolist())
        cat_filter = st.selectbox("Categoría", categorias)
    with col2:
        tallas = ['Todas'] + sorted(df['talla'].dropna().unique().tolist())
        talla_filter = st.selectbox("Talla", tallas)
    with col3:
        colores = ['Todas'] + sorted(df['color'].dropna().unique().tolist())
        color_filter = st.selectbox("Color", colores)
    with col4:
        stock_filter = st.selectbox("Stock", ['Todo', 'Con stock', 'Stock bajo', 'Agotado'])

    # Aplicar filtros
    filtered = df.copy()
    if cat_filter != 'Todas':
        filtered = filtered[filtered['categoria'] == cat_filter]
    if talla_filter != 'Todas':
        filtered = filtered[filtered['talla'] == talla_filter]
    if color_filter != 'Todas':
        filtered = filtered[filtered['color'] == color_filter]
    if stock_filter == 'Con stock':
        filtered = filtered[filtered['stock'] > 0]
    elif stock_filter == 'Stock bajo':
        filtered = filtered[(filtered['stock'] > 0) & (filtered['stock'] <= filtered['stock_minimo'])]
    elif stock_filter == 'Agotado':
        filtered = filtered[filtered['stock'] <= 0]

    # ── Tabla de inventario ──
    st.markdown(f"### Productos ({len(filtered)} de {len(df)})")

    if not filtered.empty:
        # Agregar indicador visual de stock
        display = filtered[['sku', 'nombre', 'categoria', 'talla', 'color', 'costo', 'precio_venta', 'stock', 'stock_minimo']].copy()
        display['estado'] = display.apply(lambda r: color_stock(r['stock'], r['stock_minimo']), axis=1)
        display['costo'] = display['costo'].apply(fmt_cop)
        display['precio_venta'] = display['precio_venta'].apply(fmt_cop)

        render_table(display.rename(columns={
            'sku': 'SKU',
            'nombre': 'Producto',
            'categoria': 'Categoría',
            'talla': 'Talla',
            'color': 'Color',
            'costo': 'Costo',
            'precio_venta': 'Precio Venta',
            'stock': 'Stock',
            'stock_minimo': 'Mínimo',
            'estado': 'Estado',
        }))

    # ── Resumen por categoría ──
    st.markdown("---")
    st.markdown("### Resumen por Categoría")

    resumen = get_resumen_inventario()
    if resumen['por_categoria']:
        df_cat = pd.DataFrame(resumen['por_categoria'])
        df_cat['valor_costo'] = df_cat['valor_costo'].apply(lambda x: fmt_cop(x or 0))
        df_cat['valor_venta'] = df_cat['valor_venta'].apply(lambda x: fmt_cop(x or 0))
        render_table(df_cat.rename(columns={
            'categoria': 'Categoría',
            'skus': 'SKUs',
            'unidades': 'Unidades',
            'valor_costo': 'Valor Costo',
            'valor_venta': 'Valor Venta',
        }))

    # ── Agregar stock ──
    st.markdown("---")
    st.markdown("### Agregar Stock (entrada de mercancía)")

    with st.form("form_agregar_stock"):
        opciones_sku = [f"{p['sku']} | {p['nombre']}" for p in productos]
        seleccion = st.selectbox("Producto", opciones_sku, index=None, placeholder="Selecciona producto...")
        cantidad_add = st.number_input("Unidades a agregar", min_value=1, value=1, step=1)
        submit_stock = st.form_submit_button("Agregar Stock", use_container_width=True)

    if submit_stock and seleccion:
        sku = seleccion.split(" | ")[0]
        agregar_stock(sku, cantidad_add)
        st.success(f"+{cantidad_add} unidades agregadas a {sku}")
        st.rerun()
