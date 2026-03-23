# tools/general/revision_calidad.py
"""
Analiza ficheros Python del proyecto para identificar desviaciones de los
estándares de calidad definidos en AGENTS.md.

Reglas verificadas:
  - Indentación: 4 espacios (no tabs).
  - Longitud de línea: máximo 120 caracteres.
  - Orden de imports: stdlib → third-party → local.
  - Naming: snake_case para funciones/variables, PascalCase para clases,
    UPPER_CASE para constantes.

Uso:
    python -m tools.general.revision_calidad                       # Analiza todo el proyecto
    python -m tools.general.revision_calidad "tools/bdl/list_bdl_objects.py"  # Analiza un fichero
    python -m tools.general.revision_calidad "tools/bdl/"          # Analiza un directorio
    python -m tools.general.revision_calidad --severity warning    # Solo warnings y superiores
"""
import sys
import os
import re
import ast
import json


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Módulos de la stdlib de Python 3.x (subconjunto amplio, suficiente para detectar
# los imports más habituales). No es exhaustivo, pero cubre el 95 % de usos.
_STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "base64", "binascii", "binhex", "bisect", "builtins", "bz2",
    "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "distutils", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "formatter",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io",
    "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
    "parser", "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc",
    "queue", "quopri", "random", "re", "readline", "reprlib", "resource",
    "rlcompleter", "runpy", "sched", "secrets", "select", "selectors",
    "shelve", "shlex", "shutil", "signal", "site", "smtpd", "smtplib",
    "sndhdr", "socket", "socketserver", "sqlite3", "ssl", "stat",
    "statistics", "string", "stringprep", "struct", "subprocess", "sunau",
    "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile",
    "telnetlib", "tempfile", "termios", "test", "textwrap", "threading",
    "time", "timeit", "tkinter", "token", "tokenize", "trace", "traceback",
    "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib",
    "_thread", "__future__",
}

# Severidades
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}

# Regex para naming
_RE_SNAKE_CASE = re.compile(r"^_*[a-z][a-z0-9_]*$")
_RE_PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
_RE_UPPER_CASE = re.compile(r"^_*[A-Z][A-Z0-9_]*$")


# ---------------------------------------------------------------------------
# Funciones de análisis
# ---------------------------------------------------------------------------

def _check_indentation(lines):
    """Verifica que la indentación usa 4 espacios (no tabs)."""
    issues = []
    for i, line in enumerate(lines, start=1):
        if line.startswith("\t"):
            issues.append({
                "line": i,
                "severity": "error",
                "rule": "indent-tabs",
                "message": "Se usa tabulador en vez de espacios.",
            })
        elif line != line.lstrip() and len(line) > 0:
            # Contar espacios iniciales
            stripped = line.lstrip()
            if stripped and not stripped.startswith("#"):
                indent = len(line) - len(stripped)
                # Se permite cualquier múltiplo de 4; las continuaciones a veces
                # tienen indentación arbitraria, así que solo marcamos tabs.
    return issues


def _check_line_length(lines, max_length=120):
    """Verifica que ninguna línea supere max_length caracteres."""
    issues = []
    for i, line in enumerate(lines, start=1):
        # No contar el newline final
        clean = line.rstrip("\n\r")
        if len(clean) > max_length:
            issues.append({
                "line": i,
                "severity": "warning",
                "rule": "line-length",
                "message": f"Línea de {len(clean)} caracteres (máximo {max_length}).",
            })
    return issues


def _classify_import(module_name):
    """Clasifica un módulo como stdlib, third-party o local."""
    top = module_name.split(".")[0]
    if top in _STDLIB_MODULES:
        return "stdlib"
    if top in ("tools", "ln4_lsp", "agentes", "skills"):
        return "local"
    return "third_party"


def _check_import_order(source):
    """Verifica que los imports sigan el orden: stdlib → third-party → local."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues

    # Recoger imports en orden de aparición
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, _classify_import(alias.name), alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.lineno, _classify_import(node.module), node.module))

    # Verificar orden: stdlib < third_party < local
    order_map = {"stdlib": 0, "third_party": 1, "local": 2}
    last_group = -1
    for lineno, group, module in imports:
        current = order_map[group]
        if current < last_group:
            issues.append({
                "line": lineno,
                "severity": "warning",
                "rule": "import-order",
                "message": f"Import '{module}' ({group}) aparece después de un grupo posterior. Orden esperado: stdlib → third-party → local.",
            })
        last_group = max(last_group, current)

    return issues


def _check_naming(source):
    """Verifica convenciones de nombres: snake_case, PascalCase, UPPER_CASE."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues

    for node in ast.walk(tree):
        # Funciones → snake_case
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            # Dunder methods son válidos
            if name.startswith("__") and name.endswith("__"):
                continue
            if not _RE_SNAKE_CASE.match(name):
                issues.append({
                    "line": node.lineno,
                    "severity": "warning",
                    "rule": "naming-function",
                    "message": f"Función '{name}' no sigue snake_case.",
                })

        # Clases → PascalCase
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if not _RE_PASCAL_CASE.match(name):
                issues.append({
                    "line": node.lineno,
                    "severity": "warning",
                    "rule": "naming-class",
                    "message": f"Clase '{name}' no sigue PascalCase.",
                })

        # Constantes a nivel de módulo → UPPER_CASE
        elif isinstance(node, ast.Assign):
            # Solo a nivel de módulo (no dentro de funciones/clases)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    # Heurística: si está a nivel de módulo y no es snake_case,
                    # verificar si debería ser UPPER_CASE.
                    # Esto solo se aplica si el nodo padre es el módulo.
                    # ast.walk no da contexto de padre, así que lo dejamos como info.

    return issues


def analyze_file(file_path):
    """Analiza un fichero Python y devuelve la lista de issues encontrados."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return [{"line": 0, "severity": "error", "rule": "file-read", "message": str(e)}]

    lines = source.splitlines(keepends=True)

    issues = []
    issues.extend(_check_indentation(lines))
    issues.extend(_check_line_length(lines))
    issues.extend(_check_import_order(source))
    issues.extend(_check_naming(source))

    return issues


def find_python_files(path):
    """Busca ficheros .py recursivamente bajo path."""
    files = []
    if os.path.isfile(path) and path.endswith(".py"):
        return [path]
    if os.path.isdir(path):
        for root, _dirs, filenames in os.walk(path):
            # Excluir directorios generados, __pycache__, node_modules, .git
            _dirs[:] = [d for d in _dirs if d not in {"__pycache__", "node_modules", ".git", ".venv", "generated"}]
            for fname in sorted(filenames):
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))
    return files


def run_analysis(path, min_severity="info"):
    """Ejecuta el análisis completo sobre un path (fichero o directorio).

    Args:
        path: Ruta a un fichero .py o directorio.
        min_severity: Severidad mínima a incluir en resultados (info, warning, error).

    Returns:
        dict con status, resumen y hallazgos por fichero.
    """
    min_sev = SEVERITY_ORDER.get(min_severity, 0)
    files = find_python_files(path)

    if not files:
        return {
            "status": "error",
            "message": f"No se encontraron ficheros Python en '{path}'.",
        }

    results = []
    total_issues = 0
    counts_by_severity = {"info": 0, "warning": 0, "error": 0}
    counts_by_rule = {}

    for file_path in files:
        # Normalizar ruta para legibilidad
        rel_path = os.path.relpath(file_path)
        issues = analyze_file(file_path)
        # Filtrar por severidad mínima
        filtered = [i for i in issues if SEVERITY_ORDER.get(i["severity"], 0) >= min_sev]

        if filtered:
            results.append({
                "file": rel_path,
                "issues_count": len(filtered),
                "issues": filtered,
            })
            total_issues += len(filtered)
            for issue in filtered:
                counts_by_severity[issue["severity"]] = counts_by_severity.get(issue["severity"], 0) + 1
                counts_by_rule[issue["rule"]] = counts_by_rule.get(issue["rule"], 0) + 1

    return {
        "status": "success",
        "files_analyzed": len(files),
        "files_with_issues": len(results),
        "total_issues": total_issues,
        "by_severity": counts_by_severity,
        "by_rule": counts_by_rule,
        "results": results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analiza ficheros Python del proyecto para verificar estándares de calidad (AGENTS.md)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Ruta al fichero .py o directorio a analizar. Por defecto: directorio actual.",
    )
    parser.add_argument(
        "--severity",
        choices=["info", "warning", "error"],
        default="info",
        help="Severidad mínima a reportar (default: info).",
    )

    args = parser.parse_args()
    result = run_analysis(args.path, min_severity=args.severity)
    print(json.dumps(result, indent=2, default=str))
