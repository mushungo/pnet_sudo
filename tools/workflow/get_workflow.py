# tools/workflow/get_workflow.py
"""
Obtiene los detalles completos de un proceso de workflow (BPC) de PeopleNet.

Incluye: definición del BPC, estados, transiciones, tareas, definiciones
de datos, delegaciones, y estadísticas de instancias y work items.

Uso:
    python -m tools.workflow.get_workflow <ID_BPC>
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_workflow_details(id_bpc):
    """Obtiene la definición completa de un workflow (BPC).

    Consulta: M4RWF_BPC, M4RWF_STATE, M4RWF_TRANSITION, M4RWF_TASK,
    M4RWF_DATADEF, M4RWF_DELEGATION, M4RWF_BPO, M4RWF_WORKITEM.

    Args:
        id_bpc: Identificador numérico del BPC.

    Returns:
        dict con la definición completa o estado de error.
    """
    try:
        id_bpc = int(id_bpc)
    except (ValueError, TypeError):
        return {"status": "error", "message": f"ID_BPC debe ser un entero, se recibió: '{id_bpc}'."}

    # Mapeo de estados de publicación
    pub_status_map = {0: "Draft", 1: "Published", 2: "Deprecated"}

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Definición principal del BPC
            cursor.execute(
                "SELECT ID_BPC, NAME_ESP, NAME_ENG, ID_TYPE, CLASSIFICATION, "
                "ID_PUB_STATUS, HAVE_SECURITY, DT_CREATION, ID_CREATOR, "
                "DEADLINE_YEARS, DEADLINE_MONTHS, DEADLINE_DAYS, "
                "DEADLINE_HOURS, DEADLINE_MINS "
                "FROM M4RWF_BPC WHERE ID_BPC = ?",
                id_bpc
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {"status": "not_found", "message": f"No se encontró el workflow BPC con ID {id_bpc}."}

            result = {
                "id_bpc": main_row.ID_BPC,
                "name_esp": main_row.NAME_ESP,
                "name_eng": main_row.NAME_ENG,
                "type": main_row.ID_TYPE,
                "classification": main_row.CLASSIFICATION,
                "pub_status": main_row.ID_PUB_STATUS,
                "pub_status_name": pub_status_map.get(main_row.ID_PUB_STATUS, f"Unknown({main_row.ID_PUB_STATUS})"),
                "have_security": bool(main_row.HAVE_SECURITY) if main_row.HAVE_SECURITY is not None else None,
                "created": str(main_row.DT_CREATION) if main_row.DT_CREATION else None,
                "creator": main_row.ID_CREATOR,
                "deadline": {
                    "years": main_row.DEADLINE_YEARS,
                    "months": main_row.DEADLINE_MONTHS,
                    "days": main_row.DEADLINE_DAYS,
                    "hours": main_row.DEADLINE_HOURS,
                    "mins": main_row.DEADLINE_MINS,
                },
            }

            # 2. Estados del workflow
            cursor.execute(
                "SELECT ID_STATE, NAME_ESP, NAME_ENG, ID_TYPE, "
                "X_POS, Y_POS, WIDTH, HEIGHT, "
                "ASSIGN_TYPE, CANCEL_TYPE, NO_DELEGABLE, "
                "DEADLINE_YEARS, DEADLINE_MONTHS, DEADLINE_DAYS, "
                "DEADLINE_HOURS, DEADLINE_MINS "
                "FROM M4RWF_STATE WHERE ID_BPC = ? ORDER BY ID_STATE",
                id_bpc
            )
            result["states"] = []
            for row in cursor.fetchall():
                result["states"].append({
                    "id_state": row.ID_STATE,
                    "name": row.NAME_ESP or row.NAME_ENG,
                    "name_esp": row.NAME_ESP,
                    "name_eng": row.NAME_ENG,
                    "type": row.ID_TYPE,
                    "position": {"x": row.X_POS, "y": row.Y_POS},
                    "size": {"width": row.WIDTH, "height": row.HEIGHT},
                    "assign_type": row.ASSIGN_TYPE,
                    "cancel_type": row.CANCEL_TYPE,
                    "no_delegable": bool(row.NO_DELEGABLE) if row.NO_DELEGABLE is not None else None,
                    "deadline": {
                        "years": row.DEADLINE_YEARS,
                        "months": row.DEADLINE_MONTHS,
                        "days": row.DEADLINE_DAYS,
                        "hours": row.DEADLINE_HOURS,
                        "mins": row.DEADLINE_MINS,
                    },
                })

            # 3. Transiciones entre estados
            cursor.execute(
                "SELECT ID_TRANSITION, ID_FROM, ID_TO, "
                "IS_CONDITION, VALUE_COND, IS_HIDE, EXEC_ADM "
                "FROM M4RWF_TRANSITION WHERE ID_BPC = ? ORDER BY ID_TRANSITION",
                id_bpc
            )
            result["transitions"] = []
            for row in cursor.fetchall():
                result["transitions"].append({
                    "id_transition": row.ID_TRANSITION,
                    "from_state": row.ID_FROM,
                    "to_state": row.ID_TO,
                    "is_condition": bool(row.IS_CONDITION) if row.IS_CONDITION is not None else None,
                    "value_cond": row.VALUE_COND,
                    "is_hide": bool(row.IS_HIDE) if row.IS_HIDE is not None else None,
                    "exec_adm": bool(row.EXEC_ADM) if row.EXEC_ADM is not None else None,
                })

            # 4. Tareas asociadas
            cursor.execute(
                "SELECT ID_TASK, ID_STATE, NAME_ESP, NAME_ENG "
                "FROM M4RWF_TASK WHERE ID_BPC = ? ORDER BY ID_STATE, ID_TASK",
                id_bpc
            )
            result["tasks"] = []
            for row in cursor.fetchall():
                result["tasks"].append({
                    "id_task": row.ID_TASK,
                    "id_state": row.ID_STATE,
                    "name": row.NAME_ESP or row.NAME_ENG,
                    "name_esp": row.NAME_ESP,
                    "name_eng": row.NAME_ENG,
                })

            # 5. Definiciones de datos del workflow
            cursor.execute(
                "SELECT ID_DATA, NAME_ESP, NAME_ENG, ID_TYPE "
                "FROM M4RWF_DATADEF WHERE ID_BPC = ? ORDER BY ID_DATA",
                id_bpc
            )
            result["data_definitions"] = []
            for row in cursor.fetchall():
                result["data_definitions"].append({
                    "id_data": row.ID_DATA,
                    "name": row.NAME_ESP or row.NAME_ENG,
                    "name_esp": row.NAME_ESP,
                    "name_eng": row.NAME_ENG,
                    "type": row.ID_TYPE,
                })

            # 6. Delegaciones configuradas
            cursor.execute(
                "SELECT ID_ORGANIZATION, ID_RESPONSIBLE, "
                "DT_START, DT_END, ID_DELEGATE, "
                "DELEGATE_TASK_PENDING, ID_APPROLE "
                "FROM M4RWF_DELEGATION WHERE ID_BPC = ? "
                "ORDER BY ID_ORGANIZATION, ID_RESPONSIBLE",
                id_bpc
            )
            result["delegations"] = []
            for row in cursor.fetchall():
                result["delegations"].append({
                    "organization": row.ID_ORGANIZATION,
                    "responsible": row.ID_RESPONSIBLE,
                    "delegate": row.ID_DELEGATE,
                    "start": str(row.DT_START) if row.DT_START else None,
                    "end": str(row.DT_END) if row.DT_END else None,
                    "delegate_task_pending": bool(row.DELEGATE_TASK_PENDING) if row.DELEGATE_TASK_PENDING is not None else None,
                    "approle": row.ID_APPROLE,
                })

            # 7. Conteo de instancias (BPO)
            cursor.execute(
                "SELECT COUNT(*) AS total FROM M4RWF_BPO WHERE ID_BPC = ?",
                id_bpc
            )
            count_row = cursor.fetchone()
            result["instance_count"] = count_row.total if count_row else 0

            # 8. Conteo de work items
            cursor.execute(
                "SELECT COUNT(*) AS total FROM M4RWF_WORKITEM WHERE ID_BPC = ?",
                id_bpc
            )
            count_row = cursor.fetchone()
            result["workitem_count"] = count_row.total if count_row else 0

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.workflow.get_workflow <ID_BPC>"
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_workflow_details(sys.argv[1]), indent=2, default=str))
