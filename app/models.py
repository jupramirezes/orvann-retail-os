"""Logica de negocio de ORVANN Retail OS. v1.4"""
import math
from datetime import date, datetime, timedelta
from app.database import query, execute, get_connection, adapt_sql, _is_sqlite

SOCIOS = ['JP', 'KATHE', 'ANDRES']


# ── Ventas ──────────────────────────────────────────────

def registrar_venta(sku, cantidad, precio, metodo_pago, cliente=None,
                    vendedor=None, descuento=0, notas=None, db_path=None):
    """Registra venta, descuenta stock. Si es crédito, crea registro en creditos_clientes.
    Compatible SQLite y PostgreSQL via adapt_sql()."""
    conn = get_connection(db_path)
    is_sqlite = _is_sqlite(db_path)
    _sql = lambda s: adapt_sql(s, db_path)
    try:
        if is_sqlite:
            prod = conn.execute(_sql("SELECT stock, nombre FROM productos WHERE sku = ?"), (sku,)).fetchone()
            prod = dict(prod) if prod else None
        else:
            cur = conn.cursor()
            cur.execute(_sql("SELECT stock, nombre FROM productos WHERE sku = ?"), (sku,))
            cols = [d[0] for d in cur.description] if cur.description else []
            row = cur.fetchone()
            prod = dict(zip(cols, row)) if row else None

        if prod is None:
            raise ValueError(f"Producto {sku} no existe")
        if prod['stock'] < cantidad:
            raise ValueError(f"Stock insuficiente para {sku}: {prod['stock']} disponibles, {cantidad} solicitados")

        total = precio * cantidad * (1 - descuento / 100)
        hoy = date.today().isoformat()
        ahora = datetime.now().strftime('%H:%M:%S')

        insert_sql = _sql("""
            INSERT INTO ventas (fecha, hora, sku, cantidad, precio_unitario, descuento_pct, total, metodo_pago, cliente, vendedor, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        params = (hoy, ahora, sku, cantidad, precio, descuento, total, metodo_pago, cliente, vendedor, notas)

        if is_sqlite:
            cursor = conn.execute(insert_sql, params)
            venta_id = cursor.lastrowid
        else:
            cur = conn.cursor()
            cur.execute(insert_sql.rstrip().rstrip(';') + ' RETURNING id', params)
            venta_id = cur.fetchone()[0]

        update_sql = _sql("UPDATE productos SET stock = stock - ? WHERE sku = ?")
        if is_sqlite:
            conn.execute(update_sql, (cantidad, sku))
        else:
            cur.execute(update_sql, (cantidad, sku))

        if metodo_pago == 'Crédito':
            if not cliente:
                raise ValueError("Venta a crédito requiere nombre de cliente")
            credit_sql = _sql("""
                INSERT INTO creditos_clientes (venta_id, cliente, monto, fecha_credito, pagado, notas)
                VALUES (?, ?, ?, ?, 0, ?)
            """)
            if is_sqlite:
                conn.execute(credit_sql, (venta_id, cliente, total, hoy, notas))
            else:
                cur.execute(credit_sql, (venta_id, cliente, total, hoy, notas))

        conn.commit()
        return venta_id
    finally:
        conn.close()


def anular_venta(venta_id, db_path=None):
    """Revierte una venta: devuelve stock, elimina crédito si existe, borra venta.
    Compatible SQLite y PostgreSQL."""
    # Fetch venta using backend-agnostic query()
    ventas = query("SELECT * FROM ventas WHERE id = ?", (venta_id,), db_path=db_path)
    if not ventas:
        raise ValueError(f"Venta #{venta_id} no existe")
    venta = ventas[0]

    # Execute all updates using backend-agnostic execute()
    execute("UPDATE productos SET stock = stock + ? WHERE sku = ?",
            (venta['cantidad'], venta['sku']), db_path=db_path)
    execute("DELETE FROM creditos_clientes WHERE venta_id = ?", (venta_id,), db_path=db_path)
    execute("DELETE FROM ventas WHERE id = ?", (venta_id,), db_path=db_path)

    return dict(venta)


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


def get_ventas_rango(fecha_inicio, fecha_fin, db_path=None):
    """Ventas en un rango de fechas."""
    return query("""
        SELECT v.*, p.nombre as producto_nombre, p.costo
        FROM ventas v
        LEFT JOIN productos p ON v.sku = p.sku
        WHERE v.fecha >= ? AND v.fecha <= ?
        ORDER BY v.fecha DESC, v.hora DESC
    """, (fecha_inicio, fecha_fin), db_path=db_path)


def get_ventas_semana(db_path=None):
    """Ventas de la semana actual (lunes a hoy)."""
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    ventas = get_ventas_rango(lunes.isoformat(), hoy.isoformat(), db_path=db_path)

    total = sum(v['total'] for v in ventas)
    unidades = sum(v['cantidad'] for v in ventas)
    costo = sum((v.get('costo') or 0) * v['cantidad'] for v in ventas)

    return {
        'ventas': ventas,
        'total': total,
        'unidades': unidades,
        'costo': costo,
        'utilidad': total - costo,
        'fecha_inicio': lunes.isoformat(),
        'fecha_fin': hoy.isoformat(),
    }


def get_ventas_semana_anterior(db_path=None):
    """Ventas de la semana anterior."""
    hoy = date.today()
    lunes_esta = hoy - timedelta(days=hoy.weekday())
    domingo_pasado = lunes_esta - timedelta(days=1)
    lunes_pasado = domingo_pasado - timedelta(days=domingo_pasado.weekday())

    ventas = get_ventas_rango(lunes_pasado.isoformat(), domingo_pasado.isoformat(), db_path=db_path)
    total = sum(v['total'] for v in ventas)
    unidades = sum(v['cantidad'] for v in ventas)

    return {'total': total, 'unidades': unidades}


def get_ventas_diarias_mes(year, month, db_path=None):
    """Ventas agrupadas por día para gráfico."""
    fecha_inicio = f"{year}-{month:02d}-01"
    if month == 12:
        fecha_fin = f"{year + 1}-01-01"
    else:
        fecha_fin = f"{year}-{month + 1:02d}-01"

    return query("""
        SELECT fecha, SUM(total) as total_dia, SUM(cantidad) as unidades_dia
        FROM ventas
        WHERE fecha >= ? AND fecha < ?
        GROUP BY fecha
        ORDER BY fecha
    """, (fecha_inicio, fecha_fin), db_path=db_path)


# ── Punto de Equilibrio ──────────────────────────────────

def calcular_punto_equilibrio(db_path=None):
    """Calcula punto de equilibrio mensual."""
    costos = query("SELECT SUM(monto_mensual) as total FROM costos_fijos WHERE activo = 1", db_path=db_path)
    cf = costos[0]['total'] or 0

    productos = query("""
        SELECT precio_venta, costo, stock
        FROM productos WHERE stock > 0 AND precio_venta > 0
    """, db_path=db_path)

    if not productos:
        productos = query("SELECT precio_venta, costo, stock FROM productos WHERE precio_venta > 0", db_path=db_path)

    total_margen_pond = 0
    total_stock = 0
    total_precio_pond = 0

    for p in productos:
        stock = max(p['stock'], 1)
        margen = (p['precio_venta'] - p['costo']) / p['precio_venta'] if p['precio_venta'] > 0 else 0
        total_margen_pond += margen * stock
        total_stock += stock
        total_precio_pond += p['precio_venta'] * stock

    margen_prom = total_margen_pond / total_stock if total_stock > 0 else 0.5
    ticket_prom = total_precio_pond / total_stock if total_stock > 0 else 100000

    pe_pesos = cf / margen_prom if margen_prom > 0 else 0
    pe_unidades = pe_pesos / ticket_prom if ticket_prom > 0 else 0
    pe_diario = pe_unidades / 30

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
    Cada fila de gastos es un pago real de un socio específico.
    """
    gastos = query("SELECT * FROM gastos ORDER BY fecha", db_path=db_path)

    aportes = {s: 0.0 for s in SOCIOS}
    total_real = 0.0
    por_categoria = {}
    por_socio_categoria = {s: {} for s in SOCIOS}

    for g in gastos:
        monto = g['monto']
        pagado_por = g['pagado_por']

        if pagado_por in SOCIOS:
            aportes[pagado_por] += monto

        total_real += monto

        cat = g['categoria']
        por_categoria[cat] = por_categoria.get(cat, 0) + monto

        if pagado_por in SOCIOS:
            por_socio_categoria[pagado_por][cat] = por_socio_categoria[pagado_por].get(cat, 0) + monto

    parte_cada_uno = total_real / 3 if total_real > 0 else 0

    saldos = {}
    for s in SOCIOS:
        saldos[s] = {
            'aportado': aportes[s],
            'le_corresponde': parte_cada_uno,
            'saldo': aportes[s] - parte_cada_uno,
        }

    return {
        'total_real': total_real,
        'aportes': aportes,
        'parte_cada_uno': parte_cada_uno,
        'saldos': saldos,
        'por_categoria': por_categoria,
        'por_socio_categoria': por_socio_categoria,
        'gastos': gastos,
    }


# ── Caja ─────────────────────────────────────────────────

def abrir_caja(fecha=None, efectivo_inicio=0, db_path=None):
    """Abre la caja del día con un monto inicial de efectivo.
    Compatible SQLite y PostgreSQL."""
    if fecha is None:
        fecha = date.today().isoformat()

    existing = query("SELECT * FROM caja_diaria WHERE fecha = ?", (fecha,), db_path=db_path)
    if existing:
        execute("UPDATE caja_diaria SET efectivo_inicio = ? WHERE fecha = ?",
                (efectivo_inicio, fecha), db_path=db_path)
    else:
        execute("""
            INSERT INTO caja_diaria (fecha, efectivo_inicio, cerrada)
            VALUES (?, ?, 0)
        """, (fecha, efectivo_inicio), db_path=db_path)

    return {'fecha': fecha, 'efectivo_inicio': efectivo_inicio}


def get_estado_caja(fecha=None, db_path=None):
    """Estado de caja del día."""
    if fecha is None:
        fecha = date.today().isoformat()

    caja = query("SELECT * FROM caja_diaria WHERE fecha = ?", (fecha,), db_path=db_path)
    efectivo_inicio = caja[0]['efectivo_inicio'] if caja else 0
    caja_abierta = len(caja) > 0

    ventas = query("""
        SELECT metodo_pago, SUM(total) as total
        FROM ventas WHERE fecha = ?
        GROUP BY metodo_pago
    """, (fecha,), db_path=db_path)

    totales_ventas = {v['metodo_pago']: v['total'] for v in ventas}
    ventas_efectivo = totales_ventas.get('Efectivo', 0)

    gastos = query("""
        SELECT SUM(monto) as total
        FROM gastos WHERE fecha = ? AND metodo_pago = 'Efectivo'
    """, (fecha,), db_path=db_path)
    gastos_efectivo = gastos[0]['total'] if gastos and gastos[0]['total'] else 0

    efectivo_esperado = efectivo_inicio + ventas_efectivo - gastos_efectivo

    return {
        'fecha': fecha,
        'caja_abierta': caja_abierta,
        'efectivo_inicio': efectivo_inicio,
        'totales_ventas': totales_ventas,
        'ventas_efectivo': ventas_efectivo,
        'gastos_efectivo': gastos_efectivo,
        'efectivo_esperado': efectivo_esperado,
        'cerrada': caja[0]['cerrada'] if caja else 0,
        'efectivo_cierre_real': caja[0]['efectivo_cierre_real'] if caja else None,
    }


def cerrar_caja(fecha, efectivo_real, notas=None, db_path=None):
    """Registra cierre de caja y calcula diferencia.
    Compatible SQLite y PostgreSQL."""
    estado = get_estado_caja(fecha, db_path=db_path)
    diferencia = efectivo_real - estado['efectivo_esperado']

    # Check if caja exists for today
    existing = query("SELECT * FROM caja_diaria WHERE fecha = ?", (fecha,), db_path=db_path)
    if existing:
        execute("""
            UPDATE caja_diaria SET efectivo_cierre_real = ?, cerrada = 1, notas = ?
            WHERE fecha = ?
        """, (efectivo_real, notas, fecha), db_path=db_path)
    else:
        execute("""
            INSERT INTO caja_diaria (fecha, efectivo_inicio, efectivo_cierre_real, cerrada, notas)
            VALUES (?, ?, ?, 1, ?)
        """, (fecha, estado['efectivo_inicio'], efectivo_real, notas), db_path=db_path)

    return {
        'efectivo_esperado': estado['efectivo_esperado'],
        'efectivo_real': efectivo_real,
        'diferencia': diferencia,
    }


def reabrir_caja(fecha=None, db_path=None):
    """Reabre una caja cerrada (borra cierre, mantiene apertura).
    Compatible SQLite y PostgreSQL."""
    if fecha is None:
        fecha = date.today().isoformat()
    execute("""
        UPDATE caja_diaria
        SET cerrada = 0, efectivo_cierre_real = NULL, notas = NULL
        WHERE fecha = ?
    """, (fecha,), db_path=db_path)


def editar_venta(venta_id, precio=None, metodo_pago=None, vendedor=None,
                 notas=None, db_path=None):
    """Edita campos de una venta sin afectar stock.
    Recalcula total si cambia precio."""
    updates = []
    params = []
    if precio is not None:
        updates.append("precio_unitario = ?")
        params.append(precio)
    if metodo_pago is not None:
        updates.append("metodo_pago = ?")
        params.append(metodo_pago)
    if vendedor is not None:
        updates.append("vendedor = ?")
        params.append(vendedor)
    if notas is not None:
        updates.append("notas = ?")
        params.append(notas)

    if not updates:
        return

    # Si cambia precio, recalcular total
    if precio is not None:
        venta = query("SELECT * FROM ventas WHERE id = ?", (venta_id,), db_path=db_path)
        if venta:
            v = venta[0]
            new_total = precio * v['cantidad'] * (1 - (v.get('descuento_pct') or 0) / 100)
            updates.append("total = ?")
            params.append(new_total)

    params.append(venta_id)
    sql = f"UPDATE ventas SET {', '.join(updates)} WHERE id = ?"
    execute(sql, tuple(params), db_path=db_path)


# ── Créditos ──────────────────────────────────────────────

def get_creditos_pendientes(db_path=None):
    return query("""
        SELECT c.*, v.fecha as fecha_venta, v.sku, p.nombre as producto_nombre
        FROM creditos_clientes c
        LEFT JOIN ventas v ON c.venta_id = v.id
        LEFT JOIN productos p ON v.sku = p.sku
        WHERE c.pagado = 0
        ORDER BY c.fecha_credito
    """, db_path=db_path)


def registrar_pago_credito(credito_id, fecha_pago=None, db_path=None):
    """Marca un credito como completamente pagado."""
    if fecha_pago is None:
        fecha_pago = date.today().isoformat()
    # Set monto_pagado to full monto when marking as paid
    credito = query("SELECT monto FROM creditos_clientes WHERE id = ?", (credito_id,), db_path=db_path)
    if credito:
        execute("UPDATE creditos_clientes SET pagado = 1, fecha_pago = ?, monto_pagado = ? WHERE id = ?",
                (fecha_pago, credito[0]['monto'], credito_id), db_path=db_path)
    else:
        execute("UPDATE creditos_clientes SET pagado = 1, fecha_pago = ? WHERE id = ?",
                (fecha_pago, credito_id), db_path=db_path)


def registrar_abono(credito_id, monto_abono, db_path=None):
    """Registra un abono parcial a un credito. Si cubre el total, marca como pagado."""
    credito = query("SELECT * FROM creditos_clientes WHERE id = ?", (credito_id,), db_path=db_path)
    if not credito:
        raise ValueError(f"Credito #{credito_id} no existe")
    credito = credito[0]

    if credito['pagado']:
        raise ValueError(f"Credito #{credito_id} ya esta pagado")

    if monto_abono <= 0:
        raise ValueError("El monto del abono debe ser mayor a 0")

    monto_pagado_actual = credito.get('monto_pagado') or 0
    nuevo_pagado = monto_pagado_actual + monto_abono
    saldo_restante = credito['monto'] - nuevo_pagado

    if saldo_restante <= 0:
        # Abono completa el pago
        execute("""
            UPDATE creditos_clientes
            SET monto_pagado = ?, pagado = 1, fecha_pago = ?
            WHERE id = ?
        """, (credito['monto'], date.today().isoformat(), credito_id), db_path=db_path)
    else:
        # Abono parcial
        execute("""
            UPDATE creditos_clientes SET monto_pagado = ? WHERE id = ?
        """, (nuevo_pagado, credito_id), db_path=db_path)

    return {
        'credito_id': credito_id,
        'abono': monto_abono,
        'total_pagado': min(nuevo_pagado, credito['monto']),
        'saldo_restante': max(0, saldo_restante),
        'completado': saldo_restante <= 0,
    }


# ── Inventario ────────────────────────────────────────────

def get_alertas_stock(db_path=None):
    return query("""
        SELECT * FROM productos WHERE stock <= stock_minimo
        ORDER BY stock ASC, nombre
    """, db_path=db_path)


def get_resumen_inventario(db_path=None):
    total = query("""
        SELECT COUNT(*) as total_skus, SUM(stock) as total_unidades,
               SUM(costo * stock) as valor_costo, SUM(precio_venta * stock) as valor_venta
        FROM productos
    """, db_path=db_path)

    por_categoria = query("""
        SELECT categoria, COUNT(*) as skus, SUM(stock) as unidades,
               SUM(costo * stock) as valor_costo, SUM(precio_venta * stock) as valor_venta
        FROM productos GROUP BY categoria ORDER BY valor_venta DESC
    """, db_path=db_path)

    return {'total': total[0] if total else {}, 'por_categoria': por_categoria}


def agregar_stock(sku, cantidad, db_path=None):
    execute("UPDATE productos SET stock = stock + ? WHERE sku = ?", (cantidad, sku), db_path=db_path)


# ── Gastos ────────────────────────────────────────────────

def registrar_gasto(fecha, categoria, monto, descripcion, pagado_por,
                    metodo_pago=None, es_inversion=0, notas=None, db_path=None):
    """Registra un nuevo gasto."""
    return execute("""
        INSERT INTO gastos (fecha, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas),
        db_path=db_path)


def registrar_gasto_parejo(fecha, categoria, monto_total, descripcion,
                           metodo_pago=None, es_inversion=0, notas=None, db_path=None):
    """Registra un gasto dividido parejo entre los 3 socios. Crea 3 registros."""
    parte = round(monto_total / 3)
    resto = monto_total - (parte * 3)
    ids = []
    for i, socio in enumerate(SOCIOS):
        m = parte + (resto if i == len(SOCIOS) - 1 else 0)
        gid = registrar_gasto(fecha, categoria, m, descripcion, socio,
                              metodo_pago, es_inversion, notas, db_path=db_path)
        ids.append(gid)
    return ids


def registrar_gasto_personalizado(fecha, categoria, montos_por_socio, descripcion,
                                  metodo_pago=None, es_inversion=0, notas=None, db_path=None):
    """Registra un gasto con montos diferentes por socio. Solo crea registros para montos > 0."""
    ids = []
    for socio, monto in montos_por_socio.items():
        if monto > 0:
            gid = registrar_gasto(fecha, categoria, monto, descripcion, socio,
                                  metodo_pago, es_inversion, notas, db_path=db_path)
            ids.append(gid)
    return ids


def editar_gasto(gasto_id, fecha=None, categoria=None, monto=None,
                 descripcion=None, pagado_por=None, metodo_pago=None, db_path=None):
    """Edita un gasto existente. Solo actualiza los campos proporcionados."""
    updates = []
    params = []
    if fecha is not None:
        updates.append("fecha = ?")
        params.append(fecha)
    if categoria is not None:
        updates.append("categoria = ?")
        params.append(categoria)
    if monto is not None:
        updates.append("monto = ?")
        params.append(monto)
    if descripcion is not None:
        updates.append("descripcion = ?")
        params.append(descripcion)
    if pagado_por is not None:
        updates.append("pagado_por = ?")
        params.append(pagado_por)
    if metodo_pago is not None:
        updates.append("metodo_pago = ?")
        params.append(metodo_pago)

    if not updates:
        return
    params.append(gasto_id)
    sql = f"UPDATE gastos SET {', '.join(updates)} WHERE id = ?"
    execute(sql, tuple(params), db_path=db_path)


def eliminar_gasto(gasto_id, db_path=None):
    """Elimina un gasto por ID."""
    execute("DELETE FROM gastos WHERE id = ?", (gasto_id,), db_path=db_path)


def get_gastos_mes(year, month, db_path=None):
    fecha_inicio = f"{year}-{month:02d}-01"
    fecha_fin = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"

    gastos = query("SELECT * FROM gastos WHERE fecha >= ? AND fecha < ? ORDER BY fecha DESC",
                   (fecha_inicio, fecha_fin), db_path=db_path)

    por_categoria = {}
    total = 0
    for g in gastos:
        cat = g['categoria']
        por_categoria[cat] = por_categoria.get(cat, 0) + g['monto']
        total += g['monto']

    return {'gastos': gastos, 'por_categoria': por_categoria, 'total': total}


def get_gastos_rango(fecha_inicio, fecha_fin, db_path=None):
    """Gastos en un rango de fechas."""
    return query("""
        SELECT * FROM gastos WHERE fecha >= ? AND fecha <= ? ORDER BY fecha DESC
    """, (fecha_inicio, fecha_fin), db_path=db_path)


# ── Productos ─────────────────────────────────────────────

def get_productos(db_path=None):
    return query("SELECT * FROM productos ORDER BY categoria, nombre", db_path=db_path)


def get_producto(sku, db_path=None):
    result = query("SELECT * FROM productos WHERE sku = ?", (sku,), db_path=db_path)
    return result[0] if result else None


def crear_producto(sku, nombre, categoria, talla, color, costo, precio_venta,
                   stock=0, stock_minimo=3, proveedor=None, notas=None, db_path=None):
    """Crea un nuevo producto."""
    execute("""
        INSERT INTO productos (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo, proveedor, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo, proveedor, notas),
        db_path=db_path)


def editar_producto(sku, nombre=None, categoria=None, talla=None, color=None,
                    costo=None, precio_venta=None, stock=None, stock_minimo=None,
                    proveedor=None, notas=None, db_path=None):
    """Edita un producto existente."""
    updates = []
    params = []
    for field, value in [('nombre', nombre), ('categoria', categoria), ('talla', talla),
                         ('color', color), ('costo', costo), ('precio_venta', precio_venta),
                         ('stock', stock), ('stock_minimo', stock_minimo),
                         ('proveedor', proveedor), ('notas', notas)]:
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        return
    params.append(sku)
    sql = f"UPDATE productos SET {', '.join(updates)} WHERE sku = ?"
    execute(sql, tuple(params), db_path=db_path)


def eliminar_producto(sku, db_path=None):
    """Elimina un producto. Falla si tiene ventas asociadas."""
    ventas = query("SELECT COUNT(*) as c FROM ventas WHERE sku = ?", (sku,), db_path=db_path)
    if ventas[0]['c'] > 0:
        raise ValueError(f"No se puede eliminar {sku}: tiene {ventas[0]['c']} ventas asociadas")
    execute("DELETE FROM productos WHERE sku = ?", (sku,), db_path=db_path)


# ── Costos Fijos ─────────────────────────────────────────

def get_costos_fijos(db_path=None):
    return query("SELECT * FROM costos_fijos ORDER BY concepto", db_path=db_path)


def crear_costo_fijo(concepto, monto_mensual, activo=1, notas=None, db_path=None):
    return execute("""
        INSERT INTO costos_fijos (concepto, monto_mensual, activo, notas)
        VALUES (?, ?, ?, ?)
    """, (concepto, monto_mensual, activo, notas), db_path=db_path)


def editar_costo_fijo(costo_id, concepto=None, monto_mensual=None, activo=None, notas=None, db_path=None):
    updates = []
    params = []
    if concepto is not None:
        updates.append("concepto = ?")
        params.append(concepto)
    if monto_mensual is not None:
        updates.append("monto_mensual = ?")
        params.append(monto_mensual)
    if activo is not None:
        updates.append("activo = ?")
        params.append(activo)
    if notas is not None:
        updates.append("notas = ?")
        params.append(notas)
    if not updates:
        return
    params.append(costo_id)
    sql = f"UPDATE costos_fijos SET {', '.join(updates)} WHERE id = ?"
    execute(sql, tuple(params), db_path=db_path)


def eliminar_costo_fijo(costo_id, db_path=None):
    execute("DELETE FROM costos_fijos WHERE id = ?", (costo_id,), db_path=db_path)


# ── Pedidos ───────────────────────────────────────────────

def get_pedidos(db_path=None):
    """Todos los pedidos, más recientes primero."""
    return query("SELECT * FROM pedidos_proveedores ORDER BY fecha_pedido DESC", db_path=db_path)


def get_pedidos_pendientes(db_path=None):
    return query("SELECT * FROM pedidos_proveedores WHERE estado NOT IN ('Completo') ORDER BY fecha_pedido DESC",
                 db_path=db_path)


def get_total_deuda_proveedores(db_path=None):
    result = query("SELECT SUM(total) as total FROM pedidos_proveedores WHERE estado = 'Pendiente'",
                   db_path=db_path)
    return result[0]['total'] or 0 if result else 0


def registrar_pedido(fecha_pedido, proveedor, descripcion, unidades, costo_unitario,
                     pagado_por=None, fecha_entrega_est=None, notas=None, db_path=None):
    """Registra un nuevo pedido a proveedor. Estado inicial: Pendiente."""
    total = unidades * costo_unitario
    return execute("""
        INSERT INTO pedidos_proveedores (fecha_pedido, proveedor, descripcion, unidades, costo_unitario, total, estado, pagado_por, fecha_entrega_est, notas)
        VALUES (?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?, ?)
    """, (fecha_pedido, proveedor, descripcion, unidades, costo_unitario, total,
          pagado_por, fecha_entrega_est, notas), db_path=db_path)


def pagar_pedido(pedido_id, pagado_por, fecha_pago=None, metodo_pago='Transferencia', db_path=None):
    """
    Marca un pedido como Pagado y registra el gasto correspondiente.
    Crea gastos según quién paga (un socio o parejo).
    """
    pedido = query("SELECT * FROM pedidos_proveedores WHERE id = ?", (pedido_id,), db_path=db_path)
    if not pedido:
        raise ValueError(f"Pedido #{pedido_id} no existe")
    pedido = pedido[0]

    if pedido['estado'] not in ('Pendiente',):
        raise ValueError(f"Pedido #{pedido_id} ya está en estado '{pedido['estado']}'")

    if fecha_pago is None:
        fecha_pago = date.today().isoformat()

    # Registrar gasto
    desc = f"Pedido #{pedido_id} — {pedido['proveedor']}: {pedido['descripcion']}"
    registrar_gasto(
        fecha=fecha_pago,
        categoria='Mercancía',
        monto=pedido['total'],
        descripcion=desc,
        pagado_por=pagado_por,
        metodo_pago=metodo_pago,
        db_path=db_path,
    )

    # Actualizar estado
    execute("UPDATE pedidos_proveedores SET estado = 'Pagado', pagado_por = ? WHERE id = ?",
            (pagado_por, pedido_id), db_path=db_path)

    return pedido


def recibir_mercancia(pedido_id, skus_cantidades, db_path=None):
    """
    Marca un pedido como Completo y agrega stock.
    skus_cantidades: lista de tuplas (sku, cantidad)
    """
    pedido = query("SELECT * FROM pedidos_proveedores WHERE id = ?", (pedido_id,), db_path=db_path)
    if not pedido:
        raise ValueError(f"Pedido #{pedido_id} no existe")
    pedido = pedido[0]

    if pedido['estado'] == 'Pendiente':
        raise ValueError(f"Pedido #{pedido_id} aún no está pagado")

    for sku, cantidad in skus_cantidades:
        agregar_stock(sku, cantidad, db_path=db_path)

    execute("UPDATE pedidos_proveedores SET estado = 'Completo' WHERE id = ?",
            (pedido_id,), db_path=db_path)

    return pedido


def editar_pedido(pedido_id, proveedor=None, descripcion=None, unidades=None,
                  costo_unitario=None, estado=None, notas=None, db_path=None):
    """Edita un pedido existente."""
    updates = []
    params = []
    for field, value in [('proveedor', proveedor), ('descripcion', descripcion),
                         ('unidades', unidades), ('costo_unitario', costo_unitario),
                         ('estado', estado), ('notas', notas)]:
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    # Recalcular total si cambian unidades o costo
    if unidades is not None or costo_unitario is not None:
        pedido = query("SELECT * FROM pedidos_proveedores WHERE id = ?", (pedido_id,), db_path=db_path)
        if pedido:
            p = pedido[0]
            new_u = unidades if unidades is not None else p['unidades']
            new_c = costo_unitario if costo_unitario is not None else p['costo_unitario']
            updates.append("total = ?")
            params.append(new_u * new_c)
    if not updates:
        return
    params.append(pedido_id)
    sql = f"UPDATE pedidos_proveedores SET {', '.join(updates)} WHERE id = ?"
    execute(sql, tuple(params), db_path=db_path)


def eliminar_pedido(pedido_id, db_path=None):
    """Elimina un pedido."""
    execute("DELETE FROM pedidos_proveedores WHERE id = ?", (pedido_id,), db_path=db_path)
