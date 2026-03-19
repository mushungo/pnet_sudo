# tools/bdl/list_real_objects.py
"""
Lista todos los objetos físicos (REAL_OBJECTS) del repositorio de metadatos BDL.

Muestra el mapeo entre objetos lógicos y sus tablas SQL físicas,
incluyendo tipo de objeto y si es la tabla principal.

Uso:
    python -m tools.bdl.list_real_objects
    python -m tools.bdl.list_real_objects --object "EMPLOYEE"
    python -m tools.bdl.list_real_objects --type 1
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# Tipos de objeto físico
OBJECT_TYPE_MAP = {
    1: "table",
    3: "overflow",
    4: "view",
    5: "master_overflow",
    7: "custom_m4",
    8: "hash_temp",
}


def list_real_objects(id_object=None, obj_type=None, search=None):
    """Obtiene la lista de objetos físicos con información resumida.

    Args:
        id_object: Filtrar por objeto lógico específico.
        obj_type: Filtrar por tipo de objeto (1=table, 3=overflow, 4=view, 5=master, 7=custom, 8=hash).
        search: Buscar en ID_REAL_OBJECT o ID_OBJECT.

    Returns:
        dict con status y lista de objetos físicos.
    """
    sql_query = """
    SELECT
        ro.ID_REAL_OBJECT,
        ro.ID_OBJECT,
        ro.ID_OBJECT_TYPE,
        ro.IS_PRINCIPAL,
        ro.PK_NAME
    FROM
        M4RDC_REAL_OBJECTS ro
    """
    params = []
    conditions = []

    if id_object:
        conditions.append("ro.ID_OBJECT = ?")
        params.append(id_object)

    if obj_type is not None:
        conditions.append("ro.ID_OBJECT_TYPE = ?")
        params.append(obj_type)

    if search:
        conditions.append("(ro.ID_REAL_OBJECT LIKE ? OR ro.ID_OBJECT LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += " ORDER BY ro.ID_OBJECT, ro.ID_REAL_OBJECT;"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params) if params else cursor.execute(sql_query)
            rows = cursor.fetchall()

            real_objects = []
            for row in rows:
                real_objects.append({
                    "id_real_object": row.ID_REAL_OBJECT,
                    "id_object": row.ID_OBJECT,
                    "object_type": OBJECT_TYPE_MAP.get(row.ID_OBJECT_TYPE, str(row.ID_OBJECT_TYPE)),
                    "object_type_id": row.ID_OBJECT_TYPE,
                    "is_principal": bool(row.IS_PRINCIPAL) if row.IS_PRINCIPAL is not None else None,
                    "pk_name": row.PK_NAME,
                })

            return {
                "status": "success",
                "total": len(real_objects),
                "real_objects": real_objects,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista objetos físicos (REAL_OBJECTS) de la BDL.")
    parser.add_argument("--object", dest="id_object", help="Filtrar por objeto lógico (ej. EMPLOYEE)")
    parser.add_argument("--type", type=int, dest="obj_type",
                        help="Filtrar por tipo (1=table, 3=overflow, 4=view, 5=master, 7=custom, 8=hash)")
    parser.add_argument("--search", help="Buscar en nombres de objetos físicos o lógicos")
    args = parser.parse_args()

    result = list_real_objects(id_object=args.id_object, obj_type=args.obj_type, search=args.search)
    print(json.dumps(result, indent=2, default=str))
