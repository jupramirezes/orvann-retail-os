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
- 55 gastos reales (cada fila = pago real de un socio)
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

20 tests: base de datos (5), migración (6), modelos (9).

## Vistas

| Vista | Descripción |
|-------|-------------|
| **Vender** | POS — buscar producto, registrar venta, anular, gasto rápido |
| **Dashboard** | Punto de equilibrio, semanal, gráficos, utilidad operativa, alertas |
| **Inventario** | Stock con filtros, resumen por categoría, agregar stock |
| **Historial** | Ventas y gastos históricos, filtros por fecha/método/socio, exportar Excel |
| **Admin** | Gastos (parejo/personalizado/individual), liquidación socios, caja, créditos, pedidos |

## Stack

- Python 3.11+
- Streamlit 1.41
- SQLite
- openpyxl (migración Excel)
- pandas (tablas y gráficos)

## Deploy

Incluye `Procfile` y `runtime.txt` para Railway.

```bash
web: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
