# =============================================================================
# ln4_lsp/tests/test_symbol_index.py — Tests del índice de símbolos (Tier 1)
# =============================================================================
"""
Prueba la construcción del SymbolIndex a partir de parse trees LN4.
Verifica que se detectan correctamente:
  - Asignaciones de variables
  - Variables de For loop
  - Llamadas a función
  - Acceso a miembros (TI.ITEM)
  - Métodos de sistema (TI..SysMethod)
  - Referencias cross-channel (CHANNEL!TI.ITEM)
  - Hash refs (#ITEM, TI.#ITEM)
  - At refs (@ITEM)

Uso:
    python -m ln4_lsp.tests.test_symbol_index
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.server import parse_ln4_source
from ln4_lsp.symbol_index import (
    build_symbol_index, find_definition_at_position,
    SYM_VARIABLE, SYM_FOR_VAR, SYM_FUNCTION_CALL,
    SYM_MEMBER_ACCESS, SYM_SYSTEM_METHOD, SYM_CHANNEL_REF,
    SYM_HASH_REF, SYM_AT_REF, SYM_IDENTIFIER,
)


# =============================================================================
# Helpers
# =============================================================================
def _build_index(code):
    """Parsea código LN4 y construye el SymbolIndex."""
    errors, tree = parse_ln4_source(code)
    assert not errors, f"Parse errors: {errors}"
    return build_symbol_index(tree), tree


def _get_symbols_of_type(index, sym_type):
    """Retorna todas las ocurrencias de un tipo de símbolo."""
    results = []
    for name, occs in index.all_symbols().items():
        for occ in occs:
            if occ.symbol_type == sym_type:
                results.append(occ)
    return results


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


# -- Test: Asignación simple define variable --
def test_assignment_defines_variable():
    code = "x = 5\n"
    index, _ = _build_index(code)
    defs = index.get_definitions("x")
    assert len(defs) == 1, f"Expected 1 definition, got {len(defs)}"
    assert defs[0].symbol_type == SYM_VARIABLE
    assert defs[0].is_definition is True
    assert defs[0].name == "x"


# -- Test: Múltiples asignaciones --
def test_multiple_assignments():
    code = "x = 1\ny = 2\nz = x + y\n"
    index, _ = _build_index(code)
    assert len(index.get_definitions("x")) == 1
    assert len(index.get_definitions("y")) == 1
    assert len(index.get_definitions("z")) == 1


# -- Test: For loop define variable --
def test_for_loop_variable():
    code = "For i = 1 To 10\n  x = i\nNext\n"
    index, _ = _build_index(code)
    defs = index.get_definitions("i")
    assert len(defs) == 1, f"Expected 1, got {len(defs)}"
    assert defs[0].symbol_type == SYM_FOR_VAR
    assert defs[0].is_definition is True


# -- Test: Llamada a función registrada --
def test_function_call_registered():
    code = "x = NullValue()\n"
    index, _ = _build_index(code)
    calls = _get_symbols_of_type(index, SYM_FUNCTION_CALL)
    func_names = [c.name.upper() for c in calls]
    assert "NULLVALUE" in func_names, f"Expected NULLVALUE in {func_names}"


# -- Test: Función con argumentos --
def test_function_call_with_args():
    code = 'x = Mid("hello", 1, 3)\n'
    index, _ = _build_index(code)
    calls = _get_symbols_of_type(index, SYM_FUNCTION_CALL)
    func_names = [c.name.upper() for c in calls]
    assert "MID" in func_names


# -- Test: Member access TI.ITEM --
def test_member_access_ti_item():
    code = "x = MyTI.MyItem\n"
    index, _ = _build_index(code)
    members = _get_symbols_of_type(index, SYM_MEMBER_ACCESS)
    assert len(members) >= 1, f"Expected member access, got {len(members)}"
    item_occ = [m for m in members if m.name.upper() == "MYITEM"]
    assert len(item_occ) >= 1, f"Expected MYITEM member access"
    assert item_occ[0].context_ti is not None
    assert item_occ[0].context_ti.upper() == "MYTI"


# -- Test: Member access TI.METHOD() --
def test_member_access_ti_method():
    code = "MyTI.MyMethod(arg1, arg2)\n"
    index, _ = _build_index(code)
    members = _get_symbols_of_type(index, SYM_MEMBER_ACCESS)
    method_names = [m.name.upper() for m in members]
    assert "MYMETHOD" in method_names


# -- Test: System method TI..Count() --
def test_system_method():
    code = "n = MyTI..Count()\n"
    index, _ = _build_index(code)
    sys_methods = _get_symbols_of_type(index, SYM_SYSTEM_METHOD)
    assert len(sys_methods) >= 1, f"Expected system method, got {len(sys_methods)}"
    assert sys_methods[0].name.upper() == "COUNT"
    assert sys_methods[0].context_ti is not None
    assert sys_methods[0].context_ti.upper() == "MYTI"


# -- Test: Channel reference CHANNEL!TI.ITEM --
def test_channel_ref():
    code = "x = MyChan!MyTI.MyItem\n"
    index, _ = _build_index(code)
    chan_refs = _get_symbols_of_type(index, SYM_CHANNEL_REF)
    assert len(chan_refs) >= 1, f"Expected channel ref, got {len(chan_refs)}"
    item_ref = [r for r in chan_refs if r.name.upper() == "MYITEM"]
    assert len(item_ref) >= 1, f"Expected MYITEM channel ref"
    assert item_ref[0].context_ti is not None
    assert item_ref[0].context_ti.upper() == "MYTI"
    assert item_ref[0].context_channel is not None
    assert item_ref[0].context_channel.upper() == "MYCHAN"


# -- Test: Channel method CHANNEL!Method() --
def test_channel_method():
    code = "MyChan!MyMethod()\n"
    index, _ = _build_index(code)
    chan_refs = _get_symbols_of_type(index, SYM_CHANNEL_REF)
    assert len(chan_refs) >= 1, f"Expected channel ref, got {len(chan_refs)}"
    method_ref = [r for r in chan_refs if r.name.upper() == "MYMETHOD"]
    assert len(method_ref) >= 1
    assert method_ref[0].context_channel is not None


# -- Test: Hash ref #ITEM --
def test_hash_ref_standalone():
    code = "x = #MY_FUNC\n"
    index, _ = _build_index(code)
    hash_refs = _get_symbols_of_type(index, SYM_HASH_REF)
    assert len(hash_refs) >= 1, f"Expected hash ref, got {len(hash_refs)}"
    assert hash_refs[0].name.upper() == "MY_FUNC"


# -- Test: Hash ref TI.#ITEM --
def test_hash_ref_with_ti():
    code = "x = MyTI.#MY_ITEM\n"
    index, _ = _build_index(code)
    hash_refs = _get_symbols_of_type(index, SYM_HASH_REF)
    item_refs = [r for r in hash_refs if r.name.upper() == "MY_ITEM"]
    assert len(item_refs) >= 1
    assert item_refs[0].context_ti is not None
    assert item_refs[0].context_ti.upper() == "MYTI"


# -- Test: At ref @ITEM --
def test_at_ref():
    code = "x = @MY_ITEM\n"
    index, _ = _build_index(code)
    at_refs = _get_symbols_of_type(index, SYM_AT_REF)
    assert len(at_refs) >= 1, f"Expected at ref, got {len(at_refs)}"
    assert at_refs[0].name.upper() == "MY_ITEM"


# -- Test: Identifier simple registrado --
def test_identifier_registered():
    code = "x = y + 1\n"
    index, _ = _build_index(code)
    idents = _get_symbols_of_type(index, SYM_IDENTIFIER)
    ident_names = [i.name.upper() for i in idents]
    assert "Y" in ident_names


# -- Test: find_definition_at_position para variable --
def test_find_definition_at_position_variable():
    code = "x = 5\ny = x + 1\n"
    index, tree = _build_index(code)
    # 'x' en línea 2 debería resolver a la definición en línea 1
    # Primero encontrar la posición de 'x' en línea 2
    x_uses = [o for o in index.get_all_occurrences("x") if not o.is_definition]
    assert len(x_uses) >= 1, "Expected at least one use of 'x'"
    use = x_uses[0]
    result = find_definition_at_position(index, code, use.line, use.column)
    assert result is not None, "Expected to find definition"
    # Should return the definition (line 1)
    assert result.is_definition is True


# -- Test: find_definition_at_position en la propia definición --
def test_find_definition_at_own_position():
    code = "x = 5\n"
    index, tree = _build_index(code)
    x_def = index.get_first_definition("x")
    assert x_def is not None
    result = find_definition_at_position(index, code, x_def.line, x_def.column)
    assert result is not None
    assert result.is_definition is True


# -- Test: definition_names --
def test_definition_names():
    code = "x = 1\ny = 2\nFor i = 1 To 5\nNext\n"
    index, _ = _build_index(code)
    names = index.definition_names()
    assert "X" in names
    assert "Y" in names
    assert "I" in names


# -- Test: get_member_occurrences --
def test_get_member_occurrences():
    code = "x = MyTI.MyItem\ny = MyTI.MyItem + 1\n"
    index, _ = _build_index(code)
    occs = index.get_member_occurrences("MyTI", "MyItem")
    assert len(occs) >= 2, f"Expected at least 2 member occurrences, got {len(occs)}"


# -- Test: Código vacío —no crash --
def test_empty_code():
    code = "\n"
    index, _ = _build_index(code)
    assert len(index.all_symbols()) == 0


# -- Test: Solo comentarios — no crash --
def test_comments_only():
    code = "' This is a comment\n// Another comment\n"
    index, _ = _build_index(code)
    # Comments should not produce symbols
    assert len(index.all_symbols()) == 0


# -- Test: Código complejo con múltiples tipos --
def test_complex_code():
    code = """x = 1
y = NullValue()
For i = 1 To 10
  z = MyTI.MyItem
  w = MyChan!OtherTI.OtherItem
  n = MyTI..Count()
Next
"""
    index, _ = _build_index(code)
    # Variables definidas
    defs = index.definition_names()
    assert "X" in defs
    assert "Y" in defs
    assert "I" in defs
    assert "Z" in defs
    assert "W" in defs
    assert "N" in defs
    # Función llamada
    calls = _get_symbols_of_type(index, SYM_FUNCTION_CALL)
    assert any(c.name.upper() == "NULLVALUE" for c in calls)
    # Member access
    members = _get_symbols_of_type(index, SYM_MEMBER_ACCESS)
    assert any(m.name.upper() == "MYITEM" for m in members)
    # System method
    sys_methods = _get_symbols_of_type(index, SYM_SYSTEM_METHOD)
    assert any(s.name.upper() == "COUNT" for s in sys_methods)
    # Channel ref
    chan_refs = _get_symbols_of_type(index, SYM_CHANNEL_REF)
    assert any(c.name.upper() == "OTHERITEM" for c in chan_refs)


# =============================================================================
# Runner
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LN4 Symbol Index Test Suite (Tier 1)")
    print("=" * 70)

    tests = [
        ("Asignación define variable", test_assignment_defines_variable),
        ("Múltiples asignaciones", test_multiple_assignments),
        ("For loop variable", test_for_loop_variable),
        ("Llamada a función registrada", test_function_call_registered),
        ("Función con argumentos", test_function_call_with_args),
        ("Member access TI.ITEM", test_member_access_ti_item),
        ("Member access TI.METHOD()", test_member_access_ti_method),
        ("System method TI..Count()", test_system_method),
        ("Channel ref CHANNEL!TI.ITEM", test_channel_ref),
        ("Channel method CHANNEL!Method()", test_channel_method),
        ("Hash ref #ITEM standalone", test_hash_ref_standalone),
        ("Hash ref TI.#ITEM", test_hash_ref_with_ti),
        ("At ref @ITEM", test_at_ref),
        ("Identifier simple registrado", test_identifier_registered),
        ("find_definition_at_position variable", test_find_definition_at_position_variable),
        ("find_definition en propia posición", test_find_definition_at_own_position),
        ("definition_names", test_definition_names),
        ("get_member_occurrences", test_get_member_occurrences),
        ("Código vacío", test_empty_code),
        ("Solo comentarios", test_comments_only),
        ("Código complejo", test_complex_code),
    ]

    for name, fn in tests:
        run_test(name, fn)

    print()
    print("=" * 70)
    print(f" Resultado: {passed}/{passed + failed} pasaron, {failed}/{passed + failed} fallaron")
    print("=" * 70)

    sys.exit(1 if failed > 0 else 0)
