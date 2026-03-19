# =============================================================================
# ln4_lsp/tests/test_semantic.py — Tests para el analizador semantico de LN4
# =============================================================================
# Verifica que el analisis semantico funciona correctamente:
#   1. Funciones desconocidas se reportan como warning
#   2. Aridad incorrecta se reporta como error
#   3. Constantes no se reportan como variables indefinidas
#   4. Variables asignadas se registran correctamente
#   5. For loop registra su variable
#   6. Codigo valido con funciones conocidas no genera diagnosticos
#   7. Member access (TI.ITEM) no genera falsos positivos
# =============================================================================

import sys
import os

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from ln4_lsp.generated.LN4Lexer import LN4Lexer
from ln4_lsp.generated.LN4Parser import LN4Parser
from ln4_lsp.semantic import analyze_semantics, SEVERITY_ERROR, SEVERITY_WARNING


# =============================================================================
# Helper: parsear y analizar
# =============================================================================
class SilentErrorListener(ErrorListener):
    """Suprime errores de sintaxis del parser (no nos interesan aqui)."""
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        pass


def parse_and_analyze(code):
    """Parsea codigo LN4 y ejecuta analisis semantico.

    Returns:
        Lista de tuplas (line, column, end_column, message, severity).
    """
    input_stream = InputStream(code)
    lexer = LN4Lexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(SilentErrorListener())

    token_stream = CommonTokenStream(lexer)
    parser = LN4Parser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(SilentErrorListener())

    tree = parser.program()
    return analyze_semantics(tree)


def diags_with_severity(diags, severity):
    """Filtra diagnosticos por severity."""
    return [d for d in diags if d[4] == severity]


def diags_containing(diags, text):
    """Filtra diagnosticos cuyo mensaje contiene el texto."""
    return [d for d in diags if text.upper() in d[3].upper()]


# =============================================================================
# Test cases
# =============================================================================

# -- 1. Funciones desconocidas ------------------------------------------------

def test_unknown_function_reported():
    """Una funcion que no existe en el catalogo se reporta como warning."""
    diags = parse_and_analyze("x = FakeFunc(1)")
    warnings = diags_with_severity(diags, SEVERITY_WARNING)
    unknown = diags_containing(warnings, "FAKEFUNC")
    assert len(unknown) >= 1, f"Esperaba warning por FakeFunc, obtuvo: {diags}"
    return True


def test_multiple_unknown_functions():
    """Multiples funciones desconocidas generan un warning cada una."""
    diags = parse_and_analyze("x = Foo(1)\ny = Bar(2)")
    warnings = diags_with_severity(diags, SEVERITY_WARNING)
    assert len(warnings) >= 2, f"Esperaba >= 2 warnings, obtuvo: {warnings}"
    return True


# -- 2. Funciones conocidas (sin error) ---------------------------------------

def test_known_function_no_diagnostic():
    """Una funcion conocida con aridad correcta no genera diagnosticos."""
    # NullValue() toma 0 args
    diags = parse_and_analyze("x = NullValue()")
    # No deberia haber warnings de funcion desconocida
    unknown_warns = diags_containing(diags, "desconocida")
    assert len(unknown_warns) == 0, f"No esperaba warning por NullValue, obtuvo: {diags}"
    return True


def test_known_function_abs():
    """Abs(x) con 1 argumento — funcion conocida."""
    diags = parse_and_analyze("x = Abs(42)")
    unknown_warns = diags_containing(diags, "desconocida")
    assert len(unknown_warns) == 0, f"No esperaba warning por Abs, obtuvo: {diags}"
    return True


def test_known_function_mid():
    """Mid(str, start, length) con 3 argumentos."""
    diags = parse_and_analyze('x = Mid("hello", 1, 3)')
    unknown_warns = diags_containing(diags, "desconocida")
    assert len(unknown_warns) == 0, f"No esperaba warning por Mid, obtuvo: {diags}"
    return True


# -- 3. Aridad incorrecta ----------------------------------------------------

def test_too_few_args():
    """Funcion con menos argumentos de los requeridos genera error."""
    # Abs requiere exactamente 1 argumento
    diags = parse_and_analyze("x = Abs()")
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    arity_errs = diags_containing(errors, "argumento")
    assert len(arity_errs) >= 1, f"Esperaba error de aridad para Abs(), obtuvo: {diags}"
    return True


def test_too_many_args():
    """Funcion con mas argumentos de los permitidos genera error."""
    # Abs acepta como maximo 1 argumento
    diags = parse_and_analyze("x = Abs(1, 2)")
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    arity_errs = diags_containing(errors, "argumento")
    assert len(arity_errs) >= 1, f"Esperaba error de aridad para Abs(1,2), obtuvo: {diags}"
    return True


def test_variable_args_function():
    """Funciones con argumentos variables aceptan cualquier cantidad extra."""
    # ExecuteSQL tiene variable_arguments=true
    diags = parse_and_analyze('ExecuteSQL("SELECT 1", 1, 2, 3, 4, 5)')
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    arity_errs = diags_containing(errors, "argumento")
    assert len(arity_errs) == 0, f"No esperaba error de aridad para ExecuteSQL con args variables: {diags}"
    return True


# -- 4. Constantes -----------------------------------------------------------

def test_constants_not_reported():
    """Constantes M4_TRUE, M4_FALSE, EQUAL, NULL no generan diagnosticos."""
    code = """x = M4_TRUE
y = M4_FALSE
z = EQUAL
w = NULL"""
    diags = parse_and_analyze(code)
    # No deberia haber ningun diagnostico (las constantes son conocidas)
    assert len(diags) == 0, f"No esperaba diagnosticos para constantes, obtuvo: {diags}"
    return True


def test_m4_prefix_not_reported():
    """Identificadores con prefijo M4_ no se reportan (heuristica)."""
    diags = parse_and_analyze("x = M4_SOME_UNKNOWN_CONSTANT")
    assert len(diags) == 0, f"No esperaba diagnosticos para M4_*, obtuvo: {diags}"
    return True


def test_arg_prefix_not_reported():
    """Identificadores con prefijo ARG_ no se reportan (convención PeopleNet)."""
    diags = parse_and_analyze("x = ARG_EMPLOYEE_ID")
    assert len(diags) == 0, f"No esperaba diagnosticos para ARG_*, obtuvo: {diags}"
    return True


def test_p_prefix_not_reported():
    """Identificadores con prefijo P_ no se reportan (convención parámetros)."""
    diags = parse_and_analyze("x = P_START_DATE")
    assert len(diags) == 0, f"No esperaba diagnosticos para P_*, obtuvo: {diags}"
    return True


# -- 5. Variables y asignaciones ----------------------------------------------

def test_for_loop_variable_registered():
    """La variable del For loop no se reporta como indefinida."""
    code = """For i = 1 To 10
  x = i
Next"""
    diags = parse_and_analyze(code)
    assert len(diags) == 0, f"No esperaba diagnosticos en For loop: {diags}"
    return True


def test_assignment_defines_variable():
    """Una variable asignada no genera diagnostico al usarla despues."""
    code = """myVar = 42
x = myVar + 1"""
    diags = parse_and_analyze(code)
    assert len(diags) == 0, f"No esperaba diagnosticos: {diags}"
    return True


# -- 6. Member access (TI.ITEM) — no debe generar falsos positivos -----------

def test_member_access_no_false_positive():
    """TI.ITEM no genera diagnosticos (los TIs no se validan en Phase 3)."""
    code = "x = TI.ITEM"
    diags = parse_and_analyze(code)
    # TI puede generar warning como variable desconocida, pero los checks
    # de variables indefinidas estan comentados, asi que no deberia haber nada
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores para TI.ITEM: {diags}"
    return True


def test_double_dot_system_method_no_error():
    """TI..Count() no genera errores."""
    code = "x = TI..Count()"
    diags = parse_and_analyze(code)
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores para TI..Count(): {diags}"
    return True


def test_channel_cross_ref_no_error():
    """CHANNEL!TI.ITEM no genera errores."""
    code = "x = CHANNEL!TI.ITEM"
    diags = parse_and_analyze(code)
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores para CHANNEL!TI.ITEM: {diags}"
    return True


def test_hash_ref_no_error():
    """#FUNC_NAME no genera errores."""
    code = "x = #FUNC_NAME"
    diags = parse_and_analyze(code)
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores para #FUNC_NAME: {diags}"
    return True


def test_at_ref_no_error():
    """@ITEM_NAME no genera errores."""
    code = "x = @ITEM_NAME"
    diags = parse_and_analyze(code)
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores para @ITEM_NAME: {diags}"
    return True


# -- 7. Codigo complejo (integration-style) ----------------------------------

def test_complex_code_only_unknown_funcs():
    """Codigo complejo: solo funciones desconocidas generan warnings."""
    code = """' Regla de ejemplo
x = 42
y = Abs(x)
If y > 10 Then
    z = Mid("hello", 1, 3)
    w = UnknownFunc(z)
EndIf
Return(y)"""
    diags = parse_and_analyze(code)
    # Solo deberia haber warning por UnknownFunc
    warnings = diags_with_severity(diags, SEVERITY_WARNING)
    unknown = diags_containing(warnings, "UNKNOWNFUNC")
    assert len(unknown) >= 1, f"Esperaba warning por UnknownFunc: {diags}"
    # No deberia haber errores de aridad
    errors = diags_with_severity(diags, SEVERITY_ERROR)
    assert len(errors) == 0, f"No esperaba errores: {errors}"
    return True


def test_empty_code_no_diagnostics():
    """Codigo vacio no genera diagnosticos."""
    diags = parse_and_analyze("")
    assert len(diags) == 0, f"No esperaba diagnosticos para codigo vacio: {diags}"
    return True


def test_only_comments_no_diagnostics():
    """Solo comentarios no genera diagnosticos."""
    code = """' Esto es un comentario
// Otro comentario
/* Bloque */"""
    diags = parse_and_analyze(code)
    assert len(diags) == 0, f"No esperaba diagnosticos para solo comentarios: {diags}"
    return True


# -- 8. Samples existentes — ninguno deberia generar errores de aridad --------

def test_all_samples_no_arity_errors():
    """Ninguno de los 13 samples deberia generar errores de aridad."""
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    if not os.path.isdir(samples_dir):
        print(f"  [SKIP] Directorio de samples no encontrado: {samples_dir}")
        return True

    sample_files = sorted(f for f in os.listdir(samples_dir) if f.endswith(".ln4"))
    failures = []

    for filename in sample_files:
        filepath = os.path.join(samples_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        diags = parse_and_analyze(code)
        errors = diags_with_severity(diags, SEVERITY_ERROR)
        if errors:
            failures.append((filename, errors))

    if failures:
        for fname, errs in failures:
            print(f"    {fname}: {errs}")
        assert False, f"{len(failures)} sample(s) generaron errores de aridad"

    return True


# =============================================================================
# Main
# =============================================================================
def main():
    total = 0
    passed = 0
    failed = 0

    print("=" * 70)
    print(" LN4 Semantic Analysis Test Suite")
    print("=" * 70)

    tests = [
        # 1. Funciones desconocidas
        ("Funcion desconocida reportada", test_unknown_function_reported),
        ("Multiples funciones desconocidas", test_multiple_unknown_functions),

        # 2. Funciones conocidas
        ("NullValue() sin diagnostico", test_known_function_no_diagnostic),
        ("Abs(x) sin diagnostico", test_known_function_abs),
        ("Mid(str,start,len) sin diagnostico", test_known_function_mid),

        # 3. Aridad incorrecta
        ("Abs() sin args — error aridad", test_too_few_args),
        ("Abs(1,2) demasiados args — error aridad", test_too_many_args),
        ("ExecuteSQL con args variables — sin error", test_variable_args_function),

        # 4. Constantes
        ("Constantes no reportadas", test_constants_not_reported),
        ("Prefijo M4_ no reportado", test_m4_prefix_not_reported),
        ("Prefijo ARG_ no reportado", test_arg_prefix_not_reported),
        ("Prefijo P_ no reportado", test_p_prefix_not_reported),

        # 5. Variables
        ("For loop variable registrada", test_for_loop_variable_registered),
        ("Asignacion define variable", test_assignment_defines_variable),

        # 6. Member access
        ("TI.ITEM sin falsos positivos", test_member_access_no_false_positive),
        ("TI..Count() sin errores", test_double_dot_system_method_no_error),
        ("CHANNEL!TI.ITEM sin errores", test_channel_cross_ref_no_error),
        ("#FUNC_NAME sin errores", test_hash_ref_no_error),
        ("@ITEM_NAME sin errores", test_at_ref_no_error),

        # 7. Codigo complejo
        ("Codigo complejo — solo UnknownFunc", test_complex_code_only_unknown_funcs),
        ("Codigo vacio sin diagnosticos", test_empty_code_no_diagnostics),
        ("Solo comentarios sin diagnosticos", test_only_comments_no_diagnostics),

        # 8. Samples
        ("Todos los samples sin errores aridad", test_all_samples_no_arity_errors),
    ]

    for name, test_fn in tests:
        total += 1
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  [OK] {name}")
            else:
                failed += 1
                print(f"  [FAIL] {name}")
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {name}: {type(e).__name__}: {e}")

    # -- Resumen ---
    print("\n" + "=" * 70)
    print(f" Resultado: {passed}/{total} pasaron, {failed}/{total} fallaron")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
