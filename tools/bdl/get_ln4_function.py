# tools/bdl/get_ln4_function.py
"""Obtiene la definición completa de una función LN4 del repositorio de PeopleNet."""
import sys
import os
import json


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_ln4_function(id_ln4_function):
    """Obtiene los detalles completos de una función LN4, incluyendo comentarios y argumentos.

    Consulta M4RCH_LN4_FUNCTION, M4RCH_LN4_FUNCTIO1, M4RCH_LN4_FUNC_ARG,
    M4RCH_FUNC_GROUPS y M4RDC_LU_M4_TYPES.
    """
    func_query = """
    SELECT
        f.ID_LN4_FUNCTION,
        f.N_LN4_FUNCTION,
        f.ITEM,
        f.VARIABLE_ARGUMENTS,
        f.FUNCTION_LEVEL,
        f.ID_FUNC_GROUP,
        g.DESCRIPCIONESP AS GROUP_ESP,
        g.DESCRIPCIONENG AS GROUP_ENG,
        fc.COMENTESP,
        fc.COMENTENG
    FROM M4RCH_LN4_FUNCTION f
    LEFT JOIN M4RCH_FUNC_GROUPS g ON f.ID_FUNC_GROUP = g.ID_FUNC_GROUP
    LEFT JOIN M4RCH_LN4_FUNCTIO1 fc ON f.ID_LN4_FUNCTION = fc.ID_LN4_FUNCTION
    WHERE f.ID_LN4_FUNCTION = ?;
    """
    args_query = """
    SELECT
        a.ID_LN4_FUNC_ARG,
        a.N_LN4_ARGUMENTS,
        a.POSITION,
        a.ID_M4_TYPE,
        t.N_M4_TYPEESP,
        t.N_M4_TYPEENG,
        a.ID_ARGUMENT_TYPE,
        a.OPTIONAL,
        a.COMENTESP,
        a.COMENTENG
    FROM M4RCH_LN4_FUNC_ARG a
    LEFT JOIN M4RDC_LU_M4_TYPES t ON a.ID_M4_TYPE = t.ID_M4_TYPE
    WHERE a.ID_LN4_FUNCTION = ?
    ORDER BY a.POSITION;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(func_query, id_ln4_function)
            row = cursor.fetchone()

            if not row:
                return {"status": "not_found", "message": f"No se encontró la función LN4 con ID '{id_ln4_function}'."}

            cursor.execute(args_query, id_ln4_function)
            arg_rows = cursor.fetchall()

            arguments = []
            for arg in arg_rows:
                arguments.append({
                    "id_arg": arg.ID_LN4_FUNC_ARG,
                    "name": arg.N_LN4_ARGUMENTS,
                    "position": arg.POSITION,
                    "type_id": arg.ID_M4_TYPE,
                    "type_name": arg.N_M4_TYPEESP or arg.N_M4_TYPEENG,
                    "argument_type": arg.ID_ARGUMENT_TYPE,
                    "optional": bool(arg.OPTIONAL) if arg.OPTIONAL is not None else None,
                    "comment": arg.COMENTESP or arg.COMENTENG,
                    "comment_eng": arg.COMENTENG
                })

            result = {
                "status": "success",
                "function": {
                    "id_ln4_function": row.ID_LN4_FUNCTION,
                    "name": row.N_LN4_FUNCTION,
                    "item": row.ITEM,
                    "variable_arguments": bool(row.VARIABLE_ARGUMENTS) if row.VARIABLE_ARGUMENTS is not None else None,
                    "function_level": row.FUNCTION_LEVEL,
                    "group_id": row.ID_FUNC_GROUP,
                    "group_name": row.GROUP_ESP or row.GROUP_ENG,
                    "comment": row.COMENTESP or row.COMENTENG,
                    "comment_eng": row.COMENTENG,
                    "arguments": arguments
                }
            }
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_ln4_function <ID_LN4_FUNCTION>"}, indent=2))
        sys.exit(1)
    print(json.dumps(get_ln4_function(sys.argv[1]), indent=2, default=str))
