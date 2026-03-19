# tools/bdl/build_bdl_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los objetos
de la Base de Datos Lógica (BDL) de PeopleNet.

Consulta las tablas de metadatos del repositorio y crea un fichero .md
por cada objeto lógico, más un índice maestro.
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
    """Obtiene todos los metadatos necesarios de la BDL en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all logical objects...")
    cursor.execute("SELECT ID_OBJECT, ID_TRANS_OBJESP, ID_TRANS_OBJENG, REAL_NAME FROM M4RDC_LOGIC_OBJECT;")
    objects = {row.ID_OBJECT: row for row in cursor.fetchall()}

    print("Fetching all fields...")
    cursor.execute(
        "SELECT ID_OBJECT, ID_FIELD, REAL_NAME, ID_TYPE, POSITION, POS_PK, NOT_NULL, "
        "ID_TRANS_FLDESP, ID_TRANS_FLDENG FROM M4RDC_FIELDS;"
    )
    fields = defaultdict(list)
    for row in cursor.fetchall():
        fields[row.ID_OBJECT].append(row)

    print("Fetching all relations...")
    cursor.execute("SELECT ID_RELATION, ID_OBJECT, ID_PARENT_OBJECT, ID_RELATION_TYPE FROM M4RDC_RELATIONS;")
    relations = {row.ID_RELATION: row for row in cursor.fetchall()}

    print("Fetching all relation fields...")
    cursor.execute("SELECT ID_RELATION, ID_FIELD, ID_PARENT_FIELD FROM M4RDC_RLTION_FLDS;")
    rel_fields = defaultdict(list)
    lookup_map = {}
    for row in cursor.fetchall():
        rel_fields[row.ID_RELATION].append(row)
        if row.ID_RELATION in relations:
            child_object_id = relations[row.ID_RELATION].ID_OBJECT
            lookup_map[(child_object_id, row.ID_FIELD)] = row.ID_RELATION

    return objects, fields, relations, rel_fields, lookup_map


def generate_markdown(obj_id, all_meta):
    """Genera el Markdown para un objeto usando los metadatos precargados."""
    all_objects, all_fields, all_relations, all_rel_fields, lookup_map = all_meta

    obj_details = all_objects[obj_id]
    description = obj_details.ID_TRANS_OBJESP or obj_details.ID_TRANS_OBJENG
    md = [f"# Objeto BDL: `{obj_id}`\n"]
    md.append(f"**Descripción:** {description or 'N/A'}")
    md.append(f"\n**Tabla Física:** `{obj_details.REAL_NAME or 'N/A'}`")

    # --- Campos ---
    md.append("\n## Campos\n")
    obj_fields = sorted(all_fields.get(obj_id, []), key=lambda f: (f.POS_PK is not None, f.POSITION))
    if not obj_fields:
        md.append("Este objeto no tiene campos definidos.")
    else:
        md.append("| Clave | Pos | ID del Campo | Tipo Extendido | No Nulo | Descripción (Lookup) |")
        md.append("|---|---|---|---|---|---|")
        for field in obj_fields:
            safe_type_name = safe_filename(field.ID_TYPE)
            type_link = f"[`{field.ID_TYPE}`](../extended_types/{safe_type_name}.md)"
            field_desc = field.ID_TRANS_FLDESP or field.ID_TRANS_FLDENG or ""

            if (obj_id, field.ID_FIELD) in lookup_map:
                rel_id = lookup_map[(obj_id, field.ID_FIELD)]
                if rel_id in all_relations:
                    parent_obj = all_relations[rel_id].ID_PARENT_OBJECT
                    field_desc += f" (Lookup a `{parent_obj}`)"

            is_pk = "Sí" if field.POS_PK else ""
            is_not_null = "Sí" if field.NOT_NULL else ""
            md.append(
                f"| {is_pk} | {field.POSITION} | `{field.ID_FIELD}` | {type_link} | {is_not_null} | {field_desc} |"
            )

    # --- Relaciones ---
    md.append("\n## Relaciones Lógicas\n")
    outgoing = [r for r in all_relations.values() if r.ID_OBJECT == obj_id]
    incoming = [r for r in all_relations.values() if r.ID_PARENT_OBJECT == obj_id]

    md.append("### Relaciones Salientes (Este objeto es el hijo)\n")
    if not outgoing:
        md.append("Este objeto no apunta a ningún otro objeto.")
    else:
        md.append("| Objeto Padre | ID Relación | Campos (Hijo -> Padre) |")
        md.append("|---|---|---|")
        for rel in outgoing:
            mappings = ", ".join(
                [f"`{m.ID_FIELD}` -> `{m.ID_PARENT_FIELD}`" for m in all_rel_fields.get(rel.ID_RELATION, [])]
            )
            md.append(f"| [`{rel.ID_PARENT_OBJECT}`]({rel.ID_PARENT_OBJECT}.md) | `{rel.ID_RELATION}` | {mappings} |")

    md.append("\n### Relaciones Entrantes (Este objeto es el padre)\n")
    if not incoming:
        md.append("Ningún otro objeto apunta a este.")
    else:
        md.append("| Objeto Hijo | ID Relación | Campos (Hijo -> Padre) |")
        md.append("|---|---|---|")
        for rel in incoming:
            mappings = ", ".join(
                [f"`{m.ID_FIELD}` -> `{m.ID_PARENT_FIELD}`" for m in all_rel_fields.get(rel.ID_RELATION, [])]
            )
            md.append(f"| [`{rel.ID_OBJECT}`]({rel.ID_OBJECT}.md) | `{rel.ID_RELATION}` | {mappings} |")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de la BDL."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "logical_tables")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            all_objects, _, _, _, _ = all_meta

            print("\nPaso 2: Generando ficheros Markdown desde la memoria...")
            index_entries = []

            object_list = list(all_objects.keys())
            for i, obj_id in enumerate(object_list):
                markdown_content = generate_markdown(obj_id, all_meta)

                safe_name = safe_filename(obj_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                obj_details = all_objects[obj_id]
                description = obj_details.ID_TRANS_OBJESP or obj_details.ID_TRANS_OBJENG
                index_entries.append(
                    f"| [`{obj_id}`]({safe_name}.md) | {description or ''} | `{obj_details.REAL_NAME or ''}` |"
                )
                print(f"  ({i+1}/{len(object_list)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Tablas Lógicas (BDL)\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Contiene **{len(index_entries)}** objetos.\n\n")
        f.write("| ID del Objeto | Descripción | Tabla Física |\n|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
