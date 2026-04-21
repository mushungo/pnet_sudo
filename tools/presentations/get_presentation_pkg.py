# tools/presentations/get_presentation_pkg.py
"""
Extrae el paquete OBL compilado de una presentación de PeopleNet.

El código compilado de una presentación se almacena distribuido en 9 tablas físicas
(M4RPT_PRESENT_PKG + M4RPT_PRESENT_PKG1 a M4RPT_PRESENT_PKG8). Este script
recupera los metadatos de compilación y, opcionalmente, exporta los binarios a disco.

Uso:
    python -m tools.presentations.get_presentation_pkg <ID_PRESENTATION>
    python -m tools.presentations.get_presentation_pkg <ID_PRESENTATION> --export-dir ./output
    python -m tools.presentations.get_presentation_pkg <ID_PRESENTATION> --lang esp
    python -m tools.presentations.get_presentation_pkg <ID_PRESENTATION> --metadata-only
"""
import sys
import os
import json
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection


# Mapeo de sufijo de tabla → nombre de columna → idioma/propósito
PKG_TABLE_MAP = [
    ("M4RPT_PRESENT_PKG",  None,          "metadata"),   # Solo fechas, sin binario
    ("M4RPT_PRESENT_PKG1", "XPACKAGE",    "neutral"),    # Principal (language-neutral)
    ("M4RPT_PRESENT_PKG2", "PKG_LNGENG",  "eng"),
    ("M4RPT_PRESENT_PKG3", "PKG_LNGESP",  "esp"),
    ("M4RPT_PRESENT_PKG4", "PKG_LNGFRA",  "fra"),
    ("M4RPT_PRESENT_PKG5", "PKG_LNGGER",  "ger"),
    ("M4RPT_PRESENT_PKG6", "PKG_LNGBRA",  "bra"),
    ("M4RPT_PRESENT_PKG7", "PKG_LNGITA",  "ita"),
    ("M4RPT_PRESENT_PKG8", "PKG_LNGGEN",  "gen"),
]

LANG_TO_TABLE = {entry[2]: entry for entry in PKG_TABLE_MAP if entry[1] is not None}


def get_presentation_pkg(id_presentation, lang=None, export_dir=None, metadata_only=False):
    """Obtiene los metadatos del paquete OBL compilado de una presentación.

    Opcionalmente exporta los binarios a disco (uno por variante de idioma).

    Args:
        id_presentation: Identificador de la presentación (ej: SCO_EMPLOYEE).
        lang: Si se especifica, solo recupera esa variante de idioma (neutral/eng/esp/fra/ger/bra/ita/gen).
        export_dir: Directorio de destino para exportar los binarios (.bin).
        metadata_only: Si True, solo recupera fechas de M4RPT_PRESENT_PKG (sin binarios).

    Returns:
        dict con metadatos y resumen de tamaños por variante.
    """
    if not id_presentation:
        return {"status": "error", "message": "id_presentation es requerido."}

    id_presentation = id_presentation.strip()

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Metadatos de compilación (M4RPT_PRESENT_PKG — solo fechas)
            cursor.execute(
                "SELECT ID_PRESENTATION, DT_CREATE, DT_LAST_COMPILE, "
                "DT_LAST_UPDATE, DT_LAST_UPDATE1 "
                "FROM M4RPT_PRESENT_PKG "
                "WHERE ID_PRESENTATION = ?",
                id_presentation
            )
            meta_row = cursor.fetchone()
            if not meta_row:
                return {
                    "status": "not_found",
                    "message": f"No se encontró paquete compilado para '{id_presentation}'. "
                               "La presentación puede no haber sido compilada todavía."
                }

            result = {
                "id_presentation": meta_row.ID_PRESENTATION,
                "compilation": {
                    "dt_create": str(meta_row.DT_CREATE) if meta_row.DT_CREATE else None,
                    "dt_last_compile": str(meta_row.DT_LAST_COMPILE) if meta_row.DT_LAST_COMPILE else None,
                    "dt_last_update": str(meta_row.DT_LAST_UPDATE) if meta_row.DT_LAST_UPDATE else None,
                    "dt_last_update1": str(meta_row.DT_LAST_UPDATE1) if meta_row.DT_LAST_UPDATE1 else None,
                },
                "packages": {}
            }

            if metadata_only:
                return result

            # 2. Binarios por variante de idioma
            tables_to_check = [LANG_TO_TABLE[lang]] if lang and lang in LANG_TO_TABLE else [
                e for e in PKG_TABLE_MAP if e[1] is not None
            ]

            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            for table_name, col_name, lang_key in tables_to_check:
                cursor.execute(
                    f"SELECT {col_name} FROM {table_name} WHERE ID_PRESENTATION = ?",
                    id_presentation
                )
                row = cursor.fetchone()
                blob = getattr(row, col_name, None) if row else None

                pkg_info = {
                    "table": table_name,
                    "column": col_name,
                    "lang": lang_key,
                    "present": blob is not None,
                    "size_bytes": len(blob) if blob else 0,
                }

                if blob and export_dir:
                    filename = f"{id_presentation}_{lang_key}.bin"
                    filepath = os.path.join(export_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(blob)
                    pkg_info["exported_to"] = filepath

                result["packages"][lang_key] = pkg_info

            total = sum(p["size_bytes"] for p in result["packages"].values())
            result["total_size_bytes"] = total
            result["packages_present"] = sum(1 for p in result["packages"].values() if p["present"])

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrae el paquete OBL compilado de una presentación de PeopleNet."
    )
    parser.add_argument("id_presentation", help="Identificador de la presentación (ej: SCO_EMPLOYEE)")
    parser.add_argument(
        "--lang",
        choices=list(LANG_TO_TABLE.keys()),
        help="Exportar solo la variante de idioma especificada"
    )
    parser.add_argument(
        "--export-dir",
        metavar="DIR",
        help="Directorio donde exportar los binarios (.bin)"
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Solo mostrar metadatos de compilación, sin leer binarios"
    )
    args = parser.parse_args()

    result = get_presentation_pkg(
        args.id_presentation,
        lang=args.lang,
        export_dir=args.export_dir,
        metadata_only=args.metadata_only,
    )
    print(json.dumps(result, indent=2, default=str))
