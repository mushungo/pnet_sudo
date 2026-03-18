# tools/bdl/list_bdl_objects.py
"""Lista todos los objetos lógicos (BDL) disponibles en el repositorio de metadatos."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_all_bdl_objects():
    """Obtiene una lista de todos los ID_OBJECT de la tabla de metadatos."""
    sql_query = "SELECT ID_OBJECT FROM M4RDC_LOGIC_OBJECT ORDER BY ID_OBJECT;"
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            object_ids = [row.ID_OBJECT for row in rows]
            return {"status": "success", "objects": object_ids}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = get_all_bdl_objects()
    print(json.dumps(result, indent=2))
