# tools/menus/list_menus.py
"""
Lista las opciones de menú registradas en PeopleNet (SMN_OPTIONS / M4RMN_OPTIONS).

Uso:
    python -m tools.menus.list_menus
    python -m tools.menus.list_menus --search "empleado"
    python -m tools.menus.list_menus --role HRM_MANAGER
    python -m tools.menus.list_menus --parent PEOPLENET
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_menus(search=None, role=None, parent=None, limit=200):
    """Lista opciones de menú con filtros opcionales.

    Consulta M4RMN_OPTIONS (catálogo) con JOIN opcional a M4RMN_TREE
    para filtrar por menú padre o por rol de aplicación.

    Args:
        search: Buscar en ID_MENU o textos ESP/ENG del menú.
        role: Filtrar por ID_APPROLE (en SMN_OPTIONS o SMN_TREE).
        parent: Filtrar hijos directos de un ID_PARENT_MENU.
        limit: Máximo de resultados (default 200).

    Returns:
        dict con status, total y lista de opciones de menú.
    """
    conditions = []
    params = []

    base_sql = """
    SELECT DISTINCT
        o.ID_MENU,
        o.TRANS_MENUESP,
        o.TRANS_MENUENG,
        o.ID_BP,
        o.ICON,
        o.OWNER_FLAG,
        o.ID_APPROLE,
        o.AVAILABLE_VERSION,
        o.ID_DEPENDING_MENU,
        o.SHOW_IN_MAP,
        o.DT_LAST_UPDATE
    FROM M4RMN_OPTIONS o
    """

    if parent:
        base_sql += " INNER JOIN M4RMN_TREE t ON t.ID_MENU = o.ID_MENU AND t.ID_PARENT_MENU = ?"
        params.append(parent)

    if search:
        pattern = f"%{search}%"
        conditions.append(
            "(o.ID_MENU LIKE ? OR o.TRANS_MENUESP LIKE ? OR o.TRANS_MENUENG LIKE ? "
            "OR o.KEYWORDSESP LIKE ? OR o.KEYWORDSENG LIKE ?)"
        )
        params.extend([pattern, pattern, pattern, pattern, pattern])

    if role:
        conditions.append(
            "(o.ID_APPROLE = ? OR EXISTS ("
            "  SELECT 1 FROM M4RMN_TREE tr "
            "  WHERE tr.ID_MENU = o.ID_MENU AND tr.ID_APPROLE = ?"
            "))"
        )
        params.extend([role, role])

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += f" ORDER BY o.ID_MENU OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_sql, *params) if params else cursor.execute(base_sql)
            rows = cursor.fetchall()

            menus = []
            for row in rows:
                menus.append({
                    "id_menu": row.ID_MENU,
                    "name_esp": row.TRANS_MENUESP,
                    "name_eng": row.TRANS_MENUENG,
                    "id_bp": row.ID_BP,
                    "icon": row.ICON,
                    "owner_flag": row.OWNER_FLAG,
                    "id_approle": row.ID_APPROLE,
                    "available_version": row.AVAILABLE_VERSION,
                    "id_depending_menu": row.ID_DEPENDING_MENU,
                    "show_in_map": bool(row.SHOW_IN_MAP) if row.SHOW_IN_MAP is not None else None,
                    "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                })

            return {
                "status": "success",
                "total": len(menus),
                "filters": {
                    "search": search,
                    "role": role,
                    "parent": parent,
                    "limit": limit,
                },
                "menus": menus,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista opciones de menú de PeopleNet.")
    parser.add_argument("--search", help="Buscar en ID, nombre ESP/ENG o palabras clave")
    parser.add_argument("--role", help="Filtrar por ID_APPROLE")
    parser.add_argument("--parent", help="Mostrar hijos directos de un ID_PARENT_MENU")
    parser.add_argument("--limit", type=int, default=200, help="Máximo de resultados (default: 200)")
    args = parser.parse_args()

    result = list_menus(search=args.search, role=args.role, parent=args.parent, limit=args.limit)
    print(json.dumps(result, indent=2, default=str))
