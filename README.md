# ORVANN Retail OS

Sistema POS y control operativo para ORVANN — streetwear premium en Medellín.

Streamlit + SQLite/PostgreSQL + Python puro. Mobile-first, dark theme.

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

50 tests: base de datos (5), migración (6), modelos (39).

## Vistas

| Vista | Descripción |
|-------|-------------|
| **Vender** | POS — abrir caja, vender con descuento/notas, anular, gasto rápido, cerrar caja |
| **Dashboard** | Punto de equilibrio, semanal, gráficos, utilidad operativa, alertas |
| **Inventario** | Stock con filtros, resumen por categoría, agregar stock |
| **Historial** | Ventas y gastos históricos, filtros por fecha/método/socio, exportar Excel |
| **Admin** | 7 tabs: gastos CRUD, liquidación socios, caja, créditos, pedidos CRUD, costos fijos, productos |

## Stack

- Python 3.11+
- Streamlit 1.41
- SQLite (desarrollo) / PostgreSQL (producción)
- psycopg2-binary (PostgreSQL)
- openpyxl (migración Excel)
- pandas (tablas y gráficos)

## Deploy (Railway)

Incluye `Procfile`, `runtime.txt` y `scripts/setup_railway.py`.

Requiere variable de entorno `DATABASE_URL` (PostgreSQL).

```bash
web: python scripts/setup_railway.py && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
