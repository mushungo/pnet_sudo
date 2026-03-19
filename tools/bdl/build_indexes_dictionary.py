# tools/bdl/build_indexes_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los Índices Lógicos
de la Base de Datos Lógica (BDL) de PeopleNet.

Consulta las tablas M4RDC_INDEX, M4RDC_INDEX_COLS, M4RDC_INDEX_INCLUDE_COLS
y crea un fichero .md por cada objeto que tenga índices, más un índice maestro.
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection, safe_filename


def fetch_all_metadata(conn):
    """Obtiene todos los metadatos necesarios de índices lógicos en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all logical indexes...")
    cursor.execute(
        "SELECT ID_INDEX, ID_OBJECT, REPLY_ALL_TABLES, IS_UNIQUE, "
        "REAL_NAME, DT_CREATE, DTE_CLOSED "
        "FROM M4RDC_INDEX;"
    )
    indexes = {}
    indexes_by_object = defaultdict(list)
    for row in cursor.fetchall():
        key = (row.ID_INDEX, row.ID_OBJECT)
        indexes[key] = row
        indexes_by_object[row.ID_OBJECT].append(row)

    print("Fetching all index columns...")
    cursor.execute(
        "SELECT ID_INDEX, ID_OBJECT, ID_FIELD, POSITION "
        "FROM M4RDC_INDEX_COLS ORDER BY POSITION;"
    )
    index_cols = defaultdict(list)
    for row in cursor.fetchall():
        index_cols[(row.ID_INDEX, row.ID_OBJECT)].append(row)

    print("Fetching all index include columns...")
    cursor.execute(
        "SELECT ID_INDEX, ID_OBJECT, ID_FIELD, POSITION "
        "FROM M4RDC_INDEX_INCLUDE_COLS ORDER BY POSITION;"
    )
    include_cols = defaultdict(list)
    for row in cursor.fetchall():
        include_cols[(row.ID_INDEX, row.ID_OBJECT)].append(row)

    print("Fetching logical object descriptions...")
    cursor.execute(
        "SELECT ID_OBJECT, ID_TRANS_OBJESP, ID_TRANS_OBJENG "
        "FROM M4RDC_LOGIC_OBJECT;"
    )
    object_info = {row.ID_OBJECT: row for row in cursor.fetchall()}

    return indexes, indexes_by_object, index_cols, include_cols, object_info


def generate_markdown_by_object(obj_id, all_meta):
    """Genera el Markdown agrupando todos los índices de un objeto lógico."""
    indexes, indexes_by_object, index_cols, include_cols, object_info = all_meta

    obj = object_info.get(obj_id)
    desc = ""
    if obj:
        desc = obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG or ""

    obj_indexes = indexes_by_object[obj_id]

    md = [f"# Índices de: `{obj_id}`\n"]
    md.append(f"**Descripción del Objeto:** {desc or 'N/A'}")
    md.append(f"\n**Total de Índices:** {len(obj_indexes)}")

    for idx in sorted(obj_indexes, key=lambda x: x.ID_INDEX):
        key = (idx.ID_INDEX, idx.ID_OBJECT)
        is_unique = "Sí" if idx.IS_UNIQUE else "No"
        real_name = idx.REAL_NAME or "N/A"

        md.append(f"\n## `{idx.ID_INDEX}`\n")
        md.append(f"**Nombre Físico:** `{real_name}`")
        md.append(f"\n**Único:** {is_unique}")
        if idx.REPLY_ALL_TABLES is not None:
            md.append(f"\n**Replica en todas las tablas:** {'Sí' if idx.REPLY_ALL_TABLES else 'No'}")

        # Columns
        cols = index_cols.get(key, [])
        if cols:
            md.append("\n**Columnas:**\n")
            md.append("| Pos | Campo |")
            md.append("|---|---|")
            for c in cols:
                md.append(f"| {c.POSITION} | `{c.ID_FIELD}` |")

        # Include columns
        inc_cols = include_cols.get(key, [])
        if inc_cols:
            md.append("\n**Columnas INCLUDE:**\n")
            md.append("| Pos | Campo |")
            md.append("|---|---|")
            for c in inc_cols:
                md.append(f"| {c.POSITION} | `{c.ID_FIELD}` |")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de índices lógicos."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "indexes")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            indexes, indexes_by_object, index_cols, include_cols, object_info = all_meta

            objects_with_indexes = sorted(indexes_by_object.keys())
            total_indexes = len(indexes)

            print(f"\nPaso 2: Generando ficheros Markdown para {len(objects_with_indexes)} objetos con {total_indexes} índices...")
            index_entries = []

            for i, obj_id in enumerate(objects_with_indexes):
                markdown_content = generate_markdown_by_object(obj_id, all_meta)

                safe_name = safe_filename(obj_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                obj = object_info.get(obj_id)
                desc = ""
                if obj:
                    desc = obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG or ""

                obj_indexes = indexes_by_object[obj_id]
                unique_count = sum(1 for idx in obj_indexes if idx.IS_UNIQUE)
                total_cols = sum(len(index_cols.get((idx.ID_INDEX, idx.ID_OBJECT), [])) for idx in obj_indexes)

                obj_link = f"[`{obj_id}`](../logical_tables/{obj_id}.md)"
                index_entries.append(
                    f"| {obj_link} | {desc[:40]} | {len(obj_indexes)} | {unique_count} | {total_cols} |"
                )
                print(f"  ({i+1}/{len(objects_with_indexes)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Índices Lógicos\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{total_indexes}** índices en **{len(objects_with_indexes)}** objetos.\n\n")
        f.write("| Objeto | Descripción | Índices | Únicos | Columnas |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
