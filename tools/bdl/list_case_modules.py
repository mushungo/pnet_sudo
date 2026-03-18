# tools/bdl/list_case_modules.py
"""Lista todos los Módulos de Datos (Case Modules) disponibles en el repositorio de metadatos."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_all_case_modules():
    """Obtiene una lista de todos los módulos de datos con información resumida."""
    sql_query = """
    SELECT
        m.ID_MODULE,
        m.N_MODULEESP, m.N_MODULEENG,
        m.OWNER_FLAG, m.OWNERSHIP, m.USABILITY,
        (SELECT COUNT(*) FROM M4RDD_CMOD_OBJS o WHERE o.ID_MODULE = m.ID_MODULE) AS OBJ_COUNT,
        (SELECT COUNT(*) FROM M4RDD_CMOD_RELS r WHERE r.ID_MODULE = m.ID_MODULE) AS REL_COUNT
    FROM
        M4RDD_CASE_MODULES m
    ORDER BY
        m.ID_MODULE;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            modules = []
            for row in rows:
                modules.append({
                    "id_module": row.ID_MODULE,
                    "name": row.N_MODULEESP or row.N_MODULEENG,
                    "owner_flag": row.OWNER_FLAG,
                    "ownership": row.OWNERSHIP,
                    "usability": row.USABILITY,
                    "object_count": row.OBJ_COUNT,
                    "relation_count": row.REL_COUNT
                })
            return {"status": "success", "count": len(modules), "modules": modules}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = get_all_case_modules()
    print(json.dumps(result, indent=2, default=str))
