# tools/m4object/get_ti_bdl_schema.py
"""
Traza la relación TI -> BDL -> objetos físicos SQL de PeopleNet.

Dado un ID_TI (o un ID_T3 para expandir todos sus TIs), devuelve:
  - Objetos lógicos BDL de lectura/escritura (M4RDC_LOGIC_OBJECT)
  - Tablas físicas SQL asociadas (M4RDC_REAL_OBJECTS)
  - Sentences asociadas (ID_READ_SENTENCE, ID_WRITE_SENTENCE)
  - Overrides a nivel de item (items que apuntan a un BDL distinto al del TI)

Opcionalmente con --fields incluye el mapeo campo-a-campo:
  - M4RDC_REAL_FIELDS (columna SQL <-> campo lógico BDL)

Uso:
    python -m tools.m4object.get_ti_bdl_schema --ti "EMPLOYEE_TI"
    python -m tools.m4object.get_ti_bdl_schema --t3 "SCO_MNG_DEV_PRODUCT"
    python -m tools.m4object.get_ti_bdl_schema --ti "EMPLOYEE_TI" --fields
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


OBJECT_TYPE_MAP = {
    1: "table",
    3: "overflow",
    4: "view",
    5: "master_overflow",
    7: "custom_m4",
    8: "hash_temp",
}


def _fetch_ti_info(cursor, id_ti):
    """Obtiene la info del TI y sus referencias a objetos BDL y sentences."""
    cursor.execute("""
        SELECT
            ti.ID_TI, ti.N_TIESP, ti.N_TIENG,
            ti.ID_READ_OBJECT, ti.ID_WRITE_OBJECT,
            ti.ID_READ_SENTENCE, ti.ID_WRITE_SENTENCE,
            ti.IS_SYSTEM_TI, ti.GENERATE_SQL, ti.ID_TI_BASE
        FROM M4RCH_TIS ti
        WHERE ti.ID_TI = ?
    """, id_ti)
    return cursor.fetchone()


def _fetch_tis_for_t3(cursor, id_t3):
    """Obtiene todos los TIs montados en un canal via M4RCH_NODES."""
    cursor.execute("""
        SELECT DISTINCT
            ti.ID_TI, ti.N_TIESP, ti.N_TIENG,
            ti.ID_READ_OBJECT, ti.ID_WRITE_OBJECT,
            ti.ID_READ_SENTENCE, ti.ID_WRITE_SENTENCE,
            ti.IS_SYSTEM_TI, ti.GENERATE_SQL, ti.ID_TI_BASE,
            n.ID_NODE, n.N_NODEESP
        FROM M4RCH_NODES n
        INNER JOIN M4RCH_TIS ti ON n.ID_TI = ti.ID_TI
        WHERE n.ID_T3 = ?
        ORDER BY n.POS_NODO
    """, id_t3)
    return cursor.fetchall()


def _fetch_item_overrides(cursor, id_ti):
    """Obtiene items que tienen ID_READ_OBJECT o ID_WRITE_OBJECT distinto
    al del TI padre (overrides a nivel de item)."""
    cursor.execute("""
        SELECT
            i.ID_ITEM, i.ID_ITEM_TYPE,
            i.ID_READ_OBJECT, i.ID_WRITE_OBJECT,
            i.ID_READ_FIELD, i.ID_WRITE_FIELD
        FROM M4RCH_ITEMS i
        WHERE i.ID_TI = ?
          AND (i.ID_READ_OBJECT IS NOT NULL OR i.ID_WRITE_OBJECT IS NOT NULL)
        ORDER BY i.ID_ITEM
    """, id_ti)
    return cursor.fetchall()


def _fetch_logic_object(cursor, id_object):
    """Obtiene info del objeto lógico BDL."""
    cursor.execute("""
        SELECT ID_OBJECT, REAL_NAME, ID_OBJECT_TYPE,
               ID_TRANS_OBJESP, ID_TRANS_OBJENG
        FROM M4RDC_LOGIC_OBJECT
        WHERE ID_OBJECT = ?
    """, id_object)
    return cursor.fetchone()


def _fetch_real_objects(cursor, id_object):
    """Obtiene las tablas físicas SQL asociadas a un objeto lógico."""
    cursor.execute("""
        SELECT ID_REAL_OBJECT, ID_OBJECT_TYPE, IS_PRINCIPAL, PK_NAME
        FROM M4RDC_REAL_OBJECTS
        WHERE ID_OBJECT = ?
        ORDER BY IS_PRINCIPAL DESC, ID_REAL_OBJECT
    """, id_object)
    return cursor.fetchall()


def _fetch_real_fields(cursor, id_real_object):
    """Obtiene el mapeo de campos físicos a lógicos de una tabla."""
    cursor.execute("""
        SELECT ID_REAL_FIELD, ID_FIELD, ID_OBJECT
        FROM M4RDC_REAL_FIELDS
        WHERE ID_REAL_OBJECT = ?
        ORDER BY ID_REAL_FIELD
    """, id_real_object)
    return cursor.fetchall()


def _resolve_bdl_chain(cursor, id_object, include_fields=False):
    """Resuelve la cadena completa: objeto lógico -> tablas físicas -> campos.

    Returns:
        dict con info del objeto lógico, sus tablas físicas y opcionalmente campos.
        None si el id_object es None o no se encuentra.
    """
    if not id_object:
        return None

    logic_row = _fetch_logic_object(cursor, id_object)
    if not logic_row:
        return {"id_object": id_object, "status": "not_found_in_bdl"}

    result = {
        "id_object": logic_row.ID_OBJECT,
        "real_name": logic_row.REAL_NAME,
        "description": logic_row.ID_TRANS_OBJESP or logic_row.ID_TRANS_OBJENG,
        "physical_tables": [],
    }

    real_rows = _fetch_real_objects(cursor, id_object)
    for rr in real_rows:
        table_entry = {
            "sql_table": rr.ID_REAL_OBJECT,
            "object_type": OBJECT_TYPE_MAP.get(rr.ID_OBJECT_TYPE, str(rr.ID_OBJECT_TYPE)),
            "is_principal": bool(rr.IS_PRINCIPAL) if rr.IS_PRINCIPAL is not None else None,
            "pk_name": rr.PK_NAME,
        }

        if include_fields:
            field_rows = _fetch_real_fields(cursor, rr.ID_REAL_OBJECT)
            table_entry["fields"] = [
                {
                    "sql_column": fr.ID_REAL_FIELD,
                    "logical_field": fr.ID_FIELD,
                    "logical_object": fr.ID_OBJECT,
                }
                for fr in field_rows
            ]
            table_entry["field_count"] = len(table_entry["fields"])

        result["physical_tables"].append(table_entry)

    result["table_count"] = len(result["physical_tables"])
    return result


def _build_ti_schema(cursor, ti_row, include_fields=False, node_info=None):
    """Construye el schema BDL completo para un TI.

    Args:
        cursor: DB cursor activo.
        ti_row: Row de M4RCH_TIS con las columnas esperadas.
        include_fields: Si True, incluye mapeo campo-a-campo.
        node_info: dict con id_node y node_name si viene de expansion por T3.

    Returns:
        dict con toda la info de schema BDL del TI.
    """
    ti_schema = {
        "id_ti": ti_row.ID_TI,
        "name_esp": ti_row.N_TIESP,
        "name_eng": ti_row.N_TIENG,
        "ti_base": ti_row.ID_TI_BASE,
        "is_system": bool(ti_row.IS_SYSTEM_TI) if ti_row.IS_SYSTEM_TI is not None else None,
        "generate_sql": bool(ti_row.GENERATE_SQL) if ti_row.GENERATE_SQL is not None else None,
    }

    if node_info:
        ti_schema["node"] = node_info

    # Objetos BDL a nivel de TI
    read_obj_id = ti_row.ID_READ_OBJECT
    write_obj_id = ti_row.ID_WRITE_OBJECT

    ti_schema["read_object_id"] = read_obj_id
    ti_schema["write_object_id"] = write_obj_id

    # Sentences a nivel de TI
    ti_schema["read_sentence"] = ti_row.ID_READ_SENTENCE
    ti_schema["write_sentence"] = ti_row.ID_WRITE_SENTENCE

    # Resolver cadena BDL para objetos de lectura y escritura
    # Evitar resolver el mismo objeto dos veces
    resolved_objects = {}

    if read_obj_id:
        resolved_objects[read_obj_id] = _resolve_bdl_chain(cursor, read_obj_id, include_fields)
    if write_obj_id and write_obj_id != read_obj_id:
        resolved_objects[write_obj_id] = _resolve_bdl_chain(cursor, write_obj_id, include_fields)

    ti_schema["read_bdl"] = resolved_objects.get(read_obj_id)
    ti_schema["write_bdl"] = resolved_objects.get(write_obj_id)

    # Items con overrides de BDL (items que apuntan a objetos distintos al TI)
    item_rows = _fetch_item_overrides(cursor, ti_row.ID_TI)

    # Filtrar items cuyo read/write object difiere del TI
    overrides = []
    override_object_ids = set()
    for ir in item_rows:
        item_read = ir.ID_READ_OBJECT
        item_write = ir.ID_WRITE_OBJECT

        is_override = (
            (item_read and item_read != read_obj_id)
            or (item_write and item_write != write_obj_id)
        )
        if is_override:
            entry = {
                "id_item": ir.ID_ITEM,
                "item_type": ir.ID_ITEM_TYPE,
                "read_object": item_read,
                "write_object": item_write,
                "read_field": ir.ID_READ_FIELD,
                "write_field": ir.ID_WRITE_FIELD,
            }
            overrides.append(entry)
            if item_read and item_read not in resolved_objects:
                override_object_ids.add(item_read)
            if item_write and item_write not in resolved_objects:
                override_object_ids.add(item_write)

    # Resolver objetos BDL de los overrides
    additional_bdl = {}
    for obj_id in override_object_ids:
        additional_bdl[obj_id] = _resolve_bdl_chain(cursor, obj_id, include_fields)

    ti_schema["item_overrides"] = overrides
    ti_schema["override_count"] = len(overrides)

    # Compilar todos los objetos BDL referenciados (sin duplicados)
    all_bdl = {}
    all_bdl.update(resolved_objects)
    all_bdl.update(additional_bdl)
    ti_schema["all_bdl_objects"] = {k: v for k, v in all_bdl.items() if v is not None}

    # Recopilar todas las tablas SQL referenciadas (resumen plano)
    sql_tables = set()
    for bdl_info in ti_schema["all_bdl_objects"].values():
        if isinstance(bdl_info, dict) and "physical_tables" in bdl_info:
            for pt in bdl_info["physical_tables"]:
                sql_tables.add(pt["sql_table"])
    ti_schema["all_sql_tables"] = sorted(sql_tables)

    return ti_schema


def get_ti_bdl_schema(id_ti=None, id_t3=None, include_fields=False):
    """Traza la relación TI -> BDL -> objetos físicos SQL.

    Uno de id_ti o id_t3 es requerido.

    Args:
        id_ti: Identificador de un TI específico.
        id_t3: Identificador de un canal (expande todos sus TIs).
        include_fields: Si True, incluye mapeo campo-a-campo físico/lógico.

    Returns:
        dict con status y la información de schema BDL.
    """
    if not id_ti and not id_t3:
        return {
            "status": "error",
            "message": "Se requiere --ti o --t3. Use -h para ayuda.",
        }

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            if id_ti:
                # Modo: TI individual
                ti_row = _fetch_ti_info(cursor, id_ti)
                if not ti_row:
                    return {
                        "status": "not_found",
                        "message": f"No se encontró el TI '{id_ti}'.",
                    }

                schema = _build_ti_schema(cursor, ti_row, include_fields)
                return {
                    "status": "success",
                    "mode": "single_ti",
                    "ti": schema,
                }

            else:
                # Modo: expandir todos los TIs de un canal
                ti_rows = _fetch_tis_for_t3(cursor, id_t3)
                if not ti_rows:
                    return {
                        "status": "not_found",
                        "message": f"No se encontraron TIs para el canal '{id_t3}'.",
                    }

                tis = []
                all_sql_tables = set()
                all_bdl_objects = set()

                for tr in ti_rows:
                    node_info = {
                        "id_node": tr.ID_NODE,
                        "node_name": tr.N_NODEESP,
                    }
                    schema = _build_ti_schema(cursor, tr, include_fields, node_info)
                    tis.append(schema)
                    all_sql_tables.update(schema.get("all_sql_tables", []))
                    all_bdl_objects.update(schema.get("all_bdl_objects", {}).keys())

                return {
                    "status": "success",
                    "mode": "channel_expansion",
                    "id_t3": id_t3,
                    "ti_count": len(tis),
                    "tis": tis,
                    "summary": {
                        "total_tis": len(tis),
                        "unique_bdl_objects": sorted(all_bdl_objects),
                        "unique_sql_tables": sorted(all_sql_tables),
                        "bdl_object_count": len(all_bdl_objects),
                        "sql_table_count": len(all_sql_tables),
                    },
                }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Traza la relación TI -> BDL -> objetos físicos SQL."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ti", dest="id_ti", help="Identificador del TI a trazar")
    group.add_argument("--t3", dest="id_t3", help="Identificador del canal (expande todos sus TIs)")
    parser.add_argument(
        "--fields",
        action="store_true",
        help="Incluir mapeo campo-a-campo (columna SQL <-> campo lógico BDL)"
    )
    args = parser.parse_args()

    result = get_ti_bdl_schema(id_ti=args.id_ti, id_t3=args.id_t3, include_fields=args.fields)
    print(json.dumps(result, indent=2, default=str))
