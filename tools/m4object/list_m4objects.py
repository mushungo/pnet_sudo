# tools/m4object/list_m4objects.py
"""
Lista todos los m4objects (canales) disponibles en el repositorio de metadatos de PeopleNet.

Devuelve una lista con ID_T3, nombre descriptivo, categoría, tipo de stream
y número de nodos de cada canal.

Uso:
    python -m tools.m4object.list_m4objects
    python -m tools.m4object.list_m4objects --category PAYROLL
    python -m tools.m4object.list_m4objects --search "employee"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_m4objects(category=None, search=None):
    """Obtiene la lista de todos los m4objects con información resumida.

    Args:
        category: Filtrar por ID_CATEGORY (ej. PAYROLL, HR_ADMIN).
        search: Texto libre para buscar en ID_T3 o N_T3ESP.

    Returns:
        dict con status y lista de m4objects.
    """
    sql_query = """
    SELECT
        t3.ID_T3,
        t3.N_T3ESP,
        t3.N_T3ENG,
        t3.ID_CATEGORY,
        t3.ID_SUBCATEGORY,
        t3.ID_STREAM_TYPE,
        t3.CS_EXE_TYPE,
        t3.HAVE_SECURITY,
        t3.IS_EXTERNAL,
        COUNT(DISTINCT n.ID_NODE) AS node_count
    FROM
        M4RCH_T3S t3
    LEFT JOIN
        M4RCH_NODES n ON t3.ID_T3 = n.ID_T3
    """
    params = []
    conditions = []

    if category:
        conditions.append("t3.ID_CATEGORY = ?")
        params.append(category)

    if search:
        conditions.append("(t3.ID_T3 LIKE ? OR t3.N_T3ESP LIKE ? OR t3.N_T3ENG LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += """
    GROUP BY
        t3.ID_T3, t3.N_T3ESP, t3.N_T3ENG, t3.ID_CATEGORY,
        t3.ID_SUBCATEGORY, t3.ID_STREAM_TYPE, t3.CS_EXE_TYPE,
        t3.HAVE_SECURITY, t3.IS_EXTERNAL
    ORDER BY
        t3.ID_T3;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params) if params else cursor.execute(sql_query)
            rows = cursor.fetchall()

            m4objects = []
            for row in rows:
                m4objects.append({
                    "id_t3": row.ID_T3,
                    "name_esp": row.N_T3ESP,
                    "name_eng": row.N_T3ENG,
                    "category": row.ID_CATEGORY,
                    "subcategory": row.ID_SUBCATEGORY,
                    "stream_type": row.ID_STREAM_TYPE,
                    "exe_type": row.CS_EXE_TYPE,
                    "has_security": bool(row.HAVE_SECURITY) if row.HAVE_SECURITY is not None else None,
                    "is_external": bool(row.IS_EXTERNAL) if row.IS_EXTERNAL is not None else None,
                    "node_count": row.node_count,
                })

            return {
                "status": "success",
                "total": len(m4objects),
                "m4objects": m4objects,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista m4objects (canales) de PeopleNet.")
    parser.add_argument("--category", help="Filtrar por categoría (ej. PAYROLL, HR_ADMIN)")
    parser.add_argument("--search", help="Buscar por texto en ID_T3 o nombres descriptivos")
    args = parser.parse_args()

    result = list_m4objects(category=args.category, search=args.search)
    print(json.dumps(result, indent=2, default=str))
