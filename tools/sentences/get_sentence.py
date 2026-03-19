# tools/sentences/get_sentence.py
"""
Obtiene la definición completa de una sentence de PeopleNet.

Incluye los objetos BDL referenciados (FROM), sus relaciones (JOIN),
campos adicionales (WHERE/ORDER BY/GROUP BY), funciones y cálculos.

Uso:
    python -m tools.sentences.get_sentence "ID_SENTENCE"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_sentence_details(id_sentence):
    """Obtiene la definición completa de una sentence.

    Consulta la sentence principal y todas sus tablas relacionadas:
    SENT_OBJECTS (FROM), SENT_OBJ_REL (JOIN), SENT_ADD_FLD (WHERE/ORDER),
    SENT_FUNCS (funciones), SENT_CALCULU (cálculos).

    Args:
        id_sentence: Identificador de la sentence.

    Returns:
        dict con la definición completa o estado de error.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Sentence principal
            cursor.execute(
                "SELECT ID_SENTENCE, IS_DISTINCT, ID_SENT_TYPE, ID_GROUP_OBJECTS "
                "FROM M4RCH_SENTENCES WHERE ID_SENTENCE = ?",
                id_sentence
            )
            main_row = cursor.fetchone()
            if not main_row:
                return {"status": "not_found", "message": f"No se encontró la sentence '{id_sentence}'."}

            result = {
                "id_sentence": main_row.ID_SENTENCE,
                "is_distinct": bool(main_row.IS_DISTINCT) if main_row.IS_DISTINCT is not None else None,
                "sent_type": main_row.ID_SENT_TYPE,
                "group_objects": main_row.ID_GROUP_OBJECTS,
            }

            # 2. Objetos (FROM clause)
            cursor.execute(
                "SELECT ID_OBJECT, ALIAS, IS_BASIS "
                "FROM M4RCH_SENT_OBJECTS "
                "WHERE ID_SENTENCE = ? ORDER BY IS_BASIS DESC, ALIAS",
                id_sentence
            )
            result["objects"] = []
            for row in cursor.fetchall():
                result["objects"].append({
                    "id_object": row.ID_OBJECT,
                    "alias": row.ALIAS,
                    "is_basis": bool(row.IS_BASIS) if row.IS_BASIS is not None else None,
                })

            # 3. Relaciones entre objetos (JOIN clause)
            cursor.execute(
                "SELECT ALIAS_PARENT_OBJ, ALIAS_OBJ, ID_RELATION, ID_RELATION_TYPE "
                "FROM M4RCH_SENT_OBJ_REL "
                "WHERE ID_SENTENCE = ? ORDER BY ALIAS_PARENT_OBJ, ALIAS_OBJ",
                id_sentence
            )
            result["joins"] = []
            for row in cursor.fetchall():
                result["joins"].append({
                    "alias_parent": row.ALIAS_PARENT_OBJ,
                    "alias_child": row.ALIAS_OBJ,
                    "id_relation": row.ID_RELATION,
                    "relation_type": row.ID_RELATION_TYPE,
                })

            # 4. Campos adicionales (WHERE/ORDER BY/GROUP BY)
            cursor.execute(
                "SELECT ID_FIELD, ALIAS, ID_WHERE_TYPE, ID_OBJECT "
                "FROM M4RCH_SENT_ADD_FLD "
                "WHERE ID_SENTENCE = ? ORDER BY ID_WHERE_TYPE, ID_FIELD",
                id_sentence
            )
            result["filter_fields"] = []
            for row in cursor.fetchall():
                result["filter_fields"].append({
                    "id_field": row.ID_FIELD,
                    "alias": row.ALIAS,
                    "where_type": row.ID_WHERE_TYPE,
                    "id_object": row.ID_OBJECT,
                })

            # 5. Funciones SQL usadas
            cursor.execute(
                "SELECT ID_FUNCTION, POSITION "
                "FROM M4RCH_SENT_FUNCS "
                "WHERE ID_SENTENCE = ? ORDER BY POSITION",
                id_sentence
            )
            result["functions"] = []
            for row in cursor.fetchall():
                result["functions"].append({
                    "id_function": row.ID_FUNCTION,
                    "position": row.POSITION,
                })

            # 6. Columnas calculadas
            cursor.execute(
                "SELECT ID_CALCULUS, ID_M4_TYPE, PREC, SCALE, EXPRESSION "
                "FROM M4RCH_SENT_CALCULU "
                "WHERE ID_SENTENCE = ? ORDER BY ID_CALCULUS",
                id_sentence
            )
            result["calculated_columns"] = []
            for row in cursor.fetchall():
                result["calculated_columns"].append({
                    "id_calculus": row.ID_CALCULUS,
                    "m4_type": row.ID_M4_TYPE,
                    "precision": row.PREC,
                    "scale": row.SCALE,
                    "expression": row.EXPRESSION,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.sentences.get_sentence \"ID_SENTENCE\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_sentence_details(sys.argv[1]), indent=2, default=str))
