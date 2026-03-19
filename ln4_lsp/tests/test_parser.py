"""
test_parser.py — Validacion del parser ANTLR4 para LN4 contra las 13 muestras.

Uso:
    python -m ln4_lsp.tests.test_parser             # Ejecutar todas
    python -m ln4_lsp.tests.test_parser 01           # Ejecutar solo la muestra 01
    python -m ln4_lsp.tests.test_parser 05 09 13     # Ejecutar varias

El script parsea cada .ln4, reporta errores sintacticos, y muestra el parse tree.
Exit code 0 = todas pasaron, 1 = hubo errores.
"""

import sys
import os
import glob

# Ajustar sys.path para importar desde la raiz del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from ln4_lsp.generated.LN4Lexer import LN4Lexer
from ln4_lsp.generated.LN4Parser import LN4Parser


class CollectingErrorListener(ErrorListener):
    """Recopila errores sintacticos en lugar de imprimirlos a stderr."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append({
            "line": line,
            "column": column,
            "msg": msg,
            "symbol": str(offendingSymbol) if offendingSymbol else None,
        })


def parse_file(filepath):
    """
    Parsea un archivo .ln4 y retorna (tree, errors, parser).

    - tree: parse tree (o None si fallo fatalmente)
    - errors: lista de dicts {line, column, msg, symbol}
    - parser: instancia del parser (para tree.toStringTree)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    input_stream = InputStream(code)
    lexer = LN4Lexer(input_stream)
    lexer.removeErrorListeners()
    lexer_errors = CollectingErrorListener()
    lexer.addErrorListener(lexer_errors)

    token_stream = CommonTokenStream(lexer)
    parser = LN4Parser(token_stream)
    parser.removeErrorListeners()
    parser_errors = CollectingErrorListener()
    parser.addErrorListener(parser_errors)

    tree = parser.program()

    all_errors = lexer_errors.errors + parser_errors.errors
    return tree, all_errors, parser


def format_tree(tree, parser, indent=0):
    """Formato legible del parse tree (recursivo, indentado)."""
    if tree is None:
        return ""

    # Terminal node
    if tree.getChildCount() == 0:
        token = tree.getSymbol()
        token_name = parser.symbolicNames[token.type] if token.type >= 0 else "EOF"
        text = token.text.replace("\n", "\\n").replace("\r", "\\r")
        return " " * indent + f"{token_name}: {text!r}"

    # Rule node
    rule_name = parser.ruleNames[tree.getRuleIndex()]
    lines = [" " * indent + f"({rule_name}"]
    for i in range(tree.getChildCount()):
        child = tree.getChild(i)
        lines.append(format_tree(child, parser, indent + 2))
    lines.append(" " * indent + ")")
    return "\n".join(lines)


def run_tests(sample_filters=None):
    """
    Ejecuta el parser contra todas las muestras (o las filtradas).

    Retorna: (total, passed, failed) como conteo.
    """
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    pattern = os.path.join(samples_dir, "*.ln4")
    sample_files = sorted(glob.glob(pattern))

    if not sample_files:
        print(f"ERROR: No se encontraron archivos .ln4 en {samples_dir}")
        return 0, 0, 0

    # Filtrar si se pidieron muestras especificas
    if sample_filters:
        filtered = []
        for f in sample_files:
            basename = os.path.basename(f)
            for filt in sample_filters:
                if filt in basename:
                    filtered.append(f)
                    break
        sample_files = filtered

    total = len(sample_files)
    passed = 0
    failed = 0

    print(f"{'='*70}")
    print(f" LN4 Parser Test Suite — {total} muestras")
    print(f"{'='*70}\n")

    for filepath in sample_files:
        name = os.path.basename(filepath)
        print(f"--- {name} ---")

        try:
            tree, errors, parser = parse_file(filepath)

            if errors:
                failed += 1
                print(f"  FAIL: {len(errors)} error(es)")
                for err in errors:
                    print(f"    L{err['line']}:{err['column']} — {err['msg']}")
            else:
                passed += 1
                print(f"  OK")

            # Mostrar arbol (compacto para los que pasan, completo para los que fallan)
            if errors:
                print(f"\n  Parse tree (parcial):")
                tree_str = format_tree(tree, parser, indent=4)
                # Limitar a 40 lineas para no saturar
                lines = tree_str.split("\n")
                for line in lines[:40]:
                    print(line)
                if len(lines) > 40:
                    print(f"    ... ({len(lines) - 40} lineas mas)")
            print()

        except Exception as e:
            failed += 1
            print(f"  EXCEPTION: {e}\n")

    print(f"{'='*70}")
    print(f" Resultado: {passed}/{total} pasaron, {failed}/{total} fallaron")
    print(f"{'='*70}")

    return total, passed, failed


def main():
    filters = sys.argv[1:] if len(sys.argv) > 1 else None
    total, passed, failed = run_tests(filters)

    if total == 0:
        sys.exit(2)
    elif failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
