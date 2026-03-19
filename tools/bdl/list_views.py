# tools/bdl/list_views.py
"""Lista todas las Vistas SQL definidas en la BDL de PeopleNet con un resumen de cada una."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_views():
    """Devuelve un listado resumido de todas las vistas SQL del repositorio.

    Consulta M4RDC_VIEW_CODE con JOIN a M4RDC_LOGIC_OBJECT para la descripción.
    """
    query = """
    SELECT
        vc.ID_OBJECT,
        lo.ID_TRANS_OBJESP,
        lo.ID_TRANS_OBJENG,
        lo.REAL_NAME,
        vc.IS_REAL,
        vc.DT_CREATE,
        vc.DT_MOD
    FROM M4RDC_VIEW_CODE vc
    LEFT JOIN M4RDC_LOGIC_OBJECT lo ON vc.ID_OBJECT = lo.ID_OBJECT
    ORDER BY vc.ID_OBJECT;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            views = []
            for row in rows:
                views.append({
                    "id_object": row.ID_OBJECT,
                    "description": row.ID_TRANS_OBJESP or row.ID_TRANS_OBJENG,
                    "real_name": row.REAL_NAME,
                    "is_real": bool(row.IS_REAL) if row.IS_REAL is not None else None,
                    "dt_create": row.DT_CREATE,
                    "dt_mod": row.DT_MOD
                })

            return {"status": "success", "total": len(views), "views": views}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print(json.dumps(list_views(), indent=2, default=str))
