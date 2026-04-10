# tools/m4object/list_connectors.py
"""
Lista todos los conectores a nivel de nodo para un canal (T3) o TI dado.

Los conectores definen cómo los nodos de un M4Object se interconectan
para ejecutar lógica, cargar datos y propagar contexto.

Uso:
    python -m tools.m4object.list_connectors "ID_T3"
    python -m tools.m4object.list_connectors "ID_T3" --ti "ID_TI"
    python -m tools.m4object.list_connectors "ID_T3" --ti "ID_TI" --node "ID_NODE"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection
from tools.m4object.m4object_maps import CONNECTION_TYPE_MAP, decode


def list_connectors(id_t3, id_ti=None, id_node=None):
    """Obtiene la lista de conectores a nivel de nodo.

    Args:
        id_t3: Identificador del canal (T3).
        id_ti: Filtrar por TI específico.
        id_node: Filtrar por nodo específico (requiere id_ti).

    Returns:
        dict con la lista de conectores y conteo de items por conector.
    """
    sql_query = """
    SELECT
        c.ID_T3, c.ID_TI, c.ID_NODE,
        c.ID_TI_USED, c.ID_NODE_USED,
        c.ID_CONNECTION_TYPE, c.ID_SENTENCE,
        COUNT(DISTINCT ci.ID_ITEM) AS item_count
    FROM
        M4RCH_CONNECTORS c
    LEFT JOIN
        M4RCH_CONCTOR_ITEM ci ON c.ID_T3 = ci.ID_T3
            AND c.ID_TI = ci.ID_TI AND c.ID_NODE = ci.ID_NODE
            AND c.ID_TI_USED = ci.ID_TI_USED AND c.ID_NODE_USED = ci.ID_NODE_USED
    WHERE
        c.ID_T3 = ?
    """
    params = [id_t3]

    if id_ti:
        sql_query += " AND c.ID_TI = ?"
        params.append(id_ti)

    if id_node:
        sql_query += " AND c.ID_NODE = ?"
        params.append(id_node)

    sql_query += """
    GROUP BY
        c.ID_T3, c.ID_TI, c.ID_NODE,
        c.ID_TI_USED, c.ID_NODE_USED,
        c.ID_CONNECTION_TYPE, c.ID_SENTENCE
    ORDER BY
        c.ID_TI, c.ID_NODE, c.ID_TI_USED, c.ID_NODE_USED;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params)
            rows = cursor.fetchall()

            connectors = []
            for row in rows:
                connectors.append({
                    "id_t3": row.ID_T3,
                    "id_ti": row.ID_TI,
                    "id_node": row.ID_NODE,
                    "id_ti_used": row.ID_TI_USED,
                    "id_node_used": row.ID_NODE_USED,
                    "connection_type": decode(
                        row.ID_CONNECTION_TYPE, CONNECTION_TYPE_MAP
                    ),
                    "id_sentence": row.ID_SENTENCE,
                    "item_count": row.item_count,
                })

            return {
                "status": "success",
                "id_t3": id_t3,
                "total": len(connectors),
                "connectors": connectors,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista conectores de nodo de un M4Object.")
    parser.add_argument("id_t3", help="Identificador del canal (T3)")
    parser.add_argument("--ti", dest="id_ti", help="Filtrar por TI")
    parser.add_argument("--node", dest="id_node", help="Filtrar por nodo")
    args = parser.parse_args()

    result = list_connectors(args.id_t3, id_ti=args.id_ti, id_node=args.id_node)
    print(json.dumps(result, indent=2, default=str))
