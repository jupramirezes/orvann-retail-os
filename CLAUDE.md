# ORVANN Retail OS — Documento Maestro (v1.1)

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
- **Dark theme** — colores cálidos ORVANN (dorado #d4a843 sobre gris oscuro #161618)

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
| monto | REAL | Cada fila = pago real de un socio |
| descripcion | TEXT | |
| pagado_por | TEXT | JP, KATHE, ANDRES (siempre un socio específico) |
| es_inversion | INTEGER | 1 si es gasto pre-apertura (antes 2026-02-15) |

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
- [x] Migración desde Excel (98 SKUs, 184 unidades)
- [x] Vista "Vender" (POS con búsqueda, registro, ventas del día)
- [x] Vista "Dashboard" (punto de equilibrio, métricas, alertas)
- [x] Vista "Inventario" (filtros, resumen, agregar stock)
- [x] Vista "Admin" (gastos, liquidación socios, caja, créditos, pedidos)
- [x] Dark theme ORVANN
- [x] 13 tests pasando
- [x] MILE renombrado a ANDRES en toda la BD

### Hecho (v1.1 — Correcciones y nuevas funcionalidades)
- [x] **CRÍTICO: Gastos migrados correctamente** — cada fila del Excel = pago real de un socio. NO se deduplica. Totales: JP=$5,751,890, KATHE=$5,916,090, ANDRES=$5,779,090, TOTAL=$17,447,070
- [x] **Liquidación socios corregida** — suma directa por socio, no hay concepto "ORVANN" pooled. Incluye detalle por socio/categoría y cronológico
- [x] **Venta flow arreglado** — registro directo sin segundo botón de confirmación
- [x] **Anular venta** — devuelve stock, elimina crédito asociado
- [x] **Pedidos: fechas 2025-02-XX corregidas a 2026-02-XX**
- [x] **Entrada de gastos mejorada** — 3 modos: Parejo (divide entre 3), Personalizado (montos diferentes), Solo uno
- [x] **Vista Historial** — ventas y gastos históricos con filtros, gráficos, exportar a Excel
- [x] **Tema cálido** — #161618 warm dark + colores más visibles + iconos en nav
- [x] **Gasto rápido desde Vender** — expander para registrar gasto sin ir a Admin
- [x] **Dashboard mejorado** — stats semanales, comparativa semana anterior, gráfico ventas diarias, utilidad operativa
- [x] **Deploy prep** — Procfile, runtime.txt, requirements pinned
- [x] **20 tests pasando** (5 DB + 6 migración + 9 modelos)

### TODO Futuro
- [ ] Deploy a Railway (necesita volume para SQLite persistente)
- [ ] Foto del producto al seleccionar SKU
- [ ] Notificación WhatsApp cuando stock < mínimo
- [ ] Generador de recibo (PDF/imagen para WhatsApp)
- [ ] Sync con Shopify
- [ ] PWA para instalar como app en celular
- [ ] Gestión de devoluciones

## Convenciones

- **Moneda:** COP (Pesos colombianos). Formateo: `$1.234.567` (punto como separador de miles)
- **Zona horaria:** Colombia (UTC-5) — usar `date.today()` del servidor
- **Socios:** JP, KATHE, ANDRES (33% cada uno)
- **Gastos:** Cada fila de gastos tiene un pagado_por específico (JP, KATHE o ANDRES). NO existe "ORVANN" como pagador. Si los 3 pagan parejo, se crean 3 filas.
- **Vendedores:** JP, KATHE, ANDRES (mismo que socios por ahora)
- **Métodos de pago:** Efectivo, Transferencia, Datáfono, Crédito

## Estructura de Archivos

```
orvann-retail-os/
├── CLAUDE.md              # Este documento
├── README.md              # Descripción del proyecto
├── Procfile               # Railway deploy
├── runtime.txt            # Python version for Railway
├── requirements.txt       # streamlit, openpyxl, pandas, pytest (pinned)
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
│   │   ├── vender.py      # POS + anular venta + gasto rápido
│   │   ├── dashboard.py   # Métricas, PE, semanal, gráficos
│   │   ├── inventario.py  # Stock
│   │   ├── historial.py   # Ventas/gastos históricos + export Excel
│   │   └── admin.py       # Gastos (3 modos), liquidación, caja, créditos, pedidos
│   └── components/
│       ├── styles.py      # CSS tema cálido
│       └── helpers.py     # Formateo COP, utilidades
└── tests/
    ├── conftest.py        # Fixtures
    ├── test_database.py   # 5 tests
    ├── test_models.py     # 9 tests (incluye anular, parejo, personalizado)
    └── test_migration.py  # 6 tests (incluye totales por socio, pedidos)
```
