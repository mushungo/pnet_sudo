# tools/bdl/list_ramdl_objects.py
"""Lista todos los Objetos RAMDL (transporte) del repositorio de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_ramdl_objects():
    """Devuelve un listado resumido de todos los objetos RAMDL del repositorio.

    Consulta M4RDC_RAMDL_OBJECTS agrupando versiones por objeto.
    """
    query = """
    SELECT
        ro.ID_OBJECT,
        MIN(ro.N_OBJECTESP) AS N_OBJECTESP,
        MIN(ro.N_OBJECTENG) AS N_OBJECTENG,
        MIN(ro.VER_LOWEST) AS MIN_VER,
        MAX(ro.VER_HIGHEST) AS MAX_VER,
        COUNT(*) AS VERSION_COUNT
    FROM M4RDC_RAMDL_OBJECTS ro
    GROUP BY ro.ID_OBJECT
    ORDER BY ro.ID_OBJECT;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            objects = []
            for row in rows:
                objects.append({
                    "id_object": row.ID_OBJECT,
                    "name": row.N_OBJECTESP or row.N_OBJECTENG,
                    "min_version": row.MIN_VER,
                    "max_version": row.MAX_VER,
                    "version_count": row.VERSION_COUNT
                })

            return {"status": "success", "total": len(objects), "objects": objects}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_ramdl_versions():
    """Devuelve el listado de versiones RAMDL disponibles."""
    query = "SELECT VERSION FROM M4RDC_RAMDL_VER ORDER BY VERSION;"
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            versions = [row.VERSION for row in cursor.fetchall()]
            return {"status": "success", "total": len(versions), "versions": versions}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--versions":
        print(json.dumps(list_ramdl_versions(), indent=2, default=str))
    else:
        print(json.dumps(list_ramdl_objects(), indent=2, default=str))
