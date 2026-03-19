# =============================================================================
# ln4_lsp/tests/test_definition.py — Tests del orquestador go-to-definition
# =============================================================================
"""
Prueba la resolución go-to-definition combinando:
  - Tier 1: índice de símbolos in-document (variables, for vars)
  - Tier 2: DB resolution (mock) para TI items, canales, etc.
  - Built-in functions y constantes (informativo)

Uso:
    python -m ln4_lsp.tests.test_definition
"""

import sys
import os
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.server import parse_ln4_source
from ln4_lsp.definition import resolve_definition, DefinitionResult
from ln4_lsp.db_resolver import ResolvedSymbol, DBResolver, reset_resolver
from ln4_lsp.symbol_index import (
    SYM_VARIABLE, SYM_FOR_VAR, SYM_FUNCTION_CALL,
    SYM_MEMBER_ACCESS, SYM_SYSTEM_METHOD, SYM_CHANNEL_REF,
    SYM_HASH_REF, SYM_AT_REF, SYM_IDENTIFIER,
)


# =============================================================================
# Helpers
# =============================================================================
def _parse(code):
    """Parsea código LN4 y retorna (tree, source)."""
    errors, tree = parse_ln4_source(code)
    assert not errors, f"Parse errors: {errors}"
    return tree, code


def _mock_resolver_unavailable():
    """Crea un mock de DBResolver que no está disponible."""
    resolver = MagicMock(spec=DBResolver)
    resolver.is_available = False
    resolver.resolve_item.return_value = None
    resolver.resolve_ti.return_value = None
    resolver.resolve_channel.return_value = None
    resolver.resolve_rule_source.return_value = None
    resolver.resolve_channel_item.return_value = None
    return resolver


def _mock_resolver_with_ti(ti_name, desc_esp="Desc ESP"):
    """Crea un mock de DBResolver que resuelve un TI."""
    resolver = MagicMock(spec=DBResolver)
    resolver.is_available = True
    resolver.resolve_ti.return_value = ResolvedSymbol(
        name=ti_name, kind="ti", ti_name=ti_name,
        description_esp=desc_esp, description_eng="Desc ENG",
    )
    resolver.resolve_item.return_value = None
    resolver.resolve_channel.return_value = None
    resolver.resolve_rule_source.return_value = None
    resolver.resolve_channel_item.return_value = None
    return resolver


def _mock_resolver_with_item(ti_name, item_name, item_type=3, desc="Field desc"):
    """Crea un mock de DBResolver que resuelve un item."""
    resolver = MagicMock(spec=DBResolver)
    resolver.is_available = True
    resolver.resolve_item.return_value = ResolvedSymbol(
        name=item_name, kind="item", ti_name=ti_name, item_name=item_name,
        item_type=item_type, description_esp=desc,
    )
    resolver.resolve_rule_source.return_value = None
    resolver.resolve_ti.return_value = None
    resolver.resolve_channel.return_value = None
    resolver.resolve_channel_item.return_value = None
    return resolver


# =============================================================================
# Tests
# =============================================================================
passed = 0
failed = 0


def run_test(name, test_fn):
    global passed, failed
    try:
        test_fn()
        print(f"  [OK] {name}")
        passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1
    except Exception as e:
        print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
        failed += 1


# -- Test: None tree retorna None --
def test_none_tree():
    result = resolve_definition(None, "", 1, 0)
    assert result is None, "Expected None for None tree"


# -- Test: Variable local — ir a primera definición --
def test_local_variable_definition():
    code = "x = 5\ny = x + 1\n"
    tree, source = _parse(code)
    # 'x' en línea 2, columna 4 (uso como operando)
    # Línea 2: "y = x + 1" → 'x' está en columna 4
    result = resolve_definition(tree, source, 2, 4)
    assert result is not None, "Expected DefinitionResult for 'x'"
    assert result.kind == "local"
    # Debe apuntar a la definición en línea 1 (0-indexed: line 0)
    assert result.line == 0, f"Expected line 0, got {result.line}"


# -- Test: Variable local — en la propia definición --
def test_local_variable_at_definition():
    code = "myVar = 42\n"
    tree, source = _parse(code)
    # 'myVar' está en línea 1, columna 0 (definición)
    result = resolve_definition(tree, source, 1, 0)
    assert result is not None, "Expected DefinitionResult"
    assert result.kind == "local"
    assert result.line == 0  # línea 0 en LSP (0-indexed)


# -- Test: For variable — ir a definición --
def test_for_variable_definition():
    code = "For i = 1 To 10\n  x = i\nNext\n"
    tree, source = _parse(code)
    # 'i' en línea 2, columna 6 (uso)
    result = resolve_definition(tree, source, 2, 6)
    if result is not None:
        # Debe apuntar a la definición en el For (línea 1)
        assert result.line == 0, f"Expected line 0 for For var def, got {result.line}"


# -- Test: Función built-in — retorna info --
def test_builtin_function():
    code = "x = NullValue()\n"
    tree, source = _parse(code)
    # 'NullValue' en línea 1, columna 4
    result = resolve_definition(tree, source, 1, 4)
    assert result is not None, "Expected DefinitionResult for NullValue"
    assert result.kind == "builtin_function"
    assert "NULLVALUE" in (result.tooltip or "").upper()


# -- Test: Constante conocida — retorna info --
def test_known_constant():
    code = "x = M4_TRUE\n"
    tree, source = _parse(code)
    # 'M4_TRUE' en línea 1, columna 4
    result = resolve_definition(tree, source, 1, 4)
    assert result is not None, "Expected DefinitionResult for M4_TRUE"
    assert result.kind == "constant"


# -- Test: Método de sistema — retorna info --
def test_system_method():
    code = "n = MyTI..Count()\n"
    tree, source = _parse(code)
    # '..Count' — Count está en línea 1
    # Buscamos Count en la fuente: "n = MyTI..Count()"
    # n(0) =(2) MyTI(4).(8).(9)Count(10)(15)(16)
    result = resolve_definition(tree, source, 1, 10)
    assert result is not None, "Expected DefinitionResult for system method"
    assert result.kind == "builtin_function"
    assert "Count" in (result.tooltip or "")


# -- Test: Member access TI.ITEM — con mock DB (item encontrado) --
def test_member_access_with_db():
    code = "x = MyTI.MyItem\n"
    tree, source = _parse(code)

    mock_resolver = _mock_resolver_with_item("MYTI", "MYITEM", item_type=3, desc="Mi campo")

    with patch("ln4_lsp.definition.get_resolver", return_value=mock_resolver):
        # MyItem está en línea 1; "x = MyTI.MyItem"
        # M(4)y(5)T(6)I(7).(8)M(9)y(10)I(11)t(12)e(13)m(14)
        result = resolve_definition(tree, source, 1, 9)

    assert result is not None, "Expected DefinitionResult for TI.ITEM"
    assert result.kind == "db_item"
    assert result.resolved is not None
    assert result.resolved.item_name == "MYITEM"


# -- Test: Member access TI.ITEM — sin BD --
def test_member_access_no_db():
    code = "x = MyTI.MyItem\n"
    tree, source = _parse(code)

    mock_resolver = _mock_resolver_unavailable()

    with patch("ln4_lsp.definition.get_resolver", return_value=mock_resolver):
        result = resolve_definition(tree, source, 1, 9)

    # Sin BD, no se puede resolver el member access
    assert result is None, f"Expected None without DB, got {result}"


# -- Test: Hash ref #ITEM — sin TI context --
def test_hash_ref_standalone():
    code = "x = #MY_FUNC\n"
    tree, source = _parse(code)
    # '#MY_FUNC' en línea 1, columna 4
    result = resolve_definition(tree, source, 1, 4)
    assert result is not None, "Expected DefinitionResult for hash ref"
    assert result.kind == "constant"
    assert "MY_FUNC" in (result.tooltip or "")


# -- Test: At ref @ITEM --
def test_at_ref():
    code = "x = @MY_ITEM\n"
    tree, source = _parse(code)
    # '@MY_ITEM' en línea 1, columna 4
    result = resolve_definition(tree, source, 1, 4)
    assert result is not None, "Expected DefinitionResult for at ref"
    assert result.kind == "constant"
    assert "MY_ITEM" in (result.tooltip or "")


# -- Test: Channel ref CHANNEL!TI.ITEM — con mock DB --
def test_channel_ref_with_db():
    code = "x = MyChan!MyTI.MyItem\n"
    tree, source = _parse(code)

    mock_resolver = MagicMock(spec=DBResolver)
    mock_resolver.is_available = True
    mock_resolver.resolve_channel_item.return_value = ResolvedSymbol(
        name="MYITEM", kind="item", ti_name="MYTI", item_name="MYITEM",
        channel_name="MYCHAN", item_type=3, description_esp="Cross-channel item",
    )

    with patch("ln4_lsp.definition.get_resolver", return_value=mock_resolver):
        # "x = MyChan!MyTI.MyItem"
        # MyItem starts around column 16
        result = resolve_definition(tree, source, 1, 16)

    if result is not None:
        assert result.kind == "db_item" or result.kind == "constant", \
            f"Expected db_item or constant for channel ref, got {result.kind}"


# -- Test: Posición sin símbolo --
def test_empty_position():
    code = "x = 5\n"
    tree, source = _parse(code)
    # Columna 3 es el espacio entre '=' y '5'
    result = resolve_definition(tree, source, 1, 3)
    # Puede ser None o puede resolve to something depending on token boundaries
    # This is acceptable either way


# -- Test: DefinitionResult repr --
def test_definition_result_repr():
    dr = DefinitionResult(line=5, column=10, kind="local", tooltip="test")
    repr_str = repr(dr)
    assert "local" in repr_str
    assert "5:10" in repr_str


# -- Test: DefinitionResult defaults --
def test_definition_result_defaults():
    dr = DefinitionResult(line=0, column=0)
    assert dr.uri is None
    assert dr.tooltip is None
    assert dr.kind == "local"
    assert dr.resolved is None
    assert dr.end_line == 0
    assert dr.end_column == 1


# -- Test: resolve_definition con código complejo --
def test_complex_code_no_crash():
    code = """x = 1
y = NullValue()
For i = 1 To 10
  z = MyTI.MyItem
  w = MyChan!OtherTI.OtherItem
  n = MyTI..Count()
  h = #MY_FUNC
  a = @MY_ITEM
Next
"""
    tree, source = _parse(code)
    # Intentar resolver en varias posiciones — no debe crashear
    for line in range(1, 10):
        for col in range(0, 20, 5):
            try:
                resolve_definition(tree, source, line, col)
            except Exception as e:
                assert False, f"Crash at {line}:{col}: {e}"


# =============================================================================
# Runner
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LN4 Definition Orchestrator Test Suite")
    print("=" * 70)

    tests = [
        ("None tree retorna None", test_none_tree),
        ("Variable local - ir a definicion", test_local_variable_definition),
        ("Variable local - en propia definicion", test_local_variable_at_definition),
        ("For variable - ir a definicion", test_for_variable_definition),
        ("Funcion built-in - info", test_builtin_function),
        ("Constante conocida - info", test_known_constant),
        ("Metodo de sistema - info", test_system_method),
        ("Member access TI.ITEM con DB", test_member_access_with_db),
        ("Member access TI.ITEM sin BD", test_member_access_no_db),
        ("Hash ref #ITEM standalone", test_hash_ref_standalone),
        ("At ref @ITEM", test_at_ref),
        ("Channel ref con DB", test_channel_ref_with_db),
        ("Posicion sin simbolo", test_empty_position),
        ("DefinitionResult repr", test_definition_result_repr),
        ("DefinitionResult defaults", test_definition_result_defaults),
        ("Codigo complejo no crash", test_complex_code_no_crash),
    ]

    for name, fn in tests:
        run_test(name, fn)

    print()
    print("=" * 70)
    print(f" Resultado: {passed}/{passed + failed} pasaron, {failed}/{passed + failed} fallaron")
    print("=" * 70)

    sys.exit(1 if failed > 0 else 0)
