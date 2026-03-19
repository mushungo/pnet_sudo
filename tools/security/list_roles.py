# tools/security/list_roles.py
"""
Lista todos los roles de aplicación (APPROLE) del repositorio de seguridad
de PeopleNet.

Uso:
    python -m tools.security.list_roles
    python -m tools.security.list_roles --search "ADMIN"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_roles(search=None):
    """Obtiene la lista de roles de aplicación.

    Args:
        search: Buscar en ID_APP_ROLE o nombres descriptivos.

    Returns:
        dict con status y lista de roles.
    """
    sql_query = """
    SELECT
        r.ID_APP_ROLE,
        r.N_APP_ROLE_ESP,
        r.N_APP_ROLE_ENG,
        COUNT(DISTINCT aur.ID_APP_USER) AS user_count
    FROM
        M4RSC_APPROLE r
    LEFT JOIN
        M4RSC_APP_USR_ROLE aur ON r.ID_APP_ROLE = aur.ID_APP_ROLE
    """
    params = []
    conditions = []

    if search:
        conditions.append("(r.ID_APP_ROLE LIKE ? OR r.N_APP_ROLE_ESP LIKE ? OR r.N_APP_ROLE_ENG LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += """
    GROUP BY
        r.ID_APP_ROLE, r.N_APP_ROLE_ESP, r.N_APP_ROLE_ENG
    ORDER BY
        r.ID_APP_ROLE;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params) if params else cursor.execute(sql_query)
            rows = cursor.fetchall()

            roles = []
            for row in rows:
                roles.append({
                    "id_app_role": row.ID_APP_ROLE,
                    "name_esp": row.N_APP_ROLE_ESP,
                    "name_eng": row.N_APP_ROLE_ENG,
                    "user_count": row.user_count,
                })

            return {
                "status": "success",
                "total": len(roles),
                "roles": roles,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista roles de aplicación de PeopleNet.")
    parser.add_argument("--search", help="Buscar en ID o nombres de rol")
    args = parser.parse_args()

    result = list_roles(search=args.search)
    print(json.dumps(result, indent=2, default=str))
