# tools/presentations/list_presentations.py
"""
Lista las presentaciones registradas en PeopleNet (M4RPT_PRESENTATION).

Uso:
    python -m tools.presentations.list_presentations
    python -m tools.presentations.list_presentations --search "empleado"
    python -m tools.presentations.list_presentations --t3 SCO_EMPLOYEE
    python -m tools.presentations.list_presentations --bp BP_EMPLOYEE_CARD
    python -m tools.presentations.list_presentations --type 0
    python -m tools.presentations.list_presentations --limit 100
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# PRESENTATION_TYPE: inferido de distribución de datos y nomenclatura
PRESENTATION_TYPE_MAP = {
    0: "OBL",        # Estándar (pantalla normal)
    1: "DP",         # Data Provider (nómina/payroll)
    2: "Template",   # Plantilla base
    3: "QBF",        # Query By Form (presentación de lista dinámica)
    4: "Include",    # Fragmento incluible en otras presentaciones
}


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


def list_presentations(search=None, t3=None, bp=None, ptype=None, limit=200):
    """Lista presentaciones con filtros opcionales.

    Consulta M4RPT_PRESENTATION con JOINs opcionales a M4RPT_PRES_STYLE (filtro por canal T3)
    y M4RCH_TASK_PRESENTATION (filtro por BP).

    Args:
        search: Buscar en ID_PRESENTATION o descripciones ESP/ENG.
        t3: Filtrar por canal (ID_T3) via M4RPT_PRES_STYLE.
        bp: Filtrar por Business Process via M4RCH_TASK_PRESENTATION.
        ptype: Filtrar por PRESENTATION_TYPE (0-4).
        limit: Máximo de resultados (default 200).

    Returns:
        dict con status, total y lista de presentaciones.
    """
    conditions = []
    params = []

    base_sql = """
    SELECT DISTINCT
        p.ID_PRESENTATION,
        p.DESCRIPTIONESP,
        p.DESCRIPTIONENG,
        p.PRESENTATION_TYPE,
        p.OWNER_FLAG,
        p.READ_ONLY,
        p.IS_MODIFIED,
        p.ID_APPROLE,
        p.DT_LAST_UPDATE
    FROM M4RPT_PRESENTATION p
    """

    if t3:
        base_sql += " INNER JOIN M4RPT_PRES_STYLE ps ON ps.ID_PRESENTATION = p.ID_PRESENTATION AND ps.ID_T3 = ?"
        params.append(t3)

    if bp:
        base_sql += " INNER JOIN M4RCH_TASK_PRESENTATION tp ON tp.ID_PRESENTATION = p.ID_PRESENTATION AND tp.ID_BP = ?"
        params.append(bp)

    if search:
        pattern = f"%{search}%"
        conditions.append(
            "(p.ID_PRESENTATION LIKE ? OR p.DESCRIPTIONESP LIKE ? OR p.DESCRIPTIONENG LIKE ?)"
        )
        params.extend([pattern, pattern, pattern])

    if ptype is not None:
        conditions.append("p.PRESENTATION_TYPE = ?")
        params.append(ptype)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += f" ORDER BY p.ID_PRESENTATION OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_sql, *params) if params else cursor.execute(base_sql)
            rows = cursor.fetchall()

            presentations = []
            for row in rows:
                ptype_val = row.PRESENTATION_TYPE
                presentations.append({
                    "id_presentation": row.ID_PRESENTATION,
                    "description_esp": row.DESCRIPTIONESP,
                    "description_eng": row.DESCRIPTIONENG,
                    "presentation_type": ptype_val,
                    "presentation_type_name": PRESENTATION_TYPE_MAP.get(ptype_val, f"Unknown({ptype_val})") if ptype_val is not None else None,
                    "owner_flag": row.OWNER_FLAG,
                    "owner_flag_name": decode_owner_flag(row.OWNER_FLAG),
                    "read_only": bool(row.READ_ONLY) if row.READ_ONLY is not None else None,
                    "is_modified": bool(row.IS_MODIFIED) if row.IS_MODIFIED is not None else None,
                    "id_approle": row.ID_APPROLE,
                    "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                })

            return {
                "status": "success",
                "total": len(presentations),
                "filters": {
                    "search": search,
                    "t3": t3,
                    "bp": bp,
                    "type": ptype,
                    "limit": limit,
                },
                "presentations": presentations,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista presentaciones de PeopleNet.")
    parser.add_argument("--search", help="Buscar en ID_PRESENTATION o descripciones")
    parser.add_argument("--t3", help="Filtrar por canal (ID_T3) via M4RPT_PRES_STYLE")
    parser.add_argument("--bp", help="Filtrar por Business Process via M4RCH_TASK_PRESENTATION")
    parser.add_argument("--type", type=int, dest="ptype", help="Filtrar por PRESENTATION_TYPE (0=OBL, 1=DP, 2=Template, 3=QBF, 4=Include)")
    parser.add_argument("--limit", type=int, default=200, help="Máximo de resultados (default: 200)")
    args = parser.parse_args()

    result = list_presentations(
        search=args.search,
        t3=args.t3,
        bp=args.bp,
        ptype=args.ptype,
        limit=args.limit
    )
    print(json.dumps(result, indent=2, default=str))
