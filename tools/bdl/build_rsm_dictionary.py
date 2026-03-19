# tools/bdl/build_rsm_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los Roles RSM
(Role Security Model) del repositorio de metadatos de PeopleNet.

Consulta las tablas M4RSC_RSM, M4RSC_RSM1, M4RDC_SEC_LOBJ y M4RDC_SEC_FIELDS
y crea un fichero .md por cada rol, más un índice maestro.
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
    """Obtiene todos los metadatos necesarios de roles RSM en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all RSM roles...")
    cursor.execute(
        "SELECT ID_RSM, N_RSMESP, N_RSMENG, ID_PARENT_RSM, OWNERSHIP, USABILITY "
        "FROM M4RSC_RSM;"
    )
    roles = {row.ID_RSM: row for row in cursor.fetchall()}

    print("Fetching RSM role comments...")
    cursor.execute(
        "SELECT ID_RSM, CAST(COMENT AS VARCHAR(MAX)) AS COMENT "
        "FROM M4RSC_RSM1;"
    )
    comments = {row.ID_RSM: row.COMENT for row in cursor.fetchall()}

    print("Fetching all object permissions...")
    cursor.execute(
        "SELECT ID_RSM, ID_OBJECT, MASK_SEL, MASK_INS, MASK_UPD, MASK_DEL, "
        "MASK_COR_INS, MASK_COR_UPD, MASK_COR_DEL, HAVE_SECURITY_FLD, "
        "CASCADE_OPER, ID_PARENT_RSM "
        "FROM M4RDC_SEC_LOBJ;"
    )
    object_perms = defaultdict(list)
    for row in cursor.fetchall():
        object_perms[row.ID_RSM].append(row)

    print("Fetching all field permissions...")
    cursor.execute(
        "SELECT ID_RSM, ID_OBJECT, ID_FIELD, IS_READ, IS_WRITE, ID_PARENT_RSM "
        "FROM M4RDC_SEC_FIELDS;"
    )
    field_perms = defaultdict(list)
    for row in cursor.fetchall():
        field_perms[row.ID_RSM].append(row)

    print("Fetching logical object descriptions...")
    cursor.execute(
        "SELECT ID_OBJECT, ID_TRANS_OBJESP, ID_TRANS_OBJENG "
        "FROM M4RDC_LOGIC_OBJECT;"
    )
    object_info = {row.ID_OBJECT: row for row in cursor.fetchall()}

    return roles, comments, object_perms, field_perms, object_info


def perm_flag(value):
    """Convierte un flag de permiso a texto legible."""
    if value is None:
        return ""
    return "Sí" if value else "No"


def generate_markdown(rsm_id, all_meta):
    """Genera el Markdown para un rol RSM usando los metadatos precargados."""
    roles, comments, object_perms, field_perms, object_info = all_meta

    role = roles[rsm_id]
    name = role.N_RSMESP or role.N_RSMENG
    comment = comments.get(rsm_id, "")

    md = [f"# Rol RSM: `{rsm_id}`\n"]
    md.append(f"**Nombre:** {name or 'N/A'}")

    if role.ID_PARENT_RSM:
        md.append(f"\n**Hereda de:** [`{role.ID_PARENT_RSM}`]({role.ID_PARENT_RSM}.md)")
    md.append(f"\n**Ownership:** {role.OWNERSHIP or 'N/A'}")
    md.append(f"\n**Usability:** {role.USABILITY or 'N/A'}")

    if comment:
        md.append(f"\n**Comentario:** {comment}")

    # --- Permisos sobre objetos ---
    obj_perms = object_perms.get(rsm_id, [])
    md.append(f"\n## Permisos sobre Objetos ({len(obj_perms)})\n")
    if not obj_perms:
        md.append("Este rol no tiene permisos sobre objetos definidos.")
    else:
        md.append("| Objeto | Descripción | SEL | INS | UPD | DEL | Hereda |")
        md.append("|---|---|---|---|---|---|---|")
        for p in sorted(obj_perms, key=lambda x: x.ID_OBJECT):
            obj = object_info.get(p.ID_OBJECT)
            desc = ""
            if obj:
                desc = obj.ID_TRANS_OBJESP or obj.ID_TRANS_OBJENG or ""
            obj_link = f"[`{p.ID_OBJECT}`](../logical_tables/{p.ID_OBJECT}.md)"
            inherited = f"`{p.ID_PARENT_RSM}`" if p.ID_PARENT_RSM else ""
            md.append(
                f"| {obj_link} | {desc[:50]} | {perm_flag(p.MASK_SEL)} | "
                f"{perm_flag(p.MASK_INS)} | {perm_flag(p.MASK_UPD)} | "
                f"{perm_flag(p.MASK_DEL)} | {inherited} |"
            )

    # --- Permisos sobre campos ---
    fld_perms = field_perms.get(rsm_id, [])
    if fld_perms:
        md.append(f"\n## Permisos sobre Campos ({len(fld_perms)})\n")
        md.append("| Objeto | Campo | Lectura | Escritura | Hereda |")
        md.append("|---|---|---|---|---|")
        for fp in sorted(fld_perms, key=lambda x: (x.ID_OBJECT, x.ID_FIELD)):
            inherited = f"`{fp.ID_PARENT_RSM}`" if fp.ID_PARENT_RSM else ""
            md.append(
                f"| `{fp.ID_OBJECT}` | `{fp.ID_FIELD}` | {perm_flag(fp.IS_READ)} | "
                f"{perm_flag(fp.IS_WRITE)} | {inherited} |"
            )

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de roles RSM."""
    base_path = os.path.join(project_root, "docs", "03_security", "rsm_roles")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            roles, comments, object_perms, field_perms, _ = all_meta

            print(f"\nPaso 2: Generando ficheros Markdown para {len(roles)} roles RSM...")
            index_entries = []

            role_list = sorted(roles.keys())
            for i, rsm_id in enumerate(role_list):
                markdown_content = generate_markdown(rsm_id, all_meta)

                safe_name = safe_filename(rsm_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                role = roles[rsm_id]
                name = role.N_RSMESP or role.N_RSMENG or ""
                obj_count = len(object_perms.get(rsm_id, []))
                fld_count = len(field_perms.get(rsm_id, []))
                parent = role.ID_PARENT_RSM or ""
                index_entries.append(
                    f"| [`{rsm_id}`]({safe_name}.md) | {name[:40]} | {parent} | {obj_count} | {fld_count} |"
                )
                print(f"  ({i+1}/{len(role_list)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Roles RSM (Role Security Model)\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** roles.\n\n")
        f.write("| ID RSM | Nombre | Hereda De | Permisos Obj. | Permisos Campo |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
