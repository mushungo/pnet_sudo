# tools/bdl/list_ln4_functions.py
"""Lista todas las funciones LN4 del repositorio de PeopleNet con un resumen de cada una."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_ln4_functions(group_filter=None):
    """Devuelve un listado resumido de todas las funciones LN4.

    Args:
        group_filter: Si se especifica, filtra por ID_FUNC_GROUP.
    """
    query = """
    SELECT
        f.ID_LN4_FUNCTION,
        f.N_LN4_FUNCTION,
        f.VARIABLE_ARGUMENTS,
        f.FUNCTION_LEVEL,
        f.ID_FUNC_GROUP,
        g.DESCRIPCIONESP AS GROUP_ESP,
        g.DESCRIPCIONENG AS GROUP_ENG,
        fc.COMENTESP,
        fc.COMENTENG,
        (SELECT COUNT(*) FROM M4RCH_LN4_FUNC_ARG a
         WHERE a.ID_LN4_FUNCTION = f.ID_LN4_FUNCTION) AS ARG_COUNT
    FROM M4RCH_LN4_FUNCTION f
    LEFT JOIN M4RCH_FUNC_GROUPS g ON f.ID_FUNC_GROUP = g.ID_FUNC_GROUP
    LEFT JOIN M4RCH_LN4_FUNCTIO1 fc ON f.ID_LN4_FUNCTION = fc.ID_LN4_FUNCTION
    """
    params = []
    if group_filter:
        query += " WHERE f.ID_FUNC_GROUP = ?"
        params.append(group_filter)
    query += " ORDER BY f.ID_LN4_FUNCTION;"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, *params)
            rows = cursor.fetchall()

            functions = []
            for row in rows:
                functions.append({
                    "id_ln4_function": row.ID_LN4_FUNCTION,
                    "name": row.N_LN4_FUNCTION,
                    "group_id": row.ID_FUNC_GROUP,
                    "group_name": row.GROUP_ESP or row.GROUP_ENG,
                    "comment": row.COMENTESP or row.COMENTENG,
                    "arg_count": row.ARG_COUNT,
                    "variable_arguments": bool(row.VARIABLE_ARGUMENTS) if row.VARIABLE_ARGUMENTS is not None else None,
                    "function_level": row.FUNCTION_LEVEL
                })

            return {"status": "success", "total": len(functions), "functions": functions}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_ln4_groups():
    """Devuelve el listado de grupos de funciones LN4."""
    query = """
    SELECT
        g.ID_FUNC_GROUP,
        g.DESCRIPCIONESP,
        g.DESCRIPCIONENG,
        (SELECT COUNT(*) FROM M4RCH_LN4_FUNCTION f
         WHERE f.ID_FUNC_GROUP = g.ID_FUNC_GROUP) AS FUNC_COUNT
    FROM M4RCH_FUNC_GROUPS g
    ORDER BY g.ID_FUNC_GROUP;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            groups = []
            for row in rows:
                groups.append({
                    "id_func_group": row.ID_FUNC_GROUP,
                    "description": row.DESCRIPCIONESP or row.DESCRIPCIONENG,
                    "function_count": row.FUNC_COUNT
                })

            return {"status": "success", "total": len(groups), "groups": groups}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--groups":
        print(json.dumps(list_ln4_groups(), indent=2, default=str))
    elif len(sys.argv) > 1:
        print(json.dumps(list_ln4_functions(group_filter=sys.argv[1]), indent=2, default=str))
    else:
        print(json.dumps(list_ln4_functions(), indent=2, default=str))
