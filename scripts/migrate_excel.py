"""Migra datos desde Control_Operativo_Orvann.xlsx a SQLite."""
import sqlite3
import os
import re
from datetime import datetime, date

import openpyxl

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'Control_Operativo_Orvann.xlsx')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orvann.db')

# Socios
SOCIOS = ['JP', 'KATHE', 'ANDRES']
SOCIO_RENAME = {'MILE': 'ANDRES'}

TALLAS_CONOCIDAS = ['S', 'M', 'L', 'XL', '2XL']

# Fecha de apertura de la tienda
FECHA_APERTURA = '2026-02-15'


def fix_socio(nombre):
    """Renombra MILE -> ANDRES."""
    if nombre:
        return SOCIO_RENAME.get(nombre.strip(), nombre.strip())
    return nombre


def parse_producto(nombre):
    """Extrae categoria, talla y color del nombre del producto."""
    if not nombre:
        return None, None, None

    nombre = nombre.strip()
    categoria = None
    talla = None
    color = None

    nombre_lower = nombre.lower()
    if nombre_lower.startswith('camisa'):
        categoria = 'Camisa'
    elif nombre_lower.startswith('hoodie'):
        categoria = 'Hoodie'
    elif nombre_lower.startswith('chompa'):
        categoria = 'Chompa'
    elif nombre_lower.startswith('buzo'):
        categoria = 'Buzo'
    elif nombre_lower.startswith('chaqueta'):
        categoria = 'Chaqueta'
    elif nombre_lower.startswith('jogger'):
        categoria = 'Jogger'
    elif nombre_lower.startswith('sudadera'):
        categoria = 'Sudadera'
    elif nombre_lower.startswith('pantaloneta'):
        categoria = 'Pantaloneta'

    parts = nombre.split()
    talla_idx = None
    for i, part in enumerate(parts):
        if part.upper() in TALLAS_CONOCIDAS:
            talla = part.upper()
            talla_idx = i
            break

    if talla_idx is not None and talla_idx + 1 < len(parts):
        color = ' '.join(parts[talla_idx + 1:]).strip()
    if color == '':
        color = None

    return categoria, talla, color


def to_date_str(val):
    """Convierte valor de celda a string de fecha YYYY-MM-DD."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, date):
        return val.strftime('%Y-%m-%d')
    return str(val)


def migrate_productos(ws, conn):
    """Migra hoja Inventario -> tabla productos."""
    c = conn.cursor()
    count = 0
    total_stock = 0
    seen_skus = set()

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, values_only=False):
        vals = {cell.column_letter: cell.value for cell in row}
        sku = vals.get('A')
        if sku is None:
            break

        sku = str(sku).strip()
        nombre = str(vals.get('B', '')).strip()
        costo = float(vals.get('C', 0) or 0)
        precio_venta = float(vals.get('D', 0) or 0)
        stock = int(float(vals.get('G', 0) or 0))
        notas = vals.get('H')

        categoria, talla, color = parse_producto(nombre)

        # Manejar SKUs duplicados (ej: SUD-NEG-L aparece 3 veces)
        if sku in seen_skus:
            _, real_talla, _ = parse_producto(nombre)
            if real_talla:
                base_sku = sku.rsplit('-', 1)[0] if '-' in sku else sku
                new_sku = f"{base_sku}-{real_talla}"
                if new_sku in seen_skus:
                    new_sku = f"{sku}-{real_talla}"
                sku = new_sku

        seen_skus.add(sku)

        c.execute("""
            INSERT OR REPLACE INTO productos
            (sku, nombre, categoria, talla, color, costo, precio_venta, stock, stock_minimo, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 3, ?)
        """, (sku, nombre, categoria, talla, color, costo, precio_venta, stock, notas))

        count += 1
        total_stock += stock

    conn.commit()
    print(f"  Productos: {count} SKUs, {total_stock} unidades totales")
    return count, total_stock


def migrate_ventas(ws, conn):
    """Migra hoja Ventas -> tabla ventas + creditos_clientes."""
    c = conn.cursor()
    count = 0
    creditos = 0

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        vals = {cell.column_letter: cell.value for cell in row}
        fecha = vals.get('A')
        if fecha is None:
            break

        sku = str(vals.get('B', '')).strip()
        precio_venta = float(vals.get('E', 0) or 0)
        metodo_pago = str(vals.get('F', '')).strip()
        cliente = vals.get('G')
        notas = vals.get('H')

        if cliente:
            cliente = str(cliente).strip()

        if 'cr' in metodo_pago.lower():
            metodo_pago = 'Crédito'
        elif 'transf' in metodo_pago.lower():
            metodo_pago = 'Transferencia'
        elif 'dat' in metodo_pago.lower():
            metodo_pago = 'Datáfono'
        elif 'efect' in metodo_pago.lower():
            metodo_pago = 'Efectivo'

        fecha_str = to_date_str(fecha)
        total = precio_venta

        c.execute("""
            INSERT INTO ventas (fecha, sku, cantidad, precio_unitario, descuento_pct, total, metodo_pago, cliente, notas)
            VALUES (?, ?, 1, ?, 0, ?, ?, ?, ?)
        """, (fecha_str, sku, precio_venta, total, metodo_pago, cliente, notas))

        venta_id = c.lastrowid
        count += 1

        if metodo_pago == 'Crédito' and cliente:
            c.execute("""
                INSERT INTO creditos_clientes (venta_id, cliente, monto, fecha_credito, pagado, notas)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (venta_id, cliente, total, fecha_str, notas))
            creditos += 1

    conn.commit()
    print(f"  Ventas: {count} registros, {creditos} créditos creados")
    return count, creditos


def migrate_gastos(ws, conn):
    """
    Migra hoja Gastos -> tabla gastos.
    CADA FILA del Excel es un pago REAL de un socio.
    NO se deduplica nada.
    Solo se importan filas donde hay fecha (col A) y monto (col C).
    Columnas I-N son resúmenes del Excel y se ignoran.
    """
    c = conn.cursor()
    count = 0
    totals_by_socio = {}

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        vals = {cell.column_letter: cell.value for cell in row}
        fecha = vals.get('A')
        monto = vals.get('C')

        # Solo importar filas con fecha Y monto
        if fecha is None or monto is None:
            continue

        monto = float(monto)
        if monto == 0:
            continue

        fecha_str = to_date_str(fecha)
        categoria = str(vals.get('B', '')).strip() if vals.get('B') else ''
        descripcion = str(vals.get('D', '')).strip() if vals.get('D') else ''
        metodo_pago = str(vals.get('E', '')).strip() if vals.get('E') else None
        responsable = fix_socio(str(vals.get('F', '')).strip()) if vals.get('F') else None
        notas = str(vals.get('G', '')).strip() if vals.get('G') else None
        if notas == 'None' or notas == '':
            notas = None

        # Gastos antes de la apertura (2026-02-15) son inversión
        es_inversion = 1 if fecha_str and fecha_str < FECHA_APERTURA else 0

        # Default a JP si no hay responsable (ORVANN no es socio válido)
        pagado_por = responsable if responsable in ('JP', 'KATHE', 'ANDRES') else 'JP'

        c.execute("""
            INSERT INTO gastos (fecha, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha_str, categoria, monto, descripcion, metodo_pago, pagado_por, es_inversion, notas))
        count += 1

        # Track totals per socio
        totals_by_socio[pagado_por] = totals_by_socio.get(pagado_por, 0) + monto

    conn.commit()
    print(f"  Gastos: {count} registros (cada fila del Excel = un pago real)")
    for socio, total in sorted(totals_by_socio.items()):
        print(f"    {socio}: ${total:,.0f}")
    print(f"    TOTAL: ${sum(totals_by_socio.values()):,.0f}")
    return count


def migrate_costos_fijos(ws, conn):
    """Migra hoja Costos Fijos -> tabla costos_fijos."""
    c = conn.cursor()
    count = 0
    total = 0

    for row in ws.iter_rows(min_row=4, max_row=ws.max_row, values_only=False):
        vals = {cell.column_letter: cell.value for cell in row}
        concepto = vals.get('A')
        monto = vals.get('B')

        if concepto is None or monto is None:
            if concepto and 'total' in str(concepto).lower():
                continue
            if monto is None:
                continue

        concepto = str(concepto).strip()
        if concepto.upper() == 'TOTAL' or not concepto:
            continue

        monto = float(monto or 0)
        notas = str(vals.get('C', '')).strip() if vals.get('C') else None
        if notas == 'None':
            notas = None

        c.execute("""
            INSERT INTO costos_fijos (concepto, monto_mensual, activo, notas)
            VALUES (?, ?, 1, ?)
        """, (concepto, monto, notas))
        count += 1
        total += monto

    conn.commit()
    print(f"  Costos fijos: {count} rubros, total ${total:,.0f}")
    return count, total


def migrate_pedidos(ws, conn):
    """Migra hoja Pedidos Proveedores -> tabla pedidos_proveedores.
    Corrige fechas 2025-02-XX -> 2026-02-XX (typos del Excel)."""
    c = conn.cursor()
    count = 0

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        vals = {cell.column_letter: cell.value for cell in row}
        fecha = vals.get('A')
        if fecha is None:
            break

        proveedor = str(vals.get('B', '')).strip()
        descripcion = str(vals.get('C', '')).strip()
        unidades = int(float(vals.get('D', 0) or 0))
        costo_unitario = float(vals.get('E', 0) or 0)
        total = float(vals.get('F', 0) or 0)
        estado = str(vals.get('G', 'Pendiente')).strip()
        fecha_pago = to_date_str(vals.get('H'))
        notas = str(vals.get('I', '')).strip() if vals.get('I') else None
        if notas == 'None':
            notas = None

        if notas:
            notas = notas.replace('MILE', 'ANDRES')

        fecha_str = to_date_str(fecha)

        # TAREA 4: Fix 2025-02-XX -> 2026-02-XX (Excel typo)
        if fecha_str and fecha_str.startswith('2025-02'):
            fecha_str = '2026' + fecha_str[4:]

        c.execute("""
            INSERT INTO pedidos_proveedores
            (fecha_pedido, proveedor, descripcion, unidades, costo_unitario, total, estado, fecha_entrega_est, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha_str, proveedor, descripcion, unidades, costo_unitario, total, estado, fecha_pago, notas))
        count += 1

    conn.commit()
    print(f"  Pedidos: {count} registros")
    return count


def run_migration(excel_path=None, db_path=None):
    """Ejecuta la migración completa."""
    if excel_path is None:
        excel_path = EXCEL_PATH
    if db_path is None:
        db_path = DB_PATH

    print(f"Migrando desde: {os.path.abspath(excel_path)}")
    print(f"Base de datos: {os.path.abspath(db_path)}")
    print()

    from scripts.create_db import create_tables
    create_tables(db_path)

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    conn = sqlite3.connect(db_path)

    try:
        print("Migrando datos...")
        print()

        ws = wb['Inventario']
        n_prod, total_stock = migrate_productos(ws, conn)

        ws = wb['Ventas']
        n_ventas, n_creditos = migrate_ventas(ws, conn)

        ws = wb['Gastos']
        n_gastos = migrate_gastos(ws, conn)

        ws = wb['Costos Fijos']
        n_cf, total_cf = migrate_costos_fijos(ws, conn)

        ws = wb['Pedidos Proveedores']
        n_pedidos = migrate_pedidos(ws, conn)

        print()
        print("=" * 50)
        print("RESUMEN DE MIGRACIÓN")
        print("=" * 50)
        print(f"  Productos:     {n_prod} SKUs ({total_stock} unidades)")
        print(f"  Ventas:        {n_ventas} registros")
        print(f"  Créditos:      {n_creditos} registros")
        print(f"  Gastos:        {n_gastos} registros (cada fila = pago real)")
        print(f"  Costos fijos:  {n_cf} rubros (${total_cf:,.0f}/mes)")
        print(f"  Pedidos:       {n_pedidos} registros")
        print("=" * 50)

        return {
            'productos': n_prod,
            'stock_total': total_stock,
            'ventas': n_ventas,
            'creditos': n_creditos,
            'gastos': n_gastos,
            'costos_fijos': n_cf,
            'total_cf': total_cf,
            'pedidos': n_pedidos,
        }
    finally:
        conn.close()
        wb.close()


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    run_migration()
