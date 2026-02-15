"""Tests para la base de datos ORVANN."""
import sqlite3
import pytest

from scripts.create_db import create_tables
from app.database import query, execute, get_tables
from app.models import registrar_venta


def test_crear_tablas(db_path):
    """Las 7 tablas existen después de create_tables."""
    tables = get_tables(db_path)
    expected = ['productos', 'ventas', 'caja_diaria', 'gastos',
                'creditos_clientes', 'pedidos_proveedores', 'costos_fijos']
    for t in expected:
        assert t in tables, f"Tabla '{t}' no encontrada"
    assert len(tables) >= 7


def test_insertar_producto(db_path):
    """SKU se crea correctamente."""
    execute(
        """INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ('TEST-001', 'Camisa Test S Negro', 'Camisa', 'S', 'Negro', 37000, 75000, 5),
        db_path=db_path
    )
    result = query("SELECT * FROM productos WHERE sku = ?", ('TEST-001',), db_path=db_path)
    assert len(result) == 1
    assert result[0]['nombre'] == 'Camisa Test S Negro'
    assert result[0]['costo'] == 37000
    assert result[0]['precio_venta'] == 75000
    assert result[0]['stock'] == 5


def test_insertar_venta_descuenta_stock(db_with_data):
    """El stock baja al registrar una venta."""
    db = db_with_data
    # Stock inicial = 10
    before = query("SELECT stock FROM productos WHERE sku = 'CAM-TEST-S'", db_path=db)
    assert before[0]['stock'] == 10

    registrar_venta('CAM-TEST-S', 2, 75000, 'Efectivo', vendedor='JP', db_path=db)

    after = query("SELECT stock FROM productos WHERE sku = 'CAM-TEST-S'", db_path=db)
    assert after[0]['stock'] == 8


def test_venta_credito_crea_credito(db_with_data):
    """Método 'Crédito' genera registro en creditos_clientes."""
    db = db_with_data
    registrar_venta('HOOD-TEST-L', 1, 200000, 'Crédito', cliente='Juan Test', vendedor='KATHE', db_path=db)

    creditos = query("SELECT * FROM creditos_clientes WHERE cliente = 'Juan Test'", db_path=db)
    assert len(creditos) == 1
    assert creditos[0]['monto'] == 200000
    assert creditos[0]['pagado'] == 0


def test_no_vender_sin_stock(db_with_data):
    """Error si stock = 0."""
    db = db_with_data
    with pytest.raises(ValueError, match="Stock insuficiente"):
        registrar_venta('NO-STOCK', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)
