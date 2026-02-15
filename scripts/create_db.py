"""Crea las 7 tablas de ORVANN Retail OS en SQLite."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')


def create_tables(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS productos (
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
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
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
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS caja_diaria (
        fecha DATE PRIMARY KEY,
        efectivo_inicio REAL DEFAULT 0,
        efectivo_cierre_real REAL,
        cerrada INTEGER DEFAULT 0,
        notas TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
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
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS creditos_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER REFERENCES ventas(id),
        cliente TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha_credito DATE NOT NULL,
        fecha_pago DATE,
        pagado INTEGER DEFAULT 0,
        notas TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos_proveedores (
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
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS costos_fijos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        monto_mensual REAL NOT NULL,
        activo INTEGER DEFAULT 1,
        notas TEXT
    )""")

    conn.commit()
    conn.close()
    print(f"Base de datos creada en: {os.path.abspath(db_path)}")
    return db_path


if __name__ == '__main__':
    create_tables()
