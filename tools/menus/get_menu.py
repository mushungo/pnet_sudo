# tools/menus/get_menu.py
"""
Obtiene el detalle completo de una opción de menú de PeopleNet.

Incluye: definición principal, posiciones en el árbol (padres e hijos),
argumentos, contadores de uso y favoritos.

Todas las tablas consultadas pertenecen al subsistema M4RMN_*.

Uso:
    python -m tools.menus.get_menu <ID_MENU>
    python -m tools.menus.get_menu <ID_MENU> --include-children
    python -m tools.menus.get_menu <ID_MENU> --include-hits
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def decode_owner_flag(value):
    """Decodifica OWNER_FLAG por rango."""
    if value is None:
        return None
    if value == 0:
        return "Sin propietario"
    if value == 1:
        return "Standard"
    if value == 2:
        return "Standard Extendido"
    if 3 <= value <= 9:
        return "Reservado"
    if 10 <= value <= 19:
        return "Standard Premium"
    if value == 20:
        return "Corporate"
    if value == 21:
        return "Corporate Extendido"
    if 22 <= value <= 29:
        return "Reservado Corporate"
    if 40 <= value <= 49:
        return "Country"
    if 50 <= value <= 99:
        return "Client"
    return f"Custom({value})"


def get_menu(id_menu, include_children=False, include_hits=False, include_bp=False):
    """Obtiene la definición completa de una opción de menú.

    Consulta: M4RMN_OPTIONS, M4RMN_OPTIONS1 (URLs), M4RMN_TREE (árbol),
    M4RMN_ARGUMENTS (argumentos), M4RMN_MENU_HITS (uso),
    M4RMN_FAVORIT_TREE (favoritos).

    Args:
        id_menu: Identificador lógico del menú (ej: HRM_EMPLOYEES).
        include_children: Si True, lista los hijos directos en el árbol.
        include_hits: Si True, incluye contadores de uso por usuario.

    Returns:
        dict con la definición completa o estado de error.
    """
    if not id_menu:
        return {"status": "error", "message": "id_menu es requerido."}

    id_menu = id_menu.strip()

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Definición principal
            cursor.execute(
                "SELECT o.ID_MENU, o.TRANS_MENUESP, o.TRANS_MENUENG, "
                "o.TRANS_MENUFRA, o.TRANS_MENUGER, o.TRANS_MENUBRA, "
                "o.TRANS_MENUITA, o.TRANS_MENUGEN, "
                "o.N_MENU, o.N_MENUESP, o.N_MENUENG, "
                "o.ID_BP, o.ID_BP_AUX_1, o.ID_BP_AUX_2, "
                "o.ICON, o.ICON_AUX, o.OWNER_FLAG, "
                "o.ID_APPROLE, o.ID_HELPTOPIC, "
                "o.AVAILABLE_VERSION, o.ID_DEPENDING_MENU, "
                "o.POSITION_DEPENDING_MENU, "
                "o.KEYWORDSESP, o.KEYWORDSENG, "
                "o.ID_SECUSER, o.DT_LAST_UPDATE, "
                "o.ID_SCREEN, o.OWNERSHIP, o.USABILITY "
                "FROM M4RMN_OPTIONS o "
                "WHERE o.ID_MENU = ?",
                id_menu
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {"status": "not_found", "message": f"No se encontró el menú '{id_menu}'."}

            result = {
                "id_menu": main_row.ID_MENU,
                "names": {
                    "esp": main_row.TRANS_MENUESP,
                    "eng": main_row.TRANS_MENUENG,
                    "fra": main_row.TRANS_MENUFRA,
                    "ger": main_row.TRANS_MENUGER,
                    "bra": main_row.TRANS_MENUBRA,
                    "ita": main_row.TRANS_MENUITA,
                    "gen": main_row.TRANS_MENUGEN,
                },
                "descriptions": {
                    "default": main_row.N_MENU,
                    "esp": main_row.N_MENUESP,
                    "eng": main_row.N_MENUENG,
                },
                "business_process": {
                    "id_bp": main_row.ID_BP,
                    "id_bp_aux_1": main_row.ID_BP_AUX_1,
                    "id_bp_aux_2": main_row.ID_BP_AUX_2,
                },
                "icon": main_row.ICON,
                "icon_aux": main_row.ICON_AUX,
                "owner_flag": main_row.OWNER_FLAG,
                "owner_flag_name": decode_owner_flag(main_row.OWNER_FLAG),
                "id_approle": main_row.ID_APPROLE,
                "id_helptopic": main_row.ID_HELPTOPIC,
                "available_version": main_row.AVAILABLE_VERSION,
                "pnet_plus": {
                    "id_depending_menu": main_row.ID_DEPENDING_MENU,
                    "position": main_row.POSITION_DEPENDING_MENU,
                },
                "keywords": {
                    "esp": main_row.KEYWORDSESP,
                    "eng": main_row.KEYWORDSENG,
                },
                "audit": {
                    "id_user": main_row.ID_SECUSER,
                    "dt_last_update": str(main_row.DT_LAST_UPDATE) if main_row.DT_LAST_UPDATE else None,
                },
                "id_screen": main_row.ID_SCREEN,
                "ownership": main_row.OWNERSHIP,
                "usability": main_row.USABILITY,
            }

            # 2. URLs (tabla auxiliar M4RMN_OPTIONS1)
            cursor.execute(
                "SELECT N_HTTPENG, N_HTTPESP, N_HTTPFRA, N_HTTPGER, "
                "N_HTTPBRA, N_HTTPITA, N_HTTPGEN "
                "FROM M4RMN_OPTIONS1 WHERE ID_MENU = ?",
                id_menu
            )
            url_row = cursor.fetchone()
            if url_row:
                result["urls"] = {
                    "eng": url_row.N_HTTPENG,
                    "esp": url_row.N_HTTPESP,
                    "fra": url_row.N_HTTPFRA,
                    "ger": url_row.N_HTTPGER,
                    "bra": url_row.N_HTTPBRA,
                    "ita": url_row.N_HTTPITA,
                    "gen": url_row.N_HTTPGEN,
                }
            else:
                result["urls"] = None

            # 3. Posiciones en el árbol (padres)
            cursor.execute(
                "SELECT t.ID_PARENT_MENU, t.POSITION, t.ID_APPROLE, "
                "p.TRANS_MENUESP AS parent_name_esp, "
                "p.TRANS_MENUENG AS parent_name_eng "
                "FROM M4RMN_TREE t "
                "LEFT JOIN M4RMN_OPTIONS p ON p.ID_MENU = t.ID_PARENT_MENU "
                "WHERE t.ID_MENU = ? "
                "ORDER BY t.ID_PARENT_MENU",
                id_menu
            )
            result["tree_positions"] = []
            for row in cursor.fetchall():
                result["tree_positions"].append({
                    "id_parent_menu": row.ID_PARENT_MENU,
                    "parent_name_esp": row.parent_name_esp,
                    "parent_name_eng": row.parent_name_eng,
                    "position": row.POSITION,
                    "id_approle": row.ID_APPROLE,
                })

            # 4. Hijos directos (opcional)
            if include_children:
                cursor.execute(
                    "SELECT t.ID_MENU, t.POSITION, t.ID_APPROLE, "
                    "o.TRANS_MENUESP, o.TRANS_MENUENG, o.ID_BP "
                    "FROM M4RMN_TREE t "
                    "INNER JOIN M4RMN_OPTIONS o ON o.ID_MENU = t.ID_MENU "
                    "WHERE t.ID_PARENT_MENU = ? "
                    "ORDER BY t.POSITION, t.ID_MENU",
                    id_menu
                )
                result["children"] = []
                for row in cursor.fetchall():
                    result["children"].append({
                        "id_menu": row.ID_MENU,
                        "name_esp": row.TRANS_MENUESP,
                        "name_eng": row.TRANS_MENUENG,
                        "position": row.POSITION,
                        "id_bp": row.ID_BP,
                        "id_approle": row.ID_APPROLE,
                    })
                result["children_count"] = len(result["children"])

            # 5. Argumentos
            cursor.execute(
                "SELECT ID_TREE_MENU, ID_ARGUMENT, ZVALUE "
                "FROM M4RMN_ARGUMENTS WHERE ID_MENU = ? "
                "ORDER BY ID_TREE_MENU, ID_ARGUMENT",
                id_menu
            )
            result["arguments"] = []
            for row in cursor.fetchall():
                result["arguments"].append({
                    "id_tree_menu": row.ID_TREE_MENU,
                    "id_argument": row.ID_ARGUMENT,
                    "value": row.ZVALUE,
                })

            # 6. Contadores de uso (opcional)
            if include_hits:
                cursor.execute(
                    "SELECT TOP 20 ID_APP_USR, NUM_COUNTER "
                    "FROM M4RMN_MENU_HITS WHERE ID_MENU = ? "
                    "ORDER BY NUM_COUNTER DESC",
                    id_menu
                )
                result["hits"] = []
                for row in cursor.fetchall():
                    result["hits"].append({
                        "id_app_usr": row.ID_APP_USR,
                        "num_counter": row.NUM_COUNTER,
                    })
                result["hit_total"] = sum(h["num_counter"] for h in result["hits"] if h["num_counter"])
            else:
                cursor.execute(
                    "SELECT COUNT(*) AS users, ISNULL(SUM(NUM_COUNTER), 0) AS total "
                    "FROM M4RMN_MENU_HITS WHERE ID_MENU = ?",
                    id_menu
                )
                hit_row = cursor.fetchone()
                result["hit_summary"] = {
                    "distinct_users": hit_row.users if hit_row else 0,
                    "total_hits": hit_row.total if hit_row else 0,
                }

            # 7. Favoritos (M4RMN_FAVORIT_TREE)
            cursor.execute(
                "SELECT COUNT(DISTINCT ft.ID_APP_USR) AS fav_users "
                "FROM M4RMN_FAVORIT_TREE ft "
                "WHERE ft.ID_MENU = ?",
                id_menu
            )
            fav_row = cursor.fetchone()
            result["favourites_count"] = fav_row.fav_users if fav_row else 0

            # 8. BP vinculado y presentaciones (opcional)
            if include_bp and result["business_process"]["id_bp"]:
                bp_id = result["business_process"]["id_bp"]
                cursor.execute(
                    "SELECT ID_BP, N_BPESP, N_BPENG, ID_T3, SECURITY_TYPE, STATE, OWNER_FLAG "
                    "FROM M4RBP_DEF WHERE ID_BP = ?",
                    bp_id
                )
                bp_row = cursor.fetchone()
                if bp_row:
                    bp_def = {
                        "id_bp": bp_row.ID_BP,
                        "name_esp": bp_row.N_BPESP,
                        "name_eng": bp_row.N_BPENG,
                        "id_t3": bp_row.ID_T3,
                        "security_type": bp_row.SECURITY_TYPE,
                        "state": bp_row.STATE,
                        "owner_flag": bp_row.OWNER_FLAG,
                    }
                    cursor.execute(
                        "SELECT ID_PRESENTATION, ID_APPROLE, DT_LAST_UPDATE "
                        "FROM M4RCH_TASK_PRESENTATION WHERE ID_BP = ?",
                        bp_id
                    )
                    presentations = []
                    for p_row in cursor.fetchall():
                        presentations.append({
                            "id_presentation": p_row.ID_PRESENTATION,
                            "id_approle": p_row.ID_APPROLE,
                            "dt_last_update": str(p_row.DT_LAST_UPDATE) if p_row.DT_LAST_UPDATE else None,
                        })
                    bp_def["presentations"] = presentations
                    result["business_process"]["definition"] = bp_def

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Obtiene el detalle completo de una opción de menú de PeopleNet."
    )
    parser.add_argument("id_menu", help="Identificador lógico del menú (ej: HRM_EMPLOYEES)")
    parser.add_argument(
        "--include-children",
        action="store_true",
        help="Incluir hijos directos en el árbol"
    )
    parser.add_argument(
        "--include-hits",
        action="store_true",
        help="Incluir detalle de contadores de uso por usuario"
    )
    parser.add_argument(
        "--include-bp",
        action="store_true",
        help="Incluir definición del BP vinculado y sus presentaciones"
    )
    args = parser.parse_args()

    result = get_menu(
        args.id_menu,
        include_children=args.include_children,
        include_hits=args.include_hits,
        include_bp=args.include_bp
    )
    print(json.dumps(result, indent=2, default=str))
