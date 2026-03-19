"""
test_parser_real.py — Prueba el parser LN4 contra reglas reales del repositorio PeopleNet.

Extrae un lote diverso de reglas LN4 desde M4RCH_RULES3 y las parsea con ANTLR4.
Reporta estadisticas de exito/fallo y los errores mas comunes.

Uso:
    python -m ln4_lsp.tests.test_parser_real              # 100 reglas diversas
    python -m ln4_lsp.tests.test_parser_real --count 500  # 500 reglas
    python -m ln4_lsp.tests.test_parser_real --all        # todas las reglas LN4
    python -m ln4_lsp.tests.test_parser_real --dump-errors # guardar reglas fallidas a disco
"""

import sys
import os
import argparse
from collections import Counter

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from ln4_lsp.generated.LN4Lexer import LN4Lexer
from ln4_lsp.generated.LN4Parser import LN4Parser
from tools.general.db_utils import db_connection


class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append({
            "line": line,
            "column": column,
            "msg": msg,
        })


def parse_code(code):
    """Parsea codigo LN4 y retorna lista de errores (vacia = exito)."""
    input_stream = InputStream(code)
    lexer = LN4Lexer(input_stream)
    lexer.removeErrorListeners()
    lexer_err = CollectingErrorListener()
    lexer.addErrorListener(lexer_err)

    tokens = CommonTokenStream(lexer)
    parser = LN4Parser(tokens)
    parser.removeErrorListeners()
    parser_err = CollectingErrorListener()
    parser.addErrorListener(parser_err)

    parser.program()
    return lexer_err.errors + parser_err.errors


def fetch_rules(cursor, count=None):
    """
    Extrae reglas LN4 reales. Si count es None, extrae todas.
    Retorna lista de dicts {id_ti, id_item, code}.
    """
    # Reglas LN4 con codigo no vacio, diversidad por tamano
    query = """
        SELECT r.ID_TI, r.ID_ITEM,
               CAST(r3.SOURCE_CODE AS VARCHAR(MAX)) AS code,
               DATALENGTH(r3.SOURCE_CODE) AS code_len
        FROM M4RCH_RULES r
        JOIN M4RCH_RULES3 r3
            ON r.ID_TI = r3.ID_TI
            AND r.ID_ITEM = r3.ID_ITEM
            AND r.DT_START = r3.DT_START
            AND r.ID_RULE = r3.ID_RULE
        WHERE r.ID_CODE_TYPE = 1
            AND DATALENGTH(r3.SOURCE_CODE) > 0
    """

    if count is not None:
        # Diverse sample: take from different size buckets
        query += " ORDER BY DATALENGTH(r3.SOURCE_CODE)"
        cursor.execute(query)
        all_rows = cursor.fetchall()
        total = len(all_rows)
        if total <= count:
            return [{"id_ti": r[0], "id_item": r[1], "code": r[2], "code_len": r[3]} for r in all_rows]
        # Evenly sample across the sorted list
        step = total / count
        indices = [int(i * step) for i in range(count)]
        return [{"id_ti": all_rows[i][0], "id_item": all_rows[i][1], "code": all_rows[i][2], "code_len": all_rows[i][3]} for i in indices]
    else:
        cursor.execute(query)
        return [{"id_ti": r[0], "id_item": r[1], "code": r[2], "code_len": r[3]} for r in cursor.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="Test LN4 parser against real DB rules")
    parser.add_argument("--count", type=int, default=100, help="Number of rules to test (default: 100)")
    parser.add_argument("--all", action="store_true", help="Test ALL LN4 rules")
    parser.add_argument("--dump-errors", action="store_true", help="Dump failed rules to ln4_lsp/tests/failed/")
    args = parser.parse_args()

    count = None if args.all else args.count

    print("Conectando a la base de datos...")
    with db_connection() as conn:
        cursor = conn.cursor()
        print(f"Extrayendo reglas LN4 (count={'ALL' if count is None else count})...")
        rules = fetch_rules(cursor, count)

    total = len(rules)
    print(f"Obtenidas {total} reglas. Parseando...\n")

    passed = 0
    failed = 0
    error_msgs = Counter()
    failed_rules = []

    for i, rule in enumerate(rules):
        code = rule["code"]
        if not code or not code.strip():
            passed += 1
            continue

        errors = parse_code(code)

        if errors:
            failed += 1
            # Contar el primer error de cada regla (el mas significativo)
            first_msg = errors[0]["msg"]
            # Normalizar: quitar tokens especificos para agrupar
            error_msgs[first_msg] += 1
            failed_rules.append(rule)
        else:
            passed += 1

        # Progreso cada 500 reglas
        if (i + 1) % 500 == 0:
            pct = (i + 1) / total * 100
            print(f"  Progreso: {i+1}/{total} ({pct:.1f}%) — {passed} OK, {failed} FAIL")

    print(f"\n{'='*70}")
    print(f" Resultado: {passed}/{total} pasaron ({passed/total*100:.1f}%)")
    print(f"            {failed}/{total} fallaron ({failed/total*100:.1f}%)")
    print(f"{'='*70}")

    if error_msgs:
        print(f"\n Top errores (primer error de cada regla fallida):")
        for msg, cnt in error_msgs.most_common(20):
            # Truncar mensaje largo
            display = msg[:100] + "..." if len(msg) > 100 else msg
            print(f"  {cnt:5d}x  {display}")

    if failed_rules and args.dump_errors:
        dump_dir = os.path.join(os.path.dirname(__file__), "failed")
        os.makedirs(dump_dir, exist_ok=True)
        for i, rule in enumerate(failed_rules[:50]):  # Max 50
            fname = f"{rule['id_ti']}_{rule['id_item']}.ln4".replace(" ", "_")
            fpath = os.path.join(dump_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(rule["code"])
        print(f"\n  Primeras {min(50, len(failed_rules))} reglas fallidas guardadas en {dump_dir}/")

    if failed_rules and not args.dump_errors:
        # Show first 3 failed rules with their errors for quick diagnosis
        print(f"\n Primeras 3 reglas fallidas (detalles):")
        for rule in failed_rules[:3]:
            print(f"\n  --- {rule['id_ti']}.{rule['id_item']} ({rule['code_len']} bytes) ---")
            errors = parse_code(rule["code"])
            for err in errors[:5]:
                print(f"    L{err['line']}:{err['column']} — {err['msg']}")
            # Show snippet around first error
            first_err_line = errors[0]["line"]
            code_lines = rule["code"].split("\n")
            start = max(0, first_err_line - 2)
            end = min(len(code_lines), first_err_line + 3)
            print(f"    Codigo (L{start+1}-L{end}):")
            for j in range(start, end):
                marker = " >> " if j == first_err_line - 1 else "    "
                line_text = code_lines[j].rstrip()
                if len(line_text) > 120:
                    line_text = line_text[:120] + "..."
                print(f"    {marker}L{j+1}: {line_text}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
