"""Vista Historial — Ventas y gastos históricos con filtros. v1.4"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

from app.models import get_ventas_rango, get_gastos_rango
from app.components.helpers import fmt_cop


def render():
    st.markdown("## 📜 Historial")

    tab1, tab2 = st.tabs(["📈 Ventas", "💸 Gastos"])

    with tab1:
        render_historial_ventas()
    with tab2:
        render_historial_gastos()


def render_historial_ventas():
    st.markdown("### Historial de Ventas")

    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Desde",
            value=date.today().replace(day=1),
            key="hv_inicio",
        )
    with col2:
        fecha_fin = st.date_input(
            "Hasta",
            value=date.today(),
            key="hv_fin",
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio debe ser anterior a la fecha fin")
        return

    ventas = get_ventas_rango(fecha_inicio.isoformat(), fecha_fin.isoformat())

    if not ventas:
        st.info("No hay ventas en el rango seleccionado")
        return

    df = pd.DataFrame(ventas)

    # Limpiar None en vendedor (ventas migradas del Excel)
    if 'vendedor' in df.columns:
        df['vendedor'] = df['vendedor'].fillna('JP').replace('None', 'JP').replace('', 'JP')

    # Métricas del rango
    total_ventas = df['total'].sum()
    total_unidades = df['cantidad'].sum()
    total_costo = sum((v.get('costo') or 0) * v['cantidad'] for v in ventas)
    utilidad = total_ventas - total_costo

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total ventas", fmt_cop(total_ventas))
    with col2:
        st.metric("Unidades", int(total_unidades))
    with col3:
        st.metric("Utilidad bruta", fmt_cop(utilidad))
    with col4:
        dias = (fecha_fin - fecha_inicio).days + 1
        st.metric("Promedio/día", fmt_cop(total_ventas / dias if dias > 0 else 0))

    # Filtros adicionales
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        metodos = ['Todos'] + sorted(df['metodo_pago'].dropna().unique().tolist())
        filtro_metodo = st.selectbox("Método de pago", metodos, key="hv_metodo")
    with col_f2:
        vendedores = ['Todos'] + sorted(df['vendedor'].dropna().unique().tolist())
        filtro_vendedor = st.selectbox("Vendedor", vendedores, key="hv_vendedor")

    filtered = df.copy()
    if filtro_metodo != 'Todos':
        filtered = filtered[filtered['metodo_pago'] == filtro_metodo]
    if filtro_vendedor != 'Todos':
        filtered = filtered[filtered['vendedor'] == filtro_vendedor]

    # Tabla — formateada
    cols_show = ['fecha', 'hora', 'producto_nombre', 'cantidad', 'total', 'metodo_pago', 'vendedor', 'cliente']
    cols_exist = [c for c in cols_show if c in filtered.columns]
    display = filtered[cols_exist].copy()
    display = display.fillna('').replace('None', '')
    # Formatear montos y fechas
    if 'total' in display.columns:
        display['total'] = filtered['total'].apply(fmt_cop)
    if 'fecha' in display.columns:
        display['fecha'] = pd.to_datetime(filtered['fecha']).dt.strftime('%d %b')
    if 'hora' in display.columns:
        display['hora'] = display['hora'].astype(str).str[:5]
    if 'producto_nombre' in display.columns:
        display['producto_nombre'] = display['producto_nombre'].astype(str).str[:25]

    st.dataframe(
        display.rename(columns={
            'fecha': 'Fecha', 'hora': 'Hora',
            'producto_nombre': 'Producto', 'cantidad': 'Cant.',
            'total': 'Total',
            'metodo_pago': 'Método', 'vendedor': 'Vendedor', 'cliente': 'Cliente',
        }),
        use_container_width=True, hide_index=True,
    )

    # Gráfico Altair — ventas por día con colores ORVANN
    if len(filtered) > 1:
        st.markdown("#### Ventas por día")
        try:
            import altair as alt
            df_diario = filtered.groupby('fecha').agg({'total': 'sum'}).reset_index()
            df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])

            chart = alt.Chart(df_diario).mark_bar(
                color='#B8860B',
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
            ).encode(
                x=alt.X('fecha:T', title='', axis=alt.Axis(format='%d %b', labelAngle=-45)),
                y=alt.Y('total:Q', title='Ventas ($)', axis=alt.Axis(format=',.0f')),
                tooltip=[
                    alt.Tooltip('fecha:T', title='Fecha', format='%d %b %Y'),
                    alt.Tooltip('total:Q', title='Total', format='$,.0f'),
                ],
            ).configure_view(
                strokeWidth=0,
            ).configure(
                background='#FFFFFF',
                font='-apple-system, sans-serif',
            ).properties(
                height=250,
            )
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            # Fallback si altair no está instalado
            df_diario = filtered.groupby('fecha').agg({'total': 'sum'}).reset_index()
            df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
            df_diario = df_diario.set_index('fecha')
            st.bar_chart(df_diario['total'], use_container_width=True)

    # Exportar a Excel
    st.markdown("---")
    _exportar_excel(display, "ventas")


def render_historial_gastos():
    st.markdown("### Historial de Gastos")

    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Desde",
            value=date(2026, 1, 1),
            key="hg_inicio",
        )
    with col2:
        fecha_fin = st.date_input(
            "Hasta",
            value=date.today(),
            key="hg_fin",
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio debe ser anterior a la fecha fin")
        return

    gastos = get_gastos_rango(fecha_inicio.isoformat(), fecha_fin.isoformat())

    if not gastos:
        st.info("No hay gastos en el rango seleccionado")
        return

    df = pd.DataFrame(gastos)

    # Métricas del rango
    total_gastos = df['monto'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total gastos", fmt_cop(total_gastos))
    with col2:
        st.metric("Registros", len(df))
    with col3:
        dias = (fecha_fin - fecha_inicio).days + 1
        st.metric("Promedio/día", fmt_cop(total_gastos / dias if dias > 0 else 0))

    # Filtros adicionales
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        categorias = ['Todas'] + sorted(df['categoria'].dropna().unique().tolist())
        filtro_cat = st.selectbox("Categoría", categorias, key="hg_cat")
    with col_f2:
        pagadores = ['Todos'] + sorted(df['pagado_por'].dropna().unique().tolist())
        filtro_pagador = st.selectbox("Pagado por", pagadores, key="hg_pagador")

    filtered = df.copy()
    if filtro_cat != 'Todas':
        filtered = filtered[filtered['categoria'] == filtro_cat]
    if filtro_pagador != 'Todos':
        filtered = filtered[filtered['pagado_por'] == filtro_pagador]

    # Totales por socio
    st.markdown("#### Totales por socio")
    socios_totals = filtered.groupby('pagado_por')['monto'].sum().sort_values(ascending=False)
    if len(socios_totals) > 0:
        cols_socio = st.columns(min(len(socios_totals), 4))
        for i, (socio, total) in enumerate(socios_totals.items()):
            with cols_socio[i % len(cols_socio)]:
                st.metric(socio, fmt_cop(total))

    # Totales por categoría
    st.markdown("#### Totales por categoría")
    cat_totals = filtered.groupby('categoria')['monto'].sum().sort_values(ascending=False)
    for cat, total in cat_totals.items():
        st.text(f"  {cat}: {fmt_cop(total)}")

    # Tabla — formateada
    cols_show = ['fecha', 'categoria', 'monto', 'descripcion', 'pagado_por', 'metodo_pago']
    cols_exist = [c for c in cols_show if c in filtered.columns]
    display = filtered[cols_exist].copy()
    display = display.fillna('').replace('None', '')
    display['monto'] = filtered['monto'].apply(fmt_cop)
    if 'fecha' in display.columns:
        display['fecha'] = pd.to_datetime(filtered['fecha']).dt.strftime('%d %b')

    st.dataframe(
        display.rename(columns={
            'fecha': 'Fecha', 'categoria': 'Categoría', 'monto': 'Monto',
            'descripcion': 'Descripción', 'pagado_por': 'Pagado por',
            'metodo_pago': 'Método',
        }),
        use_container_width=True, hide_index=True,
    )

    # Exportar a Excel
    st.markdown("---")
    _exportar_excel(display, "gastos")


def _exportar_excel(df, nombre):
    """Botón para exportar DataFrame a Excel."""
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name=nombre.capitalize())
    buffer.seek(0)

    st.download_button(
        label=f"Descargar {nombre} (.xlsx)",
        data=buffer,
        file_name=f"orvann_{nombre}_{date.today().isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
