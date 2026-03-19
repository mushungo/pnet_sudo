# tools/bdl/build_ln4_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todas las funciones LN4
del repositorio de metadatos de PeopleNet.

Consulta las tablas M4RCH_LN4_FUNCTION, M4RCH_LN4_FUNCTIO1, M4RCH_LN4_FUNC_ARG,
M4RCH_FUNC_GROUPS y M4RDC_LU_M4_TYPES. Crea un fichero .md por cada función,
un fichero por cada grupo, más un índice maestro.
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
    """Obtiene todos los metadatos necesarios de funciones LN4 en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all LN4 functions...")
    cursor.execute(
        "SELECT ID_LN4_FUNCTION, N_LN4_FUNCTION, ITEM, "
        "VARIABLE_ARGUMENTS, FUNCTION_LEVEL, ID_FUNC_GROUP "
        "FROM M4RCH_LN4_FUNCTION;"
    )
    functions = {row.ID_LN4_FUNCTION: row for row in cursor.fetchall()}

    print("Fetching all LN4 function comments...")
    cursor.execute(
        "SELECT ID_LN4_FUNCTION, COMENTESP, COMENTENG "
        "FROM M4RCH_LN4_FUNCTIO1;"
    )
    comments = {row.ID_LN4_FUNCTION: row for row in cursor.fetchall()}

    print("Fetching all LN4 function arguments...")
    cursor.execute(
        "SELECT ID_LN4_FUNCTION, ID_LN4_FUNC_ARG, N_LN4_ARGUMENTS, "
        "POSITION, ID_M4_TYPE, ID_ARGUMENT_TYPE, OPTIONAL, "
        "COMENTESP, COMENTENG "
        "FROM M4RCH_LN4_FUNC_ARG ORDER BY POSITION;"
    )
    arguments = defaultdict(list)
    for row in cursor.fetchall():
        arguments[row.ID_LN4_FUNCTION].append(row)

    print("Fetching function groups...")
    cursor.execute(
        "SELECT ID_FUNC_GROUP, DESCRIPCIONESP, DESCRIPCIONENG "
        "FROM M4RCH_FUNC_GROUPS;"
    )
    groups = {row.ID_FUNC_GROUP: row for row in cursor.fetchall()}

    print("Fetching M4 type lookup...")
    cursor.execute("SELECT ID_M4_TYPE, N_M4_TYPEESP, N_M4_TYPEENG FROM M4RDC_LU_M4_TYPES;")
    types = {row.ID_M4_TYPE: row for row in cursor.fetchall()}

    return functions, comments, arguments, groups, types


def get_type_name(types, type_id):
    """Obtiene el nombre legible de un tipo M4."""
    if type_id in types:
        t = types[type_id]
        return t.N_M4_TYPEESP or t.N_M4_TYPEENG or str(type_id)
    return str(type_id) if type_id is not None else "N/A"


def get_group_name(groups, group_id):
    """Obtiene el nombre legible de un grupo de funciones."""
    if group_id in groups:
        g = groups[group_id]
        return g.DESCRIPCIONESP or g.DESCRIPCIONENG or str(group_id)
    return str(group_id) if group_id is not None else "Sin grupo"


def generate_markdown(func_id, all_meta):
    """Genera el Markdown para una función LN4 usando los metadatos precargados."""
    functions, comments, arguments, groups, types = all_meta

    func = functions[func_id]
    comment_row = comments.get(func_id)
    comment = ""
    if comment_row:
        comment = comment_row.COMENTESP or comment_row.COMENTENG or ""

    group_name = get_group_name(groups, func.ID_FUNC_GROUP)

    md = [f"# Función LN4: `{func.N_LN4_FUNCTION}` (ID: {func_id})\n"]
    md.append(f"**Descripción:** {comment or 'N/A'}")
    md.append(f"\n**Grupo:** {group_name} (`{func.ID_FUNC_GROUP}`)")

    if func.FUNCTION_LEVEL is not None:
        md.append(f"\n**Nivel:** {func.FUNCTION_LEVEL}")
    md.append(f"\n**Argumentos Variables:** {'Sí' if func.VARIABLE_ARGUMENTS else 'No'}")
    if func.ITEM is not None:
        md.append(f"\n**Item:** {func.ITEM}")

    # --- Argumentos ---
    func_args = arguments.get(func_id, [])
    md.append(f"\n## Argumentos ({len(func_args)})\n")
    if not func_args:
        md.append("Esta función no tiene argumentos definidos.")
    else:
        md.append("| Pos | Nombre | Tipo | Tipo Arg | Opcional | Descripción |")
        md.append("|---|---|---|---|---|---|")
        for arg in func_args:
            type_name = get_type_name(types, arg.ID_M4_TYPE)
            optional = "Sí" if arg.OPTIONAL else "No"
            arg_comment = arg.COMENTESP or arg.COMENTENG or ""
            md.append(
                f"| {arg.POSITION} | `{arg.N_LN4_ARGUMENTS or ''}` | `{type_name}` | "
                f"{arg.ID_ARGUMENT_TYPE or ''} | {optional} | {arg_comment} |"
            )

    # --- Sintaxis ---
    md.append("\n## Sintaxis\n")
    arg_names = [arg.N_LN4_ARGUMENTS or f"arg{arg.POSITION}" for arg in func_args]
    if func.VARIABLE_ARGUMENTS:
        arg_names.append("...")
    signature = f"{func.N_LN4_FUNCTION}({', '.join(arg_names)})"
    md.append(f"```\n{signature}\n```")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de funciones LN4."""
    base_path = os.path.join(project_root, "docs", "02_ln4", "functions")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            functions, comments, arguments, groups, types = all_meta

            print(f"\nPaso 2: Generando ficheros Markdown para {len(functions)} funciones LN4...")
            index_entries = []
            group_functions = defaultdict(list)

            func_list = sorted(functions.keys())
            for i, func_id in enumerate(func_list):
                markdown_content = generate_markdown(func_id, all_meta)

                func = functions[func_id]
                safe_name = safe_filename(f"{func_id}_{func.N_LN4_FUNCTION}")
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                comment_row = comments.get(func_id)
                comment = ""
                if comment_row:
                    comment = comment_row.COMENTESP or comment_row.COMENTENG or ""
                group_name = get_group_name(groups, func.ID_FUNC_GROUP)
                arg_count = len(arguments.get(func_id, []))
                varargs = "Sí" if func.VARIABLE_ARGUMENTS else ""

                entry = f"| [`{func.N_LN4_FUNCTION}`]({safe_name}.md) | {func_id} | {group_name} | {arg_count} | {varargs} | {comment[:80]} |"
                index_entries.append(entry)
                group_functions[func.ID_FUNC_GROUP].append(entry)

                print(f"  ({i+1}/{len(func_list)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Funciones LN4\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** funciones en **{len(groups)}** grupos.\n\n")

        f.write("## Grupos de Funciones\n\n")
        f.write("| ID Grupo | Nombre | Funciones |\n|---|---|---|\n")
        for gid in sorted(groups.keys()):
            gname = get_group_name(groups, gid)
            gcount = len(group_functions.get(gid, []))
            f.write(f"| `{gid}` | {gname} | {gcount} |\n")

        f.write("\n## Todas las Funciones\n\n")
        f.write("| Nombre | ID | Grupo | Args | VarArgs | Descripción |\n|---|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
