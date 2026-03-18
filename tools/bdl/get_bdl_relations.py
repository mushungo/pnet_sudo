# tools/bdl/get_bdl_relations.py
"""Obtiene todas las relaciones lógicas (entrantes y salientes) de un objeto de la BDL."""
import sys
import os
import json
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_relations_for_bdl_object(id_object):
    """Obtiene las relaciones salientes y entrantes de un objeto BDL, con sus campos mapeados."""
    relations_query = (
        "SELECT ID_RELATION, ID_OBJECT as CHILD_OBJECT, ID_PARENT_OBJECT, ID_RELATION_TYPE "
        "FROM M4RDC_RELATIONS WHERE ID_OBJECT = ? OR ID_PARENT_OBJECT = ?;"
    )
    fields_query_template = "SELECT ID_RELATION, ID_FIELD, ID_PARENT_FIELD FROM M4RDC_RLTION_FLDS WHERE ID_RELATION IN ({});"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(relations_query, id_object, id_object)
            relations = cursor.fetchall()

            if not relations:
                return {"object_searched": id_object, "message": "No participa en relaciones."}

            relation_ids = [rel.ID_RELATION for rel in relations]
            placeholders = ",".join(["?"] * len(relation_ids))
            cursor.execute(fields_query_template.format(placeholders), relation_ids)
            fields = cursor.fetchall()

            relation_fields_map = defaultdict(list)
            for field in fields:
                relation_fields_map[field.ID_RELATION].append({
                    "child_field": field.ID_FIELD,
                    "parent_field": field.ID_PARENT_FIELD
                })

            output = {"object_searched": id_object, "outgoing_relations": [], "incoming_relations": []}
            for rel in relations:
                relation_data = {
                    "relation_id": rel.ID_RELATION,
                    "type": rel.ID_RELATION_TYPE,
                    "field_mappings": relation_fields_map[rel.ID_RELATION]
                }
                if rel.CHILD_OBJECT == id_object:
                    relation_data["points_to_parent_object"] = rel.ID_PARENT_OBJECT
                    output["outgoing_relations"].append(relation_data)
                else:
                    relation_data["originates_from_child_object"] = rel.CHILD_OBJECT
                    output["incoming_relations"].append(relation_data)

            return output

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_bdl_relations \"ID_OBJETO\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_relations_for_bdl_object(sys.argv[1]), indent=2, default=str))
