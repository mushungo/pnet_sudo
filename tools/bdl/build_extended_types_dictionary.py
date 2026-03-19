# tools/bdl/build_extended_types_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los Tipos Extendidos
de la Base de Datos Lógica (BDL) de PeopleNet.

Consulta las tablas M4RDC_EXTENDED_TPS, M4RDC_LU_M4_TYPES y M4RDC_BDL_FUNCTION
y crea un fichero .md por cada tipo extendido, más un índice maestro
en docs/01_bdl/extended_types/.
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
    """Obtiene todos los metadatos necesarios de tipos extendidos en consultas masivas."""
    cursor = conn.cursor()

    print("Fetching all extended types...")
    cursor.execute(
        "SELECT ID_TYPE, N_EXT_TYPEESP, N_EXT_TYPEENG, ID_M4_TYPE, "
        "PREC, SCALE, ID_DEFAULT_FUNC, DEFAULT_ARGS, "
        "ID_CONSTRAINT_FUNC, CONSTRAINT_ARGS, IS_ENCRYPTED "
        "FROM M4RDC_EXTENDED_TPS;"
    )
    types = {row.ID_TYPE: row for row in cursor.fetchall()}

    print("Fetching M4 base type lookup...")
    cursor.execute("SELECT ID_M4_TYPE, N_M4_TYPEESP, N_M4_TYPEENG FROM M4RDC_LU_M4_TYPES;")
    base_types = {row.ID_M4_TYPE: row for row in cursor.fetchall()}

    print("Fetching BDL functions (for default/constraint resolution)...")
    cursor.execute("SELECT ID_FUNCTION, N_FUNCTIONESP, N_FUNCTIONENG FROM M4RDC_BDL_FUNCTION;")
    bdl_functions = {row.ID_FUNCTION: row for row in cursor.fetchall()}

    print("Fetching field usage counts per type...")
    cursor.execute(
        "SELECT ID_TYPE, COUNT(*) as FIELD_COUNT "
        "FROM M4RDC_FIELDS GROUP BY ID_TYPE;"
    )
    field_counts = {row.ID_TYPE: row.FIELD_COUNT for row in cursor.fetchall()}

    return types, base_types, bdl_functions, field_counts


def get_base_type_name(base_types, type_id):
    """Obtiene el nombre legible de un tipo base M4."""
    if type_id in base_types:
        t = base_types[type_id]
        return t.N_M4_TYPEESP or t.N_M4_TYPEENG or str(type_id)
    return str(type_id) if type_id is not None else "N/A"


def get_function_name(bdl_functions, func_id):
    """Obtiene el nombre legible de una función BDL."""
    if func_id is not None and func_id in bdl_functions:
        f = bdl_functions[func_id]
        return f.N_FUNCTIONESP or f.N_FUNCTIONENG or str(func_id)
    return None


def generate_markdown(type_id, all_meta):
    """Genera el Markdown para un tipo extendido usando los metadatos precargados."""
    types, base_types, bdl_functions, field_counts = all_meta

    ext_type = types[type_id]
    name = ext_type.N_EXT_TYPEESP or ext_type.N_EXT_TYPEENG
    base_type_name = get_base_type_name(base_types, ext_type.ID_M4_TYPE)

    md = [f"# Tipo Extendido: `{type_id}`\n"]
    md.append(f"**Nombre:** {name or 'N/A'}")
    md.append(f"\n**Tipo Base:** `{base_type_name}` (ID: {ext_type.ID_M4_TYPE})")

    if ext_type.PREC is not None:
        md.append(f"\n**Precisión:** {ext_type.PREC}")
    if ext_type.SCALE is not None:
        md.append(f"\n**Escala:** {ext_type.SCALE}")

    md.append(f"\n**Cifrado:** {'Sí' if ext_type.IS_ENCRYPTED else 'No'}")

    usage_count = field_counts.get(type_id, 0)
    md.append(f"\n**Campos que usan este tipo:** {usage_count}")

    # --- Función de Valor por Defecto ---
    md.append("\n## Función de Valor por Defecto\n")
    if ext_type.ID_DEFAULT_FUNC is not None:
        func_name = get_function_name(bdl_functions, ext_type.ID_DEFAULT_FUNC)
        func_label = f"**Función:** `{ext_type.ID_DEFAULT_FUNC}`"
        if func_name:
            func_label += f" ({func_name})"
        md.append(func_label)
        if ext_type.DEFAULT_ARGS:
            md.append(f"\n**Argumentos:** `{ext_type.DEFAULT_ARGS}`")
    else:
        md.append("No tiene función de valor por defecto configurada.")

    # --- Función de Restricción ---
    md.append("\n## Función de Restricción (Constraint)\n")
    if ext_type.ID_CONSTRAINT_FUNC is not None:
        func_name = get_function_name(bdl_functions, ext_type.ID_CONSTRAINT_FUNC)
        func_label = f"**Función:** `{ext_type.ID_CONSTRAINT_FUNC}`"
        if func_name:
            func_label += f" ({func_name})"
        md.append(func_label)
        if ext_type.CONSTRAINT_ARGS:
            md.append(f"\n**Argumentos:** `{ext_type.CONSTRAINT_ARGS}`")
    else:
        md.append("No tiene función de restricción configurada.")

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de tipos extendidos."""
    base_path = os.path.join(project_root, "docs", "01_bdl", "extended_types")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            types, base_types, bdl_functions, field_counts = all_meta

            print(f"\nPaso 2: Generando ficheros Markdown para {len(types)} tipos extendidos...")
            index_entries = []

            type_list = sorted(types.keys())
            for i, type_id in enumerate(type_list):
                markdown_content = generate_markdown(type_id, all_meta)

                safe_name = safe_filename(type_id)
                with open(os.path.join(base_path, f"{safe_name}.md"), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                ext_type = types[type_id]
                name = ext_type.N_EXT_TYPEESP or ext_type.N_EXT_TYPEENG
                base_type_name = get_base_type_name(base_types, ext_type.ID_M4_TYPE)
                usage_count = field_counts.get(type_id, 0)
                encrypted = "Sí" if ext_type.IS_ENCRYPTED else ""
                index_entries.append(
                    f"| [`{type_id}`]({safe_name}.md) | {name or ''} | `{base_type_name}` | {usage_count} | {encrypted} |"
                )
                print(f"  ({i+1}/{len(type_list)}) -> Creado '{safe_name}.md'")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de Tipos Extendidos\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** tipos extendidos.\n\n")
        f.write("| ID del Tipo | Nombre | Tipo Base | Campos | Cifrado |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
