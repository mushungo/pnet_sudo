# tools/presentations/get_presentation.py
"""
Obtiene el detalle completo de una presentación de PeopleNet.

Incluye: definición principal, canales (T3) que la utilizan,
herencia de presentación base, y Business Processes vinculados.

Uso:
    python -m tools.presentations.get_presentation <ID_PRESENTATION>
    python -m tools.presentations.get_presentation <ID_PRESENTATION> --include-channels
    python -m tools.presentations.get_presentation <ID_PRESENTATION> --include-bps
    python -m tools.presentations.get_presentation <ID_PRESENTATION> --include-channels --include-bps
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

# PRESENTATION_STYLE en M4RPT_PRES_STYLE
PRESENTATION_STYLE_MAP = {
    10: "Normal",
    11: "Light",
    12: "Responsive",
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


def get_presentation(id_presentation, include_channels=False, include_bps=False):
    """Obtiene el detalle completo de una presentación.

    Consulta: M4RPT_PRESENTATION, M4RPT_PRES_INHERIT (herencia),
    M4RPT_PRES_STYLE (canales/T3), M4RCH_TASK_PRESENTATION (BPs vinculados).

    Args:
        id_presentation: Identificador de la presentación (ej: SCO_EMPLOYEE).
        include_channels: Si True, lista los canales (T3) que usan esta presentación.
        include_bps: Si True, lista los Business Processes vinculados.

    Returns:
        dict con la definición completa o estado de error.
    """
    if not id_presentation:
        return {"status": "error", "message": "id_presentation es requerido."}

    id_presentation = id_presentation.strip()

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Definición principal
            cursor.execute(
                "SELECT ID_PRESENTATION, DESCRIPTIONESP, DESCRIPTIONENG, "
                "DESCRIPTIONFRA, DESCRIPTIONGER, DESCRIPTIONBRA, DESCRIPTIONITA, DESCRIPTIONGEN, "
                "PRESENTATION_TYPE, OWNER_FLAG, READ_ONLY, IS_MODIFIED, BLOCKROBOT, "
                "ID_ORG_TYPE, ID_APPROLE, ID_SECUSER, DT_CREATE, DT_LAST_UPDATE, "
                "OWNERSHIP, USABILITY "
                "FROM M4RPT_PRESENTATION "
                "WHERE ID_PRESENTATION = ?",
                id_presentation
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {"status": "not_found", "message": f"No se encontró la presentación '{id_presentation}'."}

            ptype_val = main_row.PRESENTATION_TYPE
            result = {
                "id_presentation": main_row.ID_PRESENTATION,
                "descriptions": {
                    "esp": main_row.DESCRIPTIONESP,
                    "eng": main_row.DESCRIPTIONENG,
                    "fra": main_row.DESCRIPTIONFRA,
                    "ger": main_row.DESCRIPTIONGER,
                    "bra": main_row.DESCRIPTIONBRA,
                    "ita": main_row.DESCRIPTIONITA,
                    "gen": main_row.DESCRIPTIONGEN,
                },
                "presentation_type": ptype_val,
                "presentation_type_name": PRESENTATION_TYPE_MAP.get(ptype_val, f"Unknown({ptype_val})") if ptype_val is not None else None,
                "owner_flag": main_row.OWNER_FLAG,
                "owner_flag_name": decode_owner_flag(main_row.OWNER_FLAG),
                "read_only": bool(main_row.READ_ONLY) if main_row.READ_ONLY is not None else None,
                "is_modified": bool(main_row.IS_MODIFIED) if main_row.IS_MODIFIED is not None else None,
                "blockrobot": bool(main_row.BLOCKROBOT) if main_row.BLOCKROBOT is not None else None,
                "id_org_type": main_row.ID_ORG_TYPE,
                "id_approle": main_row.ID_APPROLE,
                "audit": {
                    "id_user": main_row.ID_SECUSER,
                    "dt_create": str(main_row.DT_CREATE) if main_row.DT_CREATE else None,
                    "dt_last_update": str(main_row.DT_LAST_UPDATE) if main_row.DT_LAST_UPDATE else None,
                },
                "ownership": main_row.OWNERSHIP,
                "usability": main_row.USABILITY,
            }

            # 2. Herencia: presentación base
            cursor.execute(
                "SELECT ID_PRES_BASE, ID_LEVEL "
                "FROM M4RPT_PRES_INHERIT "
                "WHERE ID_PRES = ? AND ID_LEVEL = 1",
                id_presentation
            )
            inherit_row = cursor.fetchone()
            result["base_presentation"] = inherit_row.ID_PRES_BASE if inherit_row else None

            # 3. Presentaciones que heredan de esta (hijos directos)
            cursor.execute(
                "SELECT COUNT(*) AS cnt "
                "FROM M4RPT_PRES_INHERIT "
                "WHERE ID_PRES_BASE = ? AND ID_LEVEL = 1",
                id_presentation
            )
            inh_row = cursor.fetchone()
            result["inherited_by_count"] = inh_row.cnt if inh_row else 0

            # 4. Canales (T3) que usan esta presentación con su estilo (opcional)
            if include_channels:
                cursor.execute(
                    "SELECT ps.ID_T3, ps.PRESENTATION_STYLE, "
                    "t.N_T3ESP "
                    "FROM M4RPT_PRES_STYLE ps "
                    "LEFT JOIN M4RCH_T3S t ON t.ID_T3 = ps.ID_T3 "
                    "WHERE ps.ID_PRESENTATION = ? "
                    "ORDER BY ps.ID_T3",
                    id_presentation
                )
                result["channels"] = []
                for row in cursor.fetchall():
                    style_val = row.PRESENTATION_STYLE
                    result["channels"].append({
                        "id_t3": row.ID_T3,
                        "name_esp": row.N_T3ESP,
                        "presentation_style": style_val,
                        "presentation_style_name": PRESENTATION_STYLE_MAP.get(style_val, f"Unknown({style_val})") if style_val is not None else None,
                    })
                result["channels_count"] = len(result["channels"])

            # 5. Business Processes vinculados (opcional)
            if include_bps:
                cursor.execute(
                    "SELECT tp.ID_BP, tp.ID_APPROLE, tp.DT_LAST_UPDATE, "
                    "b.N_BPESP, b.N_BPENG, b.ID_T3 "
                    "FROM M4RCH_TASK_PRESENTATION tp "
                    "LEFT JOIN M4RBP_DEF b ON b.ID_BP = tp.ID_BP "
                    "WHERE tp.ID_PRESENTATION = ? "
                    "ORDER BY tp.ID_BP",
                    id_presentation
                )
                result["business_processes"] = []
                for row in cursor.fetchall():
                    result["business_processes"].append({
                        "id_bp": row.ID_BP,
                        "name_esp": row.N_BPESP,
                        "name_eng": row.N_BPENG,
                        "id_t3": row.ID_T3,
                        "id_approle": row.ID_APPROLE,
                        "dt_last_update": str(row.DT_LAST_UPDATE) if row.DT_LAST_UPDATE else None,
                    })
                result["business_processes_count"] = len(result["business_processes"])

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Obtiene el detalle completo de una presentación de PeopleNet."
    )
    parser.add_argument("id_presentation", help="Identificador de la presentación (ej: SCO_EMPLOYEE)")
    parser.add_argument(
        "--include-channels",
        action="store_true",
        help="Incluir canales (T3) que usan esta presentación"
    )
    parser.add_argument(
        "--include-bps",
        action="store_true",
        help="Incluir Business Processes vinculados"
    )
    args = parser.parse_args()

    result = get_presentation(
        args.id_presentation,
        include_channels=args.include_channels,
        include_bps=args.include_bps
    )
    print(json.dumps(result, indent=2, default=str))
