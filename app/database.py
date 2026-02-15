"""Conexión a SQLite y queries base para ORVANN Retail OS."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')


def get_connection(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql, params=(), db_path=None):
    """Ejecuta un SELECT y retorna lista de dicts."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute(sql, params=(), db_path=None):
    """Ejecuta INSERT/UPDATE/DELETE y retorna lastrowid."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def execute_many(sql, params_list, db_path=None):
    """Ejecuta múltiples INSERT/UPDATE/DELETE."""
    conn = get_connection(db_path)
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()


def get_tables(db_path=None):
    """Lista todas las tablas en la BD."""
    return [r['name'] for r in query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        db_path=db_path
    )]
