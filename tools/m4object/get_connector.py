# tools/m4object/get_connector.py
"""
Obtiene el detalle completo de un conector específico entre dos nodos,
incluyendo los items conectados y parámetros de sentence.

Uso:
    python -m tools.m4object.get_connector "ID_T3" "ID_TI" "ID_NODE" "ID_TI_USED" "ID_NODE_USED"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# Mapeo de tipos
CONNECTION_TYPE_MAP = {1: "call", 3: "self/bidirectional"}
PRECEDENCE_TYPE_MAP = {1: "before", 2: "after"}
CSTYPE_MAP = {2: "execution", 3: "parameter"}


def get_connector_details(id_t3, id_ti, id_node, id_ti_used, id_node_used):
    """Obtiene el detalle completo de un conector entre dos nodos.

    Args:
        id_t3: Identificador del canal.
        id_ti: TI origen.
        id_node: Nodo origen.
        id_ti_used: TI destino.
        id_node_used: Nodo destino.

    Returns:
        dict con el detalle completo o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Conector principal
            cursor.execute(
                "SELECT ID_T3, ID_TI, ID_NODE, ID_TI_USED, ID_NODE_USED, "
                "ID_CONNECTION_TYPE, ID_SENTENCE "
                "FROM M4RCH_CONNECTORS "
                "WHERE ID_T3 = ? AND ID_TI = ? AND ID_NODE = ? "
                "AND ID_TI_USED = ? AND ID_NODE_USED = ?",
                id_t3, id_ti, id_node, id_ti_used, id_node_used
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el conector {id_t3}/{id_ti}/{id_node} -> {id_ti_used}/{id_node_used}."
                }

            result = {
                "id_t3": main_row.ID_T3,
                "id_ti": main_row.ID_TI,
                "id_node": main_row.ID_NODE,
                "id_ti_used": main_row.ID_TI_USED,
                "id_node_used": main_row.ID_NODE_USED,
                "connection_type": CONNECTION_TYPE_MAP.get(
                    main_row.ID_CONNECTION_TYPE, str(main_row.ID_CONNECTION_TYPE)
                ),
                "id_sentence": main_row.ID_SENTENCE,
            }

            # 2. Items conectados
            cursor.execute(
                "SELECT ID_ITEM, ID_ITEM_USED, ID_PRECEDENCE_TYPE, "
                "ID_SPIN_TYPE, ID_RELSHIP_TYPE, ID_CONTEXT_TYPE, "
                "TRIGGER_MODE, ID_CSTYPE "
                "FROM M4RCH_CONCTOR_ITEM "
                "WHERE ID_T3 = ? AND ID_TI = ? AND ID_NODE = ? "
                "AND ID_TI_USED = ? AND ID_NODE_USED = ? "
                "ORDER BY ID_ITEM",
                id_t3, id_ti, id_node, id_ti_used, id_node_used
            )
            result["items"] = []
            for row in cursor.fetchall():
                result["items"].append({
                    "id_item": row.ID_ITEM,
                    "id_item_used": row.ID_ITEM_USED,
                    "precedence": PRECEDENCE_TYPE_MAP.get(
                        row.ID_PRECEDENCE_TYPE, str(row.ID_PRECEDENCE_TYPE)
                    ) if row.ID_PRECEDENCE_TYPE else None,
                    "spin_type": row.ID_SPIN_TYPE,
                    "relationship_type": row.ID_RELSHIP_TYPE,
                    "context_type": row.ID_CONTEXT_TYPE,
                    "trigger_mode": row.TRIGGER_MODE,
                    "cstype": CSTYPE_MAP.get(
                        row.ID_CSTYPE, str(row.ID_CSTYPE)
                    ) if row.ID_CSTYPE else None,
                })

            # 3. Parámetros de sentence (si hay)
            cursor.execute(
                "SELECT ID_SENTENCE, ID_FIELD, ALIAS "
                "FROM M4RCH_CONCTOR_PAR "
                "WHERE ID_T3 = ? AND ID_TI = ? AND ID_NODE = ? "
                "AND ID_TI_USED = ? AND ID_NODE_USED = ? "
                "ORDER BY ID_FIELD",
                id_t3, id_ti, id_node, id_ti_used, id_node_used
            )
            result["sentence_params"] = []
            for row in cursor.fetchall():
                result["sentence_params"].append({
                    "id_sentence": row.ID_SENTENCE,
                    "id_field": row.ID_FIELD,
                    "alias": row.ALIAS,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.m4object.get_connector "
                       "\"ID_T3\" \"ID_TI\" \"ID_NODE\" \"ID_TI_USED\" \"ID_NODE_USED\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(
        get_connector_details(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]),
        indent=2, default=str
    ))
