"""Lógica de negocio de ORVANN Retail OS."""
from datetime import date, datetime
from app.database import query, execute, get_connection

SOCIOS = ['JP', 'KATHE', 'ANDRES']


# ── Ventas ──────────────────────────────────────────────

def registrar_venta(sku, cantidad, precio, metodo_pago, cliente=None,
                    vendedor=None, descuento=0, notas=None, db_path=None):
    """Registra venta, descuenta stock. Si es crédito, crea registro en creditos_clientes."""
    conn = get_connection(db_path)
    try:
        # Verificar stock
        prod = conn.execute("SELECT stock, nombre FROM productos WHERE sku = ?", (sku,)).fetchone()
        if prod is None:
            raise ValueError(f"Producto {sku} no existe")
        if prod['stock'] < cantidad:
            raise ValueError(f"Stock insuficiente para {sku}: {prod['stock']} disponibles, {cantidad} solicitados")

        total = precio * cantidad * (1 - descuento / 100)
        hoy = date.today().isoformat()
        ahora = datetime.now().strftime('%H:%M:%S')

        cursor = conn.execute("""
            INSERT INTO ventas (fecha, hora, sku, cantidad, precio_unitario, descuento_pct, total, metodo_pago, cliente, vendedor, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (hoy, ahora, sku, cantidad, precio, descuento, total, metodo_pago, cliente, vendedor, notas))

        venta_id = cursor.lastrowid

        # Descontar stock
        conn.execute("UPDATE productos SET stock = stock - ? WHERE sku = ?", (cantidad, sku))

        # Si es crédito, crear registro
        if metodo_pago == 'Crédito':
            if not cliente:
                raise ValueError("Venta a crédito requiere nombre de cliente")
            conn.execute("""
                INSERT INTO creditos_clientes (venta_id, cliente, monto, fecha_credito, pagado, notas)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (venta_id, cliente, total, hoy, notas))

        conn.commit()
        return venta_id
    finally:
        conn.close()


def get_ventas_dia(fecha=None, db_path=None):
    """Ventas del día con totales por método de pago."""
    if fecha is None:
        fecha = date.today().isoformat()
    ventas = query("""
        SELECT v.*, p.nombre as producto_nombre
        FROM ventas v
        LEFT JOIN productos p ON v.sku = p.sku
        WHERE v.fecha = ?
        ORDER BY v.hora DESC
    """, (fecha,), db_path=db_path)

    totales = {}
    total_general = 0
    for v in ventas:
        mp = v['metodo_pago']
        totales[mp] = totales.get(mp, 0) + v['total']
        total_general += v['total']

    return {
        'ventas': ventas,
        'totales_metodo': totales,
        'total': total_general,
        'unidades': sum(v['cantidad'] for v in ventas),
    }


def get_ventas_mes(year, month, db_path=None):
    """Ventas del mes con métricas."""
    fecha_inicio = f"{year}-{month:02d}-01"
    if month == 12:
        fecha_fin = f"{year + 1}-01-01"
    else:
        fecha_fin = f"{year}-{month + 1:02d}-01"

    ventas = query("""
        SELECT v.*, p.nombre as producto_nombre, p.costo
        FROM ventas v
        LEFT JOIN productos p ON v.sku = p.sku
        WHERE v.fecha >= ? AND v.fecha < ?
        ORDER BY v.fecha DESC, v.hora DESC
    """, (fecha_inicio, fecha_fin), db_path=db_path)

    total_ventas = sum(v['total'] for v in ventas)
    total_costo = sum((v.get('costo') or 0) * v['cantidad'] for v in ventas)
    total_unidades = sum(v['cantidad'] for v in ventas)

    # Top productos
    from collections import Counter
    prod_count = Counter()
    prod_revenue = Counter()
    for v in ventas:
        nombre = v.get('producto_nombre') or v['sku']
        prod_count[nombre] += v['cantidad']
        prod_revenue[nombre] += v['total']

    return {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_costo': total_costo,
        'utilidad_bruta': total_ventas - total_costo,
        'total_unidades': total_unidades,
        'top_productos': prod_count.most_common(10),
        'top_revenue': prod_revenue.most_common(10),
    }


# ── Punto de Equilibrio ──────────────────────────────────

def calcular_punto_equilibrio(db_path=None):
    """
    Calcula punto de equilibrio mensual.
    CF = costos fijos activos
    Margen promedio ponderado = SUM(margen * stock) / SUM(stock)
    """
    costos = query("SELECT SUM(monto_mensual) as total FROM costos_fijos WHERE activo = 1", db_path=db_path)
    cf = costos[0]['total'] or 0

    # Margen ponderado por stock
    productos = query("""
        SELECT precio_venta, costo, stock
        FROM productos
        WHERE stock > 0 AND precio_venta > 0
    """, db_path=db_path)

    if not productos:
        # Si no hay stock, usar todos los productos
        productos = query("""
            SELECT precio_venta, costo, stock
            FROM productos
            WHERE precio_venta > 0
        """, db_path=db_path)

    total_margen_pond = 0
    total_stock = 0
    total_precio_pond = 0

    for p in productos:
        stock = max(p['stock'], 1)  # mínimo 1 para promediar
        margen = (p['precio_venta'] - p['costo']) / p['precio_venta'] if p['precio_venta'] > 0 else 0
        total_margen_pond += margen * stock
        total_stock += stock
        total_precio_pond += p['precio_venta'] * stock

    margen_prom = total_margen_pond / total_stock if total_stock > 0 else 0.5
    ticket_prom = total_precio_pond / total_stock if total_stock > 0 else 100000

    pe_pesos = cf / margen_prom if margen_prom > 0 else 0
    pe_unidades = pe_pesos / ticket_prom if ticket_prom > 0 else 0
    pe_diario = pe_unidades / 30

    # Ventas del mes actual
    hoy = date.today()
    ventas_mes = get_ventas_mes(hoy.year, hoy.month, db_path=db_path)
    ventas_acumuladas = ventas_mes['total_ventas']
    unidades_vendidas = ventas_mes['total_unidades']

    progreso_pct = (ventas_acumuladas / pe_pesos * 100) if pe_pesos > 0 else 0
    dias_restantes = max(1, 30 - hoy.day)
    unidades_faltantes = max(0, pe_unidades - unidades_vendidas)

    return {
        'cf': cf,
        'margen_prom': margen_prom,
        'ticket_prom': ticket_prom,
        'pe_pesos': pe_pesos,
        'pe_unidades': pe_unidades,
        'pe_diario': pe_diario,
        'ventas_acumuladas': ventas_acumuladas,
        'unidades_vendidas': unidades_vendidas,
        'progreso_pct': progreso_pct,
        'dias_restantes': dias_restantes,
        'unidades_faltantes': unidades_faltantes,
    }


# ── Liquidación Socios ────────────────────────────────────

def calcular_liquidacion_socios(db_path=None):
    """
    Calcula cuánto puso cada socio y cuánto le corresponde.
    Gastos de ORVANN (pagados parejo) se dividen 33.3% cada uno.
    """
    gastos = query("SELECT * FROM gastos", db_path=db_path)

    aportes = {s: 0.0 for s in SOCIOS}
    total_real = 0.0
    por_categoria = {}

    for g in gastos:
        monto = g['monto']
        pagado_por = g['pagado_por']

        if pagado_por == 'ORVANN':
            # Pagado parejo entre los 3
            for s in SOCIOS:
                aportes[s] += monto  # cada uno puso 'monto'
            total_real += monto
        elif pagado_por in SOCIOS:
            aportes[pagado_por] += monto
            total_real += monto
        else:
            total_real += monto

        cat = g['categoria']
        por_categoria[cat] = por_categoria.get(cat, 0) + monto

    # Cada socio le corresponde 33.3% del total
    parte_cada_uno = total_real / 3

    saldos = {}
    for s in SOCIOS:
        saldos[s] = {
            'aportado': aportes[s],
            'le_corresponde': parte_cada_uno,
            'saldo': aportes[s] - parte_cada_uno,  # positivo = le deben, negativo = debe
        }

    return {
        'total_real': total_real,
        'aportes': aportes,
        'parte_cada_uno': parte_cada_uno,
        'saldos': saldos,
        'por_categoria': por_categoria,
    }


# ── Caja ─────────────────────────────────────────────────

def get_estado_caja(fecha=None, db_path=None):
    """Estado de caja del día: efectivo inicio + ventas por método - gastos efectivo."""
    if fecha is None:
        fecha = date.today().isoformat()

    # Buscar caja del día
    caja = query("SELECT * FROM caja_diaria WHERE fecha = ?", (fecha,), db_path=db_path)
    efectivo_inicio = caja[0]['efectivo_inicio'] if caja else 0

    # Ventas del día por método
    ventas = query("""
        SELECT metodo_pago, SUM(total) as total
        FROM ventas WHERE fecha = ?
        GROUP BY metodo_pago
    """, (fecha,), db_path=db_path)

    totales_ventas = {v['metodo_pago']: v['total'] for v in ventas}
    ventas_efectivo = totales_ventas.get('Efectivo', 0)

    # Gastos del día en efectivo
    gastos = query("""
        SELECT SUM(monto) as total
        FROM gastos WHERE fecha = ? AND metodo_pago = 'Efectivo'
    """, (fecha,), db_path=db_path)
    gastos_efectivo = gastos[0]['total'] if gastos and gastos[0]['total'] else 0

    efectivo_esperado = efectivo_inicio + ventas_efectivo - gastos_efectivo

    return {
        'fecha': fecha,
        'efectivo_inicio': efectivo_inicio,
        'totales_ventas': totales_ventas,
        'ventas_efectivo': ventas_efectivo,
        'gastos_efectivo': gastos_efectivo,
        'efectivo_esperado': efectivo_esperado,
        'cerrada': caja[0]['cerrada'] if caja else 0,
        'efectivo_cierre_real': caja[0]['efectivo_cierre_real'] if caja else None,
    }


def cerrar_caja(fecha, efectivo_real, notas=None, db_path=None):
    """Registra cierre de caja y calcula diferencia."""
    estado = get_estado_caja(fecha, db_path=db_path)
    diferencia = efectivo_real - estado['efectivo_esperado']

    conn = get_connection(db_path)
    try:
        conn.execute("""
            INSERT INTO caja_diaria (fecha, efectivo_inicio, efectivo_cierre_real, cerrada, notas)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                efectivo_cierre_real = ?,
                cerrada = 1,
                notas = ?
        """, (fecha, estado['efectivo_inicio'], efectivo_real, notas, efectivo_real, notas))
        conn.commit()
    finally:
        conn.close()

    return {
        'efectivo_esperado': estado['efectivo_esperado'],
        'efectivo_real': efectivo_real,
        'diferencia': diferencia,
    }


# ── Créditos ──────────────────────────────────────────────

def get_creditos_pendientes(db_path=None):
    """Lista de créditos pendientes de pago."""
    return query("""
        SELECT c.*, v.fecha as fecha_venta, v.sku, p.nombre as producto_nombre
        FROM creditos_clientes c
        LEFT JOIN ventas v ON c.venta_id = v.id
        LEFT JOIN productos p ON v.sku = p.sku
        WHERE c.pagado = 0
        ORDER BY c.fecha_credito
    """, db_path=db_path)


def registrar_pago_credito(credito_id, fecha_pago=None, db_path=None):
    """Marca crédito como pagado."""
    if fecha_pago is None:
        fecha_pago = date.today().isoformat()
    execute(
        "UPDATE creditos_clientes SET pagado = 1, fecha_pago = ? WHERE id = ?",
        (fecha_pago, credito_id), db_path=db_path
    )


# ── Inventario ────────────────────────────────────────────

def get_alertas_stock(db_path=None):
    """Productos con stock <= stock_minimo."""
    return query("""
        SELECT * FROM productos
        WHERE stock <= stock_minimo
        ORDER BY stock ASC, nombre
    """, db_path=db_path)


def get_resumen_inventario(db_path=None):
    """Resumen de inventario por categoría."""
    total = query("""
        SELECT
            COUNT(*) as total_skus,
            SUM(stock) as total_unidades,
            SUM(costo * stock) as valor_costo,
            SUM(precio_venta * stock) as valor_venta
        FROM productos
    """, db_path=db_path)

    por_categoria = query("""
        SELECT
            categoria,
            COUNT(*) as skus,
            SUM(stock) as unidades,
            SUM(costo * stock) as valor_costo,
            SUM(precio_venta * stock) as valor_venta
        FROM productos
        GROUP BY categoria
        ORDER BY valor_venta DESC
    """, db_path=db_path)

    return {
        'total': total[0] if total else {},
        'por_categoria': por_categoria,
    }


def agregar_stock(sku, cantidad, db_path=None):
    """Agrega unidades al stock de un producto."""
    execute(
        "UPDATE productos SET stock = stock + ? WHERE sku = ?",
        (cantidad, sku), db_path=db_path
    )


# ── Gastos ────────────────────────────────────────────────

def registrar_gasto(fecha, categoria, monto, descripcion, pagado_por,
                    metodo_pago=None, es_inversion=0, notas=None, db_path=None):
    """Registra un nuevo gasto."""
    return execute("""
        INSERT INTO gastos (fecha, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas),
        db_path=db_path)


def get_gastos_mes(year, month, db_path=None):
    """Gastos del mes con totales por categoría."""
    fecha_inicio = f"{year}-{month:02d}-01"
    if month == 12:
        fecha_fin = f"{year + 1}-01-01"
    else:
        fecha_fin = f"{year}-{month + 1:02d}-01"

    gastos = query("""
        SELECT * FROM gastos
        WHERE fecha >= ? AND fecha < ?
        ORDER BY fecha DESC
    """, (fecha_inicio, fecha_fin), db_path=db_path)

    por_categoria = {}
    total = 0
    for g in gastos:
        cat = g['categoria']
        por_categoria[cat] = por_categoria.get(cat, 0) + g['monto']
        total += g['monto']

    return {
        'gastos': gastos,
        'por_categoria': por_categoria,
        'total': total,
    }


# ── Productos ─────────────────────────────────────────────

def get_productos(db_path=None):
    """Todos los productos."""
    return query("SELECT * FROM productos ORDER BY categoria, nombre", db_path=db_path)


def get_producto(sku, db_path=None):
    """Un producto por SKU."""
    result = query("SELECT * FROM productos WHERE sku = ?", (sku,), db_path=db_path)
    return result[0] if result else None


# ── Pedidos ───────────────────────────────────────────────

def get_pedidos_pendientes(db_path=None):
    """Pedidos pendientes de pago."""
    return query("""
        SELECT * FROM pedidos_proveedores
        WHERE estado != 'Pagado'
        ORDER BY fecha_pedido DESC
    """, db_path=db_path)


def get_total_deuda_proveedores(db_path=None):
    """Total pendiente de pago a proveedores."""
    result = query("""
        SELECT SUM(total) as total
        FROM pedidos_proveedores
        WHERE estado != 'Pagado'
    """, db_path=db_path)
    return result[0]['total'] or 0 if result else 0
