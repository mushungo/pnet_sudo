# tools/bdl/build_views_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todas las Vistas SQL
definidas en el repositorio de metadatos de PeopleNet.

Consulta las tablas M4RDC_VIEW_CODE, M4RDC_VIEW_CODE1 y M4RDC_LOGIC_OBJECT
y crea un fichero .md por cada vista, más un índice maestro.
"""
import sys
import os
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection, safe_filename


def fetch_all_metadata(conn):
    """Obtiene todos los metadatos necesarios de vistas SQL en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all view metadata...")
    cursor.execute(
        "SELECT ID_OBJECT, IS_REAL, DT_CREATE, DT_CLOSED, DT_MOD, DT_MOD_SCRIPT, "
        "ID_APPROLE, ID_SECUSER "
        "FROM M4RDC_VIEW_CODE;"
    )
    views = {row.ID_OBJECT: row for row in cursor.fetchall()}

    print("Fetching all view SQL code...")
    cursor.execute(
        "SELECT ID_OBJECT, CAST(VIEW_CODE AS VARCHAR(MAX)) AS VIEW_CODE "
        "FROM M4RDC_VIEW_CODE1;"
    )
    view_code = {row.ID_OBJECT: row.VIEW_CODE for row in cursor.fetchall()}

    print("Fetching logical object descriptions...")
    cursor.execute(
        "SELECT ID_OBJECT, ID_TRANS_OBJESP, ID_TRANS_OBJENG, REAL_NAME "
        "FROM M4RDC_LOGIC_OBJECT;"
    )
    object_info = {row.ID_OBJECT: row for row in cursor.fetchall()}

    return views, view_code, object_info


def generate_markdown(view_id, all_meta):
    """Genera el Markdown para una vista SQL usando los metadatos precargados."""
    views, view_code, object_info = all_meta

    view = views[view_id]
    obj = object_info.get(view_id)
    description = ""
    real_name = ""
    if obj:
        description = obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG or ""
        real_name = obj.REAL_NAME or ""

    md = [f"# Vista SQL: `{view_id}`\n"]
    md.append(f"**Descripción:** {description or 'N/A'}")
    md.append(f"\n**Nombre Físico:** `{real_name or 'N/A'}`")
    md.append(f"\n**Es Real:** {'Sí' if view.IS_REAL else 'No'}")

    if view.DT_CREATE:
        md.append(f"\n**Fecha Creación:** {view.DT_CREATE}")
    if view.DT_MOD:
        md.append(f"\n**Última Modificación:** {view.DT_MOD}")
    if view.ID_APPROLE:
        md.append(f"\n**AppRole:** {view.ID_APPROLE}")

    # --- Código SQL ---
    code = view_code.get(view_id)
    md.append("\n## Código SQL\n")
    if code:
        md.append(f"```sql\n{code}\n```")
    else:
        md.append("No se encontró código SQL para esta vista.")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de vistas SQL."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "views")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            views, view_code, object_info = all_meta

            print(f"\nPaso 2: Generando ficheros Markdown para {len(views)} vistas...")
            index_entries = []

            view_list = sorted(views.keys())
            for i, view_id in enumerate(view_list):
                markdown_content = generate_markdown(view_id, all_meta)

                safe_name = safe_filename(view_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                obj = object_info.get(view_id)
                description = ""
                real_name = ""
                if obj:
                    description = obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG or ""
                    real_name = obj.REAL_NAME or ""
                has_code = "Sí" if view_code.get(view_id) else "No"
                index_entries.append(
                    f"| [`{view_id}`]({safe_name}.md) | {description} | `{real_name}` | {has_code} |"
                )
                print(f"  ({i+1}/{len(view_list)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Vistas SQL\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** vistas.\n\n")
        f.write("| ID de Vista | Descripción | Nombre Físico | Tiene Código |\n|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
