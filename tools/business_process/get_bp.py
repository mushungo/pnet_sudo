# tools/business_process/get_bp.py
"""
Obtiene el detalle completo de un Business Process de PeopleNet.

Uso:
    python -m tools.business_process.get_bp HRM_EMPLOYEES_BP
    python -m tools.business_process.get_bp HRM_EMPLOYEES_BP --include-menus
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


SECURITY_TYPE_MAP = {
    0: "Sin seguridad",
    1: "Auditoría",
    2: "Seguridad completa",
}

CODE_TYPE_MAP = {
    1: "Cliente Windows",
    2: "LN4",
    3: "Cliente Java",
    4: "Cliente ligero",
}

STATE_MAP = {
    0: "Activo",
    1: "Inactivo",
    2: "Obsoleto",
}

OWNER_FLAG_MAP = {
    1: "Standard",
    2: "Standard extendido",
    10: "Corporate",
    20: "Corporate extendido",
}


def get_bp(id_bp, include_menus=False, include_roles=False, include_code=False, include_subtasks=False, include_params=False):
    """Obtiene el detalle completo de un Business Process.

    Consulta M4RBP_DEF (definición), M4RBP_DEF1 (descripciones),
    M4RCH_TASK_PRESENTATION (presentaciones), M4RBP_APPROLE (roles),
    M4RBP_EXE_CODE (tipos de cliente), M4RBP_STRUCT (subtareas),
    M4RBP_PARAM_DEF (parámetros), y opcionalmente M4RMN_OPTIONS (menús).

    Args:
        id_bp: Identificador del Business Process.
        include_menus: Incluir menús que usan este BP.
        include_roles: Incluir roles autorizados.
        include_code: Incluir tipos de cliente que ejecutan el BP.
        include_subtasks: Incluir subtareas del BP.
        include_params: Incluir parámetros del BP.

    Returns:
        dict con detalle del Business Process.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            bp_sql = """
            SELECT
                b.ID_BP,
                b.N_BPESP,
                b.N_BPENG,
                b.N_BPFRA,
                b.N_BPGER,
                b.N_BPBRA,
                b.N_BPITA,
                b.N_BPGEN,
                b.SECURITY_TYPE,
                b.ID_T3,
                b.SOC_DEPENDENT,
                b.STATE,
                b.OWNER_FLAG,
                b.ID_APPROLE,
                b.ADMINISTRATIVE,
                b.CONCURRENCY_LEVEL,
                b.SELF_RECOVER,
                b.DT_LAST_UPDATE
            FROM M4RBP_DEF b
            WHERE b.ID_BP = ?
            """
            cursor.execute(bp_sql, id_bp)
            row = cursor.fetchone()

            if not row:
                return {"status": "error", "message": f"Business Process '{id_bp}' no encontrado"}

            security_type = int(row.SECURITY_TYPE) if row.SECURITY_TYPE is not None else None
            state = int(row.STATE) if row.STATE is not None else None
            owner_flag = int(row.OWNER_FLAG) if row.OWNER_FLAG is not None else None

            result = {
                "status": "success",
                "id_bp": row.ID_BP,
                "names": {
                    "esp": row.N_BPESP,
                    "eng": row.N_BPENG,
                    "fra": row.N_BPFRA,
                    "ger": row.N_BPGER,
                    "bra": row.N_BPBRA,
                    "ita": row.N_BPITA,
                    "gen": row.N_BPGEN,
                },
                "security_type": security_type,
                "security_type_decoded": SECURITY_TYPE_MAP.get(security_type),
                "id_t3": row.ID_T3,
                "soc_dependent": bool(row.SOC_DEPENDENT),
                "state": state,
                "state_decoded": STATE_MAP.get(state),
                "owner_flag": owner_flag,
                "owner_flag_decoded": OWNER_FLAG_MAP.get(owner_flag, f"Custom ({owner_flag})"),
                "id_approle": row.ID_APPROLE,
                "administrative": int(row.ADMINISTRATIVE) if row.ADMINISTRATIVE is not None else None,
                "concurrency_level": int(row.CONCURRENCY_LEVEL) if row.CONCURRENCY_LEVEL is not None else None,
                "self_recover": bool(row.SELF_RECOVER),
                "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
            }

            bp1_sql = """
            SELECT
                DESC_BPESP,
                DESC_BPENG,
                DESC_BPFRA,
                DESC_BPGER,
                DESC_BPBRA,
                DESC_BPITA,
                DESC_BPGEN
            FROM M4RBP_DEF1
            WHERE ID_BP = ?
            """
            cursor.execute(bp1_sql, id_bp)
            row1 = cursor.fetchone()
            if row1:
                result["descriptions"] = {
                    "esp": row1.DESC_BPESP,
                    "eng": row1.DESC_BPENG,
                    "fra": row1.DESC_BPFRA,
                    "ger": row1.DESC_BPGER,
                    "bra": row1.DESC_BPBRA,
                    "ita": row1.DESC_BPITA,
                    "gen": row1.DESC_BPGEN,
                }

            pres_sql = """
            SELECT
                tp.ID_PRESENTATION,
                tp.ID_APPROLE,
                tp.DT_LAST_UPDATE
            FROM M4RCH_TASK_PRESENTATION tp
            WHERE tp.ID_BP = ?
            """
            cursor.execute(pres_sql, id_bp)
            presentations = []
            for row in cursor.fetchall():
                presentations.append({
                    "id_presentation": row.ID_PRESENTATION,
                    "id_approle": row.ID_APPROLE,
                    "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                })
            if presentations:
                result["presentations"] = presentations

            if include_roles:
                role_sql = """
                SELECT
                    r.ID_APPROLE_BP,
                    r.ID_APPROLE,
                    r.DT_LAST_UPDATE
                FROM M4RBP_APPROLE r
                WHERE r.ID_BP = ?
                """
                cursor.execute(role_sql, id_bp)
                roles = []
                for row in cursor.fetchall():
                    roles.append({
                        "id_approle_bp": row.ID_APPROLE_BP,
                        "id_approle": row.ID_APPROLE,
                        "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                    })
                if roles:
                    result["roles"] = roles

            if include_menus:
                menu_sql = """
                SELECT DISTINCT
                    o.ID_MENU,
                    o.TRANS_MENUESP,
                    o.TRANS_MENUENG,
                    o.ID_APPROLE,
                    o.POSITION_DEPENDING_MENU
                FROM M4RMN_OPTIONS o
                WHERE o.ID_BP = ? OR o.ID_BP_AUX_1 = ? OR o.ID_BP_AUX_2 = ?
                ORDER BY o.TRANS_MENUESP
                """
                cursor.execute(menu_sql, (id_bp, id_bp, id_bp))
                menus = []
                for row in cursor.fetchall():
                    menus.append({
                        "id_menu": row.ID_MENU,
                        "name_esp": row.TRANS_MENUESP,
                        "name_eng": row.TRANS_MENUENG,
                        "id_approle": row.ID_APPROLE,
                        "position": int(row.POSITION_DEPENDING_MENU) if row.POSITION_DEPENDING_MENU is not None else None,
                    })
                if menus:
                    result["menus"] = menus

            if include_code:
                code_sql = """
                SELECT
                    c.CODE_TYPE,
                    c.RECOVERABLE,
                    c.DT_LAST_UPDATE
                FROM M4RBP_EXE_CODE c
                WHERE c.ID_BP = ?
                """
                cursor.execute(code_sql, id_bp)
                code_list = []
                for row in cursor.fetchall():
                    code_list.append({
                        "code_type": CODE_TYPE_MAP.get(int(row.CODE_TYPE), str(row.CODE_TYPE)),
                        "code_type_raw": int(row.CODE_TYPE),
                        "recoverable": bool(row.RECOVERABLE),
                        "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                    })
                if code_list:
                    result["client_code"] = code_list

            if include_subtasks:
                struct_sql = """
                SELECT
                    s.LOCAL_ID,
                    s.ID_SUBTASK,
                    s.LOCAL_NAME,
                    s.LOCAL_DESC,
                    s.DT_LAST_UPDATE
                FROM M4RBP_STRUCT s
                WHERE s.ID_BP = ?
                ORDER BY s.LOCAL_ID
                """
                cursor.execute(struct_sql, id_bp)
                subtasks = []
                for row in cursor.fetchall():
                    subtasks.append({
                        "local_id": int(row.LOCAL_ID) if row.LOCAL_ID is not None else None,
                        "id_subtask": row.ID_SUBTASK,
                        "local_name": row.LOCAL_NAME,
                        "local_desc": row.LOCAL_DESC,
                        "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                    })
                if subtasks:
                    result["subtasks"] = subtasks

            if include_params:
                param_sql = """
                SELECT
                    p.ID_PARAM,
                    p.N_PARAMESP,
                    p.N_PARAMENG,
                    p.ID_TYPE,
                    p.SCOPE_TYPE,
                    p.PARAM_ORDINAL,
                    p.FLOW_TYPE,
                    p.TASK_SOURCE,
                    p.DT_LAST_UPDATE
                FROM M4RBP_PARAM_DEF p
                WHERE p.ID_BP = ?
                ORDER BY p.PARAM_ORDINAL
                """
                cursor.execute(param_sql, id_bp)
                params = []
                for row in cursor.fetchall():
                    params.append({
                        "id_param": row.ID_PARAM,
                        "name_esp": row.N_PARAMESP,
                        "name_eng": row.N_PARAMENG,
                        "id_type": int(row.ID_TYPE) if row.ID_TYPE is not None else None,
                        "scope_type": int(row.SCOPE_TYPE) if row.SCOPE_TYPE is not None else None,
                        "param_ordinal": int(row.PARAM_ORDINAL) if row.PARAM_ORDINAL is not None else None,
                        "flow_type": int(row.FLOW_TYPE) if row.FLOW_TYPE is not None else None,
                        "task_source": row.TASK_SOURCE,
                        "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                    })
                if params:
                    result["parameters"] = params

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obtiene detalle de un Business Process.")
    parser.add_argument("id_bp", help="Identificador del Business Process")
    parser.add_argument("--include-menus", action="store_true", help="Incluir menús que usan este BP")
    parser.add_argument("--include-roles", action="store_true", help="Incluir roles autorizados")
    parser.add_argument("--include-code", action="store_true", help="Incluir tipos de cliente que ejecutan el BP")
    parser.add_argument("--include-subtasks", action="store_true", help="Incluir subtareas del BP")
    parser.add_argument("--include-params", action="store_true", help="Incluir parámetros del BP")
    args = parser.parse_args()

    result = get_bp(
        args.id_bp,
        include_menus=args.include_menus,
        include_roles=args.include_roles,
        include_code=args.include_code,
        include_subtasks=args.include_subtasks,
        include_params=args.include_params,
    )
    print(json.dumps(result, indent=2, default=str))