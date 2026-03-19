# tools/sentences/list_sentences.py
"""
Lista todas las sentences (definiciones de acceso a datos SQL-like) del repositorio
de metadatos de PeopleNet.

Cada sentence define cómo un TI carga datos: qué objetos BDL consulta,
con qué JOINs, filtros y ordenación.

Uso:
    python -m tools.sentences.list_sentences
    python -m tools.sentences.list_sentences --type 1
    python -m tools.sentences.list_sentences --search "EMPLOYEE"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def list_sentences(sent_type=None, search=None):
    """Obtiene la lista de todas las sentences con información resumida.

    Args:
        sent_type: Filtrar por ID_SENT_TYPE (ej. 1, 2, 3...).
        search: Texto libre para buscar en ID_SENTENCE.

    Returns:
        dict con status y lista de sentences.
    """
    sql_query = """
    SELECT
        s.ID_SENTENCE,
        s.IS_DISTINCT,
        s.ID_SENT_TYPE,
        s.ID_GROUP_OBJECTS,
        COUNT(DISTINCT so.ID_OBJECT) AS object_count,
        COUNT(DISTINCT sor.ID_RELATION) AS join_count,
        COUNT(DISTINCT saf.ID_FIELD) AS filter_field_count
    FROM
        M4RCH_SENTENCES s
    LEFT JOIN
        M4RCH_SENT_OBJECTS so ON s.ID_SENTENCE = so.ID_SENTENCE
    LEFT JOIN
        M4RCH_SENT_OBJ_REL sor ON s.ID_SENTENCE = sor.ID_SENTENCE
    LEFT JOIN
        M4RCH_SENT_ADD_FLD saf ON s.ID_SENTENCE = saf.ID_SENTENCE
    """
    params = []
    conditions = []

    if sent_type is not None:
        conditions.append("s.ID_SENT_TYPE = ?")
        params.append(sent_type)

    if search:
        conditions.append("s.ID_SENTENCE LIKE ?")
        search_pattern = f"%{search}%"
        params.append(search_pattern)

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += """
    GROUP BY
        s.ID_SENTENCE, s.IS_DISTINCT, s.ID_SENT_TYPE, s.ID_GROUP_OBJECTS
    ORDER BY
        s.ID_SENTENCE;
    """

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, *params) if params else cursor.execute(sql_query)
            rows = cursor.fetchall()

            sentences = []
            for row in rows:
                sentences.append({
                    "id_sentence": row.ID_SENTENCE,
                    "is_distinct": bool(row.IS_DISTINCT) if row.IS_DISTINCT is not None else None,
                    "sent_type": row.ID_SENT_TYPE,
                    "group_objects": row.ID_GROUP_OBJECTS,
                    "object_count": row.object_count,
                    "join_count": row.join_count,
                    "filter_field_count": row.filter_field_count,
                })

            return {
                "status": "success",
                "total": len(sentences),
                "sentences": sentences,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lista sentences (definiciones de acceso a datos) de PeopleNet.")
    parser.add_argument("--type", type=int, dest="sent_type", help="Filtrar por tipo de sentence (ej. 1, 2, 3)")
    parser.add_argument("--search", help="Buscar por texto en ID_SENTENCE")
    args = parser.parse_args()

    result = list_sentences(sent_type=args.sent_type, search=args.search)
    print(json.dumps(result, indent=2, default=str))
