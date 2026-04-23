# tools/cct/audit_cct.py
"""
Audita un CCT (Control de Cambio): detecta objetos PeopleNet creados o
modificados en BD que no están registrados en el CCT indicado.

Barre las tablas tecnológicas de metadatos filtrando por usuario y/o rango
de fechas (campos auditables universales: ID_SECUSER, DT_LAST_UPDATE,
ID_APPROLE) y cruza los resultados contra M4RCT_OBJECTS.

Tablas barridas:
  - M4RDC_FIELDS     (campos BDL)
  - M4RCH_ITEMS      (items de TI)
  - M4RCH_PAYROLL_ITEM (items de nómina)
  - M4RCH_T3S        (presentaciones/canales)
  - M4RCH_RULES      (reglas LN4)
  - M4RCH_CONCEPTS   (conceptos de nómina)
  - M4RCH_SENTENCES  (sentencias SQL)

Uso:
    python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --user JPEREZ
    python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --from 2026-01-01 --to 2026-03-25
    python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --user JPEREZ --from 2026-03-01
"""
import sys
import os
import json
import argparse
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# Definición de las tablas a barrer.
# Cada entrada: (tipo_cct, tabla, columnas_id, columna_id_principal)
# columnas_id: columnas que identifican el objeto para cruzar con M4RCT_OBJECTS
SWEEP_TABLES = [
    {
        "cct_type": "FIELD",
        "table": "M4RDC_FIELDS",
        "id_columns": ["ID_FIELD", "ID_OBJECT"],
        "primary_id": "ID_FIELD",
    },
    {
        "cct_type": "ITEM",
        "table": "M4RCH_ITEMS",
        "id_columns": ["ID_ITEM", "ID_TI"],
        "primary_id": "ID_ITEM",
    },
    {
        "cct_type": "PAYROLL_ITEM",
        "table": "M4RCH_PAYROLL_ITEM",
        "id_columns": ["ID_PAYROLL_ITEM", "ID_T3"],
        "primary_id": "ID_PAYROLL_ITEM",
    },
    {
        "cct_type": "PRESENTATION",
        "table": "M4RCH_T3S",
        "id_columns": ["ID_T3"],
        "primary_id": "ID_T3",
    },
    {
        "cct_type": "RULE",
        "table": "M4RCH_RULES",
        "id_columns": ["ID_RULE", "ID_TI", "ID_ITEM"],
        "primary_id": "ID_RULE",
    },
    {
        "cct_type": "CONCEPT",
        "table": "M4RCH_CONCEPTS",
        "id_columns": ["ID_TI", "ID_ITEM"],
        "primary_id": "ID_ITEM",
    },
    {
        "cct_type": "SENTENCE",
        "table": "M4RCH_SENTENCES",
        "id_columns": ["ID_SENTENCE"],
        "primary_id": "ID_SENTENCE",
    },
]


def _fetch_cct_header(cursor, cct_task_id):
    """Obtiene la cabecera del CCT desde M4RCT_TASK.

    Intenta primero con CCT_TASK_ID, luego con ID_TASK como fallback
    por si el nombre de columna difiere entre instalaciones.
    """
    # Intentar las variantes de columna PK conocidas
    for pk_col in ["CCT_TASK_ID", "ID_TASK"]:
        try:
            cursor.execute(f"""
                SELECT TOP 1 *
                FROM M4RCT_TASK
                WHERE {pk_col} = ?
            """, cct_task_id)
            row = cursor.fetchone()
            if row:
                # Extraer columnas disponibles dinámicamente
                columns = [desc[0] for desc in cursor.description]
                header = {}
                for col in columns:
                    header[col.lower()] = getattr(row, col, None)
                header["_pk_column"] = pk_col
                return header
        except Exception:
            continue

    return None


def _fetch_cct_registered_objects(cursor, cct_task_id, pk_col):
    """Obtiene los objetos ya registrados en el CCT desde M4RCT_OBJECTS.

    Returns:
        tuple (registered_set, registered_detail, registered_map) donde:
          - registered_set: set de CCT_OBJECT_ID registrados.
          - registered_detail: lista de dicts con el detalle completo.
          - registered_map: dict {cct_object_id: [cct_parent_obj_id, ...]} para
            verificar cobertura por canal.
    """
    registered = set()
    registered_map = {}
    try:
        cursor.execute(f"""
            SELECT *
            FROM M4RCT_OBJECTS
            WHERE {pk_col} = ?
        """, cct_task_id)
        rows = cursor.fetchall()

        if not rows:
            return registered, [], registered_map

        columns = [desc[0] for desc in cursor.description]
        objects_detail = []
        for row in rows:
            obj = {}
            for col in columns:
                obj[col.lower()] = getattr(row, col, None)
            objects_detail.append(obj)

            # Intentar extraer el ID del objeto registrado
            # Buscar en columnas candidatas
            for candidate in ["CCT_OBJECT_ID", "ID_OBJECT", "OBJECT_ID"]:
                val = getattr(row, candidate, None)
                if val:
                    obj_id = str(val).strip()
                    registered.add(obj_id)

                    # Construir el mapa de canales por objeto
                    parent_val = None
                    for parent_candidate in ["CCT_PARENT_OBJ_ID", "ID_PARENT", "PARENT_OBJ_ID"]:
                        parent_val = getattr(row, parent_candidate, None)
                        if parent_val:
                            break
                    parent_str = str(parent_val).strip() if parent_val else None
                    if obj_id not in registered_map:
                        registered_map[obj_id] = []
                    if parent_str and parent_str not in registered_map[obj_id]:
                        registered_map[obj_id].append(parent_str)
                    break

        return registered, objects_detail, registered_map

    except Exception as e:
        return registered, [{"error": str(e)}], registered_map


def _sweep_table(cursor, table_def, id_secuser=None, fecha_desde=None, fecha_hasta=None):
    """Barre una tabla tecnológica filtrando por campos auditables.

    Returns:
        list of dicts con los objetos encontrados.
    """
    id_cols = ", ".join(table_def["id_columns"])
    table = table_def["table"]

    where_parts = []
    params = []

    if id_secuser:
        where_parts.append("ID_SECUSER = ?")
        params.append(id_secuser)

    if fecha_desde:
        where_parts.append("DT_LAST_UPDATE >= ?")
        params.append(fecha_desde)

    if fecha_hasta:
        where_parts.append("DT_LAST_UPDATE <= ?")
        params.append(fecha_hasta)

    where_clause = " AND ".join(where_parts) if where_parts else "1=1"

    sql = f"""
        SELECT {id_cols}, ID_SECUSER, DT_LAST_UPDATE, ID_APPROLE
        FROM {table}
        WHERE {where_clause}
        ORDER BY DT_LAST_UPDATE DESC
    """

    try:
        cursor.execute(sql, *params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            entry = {
                "id_secuser": row.ID_SECUSER,
                "dt_last_update": row.DT_LAST_UPDATE,
                "id_approle": row.ID_APPROLE,
            }
            for col in table_def["id_columns"]:
                entry[col.lower()] = getattr(row, col, None)

            # Generar un ID comparable para cruzar con M4RCT_OBJECTS
            primary_val = getattr(row, table_def["primary_id"], None)
            entry["_primary_id"] = str(primary_val).strip() if primary_val else None

            results.append(entry)

        return results

    except Exception as e:
        return [{"_error": str(e), "_table": table}]


def _cross_reference(swept_items, registered_set, registered_map=None, parent_col=None):
    """Cruza los items barridos contra el set de objetos registrados en el CCT.

    Para tipos que usan clave compuesta (FIELD, ITEM), si se pasa registered_map
    y parent_col se verifica también que el parent coincida. Si el objeto está en
    registered_set pero con parent incorrecto se marca como 'wrong_parent'.

    Args:
        swept_items: lista de dicts del barrido.
        registered_set: set de CCT_OBJECT_ID registrados.
        registered_map: dict {cct_object_id: [cct_parent_obj_id]} (opcional).
        parent_col: nombre de la columna parent en el entry (ej: "id_ti", "id_object").

    Returns:
        tuple (in_cct, gaps, wrong_parent): listas de registrados, faltantes y con parent incorrecto.
    """
    in_cct = []
    gaps = []
    wrong_parent = []

    for item in swept_items:
        if "_error" in item:
            gaps.append(item)
            continue

        primary_id = item.get("_primary_id", "")
        if not primary_id or primary_id not in registered_set:
            gaps.append(item)
            continue

        # El objeto está en el CCT — verificar parent si aplica
        if registered_map is not None and parent_col:
            parent_val = item.get(parent_col)
            parents_in_cct = registered_map.get(primary_id, [])
            if parent_val and parents_in_cct and parent_val not in parents_in_cct:
                wrong = dict(item)
                wrong["_parent_in_bd"] = parent_val
                wrong["_parent_in_cct"] = parents_in_cct
                wrong["_note"] = (
                    f"Registrado en CCT con parent {parents_in_cct} "
                    f"pero en BD el parent es '{parent_val}'"
                )
                wrong_parent.append(wrong)
                continue

        in_cct.append(item)

    return in_cct, gaps, wrong_parent


def _check_rule_covered_by_ns_item(rule_gaps, registered_map):
    """Reclasifica gaps de RULE según si el ítem padre está en el CCT para el mismo canal.

    El objeto RAMDL NS ITEM incluye automáticamente todas las reglas del ítem
    en ese canal (lee SCH_RULES y llama call-object RULE por cada una). Por
    tanto, si un ITEM está registrado en el CCT para (canal X), todas sus
    reglas en (canal X) quedan cubiertas sin necesidad de registro explícito.

    Args:
        rule_gaps: lista de dicts de gaps RULE (cada uno tiene id_rule, id_ti, id_item).
        registered_map: dict {cct_object_id: [cct_parent_obj_id, ...]} del CCT.

    Returns:
        tuple (true_gaps, covered_by_ns_item):
          - true_gaps: reglas que siguen siendo gaps reales.
          - covered_by_ns_item: reglas cubiertas por el NS ITEM del canal.
    """
    true_gaps = []
    covered_by_ns_item = []

    for gap in rule_gaps:
        if "_error" in gap:
            true_gaps.append(gap)
            continue

        id_item = gap.get("id_item")
        id_ti = gap.get("id_ti")

        # Comprobar si el ítem padre está registrado en el CCT para este canal
        parents_in_cct = registered_map.get(id_item, []) if id_item else []
        if id_ti and id_ti in parents_in_cct:
            covered = dict(gap)
            covered["_covered_by"] = f"NS ITEM {id_item} en {id_ti}"
            covered_by_ns_item.append(covered)
        else:
            true_gaps.append(gap)

    return true_gaps, covered_by_ns_item


def _check_object_parent_coverage(swept, registered_map, object_col, parent_col, cct_type_label):
    """Detecta objetos modificados en parents (canal/BDL obj) no registrados en el CCT.

    Generalización para ITEM (parent = ID_TI) y FIELD (parent = ID_OBJECT).
    Si el objeto está en el CCT pero con parent distinto al de BD → parent_gaps.
    Si el objeto está en el CCT para ese parent → ok.
    Si el objeto no está en absoluto → lo detecta el cross_reference normal.

    Args:
        swept: lista de dicts del barrido.
        registered_map: dict {cct_object_id: [cct_parent_obj_id, ...]} del CCT.
        object_col: nombre de la columna del objeto en el entry (ej: "id_item", "id_field").
        parent_col: nombre de la columna del parent en el entry (ej: "id_ti", "id_object").
        cct_type_label: etiqueta para el campo "type" del gap (ej: "ITEM", "FIELD").

    Returns:
        lista de dicts con los (object, parent) que faltan en el CCT.
    """
    parent_gaps = []

    for entry in swept:
        if "_error" in entry:
            continue
        obj_id = entry.get(object_col)
        parent_id = entry.get(parent_col)

        parents_in_cct = registered_map.get(obj_id, [])

        if not parents_in_cct:
            # No está en el CCT en absoluto → ya lo detecta el gap normal
            continue

        if parent_id and parent_id not in parents_in_cct:
            parent_gaps.append({
                "cct_type": cct_type_label,
                object_col: obj_id,
                parent_col: parent_id,
                f"{parent_col}_en_cct": parents_in_cct,
                "id_secuser": entry.get("id_secuser"),
                "dt_last_update": entry.get("dt_last_update"),
                "note": (
                    f"{cct_type_label} registrado en CCT con parent {parents_in_cct} "
                    f"pero modificado con parent '{parent_id}'"
                ),
            })

    return parent_gaps


def _detect_physical_script_gaps(cursor, field_swept, registered_map):
    """Detecta columnas físicas en BD que no tienen PHYSICAL SCRIPT en el CCT.

    Para cada campo lógico (M4RDC_FIELDS) barrido, busca si existe una columna
    física en INFORMATION_SCHEMA.COLUMNS en tablas M4<ID_OBJECT>. Si la columna
    existe físicamente pero no hay un PHYSICAL SCRIPT registrado en el CCT con
    ese ID_FIELD, se reporta como gap.

    El patrón de nombre de tabla física es: M4 + los primeros 14 chars del ID_OBJECT
    (truncado para ajustarse a los 16 chars de nombre de tabla SQL Server usados
    históricamente en PeopleNet, ej: SVE_AC_HR_PERIOD → M4SVE_AC_HR_PER).

    Args:
        cursor: cursor de BD activo.
        field_swept: lista de dicts del barrido de M4RDC_FIELDS.
        registered_map: dict {cct_object_id: [cct_parent_obj_id, ...]} del CCT.

    Returns:
        lista de dicts con columnas físicas que faltan como PHYSICAL SCRIPT en el CCT.
    """
    physical_gaps = []
    checked = set()  # evitar duplicados (mismo field puede aparecer varias veces)

    for entry in field_swept:
        if "_error" in entry:
            continue
        id_field = entry.get("id_field")
        id_object = entry.get("id_object")
        if not id_field or not id_object:
            continue

        key = (id_field, id_object)
        if key in checked:
            continue
        checked.add(key)

        # Nombre de tabla física: M4 + id_object (SQL Server trunca a 128 chars,
        # pero PeopleNet históricamente usa M4 + primeros 14 chars del ID_OBJECT)
        physical_table_prefix = ("M4" + id_object)[:16]

        try:
            cursor.execute(
                """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE COLUMN_NAME = ? AND TABLE_NAME LIKE ?""",
                id_field,
                physical_table_prefix + "%",
            )
            phys_rows = cursor.fetchall()
        except Exception:
            continue

        if not phys_rows:
            continue  # no existe columna física → no es un campo almacenado

        # Existe físicamente → comprobar si hay PHYSICAL SCRIPT en el CCT
        # El registered_map contiene todos los CCT_OBJECT_ID independientemente del tipo;
        # un PHYSICAL SCRIPT se registra con CCT_OBJECT_ID = ID_FIELD
        if id_field in registered_map:
            continue  # ya registrado como PHYSICAL SCRIPT (u otro tipo con mismo ID)

        physical_gaps.append({
            "id_field": id_field,
            "id_object": id_object,
            "physical_tables": [r[0] for r in phys_rows],
            "id_secuser": entry.get("id_secuser"),
            "dt_last_update": entry.get("dt_last_update"),
            "note": (
                f"Columna física '{id_field}' existe en {[r[0] for r in phys_rows]} "
                f"pero no hay PHYSICAL SCRIPT registrado en el CCT"
            ),
        })

    return physical_gaps


def audit_cct(cct_task_id, id_secuser=None, fecha_desde=None, fecha_hasta=None):
    """Audita un CCT: detecta gaps entre objetos modificados en BD y registrados en el CCT.

    Args:
        cct_task_id: Identificador del CCT a auditar.
        id_secuser: Filtrar por usuario que modificó (opcional).
        fecha_desde: Filtrar desde esta fecha YYYY-MM-DD (opcional).
        fecha_hasta: Filtrar hasta esta fecha YYYY-MM-DD (opcional).

    Returns:
        dict con cabecera del CCT, objetos registrados, gaps por tipo, y resumen.
    """
    if not id_secuser and not fecha_desde:
        return {
            "status": "error",
            "message": "Se requiere al menos --user o --from para acotar el barrido. "
                       "Sin filtros, el barrido devolvería toda la historia de todas las tablas.",
        }

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Cabecera del CCT
            header = _fetch_cct_header(cursor, cct_task_id)
            if not header:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el CCT '{cct_task_id}' en M4RCT_TASK.",
                }

            pk_col = header.pop("_pk_column", "CCT_TASK_ID")

            # 2. Objetos ya registrados
            registered_set, registered_detail, registered_map = _fetch_cct_registered_objects(
                cursor, cct_task_id, pk_col
            )

            # 3 & 4. Barrer tablas y cruzar
            audit_results = {}
            summary = {
                "total_swept": 0,
                "total_in_cct": 0,
                "total_gaps": 0,
                "gaps_by_type": {},
            }

            field_swept_all = []
            item_swept_all = []

            for table_def in SWEEP_TABLES:
                cct_type = table_def["cct_type"]

                swept = _sweep_table(
                    cursor, table_def,
                    id_secuser=id_secuser,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                )

                # Determinar si se requiere verificación de parent
                if cct_type == "ITEM":
                    in_cct, gaps, wrong_parent = _cross_reference(
                        swept, registered_set, registered_map=registered_map, parent_col="id_ti"
                    )
                    item_swept_all = swept
                elif cct_type == "FIELD":
                    in_cct, gaps, wrong_parent = _cross_reference(
                        swept, registered_set, registered_map=registered_map, parent_col="id_object"
                    )
                    field_swept_all = swept
                else:
                    in_cct, gaps, wrong_parent = _cross_reference(swept, registered_set)

                # Para RULE: reclasificar gaps cubiertos por NS ITEM
                covered_by_ns_item = []
                if cct_type == "RULE":
                    gaps, covered_by_ns_item = _check_rule_covered_by_ns_item(gaps, registered_map)
                    for gap in gaps:
                        id_item = gap.get("id_item")
                        id_ti = gap.get("id_ti")
                        if id_item and id_item in registered_map:
                            gap["_note"] = (
                                f"Se resuelve registrando ITEM {id_item} en canal {id_ti} en el CCT"
                            )

                # Limpiar _primary_id del output (es interno)
                for item in in_cct + gaps + covered_by_ns_item + wrong_parent:
                    item.pop("_primary_id", None)

                result_entry = {
                    "table": table_def["table"],
                    "swept_count": len(swept),
                    "in_cct_count": len(in_cct),
                    "gap_count": len(gaps),
                    "in_cct": in_cct,
                    "gaps": gaps,
                }
                if covered_by_ns_item:
                    result_entry["covered_by_ns_item"] = covered_by_ns_item
                    result_entry["covered_by_ns_item_count"] = len(covered_by_ns_item)
                if wrong_parent:
                    result_entry["wrong_parent"] = wrong_parent
                    result_entry["wrong_parent_count"] = len(wrong_parent)

                audit_results[cct_type] = result_entry

                summary["total_swept"] += len(swept)
                summary["total_in_cct"] += len(in_cct)
                summary["total_gaps"] += len(gaps)
                if len(gaps) > 0:
                    summary["gaps_by_type"][cct_type] = len(gaps)

            # 5. Verificación de cobertura de parents (canales para ITEM, objetos BDL para FIELD)
            item_parent_gaps = _check_object_parent_coverage(
                item_swept_all, registered_map,
                object_col="id_item", parent_col="id_ti", cct_type_label="ITEM"
            )
            field_parent_gaps = _check_object_parent_coverage(
                field_swept_all, registered_map,
                object_col="id_field", parent_col="id_object", cct_type_label="FIELD"
            )
            parent_gaps = item_parent_gaps + field_parent_gaps
            if parent_gaps:
                summary["parent_gaps_count"] = len(parent_gaps)

            # 6. Detectar columnas físicas sin PHYSICAL SCRIPT en el CCT
            physical_script_gaps = _detect_physical_script_gaps(cursor, field_swept_all, registered_map)
            if physical_script_gaps:
                summary["physical_script_gaps_count"] = len(physical_script_gaps)

            return {
                "status": "success",
                "cct_task_id": cct_task_id,
                "cct_header": header,
                "registered_objects": {
                    "count": len(registered_set),
                    "ids": sorted(registered_set),
                    "detail": registered_detail,
                },
                "filters": {
                    "id_secuser": id_secuser,
                    "fecha_desde": fecha_desde,
                    "fecha_hasta": fecha_hasta,
                },
                "audit": audit_results,
                "parent_gaps": parent_gaps,
                "physical_script_gaps": physical_script_gaps,
                "summary": summary,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audita un CCT: detecta gaps entre objetos modificados en BD "
                    "y registrados en el Control de Cambio."
    )
    parser.add_argument(
        "cct_task_id",
        help="Identificador del CCT a auditar (ej: CONTROL_CAMBIO_258_2026)"
    )
    parser.add_argument(
        "--user",
        dest="id_secuser",
        help="Filtrar por usuario que modificó (ID_SECUSER)"
    )
    parser.add_argument(
        "--from",
        dest="fecha_desde",
        help="Filtrar desde esta fecha (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to",
        dest="fecha_hasta",
        help="Filtrar hasta esta fecha (YYYY-MM-DD)"
    )
    args = parser.parse_args()

    result = audit_cct(
        args.cct_task_id,
        id_secuser=args.id_secuser,
        fecha_desde=args.fecha_desde,
        fecha_hasta=args.fecha_hasta,
    )
    print(json.dumps(result, indent=2, default=str))
