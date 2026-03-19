# =============================================================================
# ln4_lsp/tests/test_server.py — Tests para el servidor LSP de LN4
# =============================================================================
# Verifica que el servidor LSP funciona correctamente:
#   1. El parsing detecta errores de sintaxis correctamente
#   2. Los errores se convierten a LSP Diagnostics
#   3. El código válido no genera diagnósticos
#   4. El servidor se puede inicializar
# =============================================================================

import sys
import os

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.server import parse_ln4_source, errors_to_diagnostics, semantic_to_diagnostics, LN4LanguageServer


# =============================================================================
# Casos de prueba para parsing + diagnósticos
# =============================================================================
TEST_CASES = [
    # (descripción, código, errores_esperados)
    ("Asignación simple", "x = 1", 0),
    ("Return con valor", "Return(42)", 0),
    ("Llamada a función", 'MsgBox("Hola")', 0),
    ("If multi-line", "If x = 1 Then\n  y = 2\nEndIf", 0),
    ("If single-line", "If x = 1 Then y = 2", 0),
    ("If single-line con Else", "If x = 1 Then y = 2 Else y = 3", 0),
    ("For loop", "For i = 1 To 10\n  x = i\nNext", 0),
    ("While loop", "While x > 0\n  x = x - 1\nWend", 0),
    ("Do Until", "Do\n  x = x + 1\nUntil x > 10", 0),
    ("Member access", "TI.ITEM = 1", 0),
    ("Double-dot system method", "TI..Count()", 0),
    ("Channel cross-ref", "CHANNEL!TI.ITEM", 0),
    ("Hash reference", "#FUNC_NAME", 0),
    ("At reference", "@ITEM_NAME", 0),
    ("Date literal", "x = {2025-10-31}", 0),
    ("Expresión compleja", "x = (a + b) * c / d - e", 0),
    ("Múltiples statements", "x = 1\ny = 2\nz = x + y", 0),
    ("Comentario single-quote", "' Esto es un comentario\nx = 1", 0),
    ("Comentario double-slash", "// Esto es un comentario\nx = 1", 0),
    ("Comentario bloque", "/* comentario */\nx = 1", 0),
    # Casos con errores de sintaxis
    ("If sin Then", "If x = 1\n  y = 2\nEndIf", 1),  # Falta Then
    ("EndIf suelto", "EndIf", 1),  # EndIf sin If
    ("Paréntesis sin cerrar", "x = (a + b", 1),  # Falta )
]


def run_test(description, code, expected_error_count):
    """Ejecuta un caso de prueba y retorna (passed, message)."""
    try:
        errors, tree = parse_ln4_source(code)
        diagnostics = errors_to_diagnostics(errors)
        actual_count = len(diagnostics)

        if expected_error_count == 0:
            if actual_count == 0:
                return True, "OK"
            else:
                msgs = "; ".join(d.message for d in diagnostics)
                return False, f"Esperaba 0 errores, obtuvo {actual_count}: {msgs}"
        else:
            if actual_count >= 1:
                return True, f"OK ({actual_count} error(es) detectado(s))"
            else:
                return False, f"Esperaba >= 1 error(es), obtuvo 0"
    except Exception as e:
        return False, f"Excepción: {e}"


def test_diagnostic_fields():
    """Verifica que los campos del Diagnostic son correctos."""
    from lsprotocol import types

    code = "If Then"  # Sintaxis inválida
    errors, tree = parse_ln4_source(code)
    diagnostics = errors_to_diagnostics(errors)

    assert len(diagnostics) >= 1, f"Esperaba >= 1 diagnóstico, obtuvo {len(diagnostics)}"

    d = diagnostics[0]
    assert d.severity == types.DiagnosticSeverity.Error, f"Severity: {d.severity}"
    assert d.source == "ln4", f"Source: {d.source}"
    assert d.range.start.line >= 0, f"Start line: {d.range.start.line}"
    assert d.range.start.character >= 0, f"Start char: {d.range.start.character}"
    assert d.range.end.line >= d.range.start.line, "End line < start line"
    assert d.range.end.character > d.range.start.character or d.range.end.line > d.range.start.line, \
        "End must be after start"
    assert len(d.message) > 0, "Empty message"

    return True


def test_empty_source():
    """Código vacío no debe generar errores."""
    errors, tree = parse_ln4_source("")
    return len(errors) == 0


def test_whitespace_only():
    """Solo espacios/tabs no debe generar errores."""
    errors, tree = parse_ln4_source("   \t  \n\n  ")
    return len(errors) == 0


def test_server_initialization():
    """Verifica que el servidor se puede crear correctamente."""
    ls = LN4LanguageServer()
    assert ls.name == "ln4-language-server"
    assert ls.version == "v0.6.0"
    return True


# =============================================================================
# Main
# =============================================================================
def main():
    total = 0
    passed = 0
    failed = 0

    print("=" * 70)
    print(" LN4 LSP Server Test Suite")
    print("=" * 70)

    # -- Tests de parsing + diagnósticos ---
    print("\n--- Tests de parsing y diagnósticos ---\n")
    for description, code, expected_errors in TEST_CASES:
        total += 1
        ok, msg = run_test(description, code, expected_errors)
        status = "OK" if ok else "FAIL"
        if ok:
            passed += 1
            print(f"  [{status}] {description}: {msg}")
        else:
            failed += 1
            print(f"  [{status}] {description}: {msg}")
            # Mostrar el código que falló
            for i, line in enumerate(code.split("\n"), 1):
                print(f"       {i}: {line}")

    # -- Tests estructurales ---
    print("\n--- Tests estructurales ---\n")

    for name, test_fn in [
        ("Campos del Diagnostic", test_diagnostic_fields),
        ("Código vacío", test_empty_source),
        ("Solo whitespace", test_whitespace_only),
        ("Inicialización del servidor", test_server_initialization),
    ]:
        total += 1
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  [OK] {name}")
            else:
                failed += 1
                print(f"  [FAIL] {name}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {name}: {e}")

    # -- Resumen ---
    print("\n" + "=" * 70)
    print(f" Resultado: {passed}/{total} pasaron, {failed}/{total} fallaron")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
