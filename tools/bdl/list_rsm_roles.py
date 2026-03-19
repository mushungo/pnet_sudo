# tools/bdl/list_rsm_roles.py
"""Lista todos los Roles RSM (Role Security Model) de PeopleNet con un resumen de cada uno."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_rsm_roles():
    """Devuelve un listado resumido de todos los roles RSM del repositorio.

    Consulta M4RSC_RSM con conteo de permisos de M4RDC_SEC_LOBJ.
    """
    query = """
    SELECT
        r.ID_RSM,
        r.N_RSMESP,
        r.N_RSMENG,
        r.ID_PARENT_RSM,
        r.OWNERSHIP,
        r.USABILITY,
        (SELECT COUNT(*) FROM M4RDC_SEC_LOBJ sl WHERE sl.ID_RSM = r.ID_RSM) AS OBJ_PERM_COUNT,
        (SELECT COUNT(*) FROM M4RDC_SEC_FIELDS sf WHERE sf.ID_RSM = r.ID_RSM) AS FIELD_PERM_COUNT
    FROM M4RSC_RSM r
    ORDER BY r.ID_RSM;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            roles = []
            for row in rows:
                roles.append({
                    "id_rsm": row.ID_RSM,
                    "name": row.N_RSMESP or row.N_RSMENG,
                    "parent_rsm": row.ID_PARENT_RSM,
                    "ownership": row.OWNERSHIP,
                    "usability": row.USABILITY,
                    "object_permissions": row.OBJ_PERM_COUNT,
                    "field_permissions": row.FIELD_PERM_COUNT
                })

            return {"status": "success", "total": len(roles), "roles": roles}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print(json.dumps(list_rsm_roles(), indent=2, default=str))
