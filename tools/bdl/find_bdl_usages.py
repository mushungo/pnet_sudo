# tools/bdl/find_bdl_usages.py
"""Encuentra todos los m4objects (canales) que utilizan un Objeto Lógico (BDL) específico."""
import sys
import os
import json
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def find_bdl_object_usages(id_object):
    """Busca en qué m4objects se utiliza un objeto BDL, tanto en lectura como en escritura."""
    sql_query = """
    SELECT DISTINCT
        i.ID_TI, t.N_T3ESP, t.N_T3ENG, n.ID_NODE, i.ID_ITEM,
        i.ID_READ_OBJECT, i.ID_WRITE_OBJECT, i.ID_READ_FIELD, i.ID_WRITE_FIELD
    FROM M4RCH_ITEMS i
    INNER JOIN M4RCH_NODES n ON i.ID_TI = n.ID_TI
    INNER JOIN M4RCH_T3S t ON n.ID_T3 = t.ID_T3
    WHERE i.ID_READ_OBJECT = ? OR i.ID_WRITE_OBJECT = ?
    ORDER BY i.ID_TI, n.ID_NODE, i.ID_ITEM;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, id_object, id_object)
            rows = cursor.fetchall()

            if not rows:
                return {"bdl_object_searched": id_object, "message": "No utilizado.", "usages": []}

            m4object_usages = defaultdict(lambda: {"description": "", "nodes": defaultdict(list)})
            for row in rows:
                usage_type = []
                if row.ID_READ_OBJECT == id_object:
                    usage_type.append("read")
                if row.ID_WRITE_OBJECT == id_object:
                    usage_type.append("write")
                field_used = row.ID_READ_FIELD if row.ID_READ_OBJECT == id_object else row.ID_WRITE_FIELD

                m4object_usages[row.ID_TI]["description"] = row.N_T3ESP or row.N_T3ENG
                m4object_usages[row.ID_TI]["nodes"][row.ID_NODE].append({
                    "item": row.ID_ITEM,
                    "field_used": field_used,
                    "usage_type": ", ".join(usage_type)
                })

            output_usages = [
                {
                    "m4object_ti": ti,
                    "description": data["description"],
                    "nodes": [
                        {"node_id": node, "items": items}
                        for node, items in data["nodes"].items()
                    ]
                }
                for ti, data in m4object_usages.items()
            ]
            return {"bdl_object_searched": id_object, "usages": output_usages}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.find_bdl_usages \"ID_OBJETO\""}, indent=2))
        sys.exit(1)
    print(json.dumps(find_bdl_object_usages(sys.argv[1]), indent=2, default=str))
