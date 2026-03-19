# tools/bdl/get_rsm_role.py
"""Obtiene la definición completa de un Rol RSM (Role Security Model) de PeopleNet."""
import sys
import os
import json


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_rsm_role(id_rsm):
    """Obtiene los detalles completos de un rol RSM, incluyendo sus permisos sobre objetos.

    Consulta M4RSC_RSM, M4RSC_RSM1, M4RDC_SEC_LOBJ y M4RDC_SEC_FIELDS.
    """
    role_query = """
    SELECT
        r.ID_RSM,
        r.N_RSMESP,
        r.N_RSMENG,
        r.ID_PARENT_RSM,
        r.OWNERSHIP,
        r.USABILITY,
        CAST(r1.COMENT AS VARCHAR(MAX)) AS COMENT
    FROM M4RSC_RSM r
    LEFT JOIN M4RSC_RSM1 r1 ON r.ID_RSM = r1.ID_RSM
    WHERE r.ID_RSM = ?;
    """
    perms_query = """
    SELECT
        sl.ID_OBJECT,
        lo.ID_TRANS_OBJESP,
        lo.ID_TRANS_OBJENG,
        sl.MASK_SEL,
        sl.MASK_INS,
        sl.MASK_UPD,
        sl.MASK_DEL,
        sl.MASK_COR_INS,
        sl.MASK_COR_UPD,
        sl.MASK_COR_DEL,
        sl.HAVE_SECURITY_FLD,
        sl.CASCADE_OPER,
        sl.HIST_ADAPT,
        sl.ID_PARENT_RSM
    FROM M4RDC_SEC_LOBJ sl
    LEFT JOIN M4RDC_LOGIC_OBJECT lo ON sl.ID_OBJECT = lo.ID_OBJECT
    WHERE sl.ID_RSM = ?
    ORDER BY sl.ID_OBJECT;
    """
    fields_query = """
    SELECT
        sf.ID_OBJECT,
        sf.ID_FIELD,
        sf.IS_READ,
        sf.IS_WRITE,
        sf.ID_PARENT_RSM
    FROM M4RDC_SEC_FIELDS sf
    WHERE sf.ID_RSM = ?
    ORDER BY sf.ID_OBJECT, sf.ID_FIELD;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(role_query, id_rsm)
            row = cursor.fetchone()

            if not row:
                return {"status": "not_found", "message": f"No se encontró el rol RSM '{id_rsm}'."}

            cursor.execute(perms_query, id_rsm)
            perm_rows = cursor.fetchall()

            permissions = []
            for p in perm_rows:
                permissions.append({
                    "id_object": p.ID_OBJECT,
                    "description": p.ID_TRANS_OBJESP or p.ID_TRANS_OBJENG,
                    "select": bool(p.MASK_SEL) if p.MASK_SEL is not None else None,
                    "insert": bool(p.MASK_INS) if p.MASK_INS is not None else None,
                    "update": bool(p.MASK_UPD) if p.MASK_UPD is not None else None,
                    "delete": bool(p.MASK_DEL) if p.MASK_DEL is not None else None,
                    "corr_insert": bool(p.MASK_COR_INS) if p.MASK_COR_INS is not None else None,
                    "corr_update": bool(p.MASK_COR_UPD) if p.MASK_COR_UPD is not None else None,
                    "corr_delete": bool(p.MASK_COR_DEL) if p.MASK_COR_DEL is not None else None,
                    "has_field_security": bool(p.HAVE_SECURITY_FLD) if p.HAVE_SECURITY_FLD is not None else None,
                    "cascade_oper": bool(p.CASCADE_OPER) if p.CASCADE_OPER is not None else None,
                    "hist_adapt": bool(p.HIST_ADAPT) if p.HIST_ADAPT is not None else None,
                    "inherited_from": p.ID_PARENT_RSM
                })

            cursor.execute(fields_query, id_rsm)
            field_rows = cursor.fetchall()

            field_perms = []
            for fp in field_rows:
                field_perms.append({
                    "id_object": fp.ID_OBJECT,
                    "id_field": fp.ID_FIELD,
                    "is_read": bool(fp.IS_READ) if fp.IS_READ is not None else None,
                    "is_write": bool(fp.IS_WRITE) if fp.IS_WRITE is not None else None,
                    "inherited_from": fp.ID_PARENT_RSM
                })

            result = {
                "status": "success",
                "role": {
                    "id_rsm": row.ID_RSM,
                    "name": row.N_RSMESP or row.N_RSMENG,
                    "name_eng": row.N_RSMENG,
                    "parent_rsm": row.ID_PARENT_RSM,
                    "ownership": row.OWNERSHIP,
                    "usability": row.USABILITY,
                    "comment": row.COMENT,
                    "object_permissions_count": len(permissions),
                    "field_permissions_count": len(field_perms),
                    "object_permissions": permissions,
                    "field_permissions": field_perms
                }
            }
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_rsm_role \"ID_RSM\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_rsm_role(sys.argv[1]), indent=2, default=str))
