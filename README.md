# ORVANN Retail OS v1.6

Sistema POS y control operativo para ORVANN — streetwear premium en Medellín.

Streamlit + SQLite/PostgreSQL + Python puro. Mobile-first, tema claro Apple-style.

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

67 tests: base de datos (5), migración (6), modelos (56).

## Vistas

| Vista | Descripción |
|-------|-------------|
| **Vender** | POS — abrir caja, vender con descuento/notas, anular, gasto rápido, cerrar caja |
| **Dashboard** | Punto de equilibrio, semanal, utilidad operativa, alertas |
| **Inventario** | Stock con filtros, resumen por categoría, agregar stock |
| **Historial** | Ventas y gastos históricos, filtros, gráficos Altair, exportar Excel |
| **Admin** | 6 tabs: Gastos CRUD, Socios (liquidación), Pedidos, Caja/Créditos, Config (costos fijos + productos), Auditoría |

## Hardening (v1.5 / v1.6)

- CHECK constraints en las 7 tablas (SQLite y PostgreSQL)
- Tablas HTML puras (`render_table()`) — bypass Glide DataGrid canvas
- `html.escape()` en todas las celdas para prevenir XSS
- Undo: reabrir caja, editar venta, confirmar anulación
- Tema claro forzado via `.streamlit/config.toml`
- Multipage auto-nav oculta (navegación manual con `session_state`)
- ORVANN.png como favicon

## Stack

- Python 3.11+
- Streamlit 1.41
- SQLite (desarrollo) / PostgreSQL (producción)
- psycopg2-binary (PostgreSQL)
- openpyxl (migración Excel)
- pandas + Altair (tablas y gráficos)

## Deploy (Railway)

Incluye `Procfile`, `runtime.txt` y `scripts/setup_railway.py`.

Requiere variable de entorno `DATABASE_URL` (PostgreSQL).

```bash
web: python scripts/setup_railway.py && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
