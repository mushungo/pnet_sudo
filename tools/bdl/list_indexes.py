# tools/bdl/list_indexes.py
"""Lista todos los Índices Lógicos de la BDL de PeopleNet con un resumen de cada uno."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_indexes(object_filter=None):
    """Devuelve un listado resumido de todos los índices lógicos.

    Args:
        object_filter: Si se especifica, filtra por ID_OBJECT.
    """
    query = """
    SELECT
        i.ID_INDEX,
        i.ID_OBJECT,
        lo.ID_TRANS_OBJESP,
        lo.ID_TRANS_OBJENG,
        i.IS_UNIQUE,
        i.REAL_NAME,
        (SELECT COUNT(*) FROM M4RDC_INDEX_COLS ic
         WHERE ic.ID_INDEX = i.ID_INDEX AND ic.ID_OBJECT = i.ID_OBJECT) AS COL_COUNT,
        (SELECT COUNT(*) FROM M4RDC_INDEX_INCLUDE_COLS iic
         WHERE iic.ID_INDEX = i.ID_INDEX AND iic.ID_OBJECT = i.ID_OBJECT) AS INCLUDE_COL_COUNT
    FROM M4RDC_INDEX i
    LEFT JOIN M4RDC_LOGIC_OBJECT lo ON i.ID_OBJECT = lo.ID_OBJECT
    """
    params = []
    if object_filter:
        query += " WHERE i.ID_OBJECT = ?"
        params.append(object_filter)
    query += " ORDER BY i.ID_OBJECT, i.ID_INDEX;"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, *params)
            rows = cursor.fetchall()

            indexes = []
            for row in rows:
                indexes.append({
                    "id_index": row.ID_INDEX,
                    "id_object": row.ID_OBJECT,
                    "object_description": row.ID_TRANS_OBJESP or row.ID_TRANS_OBJENG,
                    "is_unique": bool(row.IS_UNIQUE) if row.IS_UNIQUE is not None else None,
                    "real_name": row.REAL_NAME,
                    "column_count": row.COL_COUNT,
                    "include_column_count": row.INCLUDE_COL_COUNT
                })

            return {"status": "success", "total": len(indexes), "indexes": indexes}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(list_indexes(object_filter=sys.argv[1]), indent=2, default=str))
    else:
        print(json.dumps(list_indexes(), indent=2, default=str))
