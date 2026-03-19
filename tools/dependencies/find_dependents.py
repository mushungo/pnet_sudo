# tools/dependencies/find_dependents.py
"""
Análisis de impacto: dado un TI + ITEM, busca todas las dependencias
que lo referencian (quién depende de este item).

Busca en las tres tablas de dependencias:
- INTERNAL_DEP: dentro del mismo TI
- EXTERNAL_DEP: desde otros TIs
- CHANNEL_DEP: desde otros canales (T3)

Uso:
    python -m tools.dependencies.find_dependents "ID_TI" "ID_ITEM"
    python -m tools.dependencies.find_dependents "ID_TI" "ID_ITEM" --direction both
    python -m tools.dependencies.find_dependents "ID_TI" "ID_ITEM" --direction uses
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# Mapeo de tipos de dependencia
DEPENDENCE_TYPE_MAP = {
    1: "call",
    2: "read",
    3: "write",
}


def find_dependents(id_ti, id_item, direction="dependents"):
    """Busca dependencias de un item en las tres tablas de dependencias.

    Args:
        id_ti: Identificador del TI.
        id_item: Identificador del item.
        direction: "dependents" (quién depende de mí), "uses" (de quién dependo yo),
                   o "both" (ambas direcciones).

    Returns:
        dict con las dependencias encontradas en cada tabla.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            result = {
                "id_ti": id_ti,
                "id_item": id_item,
                "direction": direction,
                "internal": [],
                "external": [],
                "channel": [],
            }

            # --- INTERNAL_DEP (mismo TI) ---
            if direction in ("dependents", "both"):
                cursor.execute(
                    "SELECT ID_TI, ID_ITEM, ID_RULE, DEPENDENCE_TP, "
                    "DT_START, DT_END "
                    "FROM M4RCH_INTERNAL_DEP "
                    "WHERE ID_TI = ? AND ID_ITEM_USED = ? "
                    "ORDER BY ID_ITEM",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["internal"].append({
                        "id_ti": row.ID_TI,
                        "id_item": row.ID_ITEM,
                        "id_rule": row.ID_RULE,
                        "dep_type": DEPENDENCE_TYPE_MAP.get(row.DEPENDENCE_TP, str(row.DEPENDENCE_TP)),
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "internal",
                        "relation": "depends_on_me",
                    })

            if direction in ("uses", "both"):
                cursor.execute(
                    "SELECT ID_ITEM_USED, ID_RULE, DEPENDENCE_TP, "
                    "DT_START, DT_END "
                    "FROM M4RCH_INTERNAL_DEP "
                    "WHERE ID_TI = ? AND ID_ITEM = ? "
                    "ORDER BY ID_ITEM_USED",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["internal"].append({
                        "id_ti": id_ti,
                        "id_item_used": row.ID_ITEM_USED,
                        "id_rule": row.ID_RULE,
                        "dep_type": DEPENDENCE_TYPE_MAP.get(row.DEPENDENCE_TP, str(row.DEPENDENCE_TP)),
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "internal",
                        "relation": "i_use",
                    })

            # --- EXTERNAL_DEP (otros TIs) ---
            if direction in ("dependents", "both"):
                cursor.execute(
                    "SELECT ID_TI, ID_ITEM, ID_RULE, ALIAS, REAL_ALIAS, "
                    "DT_START, DT_END "
                    "FROM M4RCH_EXTERNAL_DEP "
                    "WHERE ID_TI_USED = ? AND ID_ITEM_USED = ? "
                    "ORDER BY ID_TI, ID_ITEM",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["external"].append({
                        "id_ti": row.ID_TI,
                        "id_item": row.ID_ITEM,
                        "id_rule": row.ID_RULE,
                        "alias": row.ALIAS,
                        "real_alias": row.REAL_ALIAS,
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "external",
                        "relation": "depends_on_me",
                    })

            if direction in ("uses", "both"):
                cursor.execute(
                    "SELECT ID_TI_USED, ID_ITEM_USED, ID_RULE, ALIAS, REAL_ALIAS, "
                    "DT_START, DT_END "
                    "FROM M4RCH_EXTERNAL_DEP "
                    "WHERE ID_TI = ? AND ID_ITEM = ? "
                    "ORDER BY ID_TI_USED, ID_ITEM_USED",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["external"].append({
                        "id_ti_used": row.ID_TI_USED,
                        "id_item_used": row.ID_ITEM_USED,
                        "id_rule": row.ID_RULE,
                        "alias": row.ALIAS,
                        "real_alias": row.REAL_ALIAS,
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "external",
                        "relation": "i_use",
                    })

            # --- CHANNEL_DEP (otros canales) ---
            if direction in ("dependents", "both"):
                cursor.execute(
                    "SELECT ID_TI, ID_ITEM, ID_T3_USED, ID_NODE_USED, "
                    "ID_NODE_T3_USED, DT_START, DT_END "
                    "FROM M4RCH_CHANNEL_DEP "
                    "WHERE ID_TI_USED = ? AND ID_ITEM_USED = ? "
                    "ORDER BY ID_TI, ID_ITEM",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["channel"].append({
                        "id_ti": row.ID_TI,
                        "id_item": row.ID_ITEM,
                        "id_t3_used": row.ID_T3_USED,
                        "id_node_used": row.ID_NODE_USED,
                        "id_node_t3_used": row.ID_NODE_T3_USED,
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "channel",
                        "relation": "depends_on_me",
                    })

            if direction in ("uses", "both"):
                cursor.execute(
                    "SELECT ID_TI_USED, ID_ITEM_USED, ID_T3_USED, ID_NODE_USED, "
                    "ID_NODE_T3_USED, DT_START, DT_END "
                    "FROM M4RCH_CHANNEL_DEP "
                    "WHERE ID_TI = ? AND ID_ITEM = ? "
                    "ORDER BY ID_TI_USED, ID_ITEM_USED",
                    id_ti, id_item
                )
                for row in cursor.fetchall():
                    result["channel"].append({
                        "id_ti_used": row.ID_TI_USED,
                        "id_item_used": row.ID_ITEM_USED,
                        "id_t3_used": row.ID_T3_USED,
                        "id_node_used": row.ID_NODE_USED,
                        "id_node_t3_used": row.ID_NODE_T3_USED,
                        "dt_start": row.DT_START,
                        "dt_end": row.DT_END,
                        "scope": "channel",
                        "relation": "i_use",
                    })

            # Resumen
            result["summary"] = {
                "internal_count": len([d for d in result["internal"]]),
                "external_count": len([d for d in result["external"]]),
                "channel_count": len([d for d in result["channel"]]),
                "total": len(result["internal"]) + len(result["external"]) + len(result["channel"]),
            }

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Análisis de impacto: busca dependencias de un TI+ITEM en PeopleNet."
    )
    parser.add_argument("id_ti", help="Identificador del TI")
    parser.add_argument("id_item", help="Identificador del item")
    parser.add_argument(
        "--direction",
        choices=["dependents", "uses", "both"],
        default="dependents",
        help="Dirección de búsqueda: dependents (quién depende de mí), "
             "uses (de quién dependo yo), both (ambas). Default: dependents"
    )
    args = parser.parse_args()

    result = find_dependents(args.id_ti, args.id_item, direction=args.direction)
    print(json.dumps(result, indent=2, default=str))
