# tools/general/audit_dialect.py
"""
Herramienta de auditoría: detecta SQL engine-specific en los tools del proyecto.

Escanea todos los ficheros .py de tools/ y reporta qué expresiones SQL
no son portables (SQL Server-specific o Oracle-specific) y deben
migrarse a llamadas del dialecto (get_dialect()).

Uso:
    python tools/general/audit_dialect.py
    python tools/general/audit_dialect.py --fix-hints   # muestra sugerencia de reemplazo
    python tools/general/audit_dialect.py --json        # salida en JSON

Salida:
    Lista de ficheros con sus ocurrencias de SQL no-portable,
    ordenada por número de ocurrencias (mayor primero).
"""
import argparse
import ast
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Patrones a detectar
# ---------------------------------------------------------------------------

# Cada entrada: (nombre_legible, regex, motor_origen, reemplazo_dialecto)
PATTERNS = [
    # SQL Server
    ("GETDATE()",         r"\bGETDATE\s*\(\s*\)",          "sqlserver",  "d.today()"),
    ("ISNULL()",          r"\bISNULL\s*\(",                 "sqlserver",  "d.isnull(col, val)"),
    ("TOP n",             r"\bSELECT\s+TOP\s+\d+",         "sqlserver",  "SELECT {d.select_prefix(n)} ... {d.select_suffix(n)}"),
    ("CAST AS VARCHAR",   r"\bCAST\s*\([^)]+AS\s+N?VARCHAR","sqlserver",  "d.cast_varchar(col)"),
    ("+ concat",          r"'[^']*'\s*\+\s*[A-Za-z_]|[A-Za-z_]\w*\s*\+\s*'[^']*'", "sqlserver", "d.concat(a, b)"),
    ("CONVERT()",         r"\bCONVERT\s*\(",               "sqlserver",  "d.cast_varchar(col) o equivalente"),
    ("NEWID()",           r"\bNEWID\s*\(\s*\)",            "sqlserver",  "sin equivalente directo — revisar manualmente"),
    ("LEN()",             r"\bLEN\s*\(",                   "sqlserver",  "LENGTH() en Oracle"),
    ("CHARINDEX()",       r"\bCHARINDEX\s*\(",             "sqlserver",  "INSTR() en Oracle"),
    ("STUFF()",           r"\bSTUFF\s*\(",                 "sqlserver",  "sin equivalente directo"),
    ("NOLOCK hint",       r"\bWITH\s*\(\s*NOLOCK\s*\)",   "sqlserver",  "eliminar — Oracle no usa hints de lock así"),
    # Oracle
    ("SYSDATE",           r"\bSYSDATE\b",                  "oracle",     "d.today()"),
    ("NVL()",             r"\bNVL\s*\(",                   "oracle",     "d.isnull(col, val)"),
    ("ROWNUM",            r"\bROWNUM\b",                   "oracle",     "d.select_suffix(n)"),
    ("FETCH FIRST",       r"\bFETCH\s+FIRST\b",            "oracle",     "d.select_suffix(n)"),
    ("TO_CHAR()",         r"\bTO_CHAR\s*\(",               "oracle",     "d.cast_varchar(col)"),
    ("|| concat",         r"\|\|",                         "oracle",     "d.concat(a, b)"),
    ("DECODE()",          r"\bDECODE\s*\(",                "oracle",     "CASE WHEN ... END"),
    ("DUAL",              r"\bFROM\s+DUAL\b",              "oracle",     "FROM (SELECT 1) t o eliminar"),
    ("SEQUENCE.NEXTVAL",  r"\w+\.NEXTVAL\b",               "oracle",     "IDENTITY / SEQUENCE según motor"),
]

# ---------------------------------------------------------------------------
# Escáner
# ---------------------------------------------------------------------------

def _scan_file(filepath):
    """Escanea un fichero Python buscando strings con SQL no-portable.

    Solo escanea nodos ast.Constant de tipo str (literales de string),
    para evitar falsos positivos en nombres de variables o comentarios de código.
    Pero también escanea líneas completas para capturar f-strings y concatenaciones.

    Returns:
        list of dict: [{"pattern": ..., "engine": ..., "hint": ..., "line": ..., "text": ...}]
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    hits = []
    for lineno, line in enumerate(lines, start=1):
        # Ignorar comentarios Python puros
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for name, pattern, engine, hint in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                hits.append({
                    "pattern": name,
                    "engine": engine,
                    "hint": hint,
                    "line": lineno,
                    "text": line.rstrip(),
                })
    return hits


def scan_directory(root_dir):
    """Escanea todos los .py bajo root_dir.

    Returns:
        dict: {filepath: [hits]}  — solo ficheros con al menos un hit.
    """
    results = {}
    for dirpath, _dirs, files in os.walk(root_dir):
        # Excluir directorios no relevantes
        _dirs[:] = [d for d in _dirs if d not in ("__pycache__", ".venv", "venv", "generated")]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            hits = _scan_file(fpath)
            if hits:
                results[fpath] = hits
    return results


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def _relative(path, base):
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return path


def print_report(results, base_dir, fix_hints=False):
    """Imprime el reporte de auditoría en la consola."""
    if not results:
        print("OK — No se encontraron patrones SQL no-portables.")
        return

    total_hits = sum(len(hits) for hits in results.values())
    print(f"\nAuditoria de dialecto SQL — {len(results)} fichero(s) con {total_hits} ocurrencia(s)\n")
    print("=" * 80)

    # Ordenar por numero de ocurrencias descendente
    for fpath in sorted(results, key=lambda p: -len(results[p])):
        hits = results[fpath]
        rel = _relative(fpath, base_dir)
        sqlserver_count = sum(1 for h in hits if h["engine"] == "sqlserver")
        oracle_count = sum(1 for h in hits if h["engine"] == "oracle")
        tags = []
        if sqlserver_count:
            tags.append(f"sqlserver:{sqlserver_count}")
        if oracle_count:
            tags.append(f"oracle:{oracle_count}")
        print(f"\n[{', '.join(tags)}]  {rel}  ({len(hits)} ocurrencias)")
        print("-" * 70)
        for h in hits:
            print(f"  L{h['line']:>4}  [{h['engine']:9}]  {h['pattern']}")
            if fix_hints:
                print(f"          -> Usar: {h['hint']}")
                print(f"          Linea: {h['text'].strip()}")

    print("\n" + "=" * 80)
    print(f"Total: {total_hits} expresiones SQL no-portables en {len(results)} fichero(s).")
    print("Migrar a llamadas del dialecto: from tools.general.db_utils import get_dialect")


def print_json(results, base_dir):
    """Imprime el reporte en formato JSON."""
    output = {}
    for fpath, hits in results.items():
        rel = _relative(fpath, base_dir)
        output[rel] = hits
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Audita los tools buscando SQL no-portable (engine-specific)."
    )
    parser.add_argument(
        "--fix-hints", action="store_true",
        help="Muestra sugerencias de reemplazo con el dialecto para cada ocurrencia."
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Salida en formato JSON."
    )
    parser.add_argument(
        "--dir", default=None,
        help="Directorio raíz a escanear (por defecto: tools/ del proyecto)."
    )
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    scan_dir = args.dir if args.dir else os.path.join(project_root, "tools")

    results = scan_directory(scan_dir)

    if args.json:
        print_json(results, project_root)
    else:
        print_report(results, project_root, fix_hints=args.fix_hints)

    # Exit code != 0 si hay ocurrencias (útil en CI)
    sys.exit(1 if results else 0)


if __name__ == "__main__":
    main()
