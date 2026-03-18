# tools/bdl/build_extended_functions_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todas las Funciones
Extendidas del repositorio de metadatos de PeopleNet.

Consulta las tablas M4RDC_EXTENDED_FUN, M4RDC_EXT_FUNC_ARG y M4RDC_LU_M4_TYPES
y crea un fichero .md por cada función, más un índice maestro.
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
    """Obtiene todos los metadatos necesarios de funciones extendidas en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all extended functions...")
    cursor.execute(
        "SELECT ID_FUNCTION, N_FUNCTIONESP, N_FUNCTIONENG, ID_M4_TYPE, "
        "PREC, SCALE, OWNER_FLAG, FREQUENT_USE, FREQUENT_USE_ORDER, "
        "DETAILSESP, DETAILSENG, OWNERSHIP, USABILITY "
        "FROM M4RDC_EXTENDED_FUN;"
    )
    functions = {row.ID_FUNCTION: row for row in cursor.fetchall()}

    print("Fetching all function arguments...")
    cursor.execute(
        "SELECT ID_FUNCTION, ARGUMENT_POS, N_ARGUMENT, ID_M4_TYPE, "
        "IS_MANDATORY, VALUE_MIN, VALUE_MAX, OWNER_FLAG "
        "FROM M4RDC_EXT_FUNC_ARG ORDER BY ARGUMENT_POS;"
    )
    arguments = defaultdict(list)
    for row in cursor.fetchall():
        arguments[row.ID_FUNCTION].append(row)

    print("Fetching M4 type lookup...")
    cursor.execute("SELECT ID_M4_TYPE, N_M4_TYPEESP, N_M4_TYPEENG FROM M4RDC_LU_M4_TYPES;")
    types = {row.ID_M4_TYPE: row for row in cursor.fetchall()}

    return functions, arguments, types


def get_type_name(types, type_id):
    """Obtiene el nombre legible de un tipo M4."""
    if type_id in types:
        t = types[type_id]
        return t.N_M4_TYPEESP or t.N_M4_TYPEENG or str(type_id)
    return str(type_id) if type_id is not None else "N/A"


def generate_markdown(func_id, all_meta):
    """Genera el Markdown para una función extendida usando los metadatos precargados."""
    functions, arguments, types = all_meta

    func = functions[func_id]
    name = func.N_FUNCTIONESP or func.N_FUNCTIONENG
    return_type_name = get_type_name(types, func.ID_M4_TYPE)
    details = func.DETAILSESP or func.DETAILSENG

    md = [f"# Función Extendida: `{func_id}`\n"]
    md.append(f"**Nombre:** {name or 'N/A'}")
    md.append(f"\n**Tipo de Retorno:** `{return_type_name}` (ID: {func.ID_M4_TYPE})")

    if func.PREC is not None:
        md.append(f"\n**Precisión:** {func.PREC}")
    if func.SCALE is not None:
        md.append(f"\n**Escala:** {func.SCALE}")

    md.append(f"\n**Uso Frecuente:** {'Sí' if func.FREQUENT_USE else 'No'}")
    if func.FREQUENT_USE_ORDER is not None:
        md.append(f" (Orden: {func.FREQUENT_USE_ORDER})")
    md.append(f"\n**Owner Flag:** {func.OWNER_FLAG or 'N/A'}")
    md.append(f"\n**Ownership:** {func.OWNERSHIP or 'N/A'}")
    md.append(f"\n**Usability:** {func.USABILITY or 'N/A'}")

    # --- Argumentos ---
    func_args = arguments.get(func_id, [])
    md.append("\n## Argumentos\n")
    if not func_args:
        md.append("Esta función no tiene argumentos definidos.")
    else:
        md.append(f"**Total:** {len(func_args)} argumento(s)\n")
        md.append("| Pos | Nombre | Tipo | Obligatorio | Valor Mín | Valor Máx |")
        md.append("|---|---|---|---|---|---|")
        for arg in func_args:
            arg_type_name = get_type_name(types, arg.ID_M4_TYPE)
            is_mandatory = "Sí" if arg.IS_MANDATORY else "No"
            val_min = str(arg.VALUE_MIN) if arg.VALUE_MIN is not None else ""
            val_max = str(arg.VALUE_MAX) if arg.VALUE_MAX is not None else ""
            md.append(
                f"| {arg.ARGUMENT_POS} | `{arg.N_ARGUMENT}` | `{arg_type_name}` | {is_mandatory} | {val_min} | {val_max} |"
            )

    # --- Sintaxis ---
    md.append("\n## Sintaxis\n")
    arg_names = [arg.N_ARGUMENT for arg in func_args]
    signature = f"{func_id}({', '.join(arg_names)})"
    md.append(f"```\n{signature}\n```")

    # --- Documentación detallada ---
    if details:
        md.append("\n## Documentación Detallada\n")
        md.append(details)

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de funciones extendidas."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "extended_functions")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            functions, arguments, types = all_meta

            print("\nPaso 2: Generando ficheros Markdown desde la memoria...")
            index_entries = []

            func_list = sorted(functions.keys())
            for i, func_id in enumerate(func_list):
                markdown_content = generate_markdown(func_id, all_meta)

                with open(os.path.join(base_path, f"{func_id}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                func = functions[func_id]
                name = func.N_FUNCTIONESP or func.N_FUNCTIONENG
                return_type_name = get_type_name(types, func.ID_M4_TYPE)
                arg_count = len(arguments.get(func_id, []))
                frequent = "Sí" if func.FREQUENT_USE else "No"
                index_entries.append(
                    f"| [`{func_id}`]({func_id}.md) | {name or ''} | `{return_type_name}` | {arg_count} | {frequent} |"
                )
                print(f"  ({i+1}/{len(func_list)}) -> Creado '{func_id}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Funciones Extendidas\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** funciones.\n\n")
        f.write("| ID de Función | Nombre | Tipo Retorno | Args | Uso Frecuente |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
