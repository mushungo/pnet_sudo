# tools/dependencies/dependency_maps.py
"""
Diccionarios de decodificación para los campos clasificadores de dependencias.

Fuente: tablas de dependencias del repositorio de metadatos de PeopleNet.
  - M4RCH_INTERNAL_DEP  -> DEPENDENCE_TP (mismo TI)
  - M4RCH_EXTERNAL_DEP  -> dependencias cruzadas entre TIs
  - M4RCH_CHANNEL_DEP   -> dependencias cruzadas entre canales (T3)
"""


# --- DEPENDENCE_TP (M4RCH_INTERNAL_DEP) -> Tipo de dependencia ---
DEPENDENCE_TYPE_MAP = {
    1: "call",
    2: "read",
    3: "write",
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
