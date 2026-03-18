# tools/bdl/list_extended_functions.py
"""Lista todas las Funciones Extendidas disponibles en el repositorio de metadatos."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_all_extended_functions():
    """Obtiene una lista de todas las funciones extendidas con información resumida."""
    sql_query = """
    SELECT
        f.ID_FUNCTION,
        f.N_FUNCTIONESP, f.N_FUNCTIONENG,
        f.ID_M4_TYPE,
        t.N_M4_TYPEESP AS RETURN_TYPE_NAME_ESP,
        t.N_M4_TYPEENG AS RETURN_TYPE_NAME_ENG,
        f.FREQUENT_USE,
        (SELECT COUNT(*) FROM M4RDC_EXT_FUNC_ARG a WHERE a.ID_FUNCTION = f.ID_FUNCTION) AS ARG_COUNT
    FROM
        M4RDC_EXTENDED_FUN f
    LEFT JOIN
        M4RDC_LU_M4_TYPES t ON f.ID_M4_TYPE = t.ID_M4_TYPE
    ORDER BY
        f.ID_FUNCTION;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            functions = []
            for row in rows:
                functions.append({
                    "id_function": row.ID_FUNCTION,
                    "name": row.N_FUNCTIONESP or row.N_FUNCTIONENG,
                    "return_type_id": row.ID_M4_TYPE,
                    "return_type_name": row.RETURN_TYPE_NAME_ESP or row.RETURN_TYPE_NAME_ENG,
                    "frequent_use": bool(row.FREQUENT_USE),
                    "arg_count": row.ARG_COUNT
                })
            return {"status": "success", "count": len(functions), "functions": functions}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = get_all_extended_functions()
    print(json.dumps(result, indent=2, default=str))
