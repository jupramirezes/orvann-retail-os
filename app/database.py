"""
Conexión dual SQLite / PostgreSQL para ORVANN Retail OS. v1.2

- Si DATABASE_URL está definida → PostgreSQL (Railway production)
- Si no → SQLite local (data/orvann.db)
- Tests siempre usan SQLite (pasan db_path explícito)
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Detectar si estamos usando PostgreSQL
USE_POSTGRES = DATABASE_URL.startswith('postgres')


def _get_pg_connection():
    """Conexión a PostgreSQL usando psycopg2."""
    import psycopg2
    import psycopg2.extras
    url = DATABASE_URL
    # Railway usa postgres:// pero psycopg2 necesita postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    return conn


def _get_sqlite_connection(db_path=None):
    """Conexión a SQLite."""
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection(db_path=None):
    """Retorna conexión al backend activo.

    Si db_path es explícito → SQLite (tests).
    Si DATABASE_URL → PostgreSQL.
    Si no → SQLite local.
    """
    if db_path is not None:
        return _get_sqlite_connection(db_path)
    if USE_POSTGRES:
        return _get_pg_connection()
    return _get_sqlite_connection()


def _is_sqlite(db_path=None):
    """True si la conexión actual es SQLite."""
    if db_path is not None:
        return True
    return not USE_POSTGRES


def _rows_to_dicts(cursor, is_sqlite_conn=True):
    """Convierte rows del cursor a lista de dicts."""
    if is_sqlite_conn:
        return [dict(r) for r in cursor.fetchall()]
    else:
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def adapt_sql(sql, db_path=None):
    """Adapta SQL de SQLite a PostgreSQL si es necesario.

    SQLite usa ? como placeholder, PostgreSQL usa %s.
    """
    if _is_sqlite(db_path):
        return sql
    return sql.replace('?', '%s')


def query(sql, params=(), db_path=None):
    """Ejecuta un SELECT y retorna lista de dicts."""
    conn = get_connection(db_path)
    is_sqlite = _is_sqlite(db_path)
    try:
        adapted = adapt_sql(sql, db_path)
        if is_sqlite:
            cursor = conn.execute(adapted, params)
            return _rows_to_dicts(cursor, True)
        else:
            cursor = conn.cursor()
            cursor.execute(adapted, params)
            return _rows_to_dicts(cursor, False)
    finally:
        conn.close()


def execute(sql, params=(), db_path=None):
    """Ejecuta INSERT/UPDATE/DELETE y retorna lastrowid."""
    conn = get_connection(db_path)
    is_sqlite = _is_sqlite(db_path)
    try:
        adapted = adapt_sql(sql, db_path)
        if is_sqlite:
            cursor = conn.execute(adapted, params)
            conn.commit()
            return cursor.lastrowid
        else:
            cursor = conn.cursor()
            # Para INSERT, agregar RETURNING id si no está presente
            if adapted.strip().upper().startswith('INSERT') and 'RETURNING' not in adapted.upper():
                adapted = adapted.rstrip().rstrip(';') + ' RETURNING id'
                cursor.execute(adapted, params)
                result = cursor.fetchone()
                conn.commit()
                return result[0] if result else None
            else:
                cursor.execute(adapted, params)
                conn.commit()
                if cursor.description:
                    result = cursor.fetchone()
                    return result[0] if result else None
                return cursor.rowcount
    finally:
        conn.close()


def execute_many(sql, params_list, db_path=None):
    """Ejecuta múltiples INSERT/UPDATE/DELETE."""
    conn = get_connection(db_path)
    is_sqlite = _is_sqlite(db_path)
    try:
        adapted = adapt_sql(sql, db_path)
        if is_sqlite:
            conn.executemany(adapted, params_list)
        else:
            cursor = conn.cursor()
            for params in params_list:
                cursor.execute(adapted, params)
        conn.commit()
    finally:
        conn.close()


def execute_raw(sql, params=(), db_path=None):
    """Ejecuta SQL sin adaptar placeholders (para DDL específico del backend)."""
    conn = get_connection(db_path)
    is_sqlite = _is_sqlite(db_path)
    try:
        if is_sqlite:
            conn.execute(sql, params)
        else:
            cursor = conn.cursor()
            cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def get_tables(db_path=None):
    """Lista todas las tablas en la BD."""
    if _is_sqlite(db_path):
        return [r['name'] for r in query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            db_path=db_path
        )]
    else:
        return [r['tablename'] for r in query(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )]
