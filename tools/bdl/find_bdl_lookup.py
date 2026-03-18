# tools/bdl/find_bdl_lookup.py
"""Encuentra la tabla maestra (lookup) que provee los valores válidos para un campo de la BDL."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def find_lookup_table(id_object, id_field):
    """Encuentra la tabla maestra asociada a un campo específico de un objeto BDL."""
    rel_fields_query = "SELECT ID_RELATION FROM M4RDC_RLTION_FLDS WHERE ID_OBJECT = ? AND ID_FIELD = ?;"
    relations_query = "SELECT ID_PARENT_OBJECT FROM M4RDC_RELATIONS WHERE ID_RELATION = ?;"
    logic_object_query = "SELECT REAL_NAME FROM M4RDC_LOGIC_OBJECT WHERE ID_OBJECT = ?;"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(rel_fields_query, id_object, id_field)
            rel_field_row = cursor.fetchone()
            if not rel_field_row:
                return {"status": "not_found", "message": f"No se encontró relación para {id_object}.{id_field}."}

            id_relation = rel_field_row.ID_RELATION

            cursor.execute(relations_query, id_relation)
            relation_row = cursor.fetchone()
            if not relation_row:
                return {"status": "error", "message": f"Relación '{id_relation}' sin objeto padre."}

            id_parent_object = relation_row.ID_PARENT_OBJECT

            cursor.execute(logic_object_query, id_parent_object)
            logic_object_row = cursor.fetchone()
            if not logic_object_row:
                return {"status": "error", "message": f"Objeto padre '{id_parent_object}' sin tabla física."}

            return {
                "status": "success",
                "search_parameters": {"object": id_object, "field": id_field},
                "found_lookup": {
                    "relation_id": id_relation,
                    "parent_logic_object": id_parent_object,
                    "parent_physical_table": logic_object_row.REAL_NAME
                }
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.find_bdl_lookup \"ID_OBJETO\" \"ID_CAMPO\""}, indent=2))
        sys.exit(1)
    print(json.dumps(find_lookup_table(sys.argv[1], sys.argv[2]), indent=2, default=str))
