# =============================================================================
# ln4_lsp/tools/export_builtins.py — Exportar catálogo de funciones LN4 a JSON
# =============================================================================
# Genera ln4_lsp/data/ln4_builtins.json con todas las funciones built-in
# y sus argumentos, consultando la BD del repositorio PeopleNet.
#
# Uso:
#   python -m ln4_lsp.tools.export_builtins
#
# Solo se necesita ejecutar una vez (o cuando cambien las funciones en el repo).
# =============================================================================

import sys
import os
import json
from decimal import Decimal
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def _to_int(val):
    """Convierte Decimal/int/None a int o None (para JSON serialization)."""
    if val is None:
        return None
    return int(val)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder que convierte Decimal a int/float."""
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super().default(o)


def export_builtins():
    """Exporta el catálogo completo de funciones LN4 a JSON."""

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ln4_builtins.json")

    with db_connection() as conn:
        cursor = conn.cursor()

        # -- Funciones --
        print("Consultando funciones LN4...")
        cursor.execute(
            "SELECT ID_LN4_FUNCTION, N_LN4_FUNCTION, ITEM, "
            "VARIABLE_ARGUMENTS, FUNCTION_LEVEL, ID_FUNC_GROUP "
            "FROM M4RCH_LN4_FUNCTION"
        )
        functions_raw = cursor.fetchall()

        # -- Comentarios --
        print("Consultando comentarios...")
        cursor.execute(
            "SELECT ID_LN4_FUNCTION, COMENTESP, COMENTENG "
            "FROM M4RCH_LN4_FUNCTIO1"
        )
        comments = {}
        for row in cursor.fetchall():
            comments[row.ID_LN4_FUNCTION] = {
                "esp": (row.COMENTESP or "").strip(),
                "eng": (row.COMENTENG or "").strip(),
            }

        # -- Argumentos --
        print("Consultando argumentos...")
        cursor.execute(
            "SELECT ID_LN4_FUNCTION, N_LN4_ARGUMENTS, "
            "POSITION, ID_M4_TYPE, ID_ARGUMENT_TYPE, OPTIONAL "
            "FROM M4RCH_LN4_FUNC_ARG ORDER BY POSITION"
        )
        arguments = defaultdict(list)
        for row in cursor.fetchall():
            arguments[row.ID_LN4_FUNCTION].append({
                "name": (row.N_LN4_ARGUMENTS or "").strip(),
                "position": _to_int(row.POSITION),
                "m4_type": _to_int(row.ID_M4_TYPE),
                "arg_type": _to_int(row.ID_ARGUMENT_TYPE),
                "optional": bool(row.OPTIONAL) if row.OPTIONAL is not None else False,
            })

        # -- Grupos --
        print("Consultando grupos...")
        cursor.execute(
            "SELECT ID_FUNC_GROUP, DESCRIPCIONESP, DESCRIPCIONENG "
            "FROM M4RCH_FUNC_GROUPS"
        )
        groups = {}
        for row in cursor.fetchall():
            groups[row.ID_FUNC_GROUP] = (row.DESCRIPCIONESP or row.DESCRIPCIONENG or "").strip()

        # -- Tipos M4 --
        print("Consultando tipos M4...")
        cursor.execute(
            "SELECT ID_M4_TYPE, N_M4_TYPEESP, N_M4_TYPEENG "
            "FROM M4RDC_LU_M4_TYPES"
        )
        m4_types = {}
        for row in cursor.fetchall():
            m4_types[str(_to_int(row.ID_M4_TYPE))] = (row.N_M4_TYPEESP or row.N_M4_TYPEENG or "").strip()

    # -- Construir catálogo JSON --
    print("Construyendo catálogo...")
    catalog = {
        "version": "1.0",
        "description": "LN4 built-in function catalog exported from PeopleNet repository",
        "m4_types": m4_types,
        "groups": groups,
        "functions": {},
    }

    for func in functions_raw:
        func_id = func.ID_LN4_FUNCTION
        func_name = (func.N_LN4_FUNCTION or "").strip().upper()
        func_args = arguments.get(func_id, [])
        func_comment = comments.get(func_id, {"esp": "", "eng": ""})
        var_args = bool(func.VARIABLE_ARGUMENTS) if func.VARIABLE_ARGUMENTS is not None else False

        # Calcular aridad
        required_args = sum(1 for a in func_args if not a["optional"])
        max_args = len(func_args) if not var_args else None  # None = ilimitado

        catalog["functions"][func_name] = {
            "id": func_id,
            "name": func_name,
            "group": func.ID_FUNC_GROUP,
            "group_name": groups.get(func.ID_FUNC_GROUP, ""),
            "level": _to_int(func.FUNCTION_LEVEL),
            "variable_arguments": var_args,
            "comment": func_comment.get("esp") or func_comment.get("eng", ""),
            "min_args": required_args,
            "max_args": max_args,
            "arguments": func_args,
        }

    # -- Escribir JSON --
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)

    func_count = len(catalog["functions"])
    print(f"Exportado: {func_count} funciones -> {output_path}")
    return output_path


if __name__ == "__main__":
    export_builtins()
