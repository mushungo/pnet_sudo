# tools/workflow/list_workflows.py
"""
Lista todas las definiciones de procesos de workflow (BPC) de PeopleNet.

Consulta la tabla M4RWF_BPC con subconsultas de conteo para estados,
transiciones e instancias del motor de workflow.

Uso:
    python -m tools.workflow.list_workflows
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_all_workflows():
    """Obtiene la lista de definiciones de workflow (BPC) con estadísticas.

    Consulta M4RWF_BPC y agrega conteos de estados (M4RWF_STATE),
    transiciones (M4RWF_TRANSITION) e instancias (M4RWF_BPO).

    Returns:
        dict con status y lista de workflows, o estado de error.
    """
    sql_query = """
    SELECT
        b.ID_BPC,
        b.NAME_ESP,
        b.NAME_ENG,
        b.ID_TYPE,
        b.CLASSIFICATION,
        b.ID_PUB_STATUS,
        b.HAVE_SECURITY,
        b.DT_CREATION,
        b.ID_CREATOR,
        (SELECT COUNT(*) FROM M4RWF_STATE s WHERE s.ID_BPC = b.ID_BPC) AS NUM_STATES,
        (SELECT COUNT(*) FROM M4RWF_TRANSITION t WHERE t.ID_BPC = b.ID_BPC) AS NUM_TRANSITIONS,
        (SELECT COUNT(*) FROM M4RWF_TASK tk WHERE tk.ID_BPC = b.ID_BPC) AS NUM_TASKS,
        (SELECT COUNT(*) FROM M4RWF_BPO o WHERE o.ID_BPC = b.ID_BPC) AS NUM_INSTANCES
    FROM M4RWF_BPC b
    ORDER BY b.ID_BPC;
    """

    # Mapeo de estados de publicación
    pub_status_map = {
        0: "Draft",
        1: "Published",
        2: "Deprecated",
    }

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            workflows = []
            for row in rows:
                workflows.append({
                    "id_bpc": row.ID_BPC,
                    "name": row.NAME_ESP or row.NAME_ENG,
                    "name_esp": row.NAME_ESP,
                    "name_eng": row.NAME_ENG,
                    "type": row.ID_TYPE,
                    "classification": row.CLASSIFICATION,
                    "pub_status": row.ID_PUB_STATUS,
                    "pub_status_name": pub_status_map.get(row.ID_PUB_STATUS, f"Unknown({row.ID_PUB_STATUS})"),
                    "have_security": bool(row.HAVE_SECURITY) if row.HAVE_SECURITY is not None else None,
                    "created": str(row.DT_CREATION) if row.DT_CREATION else None,
                    "creator": row.ID_CREATOR,
                    "num_states": row.NUM_STATES,
                    "num_transitions": row.NUM_TRANSITIONS,
                    "num_tasks": row.NUM_TASKS,
                    "num_instances": row.NUM_INSTANCES,
                })

            return {"status": "success", "count": len(workflows), "workflows": workflows}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = get_all_workflows()
    print(json.dumps(result, indent=2, default=str))
