# ORVANN Retail OS

Sistema POS y control operativo para ORVANN — streetwear premium en Medellín.

Streamlit + SQLite + Python puro. Mobile-first, dark theme.

## Instalación

```bash
pip install -r requirements.txt
```

## Migración de datos (solo primera vez)

```bash
python scripts/migrate_excel.py
```

Migra datos desde `data/Control_Operativo_Orvann.xlsx`:
- 98 productos (SKUs)
- 184 unidades en inventario
- 2 ventas iniciales
- 25 gastos reales (deduplicados)
- 6 costos fijos ($1.9M/mes)
- 11 pedidos a proveedores

## Ejecución

```bash
streamlit run app/main.py
```

## Tests

```bash
python -m pytest tests/ -v
```

## Vistas

| Vista | Descripción |
|-------|-------------|
| **Vender** | POS — buscar producto, registrar venta, ver ventas del día |
| **Dashboard** | Punto de equilibrio, métricas, alertas de stock |
| **Inventario** | Stock con filtros, resumen por categoría, agregar stock |
| **Admin** | Gastos, liquidación socios, cierre de caja, créditos, pedidos |

## Stack

- Python 3.11+
- Streamlit
- SQLite
- openpyxl (migración Excel)
- pandas (tablas)
