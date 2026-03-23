# tools/sentences/find_sentence_by_object.py
"""
Encuentra todas las sentences que referencian un Objeto Lógico (BDL) dado.

Busca en M4RCH_SENT_OBJECTS qué sentences incluyen el objeto en su cláusula FROM,
y opcionalmente enriquece con información de JOINs y filtros de cada sentence.

Uso:
    python -m tools.sentences.find_sentence_by_object "EMPLOYEE"
    python -m tools.sentences.find_sentence_by_object "EMPLOYEE" --detail
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def find_sentences_by_object(id_object, detail=False):
    """Encuentra todas las sentences que referencian un objeto BDL.

    Consulta M4RCH_SENT_OBJECTS para localizar el objeto en cláusulas FROM,
    y agrega conteos de objetos, JOINs y filtros por sentence.

    Args:
        id_object: Identificador del objeto BDL a buscar.
        detail: Si True, incluye la lista completa de objetos y JOINs
                de cada sentence encontrada.

    Returns:
        dict con status, conteo y lista de sentences que usan el objeto.
    """
    # Query base: sentences que referencian el objeto, con conteos
    sql_query = """
    SELECT
        so.ID_SENTENCE,
        so.ALIAS,
        so.IS_BASIS,
        s.ID_SENT_TYPE,
        s.IS_DISTINCT,
        obj_count.total_objects,
        join_count.total_joins,
        fld_count.total_filters
    FROM
        M4RCH_SENT_OBJECTS so
    INNER JOIN
        M4RCH_SENTENCES s ON so.ID_SENTENCE = s.ID_SENTENCE
    LEFT JOIN (
        SELECT ID_SENTENCE, COUNT(*) AS total_objects
        FROM M4RCH_SENT_OBJECTS
        GROUP BY ID_SENTENCE
    ) obj_count ON so.ID_SENTENCE = obj_count.ID_SENTENCE
    LEFT JOIN (
        SELECT ID_SENTENCE, COUNT(*) AS total_joins
        FROM M4RCH_SENT_OBJ_REL
        GROUP BY ID_SENTENCE
    ) join_count ON so.ID_SENTENCE = join_count.ID_SENTENCE
    LEFT JOIN (
        SELECT ID_SENTENCE, COUNT(*) AS total_filters
        FROM M4RCH_SENT_ADD_FLD
        GROUP BY ID_SENTENCE
    ) fld_count ON so.ID_SENTENCE = fld_count.ID_SENTENCE
    WHERE
        so.ID_OBJECT = ?
    ORDER BY
        so.ID_SENTENCE;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, id_object)
            rows = cursor.fetchall()

            if not rows:
                return {
                    "status": "success",
                    "bdl_object_searched": id_object,
                    "count": 0,
                    "message": f"No se encontraron sentences que referencien '{id_object}'.",
                    "sentences": []
                }

            sentences = []
            for row in rows:
                entry = {
                    "id_sentence": row.ID_SENTENCE,
                    "alias_in_sentence": row.ALIAS,
                    "is_basis": bool(row.IS_BASIS) if row.IS_BASIS is not None else None,
                    "sent_type": row.ID_SENT_TYPE,
                    "is_distinct": bool(row.IS_DISTINCT) if row.IS_DISTINCT is not None else None,
                    "total_objects": row.total_objects or 0,
                    "total_joins": row.total_joins or 0,
                    "total_filters": row.total_filters or 0,
                }
                sentences.append(entry)

            # Si se pide detalle, agregar objetos y joins de cada sentence
            if detail:
                for entry in sentences:
                    sid = entry["id_sentence"]

                    # Objetos de la sentence
                    cursor.execute(
                        "SELECT ID_OBJECT, ALIAS, IS_BASIS "
                        "FROM M4RCH_SENT_OBJECTS "
                        "WHERE ID_SENTENCE = ? ORDER BY IS_BASIS DESC, ALIAS",
                        sid
                    )
                    entry["objects"] = []
                    for obj_row in cursor.fetchall():
                        entry["objects"].append({
                            "id_object": obj_row.ID_OBJECT,
                            "alias": obj_row.ALIAS,
                            "is_basis": bool(obj_row.IS_BASIS) if obj_row.IS_BASIS is not None else None,
                        })

                    # JOINs de la sentence
                    cursor.execute(
                        "SELECT ALIAS_PARENT_OBJ, ALIAS_OBJ, ID_RELATION, ID_RELATION_TYPE "
                        "FROM M4RCH_SENT_OBJ_REL "
                        "WHERE ID_SENTENCE = ? ORDER BY ALIAS_PARENT_OBJ, ALIAS_OBJ",
                        sid
                    )
                    entry["joins"] = []
                    for join_row in cursor.fetchall():
                        entry["joins"].append({
                            "alias_parent": join_row.ALIAS_PARENT_OBJ,
                            "alias_child": join_row.ALIAS_OBJ,
                            "id_relation": join_row.ID_RELATION,
                            "relation_type": join_row.ID_RELATION_TYPE,
                        })

            return {
                "status": "success",
                "bdl_object_searched": id_object,
                "count": len(sentences),
                "sentences": sentences,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encuentra sentences que referencian un objeto BDL."
    )
    parser.add_argument(
        "id_object",
        help="Identificador del objeto BDL a buscar (ej: EMPLOYEE, STD_PERSON)"
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Incluir lista completa de objetos y JOINs de cada sentence"
    )
    args = parser.parse_args()

    result = find_sentences_by_object(args.id_object, detail=args.detail)
    print(json.dumps(result, indent=2, default=str))
