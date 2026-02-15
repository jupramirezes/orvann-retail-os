# ORVANN Retail OS — Documento Maestro (v1.2)

## Qué es

Sistema POS y control operativo para ORVANN, tienda de streetwear premium en Medellín. Reemplaza el Excel "Control_Operativo_Orvann.xlsx" con una aplicación web Streamlit.

**Socios:** JP, KATHE, ANDRES (33% cada uno)
**Apertura:** 15 de febrero de 2026

## Arquitectura

```
Streamlit (frontend) → Python (lógica) → SQLite / PostgreSQL (datos)
```

- **Sin API REST** — Streamlit consulta la BD directamente
- **Sin frameworks pesados** — solo Streamlit + openpyxl + pandas
- **Mobile-first** — diseñado para usar desde celular
- **Dark theme** — colores cálidos ORVANN (dorado #d4a843 sobre gris oscuro #161618)
- **Dual backend** — SQLite local para desarrollo, PostgreSQL para producción (Railway)

## Cómo correr

### Local (SQLite)
```bash
pip install -r requirements.txt
python scripts/migrate_excel.py   # Migrar datos desde Excel (solo primera vez)
streamlit run app/main.py         # Iniciar aplicación
```

### Producción (Railway + PostgreSQL)
```bash
# Railway auto-ejecuta:
python scripts/setup_railway.py && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
Variable de entorno requerida: `DATABASE_URL` (provista por Railway PostgreSQL add-on).

### Tests
```bash
python -m pytest tests/ -v        # 50 tests (siempre usan SQLite temporal)
```

## Backend de Datos (database.py)

La app detecta automáticamente el backend:
- Si `DATABASE_URL` env var existe y empieza con `postgres` → **PostgreSQL**
- Si no → **SQLite** (`data/orvann.db`)
- Tests siempre usan **SQLite temporal** (pasan `db_path` explícito)

Funciones clave:
- `adapt_sql(sql)` — convierte `?` → `%s` para PostgreSQL
- `execute(sql)` — auto-agrega `RETURNING id` en PostgreSQL INSERTs
- `_rows_to_dicts()` — normaliza resultados de ambos backends
- `execute_raw(sql)` — para DDL sin adaptar placeholders

## Tablas de BD

### productos
| Campo | Tipo | Notas |
|-------|------|-------|
| sku | TEXT PK | Ej: CAM-OVS-NEG-S |
| nombre | TEXT | Camisa Oversize Peruana S Negro |
| categoria | TEXT | Camisa, Hoodie, Buzo, Chaqueta, Chompa, Jogger, Sudadera, Pantaloneta |
| talla | TEXT | S, M, L, XL, 2XL |
| color | TEXT | Negro, Blanco, Perla, Beige, etc. |
| costo | REAL/NUMERIC | Precio de compra |
| precio_venta | REAL/NUMERIC | Precio al público |
| stock | INTEGER | Unidades disponibles |
| stock_minimo | INTEGER | Default 3 — alerta si stock <= mínimo |
| proveedor | TEXT | YOUR BRAND, BRACOR, AUREN, etc. |
| notas | TEXT | Opcional |

### ventas
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | Autoincrement/SERIAL |
| fecha | DATE | |
| hora | TIME/TEXT | |
| sku | TEXT FK | → productos.sku |
| cantidad | INTEGER | Default 1 |
| precio_unitario | REAL/NUMERIC | |
| descuento_pct | REAL/NUMERIC | 0-100 |
| total | REAL/NUMERIC | precio * cantidad * (1 - descuento/100) |
| metodo_pago | TEXT | Efectivo, Transferencia, Datáfono, Crédito |
| cliente | TEXT | Obligatorio si crédito |
| vendedor | TEXT | JP, KATHE, ANDRES |
| notas | TEXT | Notas opcionales de la venta |

### caja_diaria
| Campo | Tipo | Notas |
|-------|------|-------|
| fecha | DATE PK | |
| efectivo_inicio | REAL/NUMERIC | Monto al abrir caja |
| efectivo_cierre_real | REAL/NUMERIC | Lo que hay al cerrar |
| cerrada | INTEGER | 0/1 |
| notas | TEXT | Notas de cierre |

### gastos
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| fecha | DATE | |
| categoria | TEXT | Arriendo, Servicios, Mercancía, Transporte, etc. |
| monto | REAL/NUMERIC | Cada fila = pago real de un socio |
| descripcion | TEXT | |
| metodo_pago | TEXT | Efectivo, Transferencia, Datáfono |
| pagado_por | TEXT | JP, KATHE, ANDRES (siempre un socio específico) |
| es_inversion | INTEGER | 1 si es gasto pre-apertura |
| notas | TEXT | Opcional |

### creditos_clientes
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| venta_id | INTEGER FK | → ventas.id |
| cliente | TEXT | |
| monto | REAL/NUMERIC | |
| fecha_credito | DATE | |
| fecha_pago | DATE | NULL si no pagado |
| pagado | INTEGER | 0/1 |
| notas | TEXT | |

### pedidos_proveedores
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| fecha_pedido | DATE | |
| proveedor | TEXT | YOUR BRAND, BRACOR, AUREN |
| descripcion | TEXT | |
| unidades | INTEGER | |
| costo_unitario | REAL/NUMERIC | |
| total | REAL/NUMERIC | unidades * costo_unitario |
| estado | TEXT | Pendiente → Pagado → Completo |
| pagado_por | TEXT | Socio que pagó |
| fecha_entrega_est | DATE | Fecha estimada de entrega |
| notas | TEXT | |

### costos_fijos
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| concepto | TEXT | Arriendo, Servicios, Internet, etc. |
| monto_mensual | REAL/NUMERIC | |
| activo | INTEGER | 1 = se cuenta para PE |
| notas | TEXT | |

## Vistas de la App

### Vender (POS)
- Resumen del día en la parte superior (ventas, unidades, efectivo, en caja)
- Fecha visible en el encabezado
- Abrir caja con monto inicial (expander)
- Buscar producto por SKU, seleccionar cantidad y método de pago
- Opciones adicionales en expander: cliente, descuento %, notas
- Tabla de ventas del día con botón anular
- Gasto rápido sin ir a Admin
- Cerrar caja al final del día

### Dashboard
- Punto de equilibrio (progreso, meta diaria)
- Stats semanales + comparativa con semana anterior
- Gráfico de ventas diarias del mes
- Utilidad operativa mensual
- Alertas de stock bajo
- Deuda a proveedores

### Inventario
- Stock con filtros por categoría y búsqueda
- Resumen por categoría (valor costo, valor venta)
- Agregar stock a productos existentes

### Historial
- Ventas y gastos históricos con filtros por fecha/método/socio
- Exportar a Excel

### Admin (7 tabs)
1. **Gastos** — Lista con edición inline (✏️) y eliminación (🗑️). Modo parejo/personalizado/individual
2. **Liquidación** — Cuánto puso cada socio, cuánto le corresponde, saldos
3. **Caja** — Estado de caja actual, historial
4. **Créditos** — Créditos pendientes, marcar pagado
5. **Pedidos** — CRUD completo: registrar, pagar (crea gasto), recibir mercancía (agrega stock), eliminar
6. **Costos Fijos** — Agregar, editar, eliminar, activar/desactivar
7. **Productos** — Crear, editar (costo, precio, stock, mínimo), eliminar (protegido si tiene ventas)

## Funciones del Modelo (models.py)

### Ventas
- `registrar_venta()` — Descuenta stock, soporta descuento % y notas
- `anular_venta()` — Devuelve stock, elimina crédito
- `get_ventas_dia()`, `get_ventas_mes()`, `get_ventas_semana()`, `get_ventas_rango()`

### Caja
- `abrir_caja()` — Registra monto inicial, idempotente
- `cerrar_caja()` — Calcula diferencia esperado vs real
- `get_estado_caja()` — Incluye campo `caja_abierta`

### Gastos
- `registrar_gasto()` — Individual con pagado_por
- `registrar_gasto_parejo()` — Divide entre 3 socios
- `registrar_gasto_personalizado()` — Montos diferentes por socio
- `editar_gasto()` — Actualización parcial de campos
- `eliminar_gasto()`

### Productos
- `get_productos()`, `get_producto(sku)`
- `crear_producto()` — Todos los campos
- `editar_producto()` — Actualización parcial
- `eliminar_producto()` — Falla si tiene ventas asociadas

### Costos Fijos
- `get_costos_fijos()`
- `crear_costo_fijo()`, `editar_costo_fijo()`, `eliminar_costo_fijo()`

### Pedidos a Proveedores
- `get_pedidos()`, `get_pedidos_pendientes()`, `get_total_deuda_proveedores()`
- `registrar_pedido()` — Estado inicial: Pendiente
- `pagar_pedido()` — Pendiente → Pagado, crea gasto automático
- `recibir_mercancia()` — Pagado → Completo, agrega stock por SKU
- `editar_pedido()` — Recalcula total si cambian unidades/costo
- `eliminar_pedido()`

### Otros
- `calcular_punto_equilibrio()` — CF / margen ponderado
- `calcular_liquidacion_socios()` — Suma directa por socio
- `get_alertas_stock()` — Productos bajo mínimo

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

### Hecho (v1.1 — Correcciones)
- [x] **Gastos migrados correctamente** — cada fila = pago real, NO deduplicado
- [x] **Liquidación socios corregida** — suma directa por socio
- [x] **Anular venta** — devuelve stock + elimina crédito
- [x] **3 modos de gasto** — Parejo, Personalizado, Individual
- [x] **Vista Historial** — filtros + exportar Excel
- [x] **Tema cálido** + gasto rápido + dashboard mejorado
- [x] **Deploy prep** — Procfile, runtime.txt
- [x] 20 tests pasando

### Hecho (v1.2 — CRUD Completo + PostgreSQL)
- [x] **Navegación arreglada** — st.session_state persiste página activa
- [x] **Dual SQLite/PostgreSQL** — DATABASE_URL auto-detecta backend
- [x] **Railway deploy** — setup_railway.py con migración automática desde SQLite
- [x] **Vender mejorado** — resumen del día, abrir/cerrar caja, descuento + notas en expander
- [x] **Caja completa** — abrir con monto, gastos efectivo restados, cerrar con diferencia
- [x] **Pedidos CRUD** — registrar → pagar (crea gasto) → recibir (agrega stock)
- [x] **Edit/delete** — gastos, productos, costos fijos, pedidos (inline en Admin)
- [x] **Admin 7 tabs** — Gastos, Liquidación, Caja, Créditos, Pedidos, Costos Fijos, Productos
- [x] **50 tests pasando** (5 DB + 6 migración + 39 modelos)

### TODO Futuro
- [ ] Foto del producto al seleccionar SKU
- [ ] Notificación WhatsApp cuando stock < mínimo
- [ ] Generador de recibo (PDF/imagen para WhatsApp)
- [ ] Sync con Shopify
- [ ] PWA para instalar como app en celular
- [ ] Gestión de devoluciones
- [ ] Reportes PDF mensuales
- [ ] Backup automático de BD

## Convenciones

- **Moneda:** COP (Pesos colombianos). Formateo: `$1.234.567` (punto como separador de miles)
- **Zona horaria:** Colombia (UTC-5) — usar `date.today()` del servidor
- **Socios:** JP, KATHE, ANDRES (33% cada uno)
- **Gastos:** Cada fila tiene un `pagado_por` específico. NO existe "ORVANN" como pagador. Gasto parejo = 3 filas.
- **Vendedores:** JP, KATHE, ANDRES (mismo que socios)
- **Métodos de pago:** Efectivo, Transferencia, Datáfono, Crédito
- **Pedidos estados:** Pendiente → Pagado → Completo (flujo lineal)
- **Proveedores:** YOUR BRAND, BRACOR, AUREN, Otro

## Estructura de Archivos

```
orvann-retail-os/
├── CLAUDE.md              # Este documento
├── README.md              # Descripción del proyecto
├── Procfile               # Railway deploy
├── runtime.txt            # Python version for Railway
├── requirements.txt       # streamlit, openpyxl, pandas, psycopg2-binary, pytest
├── data/
│   ├── orvann.db          # BD SQLite (desarrollo local)
│   └── Control_Operativo_Orvann.xlsx
├── scripts/
│   ├── create_db.py       # Crear tablas (SQLite + PostgreSQL)
│   ├── migrate_excel.py   # Migrar datos desde Excel
│   └── setup_railway.py   # Setup Railway (tablas + seed desde SQLite)
├── app/
│   ├── main.py            # Entry point + navegación con session_state
│   ├── database.py        # Dual SQLite/PostgreSQL backend
│   ├── models.py          # Lógica de negocio (ventas, gastos, pedidos, caja, CRUD)
│   ├── pages/
│   │   ├── vender.py      # POS + caja + gasto rápido
│   │   ├── dashboard.py   # Métricas, PE, semanal, gráficos
│   │   ├── inventario.py  # Stock
│   │   ├── historial.py   # Ventas/gastos históricos + export Excel
│   │   └── admin.py       # 7 tabs: gastos, liquidación, caja, créditos, pedidos, costos fijos, productos
│   └── components/
│       ├── styles.py      # CSS tema cálido
│       └── helpers.py     # Formateo COP, constantes
└── tests/
    ├── conftest.py        # Fixtures (db_path, db_with_data)
    ├── test_database.py   # 5 tests
    ├── test_models.py     # 39 tests (caja, CRUD gastos/productos/costos/pedidos, descuentos)
    └── test_migration.py  # 6 tests
```
