# tools/m4object/m4object_maps.py
"""
Diccionarios de decodificación para los campos clasificadores de M4Objects.

Fuente: tablas de lookup del repositorio de metadatos de PeopleNet.
  - M4RCH_LU_EXE_TYPE   -> CS_EXE_TYPE
  - M4RCH_LU_STREAM_TP  -> ID_STREAM_TYPE
  - M4RCH_LU_CSTYPE     -> ID_CSTYPE (de items)
  - M4RCH_LU_NODES_TP   -> NODES_TYPE
  - M4RCH_LU_SLCBHV_TP  -> ID_SLICE_BHVR_TYPE
  - M4RCH_LU_SLC_SPLTP  -> ID_SLICE_SPLIT_TP
"""


# --- CS_EXE_TYPE (M4RCH_T3S) -> Modo de ejecución C/S del canal ---
EXE_TYPE_MAP = {
    0: "OLTP",
    1: "Proxy",
    2: "Delta",
}


# --- ID_STREAM_TYPE (M4RCH_T3S) -> Tipo de stream/objeto del canal ---
STREAM_TYPE_MAP = {
    1: "Normal",
    2: "Cache",
    3: "Sistema",
    4: "Meta",
    5: "Nómina",
    6: "Valores aplicados",
    7: "Cuota",
}


# --- ID_CSTYPE (M4RCH_ITEMS) -> Tipo C/S del ítem ---
# Nota: en conectores (M4RCH_CONCTOR_ITEM) el ID_CSTYPE tiene significado
# diferente (2=ejecución, 3=parámetro). Este mapeo es solo para ítems.
ITEM_CSTYPE_MAP = {
    1: "Parte cliente",
    2: "Parte servidor",
    3: "Parte completa",
    7: "Ambas partes (sinc.)",
}


# --- NODES_TYPE (M4RCH_NODES) -> Tipo de nodo ---
# Genéricos (0-25), Nómina (100-199), Contabilidad (120-135),
# Información (201-202), Consultas (301), VAS (700)
NODES_TYPE_MAP = {
    -1: "Sin tipo (-1)",
    0: "Genérico",
    1: "Grupo",
    2: "Detail1",
    3: "Detail1 (bis)",
    4: "Base",
    5: "Pivote origen",
    6: "Pivote destino",
    7: "Tabla origen",
    8: "Tabla destino",
    9: "Otro detalle",
    15: "Consulta nómina: auxiliar",
    16: "Consulta nómina: pagas",
    17: "Auxiliar info. concepto final",
    18: "Pivotado corto a largo",
    19: "Acumulado lectura corto",
    20: "Pivote final columnas fijas",
    21: "Totalización de acumulado",
    22: "Pivote consulta nómina",
    24: "Exportación",
    25: "Filtrado de datos",
    100: "Nómina: cálculo",
    101: "Nómina: lectura acumulado",
    102: "Nómina: acumulado",
    103: "Nómina: diferencia",
    104: "Nómina: revisión",
    105: "Nómina: principal",
    106: "Nómina: auxiliar",
    107: "Entidad legal",
    108: "Moneda legal",
    109: "Moneda de RRHH",
    110: "Nómina: lectura AC",
    111: "Nómina: cálculo AC",
    112: "Nómina: max. fecha localización",
    113: "Nómina: max. fecha de paga",
    114: "Periodo de RH",
    115: "Fechas",
    116: "Roles",
    120: "Contabilidad (cálculo cuenta)",
    121: "Contabilidad",
    122: "Contabilidad",
    123: "Contabilidad",
    124: "Contabilidad",
    125: "Contabilidad (lectura acum. periodo)",
    126: "Contabilidad",
    127: "Contabilidad",
    128: "Contabilidad",
    129: "Contabilidad",
    130: "Contabilidad (lectura acum. rol)",
    135: "Uso funcional",
    199: "Pagos atrasados",
    201: "Cabecera de información",
    202: "Principal de información",
    301: "Auxiliar de consulta",
    700: "Valor aplicado interno (VAS)",
}


# --- Conectores: CONNECTION_TYPE (M4RCH_CONNECTORS) ---
CONNECTION_TYPE_MAP = {
    1: "call",
    3: "self/bidirectional",
}


# --- Conectores: PRECEDENCE_TYPE (M4RCH_CONCTOR_ITEM) ---
PRECEDENCE_TYPE_MAP = {
    1: "before",
    2: "after",
}


# --- Conectores: CSTYPE de conector (M4RCH_CONCTOR_ITEM) ---
# Diferente del CSTYPE de ítems
CONNECTOR_CSTYPE_MAP = {
    2: "execution",
    3: "parameter",
}


# --- ID_SLICE_BHVR_TYPE (M4RCH_ITEMS / M4RCH_DMD_COMPNTS) -> Tipo de comportamiento de tramo ---
SLICE_BHVR_TYPE_MAP = {
    1: "Valor base",
    2: "Valor final",
    3: "Unidad",
    4: "Incidencia",
    5: "Valor final por periodo",
}


# --- ID_SLICE_SPLIT_TP (M4RCH_ITEMS) -> Tipo de partición de tramo ---
SLICE_SPLIT_TYPE_MAP = {
    1: "Lineal",
    2: "No lineal",
    3: "Sin tramos",
}


def decode(value, mapping, default_fmt="({})"):
    """Decodifica un valor numérico usando el mapeo proporcionado.

    Args:
        value: Valor numérico (puede ser Decimal, int, o None).
        mapping: Diccionario de mapeo {int: str}.
        default_fmt: Formato para valores desconocidos.

    Returns:
        str decodificado, o None si el valor es None.
    """
    if value is None:
        return None
    key = int(value)
    return mapping.get(key, default_fmt.format(key))
