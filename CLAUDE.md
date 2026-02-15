# ORVANN Retail OS — Documento Maestro (v1.3)

## Que es

Sistema interno de control operativo y registro de ventas para ORVANN, tienda de streetwear premium en Medellin. Reemplaza el Excel "Control_Operativo_Orvann.xlsx" con una aplicacion web Streamlit.

**NO es un POS comercial.** Es un sistema interno para 3 socios: JP, KATHE, ANDRES (33% cada uno).

**Objetivo:**
1. Registrar ventas y gastos rapido (reemplazar cuaderno)
2. Ver punto de equilibrio y proyecciones
3. Liquidacion entre socios (quien pago que)
4. Control de inventario

**Apertura:** 15 de febrero de 2026

## Arquitectura

```
Streamlit (frontend) → Python (logica) → SQLite / PostgreSQL (datos)
```

- **Sin API REST** — Streamlit consulta la BD directamente
- **Sin frameworks pesados** — solo Streamlit + openpyxl + pandas
- **Mobile-first** — disenado para usar desde celular
- **White theme Apple-style** — fondo blanco #F5F5F7, acento dorado #B8860B, SF Pro font
- **Dual backend** — SQLite local para desarrollo, PostgreSQL para produccion (Railway)

## Como correr

### Local (SQLite)
```bash
pip install -r requirements.txt
python scripts/migrate_excel.py   # Migrar datos desde Excel (solo primera vez)
streamlit run app/main.py         # Iniciar aplicacion
```

### Produccion (Railway + PostgreSQL)
```bash
# Railway auto-ejecuta:
python scripts/setup_railway.py && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```
Variable de entorno requerida: `DATABASE_URL` (provista por Railway PostgreSQL add-on).

### Tests
```bash
python -m pytest tests/ -v        # 55 tests (siempre usan SQLite temporal)
```

## Backend de Datos (database.py)

La app detecta automaticamente el backend:
- Si `DATABASE_URL` env var existe y empieza con `postgres` → **PostgreSQL**
- Si no → **SQLite** (`data/orvann.db`)
- Tests siempre usan **SQLite temporal** (pasan `db_path` explicito)

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
| precio_venta | REAL/NUMERIC | Precio al publico |
| stock | INTEGER | Unidades disponibles |
| stock_minimo | INTEGER | Default 3 — alerta si stock <= minimo |
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
| metodo_pago | TEXT | Efectivo, Transferencia, Datafono, Credito |
| cliente | TEXT | Obligatorio si credito |
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
| categoria | TEXT | Arriendo, Servicios, Mercancia, Transporte, etc. |
| monto | REAL/NUMERIC | Cada fila = pago real de un socio |
| descripcion | TEXT | |
| metodo_pago | TEXT | Efectivo, Transferencia, Datafono |
| pagado_por | TEXT | JP, KATHE, ANDRES (siempre un socio especifico) |
| es_inversion | INTEGER | 1 si es gasto pre-apertura |
| notas | TEXT | Opcional |

### creditos_clientes
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| venta_id | INTEGER FK | → ventas.id |
| cliente | TEXT | |
| monto | REAL/NUMERIC | Total del credito |
| monto_pagado | REAL/NUMERIC | Default 0 — acumula abonos parciales |
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
| pagado_por | TEXT | Socio que pago |
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

### Vender (POS) — mobile-first, minimo clicks
- 2 metricas: ventas hoy + efectivo en caja
- Abrir caja con monto inicial
- Buscar producto por nombre (solo muestra con stock > 0)
- Precio auto-llenado, cantidad, metodo pago, vendedor
- Campo cliente solo si metodo = Credito
- Boton muestra total: "REGISTRAR VENTA — $75,000"
- Tabla compacta: Hora | Producto | Total | M (1 letra) | Quien
- Anular venta (expander)
- Gasto rapido (expander)
- Cerrar caja (expander)

### Dashboard — metricas esenciales
- Punto de equilibrio (barra de progreso + meta diaria)
- Stats semanales (ventas, unidades, promedio/dia)
- Resultado mensual (ingresos, costo, gastos, utilidad operativa)
- Situacion actual (inventario costo/venta, deuda proveedores, creditos)
- Alertas stock (agotados + bajo) con nombres de producto

### Inventario
- Stock con filtros por categoria y busqueda
- Resumen por categoria (valor costo, valor venta)
- Agregar stock a productos existentes

### Historial
- Ventas y gastos historicos con filtros por fecha/metodo/socio
- Exportar a Excel

### Admin (5 tabs)
1. **Gastos** — Registrar (3 modos: parejo/personalizado/individual) + tabla del mes + editar/eliminar
2. **Socios** — Liquidacion: quien pago que, cuanto le corresponde, saldos
3. **Pedidos** — CRUD + flujo: registrar → pagar (crea gasto) → recibir (agrega stock) → eliminar
4. **Caja** — Abrir/cerrar + metricas efectivo + creditos pendientes
5. **Config** — Sub-tabs: Costos fijos (CRUD) + Productos (CRUD con auto-SKU)

## Auto-SKU para Nuevos Productos

Al crear un producto en Config > Productos, el SKU se genera automaticamente:
```
{CAT3}-{COLOR3}-{TALLA}
```
Ejemplo: Camisa + Negro + S = `CAM-NEG-S`

Mapa de categorias: CAM, HOO, BUZ, CHQ, CHO, JOG, SUD, PAN, OTR.
El usuario puede editar el SKU antes de confirmar.

## Funciones del Modelo (models.py)

### Ventas
- `registrar_venta()` — Descuenta stock, soporta descuento % y notas
- `anular_venta()` — Devuelve stock, elimina credito
- `get_ventas_dia()`, `get_ventas_mes()`, `get_ventas_semana()`, `get_ventas_rango()`

### Caja
- `abrir_caja()` — Registra monto inicial, idempotente
- `cerrar_caja()` — Calcula diferencia esperado vs real
- `get_estado_caja()` — Incluye campo `caja_abierta`

### Gastos
- `registrar_gasto()` — Individual con pagado_por
- `registrar_gasto_parejo()` — Divide entre 3 socios
- `registrar_gasto_personalizado()` — Montos diferentes por socio
- `editar_gasto()` — Actualizacion parcial de campos
- `eliminar_gasto()`

### Productos
- `get_productos()`, `get_producto(sku)`
- `crear_producto()` — Todos los campos
- `editar_producto()` — Actualizacion parcial
- `eliminar_producto()` — Falla si tiene ventas asociadas

### Costos Fijos
- `get_costos_fijos()`
- `crear_costo_fijo()`, `editar_costo_fijo()`, `eliminar_costo_fijo()`

### Pedidos a Proveedores
- `get_pedidos()`, `get_pedidos_pendientes()`, `get_total_deuda_proveedores()`
- `registrar_pedido()` — Estado inicial: Pendiente
- `pagar_pedido()` — Pendiente → Pagado, crea gasto automatico
- `recibir_mercancia()` — Pagado → Completo, agrega stock por SKU
- `editar_pedido()` — Recalcula total si cambian unidades/costo
- `eliminar_pedido()`

### Creditos
- `get_creditos_pendientes()` — Creditos no pagados
- `registrar_pago_credito()` — Marca como pagado (monto_pagado = monto)
- `registrar_abono()` — Abono parcial, si cubre total marca como pagado

### Otros
- `calcular_punto_equilibrio()` — CF / margen ponderado
- `calcular_liquidacion_socios()` — Suma directa por socio
- `get_alertas_stock()` — Productos bajo minimo

## Estado del Proyecto

### Hecho (v1.0)
- [x] BD SQLite con 7 tablas
- [x] Migracion desde Excel (98 SKUs, 184 unidades)
- [x] Vista "Vender" (POS con busqueda, registro, ventas del dia)
- [x] Vista "Dashboard" (punto de equilibrio, metricas, alertas)
- [x] Vista "Inventario" (filtros, resumen, agregar stock)
- [x] Vista "Admin" (gastos, liquidacion socios, caja, creditos, pedidos)
- [x] Dark theme ORVANN
- [x] 13 tests pasando

### Hecho (v1.1 — Correcciones)
- [x] Gastos migrados correctamente — cada fila = pago real, NO deduplicado
- [x] Liquidacion socios corregida — suma directa por socio
- [x] Anular venta — devuelve stock + elimina credito
- [x] 3 modos de gasto — Parejo, Personalizado, Individual
- [x] Vista Historial — filtros + exportar Excel
- [x] Tema calido + gasto rapido + dashboard mejorado
- [x] Deploy prep — Procfile, runtime.txt
- [x] 20 tests pasando

### Hecho (v1.2 — CRUD Completo + PostgreSQL)
- [x] Navegacion arreglada — st.session_state persiste pagina activa
- [x] Dual SQLite/PostgreSQL — DATABASE_URL auto-detecta backend
- [x] Railway deploy — setup_railway.py con migracion automatica desde SQLite
- [x] Vender mejorado — resumen del dia, abrir/cerrar caja, descuento + notas en expander
- [x] Caja completa — abrir con monto, gastos efectivo restados, cerrar con diferencia
- [x] Pedidos CRUD — registrar → pagar (crea gasto) → recibir (agrega stock)
- [x] Edit/delete — gastos, productos, costos fijos, pedidos (inline en Admin)
- [x] Admin 7 tabs — Gastos, Liquidacion, Caja, Creditos, Pedidos, Costos Fijos, Productos
- [x] 50 tests pasando

### Hecho (v1.3 — Simplificacion + Theme Apple)
- [x] Theme Apple white — fondo blanco, cards con sombra, tipografia SF Pro
- [x] Vender simplificado — 2 metricas, busqueda por nombre, precio auto-fill, minimo clicks
- [x] Admin 5 tabs — Gastos | Socios | Pedidos | Caja | Config (fusiono creditos+caja, costos+productos)
- [x] Auto-SKU — genera SKU automatico CAT-COLOR-TALLA al crear producto
- [x] Dashboard simplificado — solo metricas utiles (PE, semanal, resultado, inventario, alertas)
- [x] Gastos tabla compacta — dataframe en lugar de lista inline, edit/delete via select+expander
- [x] Abono parcial de creditos — monto_pagado acumula abonos, marca pagado al cubrir total
- [x] Sync Excel → BD — scripts/sync_excel.py (gastos, costos fijos, precios) idempotente
- [x] 55 tests pasando

### TODO Futuro
- [ ] Foto del producto al seleccionar SKU
- [ ] Notificacion WhatsApp cuando stock < minimo
- [ ] PWA para instalar como app en celular
- [ ] Reportes PDF mensuales
- [ ] Backup automatico de BD

## Convenciones

- **Moneda:** COP (Pesos colombianos). Formateo: `$1.234.567` (punto como separador de miles)
- **Zona horaria:** Colombia (UTC-5) — usar `date.today()` del servidor
- **Socios:** JP, KATHE, ANDRES (33% cada uno)
- **Gastos:** Cada fila tiene un `pagado_por` especifico. NO existe "ORVANN" como pagador. Gasto parejo = 3 filas.
- **Vendedores:** JP, KATHE, ANDRES (mismo que socios)
- **Metodos de pago:** Efectivo, Transferencia, Datafono, Credito
- **Pedidos estados:** Pendiente → Pagado → Completo (flujo lineal)
- **Proveedores:** YOUR BRAND, BRACOR, AUREN, Otro
- **Excel usa "MILE"** que corresponde a "ANDRES" en la BD

## Estructura de Archivos

```
orvann-retail-os/
├── CLAUDE.md              # Este documento
├── README.md              # Descripcion del proyecto
├── Procfile               # Railway deploy
├── runtime.txt            # Python version for Railway
├── requirements.txt       # streamlit, openpyxl, pandas, psycopg2-binary, pytest
├── data/
│   ├── orvann.db          # BD SQLite (desarrollo local)
│   └── Control_Operativo_Orvann.xlsx
├── scripts/
│   ├── create_db.py       # Crear tablas (SQLite + PostgreSQL)
│   ├── migrate_excel.py   # Migrar datos desde Excel
│   ├── read_excel.py      # Comparar Excel vs BD (temporal/diagnostico)
│   ├── sync_excel.py      # Sync Excel → BD (gastos, costos, precios) idempotente
│   └── setup_railway.py   # Setup Railway (tablas + seed desde SQLite)
├── app/
│   ├── main.py            # Entry point + navegacion con session_state
│   ├── database.py        # Dual SQLite/PostgreSQL backend
│   ├── models.py          # Logica de negocio (ventas, gastos, pedidos, caja, CRUD)
│   ├── pages/
│   │   ├── vender.py      # POS simplificado — minimo clicks
│   │   ├── dashboard.py   # Metricas esenciales + PE + alertas
│   │   ├── inventario.py  # Stock
│   │   ├── historial.py   # Ventas/gastos historicos + export Excel
│   │   └── admin.py       # 5 tabs: Gastos, Socios, Pedidos, Caja, Config
│   └── components/
│       ├── styles.py      # CSS tema Apple white
│       └── helpers.py     # Formateo COP, constantes
└── tests/
    ├── conftest.py        # Fixtures (db_path, db_with_data)
    ├── test_database.py   # 5 tests
    ├── test_models.py     # 44 tests (caja, CRUD, descuentos, abonos)
    └── test_migration.py  # 6 tests
```
