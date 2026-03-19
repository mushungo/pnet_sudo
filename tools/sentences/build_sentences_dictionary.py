# tools/sentences/build_sentences_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todas las sentences
(definiciones de acceso a datos) de PeopleNet.

Consulta las tablas de metadatos del repositorio y crea un fichero .md
por cada sentence, más un índice maestro.

Uso:
    python -m tools.sentences.build_sentences_dictionary
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection, safe_filename


# Mapeo de tipos de relación a nombres legibles
RELATION_TYPE_MAP = {
    1: "INNER JOIN",
    2: "LEFT JOIN",
    3: "OUTER JOIN",
}


def fetch_all_metadata(conn):
    """Obtiene todos los metadatos de sentences en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all sentences...")
    cursor.execute(
        "SELECT ID_SENTENCE, IS_DISTINCT, ID_SENT_TYPE, ID_GROUP_OBJECTS "
        "FROM M4RCH_SENTENCES;"
    )
    sentences = {row.ID_SENTENCE: row for row in cursor.fetchall()}

    print("Fetching all sentence objects (FROM clause)...")
    cursor.execute(
        "SELECT ID_SENTENCE, ID_OBJECT, ALIAS, IS_BASIS "
        "FROM M4RCH_SENT_OBJECTS;"
    )
    objects = defaultdict(list)
    for row in cursor.fetchall():
        objects[row.ID_SENTENCE].append(row)

    print("Fetching all sentence object relations (JOIN clause)...")
    cursor.execute(
        "SELECT ID_SENTENCE, ALIAS_PARENT_OBJ, ALIAS_OBJ, ID_RELATION, ID_RELATION_TYPE "
        "FROM M4RCH_SENT_OBJ_REL;"
    )
    joins = defaultdict(list)
    for row in cursor.fetchall():
        joins[row.ID_SENTENCE].append(row)

    print("Fetching all filter/order fields...")
    cursor.execute(
        "SELECT ID_SENTENCE, ID_FIELD, ALIAS, ID_WHERE_TYPE, ID_OBJECT "
        "FROM M4RCH_SENT_ADD_FLD;"
    )
    filters = defaultdict(list)
    for row in cursor.fetchall():
        filters[row.ID_SENTENCE].append(row)

    print("Fetching all sentence functions...")
    cursor.execute(
        "SELECT ID_SENTENCE, ID_FUNCTION, POSITION "
        "FROM M4RCH_SENT_FUNCS;"
    )
    functions = defaultdict(list)
    for row in cursor.fetchall():
        functions[row.ID_SENTENCE].append(row)

    print("Fetching all calculated columns...")
    cursor.execute(
        "SELECT ID_SENTENCE, ID_CALCULUS, ID_M4_TYPE, PREC, SCALE, EXPRESSION "
        "FROM M4RCH_SENT_CALCULU;"
    )
    calculations = defaultdict(list)
    for row in cursor.fetchall():
        calculations[row.ID_SENTENCE].append(row)

    return sentences, objects, joins, filters, functions, calculations


def generate_markdown(sent_id, all_meta):
    """Genera el Markdown para una sentence usando los metadatos precargados."""
    sentences, all_objects, all_joins, all_filters, all_functions, all_calcs = all_meta

    sent = sentences[sent_id]
    md = [f"# Sentence: `{sent_id}`\n"]

    sent_type = sent.ID_SENT_TYPE
    md.append(f"**Tipo:** {sent_type or 'N/A'}")
    md.append(f"**Distinct:** {'Sí' if sent.IS_DISTINCT else 'No'}")
    if sent.ID_GROUP_OBJECTS:
        md.append(f"**Grupo de Objetos:** `{sent.ID_GROUP_OBJECTS}`")

    # --- FROM clause (objetos) ---
    objs = sorted(all_objects.get(sent_id, []), key=lambda o: (not (o.IS_BASIS or 0), o.ALIAS or ""))
    md.append("\n## Objetos (FROM)\n")
    if not objs:
        md.append("Sin objetos definidos.")
    else:
        md.append("| Alias | Objeto BDL | Objeto Base |")
        md.append("|---|---|---|")
        for obj in objs:
            is_basis = "Sí" if obj.IS_BASIS else ""
            md.append(f"| `{obj.ALIAS or ''}` | `{obj.ID_OBJECT}` | {is_basis} |")

    # --- JOINs ---
    jns = all_joins.get(sent_id, [])
    md.append("\n## Relaciones (JOIN)\n")
    if not jns:
        md.append("Sin relaciones entre objetos.")
    else:
        md.append("| Alias Padre | Alias Hijo | Relación BDL | Tipo |")
        md.append("|---|---|---|---|")
        for jn in jns:
            rel_type = RELATION_TYPE_MAP.get(jn.ID_RELATION_TYPE, str(jn.ID_RELATION_TYPE))
            md.append(f"| `{jn.ALIAS_PARENT_OBJ or ''}` | `{jn.ALIAS_OBJ or ''}` | `{jn.ID_RELATION or ''}` | {rel_type} |")

    # --- Filtros / WHERE / ORDER BY ---
    flts = all_filters.get(sent_id, [])
    md.append("\n## Campos de Filtro / Orden\n")
    if not flts:
        md.append("Sin campos adicionales de filtro u ordenación.")
    else:
        md.append("| Campo | Alias | Tipo Cláusula | Objeto |")
        md.append("|---|---|---|---|")
        for flt in sorted(flts, key=lambda f: (f.ID_WHERE_TYPE or 0, f.ID_FIELD or "")):
            md.append(f"| `{flt.ID_FIELD or ''}` | `{flt.ALIAS or ''}` | {flt.ID_WHERE_TYPE or ''} | `{flt.ID_OBJECT or ''}` |")

    # --- Funciones SQL ---
    fns = all_functions.get(sent_id, [])
    if fns:
        md.append("\n## Funciones SQL\n")
        md.append("| Función | Posición |")
        md.append("|---|---|")
        for fn in sorted(fns, key=lambda f: f.POSITION or 0):
            md.append(f"| `{fn.ID_FUNCTION}` | {fn.POSITION} |")

    # --- Columnas calculadas ---
    calcs = all_calcs.get(sent_id, [])
    if calcs:
        md.append("\n## Columnas Calculadas\n")
        md.append("| ID Cálculo | Tipo M4 | Precisión | Escala | Expresión |")
        md.append("|---|---|---|---|---|")
        for calc in calcs:
            md.append(
                f"| `{calc.ID_CALCULUS}` | `{calc.ID_M4_TYPE or ''}` "
                f"| {calc.PREC or ''} | {calc.SCALE or ''} "
                f"| `{calc.EXPRESSION or ''}` |"
            )

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de sentences."""
    base_path = os.path.join(project_root, "docs", "03_sentences")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            sentences = all_meta[0]

            print(f"\nPaso 2: Generando {len(sentences)} ficheros Markdown...")
            index_entries = []

            sentence_list = sorted(sentences.keys())
            for i, sent_id in enumerate(sentence_list):
                markdown_content = generate_markdown(sent_id, all_meta)

                safe_name = safe_filename(sent_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                sent = sentences[sent_id]
                obj_count = len(all_meta[1].get(sent_id, []))
                index_entries.append(
                    f"| [`{sent_id}`]({safe_name}.md) | {sent.ID_SENT_TYPE or ''} | {obj_count} |"
                )

                if (i + 1) % 500 == 0 or (i + 1) == len(sentence_list):
                    print(f"  ({i + 1}/{len(sentence_list)}) procesadas...")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Sentences\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** sentences.\n\n")
        f.write("| ID Sentence | Tipo | Objetos |\n|---|---|---|\n")
        f.write("\n".join(index_entries))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
