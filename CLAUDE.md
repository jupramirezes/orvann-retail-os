# ORVANN Retail OS — Documento Maestro

## Qué es

Sistema POS y control operativo para ORVANN, tienda de streetwear premium en Medellín. Reemplaza el Excel "Control_Operativo_Orvann.xlsx" con una aplicación web Streamlit + SQLite.

**Socios:** JP, KATHE, ANDRES (33% cada uno)
**Apertura:** 15 de febrero de 2026

## Arquitectura

```
Streamlit (frontend) → Python (lógica) → SQLite (datos)
```

- **Sin API REST** — Streamlit consulta SQLite directamente
- **Sin frameworks pesados** — solo Streamlit + openpyxl + pandas
- **Mobile-first** — diseñado para usar desde celular
- **Dark theme** — colores de marca ORVANN (dorado #c4a35a sobre negro #0a0a0a)

## Cómo correr

```bash
pip install -r requirements.txt
python scripts/migrate_excel.py   # Migrar datos desde Excel (solo primera vez)
streamlit run app/main.py         # Iniciar aplicación
```

## Tablas de BD (data/orvann.db)

### productos
| Campo | Tipo | Notas |
|-------|------|-------|
| sku | TEXT PK | Ej: CAM-OVS-NEG-S |
| nombre | TEXT | Camisa Oversize Peruana S Negro |
| categoria | TEXT | Camisa, Hoodie, Buzo, Chaqueta, Chompa, Jogger, Sudadera, Pantaloneta |
| talla | TEXT | S, M, L, XL, 2XL |
| color | TEXT | Negro, Blanco, Perla, Beige, etc. |
| costo | REAL | Precio de compra |
| precio_venta | REAL | Precio al público |
| stock | INTEGER | Unidades disponibles |
| stock_minimo | INTEGER | Default 3 — alerta si stock <= mínimo |

### ventas
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | Autoincrement |
| fecha | DATE | |
| hora | TIME | |
| sku | TEXT FK | → productos.sku |
| cantidad | INTEGER | Default 1 |
| precio_unitario | REAL | |
| descuento_pct | REAL | 0-100 |
| total | REAL | precio * cantidad * (1 - descuento/100) |
| metodo_pago | TEXT | Efectivo, Transferencia, Datáfono, Crédito |
| cliente | TEXT | Obligatorio si crédito |
| vendedor | TEXT | JP, KATHE, ANDRES |

### caja_diaria
| Campo | Tipo | Notas |
|-------|------|-------|
| fecha | DATE PK | |
| efectivo_inicio | REAL | |
| efectivo_cierre_real | REAL | Lo que hay al cerrar |
| cerrada | INTEGER | 0/1 |

### gastos
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| fecha | DATE | |
| categoria | TEXT | Arriendo, Servicios, etc. |
| monto | REAL | Monto REAL (no triplicado) |
| descripcion | TEXT | |
| pagado_por | TEXT | JP, KATHE, ANDRES, ORVANN |
| es_inversion | INTEGER | 1 si es gasto pre-apertura |

### creditos_clientes
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| venta_id | INTEGER FK | → ventas.id |
| cliente | TEXT | |
| monto | REAL | |
| fecha_credito | DATE | |
| fecha_pago | DATE | NULL si no pagado |
| pagado | INTEGER | 0/1 |

### pedidos_proveedores
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| fecha_pedido | DATE | |
| proveedor | TEXT | YOUR BRAND, BRACOR, AUREN |
| descripcion | TEXT | |
| unidades | INTEGER | |
| costo_unitario | REAL | |
| total | REAL | |
| estado | TEXT | Pendiente, Pagado |

### costos_fijos
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| concepto | TEXT | Arriendo, Servicios, Internet, etc. |
| monto_mensual | REAL | |
| activo | INTEGER | 1 = se cuenta para PE |

## Estado del Proyecto

### Hecho (v1.0)
- [x] BD SQLite con 7 tablas
- [x] Migración desde Excel (98 SKUs, 184 unidades, gastos deduplicados)
- [x] Vista "Vender" (POS con búsqueda, registro, ventas del día)
- [x] Vista "Dashboard" (punto de equilibrio, métricas, alertas)
- [x] Vista "Inventario" (filtros, resumen, agregar stock)
- [x] Vista "Admin" (gastos, liquidación socios, caja, créditos, pedidos)
- [x] Dark theme ORVANN
- [x] 13 tests pasando
- [x] MILE renombrado a ANDRES en toda la BD

### TODO Futuro
- [ ] Foto del producto al seleccionar SKU
- [ ] Gráficos de tendencia de ventas
- [ ] Notificación WhatsApp cuando stock < mínimo
- [ ] Generador de recibo (PDF/imagen para WhatsApp)
- [ ] Sync con Shopify
- [ ] PWA para instalar como app en celular
- [ ] Gestión de devoluciones
- [ ] Reportes exportables (Excel/PDF)

## Convenciones

- **Moneda:** COP (Pesos colombianos). Formateo: `$1.234.567` (punto como separador de miles)
- **Zona horaria:** Colombia (UTC-5) — usar `date.today()` del servidor
- **Socios:** JP, KATHE, ANDRES (33% cada uno)
- **Gastos ORVANN:** Cuando los 3 socios pagan parejo, pagado_por = 'ORVANN'
- **Vendedores:** JP, KATHE, ANDRES (mismo que socios por ahora)
- **Métodos de pago:** Efectivo, Transferencia, Datáfono, Crédito

## Estructura de Archivos

```
orvann-retail-os/
├── CLAUDE.md              # Este documento
├── README.md              # Descripción del proyecto
├── requirements.txt       # streamlit, openpyxl, pandas, pytest
├── data/
│   ├── orvann.db          # BD SQLite
│   └── Control_Operativo_Orvann.xlsx
├── scripts/
│   ├── create_db.py       # Crear tablas
│   └── migrate_excel.py   # Migrar datos desde Excel
├── app/
│   ├── main.py            # Entry point
│   ├── database.py        # Conexión y queries
│   ├── models.py          # Lógica de negocio
│   ├── pages/
│   │   ├── vender.py      # POS
│   │   ├── dashboard.py   # Métricas y PE
│   │   ├── inventario.py  # Stock
│   │   └── admin.py       # Gastos, socios, caja, créditos
│   └── components/
│       ├── styles.py      # CSS dark theme
│       └── helpers.py     # Formateo COP, utilidades
└── tests/
    ├── conftest.py        # Fixtures
    ├── test_database.py
    ├── test_models.py
    └── test_migration.py
```
