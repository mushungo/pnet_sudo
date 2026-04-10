# tools/security/find_roles_for_object.py
"""
Encuentra todos los roles que tienen permisos sobre un M4Object (canal/nodo/item).

Consulta M4RSC_CLIENT_USE en dirección inversa: dado un ID_T3 (y opcionalmente
ID_NODE e ID_ITEM), devuelve los roles con permisos explícitos sobre ese objeto.

Es el complemento inverso de get_role.py, que va de rol -> permisos.
Este tool va de objeto -> roles.

Uso:
    python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT"
    python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT" --node "MAIN_NODE"
    python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT" --node "MAIN_NODE" --item "CVE_ID"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def find_roles_for_object(id_t3, id_node=None, id_item=None):
    """Encuentra todos los roles con permisos sobre un objeto M4Object.

    Consulta M4RSC_CLIENT_USE JOIN M4RSC_APPROLE para resolver nombres.

    Args:
        id_t3: Identificador del canal (T3) — requerido.
        id_node: Filtrar por nodo específico (opcional).
        id_item: Filtrar por item específico (opcional, requiere id_node).

    Returns:
        dict con status, conteo y lista de roles con sus permisos.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["cu.ID_T3 = ?"]
            params = [id_t3]

            if id_node:
                where_clauses.append("cu.ID_NODE = ?")
                params.append(id_node)

            if id_item:
                where_clauses.append("cu.ID_ITEM = ?")
                params.append(id_item)

            where = " AND ".join(where_clauses)

            cursor.execute(f"""
                SELECT
                    cu.ID_GROUP,
                    ar.N_APP_ROLE_ESP,
                    ar.N_APP_ROLE_ENG,
                    cu.ID_T3, cu.ID_NODE, cu.ID_ITEM,
                    cu.CAN_READ, cu.CAN_WRITE, cu.CAN_EXECUTE,
                    cu.MUST_AUTHENTICATE, cu.ENCRYPTED
                FROM M4RSC_CLIENT_USE cu
                LEFT JOIN M4RSC_APPROLE ar ON cu.ID_GROUP = ar.ID_APP_ROLE
                WHERE {where}
                ORDER BY cu.ID_GROUP, cu.ID_NODE, cu.ID_ITEM
            """, *params)
            rows = cursor.fetchall()

            if not rows:
                return {
                    "status": "success",
                    "object_searched": {
                        "id_t3": id_t3,
                        "id_node": id_node,
                        "id_item": id_item,
                    },
                    "count": 0,
                    "message": f"No se encontraron roles con permisos sobre '{id_t3}'.",
                    "roles": [],
                }

            # Agrupar por rol
            roles_dict = {}
            for r in rows:
                role_id = r.ID_GROUP
                if role_id not in roles_dict:
                    roles_dict[role_id] = {
                        "id_role": role_id,
                        "name_esp": r.N_APP_ROLE_ESP,
                        "name_eng": r.N_APP_ROLE_ENG,
                        "permissions": [],
                    }
                roles_dict[role_id]["permissions"].append({
                    "id_node": r.ID_NODE,
                    "id_item": r.ID_ITEM,
                    "can_read": bool(r.CAN_READ) if r.CAN_READ is not None else None,
                    "can_write": bool(r.CAN_WRITE) if r.CAN_WRITE is not None else None,
                    "can_execute": bool(r.CAN_EXECUTE) if r.CAN_EXECUTE is not None else None,
                    "must_authenticate": bool(r.MUST_AUTHENTICATE) if r.MUST_AUTHENTICATE is not None else None,
                    "encrypted": bool(r.ENCRYPTED) if r.ENCRYPTED is not None else None,
                })

            roles_list = list(roles_dict.values())

            return {
                "status": "success",
                "object_searched": {
                    "id_t3": id_t3,
                    "id_node": id_node,
                    "id_item": id_item,
                },
                "count": len(roles_list),
                "total_permissions": len(rows),
                "roles": roles_list,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encuentra roles con permisos sobre un M4Object."
    )
    parser.add_argument("id_t3", help="Identificador del canal (ID_T3)")
    parser.add_argument("--node", help="Filtrar por nodo (ID_NODE)")
    parser.add_argument("--item", help="Filtrar por item (ID_ITEM)")
    args = parser.parse_args()

    result = find_roles_for_object(args.id_t3, id_node=args.node, id_item=args.item)
    print(json.dumps(result, indent=2, default=str))
