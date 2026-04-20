# tools/business_process/list_bp.py
"""
Lista los Business Processes (tareas) registrados en PeopleNet.

Uso:
    python -m tools.business_process.list_bp
    python -m tools.business_process.list_bp --search "empleado"
    python -m tools.business_process.list_bp --t3 CRVE_PA_TR_PERSON
    python -m tools.business_process.list_bp --with-presentation
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_bp(search=None, t3=None, with_presentation=False, limit=200):
    """Lista Business Processes con filtros opcionales.

    Consulta M4RBP_DEF (catálogo) con JOIN opcional a M4RBP_DEF1 (descripciones)
    y M4RCH_TASK_PRESENTATION (presentaciones asociadas).

    Args:
        search: Buscar en ID_BP o nombres ESP/ENG del BP.
        t3: Filtrar por ID_T3 (canal al que pertenece el BP).
        with_presentation: Solo BPs que tienen una presentación asociada.
        limit: Máximo de resultados (default 200).

    Returns:
        dict con status, total y lista de Business Processes.
    """
    conditions = []
    params = []

    base_sql = """
    SELECT DISTINCT
        b.ID_BP,
        b.N_BPESP,
        b.N_BPENG,
        b.SECURITY_TYPE,
        b.ID_T3,
        b.STATE,
        b.OWNER_FLAG,
        b.ID_APPROLE,
        b.DT_LAST_UPDATE,
        tp.ID_PRESENTATION
    FROM M4RBP_DEF b
    LEFT JOIN M4RBP_DEF1 b1 ON b1.ID_BP = b.ID_BP
    LEFT JOIN M4RCH_TASK_PRESENTATION tp ON tp.ID_BP = b.ID_BP
    """

    if t3:
        conditions.append("b.ID_T3 = ?")
        params.append(t3)

    if search:
        pattern = f"%{search}%"
        conditions.append(
            "(b.ID_BP LIKE ? OR b.N_BPESP LIKE ? OR b.N_BPENG LIKE ? "
            "OR b1.DESC_BPESP LIKE ? OR b1.DESC_BPENG LIKE ?)"
        )
        params.extend([pattern, pattern, pattern, pattern, pattern])

    if with_presentation:
        conditions.append("tp.ID_PRESENTATION IS NOT NULL")

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += f" ORDER BY b.ID_BP OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()

            bp_list = []
            for row in rows:
                bp_list.append({
                    "id_bp": row.ID_BP,
                    "name_esp": row.N_BPESP,
                    "name_eng": row.N_BPENG,
                    "security_type": int(row.SECURITY_TYPE) if row.SECURITY_TYPE is not None else None,
                    "id_t3": row.ID_T3,
                    "state": int(row.STATE) if row.STATE is not None else None,
                    "owner_flag": int(row.OWNER_FLAG) if row.OWNER_FLAG is not None else None,
                    "id_approle": row.ID_APPROLE,
                    "id_presentation": row.ID_PRESENTATION if row.ID_PRESENTATION else None,
                    "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                })

            return {
                "status": "success",
                "total": len(bp_list),
                "filters": {
                    "search": search,
                    "t3": t3,
                    "with_presentation": with_presentation,
                    "limit": limit,
                },
                "business_processes": bp_list,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista Business Processes de PeopleNet.")
    parser.add_argument("--search", help="Buscar en ID o nombre ESP/ENG")
    parser.add_argument("--t3", help="Filtrar por ID_T3 (canal)")
    parser.add_argument("--with-presentation", action="store_true", help="Solo BPs con presentación asociada")
    parser.add_argument("--limit", type=int, default=200, help="Máximo de resultados (default: 200)")
    args = parser.parse_args()

    result = list_bp(search=args.search, t3=args.t3, with_presentation=args.with_presentation, limit=args.limit)
    print(json.dumps(result, indent=2, default=str))
