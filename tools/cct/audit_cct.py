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
        "id_columns": ["ID_RULE", "ID_TI"],
        "primary_id": "ID_RULE",
    },
    {
        "cct_type": "CONCEPT",
        "table": "M4RCH_CONCEPTS",
        "id_columns": ["ID_CONCEPT"],
        "primary_id": "ID_CONCEPT",
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
        set de CCT_OBJECT_ID (o la columna equivalente).
    """
    registered = set()
    try:
        cursor.execute(f"""
            SELECT *
            FROM M4RCT_OBJECTS
            WHERE {pk_col} = ?
        """, cct_task_id)
        rows = cursor.fetchall()

        if not rows:
            return registered, []

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
                    registered.add(str(val).strip())
                    break

        return registered, objects_detail

    except Exception as e:
        return registered, [{"error": str(e)}]


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


def _cross_reference(swept_items, registered_set):
    """Cruza los items barridos contra el set de objetos registrados en el CCT.

    Returns:
        tuple (in_cct, gaps): listas de items ya registrados y faltantes.
    """
    in_cct = []
    gaps = []

    for item in swept_items:
        if "_error" in item:
            gaps.append(item)
            continue

        primary_id = item.get("_primary_id", "")
        if primary_id and primary_id in registered_set:
            in_cct.append(item)
        else:
            gaps.append(item)

    return in_cct, gaps


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
            registered_set, registered_detail = _fetch_cct_registered_objects(
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

            for table_def in SWEEP_TABLES:
                cct_type = table_def["cct_type"]

                swept = _sweep_table(
                    cursor, table_def,
                    id_secuser=id_secuser,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                )

                in_cct, gaps = _cross_reference(swept, registered_set)

                # Limpiar _primary_id del output (es interno)
                for item in in_cct + gaps:
                    item.pop("_primary_id", None)

                audit_results[cct_type] = {
                    "table": table_def["table"],
                    "swept_count": len(swept),
                    "in_cct_count": len(in_cct),
                    "gap_count": len(gaps),
                    "in_cct": in_cct,
                    "gaps": gaps,
                }

                summary["total_swept"] += len(swept)
                summary["total_in_cct"] += len(in_cct)
                summary["total_gaps"] += len(gaps)
                if len(gaps) > 0:
                    summary["gaps_by_type"][cct_type] = len(gaps)

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
