# tools/bdl/build_case_modules_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los Módulos de Datos
(Case Modules) del repositorio de metadatos de PeopleNet.

Consulta las tablas M4RDD_CASE_MODULES, M4RDD_CMOD_OBJS, M4RDD_CMOD_RELS
y crea un fichero .md por cada módulo, más un índice maestro.
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def fetch_all_metadata(conn):
    """Obtiene todos los metadatos necesarios de módulos de datos en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all case modules...")
    cursor.execute(
        "SELECT ID_MODULE, N_MODULEESP, N_MODULEENG, "
        "OWNER_FLAG, DEP_CROSS_MOD, OWNERSHIP, USABILITY "
        "FROM M4RDD_CASE_MODULES;"
    )
    modules = {row.ID_MODULE: row for row in cursor.fetchall()}

    print("Fetching all module objects...")
    cursor.execute(
        "SELECT ID_MODULE, ID_OBJECT, HIDDEN, ID_STATUS, DT_CREATE, DT_CLOSED "
        "FROM M4RDD_CMOD_OBJS;"
    )
    module_objects = defaultdict(list)
    for row in cursor.fetchall():
        module_objects[row.ID_MODULE].append(row)

    print("Fetching all module relations...")
    cursor.execute(
        "SELECT ID_MODULE, ID_OBJECT, ID_RELATION, LINE_STYLE, HIDDEN, DT_CREATE, DT_CLOSED "
        "FROM M4RDD_CMOD_RELS;"
    )
    module_relations = defaultdict(list)
    for row in cursor.fetchall():
        module_relations[row.ID_MODULE].append(row)

    print("Fetching logical object descriptions...")
    cursor.execute(
        "SELECT ID_OBJECT, ID_TRANS_OBJESP, ID_TRANS_OBJENG, ID_OBJECT_TYPE "
        "FROM M4RDC_LOGIC_OBJECT;"
    )
    object_info = {row.ID_OBJECT: row for row in cursor.fetchall()}

    print("Fetching relation details...")
    cursor.execute(
        "SELECT ID_RELATION, ID_OBJECT, ID_PARENT_OBJECT, ID_RELATION_TYPE "
        "FROM M4RDC_RELATIONS;"
    )
    relation_info = {row.ID_RELATION: row for row in cursor.fetchall()}

    return modules, module_objects, module_relations, object_info, relation_info


def generate_markdown(mod_id, all_meta):
    """Genera el Markdown para un módulo de datos usando los metadatos precargados."""
    modules, module_objects, module_relations, object_info, relation_info = all_meta

    mod = modules[mod_id]
    name = mod.N_MODULEESP or mod.N_MODULEENG

    md = [f"# Módulo de Datos: `{mod_id}`\n"]
    md.append(f"**Nombre:** {name or 'N/A'}")
    md.append(f"\n**Owner Flag:** {mod.OWNER_FLAG or 'N/A'}")
    md.append(f"\n**Dependencia Cross-Module:** {mod.DEP_CROSS_MOD or 'N/A'}")
    md.append(f"\n**Ownership:** {mod.OWNERSHIP or 'N/A'}")
    md.append(f"\n**Usability:** {mod.USABILITY or 'N/A'}")

    # --- Objetos del módulo ---
    mod_objs = module_objects.get(mod_id, [])
    md.append(f"\n## Objetos ({len(mod_objs)})\n")
    if not mod_objs:
        md.append("Este módulo no tiene objetos asignados.")
    else:
        md.append("| ID Objeto | Tipo | Descripción | Oculto | Estado |")
        md.append("|---|---|---|---|---|")
        for obj in sorted(mod_objs, key=lambda o: o.ID_OBJECT):
            obj_detail = object_info.get(obj.ID_OBJECT)
            if obj_detail:
                desc = obj_detail.ID_TRANS_OBJESP or obj_detail.ID_TRANS_OBJENG or ""
                obj_type = obj_detail.ID_OBJECT_TYPE or ""
            else:
                desc = ""
                obj_type = ""
            hidden = "Sí" if obj.HIDDEN else ""
            status = obj.ID_STATUS or ""
            obj_link = f"[`{obj.ID_OBJECT}`](../logical_tables/{obj.ID_OBJECT}.md)"
            md.append(f"| {obj_link} | {obj_type} | {desc} | {hidden} | {status} |")

    # --- Relaciones del módulo ---
    mod_rels = module_relations.get(mod_id, [])
    md.append(f"\n## Relaciones ({len(mod_rels)})\n")
    if not mod_rels:
        md.append("Este módulo no tiene relaciones asignadas.")
    else:
        md.append("| ID Relación | Objeto Hijo | Objeto Padre | Tipo | Oculto |")
        md.append("|---|---|---|---|---|")
        for rel in sorted(mod_rels, key=lambda r: (r.ID_OBJECT, r.ID_RELATION)):
            rel_detail = relation_info.get(rel.ID_RELATION)
            if rel_detail:
                parent_obj = rel_detail.ID_PARENT_OBJECT or ""
                rel_type = rel_detail.ID_RELATION_TYPE or ""
            else:
                parent_obj = ""
                rel_type = ""
            hidden = "Sí" if rel.HIDDEN else ""
            child_link = f"[`{rel.ID_OBJECT}`](../logical_tables/{rel.ID_OBJECT}.md)"
            parent_link = f"[`{parent_obj}`](../logical_tables/{parent_obj}.md)" if parent_obj else ""
            md.append(f"| `{rel.ID_RELATION}` | {child_link} | {parent_link} | {rel_type} | {hidden} |")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de módulos de datos."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "case_modules")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            modules, module_objects, module_relations, _, _ = all_meta

            print("\nPaso 2: Generando ficheros Markdown desde la memoria...")
            index_entries = []

            mod_list = sorted(modules.keys())
            for i, mod_id in enumerate(mod_list):
                markdown_content = generate_markdown(mod_id, all_meta)

                with open(os.path.join(base_path, f"{mod_id}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                mod = modules[mod_id]
                name = mod.N_MODULEESP or mod.N_MODULEENG
                obj_count = len(module_objects.get(mod_id, []))
                rel_count = len(module_relations.get(mod_id, []))
                index_entries.append(
                    f"| [`{mod_id}`]({mod_id}.md) | {name or ''} | {obj_count} | {rel_count} | {mod.OWNER_FLAG or ''} |"
                )
                print(f"  ({i+1}/{len(mod_list)}) -> Creado '{mod_id}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Módulos de Datos (Case Modules)\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** módulos.\n\n")
        f.write("| ID del Módulo | Nombre | Objetos | Relaciones | Owner |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
