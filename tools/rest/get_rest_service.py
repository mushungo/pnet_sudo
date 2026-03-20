# tools/rest/get_rest_service.py
"""
Obtiene los detalles de un TI de integración REST/WebService de PeopleNet.

Incluye: definición del TI, todos sus items (campos y métodos),
argumentos de los métodos, y reglas LN4 asociadas.

Uso:
    python -m tools.rest.get_rest_service "CCO_API_WS_REST"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_rest_service_details(id_ti):
    """Obtiene los detalles completos de un TI de integración.

    Consulta: M4RCH_TIS, M4RCH_ITEMS, M4RCH_ITEM_ARGS, M4RCH_RULES3.

    Args:
        id_ti: Identificador del TI de integración.

    Returns:
        dict con la definición completa o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # CSTYPE mapping
            cstype_map = {
                0: "Physical", 1: "Logical", 2: "Virtual",
                3: "Temporary", 7: "No-BDL"
            }

            # Item type mapping
            item_type_map = {
                1: "Property", 2: "Field", 3: "Method",
                4: "Concept", 5: "Total"
            }

            # 1. TI principal
            cursor.execute(
                "SELECT ID_TI, ID_T3, ID_NODE, CSTYPE, READ_OBJECT, WRITE_OBJECT "
                "FROM M4RCH_TIS WHERE ID_TI = ?",
                id_ti
            )
            ti_row = cursor.fetchone()
            if not ti_row:
                return {"status": "not_found", "message": f"No se encontró el TI '{id_ti}'."}

            result = {
                "id_ti": ti_row.ID_TI,
                "channel": ti_row.ID_T3,
                "node": ti_row.ID_NODE,
                "cstype": ti_row.CSTYPE,
                "cstype_name": cstype_map.get(ti_row.CSTYPE, f"Unknown({ti_row.CSTYPE})"),
                "read_object": ti_row.READ_OBJECT,
                "write_object": ti_row.WRITE_OBJECT,
            }

            # 2. Items (campos y métodos)
            cursor.execute(
                "SELECT ID_ITEM, ITEM_TYPE, ID_M4_TYPE, SCOPE_TYPE "
                "FROM M4RCH_ITEMS WHERE ID_TI = ? ORDER BY ITEM_TYPE, ID_ITEM",
                id_ti
            )
            items = []
            method_names = []
            for row in cursor.fetchall():
                item = {
                    "id_item": row.ID_ITEM,
                    "item_type": row.ITEM_TYPE,
                    "item_type_name": item_type_map.get(row.ITEM_TYPE, f"Unknown({row.ITEM_TYPE})"),
                    "m4_type": row.ID_M4_TYPE,
                    "scope_type": row.SCOPE_TYPE,
                }
                items.append(item)
                if row.ITEM_TYPE == 3:
                    method_names.append(row.ID_ITEM)
            result["items"] = items

            # 3. Argumentos de los métodos
            if method_names:
                placeholders = ",".join(["?"] * len(method_names))
                cursor.execute(
                    f"SELECT ID_ITEM, ID_ARGUMENT, POSITION, ID_M4_TYPE, ID_ARGUMENT_TYPE "
                    f"FROM M4RCH_ITEM_ARGS "
                    f"WHERE ID_TI = ? AND ID_ITEM IN ({placeholders}) "
                    f"ORDER BY ID_ITEM, POSITION",
                    id_ti, *method_names
                )
                args_by_method = {}
                for row in cursor.fetchall():
                    if row.ID_ITEM not in args_by_method:
                        args_by_method[row.ID_ITEM] = []
                    args_by_method[row.ID_ITEM].append({
                        "id_argument": row.ID_ARGUMENT,
                        "position": row.POSITION,
                        "m4_type": row.ID_M4_TYPE,
                        "argument_type": row.ID_ARGUMENT_TYPE,
                        "is_output": row.ID_ARGUMENT_TYPE == 2,
                    })
                result["method_args"] = args_by_method

            # 4. Reglas LN4 (código fuente de los métodos)
            cursor.execute(
                "SELECT ID_ITEM, SOURCE_CODE "
                "FROM M4RCH_RULES3 "
                "WHERE ID_TI = ? AND SOURCE_CODE IS NOT NULL "
                "ORDER BY ID_ITEM",
                id_ti
            )
            result["rules"] = []
            for row in cursor.fetchall():
                source = row.SOURCE_CODE
                if source and len(source) > 2000:
                    source = source[:2000] + "... [truncated]"
                result["rules"].append({
                    "id_item": row.ID_ITEM,
                    "source_code": source,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.rest.get_rest_service \"ID_TI\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_rest_service_details(sys.argv[1]), indent=2, default=str))
