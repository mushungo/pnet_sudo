# tools/job_scheduler/list_job_scheduler_tasks.py
"""
Lista todas las tareas programadas (scheduled tasks) del Job Scheduler de PeopleNet.

Consulta la tabla M4RJS_SCHED_TASKS para obtener las definiciones de tareas
del subsistema de planificación de trabajos.

Uso:
    python -m tools.job_scheduler.list_job_scheduler_tasks
    python -m tools.job_scheduler.list_job_scheduler_tasks --legacy    # Listar trabajos legacy (M4RJS_JOB_DEF)
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_all_scheduled_tasks():
    """Obtiene la lista de tareas del scheduler moderno (M4RJS_SCHED_TASKS).

    Returns:
        dict con status y lista de tareas, o estado de error.
    """
    sql_query = """
    SELECT TOP 500
        st.ID_SCHED_TASK,
        st.ID_ORGANIZATION,
        st.ID_BP,
        st.IS_ADMINISTRATIVE,
        st.PRIORITY,
        st.DT_CREATION,
        st.ID_STATUS,
        (SELECT COUNT(*) FROM M4RJS_TASK_EXE te WHERE te.ID_SCHED_TASK = st.ID_SCHED_TASK) AS NUM_EXECUTIONS
    FROM M4RJS_SCHED_TASKS st
    ORDER BY st.DT_CREATION DESC;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            # Mapeo de estados de ejecución
            status_map = {
                0: "Executed", 1: "Waiting", 2: "Executing",
                3: "Cancelling", 4: "Expired", 5: "Cancelled",
                6: "Interrupted", 10: "Aborting", 11: "Aborted"
            }

            tasks = []
            for row in rows:
                tasks.append({
                    "id_sched_task": row.ID_SCHED_TASK,
                    "organization": row.ID_ORGANIZATION,
                    "id_bp": row.ID_BP,
                    "is_administrative": bool(row.IS_ADMINISTRATIVE) if row.IS_ADMINISTRATIVE is not None else None,
                    "priority": row.PRIORITY,
                    "created": str(row.DT_CREATION) if row.DT_CREATION else None,
                    "status": row.ID_STATUS,
                    "status_name": status_map.get(row.ID_STATUS, f"Unknown({row.ID_STATUS})"),
                    "num_executions": row.NUM_EXECUTIONS,
                })

            return {"status": "success", "count": len(tasks), "tasks": tasks}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_all_legacy_jobs():
    """Obtiene la lista de trabajos legacy (M4RJS_JOB_DEF).

    Returns:
        dict con status y lista de trabajos legacy, o estado de error.
    """
    sql_query = """
    SELECT
        jd.ID_JOB,
        jd.ID_ORGANIZATION,
        jd.ID_JOB_TYPE,
        jd.DT_CREATION,
        (SELECT COUNT(*) FROM M4RJS_JOB_EXE je WHERE je.ID_JOB = jd.ID_JOB) AS NUM_EXECUTIONS
    FROM M4RJS_JOB_DEF jd
    ORDER BY jd.ID_JOB;
    """
    # Tipos de job legacy
    type_map = {0: "OLD_FORMAT", 1: "LN4", 2: "ADMIN"}

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            jobs = []
            for row in rows:
                jobs.append({
                    "id_job": row.ID_JOB,
                    "organization": row.ID_ORGANIZATION,
                    "job_type": row.ID_JOB_TYPE,
                    "job_type_name": type_map.get(row.ID_JOB_TYPE, f"Unknown({row.ID_JOB_TYPE})"),
                    "created": str(row.DT_CREATION) if row.DT_CREATION else None,
                    "num_executions": row.NUM_EXECUTIONS,
                })

            return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if "--legacy" in sys.argv:
        result = get_all_legacy_jobs()
    else:
        result = get_all_scheduled_tasks()
    print(json.dumps(result, indent=2, default=str))
