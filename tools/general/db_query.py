# tools/general/db_query.py
"""
Ejecuta consultas SQL arbitrarias contra la base de datos de PeopleNet
y devuelve los resultados en formato JSON.

Soporta consultas SELECT parametrizadas con límite configurable de filas.
Por seguridad, solo se permiten sentencias SELECT (no INSERT/UPDATE/DELETE).

Uso:
    python -m tools.general.db_query "SELECT TOP 10 * FROM M4RCH_TIS"
    python -m tools.general.db_query "SELECT * FROM M4RWF_BPC WHERE ID_BPC = ?" --params 2
    python -m tools.general.db_query "SELECT * FROM M4RCH_TIS" --limit 50
"""
import sys
import os
import json
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection
from tools.general.trace import db_tracer

# Límite máximo de filas por defecto para evitar descargas masivas accidentales
DEFAULT_MAX_ROWS = 500


def execute_query(sql_query, params=None, max_rows=DEFAULT_MAX_ROWS):
    """Ejecuta una consulta SQL SELECT y devuelve los resultados.

    Args:
        sql_query: La consulta SQL a ejecutar. Solo se permiten SELECT.
        params: Lista de parámetros para la consulta parametrizada (placeholders ?).
        max_rows: Número máximo de filas a devolver (default 500).

    Returns:
        dict con status, columns, rows y count, o estado de error.
    """
    if params is None:
        params = []

    # Validar que es una consulta SELECT
    stripped = sql_query.strip().upper()
    if not stripped.startswith("SELECT"):
        return {
            "status": "error",
            "message": "Solo se permiten consultas SELECT. Para modificar datos usa los scripts especializados."
        }

    # Validar que no contiene sentencias peligrosas embebidas
    dangerous_keywords = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ", "EXEC ", "EXECUTE "]
    for kw in dangerous_keywords:
        if kw in stripped:
            return {
                "status": "error",
                "message": f"La consulta contiene la palabra clave prohibida '{kw.strip()}'. Solo se permiten consultas SELECT puras."
            }

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            db_tracer.sql(sql_query, params=str(params) if params else "[]", max_rows=max_rows)
            t0 = time.perf_counter()

            if params:
                cursor.execute(sql_query, *params)
            else:
                cursor.execute(sql_query)

            # Obtener nombres de columnas desde la descripción del cursor
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Obtener filas con límite
            rows_raw = cursor.fetchmany(max_rows)
            rows = []
            for row in rows_raw:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                rows.append(row_dict)

            # Verificar si hay más filas que no se devolvieron
            extra = cursor.fetchone()
            truncated = extra is not None

            elapsed_ms = (time.perf_counter() - t0) * 1000
            db_tracer.info(
                "Query ejecutada",
                rows=len(rows),
                truncated=truncated,
                elapsed_ms=f"{elapsed_ms:.1f}",
                columns=len(columns),
            )

            return {
                "status": "success",
                "columns": columns,
                "count": len(rows),
                "truncated": truncated,
                "max_rows": max_rows,
                "rows": rows,
            }
    except Exception as e:
        db_tracer.error("Error ejecutando query", error=str(e), query=sql_query[:200])
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ejecuta consultas SQL SELECT contra PeopleNet.")
    parser.add_argument("sql", help="La consulta SQL a ejecutar.")
    parser.add_argument("--params", nargs="*", default=[], help="Parámetros para la consulta (placeholders ?).")
    parser.add_argument("--limit", type=int, default=DEFAULT_MAX_ROWS, help=f"Máximo de filas a devolver (default {DEFAULT_MAX_ROWS}).")

    args = parser.parse_args()
    result = execute_query(args.sql, params=args.params, max_rows=args.limit)
    print(json.dumps(result, indent=2, default=str))
