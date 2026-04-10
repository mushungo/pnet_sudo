# tools/m4object/get_payroll_item.py
"""
Lista y describe items de nómina (payroll items) de PeopleNet.

Consulta M4RCH_PAYROLL_ITEM para exponer la definición de conceptos de nómina
dentro de los TIs de canales de tipo payroll.

Uso:
    python -m tools.m4object.get_payroll_item --list
    python -m tools.m4object.get_payroll_item --list --ti "CVE_DP_PAYROLL_CHANNEL"
    python -m tools.m4object.get_payroll_item --ti "CVE_DP_PAYROLL_CHANNEL" --item "CVE_CUENTA_BIENESTAR"
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


def _discover_columns(cursor, table_name):
    """Descubre las columnas disponibles en una tabla."""
    try:
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
            table_name
        )
        return [r.COLUMN_NAME for r in cursor.fetchall()]
    except Exception:
        return []


def list_payroll_items(id_ti=None, search=None, limit=200):
    """Lista items de nómina, opcionalmente filtrados por TI o texto.

    Args:
        id_ti: Filtrar por TI específico (opcional).
        search: Buscar por texto en ID_ITEM o ID_CONCEPT (opcional).
        limit: Máximo de resultados (default 200).

    Returns:
        dict con status, conteo y lista de payroll items.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # Descubrir columnas disponibles
            columns = _discover_columns(cursor, "M4RCH_PAYROLL_ITEM")
            if not columns:
                return {
                    "status": "error",
                    "message": "No se encontró la tabla M4RCH_PAYROLL_ITEM o está vacía.",
                }

            # Columnas seguras para listar
            safe_cols = [c for c in columns if c not in ("SOURCE_CODE",)]
            select_cols = ", ".join(safe_cols)

            # Construir query con filtros opcionales
            where_clauses = []
            params = []

            if id_ti:
                where_clauses.append("ID_TI = ?")
                params.append(id_ti)

            if search:
                search_pattern = f"%{search}%"
                col_searches = []
                for col in ("ID_ITEM", "ID_CONCEPT", "ID_TI"):
                    if col in columns:
                        col_searches.append(f"{col} LIKE ?")
                        params.append(search_pattern)
                if col_searches:
                    where_clauses.append(f"({' OR '.join(col_searches)})")

            where = ""
            if where_clauses:
                where = "WHERE " + " AND ".join(where_clauses)

            sql = f"""
                SELECT TOP {limit} {select_cols}
                FROM M4RCH_PAYROLL_ITEM
                {where}
                ORDER BY ID_TI, ID_ITEM
            """
            cursor.execute(sql, *params)
            rows = cursor.fetchall()

            items = []
            for r in rows:
                item = {}
                for col in safe_cols:
                    val = getattr(r, col, None)
                    if isinstance(val, bool):
                        item[col.lower()] = val
                    elif val is not None:
                        item[col.lower()] = val
                    else:
                        item[col.lower()] = None
                items.append(item)

            return {
                "status": "success",
                "count": len(items),
                "columns_available": safe_cols,
                "payroll_items": items,
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_payroll_item_detail(id_ti, id_item):
    """Obtiene el detalle completo de un payroll item específico.

    Args:
        id_ti: Identificador del TI.
        id_item: Identificador del item.

    Returns:
        dict con todos los campos del payroll item.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            columns = _discover_columns(cursor, "M4RCH_PAYROLL_ITEM")
            if not columns:
                return {
                    "status": "error",
                    "message": "No se encontró la tabla M4RCH_PAYROLL_ITEM.",
                }

            select_cols = ", ".join(columns)
            cursor.execute(
                f"SELECT {select_cols} FROM M4RCH_PAYROLL_ITEM "
                f"WHERE ID_TI = ? AND ID_ITEM = ?",
                id_ti, id_item
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró el payroll item '{id_item}' en TI '{id_ti}'.",
                }

            result = {"status": "success"}
            for col in columns:
                val = getattr(row, col, None)
                result[col.lower()] = val

            # Buscar el item correspondiente en M4RCH_ITEMS para contexto
            cursor.execute(
                "SELECT ID_ITEM_TYPE, ID_M4_TYPE, N_SYNONYMESP, N_SYNONYMENG, "
                "ID_READ_OBJECT, ID_READ_FIELD "
                "FROM M4RCH_ITEMS WHERE ID_TI = ? AND ID_ITEM = ?",
                id_ti, id_item
            )
            item_row = cursor.fetchone()
            if item_row:
                result["item_context"] = {
                    "item_type": item_row.ID_ITEM_TYPE,
                    "m4_type": item_row.ID_M4_TYPE,
                    "name_esp": item_row.N_SYNONYMESP,
                    "name_eng": item_row.N_SYNONYMENG,
                    "read_object": item_row.ID_READ_OBJECT,
                    "read_field": item_row.ID_READ_FIELD,
                }

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lista o describe payroll items de PeopleNet."
    )
    parser.add_argument("--list", action="store_true", help="Listar payroll items")
    parser.add_argument("--ti", help="Filtrar/buscar por ID_TI")
    parser.add_argument("--item", help="ID_ITEM específico (requiere --ti)")
    parser.add_argument("--search", help="Buscar por texto en ID_ITEM/ID_CONCEPT/ID_TI")
    parser.add_argument("--limit", type=int, default=200, help="Máximo de resultados (default 200)")
    args = parser.parse_args()

    if args.item and args.ti:
        result = get_payroll_item_detail(args.ti, args.item)
    else:
        result = list_payroll_items(
            id_ti=args.ti,
            search=args.search,
            limit=args.limit,
        )

    print(json.dumps(result, indent=2, default=str))
