"""Crea las 7 tablas de ORVANN Retail OS. Dual SQLite/PostgreSQL. v1.5 — CHECK constraints."""
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
        costo REAL NOT NULL CHECK (costo >= 0),
        precio_venta REAL NOT NULL CHECK (precio_venta >= 0),
        stock INTEGER DEFAULT 0 CHECK (stock >= 0),
        stock_minimo INTEGER DEFAULT 3 CHECK (stock_minimo >= 0),
        proveedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL DEFAULT (date('now')),
        hora TIME DEFAULT (time('now')),
        sku TEXT NOT NULL REFERENCES productos(sku),
        cantidad INTEGER DEFAULT 1 CHECK (cantidad > 0),
        precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0),
        descuento_pct REAL DEFAULT 0 CHECK (descuento_pct >= 0 AND descuento_pct <= 100),
        total REAL NOT NULL CHECK (total >= 0),
        metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('Efectivo', 'Transferencia', 'Datáfono', 'Crédito')),
        cliente TEXT,
        vendedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS caja_diaria (
        fecha DATE PRIMARY KEY,
        efectivo_inicio REAL DEFAULT 0 CHECK (efectivo_inicio >= 0),
        efectivo_cierre_real REAL,
        cerrada INTEGER DEFAULT 0 CHECK (cerrada IN (0, 1)),
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL,
        categoria TEXT NOT NULL,
        monto REAL NOT NULL CHECK (monto > 0),
        descripcion TEXT,
        metodo_pago TEXT,
        pagado_por TEXT NOT NULL CHECK (pagado_por IN ('JP', 'KATHE', 'ANDRES')),
        es_inversion INTEGER DEFAULT 0 CHECK (es_inversion IN (0, 1)),
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS creditos_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER REFERENCES ventas(id),
        cliente TEXT NOT NULL,
        monto REAL NOT NULL CHECK (monto > 0),
        monto_pagado REAL DEFAULT 0 CHECK (monto_pagado >= 0),
        fecha_credito DATE NOT NULL,
        fecha_pago DATE,
        pagado INTEGER DEFAULT 0 CHECK (pagado IN (0, 1)),
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS pedidos_proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_pedido DATE NOT NULL,
        proveedor TEXT NOT NULL,
        descripcion TEXT,
        unidades INTEGER CHECK (unidades > 0),
        costo_unitario REAL CHECK (costo_unitario >= 0),
        total REAL CHECK (total >= 0),
        estado TEXT DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'Pagado', 'Completo')),
        pagado_por TEXT,
        fecha_entrega_est DATE,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS costos_fijos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        monto_mensual REAL NOT NULL CHECK (monto_mensual > 0),
        activo INTEGER DEFAULT 1 CHECK (activo IN (0, 1)),
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
        costo NUMERIC NOT NULL CHECK (costo >= 0),
        precio_venta NUMERIC NOT NULL CHECK (precio_venta >= 0),
        stock INTEGER DEFAULT 0 CHECK (stock >= 0),
        stock_minimo INTEGER DEFAULT 3 CHECK (stock_minimo >= 0),
        proveedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS ventas (
        id SERIAL PRIMARY KEY,
        fecha DATE NOT NULL DEFAULT CURRENT_DATE,
        hora TIME DEFAULT CURRENT_TIME,
        sku TEXT NOT NULL REFERENCES productos(sku),
        cantidad INTEGER DEFAULT 1 CHECK (cantidad > 0),
        precio_unitario NUMERIC NOT NULL CHECK (precio_unitario >= 0),
        descuento_pct NUMERIC DEFAULT 0 CHECK (descuento_pct >= 0 AND descuento_pct <= 100),
        total NUMERIC NOT NULL CHECK (total >= 0),
        metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('Efectivo', 'Transferencia', 'Datáfono', 'Crédito')),
        cliente TEXT,
        vendedor TEXT,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS caja_diaria (
        fecha DATE PRIMARY KEY,
        efectivo_inicio NUMERIC DEFAULT 0 CHECK (efectivo_inicio >= 0),
        efectivo_cierre_real NUMERIC,
        cerrada INTEGER DEFAULT 0 CHECK (cerrada IN (0, 1)),
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        fecha DATE NOT NULL,
        categoria TEXT NOT NULL,
        monto NUMERIC NOT NULL CHECK (monto > 0),
        descripcion TEXT,
        metodo_pago TEXT,
        pagado_por TEXT NOT NULL CHECK (pagado_por IN ('JP', 'KATHE', 'ANDRES')),
        es_inversion INTEGER DEFAULT 0 CHECK (es_inversion IN (0, 1)),
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS creditos_clientes (
        id SERIAL PRIMARY KEY,
        venta_id INTEGER REFERENCES ventas(id),
        cliente TEXT NOT NULL,
        monto NUMERIC NOT NULL CHECK (monto > 0),
        monto_pagado NUMERIC DEFAULT 0 CHECK (monto_pagado >= 0),
        fecha_credito DATE NOT NULL,
        fecha_pago DATE,
        pagado INTEGER DEFAULT 0 CHECK (pagado IN (0, 1)),
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS pedidos_proveedores (
        id SERIAL PRIMARY KEY,
        fecha_pedido DATE NOT NULL,
        proveedor TEXT NOT NULL,
        descripcion TEXT,
        unidades INTEGER CHECK (unidades > 0),
        costo_unitario NUMERIC CHECK (costo_unitario >= 0),
        total NUMERIC CHECK (total >= 0),
        estado TEXT DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'Pagado', 'Completo')),
        pagado_por TEXT,
        fecha_entrega_est DATE,
        notas TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS costos_fijos (
        id SERIAL PRIMARY KEY,
        concepto TEXT NOT NULL,
        monto_mensual NUMERIC NOT NULL CHECK (monto_mensual > 0),
        activo INTEGER DEFAULT 1 CHECK (activo IN (0, 1)),
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
    """Crea tablas en PostgreSQL con transacción única. Usado en Railway production."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    try:
        c = conn.cursor()
        for ddl in POSTGRES_TABLES:
            c.execute(ddl)
        conn.commit()
        print("PostgreSQL tables created successfully")
    except Exception as e:
        conn.rollback()
        print(f"ERROR creating PostgreSQL tables: {e}")
        raise
    finally:
        conn.close()


def migrate_v13_postgres(database_url=None):
    """Agrega columna monto_pagado a creditos_clientes si no existe. v1.3 — PostgreSQL."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'creditos_clientes' AND column_name = 'monto_pagado'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE creditos_clientes ADD COLUMN monto_pagado NUMERIC DEFAULT 0")
            conn.commit()
            print("Migration v1.3 (PG): added monto_pagado column")
        else:
            conn.rollback()
    except Exception as e:
        conn.rollback()
        print(f"Migration v1.3 (PG) error: {e}")
    finally:
        conn.close()


def migrate_v14_postgres(database_url=None):
    """Fix vendedor NULL en ventas migradas desde Excel. v1.4 — PostgreSQL."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE ventas SET vendedor = 'JP' WHERE vendedor IS NULL OR vendedor = ''")
        updated = cur.rowcount
        conn.commit()
        if updated > 0:
            print(f"Migration v1.4 (PG): fixed {updated} ventas with NULL vendedor → JP")
    except Exception as e:
        conn.rollback()
        print(f"Migration v1.4 (PG) error: {e}")
    finally:
        conn.close()


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


def migrate_v15_fix_orvann_pagador(db_path=None):
    """Fix gastos con pagado_por='ORVANN' → 'JP'. v1.5 — SQLite."""
    if db_path is None:
        db_path = DB_PATH
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    try:
        updated = conn.execute(
            "UPDATE gastos SET pagado_por = 'JP' WHERE pagado_por = 'ORVANN'"
        ).rowcount
        if updated > 0:
            conn.commit()
            print(f"Migration v1.5: fixed {updated} gastos with pagado_por 'ORVANN' → 'JP'")
    finally:
        conn.close()


def migrate_v15_fix_orvann_postgres(database_url=None):
    """Fix gastos con pagado_por='ORVANN' → 'JP'. v1.5 — PostgreSQL."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE gastos SET pagado_por = 'JP' WHERE pagado_por = 'ORVANN'")
        updated = cur.rowcount
        conn.commit()
        if updated > 0:
            print(f"Migration v1.5 (PG): fixed {updated} gastos with pagado_por 'ORVANN' → 'JP'")
    except Exception as e:
        conn.rollback()
        print(f"Migration v1.5 (PG) fix ORVANN error: {e}")
    finally:
        conn.close()


def migrate_v15_postgres(database_url=None):
    """Agrega CHECK constraints a tablas PostgreSQL existentes. v1.5
    Idempotente: usa IF NOT EXISTS (PG 12+) o ignora si ya existe."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    # Lista de (tabla, nombre_constraint, expresion CHECK)
    constraints = [
        # productos
        ('productos', 'chk_productos_costo', 'costo >= 0'),
        ('productos', 'chk_productos_precio', 'precio_venta >= 0'),
        ('productos', 'chk_productos_stock', 'stock >= 0'),
        ('productos', 'chk_productos_stock_min', 'stock_minimo >= 0'),
        # ventas
        ('ventas', 'chk_ventas_cantidad', 'cantidad > 0'),
        ('ventas', 'chk_ventas_precio', 'precio_unitario >= 0'),
        ('ventas', 'chk_ventas_descuento', 'descuento_pct >= 0 AND descuento_pct <= 100'),
        ('ventas', 'chk_ventas_total', 'total >= 0'),
        ('ventas', 'chk_ventas_metodo', "metodo_pago IN ('Efectivo', 'Transferencia', 'Datáfono', 'Crédito')"),
        # caja_diaria
        ('caja_diaria', 'chk_caja_inicio', 'efectivo_inicio >= 0'),
        ('caja_diaria', 'chk_caja_cerrada', 'cerrada IN (0, 1)'),
        # gastos
        ('gastos', 'chk_gastos_monto', 'monto > 0'),
        ('gastos', 'chk_gastos_pagador', "pagado_por IN ('JP', 'KATHE', 'ANDRES')"),
        ('gastos', 'chk_gastos_inversion', 'es_inversion IN (0, 1)'),
        # creditos
        ('creditos_clientes', 'chk_creditos_monto', 'monto > 0'),
        ('creditos_clientes', 'chk_creditos_pagado_monto', 'monto_pagado >= 0'),
        ('creditos_clientes', 'chk_creditos_pagado', 'pagado IN (0, 1)'),
        # pedidos
        ('pedidos_proveedores', 'chk_pedidos_unidades', 'unidades > 0'),
        ('pedidos_proveedores', 'chk_pedidos_costo', 'costo_unitario >= 0'),
        ('pedidos_proveedores', 'chk_pedidos_total', 'total >= 0'),
        ('pedidos_proveedores', 'chk_pedidos_estado', "estado IN ('Pendiente', 'Pagado', 'Completo')"),
        # costos_fijos
        ('costos_fijos', 'chk_cf_monto', 'monto_mensual > 0'),
        ('costos_fijos', 'chk_cf_activo', 'activo IN (0, 1)'),
    ]

    added = 0
    for tabla, nombre, expr in constraints:
        try:
            # Verificar si el constraint ya existe
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = %s AND constraint_name = %s
            """, (tabla, nombre))
            if cur.fetchone():
                continue  # Ya existe
            cur.execute(f'ALTER TABLE {tabla} ADD CONSTRAINT {nombre} CHECK ({expr})')
            added += 1
        except Exception as e:
            # Si falla (ej: datos existentes violan el constraint), reportar y continuar
            conn.rollback()
            print(f"  ⚠ Constraint {nombre} falló: {e}")
            continue

    conn.commit()
    conn.close()
    if added > 0:
        print(f"Migration v1.5: added {added} CHECK constraints to PostgreSQL")


EXPECTED_TABLES = {'productos', 'ventas', 'caja_diaria', 'gastos',
                    'creditos_clientes', 'pedidos_proveedores', 'costos_fijos'}


def verify_tables_postgres(database_url=None):
    """Verifica que todas las tablas existan en PostgreSQL. Post-migration check."""
    import psycopg2
    url = database_url or os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        existing = {row[0] for row in cur.fetchall()}
        missing = EXPECTED_TABLES - existing
        if missing:
            print(f"⚠ MISSING tables in PostgreSQL: {missing}")
            return False
        print(f"✅ PostgreSQL verification OK — {len(EXPECTED_TABLES)} tables present")
        return True
    finally:
        conn.close()


def verify_tables_sqlite(db_path=None):
    """Verifica que todas las tablas existan en SQLite. Post-migration check."""
    if db_path is None:
        db_path = DB_PATH
    if not os.path.exists(db_path):
        print("⚠ SQLite DB does not exist")
        return False
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        existing = {r[0] for r in rows}
        missing = EXPECTED_TABLES - existing
        if missing:
            print(f"⚠ MISSING tables in SQLite: {missing}")
            return False
        print(f"✅ SQLite verification OK — {len(EXPECTED_TABLES)} tables present")
        return True
    finally:
        conn.close()


def ensure_tables():
    """Crea tablas en el backend activo. Ejecuta migraciones. Verifica resultado.
    Idempotente (IF NOT EXISTS + column checks)."""
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres'):
        create_tables_postgres(database_url)
        migrate_v13_postgres(database_url)
        migrate_v14_postgres(database_url)
        migrate_v15_fix_orvann_postgres(database_url)  # Fix data BEFORE adding constraints
        migrate_v15_postgres(database_url)
        verify_tables_postgres(database_url)
    else:
        create_tables()
        migrate_v13()
        migrate_v14()
        migrate_v15_fix_orvann_pagador()  # Fix data (for SQLite re-migrations)
        verify_tables_sqlite()


if __name__ == '__main__':
    ensure_tables()
