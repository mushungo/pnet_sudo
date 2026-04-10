# tools/sentences/find_ti_by_sentence.py
"""
Encuentra todos los TIs (Technical Instances) que usan una sentence dada.

Consulta M4RCH_TIS buscando en ID_READ_SENTENCE e ID_WRITE_SENTENCE
para trazar la relación inversa: sentence -> TIs que la consumen.

Uso:
    python -m tools.sentences.find_ti_by_sentence "SEN_EMPLOYEE"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def find_tis_by_sentence(id_sentence, detail=False):
    """Encuentra todos los TIs que referencian una sentence.

    Busca en M4RCH_TIS.ID_READ_SENTENCE y M4RCH_TIS.ID_WRITE_SENTENCE.

    Args:
        id_sentence: Identificador de la sentence a buscar.
        detail: Si True, incluye información adicional del canal (T3)
                y del nodo donde se monta cada TI.

    Returns:
        dict con status, conteo y lista de TIs que usan la sentence.
    """
    sql_base = """
        SELECT
            ti.ID_TI, ti.N_TIESP, ti.N_TIENG,
            ti.ID_READ_OBJECT, ti.ID_WRITE_OBJECT,
            ti.ID_READ_SENTENCE, ti.ID_WRITE_SENTENCE,
            ti.IS_SYSTEM_TI
        FROM M4RCH_TIS ti
        WHERE ti.ID_READ_SENTENCE = ?
           OR ti.ID_WRITE_SENTENCE = ?
        ORDER BY ti.ID_TI
    """

    sql_with_node = """
        SELECT
            ti.ID_TI, ti.N_TIESP, ti.N_TIENG,
            ti.ID_READ_OBJECT, ti.ID_WRITE_OBJECT,
            ti.ID_READ_SENTENCE, ti.ID_WRITE_SENTENCE,
            ti.IS_SYSTEM_TI,
            n.ID_T3, n.ID_NODE, n.N_NODEESP,
            t3.N_T3ESP, t3.ID_CATEGORY
        FROM M4RCH_TIS ti
        LEFT JOIN M4RCH_NODES n ON ti.ID_TI = n.ID_TI
        LEFT JOIN M4RCH_T3S t3 ON n.ID_T3 = t3.ID_T3
        WHERE ti.ID_READ_SENTENCE = ?
           OR ti.ID_WRITE_SENTENCE = ?
        ORDER BY ti.ID_TI, n.ID_T3
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            sql = sql_with_node if detail else sql_base
            cursor.execute(sql, id_sentence, id_sentence)
            rows = cursor.fetchall()

            if not rows:
                return {
                    "status": "success",
                    "sentence_searched": id_sentence,
                    "count": 0,
                    "message": f"No se encontraron TIs que referencien la sentence '{id_sentence}'.",
                    "tis": [],
                }

            tis = []
            seen_tis = set()
            for r in rows:
                # Determinar tipo de uso
                usage = []
                if r.ID_READ_SENTENCE == id_sentence:
                    usage.append("READ")
                if r.ID_WRITE_SENTENCE == id_sentence:
                    usage.append("WRITE")

                entry = {
                    "id_ti": r.ID_TI,
                    "name_esp": r.N_TIESP,
                    "name_eng": r.N_TIENG,
                    "usage": usage,
                    "read_object": r.ID_READ_OBJECT,
                    "write_object": r.ID_WRITE_OBJECT,
                    "is_system": bool(r.IS_SYSTEM_TI) if r.IS_SYSTEM_TI is not None else None,
                }

                if detail:
                    entry["channel"] = r.ID_T3
                    entry["channel_name"] = r.N_T3ESP
                    entry["category"] = r.ID_CATEGORY
                    entry["node"] = r.ID_NODE
                    entry["node_name"] = r.N_NODEESP

                tis.append(entry)
                seen_tis.add(r.ID_TI)

            return {
                "status": "success",
                "sentence_searched": id_sentence,
                "count": len(seen_tis),
                "total_rows": len(tis),
                "tis": tis,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encuentra TIs que referencian una sentence."
    )
    parser.add_argument(
        "id_sentence",
        help="Identificador de la sentence a buscar"
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Incluir canal (T3) y nodo donde se monta cada TI"
    )
    args = parser.parse_args()

    result = find_tis_by_sentence(args.id_sentence, detail=args.detail)
    print(json.dumps(result, indent=2, default=str))
