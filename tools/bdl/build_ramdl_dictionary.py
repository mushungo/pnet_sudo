# tools/bdl/build_ramdl_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los Objetos RAMDL
(transporte) del repositorio de metadatos de PeopleNet.

Consulta las tablas M4RDC_RAMDL_OBJECTS, M4RDC_RAMDL_OBJEC1 y M4RDC_RAMDL_VER
y crea un fichero .md por cada objeto, más un índice maestro.
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
    """Obtiene todos los metadatos necesarios de objetos RAMDL en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all RAMDL objects...")
    cursor.execute(
        "SELECT ID_OBJECT, VER_LOWEST, VER_HIGHEST, N_OBJECTESP, N_OBJECTENG "
        "FROM M4RDC_RAMDL_OBJECTS;"
    )
    objects_by_id = defaultdict(list)
    for row in cursor.fetchall():
        objects_by_id[row.ID_OBJECT].append(row)

    print("Fetching RAMDL XML presence...")
    cursor.execute(
        "SELECT ID_OBJECT, VER_LOWEST, "
        "CASE WHEN XML IS NULL THEN 0 ELSE DATALENGTH(XML) END AS XML_SIZE "
        "FROM M4RDC_RAMDL_OBJEC1;"
    )
    xml_info = {}
    for row in cursor.fetchall():
        xml_info[(row.ID_OBJECT, row.VER_LOWEST)] = row.XML_SIZE

    print("Fetching RAMDL versions...")
    cursor.execute("SELECT VERSION FROM M4RDC_RAMDL_VER ORDER BY VERSION;")
    versions = [row.VERSION for row in cursor.fetchall()]

    return objects_by_id, xml_info, versions


def generate_markdown(obj_id, all_meta):
    """Genera el Markdown para un objeto RAMDL usando los metadatos precargados."""
    objects_by_id, xml_info, versions = all_meta

    obj_versions = objects_by_id[obj_id]
    first = obj_versions[0]
    name = first.N_OBJECTESP or first.N_OBJECTENG

    md = [f"# Objeto RAMDL: `{obj_id}`\n"]
    md.append(f"**Nombre:** {name or 'N/A'}")
    md.append(f"\n**Versiones:** {len(obj_versions)}")

    md.append("\n## Historial de Versiones\n")
    md.append("| Versión Mín | Versión Máx | Nombre | XML |")
    md.append("|---|---|---|---|")
    for v in sorted(obj_versions, key=lambda x: x.VER_LOWEST):
        ver_name = v.N_OBJECTESP or v.N_OBJECTENG or ""
        xml_size = xml_info.get((obj_id, v.VER_LOWEST), 0)
        has_xml = f"Sí ({xml_size:,} bytes)" if xml_size else "No"
        md.append(f"| {v.VER_LOWEST} | {v.VER_HIGHEST} | {ver_name} | {has_xml} |")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de objetos RAMDL."""
    base_path = os.path.join(project_root, "docs", "04_ramdl", "objects")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            objects_by_id, xml_info, versions = all_meta

            unique_objects = sorted(objects_by_id.keys())
            total_versions = sum(len(v) for v in objects_by_id.values())

            print(f"\nPaso 2: Generando ficheros Markdown para {len(unique_objects)} objetos RAMDL ({total_versions} versiones)...")
            index_entries = []

            for i, obj_id in enumerate(unique_objects):
                markdown_content = generate_markdown(obj_id, all_meta)

                safe_name = safe_filename(obj_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                obj_versions = objects_by_id[obj_id]
                first = obj_versions[0]
                name = first.N_OBJECTESP or first.N_OBJECTENG or ""
                min_ver = min(v.VER_LOWEST for v in obj_versions)
                max_ver = max(v.VER_HIGHEST for v in obj_versions) if any(v.VER_HIGHEST is not None for v in obj_versions) else ""
                index_entries.append(
                    f"| [`{obj_id}`]({safe_name}.md) | {name[:40]} | {len(obj_versions)} | {min_ver} | {max_ver} |"
                )
                print(f"  ({i+1}/{len(unique_objects)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Objetos RAMDL (Transporte)\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(unique_objects)}** objetos con **{total_versions}** versiones.\n\n")

        f.write("### Versiones RAMDL Registradas\n\n")
        f.write(", ".join(str(v) for v in versions))
        f.write("\n\n")

        f.write("## Objetos\n\n")
        f.write("| ID Objeto | Nombre | Versiones | Ver. Mín | Ver. Máx |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
