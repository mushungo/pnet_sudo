# tools/security/get_role.py
"""
Obtiene el detalle completo de un rol de aplicación, incluyendo
todos los usuarios asignados y permisos de cliente.

Uso:
    python -m tools.security.get_role "ID_APP_ROLE"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_role_details(id_app_role):
    """Obtiene el detalle completo de un rol de aplicación.

    Args:
        id_app_role: Identificador del rol.

    Returns:
        dict con el detalle completo o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Rol principal
            cursor.execute(
                "SELECT ID_APP_ROLE, N_APP_ROLE_ESP, N_APP_ROLE_ENG "
                "FROM M4RSC_APPROLE WHERE ID_APP_ROLE = ?",
                id_app_role
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el rol '{id_app_role}'."
                }

            result = {
                "id_app_role": main_row.ID_APP_ROLE,
                "name_esp": main_row.N_APP_ROLE_ESP,
                "name_eng": main_row.N_APP_ROLE_ENG,
            }

            # 2. Usuarios asignados
            cursor.execute(
                "SELECT aur.ID_APP_USER, u.N_APP_USER, u.ID_USER_TYPE, "
                "aur.DT_START, aur.DT_END, aur.ID_ORGANIZATION_US "
                "FROM M4RSC_APP_USR_ROLE aur "
                "LEFT JOIN M4RSC_APPUSER u ON aur.ID_APP_USER = u.ID_APP_USER "
                "WHERE aur.ID_APP_ROLE = ? "
                "ORDER BY aur.ID_APP_USER",
                id_app_role
            )
            result["users"] = []
            for row in cursor.fetchall():
                result["users"].append({
                    "id_app_user": row.ID_APP_USER,
                    "name": row.N_APP_USER,
                    "user_type": row.ID_USER_TYPE,
                    "dt_start": row.DT_START,
                    "dt_end": row.DT_END,
                    "organization": row.ID_ORGANIZATION_US,
                })

            # 3. Permisos de cliente (CLIENT_USE) para este rol
            cursor.execute(
                "SELECT ID_GROUP, ID_T3, ID_NODE, ID_ITEM, "
                "CAN_READ, CAN_WRITE, CAN_EXECUTE, "
                "MUST_AUTHENTICATE, ENCRYPTED "
                "FROM M4RSC_CLIENT_USE "
                "WHERE ID_GROUP = ? "
                "ORDER BY ID_T3, ID_NODE, ID_ITEM",
                id_app_role
            )
            result["permissions"] = []
            for row in cursor.fetchall():
                result["permissions"].append({
                    "id_group": row.ID_GROUP,
                    "id_t3": row.ID_T3,
                    "id_node": row.ID_NODE,
                    "id_item": row.ID_ITEM,
                    "can_read": bool(row.CAN_READ) if row.CAN_READ is not None else None,
                    "can_write": bool(row.CAN_WRITE) if row.CAN_WRITE is not None else None,
                    "can_execute": bool(row.CAN_EXECUTE) if row.CAN_EXECUTE is not None else None,
                    "must_authenticate": bool(row.MUST_AUTHENTICATE) if row.MUST_AUTHENTICATE is not None else None,
                    "encrypted": bool(row.ENCRYPTED) if row.ENCRYPTED is not None else None,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.security.get_role \"ID_APP_ROLE\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_role_details(sys.argv[1]), indent=2, default=str))
