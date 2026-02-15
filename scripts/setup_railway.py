"""
Setup script para Railway deployment de ORVANN Retail OS. v1.5

Se ejecuta al iniciar en Railway (antes de streamlit).
1. Crea tablas si no existen (idempotente)
2. Ejecuta todas las migraciones (v1.3, v1.4, v1.5)
3. Verifica integridad post-migración
4. Si las tablas están vacías, migra datos desde SQLite local si existe
"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATABASE_URL = os.environ.get('DATABASE_URL', '')
LOCAL_DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')


def setup():
    """Setup completo para Railway."""
    if not DATABASE_URL.startswith('postgres'):
        print("No DATABASE_URL found, skipping Railway setup")
        return

    print("=" * 50)
    print("ORVANN Railway Setup")
    print("=" * 50)

    # 1. Crear tablas + migraciones + verificación
    from scripts.create_db import ensure_tables
    ensure_tables()
    print("[OK] Tablas creadas, migraciones aplicadas, verificación OK")

    # 2. Verificar si necesita migración inicial
    _maybe_seed_from_sqlite()


def _maybe_seed_from_sqlite():
    """Si PostgreSQL está vacío y existe SQLite local, migra datos."""
    import psycopg2

    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    pg = psycopg2.connect(url)
    pgc = pg.cursor()

    # Verificar si ya hay productos
    pgc.execute("SELECT COUNT(*) FROM productos")
    count = pgc.fetchone()[0]

    if count > 0:
        print(f"[OK] PostgreSQL ya tiene {count} productos, no se necesita migración")
        pg.close()
        return

    # Verificar si existe SQLite local
    if not os.path.exists(LOCAL_DB):
        print("[INFO] No se encontró SQLite local para migrar")
        pg.close()
        return

    print("[INFO] PostgreSQL vacío, migrando desde SQLite local...")

    sqlite_conn = sqlite3.connect(LOCAL_DB)
    sqlite_conn.row_factory = sqlite3.Row

    # Migrar cada tabla en orden (respetar FKs)
    tables_order = [
        'costos_fijos',
        'productos',
        'ventas',
        'caja_diaria',
        'gastos',
        'creditos_clientes',
        'pedidos_proveedores',
    ]

    for table in tables_order:
        rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: 0 registros (vacía)")
            continue

        columns = rows[0].keys()
        # Excluir 'id' para tablas con SERIAL (PostgreSQL auto-genera)
        if table != 'productos' and table != 'caja_diaria':
            cols_to_insert = [c for c in columns if c != 'id']
        else:
            cols_to_insert = list(columns)

        placeholders = ', '.join(['%s'] * len(cols_to_insert))
        col_names = ', '.join(cols_to_insert)
        insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

        count_inserted = 0
        for row in rows:
            values = tuple(row[c] for c in cols_to_insert)
            try:
                pgc.execute(insert_sql, values)
                count_inserted += 1
            except Exception as e:
                print(f"  [WARN] {table}: Error insertando fila: {e}")

        # Reset sequence para tablas con SERIAL
        if table not in ('productos', 'caja_diaria'):
            try:
                pgc.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM {table}")
            except Exception:
                pass

        pg.commit()
        print(f"  {table}: {count_inserted} registros migrados")

    sqlite_conn.close()
    pg.close()
    print("[OK] Migración desde SQLite completada")


if __name__ == '__main__':
    setup()
