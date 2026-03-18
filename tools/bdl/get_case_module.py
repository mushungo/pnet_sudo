# tools/bdl/get_case_module.py
"""Obtiene la definición completa de un Módulo de Datos (Case Module) de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_case_module_details(id_module):
    """Obtiene los detalles de un módulo de datos, sus objetos y sus relaciones."""
    sql_module = """
    SELECT
        m.ID_MODULE,
        m.N_MODULEESP, m.N_MODULEENG,
        m.OWNER_FLAG, m.DEP_CROSS_MOD,
        m.OWNERSHIP, m.USABILITY
    FROM
        M4RDD_CASE_MODULES m
    WHERE
        m.ID_MODULE = ?;
    """
    sql_objects = """
    SELECT
        o.ID_OBJECT, o.HIDDEN, o.ID_STATUS,
        o.DT_CREATE, o.DT_CLOSED,
        lo.ID_TRANS_OBJESP, lo.ID_TRANS_OBJENG, lo.ID_OBJECT_TYPE
    FROM
        M4RDD_CMOD_OBJS o
    LEFT JOIN
        M4RDC_LOGIC_OBJECT lo ON o.ID_OBJECT = lo.ID_OBJECT
    WHERE
        o.ID_MODULE = ?
    ORDER BY
        o.ID_OBJECT;
    """
    sql_relations = """
    SELECT
        r.ID_OBJECT, r.ID_RELATION, r.LINE_STYLE, r.HIDDEN,
        r.DT_CREATE, r.DT_CLOSED,
        rel.ID_PARENT_OBJECT, rel.ID_RELATION_TYPE
    FROM
        M4RDD_CMOD_RELS r
    LEFT JOIN
        M4RDC_RELATIONS rel ON r.ID_RELATION = rel.ID_RELATION
    WHERE
        r.ID_MODULE = ?
    ORDER BY
        r.ID_OBJECT, r.ID_RELATION;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(sql_module, id_module)
            mod_row = cursor.fetchone()

            if not mod_row:
                return {"status": "not_found", "message": f"No se encontró el módulo de datos con ID '{id_module}'."}

            module_details = {
                "id_module": mod_row.ID_MODULE,
                "name": mod_row.N_MODULEESP or mod_row.N_MODULEENG,
                "name_eng": mod_row.N_MODULEENG,
                "owner_flag": mod_row.OWNER_FLAG,
                "dep_cross_mod": mod_row.DEP_CROSS_MOD,
                "ownership": mod_row.OWNERSHIP,
                "usability": mod_row.USABILITY,
                "objects": [],
                "relations": []
            }

            cursor.execute(sql_objects, id_module)
            obj_rows = cursor.fetchall()
            for obj in obj_rows:
                module_details["objects"].append({
                    "id_object": obj.ID_OBJECT,
                    "description": obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG,
                    "object_type": obj.ID_OBJECT_TYPE,
                    "hidden": bool(obj.HIDDEN),
                    "status": obj.ID_STATUS,
                    "dt_create": obj.DT_CREATE,
                    "dt_closed": obj.DT_CLOSED
                })

            cursor.execute(sql_relations, id_module)
            rel_rows = cursor.fetchall()
            for rel in rel_rows:
                module_details["relations"].append({
                    "id_object": rel.ID_OBJECT,
                    "id_relation": rel.ID_RELATION,
                    "id_parent_object": rel.ID_PARENT_OBJECT,
                    "relation_type": rel.ID_RELATION_TYPE,
                    "line_style": rel.LINE_STYLE,
                    "hidden": bool(rel.HIDDEN),
                    "dt_create": rel.DT_CREATE,
                    "dt_closed": rel.DT_CLOSED
                })

            module_details["object_count"] = len(module_details["objects"])
            module_details["relation_count"] = len(module_details["relations"])

            return module_details

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_case_module \"ID_MODULE\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_case_module_details(sys.argv[1]), indent=2, default=str))
