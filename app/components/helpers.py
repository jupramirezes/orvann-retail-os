"""Utilidades de formateo y helpers para ORVANN Retail OS."""


def fmt_cop(valor):
    """Formatea un número como pesos colombianos: $1.234.567"""
    if valor is None:
        return "$0"
    if valor < 0:
        return f"-${abs(valor):,.0f}".replace(",", ".")
    return f"${valor:,.0f}".replace(",", ".")


def fmt_pct(valor):
    """Formatea un porcentaje: 50.7%"""
    if valor is None:
        return "0%"
    return f"{valor:.1f}%"


def color_stock(stock, minimo=3):
    """Retorna emoji/indicador según nivel de stock."""
    if stock <= 0:
        return "🔴"
    elif stock <= minimo:
        return "🟡"
    return "🟢"


def color_pe(progreso_pct):
    """Color para barra de punto de equilibrio."""
    if progreso_pct >= 100:
        return "green"
    elif progreso_pct >= 50:
        return "orange"
    return "red"


CATEGORIAS_GASTO = [
    'Arriendo',
    'Servicios (Agua, Luz, Gas)',
    'Internet',
    'Nómina/Vendedor',
    'Publicidad/Marketing',
    'Empaque (Bolsas, Etiquetas)',
    'Aseo/Mantenimiento',
    'Transporte',
    'Ilustraciones/Diseño',
    'Dotación local',
    'Mercancía',
    'Imprevistos',
    'Comisiones datáfono',
    'Contador',
    'Otro',
]

METODOS_PAGO = ['Efectivo', 'Transferencia', 'Datáfono', 'Crédito']
VENDEDORES = ['JP', 'KATHE', 'ANDRES']
