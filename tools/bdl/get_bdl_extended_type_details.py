# tools/bdl/get_bdl_extended_type_details.py
"""Obtiene las propiedades y lógica de comportamiento de un Tipo Extendido de la BDL."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_extended_type_details(id_type):
    """Obtiene los detalles completos de un tipo extendido: tipo base, formato y funciones."""
    query = """
    SELECT
        et.ID_TYPE, et.N_EXT_TYPEESP, et.N_EXT_TYPEENG, et.ID_M4_TYPE,
        mt.N_M4_TYPEESP, mt.N_M4_TYPEENG, et.PREC, et.SCALE, et.ID_DEFAULT_FUNC,
        def_func.N_FUNCTIONESP as DEF_FUNC_ESP, def_func.N_FUNCTIONENG as DEF_FUNC_ENG,
        et.DEFAULT_ARGS, et.ID_CONSTRAINT_FUNC,
        con_func.N_FUNCTIONESP as CON_FUNC_ESP, con_func.N_FUNCTIONENG as CON_FUNC_ENG,
        et.CONSTRAINT_ARGS, et.IS_ENCRYPTED
    FROM M4RDC_EXTENDED_TPS et
    LEFT JOIN M4RDC_LU_M4_TYPES mt ON et.ID_M4_TYPE = mt.ID_M4_TYPE
    LEFT JOIN M4RDC_BDL_FUNCTION def_func ON et.ID_DEFAULT_FUNC = def_func.ID_FUNCTION
    LEFT JOIN M4RDC_BDL_FUNCTION con_func ON et.ID_CONSTRAINT_FUNC = con_func.ID_FUNCTION
    WHERE et.ID_TYPE = ?;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, id_type)
            row = cursor.fetchone()

            if not row:
                return {"status": "not_found", "message": f"No se encontró el Tipo Extendido '{id_type}'."}

            details = {
                "id_type": row.ID_TYPE,
                "description": row.N_EXT_TYPEESP or row.N_EXT_TYPEENG,
                "base_type": f"{row.ID_M4_TYPE} ({row.N_M4_TYPEESP or row.N_M4_TYPEENG})",
                "format": {"precision": row.PREC, "scale": row.SCALE},
                "behavior": {
                    "default_function": f"{row.ID_DEFAULT_FUNC} ({row.DEF_FUNC_ESP or row.DEF_FUNC_ENG})",
                    "default_args": row.DEFAULT_ARGS,
                    "constraint_function": f"{row.ID_CONSTRAINT_FUNC} ({row.CON_FUNC_ESP or row.CON_FUNC_ENG})",
                    "constraint_args": row.CONSTRAINT_ARGS
                },
                "is_encrypted": bool(row.IS_ENCRYPTED)
            }
            return {"status": "success", "details": details}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_bdl_extended_type_details \"ID_TIPO\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_extended_type_details(sys.argv[1]), indent=2, default=str))
