# =============================================================================
# ln4_lsp/tests/test_signature_help.py — Tests para signature help de LN4
# =============================================================================
# Verifica:
#   1. Parsing de contexto de llamada (_find_active_call)
#   2. Signature help para funciones built-in
#   3. Signature help para métodos de TI (mock sin BD)
#   4. build_item_hover_markdown para items resueltos
#   5. Edge cases: strings, anidamiento, multilínea
#
# Uso:
#     python -m ln4_lsp.tests.test_signature_help
# =============================================================================

import sys
import os

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lsprotocol import types

from ln4_lsp.signature_help import (
    _find_active_call,
    _build_builtin_signature_help,
    _build_item_signature_help,
    get_signature_help,
)
from ln4_lsp.completion import (
    build_item_hover_markdown,
    get_hover_for_word,
    M4_TYPE_NAMES,
)
from ln4_lsp.ln4_builtins import get_catalog


# =============================================================================
# Tests de _find_active_call
# =============================================================================

def test_find_active_call_simple_function():
    """Detecta una llamada simple: ROUND("""
    result = _find_active_call("ROUND(")
    assert result is not None, "Expected to detect ROUND("
    func_name, ti_name, active_param = result
    assert func_name == "ROUND"
    assert ti_name is None
    assert active_param == 0
    return True


def test_find_active_call_with_first_arg():
    """Detecta primer argumento: ROUND(x"""
    result = _find_active_call("ROUND(x")
    assert result is not None
    func_name, ti_name, active_param = result
    assert func_name == "ROUND"
    assert active_param == 0
    return True


def test_find_active_call_second_arg():
    """Detecta segundo argumento: ROUND(x, """
    result = _find_active_call("ROUND(x, ")
    assert result is not None
    func_name, ti_name, active_param = result
    assert func_name == "ROUND"
    assert active_param == 1
    return True


def test_find_active_call_third_arg():
    """Detecta tercer argumento: MID(x, y, """
    result = _find_active_call('MID("hello", 1, ')
    assert result is not None
    func_name, _, active_param = result
    assert func_name == "MID"
    assert active_param == 2
    return True


def test_find_active_call_member_access():
    """Detecta TI.Method(: MY_TI.DoSomething("""
    result = _find_active_call("MY_TI.DoSomething(")
    assert result is not None
    func_name, ti_name, active_param = result
    assert func_name == "DoSomething"
    assert ti_name == "MY_TI"
    assert active_param == 0
    return True


def test_find_active_call_member_with_args():
    """Detecta TI.Method con args: MY_TI.DoSomething(x, """
    result = _find_active_call("MY_TI.DoSomething(x, ")
    assert result is not None
    func_name, ti_name, active_param = result
    assert func_name == "DoSomething"
    assert ti_name == "MY_TI"
    assert active_param == 1
    return True


def test_find_active_call_nested():
    """Detecta llamada anidada: ROUND(MID(x, """
    result = _find_active_call("ROUND(MID(x, ")
    assert result is not None
    func_name, _, active_param = result
    # Should detect the innermost call (MID)
    assert func_name == "MID"
    assert active_param == 1
    return True


def test_find_active_call_nested_closed():
    """Detecta outer call con inner cerrada: ROUND(MID(x, y), """
    result = _find_active_call("ROUND(MID(x, y), ")
    assert result is not None
    func_name, _, active_param = result
    # Inner call is closed, so outer ROUND is active
    assert func_name == "ROUND"
    assert active_param == 1
    return True


def test_find_active_call_no_call():
    """No detecta llamada cuando no hay paréntesis abierto."""
    result = _find_active_call("x = 42")
    assert result is None
    return True


def test_find_active_call_closed_paren():
    """No detecta llamada cuando todos los paréntesis están cerrados."""
    result = _find_active_call("ROUND(x, 2) ")
    assert result is None
    return True


def test_find_active_call_string_with_comma():
    """Ignora comas dentro de strings."""
    result = _find_active_call('FUNC("a,b,c", ')
    assert result is not None
    func_name, _, active_param = result
    assert func_name == "FUNC"
    assert active_param == 1  # Solo 1 coma real, no las de dentro del string
    return True


def test_find_active_call_system_method():
    """Detecta TI..SysMethod("""
    result = _find_active_call("MY_TI..LoadAll(")
    assert result is not None
    func_name, ti_name, active_param = result
    assert func_name == "LoadAll"
    # ti_name es None para system methods (no se puede resolver via DB)
    assert active_param == 0
    return True


def test_find_active_call_with_spaces():
    """Detecta llamada con espacios: FUNC  (  x ,  """
    result = _find_active_call("FUNC  (  x ,  ")
    assert result is not None
    func_name, _, active_param = result
    assert func_name == "FUNC"
    assert active_param == 1
    return True


# =============================================================================
# Tests de _build_builtin_signature_help
# =============================================================================

def test_builtin_signature_help_round():
    """Signature help para ROUND muestra 2 parámetros."""
    catalog = get_catalog()
    func = catalog.get_function("ROUND")
    assert func is not None, "ROUND not in catalog"

    result = _build_builtin_signature_help(func, 0)
    assert isinstance(result, types.SignatureHelp)
    assert len(result.signatures) == 1
    sig = result.signatures[0]
    assert "ROUND" in sig.label
    assert len(sig.parameters) == 2
    assert result.active_parameter == 0
    return True


def test_builtin_signature_help_second_param():
    """Active parameter se mueve al segundo."""
    catalog = get_catalog()
    func = catalog.get_function("ROUND")

    result = _build_builtin_signature_help(func, 1)
    assert result.active_parameter == 1
    return True


def test_builtin_signature_help_clamp():
    """Active parameter se clampea al rango válido."""
    catalog = get_catalog()
    func = catalog.get_function("ROUND")

    # ROUND tiene 2 params, pedir el 10o debería clampear a 1
    result = _build_builtin_signature_help(func, 10)
    assert result.active_parameter == 1
    return True


def test_builtin_signature_help_no_args():
    """Signature help para función sin args."""
    catalog = get_catalog()
    func = catalog.get_function("NULLVALUE")
    assert func is not None, "NULLVALUE not in catalog"

    result = _build_builtin_signature_help(func, 0)
    assert isinstance(result, types.SignatureHelp)
    assert len(result.signatures[0].parameters) == 0
    return True


def test_builtin_signature_help_variable_args():
    """Signature help para función con argumentos variables."""
    catalog = get_catalog()
    func = catalog.get_function("EXECUTESQL")
    assert func is not None, "EXECUTESQL not in catalog"

    result = _build_builtin_signature_help(func, 0)
    assert isinstance(result, types.SignatureHelp)
    # Should have ... parameter
    params = result.signatures[0].parameters
    assert any(p.label == "..." for p in params), "Expected '...' parameter"
    return True


# =============================================================================
# Tests de _build_item_signature_help
# =============================================================================

def test_item_signature_help_basic():
    """Signature help para método de TI con argumentos mock."""
    args = [
        {"name": "Value", "position": 1, "m4_type": 7, "arg_type": 1},
        {"name": "Count", "position": 2, "m4_type": 3, "arg_type": 1},
    ]
    result = _build_item_signature_help("MY_TI", "MY_METHOD", args, 0)
    assert isinstance(result, types.SignatureHelp)
    sig = result.signatures[0]
    assert "MY_TI.MY_METHOD" in sig.label
    assert "Value" in sig.label
    assert "Count" in sig.label
    assert len(sig.parameters) == 2
    assert result.active_parameter == 0
    return True


def test_item_signature_help_second_param():
    """Active parameter en segundo arg de TI method."""
    args = [
        {"name": "A", "position": 1, "m4_type": 2, "arg_type": 1},
        {"name": "B", "position": 2, "m4_type": 6, "arg_type": 1},
    ]
    result = _build_item_signature_help("TI", "M", args, 1)
    assert result.active_parameter == 1
    return True


def test_item_signature_help_no_args():
    """Signature help para método sin argumentos."""
    result = _build_item_signature_help("TI", "M", [], 0)
    assert isinstance(result, types.SignatureHelp)
    assert "TI.M()" in result.signatures[0].label
    return True


def test_item_signature_help_output_param():
    """Signature help muestra output param."""
    args = [
        {"name": "Year", "position": 1, "m4_type": 3, "arg_type": 2},
    ]
    result = _build_item_signature_help("TI", "M", args, 0)
    sig = result.signatures[0]
    # Output param should have documentation
    assert sig.parameters[0].documentation == "(output / by-ref)"
    return True


def test_item_signature_help_with_description():
    """Signature help incluye descripción del item."""
    args = [
        {"name": "X", "position": 1, "m4_type": 7, "arg_type": 1},
    ]
    result = _build_item_signature_help("TI", "M", args, 0, item_desc="Does something")
    sig = result.signatures[0]
    assert sig.documentation is not None
    assert "Does something" in sig.documentation.value
    return True


# =============================================================================
# Tests de get_signature_help (integración con catálogo built-in)
# =============================================================================

def test_get_signature_help_builtin():
    """get_signature_help retorna firma para ROUND(."""
    source = 'ROUND('
    result = get_signature_help(source, 0, 6)
    assert result is not None, "Expected signature help for ROUND("
    assert "ROUND" in result.signatures[0].label
    return True


def test_get_signature_help_builtin_second_param():
    """get_signature_help retorna param 1 para ROUND(x, ."""
    source = 'ROUND(x, '
    result = get_signature_help(source, 0, 9)
    assert result is not None
    assert result.active_parameter == 1
    return True


def test_get_signature_help_no_context():
    """get_signature_help retorna None sin contexto de llamada."""
    source = 'x = 42'
    result = get_signature_help(source, 0, 6)
    assert result is None
    return True


def test_get_signature_help_multiline():
    """get_signature_help funciona con contexto multilínea."""
    source = "x = 1\nROUND(\n"
    result = get_signature_help(source, 1, 6)
    assert result is not None
    assert "ROUND" in result.signatures[0].label
    return True


def test_get_signature_help_nested_call():
    """get_signature_help detecta la llamada interna en anidamiento."""
    source = "ROUND(ABS("
    result = get_signature_help(source, 0, 10)
    assert result is not None
    assert "ABS" in result.signatures[0].label
    return True


# =============================================================================
# Tests de build_item_hover_markdown
# =============================================================================

def test_item_hover_markdown_with_args():
    """Hover markdown para item con argumentos."""
    from ln4_lsp.db_resolver import ResolvedSymbol
    sym = ResolvedSymbol(
        name="MY_METHOD",
        kind="item",
        ti_name="MY_TI",
        item_name="MY_METHOD",
        item_type=1,
        m4_type=7,
        description_esp="Hace algo",
        arguments=[
            {"name": "Value", "m4_type": 7, "arg_type": 1},
            {"name": "Count", "m4_type": 3, "arg_type": 2},
        ],
    )
    md = build_item_hover_markdown(sym)
    assert "MY_TI.MY_METHOD" in md
    assert "Value: Variant" in md
    assert "Count: Long" in md
    assert "Method" in md
    assert "Hace algo" in md
    assert "*(output)*" in md  # arg_type=2
    return True


def test_item_hover_markdown_no_args():
    """Hover markdown para item sin argumentos."""
    from ln4_lsp.db_resolver import ResolvedSymbol
    sym = ResolvedSymbol(
        name="MY_PROP",
        kind="item",
        ti_name="MY_TI",
        item_name="MY_PROP",
        item_type=2,
        m4_type=2,
        description_esp="Una propiedad",
    )
    md = build_item_hover_markdown(sym)
    assert "MY_TI.MY_PROP" in md
    assert "Property" in md
    assert "Una propiedad" in md
    assert "Argumentos" not in md  # No args section
    return True


def test_item_hover_markdown_method_no_args():
    """Hover markdown para método sin argumentos muestra ()."""
    from ln4_lsp.db_resolver import ResolvedSymbol
    sym = ResolvedSymbol(
        name="INIT",
        kind="item",
        ti_name="MY_TI",
        item_name="INIT",
        item_type=1,
        m4_type=0,
    )
    md = build_item_hover_markdown(sym)
    assert "MY_TI.INIT()" in md
    return True


# =============================================================================
# Tests de _build_item_signature_help con variable_arguments
# =============================================================================

def test_item_signature_help_variable_args():
    """Signature help para método variadic de TI muestra '...' parameter."""
    args = [
        {"name": "Query", "position": 1, "m4_type": 2, "arg_type": 1},
    ]
    result = _build_item_signature_help("MY_TI", "MY_METHOD", args, 0,
                                        variable_arguments=True)
    assert isinstance(result, types.SignatureHelp)
    sig = result.signatures[0]
    assert "MY_TI.MY_METHOD" in sig.label
    assert "..." in sig.label
    params = sig.parameters
    assert any(p.label == "..." for p in params), "Expected '...' parameter"
    return True


def test_item_signature_help_pure_variable_args():
    """Signature help para método sin args fijos pero variadic (estilo ExecuteSQL de TI)."""
    result = _build_item_signature_help("MY_TI", "EXEC_QUERY", None, 0,
                                        variable_arguments=True)
    assert isinstance(result, types.SignatureHelp)
    sig = result.signatures[0]
    assert "EXEC_QUERY" in sig.label
    assert "..." in sig.label
    params = sig.parameters
    assert len(params) == 1
    assert params[0].label == "..."
    return True


def test_item_signature_help_variable_args_clamp():
    """Active parameter se fija en '...' cuando el índice excede los args fijos."""
    args = [
        {"name": "A", "position": 1, "m4_type": 2, "arg_type": 1},
    ]
    # active_param=5 debería quedar en el índice de '...' (posición 1)
    result = _build_item_signature_help("TI", "M", args, 5, variable_arguments=True)
    assert isinstance(result, types.SignatureHelp)
    assert result.active_parameter == 1  # clamped to '...'
    return True


def test_item_signature_help_no_args_variadic_empty_list():
    """_build_item_signature_help con lista vacía y variable_arguments=True."""
    result = _build_item_signature_help("TI", "M", [], 0, variable_arguments=True)
    assert isinstance(result, types.SignatureHelp)
    sig = result.signatures[0]
    assert "..." in sig.label
    return True


# =============================================================================
# Tests de build_item_hover_markdown con variable_arguments
# =============================================================================

def test_item_hover_markdown_variable_args():
    """Hover markdown para item variadic muestra '...' en argumentos."""
    from ln4_lsp.db_resolver import ResolvedSymbol
    sym = ResolvedSymbol(
        name="EXEC_QUERY",
        kind="item",
        ti_name="MY_TI",
        item_name="EXEC_QUERY",
        item_type=4,  # Concept
        m4_type=7,
        description_esp="Ejecuta SQL con parámetros variables",
        arguments=None,
        variable_arguments=True,
    )
    md = build_item_hover_markdown(sym)
    assert "MY_TI.EXEC_QUERY(...)" in md
    assert "argumentos variables" in md
    return True


def test_item_hover_markdown_mixed_args_and_varargs():
    """Hover markdown para item con args fijos + variadic."""
    from ln4_lsp.db_resolver import ResolvedSymbol
    sym = ResolvedSymbol(
        name="MY_VARARGS",
        kind="item",
        ti_name="MY_TI",
        item_name="MY_VARARGS",
        item_type=1,  # Method
        m4_type=7,
        description_esp="Método con args mixtos",
        arguments=[
            {"name": "Param1", "m4_type": 2, "arg_type": 1},
        ],
        variable_arguments=True,
    )
    md = build_item_hover_markdown(sym)
    assert "Param1" in md
    assert "..." in md
    assert "argumentos variables" in md
    return True


# =============================================================================
# Tests de _build_item_signature_str con variable_arguments
# =============================================================================

def test_item_signature_str_variable_args():
    """_build_item_signature_str incluye '...' cuando variable_arguments=True."""
    from ln4_lsp.completion import _build_item_signature_str
    result = _build_item_signature_str("MY_METHOD", None, variable_arguments=True)
    assert result == "MY_METHOD(...)"
    return True


def test_item_signature_str_mixed_variable_args():
    """_build_item_signature_str muestra args fijos + '...'."""
    from ln4_lsp.completion import _build_item_signature_str
    args = [{"name": "X", "m4_type": 6, "arg_type": 1}]
    result = _build_item_signature_str("MY_METHOD", args, variable_arguments=True)
    assert "X: Number" in result
    assert "..." in result
    return True



# =============================================================================
# Main
# =============================================================================
def main():
    total = 0
    passed = 0
    failed = 0

    print("=" * 70)
    print(" LN4 Signature Help & Item Hover Test Suite")
    print("=" * 70)

    tests = [
        # _find_active_call
        ("find_active_call simple", test_find_active_call_simple_function),
        ("find_active_call con primer arg", test_find_active_call_with_first_arg),
        ("find_active_call segundo arg", test_find_active_call_second_arg),
        ("find_active_call tercer arg", test_find_active_call_third_arg),
        ("find_active_call member access", test_find_active_call_member_access),
        ("find_active_call member con args", test_find_active_call_member_with_args),
        ("find_active_call anidado", test_find_active_call_nested),
        ("find_active_call anidado cerrado", test_find_active_call_nested_closed),
        ("find_active_call sin llamada", test_find_active_call_no_call),
        ("find_active_call paréntesis cerrado", test_find_active_call_closed_paren),
        ("find_active_call string con coma", test_find_active_call_string_with_comma),
        ("find_active_call system method", test_find_active_call_system_method),
        ("find_active_call con espacios", test_find_active_call_with_spaces),

        # _build_builtin_signature_help
        ("Builtin signature ROUND", test_builtin_signature_help_round),
        ("Builtin signature segundo param", test_builtin_signature_help_second_param),
        ("Builtin signature clamp", test_builtin_signature_help_clamp),
        ("Builtin signature sin args", test_builtin_signature_help_no_args),
        ("Builtin signature args variables", test_builtin_signature_help_variable_args),

        # _build_item_signature_help
        ("Item signature básico", test_item_signature_help_basic),
        ("Item signature segundo param", test_item_signature_help_second_param),
        ("Item signature sin args", test_item_signature_help_no_args),
        ("Item signature output param", test_item_signature_help_output_param),
        ("Item signature con descripción", test_item_signature_help_with_description),

        # get_signature_help
        ("get_signature_help built-in", test_get_signature_help_builtin),
        ("get_signature_help segundo param", test_get_signature_help_builtin_second_param),
        ("get_signature_help sin contexto", test_get_signature_help_no_context),
        ("get_signature_help multilínea", test_get_signature_help_multiline),
        ("get_signature_help anidado", test_get_signature_help_nested_call),

        # build_item_hover_markdown
        ("Item hover con args", test_item_hover_markdown_with_args),
        ("Item hover sin args", test_item_hover_markdown_no_args),
        ("Item hover método sin args", test_item_hover_markdown_method_no_args),

        # variable_arguments para TI items
        ("Item signature variadic", test_item_signature_help_variable_args),
        ("Item signature solo variadic", test_item_signature_help_pure_variable_args),
        ("Item signature variadic clamp", test_item_signature_help_variable_args_clamp),
        ("Item signature lista vacía variadic", test_item_signature_help_no_args_variadic_empty_list),
        ("Item hover variadic", test_item_hover_markdown_variable_args),
        ("Item hover mixto + variadic", test_item_hover_markdown_mixed_args_and_varargs),
        ("Item sig str variadic", test_item_signature_str_variable_args),
        ("Item sig str mixto variadic", test_item_signature_str_mixed_variable_args),
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
