# tools/dependencies/list_dependencies.py
"""
Lista todas las dependencias de un TI completo, agrupadas por item.

Muestra un resumen de cuántas dependencias internas, externas y de canal
tiene cada item del TI.

Uso:
    python -m tools.dependencies.list_dependencies "ID_TI"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_dependencies(id_ti):
    """Obtiene un resumen de dependencias por item para un TI.

    Args:
        id_ti: Identificador del TI.

    Returns:
        dict con el resumen de dependencias por item.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # Dependencias internas (agrupadas por item)
            cursor.execute(
                "SELECT ID_ITEM, COUNT(*) AS dep_count "
                "FROM M4RCH_INTERNAL_DEP "
                "WHERE ID_TI = ? "
                "GROUP BY ID_ITEM ORDER BY dep_count DESC",
                id_ti
            )
            internal = {row.ID_ITEM: row.dep_count for row in cursor.fetchall()}

            # Items usados internamente
            cursor.execute(
                "SELECT ID_ITEM_USED, COUNT(*) AS used_count "
                "FROM M4RCH_INTERNAL_DEP "
                "WHERE ID_TI = ? "
                "GROUP BY ID_ITEM_USED ORDER BY used_count DESC",
                id_ti
            )
            internal_used = {row.ID_ITEM_USED: row.used_count for row in cursor.fetchall()}

            # Dependencias externas (items de este TI que usan otros TIs)
            cursor.execute(
                "SELECT ID_ITEM, COUNT(*) AS dep_count "
                "FROM M4RCH_EXTERNAL_DEP "
                "WHERE ID_TI = ? "
                "GROUP BY ID_ITEM ORDER BY dep_count DESC",
                id_ti
            )
            external_uses = {row.ID_ITEM: row.dep_count for row in cursor.fetchall()}

            # Items de este TI usados externamente por otros
            cursor.execute(
                "SELECT ID_ITEM_USED, COUNT(*) AS used_count "
                "FROM M4RCH_EXTERNAL_DEP "
                "WHERE ID_TI_USED = ? "
                "GROUP BY ID_ITEM_USED ORDER BY used_count DESC",
                id_ti
            )
            external_dependents = {row.ID_ITEM_USED: row.used_count for row in cursor.fetchall()}

            # Dependencias de canal
            cursor.execute(
                "SELECT ID_ITEM, COUNT(*) AS dep_count "
                "FROM M4RCH_CHANNEL_DEP "
                "WHERE ID_TI = ? "
                "GROUP BY ID_ITEM ORDER BY dep_count DESC",
                id_ti
            )
            channel_uses = {row.ID_ITEM: row.dep_count for row in cursor.fetchall()}

            cursor.execute(
                "SELECT ID_ITEM_USED, COUNT(*) AS used_count "
                "FROM M4RCH_CHANNEL_DEP "
                "WHERE ID_TI_USED = ? "
                "GROUP BY ID_ITEM_USED ORDER BY used_count DESC",
                id_ti
            )
            channel_dependents = {row.ID_ITEM_USED: row.used_count for row in cursor.fetchall()}

            # Unificar todos los items
            all_items = sorted(set(
                list(internal.keys()) + list(internal_used.keys()) +
                list(external_uses.keys()) + list(external_dependents.keys()) +
                list(channel_uses.keys()) + list(channel_dependents.keys())
            ))

            items_summary = []
            for item in all_items:
                items_summary.append({
                    "id_item": item,
                    "internal_deps": internal.get(item, 0),
                    "internal_used_by": internal_used.get(item, 0),
                    "external_uses": external_uses.get(item, 0),
                    "external_dependents": external_dependents.get(item, 0),
                    "channel_uses": channel_uses.get(item, 0),
                    "channel_dependents": channel_dependents.get(item, 0),
                })

            return {
                "status": "success",
                "id_ti": id_ti,
                "total_items": len(items_summary),
                "items": items_summary,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.dependencies.list_dependencies \"ID_TI\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(list_dependencies(sys.argv[1]), indent=2, default=str))
