"""Tests para la logica de negocio ORVANN. v1.5"""
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
    # v1.2 — Caja
    abrir_caja,
    cerrar_caja,
    # v1.2 — Gastos CRUD
    editar_gasto,
    eliminar_gasto,
    # v1.2 — Productos CRUD
    get_productos,
    get_producto,
    crear_producto,
    editar_producto,
    eliminar_producto,
    # v1.2 — Costos Fijos CRUD
    get_costos_fijos,
    crear_costo_fijo,
    editar_costo_fijo,
    eliminar_costo_fijo,
    # v1.2 — Pedidos CRUD
    get_pedidos,
    registrar_pedido,
    pagar_pedido,
    recibir_mercancia,
    editar_pedido,
    eliminar_pedido,
    get_pedidos_pendientes,
    get_total_deuda_proveedores,
    # Ventas helpers
    get_ventas_dia,
    # v1.3 — Creditos
    get_creditos_pendientes,
    registrar_abono,
    registrar_pago_credito,
    # v1.4 — Undo operations
    reabrir_caja,
    editar_venta,
)
from app.database import execute, query


# ── Tests originales v1.1 ─────────────────────────────────

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


# ── Tests v1.2 — Caja ─────────────────────────────────────

def test_abrir_caja(db_with_data):
    """Abrir caja registra efectivo inicio y marca caja como abierta."""
    db = db_with_data
    hoy = date.today().isoformat()
    result = abrir_caja(fecha=hoy, efectivo_inicio=200000, db_path=db)

    assert result['fecha'] == hoy
    assert result['efectivo_inicio'] == 200000

    estado = get_estado_caja(fecha=hoy, db_path=db)
    assert estado['caja_abierta'] is True
    assert estado['efectivo_inicio'] == 200000
    assert estado['cerrada'] == 0


def test_abrir_caja_actualiza_si_existe(db_with_data):
    """Si la caja ya fue abierta, abrir de nuevo actualiza el monto."""
    db = db_with_data
    hoy = date.today().isoformat()
    abrir_caja(fecha=hoy, efectivo_inicio=100000, db_path=db)
    abrir_caja(fecha=hoy, efectivo_inicio=250000, db_path=db)

    estado = get_estado_caja(fecha=hoy, db_path=db)
    assert estado['efectivo_inicio'] == 250000


def test_cerrar_caja(db_with_data):
    """Cerrar caja calcula diferencia correctamente."""
    db = db_with_data
    hoy = date.today().isoformat()
    abrir_caja(fecha=hoy, efectivo_inicio=100000, db_path=db)

    # Registrar venta en efectivo
    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)

    # Esperado = 100000 + 75000 = 175000
    result = cerrar_caja(fecha=hoy, efectivo_real=180000, db_path=db)

    assert result['efectivo_esperado'] == pytest.approx(175000)
    assert result['efectivo_real'] == 180000
    assert result['diferencia'] == pytest.approx(5000)

    estado = get_estado_caja(fecha=hoy, db_path=db)
    assert estado['cerrada'] == 1


def test_estado_caja_con_gastos_efectivo(db_with_data):
    """Gastos en efectivo reducen el efectivo esperado."""
    db = db_with_data
    hoy = date.today().isoformat()
    abrir_caja(fecha=hoy, efectivo_inicio=200000, db_path=db)

    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)
    registrar_gasto(
        fecha=hoy, categoria='Transporte', monto=30000,
        descripcion='Taxi', pagado_por='JP', metodo_pago='Efectivo', db_path=db,
    )

    estado = get_estado_caja(fecha=hoy, db_path=db)
    # Esperado = 200000 + 75000 - 30000 = 245000
    assert estado['efectivo_esperado'] == pytest.approx(245000)
    assert estado['gastos_efectivo'] == pytest.approx(30000)


# ── Tests v1.2 — Editar/Eliminar Gastos ────────────────────

def test_editar_gasto(db_with_data):
    """Editar gasto cambia solo los campos proporcionados."""
    db = db_with_data
    gid = registrar_gasto(
        fecha='2026-02-10', categoria='Transporte', monto=50000,
        descripcion='Original', pagado_por='JP', db_path=db,
    )

    editar_gasto(gid, monto=60000, descripcion='Editado', db_path=db)

    gastos = query("SELECT * FROM gastos WHERE id = ?", (gid,), db_path=db)
    assert len(gastos) == 1
    assert gastos[0]['monto'] == 60000
    assert gastos[0]['descripcion'] == 'Editado'
    # Campos no editados permanecen
    assert gastos[0]['pagado_por'] == 'JP'
    assert gastos[0]['categoria'] == 'Transporte'


def test_editar_gasto_sin_campos_no_cambia(db_with_data):
    """Editar sin proporcionar campos no hace nada."""
    db = db_with_data
    gid = registrar_gasto(
        fecha='2026-02-10', categoria='Transporte', monto=50000,
        descripcion='Sin cambios', pagado_por='JP', db_path=db,
    )

    editar_gasto(gid, db_path=db)  # Sin campos

    gastos = query("SELECT * FROM gastos WHERE id = ?", (gid,), db_path=db)
    assert gastos[0]['monto'] == 50000
    assert gastos[0]['descripcion'] == 'Sin cambios'


def test_eliminar_gasto(db_with_data):
    """Eliminar gasto lo borra de la BD."""
    db = db_with_data
    gid = registrar_gasto(
        fecha='2026-02-10', categoria='Transporte', monto=50000,
        descripcion='A borrar', pagado_por='JP', db_path=db,
    )

    gastos_antes = query("SELECT * FROM gastos WHERE id = ?", (gid,), db_path=db)
    assert len(gastos_antes) == 1

    eliminar_gasto(gid, db_path=db)

    gastos_despues = query("SELECT * FROM gastos WHERE id = ?", (gid,), db_path=db)
    assert len(gastos_despues) == 0


# ── Tests v1.2 — Productos CRUD ────────────────────────────

def test_crear_producto(db_path):
    """Crear un producto nuevo con todos los campos."""
    crear_producto(
        sku='NEW-CAM-M', nombre='Camisa Nueva M', categoria='Camisa',
        talla='M', color='Rojo', costo=40000, precio_venta=80000,
        stock=15, stock_minimo=5, proveedor='YOUR BRAND', db_path=db_path,
    )

    prod = get_producto('NEW-CAM-M', db_path=db_path)
    assert prod is not None
    assert prod['nombre'] == 'Camisa Nueva M'
    assert prod['costo'] == 40000
    assert prod['precio_venta'] == 80000
    assert prod['stock'] == 15
    assert prod['stock_minimo'] == 5


def test_editar_producto(db_with_data):
    """Editar producto cambia solo campos proporcionados."""
    db = db_with_data
    editar_producto('CAM-TEST-S', costo=45000, precio_venta=90000, db_path=db)

    prod = get_producto('CAM-TEST-S', db_path=db)
    assert prod['costo'] == 45000
    assert prod['precio_venta'] == 90000
    # Campos no editados permanecen
    assert prod['nombre'] == 'Camisa Test S Negro'
    assert prod['stock'] == 10


def test_editar_producto_stock(db_with_data):
    """Editar stock directamente (sin agregar_stock)."""
    db = db_with_data
    editar_producto('HOOD-TEST-L', stock=20, db_path=db)

    prod = get_producto('HOOD-TEST-L', db_path=db)
    assert prod['stock'] == 20


def test_eliminar_producto_sin_ventas(db_with_data):
    """Se puede eliminar un producto sin ventas."""
    db = db_with_data

    prod_antes = get_producto('NO-STOCK', db_path=db)
    assert prod_antes is not None

    eliminar_producto('NO-STOCK', db_path=db)

    prod_despues = get_producto('NO-STOCK', db_path=db)
    assert prod_despues is None


def test_eliminar_producto_con_ventas_falla(db_with_data):
    """No se puede eliminar un producto con ventas asociadas."""
    db = db_with_data

    # Registrar una venta
    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)

    # Intentar eliminar debe fallar
    with pytest.raises(ValueError, match="tiene .* ventas asociadas"):
        eliminar_producto('CAM-TEST-S', db_path=db)


def test_get_productos(db_with_data):
    """get_productos retorna todos los productos."""
    db = db_with_data
    prods = get_productos(db_path=db)
    assert len(prods) == 4  # 4 productos en fixture


# ── Tests v1.2 — Costos Fijos CRUD ─────────────────────────

def test_get_costos_fijos(db_with_data):
    """get_costos_fijos retorna los costos del fixture."""
    db = db_with_data
    costos = get_costos_fijos(db_path=db)
    assert len(costos) == 6  # 6 costos en fixture
    conceptos = [c['concepto'] for c in costos]
    assert 'Arriendo' in conceptos
    assert 'Servicios' in conceptos


def test_crear_costo_fijo(db_path):
    """Crear un nuevo costo fijo."""
    cid = crear_costo_fijo('Contador', 200000, db_path=db_path)
    assert cid is not None

    costos = get_costos_fijos(db_path=db_path)
    assert len(costos) == 1
    assert costos[0]['concepto'] == 'Contador'
    assert costos[0]['monto_mensual'] == 200000
    assert costos[0]['activo'] == 1


def test_editar_costo_fijo(db_with_data):
    """Editar costo fijo cambia campos proporcionados."""
    db = db_with_data
    costos = get_costos_fijos(db_path=db)
    arriendo = [c for c in costos if c['concepto'] == 'Arriendo'][0]

    editar_costo_fijo(arriendo['id'], monto_mensual=1300000, db_path=db)

    costos_despues = get_costos_fijos(db_path=db)
    arriendo_despues = [c for c in costos_despues if c['concepto'] == 'Arriendo'][0]
    assert arriendo_despues['monto_mensual'] == 1300000


def test_desactivar_costo_fijo(db_with_data):
    """Desactivar un costo fijo afecta el punto de equilibrio."""
    db = db_with_data
    pe_antes = calcular_punto_equilibrio(db_path=db)

    costos = get_costos_fijos(db_path=db)
    arriendo = [c for c in costos if c['concepto'] == 'Arriendo'][0]
    editar_costo_fijo(arriendo['id'], activo=0, db_path=db)

    pe_despues = calcular_punto_equilibrio(db_path=db)
    assert pe_despues['cf'] < pe_antes['cf']
    assert pe_despues['cf'] == pytest.approx(pe_antes['cf'] - 1210000, rel=0.01)


def test_eliminar_costo_fijo(db_with_data):
    """Eliminar costo fijo lo remueve de la BD."""
    db = db_with_data
    costos = get_costos_fijos(db_path=db)
    imprevistos = [c for c in costos if c['concepto'] == 'Imprevistos'][0]

    eliminar_costo_fijo(imprevistos['id'], db_path=db)

    costos_despues = get_costos_fijos(db_path=db)
    conceptos = [c['concepto'] for c in costos_despues]
    assert 'Imprevistos' not in conceptos
    assert len(costos_despues) == 5  # Era 6, ahora 5


# ── Tests v1.2 — Pedidos CRUD ──────────────────────────────

def test_registrar_pedido(db_with_data):
    """Registrar pedido con estado Pendiente y total calculado."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='BRACOR',
        descripcion='Hoodies x10', unidades=10, costo_unitario=120000,
        pagado_por='JP', db_path=db,
    )
    assert pid is not None

    pedidos = get_pedidos(db_path=db)
    nuevo = [p for p in pedidos if p['id'] == pid][0]
    assert nuevo['proveedor'] == 'BRACOR'
    assert nuevo['unidades'] == 10
    assert nuevo['total'] == 1200000  # 10 * 120000
    assert nuevo['estado'] == 'Pendiente'


def test_pagar_pedido(db_with_data):
    """Pagar pedido cambia estado a Pagado y crea gasto."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='AUREN',
        descripcion='Camisas x5', unidades=5, costo_unitario=37000,
        db_path=db,
    )

    # Pagar
    pagar_pedido(pid, pagado_por='KATHE', db_path=db)

    # Verificar estado
    pedidos = get_pedidos(db_path=db)
    pedido = [p for p in pedidos if p['id'] == pid][0]
    assert pedido['estado'] == 'Pagado'
    assert pedido['pagado_por'] == 'KATHE'

    # Verificar que se creó el gasto
    gastos = query("SELECT * FROM gastos WHERE descripcion LIKE ?",
                   (f"Pedido #{pid}%",), db_path=db)
    assert len(gastos) == 1
    assert gastos[0]['monto'] == 185000  # 5 * 37000
    assert gastos[0]['pagado_por'] == 'KATHE'
    assert gastos[0]['categoria'] == 'Mercancía'


def test_pagar_pedido_ya_pagado_falla(db_with_data):
    """No se puede pagar un pedido ya pagado."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='BRACOR',
        descripcion='Test', unidades=5, costo_unitario=50000,
        db_path=db,
    )
    pagar_pedido(pid, pagado_por='JP', db_path=db)

    with pytest.raises(ValueError, match="ya está en estado"):
        pagar_pedido(pid, pagado_por='JP', db_path=db)


def test_recibir_mercancia(db_with_data):
    """Recibir mercancía cambia estado a Completo y agrega stock."""
    db = db_with_data
    stock_antes = get_producto('CAM-TEST-S', db_path=db)['stock']

    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='AUREN',
        descripcion='Camisas S', unidades=5, costo_unitario=37000,
        db_path=db,
    )
    pagar_pedido(pid, pagado_por='JP', db_path=db)

    # Recibir y agregar stock
    recibir_mercancia(pid, [('CAM-TEST-S', 5)], db_path=db)

    # Verificar estado
    pedidos = get_pedidos(db_path=db)
    pedido = [p for p in pedidos if p['id'] == pid][0]
    assert pedido['estado'] == 'Completo'

    # Verificar stock
    stock_despues = get_producto('CAM-TEST-S', db_path=db)['stock']
    assert stock_despues == stock_antes + 5


def test_recibir_sin_pagar_falla(db_with_data):
    """No se puede recibir mercancía de un pedido no pagado."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='BRACOR',
        descripcion='Test', unidades=5, costo_unitario=50000,
        db_path=db,
    )

    with pytest.raises(ValueError, match="no está pagado"):
        recibir_mercancia(pid, [('CAM-TEST-S', 5)], db_path=db)


def test_editar_pedido(db_with_data):
    """Editar pedido recalcula total si cambian unidades/costo."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='BRACOR',
        descripcion='Orig', unidades=10, costo_unitario=50000,
        db_path=db,
    )

    editar_pedido(pid, unidades=20, db_path=db)

    pedidos = get_pedidos(db_path=db)
    pedido = [p for p in pedidos if p['id'] == pid][0]
    assert pedido['unidades'] == 20
    # Total recalculado: 20 * 50000 = 1,000,000
    assert pedido['total'] == 1000000


def test_eliminar_pedido(db_with_data):
    """Eliminar pedido lo borra de la BD."""
    db = db_with_data
    pid = registrar_pedido(
        fecha_pedido='2026-02-10', proveedor='BRACOR',
        descripcion='A borrar', unidades=5, costo_unitario=50000,
        db_path=db,
    )

    pedidos_antes = get_pedidos(db_path=db)
    assert any(p['id'] == pid for p in pedidos_antes)

    eliminar_pedido(pid, db_path=db)

    pedidos_despues = get_pedidos(db_path=db)
    assert not any(p['id'] == pid for p in pedidos_despues)


def test_get_pedidos_pendientes(db_with_data):
    """get_pedidos_pendientes excluye los Completo."""
    db = db_with_data

    pid1 = registrar_pedido('2026-02-10', 'BRACOR', 'Pendiente', 5, 50000, db_path=db)
    pid2 = registrar_pedido('2026-02-11', 'AUREN', 'Pagado', 3, 40000, db_path=db)
    pagar_pedido(pid2, 'JP', db_path=db)
    pid3 = registrar_pedido('2026-02-12', 'YOUR BRAND', 'Completo', 2, 60000, db_path=db)
    pagar_pedido(pid3, 'KATHE', db_path=db)
    recibir_mercancia(pid3, [('CAM-TEST-S', 2)], db_path=db)

    pendientes = get_pedidos_pendientes(db_path=db)
    ids = [p['id'] for p in pendientes]
    assert pid1 in ids  # Pendiente
    assert pid2 in ids  # Pagado (no completo)
    assert pid3 not in ids  # Completo — excluido


def test_deuda_proveedores(db_with_data):
    """Solo pedidos en estado Pendiente cuentan como deuda."""
    db = db_with_data

    registrar_pedido('2026-02-10', 'BRACOR', 'Deuda1', 10, 50000, db_path=db)
    pid_pagado = registrar_pedido('2026-02-11', 'AUREN', 'Pagado', 5, 40000, db_path=db)
    pagar_pedido(pid_pagado, 'JP', db_path=db)

    deuda = get_total_deuda_proveedores(db_path=db)
    assert deuda == 500000  # Solo 10 * 50000 del pendiente


# ── Tests v1.2 — Venta con descuento y notas ───────────────

def test_venta_con_descuento(db_with_data):
    """Venta con descuento calcula total correctamente."""
    db = db_with_data
    vid = registrar_venta(
        'CAM-TEST-S', 2, 75000, 'Efectivo',
        vendedor='JP', descuento=10, db_path=db,
    )

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert len(ventas) == 1
    # Total = 75000 * 2 * (1 - 10/100) = 135000
    assert ventas[0]['total'] == pytest.approx(135000)
    assert ventas[0]['descuento_pct'] == 10


def test_venta_con_notas(db_with_data):
    """Venta con notas se registra correctamente."""
    db = db_with_data
    vid = registrar_venta(
        'CAM-TEST-S', 1, 75000, 'Efectivo',
        vendedor='JP', notas='Cliente frecuente', db_path=db,
    )

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['notas'] == 'Cliente frecuente'


def test_ventas_dia(db_with_data):
    """get_ventas_dia retorna resumen correcto."""
    db = db_with_data
    hoy = date.today().isoformat()

    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)
    registrar_venta('HOOD-TEST-L', 1, 200000, 'Transferencia', vendedor='KATHE', db_path=db)

    dia = get_ventas_dia(fecha=hoy, db_path=db)
    assert dia['total'] == pytest.approx(275000)
    assert dia['unidades'] == 2
    assert dia['totales_metodo']['Efectivo'] == pytest.approx(75000)
    assert dia['totales_metodo']['Transferencia'] == pytest.approx(200000)
    assert len(dia['ventas']) == 2


# ── Tests v1.3 — Abono parcial creditos ──────────────────

def test_abono_parcial(db_with_data):
    """Abono parcial reduce saldo sin completar credito."""
    db = db_with_data
    # Crear venta a credito
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito',
                          cliente='Carlos', vendedor='JP', db_path=db)

    # Verificar credito creado
    creditos = get_creditos_pendientes(db_path=db)
    assert len(creditos) == 1
    assert creditos[0]['monto'] == 75000
    cid = creditos[0]['id']

    # Abonar 30000
    result = registrar_abono(cid, 30000, db_path=db)
    assert result['abono'] == 30000
    assert result['total_pagado'] == 30000
    assert result['saldo_restante'] == 45000
    assert result['completado'] is False

    # Credito sigue pendiente
    creditos = get_creditos_pendientes(db_path=db)
    assert len(creditos) == 1
    assert creditos[0]['monto_pagado'] == 30000


def test_abono_completa_pago(db_with_data):
    """Abono que cubre el total marca credito como pagado."""
    db = db_with_data
    vid = registrar_venta('HOOD-TEST-L', 1, 200000, 'Crédito',
                          cliente='Maria', vendedor='KATHE', db_path=db)

    creditos = get_creditos_pendientes(db_path=db)
    cid = creditos[0]['id']

    # Abonar parcialmente
    registrar_abono(cid, 100000, db_path=db)

    # Abonar el resto
    result = registrar_abono(cid, 100000, db_path=db)
    assert result['completado'] is True
    assert result['saldo_restante'] == 0

    # Ya no hay creditos pendientes
    creditos = get_creditos_pendientes(db_path=db)
    assert len(creditos) == 0


def test_abono_credito_ya_pagado_falla(db_with_data):
    """No se puede abonar a un credito ya pagado."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito',
                          cliente='Pedro', vendedor='JP', db_path=db)

    creditos = get_creditos_pendientes(db_path=db)
    cid = creditos[0]['id']

    # Pagar completamente
    registrar_pago_credito(cid, db_path=db)

    # Intentar abonar debe fallar
    with pytest.raises(ValueError, match="ya esta pagado"):
        registrar_abono(cid, 10000, db_path=db)


def test_abono_monto_invalido(db_with_data):
    """Abono con monto 0 o negativo falla."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito',
                          cliente='Luis', vendedor='JP', db_path=db)

    creditos = get_creditos_pendientes(db_path=db)
    cid = creditos[0]['id']

    with pytest.raises(ValueError, match="mayor a 0"):
        registrar_abono(cid, 0, db_path=db)


def test_pago_completo_llena_monto_pagado(db_with_data):
    """registrar_pago_credito pone monto_pagado = monto total."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito',
                          cliente='Ana', vendedor='ANDRES', db_path=db)

    creditos = get_creditos_pendientes(db_path=db)
    cid = creditos[0]['id']

    registrar_pago_credito(cid, db_path=db)

    # Verificar que monto_pagado = monto
    paid = query("SELECT * FROM creditos_clientes WHERE id = ?", (cid,), db_path=db)
    assert paid[0]['pagado'] == 1
    assert paid[0]['monto_pagado'] == 75000


# ── Tests v1.4 — Editar venta ──────────────────────────────

def test_editar_venta_precio(db_with_data):
    """Editar precio de venta recalcula total."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 2, 75000, 'Efectivo', vendedor='JP', db_path=db)

    # Verificar total original: 2 * 75000 = 150000
    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['total'] == pytest.approx(150000)

    # Cambiar precio a 80000 → nuevo total = 2 * 80000 = 160000
    editar_venta(vid, precio=80000, db_path=db)

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['precio_unitario'] == 80000
    assert ventas[0]['total'] == pytest.approx(160000)


def test_editar_venta_metodo(db_with_data):
    """Editar método de pago sin afectar total."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)

    editar_venta(vid, metodo_pago='Transferencia', db_path=db)

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['metodo_pago'] == 'Transferencia'
    assert ventas[0]['total'] == pytest.approx(75000)  # Sin cambio


def test_editar_venta_vendedor(db_with_data):
    """Editar vendedor de una venta."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)

    editar_venta(vid, vendedor='KATHE', db_path=db)

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['vendedor'] == 'KATHE'


def test_editar_venta_sin_campos(db_with_data):
    """Editar venta sin campos no hace nada."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)

    editar_venta(vid, db_path=db)  # Sin campos

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['precio_unitario'] == 75000
    assert ventas[0]['metodo_pago'] == 'Efectivo'
    assert ventas[0]['vendedor'] == 'JP'


# ── Tests v1.4 — Reabrir caja ──────────────────────────────

def test_reabrir_caja(db_with_data):
    """Reabrir caja limpia cierre pero mantiene apertura."""
    db = db_with_data
    hoy = date.today().isoformat()

    # Abrir y cerrar caja
    abrir_caja(fecha=hoy, efectivo_inicio=100000, db_path=db)
    registrar_venta('CAM-TEST-S', 1, 75000, 'Efectivo', vendedor='JP', db_path=db)
    cerrar_caja(fecha=hoy, efectivo_real=175000, db_path=db)

    # Verificar cerrada
    estado = get_estado_caja(fecha=hoy, db_path=db)
    assert estado['cerrada'] == 1
    assert estado['efectivo_cierre_real'] == 175000

    # Reabrir
    reabrir_caja(fecha=hoy, db_path=db)

    # Verificar reabierta
    estado = get_estado_caja(fecha=hoy, db_path=db)
    assert estado['cerrada'] == 0
    assert estado['efectivo_cierre_real'] is None
    # Apertura se mantiene
    assert estado['efectivo_inicio'] == 100000
    assert estado['caja_abierta'] is True


# ── Tests v1.4 — Venta a crédito requiere cliente ──────────

def test_venta_credito_sin_cliente_falla(db_with_data):
    """Venta a crédito sin cliente debe fallar."""
    db = db_with_data
    with pytest.raises(ValueError, match="crédito requiere"):
        registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito', cliente=None,
                        vendedor='JP', db_path=db)


def test_venta_credito_con_cliente(db_with_data):
    """Venta a crédito con cliente se registra correctamente."""
    db = db_with_data
    vid = registrar_venta('CAM-TEST-S', 1, 75000, 'Crédito',
                          cliente='Diana', vendedor='KATHE', db_path=db)

    ventas = query("SELECT * FROM ventas WHERE id = ?", (vid,), db_path=db)
    assert ventas[0]['metodo_pago'] == 'Crédito'
    assert ventas[0]['cliente'] == 'Diana'

    creditos = query("SELECT * FROM creditos_clientes WHERE venta_id = ?", (vid,), db_path=db)
    assert len(creditos) == 1
    assert creditos[0]['cliente'] == 'Diana'


# ── Tests v1.5 — CHECK constraints en BD ────────────────────

def test_constraint_stock_no_negativo(db_path):
    """Stock no puede ser negativo (CHECK constraint)."""
    with pytest.raises(Exception):
        crear_producto(
            sku='BAD-STOCK', nombre='Bad', categoria='Test',
            talla='S', color='X', costo=1000, precio_venta=2000,
            stock=-5, db_path=db_path,
        )


def test_constraint_precio_no_negativo(db_path):
    """Precio de venta no puede ser negativo."""
    with pytest.raises(Exception):
        crear_producto(
            sku='BAD-PRICE', nombre='Bad', categoria='Test',
            talla='S', color='X', costo=1000, precio_venta=-500,
            stock=5, db_path=db_path,
        )


def test_constraint_gasto_monto_positivo(db_with_data):
    """Monto de gasto debe ser mayor a 0."""
    db = db_with_data
    with pytest.raises(Exception):
        registrar_gasto(
            fecha='2026-02-15', categoria='Test', monto=0,
            descripcion='Monto cero', pagado_por='JP', db_path=db,
        )


def test_constraint_gasto_pagador_valido(db_with_data):
    """Pagador de gasto debe ser JP, KATHE o ANDRES."""
    db = db_with_data
    with pytest.raises(Exception):
        registrar_gasto(
            fecha='2026-02-15', categoria='Test', monto=5000,
            descripcion='Pagador inválido', pagado_por='ORVANN', db_path=db,
        )


def test_constraint_metodo_pago_valido(db_with_data):
    """Método de pago debe ser uno de los válidos."""
    db = db_with_data
    with pytest.raises(Exception):
        registrar_venta('CAM-TEST-S', 1, 75000, 'Bitcoin',
                        vendedor='JP', db_path=db)
