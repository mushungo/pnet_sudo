# tools/bdl/get_bdl_object.py
"""Obtiene la definición completa de un Objeto Lógico (BDL) de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_bdl_object_details(id_object):
    """Obtiene los detalles de un objeto BDL y todos sus campos."""
    sql_query = """
    SELECT
        lo.ID_OBJECT, lo.REAL_NAME as OBJECT_REAL_NAME, lo.ID_OBJECT_TYPE,
        lo.ID_TRANS_OBJESP, lo.ID_TRANS_OBJENG,
        f.ID_FIELD, f.REAL_NAME as FIELD_REAL_NAME, f.ID_TYPE, f.POSITION,
        f.POS_PK, f.NOT_NULL, f.ID_TRANS_FLDESP, f.ID_TRANS_FLDENG
    FROM
        M4RDC_LOGIC_OBJECT lo
    LEFT JOIN
        M4RDC_FIELDS f ON lo.ID_OBJECT = f.ID_OBJECT
    WHERE
        lo.ID_OBJECT = ?
    ORDER BY
        f.POS_PK DESC, f.POSITION;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, id_object)
            rows = cursor.fetchall()

            if not rows:
                return {"status": "not_found", "message": f"No se encontró el objeto BDL con ID '{id_object}'."}

            first_row = rows[0]
            object_details = {
                "id_object": first_row.ID_OBJECT,
                "object_real_name": first_row.OBJECT_REAL_NAME,
                "description": first_row.ID_TRANS_OBJESP or first_row.ID_TRANS_OBJENG,
                "object_type": first_row.ID_OBJECT_TYPE,
                "fields": []
            }

            for row in rows:
                if row.ID_FIELD:
                    object_details["fields"].append({
                        "id_field": row.ID_FIELD,
                        "field_real_name": row.FIELD_REAL_NAME,
                        "type": row.ID_TYPE,
                        "position": row.POSITION,
                        "is_primary_key": bool(row.POS_PK),
                        "is_not_null": bool(row.NOT_NULL),
                        "description": row.ID_TRANS_FLDESP or row.ID_TRANS_FLDENG
                    })

            return object_details

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_bdl_object \"ID_OBJETO\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_bdl_object_details(sys.argv[1]), indent=2, default=str))
