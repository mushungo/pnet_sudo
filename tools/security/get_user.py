# tools/security/get_user.py
"""
Obtiene el detalle completo de un usuario de aplicación, incluyendo
roles asignados, alias de dominio y permisos de cliente.

Uso:
    python -m tools.security.get_user "ID_APP_USER"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_user_details(id_app_user):
    """Obtiene el detalle completo de un usuario de aplicación.

    Args:
        id_app_user: Identificador del usuario.

    Returns:
        dict con el detalle completo o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Usuario principal
            cursor.execute(
                "SELECT ID_APP_USER, N_APP_USER, ID_USER_TYPE, "
                "ID_APP_ROLE_DEF, IS_LOCK, PWD_EXPIRED, MAX_SESSIONS, "
                "ID_PERSON, USE_EMAIL_AS_ID, IS_GENERIC_USER, "
                "HR_INSIGHTS_AUTH_LEVEL "
                "FROM M4RSC_APPUSER WHERE ID_APP_USER = ?",
                id_app_user
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el usuario '{id_app_user}'."
                }

            result = {
                "id_app_user": main_row.ID_APP_USER,
                "name": main_row.N_APP_USER,
                "user_type": main_row.ID_USER_TYPE,
                "default_role": main_row.ID_APP_ROLE_DEF,
                "is_locked": bool(main_row.IS_LOCK) if main_row.IS_LOCK is not None else None,
                "pwd_expired": bool(main_row.PWD_EXPIRED) if main_row.PWD_EXPIRED is not None else None,
                "max_sessions": main_row.MAX_SESSIONS,
                "id_person": main_row.ID_PERSON,
                "use_email_as_id": bool(main_row.USE_EMAIL_AS_ID) if main_row.USE_EMAIL_AS_ID is not None else None,
                "is_generic": bool(main_row.IS_GENERIC_USER) if main_row.IS_GENERIC_USER is not None else None,
                "hr_insights_auth_level": main_row.HR_INSIGHTS_AUTH_LEVEL,
            }

            # 2. Roles asignados
            cursor.execute(
                "SELECT aur.ID_APP_ROLE, r.N_APP_ROLE_ESP, r.N_APP_ROLE_ENG, "
                "aur.DT_START, aur.DT_END, aur.ID_ORGANIZATION_US "
                "FROM M4RSC_APP_USR_ROLE aur "
                "LEFT JOIN M4RSC_APPROLE r ON aur.ID_APP_ROLE = r.ID_APP_ROLE "
                "WHERE aur.ID_APP_USER = ? "
                "ORDER BY aur.ID_APP_ROLE",
                id_app_user
            )
            result["roles"] = []
            for row in cursor.fetchall():
                result["roles"].append({
                    "id_app_role": row.ID_APP_ROLE,
                    "name_esp": row.N_APP_ROLE_ESP,
                    "name_eng": row.N_APP_ROLE_ENG,
                    "dt_start": row.DT_START,
                    "dt_end": row.DT_END,
                    "organization": row.ID_ORGANIZATION_US,
                })

            # 3. Alias de dominio
            cursor.execute(
                "SELECT ID_DOMAIN, N_ALIAS "
                "FROM M4RSC_USER_ALIAS "
                "WHERE ID_APP_USER = ? ORDER BY ID_DOMAIN",
                id_app_user
            )
            result["aliases"] = []
            for row in cursor.fetchall():
                result["aliases"].append({
                    "id_domain": row.ID_DOMAIN,
                    "alias": row.N_ALIAS,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.security.get_user \"ID_APP_USER\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_user_details(sys.argv[1]), indent=2, default=str))
