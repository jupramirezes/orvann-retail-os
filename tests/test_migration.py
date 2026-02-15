"""Tests para la migración desde Excel."""
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


def test_migrar_gastos_sin_triplicar(migrated_db):
    """Gastos reales deben ser significativamente menos que las filas crudas del Excel."""
    conn = sqlite3.connect(migrated_db)
    conn.row_factory = sqlite3.Row

    count = conn.execute("SELECT COUNT(*) as c FROM gastos").fetchone()['c']
    # Originally 55 raw rows, should be around 25 after deduplication
    assert count < 55, f"Gastos no se deduplicaron: {count} (esperado < 55)"
    assert count >= 15, f"Muy pocos gastos: {count} (esperado >= 15)"

    # No references to MILE
    mile_count = conn.execute("SELECT COUNT(*) as c FROM gastos WHERE pagado_por LIKE '%MILE%'").fetchone()['c']
    assert mile_count == 0, "Aún hay referencias a MILE en gastos"

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
