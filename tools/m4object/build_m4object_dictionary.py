# tools/m4object/build_m4object_dictionary.py
"""
Genera una base de conocimiento completa en Markdown de todos los m4objects
(canales) y TIs de PeopleNet, con estructura normalizada.

Consulta las tablas de metadatos M4RCH_* del repositorio y genera:

  docs/02_m4object/
  +-- channels/
  |   +-- _index.md              Indice de canales con estadisticas
  |   +-- <CANAL>.md             Cabecera + herencia + nodos (link a TI) + conectores
  +-- tis/
      +-- _index.md              Resumen por BDL object + tabla plana
      +-- <TI>.md                Definicion TI + items agrupados + conceptos + reglas

Los items viven dentro del fichero de su TI (agrupados por tipo).
Los canales son ligeros: solo metadata, nodos con link a TI, y conectores.
Las TIs incluyen reverse linkage (canales que las usan).

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
    EXE_TYPE_MAP, STREAM_TYPE_MAP, NODES_TYPE_MAP, ITEM_CSTYPE_MAP,
    CONNECTION_TYPE_MAP, decode,
)


# --- Tipo de item (M4RCH_ITEMS.ID_ITEM_TYPE) ---
ITEM_TYPE_MAP = {
    1: "Method",
    2: "Property",
    3: "Field",
    4: "Concept",
}

# Orden y titulo de secciones de items agrupados por tipo
ITEM_TYPE_SECTIONS = {
    3: "Campos (Fields)",
    2: "Propiedades (Properties)",
    1: "Metodos (Methods)",
    4: "Conceptos (Concepts)",
}


# =========================================================================
#  Fase 0: Extraccion masiva de metadatos
# =========================================================================

def fetch_all_metadata(conn):
    """Obtiene todos los metadatos necesarios en consultas masivas."""
    cursor = conn.cursor()

    # T3S -- canales
    print("Fetching all m4objects (T3S)...")
    cursor.execute("""
        SELECT ID_T3, N_T3ESP, N_T3ENG, ID_STREAM_TYPE, ID_CATEGORY,
               ID_SUBCATEGORY, HAVE_SECURITY, IS_EXTERNAL, CS_EXE_TYPE
        FROM M4RCH_T3S
        ORDER BY ID_T3
    """)
    t3s = {row.ID_T3: row for row in cursor.fetchall()}
    print(f"  -> {len(t3s)} canales.")

    # T3_INHERIT -- herencia de canales
    print("Fetching inheritance (T3_INHERIT)...")
    cursor.execute("SELECT ID_T3, ID_T3_BASE, ID_LEVEL FROM M4RCH_T3_INHERIT;")
    inheritance = defaultdict(list)
    for row in cursor.fetchall():
        inheritance[row.ID_T3].append(row)
    print(f"  -> {sum(len(v) for v in inheritance.values())} relaciones de herencia.")

    # NODES -- nodos (vinculo canal -> TI)
    print("Fetching all nodes...")
    cursor.execute("""
        SELECT ID_T3, ID_NODE, ID_TI, POS_NODO, IS_ROOT, N_NODEESP, N_NODEENG,
               NODES_TYPE, IS_VISIBLE, AFFECTS_DB
        FROM M4RCH_NODES
        ORDER BY ID_T3, POS_NODO, ID_NODE
    """)
    nodes = defaultdict(list)
    ti_to_channels = defaultdict(set)  # reverse linkage TI -> canales
    for row in cursor.fetchall():
        nodes[row.ID_T3].append(row)
        if row.ID_TI:
            ti_to_channels[row.ID_TI].add(row.ID_T3)
    print(f"  -> {sum(len(v) for v in nodes.values())} nodos.")

    # TIS -- technical instances
    print("Fetching all TIs...")
    cursor.execute("""
        SELECT ID_TI, N_TIESP, N_TIENG, ID_TI_BASE, ID_INHERIT_TYPE,
               ID_READ_OBJECT, ID_WRITE_OBJECT, IS_SYSTEM_TI
        FROM M4RCH_TIS
    """)
    tis = {row.ID_TI: row for row in cursor.fetchall()}
    print(f"  -> {len(tis)} TIs.")

    # ITEMS -- campos/metodos/propiedades/conceptos
    print("Fetching all items...")
    cursor.execute("""
        SELECT ID_TI, ID_ITEM, ID_ITEM_TYPE, ID_M4_TYPE,
               ID_READ_FIELD, ID_WRITE_FIELD, IS_VISIBLE, IS_PK, ITEM_ORDER,
               N_SYNONYMESP, N_SYNONYMENG, ID_CSTYPE
        FROM M4RCH_ITEMS
        ORDER BY ID_TI, ITEM_ORDER, ID_ITEM
    """)
    items = defaultdict(list)
    for row in cursor.fetchall():
        items[row.ID_TI].append(row)
    print(f"  -> {sum(len(v) for v in items.values())} items.")

    # RULES count -- conteo de reglas por TI
    print("Fetching rules count per TI...")
    cursor.execute("""
        SELECT ID_TI, COUNT(*) AS rule_count
        FROM M4RCH_RULES
        GROUP BY ID_TI
    """)
    rules_count = {row.ID_TI: row.rule_count for row in cursor.fetchall()}
    print(f"  -> {sum(rules_count.values())} reglas en {len(rules_count)} TIs.")

    # T3_CONNTORS -- conectores a nivel de canal
    print("Fetching channel connectors (T3_CONNTORS)...")
    cursor.execute("""
        SELECT ID_T3, ID_TI, ID_NODE, ID_T3_USED, ID_TI_USED, ID_NODE_USED,
               ID_CONNECTION_TYPE, IS_FILTER
        FROM M4RCH_T3_CONNTORS
        ORDER BY ID_T3, ID_TI, ID_NODE
    """)
    t3_connectors = defaultdict(list)
    for row in cursor.fetchall():
        t3_connectors[row.ID_T3].append(row)
    print(f"  -> {sum(len(v) for v in t3_connectors.values())} conectores.")

    # CONCEPTS -- conceptos de nomina
    print("Fetching payroll concepts (CONCEPTS)...")
    cursor.execute("""
        SELECT ID_TI, ID_ITEM, ID_TRANS_ITEMESP, ID_TRANS_ITEMENG,
               CLASSIFICATION, ID_CONCEPT_TYPE
        FROM M4RCH_CONCEPTS
        ORDER BY ID_TI, ID_ITEM
    """)
    concepts = defaultdict(list)
    for row in cursor.fetchall():
        concepts[row.ID_TI].append(row)
    print(f"  -> {sum(len(v) for v in concepts.values())} conceptos de nomina.")

    return {
        "t3s": t3s,
        "inheritance": inheritance,
        "nodes": nodes,
        "tis": tis,
        "items": items,
        "rules_count": rules_count,
        "t3_connectors": t3_connectors,
        "concepts": concepts,
        "ti_to_channels": ti_to_channels,
    }


# =========================================================================
#  Fase 1: Generar ficheros de TI
# =========================================================================

def generate_ti_markdown(id_ti, meta):
    """Genera el Markdown para una TI con items, conceptos y reverse linkage."""
    tis = meta["tis"]
    all_items = meta["items"]
    rules_count = meta["rules_count"]
    concepts = meta["concepts"]
    ti_to_channels = meta["ti_to_channels"]
    t3s = meta["t3s"]

    ti = tis[id_ti]
    ti_name = ti.N_TIESP or ti.N_TIENG or ""
    ti_items = all_items.get(id_ti, [])
    ti_rules = rules_count.get(id_ti, 0)
    ti_concepts = concepts.get(id_ti, [])
    channels_using = sorted(ti_to_channels.get(id_ti, []))

    # Contar items por tipo
    type_counts = defaultdict(int)
    for item in ti_items:
        itype = int(item.ID_ITEM_TYPE) if item.ID_ITEM_TYPE is not None else 0
        type_counts[itype] += 1

    # --- Cabecera ---
    md = [f"# TI: `{id_ti}`\n"]
    md.append(f"**Nombre:** {ti_name}")

    if ti.ID_TI_BASE:
        safe_base = safe_filename(ti.ID_TI_BASE)
        md.append(f"\n**Hereda de:** [`{ti.ID_TI_BASE}`]({safe_base}.md)"
                  f" ({ti.ID_INHERIT_TYPE or 'N/A'})")
    if ti.ID_READ_OBJECT:
        md.append(f"\n**Read Object:** `{ti.ID_READ_OBJECT}`")
    if ti.ID_WRITE_OBJECT:
        md.append(f"\n**Write Object:** `{ti.ID_WRITE_OBJECT}`")
    if ti.IS_SYSTEM_TI:
        md.append("\n**Sistema:** Si")

    # Resumen
    parts = []
    parts.append(f"{len(ti_items)} items")
    for type_id in (3, 2, 1, 4):
        label = ITEM_TYPE_MAP.get(type_id, f"tipo {type_id}")
        cnt = type_counts.get(type_id, 0)
        if cnt > 0:
            parts.append(f"{cnt} {label.lower()}s")
    parts.append(f"{ti_rules} reglas")
    if ti_concepts:
        parts.append(f"{len(ti_concepts)} conceptos nomina")
    md.append(f"\n**Resumen:** {', '.join(parts)}")

    # --- Canales que usan esta TI (reverse linkage) ---
    if channels_using:
        md.append(f"\n## Canales que usan esta TI ({len(channels_using)})\n")
        # Si son pocos, lista inline; si son muchos, tabla
        if len(channels_using) <= 10:
            for ch_id in channels_using:
                safe_ch = safe_filename(ch_id)
                ch_name = ""
                if ch_id in t3s:
                    ch_name = t3s[ch_id].N_T3ESP or t3s[ch_id].N_T3ENG or ""
                    if ch_name:
                        ch_name = f" — {ch_name}"
                md.append(f"- [`{ch_id}`](../channels/{safe_ch}.md){ch_name}")
        else:
            md.append("| Canal | Nombre |")
            md.append("|---|---|")
            for ch_id in channels_using:
                safe_ch = safe_filename(ch_id)
                ch_name = ""
                if ch_id in t3s:
                    ch_name = t3s[ch_id].N_T3ESP or t3s[ch_id].N_T3ENG or ""
                md.append(f"| [`{ch_id}`](../channels/{safe_ch}.md) | {ch_name} |")
    else:
        md.append("\n## Canales que usan esta TI (0)\n")
        md.append("Esta TI no esta referenciada por ningun canal (huerfana).")

    # --- Items agrupados por tipo ---
    if ti_items:
        items_by_type = defaultdict(list)
        for item in ti_items:
            itype = int(item.ID_ITEM_TYPE) if item.ID_ITEM_TYPE is not None else 0
            items_by_type[itype].append(item)

        for type_id, section_title in ITEM_TYPE_SECTIONS.items():
            type_items = items_by_type.get(type_id, [])
            if not type_items:
                continue

            md.append(f"\n## {section_title} ({len(type_items)})\n")

            if type_id == 1:
                # Metodos: tabla simplificada
                md.append("| Pos | ID Item | CS Type | Descripcion |")
                md.append("|---|---|---|---|")
                for item in type_items:
                    item_desc = item.N_SYNONYMESP or item.N_SYNONYMENG or ""
                    cs_label = decode(item.ID_CSTYPE, ITEM_CSTYPE_MAP) or ""
                    md.append(
                        f"| {item.ITEM_ORDER or ''} | `{item.ID_ITEM}` "
                        f"| {cs_label} | {item_desc} |"
                    )
            else:
                # Campos, propiedades, conceptos: tabla completa
                md.append("| Pos | ID Item | M4 Type | PK | Visible "
                          "| Campo Lectura | CS Type | Descripcion |")
                md.append("|---|---|---|---|---|---|---|---|")
                for item in type_items:
                    item_desc = item.N_SYNONYMESP or item.N_SYNONYMENG or ""
                    is_pk = "Si" if item.IS_PK else ""
                    is_vis = "Si" if item.IS_VISIBLE else ""
                    cs_label = decode(item.ID_CSTYPE, ITEM_CSTYPE_MAP) or ""
                    md.append(
                        f"| {item.ITEM_ORDER or ''} | `{item.ID_ITEM}` "
                        f"| `{item.ID_M4_TYPE or ''}` "
                        f"| {is_pk} | {is_vis} "
                        f"| `{item.ID_READ_FIELD or ''}` | {cs_label} "
                        f"| {item_desc} |"
                    )

        # Items con tipo no reconocido
        other_types = set(items_by_type.keys()) - set(ITEM_TYPE_SECTIONS.keys())
        for otype in sorted(other_types):
            other_items = items_by_type[otype]
            type_label = ITEM_TYPE_MAP.get(otype, f"Tipo {otype}")
            md.append(f"\n## {type_label} ({len(other_items)})\n")
            md.append("| Pos | ID Item | M4 Type | Descripcion |")
            md.append("|---|---|---|---|")
            for item in other_items:
                item_desc = item.N_SYNONYMESP or item.N_SYNONYMENG or ""
                md.append(
                    f"| {item.ITEM_ORDER or ''} | `{item.ID_ITEM}` "
                    f"| `{item.ID_M4_TYPE or ''}` | {item_desc} |"
                )

    # --- Conceptos de nomina ---
    if ti_concepts:
        md.append(f"\n## Conceptos de Nomina ({len(ti_concepts)})\n")
        md.append("| ID Concepto | Tipo | Clasificacion | Nombre |")
        md.append("|---|---|---|---|")
        for c in ti_concepts:
            c_name = c.ID_TRANS_ITEMESP or c.ID_TRANS_ITEMENG or ""
            c_type = c.ID_CONCEPT_TYPE or ""
            c_class = c.CLASSIFICATION or ""
            md.append(f"| `{c.ID_ITEM}` | `{c_type}` | `{c_class}` | {c_name} |")

    # --- Conteo de reglas ---
    md.append(f"\n## Reglas LN4\n")
    md.append(f"Esta TI tiene **{ti_rules}** reglas definidas.")

    return "\n".join(md)


def build_tis(meta, tis_path):
    """Genera todos los ficheros de TI."""
    tis = meta["tis"]
    ti_list = sorted(tis.keys())

    print(f"\nFase 1: Generando {len(ti_list)} ficheros de TI...")
    for i, id_ti in enumerate(ti_list):
        content = generate_ti_markdown(id_ti, meta)
        safe_name = safe_filename(id_ti)
        filepath = os.path.join(tis_path, f"{safe_name}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        if (i + 1) % 2000 == 0 or (i + 1) == len(ti_list):
            print(f"  ({i+1}/{len(ti_list)}) TIs procesadas...")


# =========================================================================
#  Fase 2: Generar ficheros de Canal (ligeros)
# =========================================================================

def generate_channel_markdown(id_t3, meta):
    """Genera el Markdown ligero para un canal (sin items, con links a TIs)."""
    t3s = meta["t3s"]
    inheritance = meta["inheritance"]
    all_nodes = meta["nodes"]
    tis = meta["tis"]
    all_items = meta["items"]
    rules_count = meta["rules_count"]
    t3_connectors = meta["t3_connectors"]

    t3 = t3s[id_t3]
    desc = t3.N_T3ESP or t3.N_T3ENG or ""
    node_list = all_nodes.get(id_t3, [])
    conn_list = t3_connectors.get(id_t3, [])

    # Estadisticas del canal
    total_items = 0
    total_rules = 0
    ti_ids = set()
    for node in node_list:
        if node.ID_TI and node.ID_TI in tis:
            ti_ids.add(node.ID_TI)
            total_items += len(all_items.get(node.ID_TI, []))
            total_rules += rules_count.get(node.ID_TI, 0)

    # --- Cabecera ---
    md = [f"# M4Object: `{id_t3}`\n"]
    md.append(f"**Nombre:** {desc}")
    md.append(f"\n**Categoria:** `{t3.ID_CATEGORY or 'N/A'}` / `{t3.ID_SUBCATEGORY or 'N/A'}`")
    md.append(f"\n**Stream Type:** `{decode(t3.ID_STREAM_TYPE, STREAM_TYPE_MAP) or 'N/A'}`")
    md.append(f"\n**Tipo Ejecucion:** `{decode(t3.CS_EXE_TYPE, EXE_TYPE_MAP) or 'N/A'}`")

    flags = []
    if t3.HAVE_SECURITY:
        flags.append("Security")
    if t3.IS_EXTERNAL:
        flags.append("External")
    if flags:
        md.append(f"\n**Flags:** {', '.join(flags)}")

    md.append(f"\n**Resumen:** {len(node_list)} nodos, {len(ti_ids)} TIs, "
              f"{total_items} items, {total_rules} reglas, "
              f"{len(conn_list)} conectores")

    # --- Herencia ---
    inh = inheritance.get(id_t3, [])
    if inh:
        md.append("\n## Herencia\n")
        md.append("| Canal Base | Nivel |")
        md.append("|---|---|")
        for r in inh:
            safe = safe_filename(r.ID_T3_BASE)
            md.append(f"| [`{r.ID_T3_BASE}`]({safe}.md) | `{r.ID_LEVEL or 'N/A'}` |")

    # --- Nodos (con link a TI) ---
    md.append(f"\n## Nodos ({len(node_list)})\n")

    if not node_list:
        md.append("Este canal no tiene nodos definidos.")
    else:
        md.append("| Pos | Nodo | Root | Tipo Nodo | TI | Visible | Afecta BD |")
        md.append("|---|---|---|---|---|---|---|")
        for node in node_list:
            root = "Si" if node.IS_ROOT else ""
            node_type_label = decode(node.NODES_TYPE, NODES_TYPE_MAP) or ""
            vis = "Si" if node.IS_VISIBLE else "No"
            adb = "Si" if node.AFFECTS_DB else "No"

            # Link a la TI
            if node.ID_TI and node.ID_TI in tis:
                safe_ti = safe_filename(node.ID_TI)
                ti_name = tis[node.ID_TI].N_TIESP or tis[node.ID_TI].N_TIENG or ""
                ti_cell = f"[`{node.ID_TI}`](../tis/{safe_ti}.md)"
                if ti_name:
                    ti_cell += f" — {ti_name}"
            elif node.ID_TI:
                ti_cell = f"`{node.ID_TI}` (no encontrada)"
            else:
                ti_cell = ""

            md.append(
                f"| {node.POS_NODO or ''} | `{node.ID_NODE}` "
                f"| {root} | {node_type_label} "
                f"| {ti_cell} | {vis} | {adb} |"
            )

    # --- Conectores ---
    if conn_list:
        md.append(f"\n## Conectores ({len(conn_list)})\n")
        md.append("| TI Origen | Nodo Origen | Canal Destino | TI Destino "
                  "| Nodo Destino | Tipo | Filtro |")
        md.append("|---|---|---|---|---|---|---|")
        for c in conn_list:
            is_filter = "Si" if c.IS_FILTER else "No"
            conn_type = decode(c.ID_CONNECTION_TYPE, CONNECTION_TYPE_MAP) or ""
            t3_used = ""
            if c.ID_T3_USED:
                safe_t3u = safe_filename(c.ID_T3_USED)
                t3_used = f"[`{c.ID_T3_USED}`]({safe_t3u}.md)"
            ti_used = f"`{c.ID_TI_USED}`" if c.ID_TI_USED else ""
            node_used = f"`{c.ID_NODE_USED}`" if c.ID_NODE_USED else ""
            md.append(
                f"| `{c.ID_TI or ''}` | `{c.ID_NODE or ''}` "
                f"| {t3_used} | {ti_used} | {node_used} "
                f"| {conn_type} | {is_filter} |"
            )

    return "\n".join(md)


def build_channels(meta, channels_path):
    """Genera todos los ficheros de canal (ligeros)."""
    t3s = meta["t3s"]
    t3_list = sorted(t3s.keys())

    print(f"\nFase 2: Generando {len(t3_list)} ficheros de canal (ligeros)...")
    for i, id_t3 in enumerate(t3_list):
        content = generate_channel_markdown(id_t3, meta)
        safe_name = safe_filename(id_t3)
        filepath = os.path.join(channels_path, f"{safe_name}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        if (i + 1) % 1000 == 0 or (i + 1) == len(t3_list):
            print(f"  ({i+1}/{len(t3_list)}) canales procesados...")


# =========================================================================
#  Fase 3: Generar indices
# =========================================================================

def build_channel_index(meta, channels_path):
    """Genera el indice maestro de canales."""
    t3s = meta["t3s"]
    all_nodes = meta["nodes"]
    tis = meta["tis"]
    all_items = meta["items"]
    rules_count = meta["rules_count"]
    t3_connectors = meta["t3_connectors"]

    # Totales globales
    total_nodes = sum(len(v) for v in all_nodes.values())
    total_items_count = sum(len(v) for v in all_items.values())
    total_rules_count = sum(rules_count.values())
    total_connectors = sum(len(v) for v in t3_connectors.values())

    by_category = defaultdict(list)
    for id_t3, t3 in sorted(t3s.items()):
        cat = t3.ID_CATEGORY or "SIN_CATEGORIA"
        by_category[cat].append((id_t3, t3))

    lines = []
    lines.append("# Diccionario de M4Objects (Canales)\n")
    lines.append(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
                 f"Contiene **{len(t3s)}** canales en **{len(by_category)}** categorias.\n")
    lines.append("Ver tambien: [Indice de TIs](../tis/_index.md) | "
                 "[Vision General](../m4objects_overview.md)\n")

    # Estadisticas
    lines.append("## Estadisticas\n")
    lines.append("| Metrica | Total |")
    lines.append("|---|---|")
    lines.append(f"| Canales | {len(t3s)} |")
    lines.append(f"| Nodos | {total_nodes} |")
    lines.append(f"| TIs | {len(tis)} |")
    lines.append(f"| Items | {total_items_count} |")
    lines.append(f"| Reglas LN4 | {total_rules_count} |")
    lines.append(f"| Conectores | {total_connectors} |")

    # Por categoria
    lines.append("\n## Canales por Categoria\n")
    lines.append("| Categoria | Canales |")
    lines.append("|---|---|")
    for cat in sorted(by_category.keys()):
        lines.append(f"| `{cat}` | {len(by_category[cat])} |")

    # Tabla completa
    lines.append("\n## Todos los Canales\n")
    lines.append("| ID del Canal | Nombre | Categoria | Stream Type "
                 "| Modo Ejecucion | Nodos | Items | Reglas |")
    lines.append("|---|---|---|---|---|---|---|---|")

    for id_t3, t3 in sorted(t3s.items()):
        safe = safe_filename(id_t3)
        desc = t3.N_T3ESP or t3.N_T3ENG or ""
        category = t3.ID_CATEGORY or ""
        stream_label = decode(t3.ID_STREAM_TYPE, STREAM_TYPE_MAP) or ""
        exe_label = decode(t3.CS_EXE_TYPE, EXE_TYPE_MAP) or ""

        n_nodes = len(all_nodes.get(id_t3, []))
        n_items = 0
        n_rules = 0
        for node in all_nodes.get(id_t3, []):
            if node.ID_TI:
                n_items += len(all_items.get(node.ID_TI, []))
                n_rules += rules_count.get(node.ID_TI, 0)

        lines.append(
            f"| [`{id_t3}`]({safe}.md) | {desc} | `{category}` "
            f"| {stream_label} | {exe_label} "
            f"| {n_nodes} | {n_items} | {n_rules} |"
        )

    index_path = os.path.join(channels_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  -> Indice de canales: {index_path}")


def build_ti_index(meta, tis_path):
    """Genera el indice de TIs con resumen por BDL object + tabla plana."""
    tis = meta["tis"]
    all_items = meta["items"]
    rules_count = meta["rules_count"]
    ti_to_channels = meta["ti_to_channels"]

    # Agrupar por Read Object
    by_read_object = defaultdict(list)
    for id_ti, ti in sorted(tis.items()):
        ro = ti.ID_READ_OBJECT or "SIN_OBJETO"
        by_read_object[ro].append((id_ti, ti))

    # Contar huerfanas
    orphan_count = sum(1 for id_ti in tis if id_ti not in ti_to_channels)

    lines = []
    lines.append("# Diccionario de TIs (Technical Instances)\n")
    lines.append(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
                 f"Contiene **{len(tis)}** TIs vinculadas a "
                 f"**{len(by_read_object)}** objetos BDL.\n")
    lines.append("Ver tambien: [Indice de Canales](../channels/_index.md) | "
                 "[Vision General](../m4objects_overview.md)\n")

    # Estadisticas
    lines.append("## Estadisticas\n")
    lines.append("| Metrica | Total |")
    lines.append("|---|---|")
    lines.append(f"| TIs | {len(tis)} |")
    lines.append(f"| Objetos BDL (Read) | {len(by_read_object)} |")
    lines.append(f"| TIs compartidas (>1 canal) | "
                 f"{sum(1 for v in ti_to_channels.values() if len(v) > 1)} |")
    lines.append(f"| TIs huerfanas (sin canal) | {orphan_count} |")
    lines.append(f"| Items totales | {sum(len(v) for v in all_items.values())} |")
    lines.append(f"| Reglas totales | {sum(rules_count.values())} |")

    # Resumen por Read Object (top 50 por cantidad de TIs)
    lines.append("\n## TIs por Objeto BDL (Read Object)\n")
    lines.append("Top 50 objetos con mas TIs asociadas.\n")
    lines.append("| Read Object | TIs |")
    lines.append("|---|---|")
    sorted_objects = sorted(by_read_object.items(), key=lambda x: -len(x[1]))
    for ro, ti_list in sorted_objects[:50]:
        lines.append(f"| `{ro}` | {len(ti_list)} |")
    if len(sorted_objects) > 50:
        remaining = sum(len(v) for _, v in sorted_objects[50:])
        lines.append(f"| *(otros {len(sorted_objects) - 50} objetos)* | {remaining} |")

    # Tabla plana completa
    lines.append("\n## Todas las TIs\n")
    lines.append("| ID TI | Nombre | Read Object | Write Object "
                 "| Items | Reglas | Canales |")
    lines.append("|---|---|---|---|---|---|---|")

    for id_ti, ti in sorted(tis.items()):
        safe = safe_filename(id_ti)
        ti_name = ti.N_TIESP or ti.N_TIENG or ""
        ro = ti.ID_READ_OBJECT or ""
        wo = ti.ID_WRITE_OBJECT or ""
        n_items = len(all_items.get(id_ti, []))
        n_rules = rules_count.get(id_ti, 0)
        n_channels = len(ti_to_channels.get(id_ti, []))

        lines.append(
            f"| [`{id_ti}`]({safe}.md) | {ti_name} "
            f"| `{ro}` | `{wo}` "
            f"| {n_items} | {n_rules} | {n_channels} |"
        )

    index_path = os.path.join(tis_path, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  -> Indice de TIs: {index_path}")


# =========================================================================
#  Orquestacion principal
# =========================================================================

def build_dictionary():
    """Genera la documentacion completa de m4objects y TIs."""
    base_path = os.path.join(project_root, "docs", "02_m4object")
    channels_path = os.path.join(base_path, "channels")
    tis_path = os.path.join(base_path, "tis")
    os.makedirs(channels_path, exist_ok=True)
    os.makedirs(tis_path, exist_ok=True)

    try:
        with db_connection() as conn:
            meta = fetch_all_metadata(conn)

            # Fase 1: TIs
            build_tis(meta, tis_path)

            # Fase 2: Canales ligeros
            build_channels(meta, channels_path)

            # Fase 3: Indices
            print("\nFase 3: Generando indices...")
            build_channel_index(meta, channels_path)
            build_ti_index(meta, tis_path)

    except Exception as e:
        print(f"\nError durante la generacion: {e}", file=sys.stderr)
        raise

    print("\nProceso completado!")
    print(f"  Canales: {channels_path}")
    print(f"  TIs:     {tis_path}")


if __name__ == "__main__":
    build_dictionary()
