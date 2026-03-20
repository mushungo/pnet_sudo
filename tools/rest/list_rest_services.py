# tools/rest/list_rest_services.py
"""
Lista los TIs de tipo REST/WebService/Integración disponibles en PeopleNet.

Busca en M4RCH_TIS los TIs relacionados con REST, WebService, SOAP, HTTP,
SAP e interfaces de integración.

Uso:
    python -m tools.rest.list_rest_services
    python -m tools.rest.list_rest_services --filter REST
    python -m tools.rest.list_rest_services --filter SAP
    python -m tools.rest.list_rest_services --filter WS
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_rest_services(filter_pattern=None):
    """Obtiene la lista de TIs de integración REST/WS.

    Busca TIs cuyo ID_TI contenga alguno de los patrones de integración
    conocidos: REST, API_WS, WEBSERVICE, SOAP, HTTP, SAP, INTERFACE, CONNECTOR.

    Args:
        filter_pattern: Patrón opcional para filtrar (ej: 'REST', 'SAP', 'WS').
            Si no se proporciona, lista todas las categorías.

    Returns:
        dict con status y lista de TIs de integración, o estado de error.
    """
    # Categorías de integración con sus patrones SQL
    categories = {
        "REST": "ID_TI LIKE '%REST%'",
        "API_WS": "ID_TI LIKE '%API_WS%'",
        "WEBSERVICE": "ID_TI LIKE '%WEBSERVICE%' OR ID_TI LIKE '%WEB_SERV%'",
        "SOAP": "ID_TI LIKE '%SOAP%'",
        "HTTP": "ID_TI LIKE '%HTTP%'",
        "SAP": "ID_TI LIKE '%SAP%'",
        "INTERFACE": "ID_TI LIKE '%INTERFACE%'",
        "CONNECTOR": "ID_TI LIKE '%CONNECTOR%'",
        "WS_": "ID_TI LIKE 'WS[_]%' OR ID_TI LIKE 'CCO[_]WS[_]%'",
    }

    if filter_pattern:
        filter_upper = filter_pattern.upper()
        if filter_upper in categories:
            where_clause = categories[filter_upper]
        else:
            where_clause = f"ID_TI LIKE '%{filter_upper}%'"
    else:
        where_clause = " OR ".join(f"({cond})" for cond in categories.values())

    sql_query = f"""
    SELECT
        ID_TI, ID_T3, ID_NODE, CSTYPE,
        READ_OBJECT, WRITE_OBJECT
    FROM M4RCH_TIS
    WHERE {where_clause}
    ORDER BY ID_TI;
    """

    # CSTYPE mapping
    cstype_map = {
        0: "Physical", 1: "Logical", 2: "Virtual",
        3: "Temporary", 7: "No-BDL"
    }

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            services = []
            for row in rows:
                services.append({
                    "id_ti": row.ID_TI,
                    "channel": row.ID_T3,
                    "node": row.ID_NODE,
                    "cstype": row.CSTYPE,
                    "cstype_name": cstype_map.get(row.CSTYPE, f"Unknown({row.CSTYPE})"),
                    "read_object": row.READ_OBJECT,
                    "write_object": row.WRITE_OBJECT,
                })

            return {"status": "success", "count": len(services), "services": services}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    filter_arg = None
    if "--filter" in sys.argv:
        idx = sys.argv.index("--filter")
        if idx + 1 < len(sys.argv):
            filter_arg = sys.argv[idx + 1]
    result = get_rest_services(filter_arg)
    print(json.dumps(result, indent=2, default=str))
