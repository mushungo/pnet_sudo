# tools/bdl/get_index.py
"""Obtiene la definición completa de un Índice Lógico de la BDL de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_index(id_index, id_object):
    """Obtiene los detalles completos de un índice lógico, incluyendo sus columnas.

    Consulta M4RDC_INDEX, M4RDC_INDEX_COLS y M4RDC_INDEX_INCLUDE_COLS.
    """
    index_query = """
    SELECT
        i.ID_INDEX,
        i.ID_OBJECT,
        lo.ID_TRANS_OBJESP,
        lo.ID_TRANS_OBJENG,
        i.REPLY_ALL_TABLES,
        i.IS_UNIQUE,
        i.REAL_NAME,
        i.DT_CREATE,
        i.DTE_CLOSED
    FROM M4RDC_INDEX i
    LEFT JOIN M4RDC_LOGIC_OBJECT lo ON i.ID_OBJECT = lo.ID_OBJECT
    WHERE i.ID_INDEX = ? AND i.ID_OBJECT = ?;
    """
    cols_query = """
    SELECT ID_FIELD, POSITION
    FROM M4RDC_INDEX_COLS
    WHERE ID_INDEX = ? AND ID_OBJECT = ?
    ORDER BY POSITION;
    """
    include_query = """
    SELECT ID_FIELD, POSITION
    FROM M4RDC_INDEX_INCLUDE_COLS
    WHERE ID_INDEX = ? AND ID_OBJECT = ?
    ORDER BY POSITION;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(index_query, id_index, id_object)
            row = cursor.fetchone()

            if not row:
                return {"status": "not_found", "message": f"No se encontró el índice '{id_index}' en objeto '{id_object}'."}

            cursor.execute(cols_query, id_index, id_object)
            columns = [{"field": r.ID_FIELD, "position": r.POSITION} for r in cursor.fetchall()]

            cursor.execute(include_query, id_index, id_object)
            include_cols = [{"field": r.ID_FIELD, "position": r.POSITION} for r in cursor.fetchall()]

            result = {
                "status": "success",
                "index": {
                    "id_index": row.ID_INDEX,
                    "id_object": row.ID_OBJECT,
                    "object_description": row.ID_TRANS_OBJESP or row.ID_TRANS_OBJENG,
                    "is_unique": bool(row.IS_UNIQUE) if row.IS_UNIQUE is not None else None,
                    "reply_all_tables": bool(row.REPLY_ALL_TABLES) if row.REPLY_ALL_TABLES is not None else None,
                    "real_name": row.REAL_NAME,
                    "dt_create": row.DT_CREATE,
                    "dt_closed": row.DTE_CLOSED,
                    "columns": columns,
                    "include_columns": include_cols
                }
            }
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_index \"ID_INDEX\" \"ID_OBJECT\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_index(sys.argv[1], sys.argv[2]), indent=2, default=str))
