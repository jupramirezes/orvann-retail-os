"""Tests para la lógica de negocio ORVANN."""
import sqlite3
import pytest
from datetime import date

from app.models import (
    calcular_punto_equilibrio,
    calcular_liquidacion_socios,
    get_estado_caja,
    get_alertas_stock,
    registrar_venta,
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
    """Gastos repartidos correctamente entre socios."""
    db = db_with_data

    # Insert some gastos
    conn = sqlite3.connect(db)
    c = conn.cursor()
    # Gasto compartido (ORVANN = los 3 pagaron parejo)
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-01', 'Arriendo', 300000, 'Arriendo Feb', 'ORVANN')""")
    # Gasto individual de JP
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-05', 'Transporte', 50000, 'Taxi mercancía', 'JP')""")
    # Gasto individual de KATHE
    c.execute("""INSERT INTO gastos (fecha, categoria, monto, descripcion, pagado_por)
                 VALUES ('2026-02-06', 'Aseo/Mantenimiento', 30000, 'Implementos', 'KATHE')""")
    conn.commit()
    conn.close()

    liq = calcular_liquidacion_socios(db_path=db)

    # Total real = 300000 (ORVANN) + 50000 (JP) + 30000 (KATHE) = 380000
    assert liq['total_real'] == pytest.approx(380000, rel=0.01)

    # Parte por socio = 380000 / 3 ≈ 126666.67
    assert liq['parte_cada_uno'] == pytest.approx(380000 / 3, rel=0.01)

    # JP aportó 300000 (su parte del ORVANN) + 50000 = 350000
    assert liq['aportes']['JP'] == pytest.approx(350000, rel=0.01)

    # KATHE aportó 300000 + 30000 = 330000
    assert liq['aportes']['KATHE'] == pytest.approx(330000, rel=0.01)

    # ANDRES aportó 300000 (solo su parte del ORVANN)
    assert liq['aportes']['ANDRES'] == pytest.approx(300000, rel=0.01)


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
