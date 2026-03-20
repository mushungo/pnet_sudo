# tools/job_scheduler/get_job_scheduler_task.py
"""
Obtiene los detalles completos de una tarea programada del Job Scheduler de PeopleNet.

Incluye: definición de la tarea, parámetros, ejecuciones recientes,
subtareas, notificaciones y código asociado.

Uso:
    python -m tools.job_scheduler.get_job_scheduler_task <ID_SCHED_TASK>
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_job_details(id_sched_task):
    """Obtiene los detalles completos de una tarea programada.

    Consulta: M4RJS_SCHED_TASKS, M4RJS_DEF_PARAMS, M4RJS_TASK_EXE,
    M4RJS_SUBTASK_EXE, M4RJS_NOTIFICATIONS, M4RBP_DEF.

    Args:
        id_sched_task: Identificador de la tarea programada.

    Returns:
        dict con la definición completa o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # Mapeo de estados
            status_map = {
                0: "Executed", 1: "Waiting", 2: "Executing",
                3: "Cancelling", 4: "Expired", 5: "Cancelled",
                6: "Interrupted", 10: "Aborting", 11: "Aborted"
            }

            # 1. Tarea principal
            cursor.execute(
                "SELECT ID_SCHED_TASK, ID_ORGANIZATION, ID_BP, IS_ADMINISTRATIVE, "
                "PRIORITY, DT_CREATION, ID_STATUS, ID_SERVER, ID_SERVICE, "
                "ID_USER, ID_APPROLE "
                "FROM M4RJS_SCHED_TASKS WHERE ID_SCHED_TASK = ?",
                id_sched_task
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {"status": "not_found", "message": f"No se encontró la tarea '{id_sched_task}'."}

            result = {
                "id_sched_task": main_row.ID_SCHED_TASK,
                "organization": main_row.ID_ORGANIZATION,
                "id_bp": main_row.ID_BP,
                "is_administrative": bool(main_row.IS_ADMINISTRATIVE) if main_row.IS_ADMINISTRATIVE is not None else None,
                "priority": main_row.PRIORITY,
                "created": str(main_row.DT_CREATION) if main_row.DT_CREATION else None,
                "status": main_row.ID_STATUS,
                "status_name": status_map.get(main_row.ID_STATUS, f"Unknown({main_row.ID_STATUS})"),
                "server": main_row.ID_SERVER,
                "service": main_row.ID_SERVICE,
                "user": main_row.ID_USER,
                "approle": main_row.ID_APPROLE,
            }

            # 2. Definición de la tarea en M4RBP_DEF (si existe)
            if main_row.ID_BP:
                cursor.execute(
                    "SELECT ID_BP, NAME_ESP, NAME_ENG, CODE_TYPE, CATEGORY "
                    "FROM M4RBP_DEF WHERE ID_BP = ?",
                    main_row.ID_BP
                )
                bp_row = cursor.fetchone()
                if bp_row:
                    code_type_map = {1: "Windows Client", 2: "LN4", 3: "Java Client", 4: "Thin Client"}
                    result["task_definition"] = {
                        "id_bp": bp_row.ID_BP,
                        "name": bp_row.NAME_ESP or bp_row.NAME_ENG,
                        "code_type": bp_row.CODE_TYPE,
                        "code_type_name": code_type_map.get(bp_row.CODE_TYPE, f"Unknown({bp_row.CODE_TYPE})"),
                        "category": bp_row.CATEGORY,
                    }

            # 3. Parámetros de definición
            cursor.execute(
                "SELECT ID_PARAM, PARAM_NAME "
                "FROM M4RJS_DEF_PARAMS WHERE ID_SCHED_TASK = ? ORDER BY ID_PARAM",
                id_sched_task
            )
            result["parameters"] = []
            for row in cursor.fetchall():
                result["parameters"].append({
                    "id_param": row.ID_PARAM,
                    "param_name": row.PARAM_NAME,
                })

            # 4. Ejecuciones recientes (últimas 20)
            cursor.execute(
                "SELECT TOP 20 ID_TASK_EXE, ID_STATUS, DT_START, DT_END, ID_SERVER "
                "FROM M4RJS_TASK_EXE WHERE ID_SCHED_TASK = ? ORDER BY DT_START DESC",
                id_sched_task
            )
            result["recent_executions"] = []
            for row in cursor.fetchall():
                result["recent_executions"].append({
                    "id_task_exe": row.ID_TASK_EXE,
                    "status": row.ID_STATUS,
                    "status_name": status_map.get(row.ID_STATUS, f"Unknown({row.ID_STATUS})"),
                    "start": str(row.DT_START) if row.DT_START else None,
                    "end": str(row.DT_END) if row.DT_END else None,
                    "server": row.ID_SERVER,
                })

            # 5. Conteo de subtareas
            cursor.execute(
                "SELECT COUNT(*) AS total FROM M4RJS_SUBTASK_EXE se "
                "INNER JOIN M4RJS_TASK_EXE te ON se.ID_TASK_EXE = te.ID_TASK_EXE "
                "WHERE te.ID_SCHED_TASK = ?",
                id_sched_task
            )
            stats_row = cursor.fetchone()
            result["subtask_count"] = stats_row.total if stats_row else 0

            # 6. Notificaciones configuradas
            cursor.execute(
                "SELECT ID_NOTIFICATION, ID_USER, ID_EVENT_TYPE "
                "FROM M4RJS_NOTIFICATIONS WHERE ID_SCHED_TASK = ? ORDER BY ID_NOTIFICATION",
                id_sched_task
            )
            result["notifications"] = []
            for row in cursor.fetchall():
                result["notifications"].append({
                    "id_notification": row.ID_NOTIFICATION,
                    "user": row.ID_USER,
                    "event_type": row.ID_EVENT_TYPE,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.job_scheduler.get_job_scheduler_task <ID_SCHED_TASK>"
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_job_details(sys.argv[1]), indent=2, default=str))
