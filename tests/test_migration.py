"""Tests para la migración desde Excel. v1.1"""
import os
import sys
import tempfile
import sqlite3
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'Control_Operativo_Orvann.xlsx')


@pytest.fixture
def migrated_db():
    """Crea una BD temporal y migra datos desde Excel."""
    if not os.path.exists(EXCEL_PATH):
        pytest.skip("Excel file not found")

    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    from scripts.migrate_excel import run_migration
    run_migration(excel_path=EXCEL_PATH, db_path=db_path)

    yield db_path
    os.unlink(db_path)


def test_migrar_productos(migrated_db):
    """98 SKUs, ~184 unidades."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    count = conn.execute("SELECT COUNT(*) as c FROM productos").fetchone()['c']
    assert count == 98

    total_stock = conn.execute("SELECT SUM(stock) as s FROM productos").fetchone()['s']
    assert total_stock == pytest.approx(184, abs=5)

    conn.close()


def test_migrar_gastos_todos_importados(migrated_db):
    """Cada fila del Excel = un pago real. No se deduplica nada."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    count = conn.execute("SELECT COUNT(*) as c FROM gastos").fetchone()['c']
    # Deben ser todas las filas con fecha y monto (55 aprox)
    assert count >= 40, f"Muy pocos gastos: {count} (esperado >= 40)"
    assert count <= 60, f"Demasiados gastos: {count} (esperado <= 60)"

    # No references to MILE
    mile_count = conn.execute("SELECT COUNT(*) as c FROM gastos WHERE pagado_por LIKE '%MILE%'").fetchone()['c']
    assert mile_count == 0, "Aún hay referencias a MILE en gastos"

    conn.close()


def test_gastos_totales_por_socio(migrated_db):
    """Totales por socio deben coincidir con Excel."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT pagado_por, SUM(monto) as total
        FROM gastos
        GROUP BY pagado_por
        ORDER BY pagado_por
    """).fetchall()

    totales = {r['pagado_por']: r['total'] for r in rows}

    # Totales conocidos del Excel
    assert totales.get('ANDRES', 0) == pytest.approx(5779090, rel=0.01), f"ANDRES: {totales.get('ANDRES')}"
    assert totales.get('JP', 0) == pytest.approx(5751890, rel=0.01), f"JP: {totales.get('JP')}"
    assert totales.get('KATHE', 0) == pytest.approx(5916090, rel=0.01), f"KATHE: {totales.get('KATHE')}"

    total_general = sum(totales.values())
    assert total_general == pytest.approx(17447070, rel=0.01), f"Total: {total_general}"

    conn.close()


def test_migrar_ventas(migrated_db):
    """2 ventas + 1 crédito."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    ventas_count = conn.execute("SELECT COUNT(*) as c FROM ventas").fetchone()['c']
    assert ventas_count == 2

    creditos_count = conn.execute("SELECT COUNT(*) as c FROM creditos_clientes").fetchone()['c']
    assert creditos_count == 1

    # El crédito debe ser de Claudia Ramírez
    cred = conn.execute("SELECT * FROM creditos_clientes").fetchone()
    assert 'Claudia' in cred['cliente']
    assert cred['monto'] == pytest.approx(200000)
    assert cred['pagado'] == 0

    conn.close()


def test_migrar_costos_fijos(migrated_db):
    """6 rubros, total ~$1.9M."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    count = conn.execute("SELECT COUNT(*) as c FROM costos_fijos").fetchone()['c']
    assert count == 6

    total = conn.execute("SELECT SUM(monto_mensual) as s FROM costos_fijos").fetchone()['s']
    assert total == pytest.approx(1914900, rel=0.01)

    conn.close()


def test_migrar_pedidos_fechas_corregidas(migrated_db):
    """Los pedidos con fecha 2025-02-XX deben haberse corregido a 2026-02-XX."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    # No debe haber pedidos con año 2025
    old_dates = conn.execute(
        "SELECT COUNT(*) as c FROM pedidos_proveedores WHERE fecha_pedido LIKE '2025-%'"
    ).fetchone()['c']
    assert old_dates == 0, f"Aún hay {old_dates} pedidos con fecha 2025"

    # Debe haber pedidos
    count = conn.execute("SELECT COUNT(*) as c FROM pedidos_proveedores").fetchone()['c']
    assert count >= 10

    conn.close()
