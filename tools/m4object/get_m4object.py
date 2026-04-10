# tools/m4object/get_m4object.py
"""
Obtiene la definición completa de un m4object (canal) de PeopleNet.

Consulta las tablas de metadatos M4RCH_* para extraer la estructura
jerárquica de un m4object:

    T3 (canal)
    ├─ Herencia (T3_INHERIT)
    ├─ Conectores (T3_CONNTORS)
    └─ Nodos (NODES)
         └─ TI (Technical Instance)
              ├─ Items (campos/métodos)
              │    └─ Argumentos de métodos (ITEM_ARGS) — siempre incluidos
              ├─ Conceptos (CONCEPTS) — siempre incluidos
              └─ Reglas (RULES)
                   └─ Código fuente LN4 (RULES3) — con --include-rules

Uso:
    python -m tools.m4object.get_m4object "ABC"
    python -m tools.m4object.get_m4object "SCO_MNG_DEV_PRODUCT" --include-rules
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection
from tools.m4object.m4object_maps import (
    EXE_TYPE_MAP, STREAM_TYPE_MAP, ITEM_CSTYPE_MAP, NODES_TYPE_MAP, decode,
)


def _fetch_t3_header(cursor, id_t3):
    """Obtiene la cabecera del canal (M4RCH_T3S)."""
    cursor.execute("""
        SELECT
            ID_T3, N_T3ESP, N_T3ENG, ID_STREAM_TYPE, ID_CATEGORY,
            ID_SUBCATEGORY, HAVE_SECURITY, IS_CACHEABLE, IS_EXTERNAL,
            IS_SEPARABLE, CS_EXE_TYPE, CREATION_TYPE, ID_SERVICE,
            ID_ORG_TYPE, OWNER_FLAG, DT_CREATE, DT_LAST_UPDATE
        FROM M4RCH_T3S
        WHERE ID_T3 = ?
    """, id_t3)
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id_t3": row.ID_T3,
        "name_esp": row.N_T3ESP,
        "name_eng": row.N_T3ENG,
        "stream_type": decode(row.ID_STREAM_TYPE, STREAM_TYPE_MAP),
        "stream_type_id": row.ID_STREAM_TYPE,
        "category": row.ID_CATEGORY,
        "subcategory": row.ID_SUBCATEGORY,
        "has_security": bool(row.HAVE_SECURITY) if row.HAVE_SECURITY is not None else None,
        "is_cacheable": bool(row.IS_CACHEABLE) if row.IS_CACHEABLE is not None else None,
        "is_external": bool(row.IS_EXTERNAL) if row.IS_EXTERNAL is not None else None,
        "is_separable": bool(row.IS_SEPARABLE) if row.IS_SEPARABLE is not None else None,
        "exe_type": decode(row.CS_EXE_TYPE, EXE_TYPE_MAP),
        "exe_type_id": row.CS_EXE_TYPE,
        "creation_type": row.CREATION_TYPE,
        "service": row.ID_SERVICE,
        "org_type": row.ID_ORG_TYPE,
        "owner_flag": row.OWNER_FLAG,
        "created": row.DT_CREATE,
        "last_updated": row.DT_LAST_UPDATE,
    }


def _fetch_t3_comments(cursor, id_t3):
    """Obtiene los comentarios multilingüe del canal (T3S1..T3S7)."""
    comments = {}
    lang_tables = {
        "ESP": "M4RCH_T3S1",
        "ENG": "M4RCH_T3S2",
        "FRA": "M4RCH_T3S3",
        "GER": "M4RCH_T3S4",
        "ITA": "M4RCH_T3S5",
        "BRA": "M4RCH_T3S6",
        "GEN": "M4RCH_T3S7",
    }
    for lang, table in lang_tables.items():
        try:
            cursor.execute(f"SELECT COMMENT_T3 FROM {table} WHERE ID_T3 = ?", id_t3)
            row = cursor.fetchone()
            if row and row.COMMENT_T3:
                comments[lang] = row.COMMENT_T3.strip()
        except Exception:
            pass  # Tabla puede no existir o no tener datos
    return comments if comments else None


def _fetch_inheritance(cursor, id_t3):
    """Obtiene la herencia del canal (M4RCH_T3_INHERIT)."""
    cursor.execute("""
        SELECT ID_T3_BASE, ID_LEVEL
        FROM M4RCH_T3_INHERIT
        WHERE ID_T3 = ?
        ORDER BY ID_T3_BASE
    """, id_t3)
    rows = cursor.fetchall()
    return [{"base_t3": r.ID_T3_BASE, "level": r.ID_LEVEL} for r in rows]


def _fetch_connectors(cursor, id_t3):
    """Obtiene los conectores del canal (M4RCH_T3_CONNTORS)."""
    cursor.execute("""
        SELECT
            ID_TI, ID_NODE, ID_T3_USED, ID_TI_USED,
            ID_NODE_USED, ID_CONNECTION_TYPE, IS_FILTER,
            ID_RELATION_TYPE
        FROM M4RCH_T3_CONNTORS
        WHERE ID_T3 = ?
        ORDER BY ID_NODE
    """, id_t3)
    rows = cursor.fetchall()
    return [{
        "ti": r.ID_TI,
        "node": r.ID_NODE,
        "t3_used": r.ID_T3_USED,
        "ti_used": r.ID_TI_USED,
        "node_used": r.ID_NODE_USED,
        "connection_type": r.ID_CONNECTION_TYPE,
        "is_filter": bool(r.IS_FILTER) if r.IS_FILTER is not None else None,
        "relation_type": r.ID_RELATION_TYPE,
    } for r in rows]


def _fetch_nodes_with_tis(cursor, id_t3):
    """Obtiene los nodos y sus TIs (M4RCH_NODES + M4RCH_TIS)."""
    cursor.execute("""
        SELECT
            n.ID_NODE, n.ID_TI, n.POS_NODO, n.IS_ROOT, n.AUTOLOAD,
            n.UNIQUE_ROW, n.NUM_ROWS, n.N_NODEESP, n.N_NODEENG,
            n.NODES_TYPE, n.IS_VISIBLE, n.AFFECTS_DB,
            n.ID_DMD, n.ID_RSM, n.DYN_FILTER,
            ti.N_TIESP, ti.N_TIENG, ti.ID_TI_BASE, ti.ID_INHERIT_TYPE,
            ti.ID_READ_OBJECT, ti.ID_WRITE_OBJECT,
            ti.ID_READ_SENTENCE, ti.ID_WRITE_SENTENCE,
            ti.IS_SYSTEM_TI, ti.GENERATE_SQL
        FROM M4RCH_NODES n
        LEFT JOIN M4RCH_TIS ti ON n.ID_TI = ti.ID_TI
        WHERE n.ID_T3 = ?
        ORDER BY n.POS_NODO, n.ID_NODE
    """, id_t3)
    rows = cursor.fetchall()

    nodes = []
    for r in rows:
        node = {
            "id_node": r.ID_NODE,
            "position": r.POS_NODO,
            "name_esp": r.N_NODEESP,
            "name_eng": r.N_NODEENG,
            "is_root": bool(r.IS_ROOT) if r.IS_ROOT is not None else None,
            "autoload": bool(r.AUTOLOAD) if r.AUTOLOAD is not None else None,
            "unique_row": bool(r.UNIQUE_ROW) if r.UNIQUE_ROW is not None else None,
            "num_rows": r.NUM_ROWS,
            "node_type": decode(r.NODES_TYPE, NODES_TYPE_MAP),
            "node_type_id": r.NODES_TYPE,
            "is_visible": bool(r.IS_VISIBLE) if r.IS_VISIBLE is not None else None,
            "affects_db": bool(r.AFFECTS_DB) if r.AFFECTS_DB is not None else None,
            "dmd": r.ID_DMD,
            "rsm": r.ID_RSM,
            "dyn_filter": r.DYN_FILTER,
            "ti": None,
        }

        if r.ID_TI:
            node["ti"] = {
                "id_ti": r.ID_TI,
                "name_esp": r.N_TIESP,
                "name_eng": r.N_TIENG,
                "base_ti": r.ID_TI_BASE,
                "inherit_type": r.ID_INHERIT_TYPE,
                "read_object": r.ID_READ_OBJECT,
                "write_object": r.ID_WRITE_OBJECT,
                "read_sentence": r.ID_READ_SENTENCE,
                "write_sentence": r.ID_WRITE_SENTENCE,
                "is_system": bool(r.IS_SYSTEM_TI) if r.IS_SYSTEM_TI is not None else None,
                "generate_sql": bool(r.GENERATE_SQL) if r.GENERATE_SQL is not None else None,
                "items": [],
                "rules_count": 0,
            }

        nodes.append(node)
    return nodes


def _fetch_items_for_tis(cursor, ti_ids):
    """Obtiene los items para un conjunto de TIs (M4RCH_ITEMS).

    Devuelve un dict {id_ti: [items]}.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    cursor.execute(f"""
        SELECT
            ID_TI, ID_ITEM, ID_ITEM_TYPE, ID_M4_TYPE,
            ID_READ_OBJECT, ID_WRITE_OBJECT,
            ID_READ_FIELD, ID_WRITE_FIELD,
            IS_VISIBLE, IS_PK, ITEM_ORDER,
            N_SYNONYMESP, N_SYNONYMENG,
            PREC, SCALE, ID_INTERNAL_TYPE,
            ID_CSTYPE, N_ITEM
        FROM M4RCH_ITEMS
        WHERE ID_TI IN ({placeholders})
        ORDER BY ID_TI, ITEM_ORDER, ID_ITEM
    """, *ti_ids)
    rows = cursor.fetchall()

    items_by_ti = {}
    for r in rows:
        item = {
            "id_item": r.ID_ITEM,
            "item_type": r.ID_ITEM_TYPE,
            "m4_type": r.ID_M4_TYPE,
            "read_object": r.ID_READ_OBJECT,
            "write_object": r.ID_WRITE_OBJECT,
            "read_field": r.ID_READ_FIELD,
            "write_field": r.ID_WRITE_FIELD,
            "is_visible": bool(r.IS_VISIBLE) if r.IS_VISIBLE is not None else None,
            "is_pk": bool(r.IS_PK) if r.IS_PK is not None else None,
            "position": r.ITEM_ORDER,
            "name_esp": r.N_SYNONYMESP,
            "name_eng": r.N_SYNONYMENG,
            "precision": r.PREC,
            "scale": r.SCALE,
            "internal_type": r.ID_INTERNAL_TYPE,
            "cs_type": decode(r.ID_CSTYPE, ITEM_CSTYPE_MAP),
            "cs_type_id": r.ID_CSTYPE,
            "item_name": r.N_ITEM,
        }
        items_by_ti.setdefault(r.ID_TI, []).append(item)
    return items_by_ti


def _fetch_rules_count_for_tis(cursor, ti_ids):
    """Obtiene el conteo de reglas por TI (M4RCH_RULES).

    Devuelve un dict {id_ti: count}.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    cursor.execute(f"""
        SELECT ID_TI, COUNT(*) AS rule_count
        FROM M4RCH_RULES
        WHERE ID_TI IN ({placeholders})
        GROUP BY ID_TI
    """, *ti_ids)
    rows = cursor.fetchall()
    return {r.ID_TI: r.rule_count for r in rows}


def _fetch_rules_summary(cursor, ti_ids):
    """Obtiene un resumen de las reglas por TI+ITEM (M4RCH_RULES).

    Solo se usa con --include-rules. Devuelve dict {id_ti: [{item, rule, ...}]}.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    cursor.execute(f"""
        SELECT
            r.ID_TI, r.ID_ITEM, r.ID_RULE, r.DT_START,
            r.ID_CODE_TYPE, r.ID_PRIORITY, r.RULE_ORDER,
            r.IS_METARULE, r.IS_EVENT_RULE
        FROM M4RCH_RULES r
        WHERE r.ID_TI IN ({placeholders})
        ORDER BY r.ID_TI, r.ID_ITEM, r.RULE_ORDER
    """, *ti_ids)
    rows = cursor.fetchall()

    rules_by_ti = {}
    for r in rows:
        rule = {
            "id_item": r.ID_ITEM,
            "id_rule": r.ID_RULE,
            "start_date": r.DT_START,
            "code_type": r.ID_CODE_TYPE,
            "priority": r.ID_PRIORITY,
            "rule_order": r.RULE_ORDER,
            "is_metarule": bool(r.IS_METARULE) if r.IS_METARULE is not None else None,
            "is_event_rule": bool(r.IS_EVENT_RULE) if r.IS_EVENT_RULE is not None else None,
        }
        rules_by_ti.setdefault(r.ID_TI, []).append(rule)
    return rules_by_ti


def _fetch_item_args_for_tis(cursor, ti_ids):
    """Obtiene los argumentos de métodos para un conjunto de TIs (M4RCH_ITEM_ARGS).

    Solo aplica a items de tipo 3 (Method). Devuelve un dict
    {(id_ti, id_item): [args]}.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    cursor.execute(f"""
        SELECT
            ID_TI, ID_ITEM, ID_ARGUMENT, POSITION,
            ID_M4_TYPE, ID_ARGUMENT_TYPE
        FROM M4RCH_ITEM_ARGS
        WHERE ID_TI IN ({placeholders})
        ORDER BY ID_TI, ID_ITEM, POSITION
    """, *ti_ids)
    rows = cursor.fetchall()

    args_by_key = {}
    for r in rows:
        arg = {
            "id_argument": r.ID_ARGUMENT,
            "position": r.POSITION,
            "m4_type": r.ID_M4_TYPE,
            "argument_type": r.ID_ARGUMENT_TYPE,
            "is_output": r.ID_ARGUMENT_TYPE == 2,
        }
        args_by_key.setdefault((r.ID_TI, r.ID_ITEM), []).append(arg)
    return args_by_key


def _fetch_rules_source_for_tis(cursor, ti_ids):
    """Obtiene el código fuente LN4 de las reglas (M4RCH_RULES3).

    Solo se usa con --include-rules. Devuelve un dict
    {(id_ti, id_item): source_code}. El código se trunca a 3000 chars.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    cursor.execute(f"""
        SELECT ID_TI, ID_ITEM, SOURCE_CODE
        FROM M4RCH_RULES3
        WHERE ID_TI IN ({placeholders})
          AND SOURCE_CODE IS NOT NULL
        ORDER BY ID_TI, ID_ITEM
    """, *ti_ids)
    rows = cursor.fetchall()

    source_by_key = {}
    for r in rows:
        source = r.SOURCE_CODE
        if source and len(source) > 3000:
            source = source[:3000] + "\n... [truncated]"
        source_by_key[(r.ID_TI, r.ID_ITEM)] = source
    return source_by_key


def _fetch_concepts_for_tis(cursor, ti_ids):
    """Obtiene los conceptos de nómina por TI (M4RCH_CONCEPTS).

    Devuelve un dict {id_ti: [concepts]}.
    """
    if not ti_ids:
        return {}

    placeholders = ",".join(["?"] * len(ti_ids))
    try:
        cursor.execute(f"""
            SELECT
                ID_TI, ID_CONCEPT, ID_ITEM, CONCEPT_TYPE,
                CONCEPT_SCOPE, IS_SYSTEM
            FROM M4RCH_CONCEPTS
            WHERE ID_TI IN ({placeholders})
            ORDER BY ID_TI, ID_CONCEPT
        """, *ti_ids)
        rows = cursor.fetchall()
    except Exception:
        # Tabla puede no existir en todas las instalaciones
        return {}

    concepts_by_ti = {}
    for r in rows:
        concept = {
            "id_concept": r.ID_CONCEPT,
            "id_item": r.ID_ITEM,
            "concept_type": r.CONCEPT_TYPE,
            "concept_scope": r.CONCEPT_SCOPE,
            "is_system": bool(r.IS_SYSTEM) if r.IS_SYSTEM is not None else None,
        }
        concepts_by_ti.setdefault(r.ID_TI, []).append(concept)
    return concepts_by_ti


def get_m4object_details(id_t3, include_rules=False):
    """Obtiene los detalles completos de un m4object a partir de su ID_T3.

    Args:
        id_t3: Identificador del m4object (canal) a consultar.
        include_rules: Si True, incluye el detalle de reglas por TI
                       y el código fuente LN4 (M4RCH_RULES3).

    Returns:
        dict con la estructura jerárquica completa del canal.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1) Cabecera del canal
            header = _fetch_t3_header(cursor, id_t3)
            if not header:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el m4object con ID_T3 '{id_t3}'.",
                }

            # 2) Comentarios multilingüe
            comments = _fetch_t3_comments(cursor, id_t3)

            # 3) Herencia
            inheritance = _fetch_inheritance(cursor, id_t3)

            # 4) Conectores
            connectors = _fetch_connectors(cursor, id_t3)

            # 5) Nodos con TIs
            nodes = _fetch_nodes_with_tis(cursor, id_t3)

            # Recoger todos los ID_TI de los nodos
            ti_ids = [n["ti"]["id_ti"] for n in nodes if n["ti"]]

            # 6) Items por TI
            items_by_ti = _fetch_items_for_tis(cursor, ti_ids)

            # 7) Argumentos de métodos (siempre)
            item_args = _fetch_item_args_for_tis(cursor, ti_ids)

            # 8) Conceptos de nómina (siempre)
            concepts_by_ti = _fetch_concepts_for_tis(cursor, ti_ids)

            # 9) Reglas (conteo siempre, detalle + fuente si se pide)
            rules_count = _fetch_rules_count_for_tis(cursor, ti_ids)
            rules_detail = {}
            rules_source = {}
            if include_rules:
                rules_detail = _fetch_rules_summary(cursor, ti_ids)
                rules_source = _fetch_rules_source_for_tis(cursor, ti_ids)

            # Ensamblar: vincular items, args, conceptos y reglas a cada TI
            for node in nodes:
                if node["ti"]:
                    ti_id = node["ti"]["id_ti"]

                    # Items con argumentos de métodos incrustados
                    ti_items = items_by_ti.get(ti_id, [])
                    for item in ti_items:
                        if item["item_type"] == 3:  # Method
                            args = item_args.get((ti_id, item["id_item"]))
                            if args:
                                item["arguments"] = args
                    node["ti"]["items"] = ti_items

                    # Conceptos
                    ti_concepts = concepts_by_ti.get(ti_id, [])
                    if ti_concepts:
                        node["ti"]["concepts"] = ti_concepts

                    # Reglas
                    node["ti"]["rules_count"] = rules_count.get(ti_id, 0)
                    if include_rules:
                        ti_rules = rules_detail.get(ti_id, [])
                        # Enriquecer cada regla con su código fuente
                        for rule in ti_rules:
                            source = rules_source.get((ti_id, rule["id_item"]))
                            if source:
                                rule["source_code"] = source
                        node["ti"]["rules"] = ti_rules

            # Construir resultado
            total_concepts = sum(len(concepts_by_ti.get(ti, [])) for ti in ti_ids)
            result = {
                "status": "success",
                **header,
                "nodes": nodes,
                "summary": {
                    "node_count": len(nodes),
                    "ti_count": len(ti_ids),
                    "total_items": sum(len(items_by_ti.get(ti, [])) for ti in ti_ids),
                    "total_concepts": total_concepts,
                    "total_rules": sum(rules_count.get(ti, 0) for ti in ti_ids),
                },
            }

            if comments:
                result["comments"] = comments
            if inheritance:
                result["inheritance"] = inheritance
            if connectors:
                result["connectors"] = connectors

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obtiene la definición completa de un m4object (canal).")
    parser.add_argument("id_t3", help="Identificador del m4object (ID_T3)")
    parser.add_argument("--include-rules", action="store_true", help="Incluir detalle de reglas por TI")
    args = parser.parse_args()

    result = get_m4object_details(args.id_t3, include_rules=args.include_rules)
    print(json.dumps(result, indent=2, default=str))
