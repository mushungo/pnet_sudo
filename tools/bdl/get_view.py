# tools/bdl/get_view.py
"""Obtiene el código SQL y metadatos de una Vista definida en la BDL de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_view(id_object):
    """Obtiene los metadatos y el código SQL de una vista de la BDL.

    Consulta M4RDC_VIEW_CODE para metadatos y M4RDC_VIEW_CODE1 para el código fuente SQL,
    además de M4RDC_LOGIC_OBJECT para la descripción del objeto.
    """
    query = """
    SELECT
        vc.ID_OBJECT,
        lo.ID_TRANS_OBJESP,
        lo.ID_TRANS_OBJENG,
        lo.REAL_NAME,
        vc.IS_REAL,
        vc.DT_CREATE,
        vc.DT_CLOSED,
        vc.DT_MOD,
        vc.DT_MOD_SCRIPT,
        vc.ID_APPROLE,
        vc.ID_SECUSER,
        CAST(vc1.VIEW_CODE AS VARCHAR(MAX)) AS VIEW_CODE
    FROM M4RDC_VIEW_CODE vc
    LEFT JOIN M4RDC_VIEW_CODE1 vc1 ON vc.ID_OBJECT = vc1.ID_OBJECT
    LEFT JOIN M4RDC_LOGIC_OBJECT lo ON vc.ID_OBJECT = lo.ID_OBJECT
    WHERE vc.ID_OBJECT = ?;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, id_object)
            row = cursor.fetchone()

            if not row:
                return {"status": "not_found", "message": f"No se encontró la vista '{id_object}'."}

            result = {
                "status": "success",
                "view": {
                    "id_object": row.ID_OBJECT,
                    "description": row.ID_TRANS_OBJESP or row.ID_TRANS_OBJENG,
                    "description_eng": row.ID_TRANS_OBJENG,
                    "real_name": row.REAL_NAME,
                    "is_real": bool(row.IS_REAL) if row.IS_REAL is not None else None,
                    "dt_create": row.DT_CREATE,
                    "dt_closed": row.DT_CLOSED,
                    "dt_mod": row.DT_MOD,
                    "id_approle": row.ID_APPROLE,
                    "id_secuser": row.ID_SECUSER,
                    "view_code": row.VIEW_CODE
                }
            }
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_view \"ID_OBJECT\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_view(sys.argv[1]), indent=2, default=str))
