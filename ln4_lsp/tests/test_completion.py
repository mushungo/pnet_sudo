# =============================================================================
# ln4_lsp/tests/test_completion.py — Tests para autocompletado y hover de LN4
# =============================================================================
# Verifica que el autocompletado y hover funcionan correctamente:
#   1. Completion items se generan para funciones, keywords y constantes
#   2. Snippets de inserción son correctos
#   3. Hover retorna documentación para funciones conocidas
#   4. Hover retorna documentación para constantes
#   5. Hover retorna documentación para keywords
#   6. Hover retorna None para palabras desconocidas
#   7. Completion contextual genera items de TI con args (mock)
# =============================================================================

import sys
import os

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lsprotocol import types

from ln4_lsp.completion import (
    get_completion_items,
    get_hover_for_word,
    _build_signature,
    _build_snippet,
    _build_hover_markdown,
    _format_arg,
    _build_item_signature_str,
    _build_item_snippet,
    _build_item_documentation,
    LN4_KEYWORDS,
)
from ln4_lsp.ln4_builtins import get_catalog, LN4_CONSTANTS
from ln4_lsp.db_resolver import ResolvedSymbol, ITEM_TYPE_METHOD, ITEM_TYPE_PROPERTY, ITEM_TYPE_FIELD


# =============================================================================
# Tests de completion items
# =============================================================================

def test_completion_items_generated():
    """Se generan items de completion (funciones + keywords + constantes)."""
    items = get_completion_items()
    assert len(items) > 0, "No se generaron items de completion"
    # Mínimo: 301 funciones + 17 keywords + constantes
    assert len(items) >= 301 + len(LN4_KEYWORDS) + len(LN4_CONSTANTS), \
        f"Esperaba al menos {301 + len(LN4_KEYWORDS) + len(LN4_CONSTANTS)} items, obtuvo {len(items)}"
    return True


def test_completion_has_functions():
    """Los items incluyen funciones built-in con tipo Function."""
    items = get_completion_items()
    functions = [i for i in items if i.kind == types.CompletionItemKind.Function]
    assert len(functions) == 301, f"Esperaba 301 funciones, obtuvo {len(functions)}"
    return True


def test_completion_has_keywords():
    """Los items incluyen keywords con tipo Keyword."""
    items = get_completion_items()
    keywords = [i for i in items if i.kind == types.CompletionItemKind.Keyword]
    assert len(keywords) == len(LN4_KEYWORDS), \
        f"Esperaba {len(LN4_KEYWORDS)} keywords, obtuvo {len(keywords)}"
    return True


def test_completion_has_constants():
    """Los items incluyen constantes con tipo Constant."""
    items = get_completion_items()
    constants = [i for i in items if i.kind == types.CompletionItemKind.Constant]
    assert len(constants) == len(LN4_CONSTANTS), \
        f"Esperaba {len(LN4_CONSTANTS)} constantes, obtuvo {len(constants)}"
    return True


def test_completion_function_has_detail():
    """Las funciones tienen detail con la firma."""
    items = get_completion_items()
    abs_items = [i for i in items if i.label == "ABS"]
    assert len(abs_items) == 1, f"Esperaba 1 ABS, obtuvo {len(abs_items)}"
    item = abs_items[0]
    assert item.detail is not None, "ABS no tiene detail"
    assert "ABS(" in item.detail, f"Detail no contiene firma: {item.detail}"
    return True


def test_completion_function_has_documentation():
    """Las funciones tienen documentación markdown."""
    items = get_completion_items()
    abs_items = [i for i in items if i.label == "ABS"]
    item = abs_items[0]
    assert item.documentation is not None, "ABS no tiene documentación"
    assert isinstance(item.documentation, types.MarkupContent), \
        f"Documentación no es MarkupContent: {type(item.documentation)}"
    assert item.documentation.kind == types.MarkupKind.Markdown
    assert "absolute" in item.documentation.value.lower(), \
        f"Documentación no menciona 'absolute': {item.documentation.value[:100]}"
    return True


def test_completion_function_has_snippet():
    """Las funciones tienen snippet de inserción con placeholders."""
    items = get_completion_items()
    abs_items = [i for i in items if i.label == "ABS"]
    item = abs_items[0]
    assert item.insert_text is not None, "ABS no tiene insert_text"
    assert item.insert_text_format == types.InsertTextFormat.Snippet
    # ABS tiene 1 argumento: ABS(${1:Value})
    assert "${1:" in item.insert_text, \
        f"Snippet no tiene placeholder: {item.insert_text}"
    return True


def test_completion_no_args_function_snippet():
    """Funciones sin argumentos generan snippet con $0."""
    items = get_completion_items()
    nullval = [i for i in items if i.label == "NULLVALUE"]
    assert len(nullval) == 1
    item = nullval[0]
    assert item.insert_text == "NULLVALUE($0)", \
        f"Snippet incorrecto para NULLVALUE: {item.insert_text}"
    return True


def test_completion_sort_order():
    """Los items tienen sort_text para ordenar: funciones > constantes > keywords."""
    items = get_completion_items()
    func_sort = [i.sort_text for i in items if i.kind == types.CompletionItemKind.Function]
    const_sort = [i.sort_text for i in items if i.kind == types.CompletionItemKind.Constant]
    kw_sort = [i.sort_text for i in items if i.kind == types.CompletionItemKind.Keyword]

    # Funciones empiezan con "0_", constantes con "1_", keywords con "2_"
    assert all(s.startswith("0_") for s in func_sort), "Funciones no empiezan con 0_"
    assert all(s.startswith("1_") for s in const_sort), "Constantes no empiezan con 1_"
    assert all(s.startswith("2_") for s in kw_sort), "Keywords no empiezan con 2_"
    return True


# =============================================================================
# Tests de _build_signature y _build_snippet
# =============================================================================

def test_signature_no_args():
    """Firma de funcion sin argumentos."""
    func = {"name": "TODAY", "arguments": [], "variable_arguments": False}
    sig = _build_signature(func)
    assert sig == "TODAY()", f"Firma incorrecta: {sig}"
    return True


def test_signature_with_args():
    """Firma de funcion con argumentos."""
    func = {
        "name": "MID",
        "arguments": [
            {"name": "Value", "m4_type": 2, "optional": False},
            {"name": "Start", "m4_type": 3, "optional": False},
            {"name": "Length", "m4_type": 3, "optional": False},
        ],
        "variable_arguments": False,
    }
    sig = _build_signature(func)
    assert sig == "MID(Value: VarChar, Start: Long, Length: Long)", \
        f"Firma incorrecta: {sig}"
    return True


def test_signature_with_optional():
    """Firma con argumentos opcionales muestra corchetes."""
    func = {
        "name": "FUNC",
        "arguments": [
            {"name": "Req", "m4_type": 7, "optional": False},
            {"name": "Opt", "m4_type": 2, "optional": True},
        ],
        "variable_arguments": False,
    }
    sig = _build_signature(func)
    assert "[Opt: VarChar]" in sig, f"Argumento opcional sin corchetes: {sig}"
    return True


def test_signature_variable_args():
    """Firma con argumentos variables muestra '...'."""
    func = {"name": "EXECUTESQL", "arguments": [], "variable_arguments": True}
    sig = _build_signature(func)
    assert "..." in sig, f"Argumentos variables sin '...': {sig}"
    return True


def test_snippet_no_args():
    """Snippet sin argumentos: FUNC($0)."""
    func = {"name": "TODAY", "arguments": []}
    snip = _build_snippet(func)
    assert snip == "TODAY($0)", f"Snippet incorrecto: {snip}"
    return True


def test_snippet_with_args():
    """Snippet con argumentos genera placeholders numerados."""
    func = {
        "name": "MID",
        "arguments": [
            {"name": "Value", "m4_type": 2, "optional": False},
            {"name": "Start", "m4_type": 3, "optional": False},
            {"name": "Length", "m4_type": 3, "optional": False},
        ],
    }
    snip = _build_snippet(func)
    assert snip == "MID(${1:Value}, ${2:Start}, ${3:Length})", \
        f"Snippet incorrecto: {snip}"
    return True


def test_snippet_skips_optional():
    """Snippet solo incluye argumentos requeridos."""
    func = {
        "name": "FUNC",
        "arguments": [
            {"name": "Req", "m4_type": 7, "optional": False},
            {"name": "Opt", "m4_type": 2, "optional": True},
        ],
    }
    snip = _build_snippet(func)
    assert "Opt" not in snip, f"Snippet incluye argumento opcional: {snip}"
    assert "${1:Req}" in snip, f"Snippet no tiene placeholder requerido: {snip}"
    return True


# =============================================================================
# Tests de hover
# =============================================================================

def test_hover_known_function():
    """Hover sobre funcion conocida retorna documentacion."""
    result = get_hover_for_word("Abs")
    assert result is not None, "Hover para Abs retornó None"
    assert isinstance(result, types.Hover)
    assert isinstance(result.contents, types.MarkupContent)
    assert "ABS" in result.contents.value
    assert "absolute" in result.contents.value.lower()
    return True


def test_hover_known_function_case_insensitive():
    """Hover es case-insensitive."""
    r1 = get_hover_for_word("abs")
    r2 = get_hover_for_word("ABS")
    r3 = get_hover_for_word("Abs")
    assert r1 is not None and r2 is not None and r3 is not None
    return True


def test_hover_function_shows_arguments():
    """Hover de funcion con argumentos muestra la lista."""
    result = get_hover_for_word("Mid")
    assert result is not None
    assert "Value" in result.contents.value
    assert "Start" in result.contents.value
    assert "Length" in result.contents.value
    return True


def test_hover_function_shows_group():
    """Hover de funcion muestra el grupo."""
    result = get_hover_for_word("Abs")
    assert result is not None
    # Abs pertenece al grupo "Funciones matemáticas"
    assert "matem" in result.contents.value.lower(), \
        f"No muestra grupo: {result.contents.value[:200]}"
    return True


def test_hover_constant():
    """Hover sobre constante retorna descripcion."""
    result = get_hover_for_word("M4_TRUE")
    assert result is not None, "Hover para M4_TRUE retornó None"
    assert "M4_TRUE" in result.contents.value
    assert "Constante" in result.contents.value
    return True


def test_hover_keyword():
    """Hover sobre keyword retorna descripcion."""
    result = get_hover_for_word("If")
    assert result is not None, "Hover para If retornó None"
    assert "If" in result.contents.value
    assert "Keyword" in result.contents.value
    return True


def test_hover_unknown_word():
    """Hover sobre palabra desconocida retorna None."""
    result = get_hover_for_word("xyzzy_unknown_variable_42")
    assert result is None, f"No esperaba hover para palabra desconocida: {result}"
    return True


def test_hover_empty_word():
    """Hover sobre palabra vacía retorna None."""
    result = get_hover_for_word("")
    assert result is None
    result2 = get_hover_for_word(None)
    assert result2 is None
    return True


# =============================================================================
# Tests de _format_arg
# =============================================================================

def test_format_arg_required():
    """Argumento requerido sin corchetes."""
    result = _format_arg({"name": "Value", "m4_type": 7, "optional": False})
    assert result == "Value: Variant", f"Formato incorrecto: {result}"
    return True


def test_format_arg_optional():
    """Argumento opcional con corchetes."""
    result = _format_arg({"name": "Opt", "m4_type": 2, "optional": True})
    assert result == "[Opt: VarChar]", f"Formato incorrecto: {result}"
    return True


# =============================================================================
# Tests de completion contextual — helpers para items de TI (mock)
# =============================================================================

def _make_mock_resolved(name, item_type, m4_type=None, args=None,
                        desc_esp=None, desc_eng=None):
    """Crea un ResolvedSymbol simulado para tests."""
    return ResolvedSymbol(
        name=name,
        kind="item",
        ti_name="TEST_TI",
        item_name=name,
        item_type=item_type,
        m4_type=m4_type,
        description_esp=desc_esp,
        description_eng=desc_eng,
        arguments=args,
    )


def test_item_signature_str_with_args():
    """Firma de item con argumentos muestra tipos."""
    args = [
        {"name": "ARG1", "m4_type": 2, "arg_type": 1},
        {"name": "ARG2", "m4_type": 6, "arg_type": 1},
    ]
    sig = _build_item_signature_str("MyMethod", args)
    assert sig == "MyMethod(ARG1: VarChar, ARG2: Number)", f"Firma: {sig}"
    return True


def test_item_signature_str_no_args():
    """Firma de item sin argumentos muestra paréntesis vacíos."""
    sig = _build_item_signature_str("MyMethod", None)
    assert sig == "MyMethod()", f"Firma: {sig}"
    sig2 = _build_item_signature_str("MyMethod", [])
    assert sig2 == "MyMethod()", f"Firma: {sig2}"
    return True


def test_item_signature_str_output_arg():
    """Firma de item con arg output muestra [out]."""
    args = [
        {"name": "IN", "m4_type": 2, "arg_type": 1},
        {"name": "OUT", "m4_type": 7, "arg_type": 2},
    ]
    sig = _build_item_signature_str("Calc", args)
    assert "OUT: Variant [out]" in sig, f"Firma: {sig}"
    return True


def test_item_snippet_method_with_args():
    """Snippet de método con argumentos genera placeholders."""
    args = [
        {"name": "ARG1", "m4_type": 2, "arg_type": 1},
        {"name": "ARG2", "m4_type": 6, "arg_type": 1},
    ]
    text, fmt = _build_item_snippet("MyMethod", ITEM_TYPE_METHOD, args)
    assert fmt == types.InsertTextFormat.Snippet
    assert "${1:ARG1}" in text, f"Snippet: {text}"
    assert "${2:ARG2}" in text, f"Snippet: {text}"
    return True


def test_item_snippet_method_no_args():
    """Snippet de método sin argumentos: Method()$0."""
    text, fmt = _build_item_snippet("NoArgs", ITEM_TYPE_METHOD, None)
    assert text == "NoArgs()$0", f"Snippet: {text}"
    assert fmt == types.InsertTextFormat.Snippet
    return True


def test_item_snippet_method_only_output_args():
    """Snippet de método con solo output args: paréntesis vacíos."""
    args = [{"name": "OUT", "m4_type": 7, "arg_type": 2}]
    text, fmt = _build_item_snippet("GetVal", ITEM_TYPE_METHOD, args)
    assert text == "GetVal()$0", f"Snippet: {text}"
    return True


def test_item_snippet_property():
    """Snippet de property: solo el nombre, sin paréntesis."""
    text, fmt = _build_item_snippet("MyProp", ITEM_TYPE_PROPERTY, None)
    assert text == "MyProp", f"Snippet: {text}"
    assert fmt == types.InsertTextFormat.PlainText
    return True


def test_item_snippet_field():
    """Snippet de field: solo el nombre, sin paréntesis."""
    text, fmt = _build_item_snippet("MyField", ITEM_TYPE_FIELD, None)
    assert text == "MyField", f"Snippet: {text}"
    assert fmt == types.InsertTextFormat.PlainText
    return True


def test_item_documentation_method_with_args():
    """Documentación de método con argumentos muestra la lista."""
    args = [
        {"name": "X", "m4_type": 6, "arg_type": 1},
        {"name": "Y", "m4_type": 6, "arg_type": 2},
    ]
    resolved = _make_mock_resolved("Calc", ITEM_TYPE_METHOD, m4_type=6,
                                    args=args, desc_esp="Calcula algo")
    doc = _build_item_documentation(resolved)
    assert "**Method**" in doc, f"Doc: {doc}"
    assert "Calcula algo" in doc, f"Doc: {doc}"
    assert "`X: Number`" in doc, f"Doc: {doc}"
    assert "*(out)*" in doc, f"Doc: {doc}"
    return True


def test_item_documentation_property_no_args():
    """Documentación de property sin argumentos."""
    resolved = _make_mock_resolved("Status", ITEM_TYPE_PROPERTY, m4_type=2,
                                    desc_esp="Estado actual")
    doc = _build_item_documentation(resolved)
    assert "**Property**" in doc, f"Doc: {doc}"
    assert "Estado actual" in doc, f"Doc: {doc}"
    assert "VarChar" in doc, f"Doc: {doc}"
    assert "Args" not in doc, f"Doc no debería tener Args: {doc}"
    return True


def test_item_documentation_english_fallback():
    """Documentación usa descripción inglesa si no hay española."""
    resolved = _make_mock_resolved("Name", ITEM_TYPE_FIELD, m4_type=2,
                                    desc_eng="Employee name")
    doc = _build_item_documentation(resolved)
    assert "Employee name" in doc, f"Doc: {doc}"
    return True


# =============================================================================
# Main
# =============================================================================
def main():
    total = 0
    passed = 0
    failed = 0

    print("=" * 70)
    print(" LN4 Completion & Hover Test Suite")
    print("=" * 70)

    tests = [
        # Completion items
        ("Items generados", test_completion_items_generated),
        ("Funciones presentes", test_completion_has_functions),
        ("Keywords presentes", test_completion_has_keywords),
        ("Constantes presentes", test_completion_has_constants),
        ("Funcion tiene detail (firma)", test_completion_function_has_detail),
        ("Funcion tiene documentacion", test_completion_function_has_documentation),
        ("Funcion tiene snippet", test_completion_function_has_snippet),
        ("Sin-args snippet con $0", test_completion_no_args_function_snippet),
        ("Orden de sort_text", test_completion_sort_order),

        # Signature / snippet builders
        ("Firma sin args", test_signature_no_args),
        ("Firma con args", test_signature_with_args),
        ("Firma con opcional", test_signature_with_optional),
        ("Firma con args variables", test_signature_variable_args),
        ("Snippet sin args", test_snippet_no_args),
        ("Snippet con args", test_snippet_with_args),
        ("Snippet omite opcionales", test_snippet_skips_optional),

        # Hover
        ("Hover funcion conocida", test_hover_known_function),
        ("Hover case-insensitive", test_hover_known_function_case_insensitive),
        ("Hover muestra argumentos", test_hover_function_shows_arguments),
        ("Hover muestra grupo", test_hover_function_shows_group),
        ("Hover constante", test_hover_constant),
        ("Hover keyword", test_hover_keyword),
        ("Hover palabra desconocida", test_hover_unknown_word),
        ("Hover palabra vacia", test_hover_empty_word),

        # Format helpers
        ("Formato arg requerido", test_format_arg_required),
        ("Formato arg opcional", test_format_arg_optional),

        # Contextual completion helpers (mock)
        ("Item firma con args", test_item_signature_str_with_args),
        ("Item firma sin args", test_item_signature_str_no_args),
        ("Item firma con output arg", test_item_signature_str_output_arg),
        ("Item snippet método con args", test_item_snippet_method_with_args),
        ("Item snippet método sin args", test_item_snippet_method_no_args),
        ("Item snippet método solo output", test_item_snippet_method_only_output_args),
        ("Item snippet property", test_item_snippet_property),
        ("Item snippet field", test_item_snippet_field),
        ("Item doc método con args", test_item_documentation_method_with_args),
        ("Item doc property sin args", test_item_documentation_property_no_args),
        ("Item doc fallback inglés", test_item_documentation_english_fallback),
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
