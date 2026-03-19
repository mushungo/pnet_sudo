# tools/bdl/get_real_object.py
"""
Obtiene el detalle completo de un objeto físico de la BDL, incluyendo
todos sus campos físicos y el mapeo a campos lógicos.

Uso:
    python -m tools.bdl.get_real_object "ID_REAL_OBJECT"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


OBJECT_TYPE_MAP = {
    1: "table",
    3: "overflow",
    4: "view",
    5: "master_overflow",
    7: "custom_m4",
    8: "hash_temp",
}


def get_real_object_details(id_real_object):
    """Obtiene el detalle de un objeto físico con sus campos y mapeos.

    Args:
        id_real_object: Identificador del objeto físico (nombre de tabla SQL).

    Returns:
        dict con detalle completo o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Objeto principal
            cursor.execute(
                "SELECT ID_REAL_OBJECT, ID_OBJECT, ID_OBJECT_TYPE, "
                "IS_PRINCIPAL, PK_NAME "
                "FROM M4RDC_REAL_OBJECTS WHERE ID_REAL_OBJECT = ?",
                id_real_object
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el objeto físico '{id_real_object}'."
                }

            result = {
                "id_real_object": main_row.ID_REAL_OBJECT,
                "id_object": main_row.ID_OBJECT,
                "object_type": OBJECT_TYPE_MAP.get(main_row.ID_OBJECT_TYPE, str(main_row.ID_OBJECT_TYPE)),
                "is_principal": bool(main_row.IS_PRINCIPAL) if main_row.IS_PRINCIPAL is not None else None,
                "pk_name": main_row.PK_NAME,
            }

            # 2. Campos físicos con mapeo a lógicos
            cursor.execute(
                "SELECT ID_REAL_FIELD, ID_FIELD, ID_OBJECT "
                "FROM M4RDC_REAL_FIELDS "
                "WHERE ID_REAL_OBJECT = ? ORDER BY ID_REAL_FIELD",
                id_real_object
            )
            result["fields"] = []
            for row in cursor.fetchall():
                result["fields"].append({
                    "id_real_field": row.ID_REAL_FIELD,
                    "id_field": row.ID_FIELD,
                    "id_object": row.ID_OBJECT,
                })

            # 3. Índices físicos
            cursor.execute(
                "SELECT ID_INDEX, IS_UNIQUE, IS_CLUSTERED_SQL, FILL_FACTOR "
                "FROM M4RDC_REAL_INDEX "
                "WHERE ID_REAL_OBJECT = ? ORDER BY ID_INDEX",
                id_real_object
            )
            result["indexes"] = []
            for row in cursor.fetchall():
                result["indexes"].append({
                    "id_index": row.ID_INDEX,
                    "is_unique": bool(row.IS_UNIQUE) if row.IS_UNIQUE is not None else None,
                    "is_clustered": bool(row.IS_CLUSTERED_SQL) if row.IS_CLUSTERED_SQL is not None else None,
                    "fill_factor": row.FILL_FACTOR,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.bdl.get_real_object \"ID_REAL_OBJECT\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_real_object_details(sys.argv[1]), indent=2, default=str))
