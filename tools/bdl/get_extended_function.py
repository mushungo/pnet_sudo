# tools/bdl/get_extended_function.py
"""Obtiene la definición completa de una Función Extendida del repositorio de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_extended_function_details(id_function):
    """Obtiene los detalles de una función extendida y todos sus argumentos."""
    sql_function = """
    SELECT
        f.ID_FUNCTION,
        f.N_FUNCTIONESP, f.N_FUNCTIONENG,
        f.ID_M4_TYPE,
        t.N_M4_TYPEESP AS RETURN_TYPE_NAME_ESP,
        t.N_M4_TYPEENG AS RETURN_TYPE_NAME_ENG,
        f.PREC, f.SCALE,
        f.OWNER_FLAG, f.FREQUENT_USE, f.FREQUENT_USE_ORDER,
        f.DETAILSESP, f.DETAILSENG,
        f.OWNERSHIP, f.USABILITY
    FROM
        M4RDC_EXTENDED_FUN f
    LEFT JOIN
        M4RDC_LU_M4_TYPES t ON f.ID_M4_TYPE = t.ID_M4_TYPE
    WHERE
        f.ID_FUNCTION = ?;
    """
    sql_arguments = """
    SELECT
        a.ARGUMENT_POS, a.N_ARGUMENT, a.ID_M4_TYPE,
        t.N_M4_TYPEESP AS ARG_TYPE_NAME_ESP,
        t.N_M4_TYPEENG AS ARG_TYPE_NAME_ENG,
        a.IS_MANDATORY, a.VALUE_MIN, a.VALUE_MAX, a.OWNER_FLAG
    FROM
        M4RDC_EXT_FUNC_ARG a
    LEFT JOIN
        M4RDC_LU_M4_TYPES t ON a.ID_M4_TYPE = t.ID_M4_TYPE
    WHERE
        a.ID_FUNCTION = ?
    ORDER BY
        a.ARGUMENT_POS;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(sql_function, id_function)
            func_row = cursor.fetchone()

            if not func_row:
                return {"status": "not_found", "message": f"No se encontró la función extendida con ID '{id_function}'."}

            function_details = {
                "id_function": func_row.ID_FUNCTION,
                "name": func_row.N_FUNCTIONESP or func_row.N_FUNCTIONENG,
                "name_eng": func_row.N_FUNCTIONENG,
                "return_type_id": func_row.ID_M4_TYPE,
                "return_type_name": func_row.RETURN_TYPE_NAME_ESP or func_row.RETURN_TYPE_NAME_ENG,
                "precision": func_row.PREC,
                "scale": func_row.SCALE,
                "owner_flag": func_row.OWNER_FLAG,
                "frequent_use": bool(func_row.FREQUENT_USE),
                "frequent_use_order": func_row.FREQUENT_USE_ORDER,
                "details": func_row.DETAILSESP or func_row.DETAILSENG,
                "details_eng": func_row.DETAILSENG,
                "ownership": func_row.OWNERSHIP,
                "usability": func_row.USABILITY,
                "arguments": []
            }

            cursor.execute(sql_arguments, id_function)
            arg_rows = cursor.fetchall()

            for arg in arg_rows:
                function_details["arguments"].append({
                    "position": arg.ARGUMENT_POS,
                    "name": arg.N_ARGUMENT,
                    "type_id": arg.ID_M4_TYPE,
                    "type_name": arg.ARG_TYPE_NAME_ESP or arg.ARG_TYPE_NAME_ENG,
                    "is_mandatory": bool(arg.IS_MANDATORY),
                    "value_min": arg.VALUE_MIN,
                    "value_max": arg.VALUE_MAX,
                    "owner_flag": arg.OWNER_FLAG
                })

            return function_details

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_extended_function \"ID_FUNCTION\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_extended_function_details(sys.argv[1]), indent=2, default=str))
