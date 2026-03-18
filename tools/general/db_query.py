# tools/general/db_query.py
"""
Ejecuta consultas SQL arbitrarias contra la base de datos de PeopleNet
y devuelve los resultados en formato JSON.

TODO: Implementar la lógica de ejecución de consultas parametrizadas
con soporte para SELECT, y potencialmente INSERT/UPDATE con confirmación.
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def execute_query(sql_query, params=None):
    """Ejecuta una consulta SQL y devuelve los resultados.

    Args:
        sql_query: La consulta SQL a ejecutar.
        params: Parámetros opcionales para la consulta parametrizada.

    Raises:
        NotImplementedError: Este script aún no está implementado.
    """
    raise NotImplementedError(
        "La ejecución de consultas arbitrarias no está implementada. "
        "Usa los scripts especializados de tools/bdl/ para consultas predefinidas."
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.general.db_query \"SELECT ...\""}, indent=2))
        sys.exit(1)

    try:
        result = execute_query(sys.argv[1])
        print(json.dumps(result, indent=2, default=str))
    except NotImplementedError as e:
        print(json.dumps({"status": "not_implemented", "message": str(e)}, indent=2))
        sys.exit(1)
