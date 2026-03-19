# tools/bdl/get_ramdl_object.py
"""Obtiene la definición completa de un Objeto RAMDL (transporte) del repositorio de PeopleNet."""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_ramdl_object(id_object):
    """Obtiene los detalles de un objeto RAMDL, incluyendo todas sus versiones y XML.

    Consulta M4RDC_RAMDL_OBJECTS y M4RDC_RAMDL_OBJEC1.
    """
    query = """
    SELECT
        ro.ID_OBJECT,
        ro.VER_LOWEST,
        ro.VER_HIGHEST,
        ro.N_OBJECTESP,
        ro.N_OBJECTENG,
        CAST(ro1.XML AS VARCHAR(MAX)) AS XML_CONTENT
    FROM M4RDC_RAMDL_OBJECTS ro
    LEFT JOIN M4RDC_RAMDL_OBJEC1 ro1
        ON ro.ID_OBJECT = ro1.ID_OBJECT AND ro.VER_LOWEST = ro1.VER_LOWEST
    WHERE ro.ID_OBJECT = ?
    ORDER BY ro.VER_LOWEST;
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, id_object)
            rows = cursor.fetchall()

            if not rows:
                return {"status": "not_found", "message": f"No se encontró el objeto RAMDL '{id_object}'."}

            versions = []
            for row in rows:
                versions.append({
                    "ver_lowest": row.VER_LOWEST,
                    "ver_highest": row.VER_HIGHEST,
                    "name": row.N_OBJECTESP or row.N_OBJECTENG,
                    "name_eng": row.N_OBJECTENG,
                    "has_xml": bool(row.XML_CONTENT),
                    "xml_length": len(row.XML_CONTENT) if row.XML_CONTENT else 0
                })

            result = {
                "status": "success",
                "ramdl_object": {
                    "id_object": id_object,
                    "name": rows[0].N_OBJECTESP or rows[0].N_OBJECTENG,
                    "version_count": len(versions),
                    "versions": versions
                }
            }
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.bdl.get_ramdl_object \"ID_OBJECT\""}, indent=2))
        sys.exit(1)
    print(json.dumps(get_ramdl_object(sys.argv[1]), indent=2, default=str))
