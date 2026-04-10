# tools/m4object/build_m4object_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los m4objects
(canales) de PeopleNet.

Consulta las tablas de metadatos M4RCH_* del repositorio y crea un fichero .md
por cada canal, más un índice maestro.

El Markdown generado incluye para cada canal:
  - Cabecera con metadatos del T3
  - Herencia de canales
  - Nodos con su TI asociada
  - Items (campos/métodos) por TI
  - Conteo de reglas por TI

Uso:
    python -m tools.m4object.build_m4object_dictionary
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection, safe_filename
from tools.m4object.m4object_maps import (
    EXE_TYPE_MAP, STREAM_TYPE_MAP, NODES_TYPE_MAP, ITEM_CSTYPE_MAP, decode,
)


def fetch_all_metadata(conn):
    """Obtiene todos los metadatos necesarios de los m4objects en consultas masivas."""
    cursor = conn.cursor()

    # T3S — canales
    print("Fetching all m4objects (T3S)...")
    cursor.execute("""
        SELECT ID_T3, N_T3ESP, N_T3ENG, ID_STREAM_TYPE, ID_CATEGORY,
               ID_SUBCATEGORY, HAVE_SECURITY, IS_EXTERNAL, CS_EXE_TYPE
        FROM M4RCH_T3S
        ORDER BY ID_T3
    """)
    t3s = {row.ID_T3: row for row in cursor.fetchall()}
    print(f"  -> {len(t3s)} canales encontrados.")

    # T3_INHERIT — herencia
    print("Fetching inheritance (T3_INHERIT)...")
    cursor.execute("SELECT ID_T3, ID_T3_BASE, ID_LEVEL FROM M4RCH_T3_INHERIT;")
    inheritance = defaultdict(list)
    for row in cursor.fetchall():
        inheritance[row.ID_T3].append(row)
    print(f"  -> {sum(len(v) for v in inheritance.values())} relaciones de herencia.")

    # NODES — nodos
    print("Fetching all nodes...")
    cursor.execute("""
        SELECT ID_T3, ID_NODE, ID_TI, POS_NODO, IS_ROOT, N_NODEESP, N_NODEENG,
               NODES_TYPE, IS_VISIBLE, AFFECTS_DB
        FROM M4RCH_NODES
        ORDER BY ID_T3, POS_NODO, ID_NODE
    """)
    nodes = defaultdict(list)
    all_ti_ids = set()
    for row in cursor.fetchall():
        nodes[row.ID_T3].append(row)
        if row.ID_TI:
            all_ti_ids.add(row.ID_TI)
    print(f"  -> {sum(len(v) for v in nodes.values())} nodos encontrados.")

    # TIS — technical instances
    print("Fetching all TIs...")
    cursor.execute("""
        SELECT ID_TI, N_TIESP, N_TIENG, ID_TI_BASE, ID_INHERIT_TYPE,
               ID_READ_OBJECT, ID_WRITE_OBJECT, IS_SYSTEM_TI
        FROM M4RCH_TIS
    """)
    tis = {row.ID_TI: row for row in cursor.fetchall()}
    print(f"  -> {len(tis)} TIs encontradas.")

    # ITEMS — campos/métodos (solo campos clave para el diccionario)
    print("Fetching all items...")
    cursor.execute("""
        SELECT ID_TI, ID_ITEM, ID_ITEM_TYPE, ID_M4_TYPE,
               ID_READ_FIELD, ID_WRITE_FIELD, IS_VISIBLE, IS_PK, ITEM_ORDER,
               N_SYNONYMESP, N_SYNONYMENG
        FROM M4RCH_ITEMS
        ORDER BY ID_TI, ITEM_ORDER, ID_ITEM
    """)
    items = defaultdict(list)
    for row in cursor.fetchall():
        items[row.ID_TI].append(row)
    print(f"  -> {sum(len(v) for v in items.values())} items encontrados.")

    # RULES count — conteo de reglas por TI
    print("Fetching rules count per TI...")
    cursor.execute("""
        SELECT ID_TI, COUNT(*) AS rule_count
        FROM M4RCH_RULES
        GROUP BY ID_TI
    """)
    rules_count = {row.ID_TI: row.rule_count for row in cursor.fetchall()}
    print(f"  -> {sum(rules_count.values())} reglas totales en {len(rules_count)} TIs.")

    return t3s, inheritance, nodes, tis, items, rules_count


def generate_markdown(id_t3, all_meta):
    """Genera el Markdown para un m4object usando los metadatos precargados."""
    t3s, inheritance, all_nodes, tis, all_items, rules_count = all_meta

    t3 = t3s[id_t3]
    desc = t3.N_T3ESP or t3.N_T3ENG or ""
    md = [f"# M4Object: `{id_t3}`\n"]
    md.append(f"**Nombre:** {desc}")
    md.append(f"\n**Categoría:** `{t3.ID_CATEGORY or 'N/A'}` / `{t3.ID_SUBCATEGORY or 'N/A'}`")
    md.append(f"\n**Stream Type:** `{decode(t3.ID_STREAM_TYPE, STREAM_TYPE_MAP) or 'N/A'}`")
    md.append(f"\n**Tipo Ejecución:** `{decode(t3.CS_EXE_TYPE, EXE_TYPE_MAP) or 'N/A'}`")

    flags = []
    if t3.HAVE_SECURITY:
        flags.append("Security")
    if t3.IS_EXTERNAL:
        flags.append("External")
    if flags:
        md.append(f"\n**Flags:** {', '.join(flags)}")

    # --- Herencia ---
    inh = inheritance.get(id_t3, [])
    if inh:
        md.append("\n## Herencia\n")
        md.append("| Canal Base | Nivel |")
        md.append("|---|---|")
        for r in inh:
            safe = safe_filename(r.ID_T3_BASE)
            md.append(f"| [`{r.ID_T3_BASE}`]({safe}.md) | `{r.ID_LEVEL or 'N/A'}` |")

    # --- Nodos ---
    node_list = all_nodes.get(id_t3, [])
    md.append(f"\n## Nodos ({len(node_list)})\n")

    if not node_list:
        md.append("Este canal no tiene nodos definidos.")
    else:
        for node in node_list:
            node_name = node.N_NODEESP or node.N_NODEENG or ""
            root_marker = " (ROOT)" if node.IS_ROOT else ""
            node_type_label = decode(node.NODES_TYPE, NODES_TYPE_MAP) or ""
            md.append(f"### Nodo: `{node.ID_NODE}`{root_marker}\n")
            md.append(f"**Nombre:** {node_name}")
            md.append(f"| Posición | Tipo | Tipo Nodo | Visible | Afecta BD |")
            md.append(f"|---|---|---|---|---|")
            md.append(
                f"| {node.POS_NODO or 'N/A'} | `{node.NODES_TYPE or 'N/A'}` "
                f"| {node_type_label} "
                f"| {'Sí' if node.IS_VISIBLE else 'No'} "
                f"| {'Sí' if node.AFFECTS_DB else 'No'} |"
            )

            # TI del nodo
            if node.ID_TI and node.ID_TI in tis:
                ti = tis[node.ID_TI]
                ti_name = ti.N_TIESP or ti.N_TIENG or ""
                ti_rules = rules_count.get(node.ID_TI, 0)
                ti_items = all_items.get(node.ID_TI, [])

                md.append(f"\n**TI:** `{node.ID_TI}` — {ti_name}")
                if ti.ID_TI_BASE:
                    md.append(f"  - Hereda de: `{ti.ID_TI_BASE}` ({ti.ID_INHERIT_TYPE or 'N/A'})")
                if ti.ID_READ_OBJECT:
                    md.append(f"  - Read Object: `{ti.ID_READ_OBJECT}`")
                if ti.ID_WRITE_OBJECT:
                    md.append(f"  - Write Object: `{ti.ID_WRITE_OBJECT}`")
                md.append(f"  - Reglas: **{ti_rules}**")

                # Items del TI
                if ti_items:
                    md.append(f"\n#### Items ({len(ti_items)})\n")
                    md.append("| Pos | ID Item | Tipo | M4 Type | PK | Visible | Campo Lectura | CS Type | Descripción |")
                    md.append("|---|---|---|---|---|---|---|---|---|")
                    for item in ti_items:
                        item_desc = item.N_SYNONYMESP or item.N_SYNONYMENG or ""
                        is_pk = "Sí" if item.IS_PK else ""
                        is_vis = "Sí" if item.IS_VISIBLE else ""
                        cs_label = decode(item.ID_CSTYPE, ITEM_CSTYPE_MAP) or ""
                        md.append(
                            f"| {item.ITEM_ORDER or ''} | `{item.ID_ITEM}` "
                            f"| `{item.ID_ITEM_TYPE or ''}` | `{item.ID_M4_TYPE or ''}` "
                            f"| {is_pk} | {is_vis} "
                            f"| `{item.ID_READ_FIELD or ''}` | {cs_label} | {item_desc} |"
                        )
            elif node.ID_TI:
                md.append(f"\n**TI:** `{node.ID_TI}` (no encontrada en M4RCH_TIS)")

            md.append("")  # separador entre nodos

    return "\n".join(md)


def build_dictionary():
    """Genera todos los ficheros Markdown del diccionario de m4objects."""
    base_path = os.path.join(project_root, "docs", "02_m4object", "channels")
    os.makedirs(base_path, exist_ok=True)

    try:
        with db_connection() as conn:
            all_meta = fetch_all_metadata(conn)
            t3s = all_meta[0]

            print(f"\nPaso 2: Generando {len(t3s)} ficheros Markdown desde la memoria...")
            index_entries = []

            t3_list = list(t3s.keys())
            for i, id_t3 in enumerate(t3_list):
                markdown_content = generate_markdown(id_t3, all_meta)

                safe_name = safe_filename(id_t3)
                filepath = os.path.join(base_path, f"{safe_name}.md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                t3 = t3s[id_t3]
                desc = t3.N_T3ESP or t3.N_T3ENG or ""
                category = t3.ID_CATEGORY or ""
                stream_label = decode(t3.ID_STREAM_TYPE, STREAM_TYPE_MAP) or ""
                exe_label = decode(t3.CS_EXE_TYPE, EXE_TYPE_MAP) or ""
                index_entries.append(
                    f"| [`{id_t3}`]({safe_name}.md) | {desc} | `{category}` | {stream_label} | {exe_label} |"
                )

                if (i + 1) % 500 == 0 or (i + 1) == len(t3_list):
                    print(f"  ({i+1}/{len(t3_list)}) procesados...")

    except Exception as e:
        print(f"\nError durante la generación: {e}", file=sys.stderr)
        raise

    print("\nPaso 3: Generando el fichero de índice maestro...")
    index_path = os.path.join(base_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Diccionario de M4Objects (Canales)\n\n")
        f.write(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. ")
        f.write(f"Contiene **{len(index_entries)}** canales.\n\n")
        f.write("| ID del Canal | Nombre | Categoría | Stream Type | Modo Ejecución |\n|---|---|---|---|---|\n")
        f.write("\n".join(sorted(index_entries)))
    print(f"-> Creado '{index_path}'")
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    build_dictionary()
