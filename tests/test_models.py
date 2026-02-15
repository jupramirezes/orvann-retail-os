"""Tests para la lógica de negocio ORVANN. v1.1"""
import sqlite3
import pytest
from datetime import date

from app.models import (
    calcular_punto_equilibrio,
    calcular_liquidacion_socios,
    get_estado_caja,
    get_alertas_stock,
    registrar_venta,
    anular_venta,
    registrar_gasto,
    registrar_gasto_parejo,
    registrar_gasto_personalizado,
)
from app.database import execute, query


def test_punto_equilibrio(db_with_data):
    """CF=~1.9M, margen promedio calculado dinámicamente."""
    db = db_with_data
    pe = calcular_punto_equilibrio(db_path=db)

    # Costos fijos deben ser 1,914,900
    assert pe['cf'] == pytest.approx(1914900, rel=0.01)

    # Margen promedio debe ser razonable (entre 40% y 60%)
    assert 0.4 <= pe['margen_prom'] <= 0.65

    # PE en pesos debe ser razonable
    assert pe['pe_pesos'] > 0
    assert pe['pe_unidades'] > 0
    assert pe['pe_diario'] > 0


def test_liquidacion_socios(db_with_data):
    """Gastos sumados directamente por socio."""
    db = db_with_data

    # Insert some gastos — cada fila es un pago real de un socio
    conn = sqlite3.connect(db)
    c = conn.cursor()
    # JP paga arriendo
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-01', 'Arriendo', 100000, 'Arriendo Feb', 'JP')""")
    # KATHE paga arriendo
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-01', 'Arriendo', 100000, 'Arriendo Feb', 'KATHE')""")
    # ANDRES paga arriendo
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-01', 'Arriendo', 100000, 'Arriendo Feb', 'ANDRES')""")
    # Gasto individual de JP
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-05', 'Transporte', 50000, 'Taxi mercancía', 'JP')""")
    # Gasto individual de KATHE
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-06', 'Aseo/Mantenimiento', 30000, 'Implementos', 'KATHE')""")
    conn.commit()
    conn.close()

    liq = calcular_liquidacion_socios(db_path=db)

    # Total real = 100k*3 + 50k + 30k = 380000
    assert liq['total_real'] == pytest.approx(380000, rel=0.01)

    # Parte por socio = 380000 / 3
    assert liq['parte_cada_uno'] == pytest.approx(380000 / 3, rel=0.01)

    # JP aportó 100000 + 50000 = 150000
    assert liq['aportes']['JP'] == pytest.approx(150000, rel=0.01)

    # KATHE aportó 100000 + 30000 = 130000
    assert liq['aportes']['KATHE'] == pytest.approx(130000, rel=0.01)

    # ANDRES aportó 100000
    assert liq['aportes']['ANDRES'] == pytest.approx(100000, rel=0.01)

    # Saldos: JP puso más de lo que le corresponde
    assert liq['saldos']['JP']['saldo'] > 0, "JP debería tener saldo a favor"
    assert liq['saldos']['ANDRES']['saldo'] < 0, "ANDRES debería deber"


def test_estado_caja(db_with_data):
    """Totales por método cuadran."""
    db = db_with_data

    # Register some sales for today
    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)
    registrar_venta('CAM-TEST-S', 1, 75000, 'Transferencia', vendedor='JP', db_path=db)
    registrar_venta('HOOD-TEST-L', 1, 200000, 'Datáfono', vendedor='KATHE', db_path=db)

    estado = get_estado_caja(db_path=db)

    assert estado['totales_ventas'].get('Efectivo', 0) == pytest.approx(75000)
    assert estado['totales_ventas'].get('Transferencia', 0) == pytest.approx(75000)
    assert estado['totales_ventas'].get('Datáfono', 0) == pytest.approx(200000)
    assert estado['ventas_efectivo'] == pytest.approx(75000)
    assert estado['efectivo_esperado'] == pytest.approx(75000)  # inicio=0 + 75000 - 0


def test_alertas_stock(db_with_data):
    """Detecta productos bajo mínimo."""
    db = db_with_data
    alertas = get_alertas_stock(db_path=db)

    # LOW-STOCK (stock=2, min=3) y NO-STOCK (stock=0, min=3) deben estar en alertas
    skus = [a['sku'] for a in alertas]
    assert 'LOW-STOCK' in skus
    assert 'NO-STOCK' in skus
    # CAM-TEST-S tiene stock=10, no debería estar
    assert 'CAM-TEST-S' not in skus


def test_anular_venta(db_with_data):
    """Anular venta devuelve stock y elimina crédito."""
    db = db_with_data

    # Stock inicial
    antes = query("SELECT stock FROM productos WHERE sku = 'CAM-TEST-S'", db_path=db)
    stock_antes = antes[0]['stock']

    # Registrar y anular
    venta_id = registrar_venta('CAM-TEST-S', 2, 75000, 'Efectivo', vendedor='JP', db_path=db)

    despues_venta = query("SELECT stock FROM productos WHERE sku = 'CAM-TEST-S'", db_path=db)
    assert despues_venta[0]['stock'] == stock_antes - 2

    anulada = anular_venta(venta_id, db_path=db)
    assert anulada['sku'] == 'CAM-TEST-S'
    assert anulada['cantidad'] == 2

    despues_anular = query("SELECT stock FROM productos WHERE sku = 'CAM-TEST-S'", db_path=db)
    assert despues_anular[0]['stock'] == stock_antes

    # La venta ya no existe
    ventas = query("SELECT * FROM ventas WHERE id = ?", (venta_id,), db_path=db)
    assert len(ventas) == 0


def test_anular_venta_credito(db_with_data):
    """Anular venta a crédito también elimina el crédito."""
    db = db_with_data
    venta_id = registrar_venta('HOOD-TEST-L', 1, 200000, 'Crédito', cliente='Test Client', vendedor='JP', db_path=db)

    creditos = query("SELECT * FROM creditos_clientes WHERE venta_id = ?", (venta_id,), db_path=db)
    assert len(creditos) == 1

    anular_venta(venta_id, db_path=db)

    creditos_after = query("SELECT * FROM creditos_clientes WHERE venta_id = ?", (venta_id,), db_path=db)
    assert len(creditos_after) == 0


def test_gasto_parejo(db_with_data):
    """Gasto parejo crea 3 registros divididos equitativamente."""
    db = db_with_data
    ids = registrar_gasto_parejo(
        fecha='2026-02-15',
        categoria='Arriendo',
        monto_total=300000,
        descripcion='Arriendo febrero',
        db_path=db,
    )
    assert len(ids) == 3

    gastos = query("SELECT * FROM gastos WHERE descripcion = 'Arriendo febrero'", db_path=db)
    assert len(gastos) == 3

    socios = [g['pagado_por'] for g in gastos]
    assert 'JP' in socios
    assert 'KATHE' in socios
    assert 'ANDRES' in socios

    total = sum(g['monto'] for g in gastos)
    assert total == pytest.approx(300000, abs=2)  # Rounding tolerance


def test_gasto_personalizado(db_with_data):
    """Gasto personalizado con montos diferentes, solo crea para montos > 0."""
    db = db_with_data
    montos = {'JP': 150000, 'KATHE': 100000, 'ANDRES': 0}
    ids = registrar_gasto_personalizado(
        fecha='2026-02-15',
        categoria='Mercancía',
        montos_por_socio=montos,
        descripcion='Compra test',
        db_path=db,
    )
    # Solo JP y KATHE (ANDRES=0)
    assert len(ids) == 2

    gastos = query("SELECT * FROM gastos WHERE descripcion = 'Compra test'", db_path=db)
    assert len(gastos) == 2

    socios = {g['pagado_por']: g['monto'] for g in gastos}
    assert socios['JP'] == 150000
    assert socios['KATHE'] == 100000
    assert 'ANDRES' not in socios


def test_gasto_individual(db_with_data):
    """Gasto individual registra un solo registro."""
    db = db_with_data
    gid = registrar_gasto(
        fecha='2026-02-15',
        categoria='Transporte',
        monto=50000,
        descripcion='Taxi único',
        pagado_por='JP',
        db_path=db,
    )
    assert gid is not None

    gastos = query("SELECT * FROM gastos WHERE descripcion = 'Taxi único'", db_path=db)
    assert len(gastos) == 1
    assert gastos[0]['pagado_por'] == 'JP'
    assert gastos[0]['monto'] == 50000
