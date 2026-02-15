"""Pytest fixtures for ORVANN tests."""
import os
import sys
import tempfile
import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def db_path():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    from scripts.create_db import create_tables
    create_tables(path)
    yield path
    os.unlink(path)


@pytest.fixture
def db_with_data(db_path):
    """Database with sample product data for testing."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Insert sample products
    c.execute("""
        INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo)
        VALUES ('CAM-TEST-S', 'Camisa Test S Negro', 'Camisa', 'S', 'Negro', 37000, 75000, 10, 3)
    """)
    c.execute("""
        INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo)
        VALUES ('HOOD-TEST-L', 'Hoodie Test L Gris', 'Hoodie', 'L', 'Gris', 120000, 200000, 5, 3)
    """)
    c.execute("""
        INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo)
        VALUES ('LOW-STOCK', 'Camisa Low Stock', 'Camisa', 'M', 'Blanco', 37000, 75000, 2, 3)
    """)
    c.execute("""
        INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo)
        VALUES ('NO-STOCK', 'Camisa Sin Stock', 'Camisa', 'L', 'Negro', 37000, 75000, 0, 3)
    """)

    # Insert costos fijos
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Arriendo', 1210000, 1)")
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Servicios', 250000, 1)")
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Internet', 69000, 1)")
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Digitales', 153000, 1)")
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Seguros', 80000, 1)")
    c.execute("INSERT INTO costos_fijos (concepto, monto_mensual, activo) VALUES ('Imprevistos', 152900, 1)")

    conn.commit()
    conn.close()
    return db_path
