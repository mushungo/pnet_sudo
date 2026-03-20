# tools/sentences/get_sentence_apisql.py
"""
Obtiene el SQL compilado (APISQL) de una sentence de PeopleNet.

Consulta M4RCH_SENTENCES3 para obtener el APISQL generado, junto con
el FILTER abstracto de M4RCH_SENTENCES1 y los metadatos de la sentence.

El APISQL usa un dialecto propietario de PeopleNet:
  - @FIELD = A.COL     -> bindings (SELECT)
  - &OBJECT            -> referencia a objeto BDL
  - #FUNC()            -> funciones built-in (#TODAY(), #SUM())
  - ?(type,size,prec)  -> parámetros (1=num, 2=str, 4=date, 5=datetime, 6=long)
  - (+)                -> Oracle-style outer join

Uso:
    python -m tools.sentences.get_sentence_apisql "ID_SENTENCE"
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def get_sentence_apisql(id_sentence):
    """Obtiene el APISQL compilado y metadatos de una sentence.

    Consulta las tablas M4RCH_SENTENCES, SENTENCES1, SENTENCES2, SENTENCES3, SENTENCES4
    para construir una vista completa del SQL generado por PeopleNet.

    Args:
        id_sentence: Identificador de la sentence.

    Returns:
        dict con APISQL, FILTER, y metadatos, o estado de error.
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

            # 2. SENTENCES1 — FILTER abstracto (template)
            cursor.execute(
                "SELECT FILTER FROM M4RCH_SENTENCES1 WHERE ID_SENTENCE = ?",
                id_sentence
            )
            s1_row = cursor.fetchone()
            result["filter_template"] = s1_row.FILTER if s1_row and s1_row.FILTER else None

            # 3. SENTENCES2 — SQL parcial / FROM clause
            cursor.execute(
                "SELECT APISQL FROM M4RCH_SENTENCES2 WHERE ID_SENTENCE = ?",
                id_sentence
            )
            s2_row = cursor.fetchone()
            result["apisql_from"] = s2_row.APISQL if s2_row and s2_row.APISQL else None

            # 4. SENTENCES3 — APISQL completo (SQL compilado)
            cursor.execute(
                "SELECT APISQL FROM M4RCH_SENTENCES3 WHERE ID_SENTENCE = ?",
                id_sentence
            )
            s3_row = cursor.fetchone()
            result["apisql"] = s3_row.APISQL if s3_row and s3_row.APISQL else None

            # 5. SENTENCES4 — SQL adicional (ORDER BY, GROUP BY, etc.)
            cursor.execute(
                "SELECT APISQL FROM M4RCH_SENTENCES4 WHERE ID_SENTENCE = ?",
                id_sentence
            )
            s4_row = cursor.fetchone()
            result["apisql_extra"] = s4_row.APISQL if s4_row and s4_row.APISQL else None

            # 6. Objetos BDL referenciados
            cursor.execute(
                "SELECT ID_OBJECT, ALIAS, IS_BASIS "
                "FROM M4RCH_SENT_OBJECTS WHERE ID_SENTENCE = ? ORDER BY IS_BASIS DESC, ALIAS",
                id_sentence
            )
            result["objects"] = []
            for row in cursor.fetchall():
                result["objects"].append({
                    "id_object": row.ID_OBJECT,
                    "alias": row.ALIAS,
                    "is_basis": bool(row.IS_BASIS) if row.IS_BASIS is not None else None,
                })

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Uso: python -m tools.sentences.get_sentence_apisql \"ID_SENTENCE\""
        }, indent=2))
        sys.exit(1)
    print(json.dumps(get_sentence_apisql(sys.argv[1]), indent=2, default=str))
