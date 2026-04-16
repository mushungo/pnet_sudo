# tools/nomina/get_payslip_layout.py
"""
Consulta el layout de "salida a papel" (recibo de nomina) de PeopleNet.

Expone las tablas:
  - M4SCO_ROWS          (filas del recibo)
  - M4SCO_ROW_COL_DEF   (definicion celda fila x columna)
  - M4SCO_ROWS_DETAIL   (configuracion de totalizacion por fila)

Estas tres tablas definen que conceptos de nomina y que valores calculados
se imprimen en cada fila y columna de un recibo de salarios.

Uso:
    python -m tools.nomina.get_payslip_layout --list-reports
    python -m tools.nomina.get_payslip_layout --list-rows
    python -m tools.nomina.get_payslip_layout --list-rows --report "ID_INFORME"
    python -m tools.nomina.get_payslip_layout --list-rows --search "BIENESTAR"
    python -m tools.nomina.get_payslip_layout --row --report "ID_INFORME" --body "ID_CUERPO" --row-id 10
    python -m tools.nomina.get_payslip_layout --list-cells --report "ID_INFORME" --body "ID_CUERPO"
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


def _row_to_dict(row, columns):
    """Convierte una fila de cursor en diccionario."""
    result = {}
    for col in columns:
        val = getattr(row, col, None)
        result[col.lower()] = val
    return result


def list_reports(search=None, limit=100):
    """Lista los informes de recibo disponibles desde M4SCO_REPORTS.

    Args:
        search: Buscar por texto en ID o nombre del informe (opcional).
        limit:  Maximo de resultados (default 100).

    Returns:
        dict con status, conteo y lista de informes.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            columns = _discover_columns(cursor, "M4SCO_REPORTS")
            if not columns:
                return {
                    "status": "error",
                    "message": "No se encontro la tabla M4SCO_REPORTS o esta vacia.",
                }
            where_clauses = []
            params = []
            if search:
                pattern = "%" + search + "%"
                text_cols = [c for c in columns if any(k in c.upper() for k in ("NAME", "REPORT", "NM_", "ID_"))]
                if text_cols:
                    col_searches = [c + " LIKE ?" for c in text_cols]
                    where_clauses.append("(" + " OR ".join(col_searches) + ")")
                    params.extend([pattern] * len(text_cols))
            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            sel = ", ".join(columns)
            sql = "SELECT TOP " + str(limit) + " " + sel + " FROM M4SCO_REPORTS " + where + " ORDER BY SCO_ID_REPORT"
            cursor.execute(sql, *params)
            rows = cursor.fetchall()
            return {
                "status": "success",
                "count": len(rows),
                "columns_available": columns,
                "reports": [_row_to_dict(r, columns) for r in rows],
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_rows(id_report=None, id_body=None, search=None, limit=200):
    """Lista las filas de recibos de nomina desde M4SCO_ROWS.

    Args:
        id_report: Filtrar por ID de informe (opcional).
        id_body:   Filtrar por ID de cuerpo/seccion (opcional, requiere id_report).
        search:    Buscar por texto en nombre de fila o ID de concepto (opcional).
        limit:     Maximo de resultados (default 200).

    Returns:
        dict con status, conteo y lista de filas.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            columns = _discover_columns(cursor, "M4SCO_ROWS")
            if not columns:
                return {
                    "status": "error",
                    "message": "No se encontro la tabla M4SCO_ROWS o esta vacia.",
                }
            where_clauses = []
            params = []
            if id_report:
                where_clauses.append("SCO_ID_REPORT = ?")
                params.append(id_report)
            if id_body:
                where_clauses.append("SCO_ID_BODY = ?")
                params.append(id_body)
            if search:
                pattern = "%" + search + "%"
                search_in = ("SCO_NM_ROW", "SCO_NM_ROWESP", "SCO_NM_ROWENG",
                             "ID_PAYROLL_ITEM", "ID_T3_PI", "SCO_ID_NODE")
                text_cols = [c for c in search_in if c in columns]
                if text_cols:
                    col_searches = [c + " LIKE ?" for c in text_cols]
                    where_clauses.append("(" + " OR ".join(col_searches) + ")")
                    params.extend([pattern] * len(text_cols))
            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            sel = ", ".join(columns)
            sql = ("SELECT TOP " + str(limit) + " " + sel + " FROM M4SCO_ROWS " + where +
                   " ORDER BY SCO_ID_REPORT, SCO_ID_BODY, SCO_ORDER, SCO_ID_ROW")
            cursor.execute(sql, *params)
            rows = cursor.fetchall()
            return {
                "status": "success",
                "count": len(rows),
                "columns_available": columns,
                "rows": [_row_to_dict(r, columns) for r in rows],
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_row_detail(id_report, id_body, id_row):
    """Obtiene el detalle completo de una fila: M4SCO_ROWS + M4SCO_ROWS_DETAIL + celdas.

    Args:
        id_report: ID del informe.
        id_body:   ID del cuerpo/seccion.
        id_row:    ID numerico de la fila.

    Returns:
        dict con todos los campos de la fila, su detalle de totalizacion y sus celdas.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # M4SCO_ROWS
            row_cols = _discover_columns(cursor, "M4SCO_ROWS")
            if not row_cols:
                return {"status": "error", "message": "No se encontro la tabla M4SCO_ROWS."}
            sel = ", ".join(row_cols)
            cursor.execute(
                "SELECT " + sel + " FROM M4SCO_ROWS "
                "WHERE SCO_ID_REPORT = ? AND SCO_ID_BODY = ? AND SCO_ID_ROW = ?",
                id_report, id_body, id_row
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "status": "not_found",
                    "message": (
                        "No se encontro la fila " + str(id_row) +
                        " en informe '" + str(id_report) +
                        "', cuerpo '" + str(id_body) + "'"
                    ),
                }

            result = {"status": "success", "row": _row_to_dict(row, row_cols)}

            # M4SCO_ROWS_DETAIL
            det_cols = _discover_columns(cursor, "M4SCO_ROWS_DETAIL")
            if det_cols:
                sel = ", ".join(det_cols)
                cursor.execute(
                    "SELECT " + sel + " FROM M4SCO_ROWS_DETAIL "
                    "WHERE SCO_ID_REPORT = ? AND SCO_ID_BODY = ? AND SCO_ID_ROW = ?",
                    id_report, id_body, id_row
                )
                det_row = cursor.fetchone()
                result["rows_detail"] = _row_to_dict(det_row, det_cols) if det_row else None

            # M4SCO_ROW_COL_DEF (celdas de esta fila)
            cell_cols = _discover_columns(cursor, "M4SCO_ROW_COL_DEF")
            if cell_cols:
                sel = ", ".join(cell_cols)
                cursor.execute(
                    "SELECT " + sel + " FROM M4SCO_ROW_COL_DEF "
                    "WHERE SCO_ID_REPORT = ? AND SCO_ID_BODY = ? AND SCO_ID_ROW = ? "
                    "ORDER BY SCO_ID_COLUMN",
                    id_report, id_body, id_row
                )
                cells = cursor.fetchall()
                result["cells"] = [_row_to_dict(c, cell_cols) for c in cells]
                result["cell_count"] = len(result["cells"])

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_cells(id_report, id_body, id_row=None, search=None, limit=500):
    """Lista las celdas (definiciones fila x columna) desde M4SCO_ROW_COL_DEF.

    Args:
        id_report: ID del informe.
        id_body:   ID del cuerpo/seccion.
        id_row:    Filtrar por fila especifica (opcional).
        search:    Buscar por texto en etiqueta, nodo o item (opcional).
        limit:     Maximo de resultados (default 500).

    Returns:
        dict con status, conteo y lista de celdas.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            columns = _discover_columns(cursor, "M4SCO_ROW_COL_DEF")
            if not columns:
                return {
                    "status": "error",
                    "message": "No se encontro la tabla M4SCO_ROW_COL_DEF o esta vacia.",
                }
            where_clauses = ["SCO_ID_REPORT = ?", "SCO_ID_BODY = ?"]
            params = [id_report, id_body]
            if id_row is not None:
                where_clauses.append("SCO_ID_ROW = ?")
                params.append(id_row)
            if search:
                pattern = "%" + search + "%"
                search_in = ("SCO_LABEL", "SCO_LABELESP", "SCO_LABELENG",
                             "SCO_ID_NODE", "SCO_ID_ITEM",
                             "SFR_ID_SOURCE_NODE", "SFR_ID_SOURCE_ITEM")
                text_cols = [c for c in search_in if c in columns]
                if text_cols:
                    col_searches = [c + " LIKE ?" for c in text_cols]
                    where_clauses.append("(" + " OR ".join(col_searches) + ")")
                    params.extend([pattern] * len(text_cols))
            where = "WHERE " + " AND ".join(where_clauses)
            sel = ", ".join(columns)
            sql = ("SELECT TOP " + str(limit) + " " + sel + " FROM M4SCO_ROW_COL_DEF " + where +
                   " ORDER BY SCO_ID_ROW, SCO_ID_COLUMN")
            cursor.execute(sql, *params)
            rows = cursor.fetchall()
            return {
                "status": "success",
                "count": len(rows),
                "columns_available": columns,
                "cells": [_row_to_dict(r, columns) for r in rows],
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta el layout de salida a papel (recibo de nomina) de PeopleNet."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--list-reports", action="store_true",
                            help="Listar informes/recibos disponibles (M4SCO_REPORTS)")
    mode_group.add_argument("--list-rows", action="store_true",
                            help="Listar filas de recibos (M4SCO_ROWS)")
    mode_group.add_argument("--row", action="store_true",
                            help="Detalle completo de una fila (requiere --report, --body, --row-id)")
    mode_group.add_argument("--list-cells", action="store_true",
                            help="Listar celdas fila x columna (requiere --report y --body)")

    parser.add_argument("--report", help="ID del informe (SCO_ID_REPORT)")
    parser.add_argument("--body", help="ID del cuerpo/seccion (SCO_ID_BODY)")
    parser.add_argument("--row-id", type=int, dest="row_id", help="ID numerico de la fila (SCO_ID_ROW)")
    parser.add_argument("--search", help="Buscar por texto")
    parser.add_argument("--limit", type=int, default=200, help="Maximo de resultados (default 200)")

    args = parser.parse_args()

    if args.list_reports:
        result = list_reports(search=args.search, limit=args.limit)
    elif args.list_rows:
        result = list_rows(id_report=args.report, id_body=args.body, search=args.search, limit=args.limit)
    elif args.row:
        if not (args.report and args.body and args.row_id is not None):
            parser.error("--row requiere --report, --body y --row-id")
        result = get_row_detail(args.report, args.body, args.row_id)
    elif args.list_cells:
        if not (args.report and args.body):
            parser.error("--list-cells requiere --report y --body")
        result = list_cells(
            id_report=args.report, id_body=args.body, id_row=args.row_id,
            search=args.search, limit=args.limit,
        )

    print(json.dumps(result, indent=2, default=str))
