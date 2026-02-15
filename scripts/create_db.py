"""Crea las 7 tablas de ORVANN Retail OS. Dual SQLite/PostgreSQL. v1.4"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')

# ── DDL SQLite ──────────────────────────────────────────

SQLITE_TABLES = [
    """CREATE TABLE IF NOT EXISTS productos (
        sku TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        categoria TEXT,
        talla TEXT,
        color TEXT,
        costo REAL NOT NULL,
        precio_venta REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 3,
        proveedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL DEFAULT (date('now')),
        hora TIME DEFAULT (time('now')),
        sku TEXT NOT NULL REFERENCES productos(sku),
        cantidad INTEGER DEFAULT 1,
        precio_unitario REAL NOT NULL,
        descuento_pct REAL DEFAULT 0,
        total REAL NOT NULL,
        metodo_pago TEXT NOT NULL,
        cliente TEXT,
        vendedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS caja_diaria (
        fecha DATE PRIMARY KEY,
        efectivo_inicio REAL DEFAULT 0,
        efectivo_cierre_real REAL,
        cerrada INTEGER DEFAULT 0,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL,
        categoria TEXT NOT NULL,
        monto REAL NOT NULL,
        descripcion TEXT,
        metodo_pago TEXT,
        pagado_por TEXT NOT NULL,
        es_inversion INTEGER DEFAULT 0,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS creditos_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER REFERENCES ventas(id),
        cliente TEXT NOT NULL,
        monto REAL NOT NULL,
        monto_pagado REAL DEFAULT 0,
        fecha_credito DATE NOT NULL,
        fecha_pago DATE,
        pagado INTEGER DEFAULT 0,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS pedidos_proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_pedido DATE NOT NULL,
        proveedor TEXT NOT NULL,
        descripcion TEXT,
        unidades INTEGER,
        costo_unitario REAL,
        total REAL,
        estado TEXT DEFAULT 'Pendiente',
        pagado_por TEXT,
        fecha_entrega_est DATE,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS costos_fijos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        monto_mensual REAL NOT NULL,
        activo INTEGER DEFAULT 1,
        notas TEXT
    )""",
]

# ── DDL PostgreSQL ──────────────────────────────────────

POSTGRES_TABLES = [
    """CREATE TABLE IF NOT EXISTS productos (
        sku TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        categoria TEXT,
        talla TEXT,
        color TEXT,
        costo NUMERIC NOT NULL,
        precio_venta NUMERIC NOT NULL,
        stock INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 3,
        proveedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS ventas (
        id SERIAL PRIMARY KEY,
        fecha DATE NOT NULL DEFAULT CURRENT_DATE,
        hora TIME DEFAULT CURRENT_TIME,
        sku TEXT NOT NULL REFERENCES productos(sku),
        cantidad INTEGER DEFAULT 1,
        precio_unitario NUMERIC NOT NULL,
        descuento_pct NUMERIC DEFAULT 0,
        total NUMERIC NOT NULL,
        metodo_pago TEXT NOT NULL,
        cliente TEXT,
        vendedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS caja_diaria (
        fecha DATE PRIMARY KEY,
        efectivo_inicio NUMERIC DEFAULT 0,
        efectivo_cierre_real NUMERIC,
        cerrada INTEGER DEFAULT 0,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        fecha DATE NOT NULL,
        categoria TEXT NOT NULL,
        monto NUMERIC NOT NULL,
        descripcion TEXT,
        metodo_pago TEXT,
        pagado_por TEXT NOT NULL,
        es_inversion INTEGER DEFAULT 0,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS creditos_clientes (
        id SERIAL PRIMARY KEY,
        venta_id INTEGER REFERENCES ventas(id),
        cliente TEXT NOT NULL,
        monto NUMERIC NOT NULL,
        monto_pagado NUMERIC DEFAULT 0,
        fecha_credito DATE NOT NULL,
        fecha_pago DATE,
        pagado INTEGER DEFAULT 0,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS pedidos_proveedores (
        id SERIAL PRIMARY KEY,
        fecha_pedido DATE NOT NULL,
        proveedor TEXT NOT NULL,
        descripcion TEXT,
        unidades INTEGER,
        costo_unitario NUMERIC,
        total NUMERIC,
        estado TEXT DEFAULT 'Pendiente',
        pagado_por TEXT,
        fecha_entrega_est DATE,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS costos_fijos (
        id SERIAL PRIMARY KEY,
        concepto TEXT NOT NULL,
        monto_mensual NUMERIC NOT NULL,
        activo INTEGER DEFAULT 1,
        notas TEXT
    )""",
]


def create_tables(db_path=None):
    """Crea tablas en SQLite. Usado para dev local y tests."""
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for ddl in SQLITE_TABLES:
        c.execute(ddl)
    conn.commit()
    conn.close()
    print(f"SQLite DB creada en: {os.path.abspath(db_path)}")
    return db_path


def create_tables_postgres(database_url=None):
    """Crea tablas en PostgreSQL. Usado en Railway production."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    c = conn.cursor()
    for ddl in POSTGRES_TABLES:
        c.execute(ddl)
    conn.commit()
    conn.close()
    print("PostgreSQL tables created successfully")


def migrate_v13(db_path=None):
    """Agrega columna monto_pagado a creditos_clientes si no existe. v1.3"""
    if db_path is None:
        db_path = DB_PATH
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(creditos_clientes)").fetchall()]
        if 'monto_pagado' not in cols:
            conn.execute("ALTER TABLE creditos_clientes ADD COLUMN monto_pagado REAL DEFAULT 0")
            conn.commit()
            print("Migration v1.3: added monto_pagado column")
    finally:
        conn.close()


def migrate_v14(db_path=None):
    """Fix vendedor NULL en ventas migradas desde Excel. v1.4"""
    if db_path is None:
        db_path = DB_PATH
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    try:
        updated = conn.execute(
            "UPDATE ventas SET vendedor = 'JP' WHERE vendedor IS NULL OR vendedor = ''"
        ).rowcount
        if updated > 0:
            conn.commit()
            print(f"Migration v1.4: fixed {updated} ventas with NULL vendedor → JP")
    finally:
        conn.close()


def ensure_tables():
    """Crea tablas en el backend activo. Idempotente (IF NOT EXISTS)."""
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres'):
        create_tables_postgres(database_url)
    else:
        create_tables()
        migrate_v13()
        migrate_v14()


if __name__ == '__main__':
    ensure_tables()
