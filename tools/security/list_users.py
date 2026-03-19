# tools/security/list_users.py
"""
Lista todos los usuarios de aplicación (APPUSER) del repositorio de seguridad
de PeopleNet.

Uso:
    python -m tools.security.list_users
    python -m tools.security.list_users --type Person
    python -m tools.security.list_users --search "ADMIN"
    python -m tools.security.list_users --locked
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_users(user_type=None, search=None, locked=False):
    """Obtiene la lista de usuarios de aplicación.

    Args:
        user_type: Filtrar por tipo de usuario (Person, System).
        search: Buscar en ID_APP_USER o N_APP_USER.
        locked: Si True, solo mostrar usuarios bloqueados.

    Returns:
        dict con status y lista de usuarios.
    """
    sql_query = """
    SELECT
        u.ID_APP_USER,
        u.N_APP_USER,
        u.ID_USER_TYPE,
        u.ID_APP_ROLE_DEF,
        u.IS_LOCK,
        u.PWD_EXPIRED,
        u.MAX_SESSIONS,
        u.ID_PERSON,
        u.USE_EMAIL_AS_ID,
        u.IS_GENERIC_USER,
        COUNT(DISTINCT aur.ID_APP_ROLE) AS role_count
    FROM
        M4RSC_APPUSER u
    LEFT JOIN
        M4RSC_APP_USR_ROLE aur ON u.ID_APP_USER = aur.ID_APP_USER
    """
    params = []
    conditions = []

    if user_type:
        conditions.append("u.ID_USER_TYPE = ?")
        params.append(user_type)

    if search:
        conditions.append("(u.ID_APP_USER LIKE ? OR u.N_APP_USER LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    if locked:
        conditions.append("u.IS_LOCK = 1")

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += """
    GROUP BY
        u.ID_APP_USER, u.N_APP_USER, u.ID_USER_TYPE, u.ID_APP_ROLE_DEF,
        u.IS_LOCK, u.PWD_EXPIRED, u.MAX_SESSIONS, u.ID_PERSON,
        u.USE_EMAIL_AS_ID, u.IS_GENERIC_USER
    ORDER BY
        u.ID_APP_USER;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params) if params else cursor.execute(sql_query)
            rows = cursor.fetchall()

            users = []
            for row in rows:
                users.append({
                    "id_app_user": row.ID_APP_USER,
                    "name": row.N_APP_USER,
                    "user_type": row.ID_USER_TYPE,
                    "default_role": row.ID_APP_ROLE_DEF,
                    "is_locked": bool(row.IS_LOCK) if row.IS_LOCK is not None else None,
                    "pwd_expired": bool(row.PWD_EXPIRED) if row.PWD_EXPIRED is not None else None,
                    "max_sessions": row.MAX_SESSIONS,
                    "id_person": row.ID_PERSON,
                    "use_email_as_id": bool(row.USE_EMAIL_AS_ID) if row.USE_EMAIL_AS_ID is not None else None,
                    "is_generic": bool(row.IS_GENERIC_USER) if row.IS_GENERIC_USER is not None else None,
                    "role_count": row.role_count,
                })

            return {
                "status": "success",
                "total": len(users),
                "users": users,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista usuarios de aplicación de PeopleNet.")
    parser.add_argument("--type", dest="user_type", help="Filtrar por tipo (Person, System)")
    parser.add_argument("--search", help="Buscar en ID o nombre de usuario")
    parser.add_argument("--locked", action="store_true", help="Solo mostrar usuarios bloqueados")
    args = parser.parse_args()

    result = list_users(user_type=args.user_type, search=args.search, locked=args.locked)
    print(json.dumps(result, indent=2, default=str))
