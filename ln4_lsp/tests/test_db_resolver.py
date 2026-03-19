# =============================================================================
# ln4_lsp/tests/test_db_resolver.py — Tests del DBResolver (Tier 2)
# =============================================================================
"""
Prueba la resolución de símbolos contra la BD de PeopleNet.
REQUIERE conexión a la BD — se salta automáticamente si no está disponible.

Verifica:
  - resolve_item: busca items por TI + nombre
  - resolve_rule_source: obtiene source code de reglas
  - resolve_ti: busca TIs por nombre
  - resolve_channel: busca canales por nombre
  - resolve_channel_item: resolución cross-channel
  - list_ti_items: lista items de un TI
  - find_tis_for_channel: lista TIs de un canal
  - resolve_item_args: obtiene argumentos de un item
  - resolve_item_with_args: item + argumentos combinados

Uso:
    python -m ln4_lsp.tests.test_db_resolver
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.db_resolver import DBResolver, ResolvedSymbol, reset_resolver


# =============================================================================
# Tests
# =============================================================================
passed = 0
failed = 0
skipped = 0


def run_test(name, test_fn, resolver):
    global passed, failed, skipped
    try:
        test_fn(resolver)
        print(f"  [OK] {name}")
        passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1
    except Exception as e:
        print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
        failed += 1


# -- Test: Resolver disponible --
def test_resolver_available(resolver):
    assert resolver.is_available, "Resolver should be available with DB connection"


# -- Test: resolve_ti con TI conocido --
def test_resolve_ti_known(resolver):
    # Usamos un TI genérico que probablemente existe en toda instalación PeopleNet
    # Alternativa: buscar cualquier TI que exista
    conn = resolver._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 ID_TI FROM M4RCH_TIS")
    row = cursor.fetchone()
    assert row is not None, "No TIs found in database"
    ti_name = row.ID_TI

    result = resolver.resolve_ti(ti_name)
    assert result is not None, f"Expected to resolve TI '{ti_name}'"
    assert result.kind == "ti"
    assert result.ti_name == ti_name


# -- Test: resolve_ti con TI inexistente --
def test_resolve_ti_unknown(resolver):
    result = resolver.resolve_ti("ZZZZZ_NONEXISTENT_TI_99999")
    assert result is None, "Expected None for nonexistent TI"


# -- Test: resolve_channel con canal conocido --
def test_resolve_channel_known(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 ID_T3 FROM M4RCH_T3S")
    row = cursor.fetchone()
    assert row is not None, "No channels found in database"
    channel_name = row.ID_T3

    result = resolver.resolve_channel(channel_name)
    assert result is not None, f"Expected to resolve channel '{channel_name}'"
    assert result.kind == "channel"
    assert result.channel_name == channel_name


# -- Test: resolve_channel con canal inexistente --
def test_resolve_channel_unknown(resolver):
    result = resolver.resolve_channel("ZZZZZ_NONEXISTENT_CHANNEL_99999")
    assert result is None, "Expected None for nonexistent channel"


# -- Test: resolve_item con item conocido --
def test_resolve_item_known(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 ID_TI, ID_ITEM FROM M4RCH_ITEMS")
    row = cursor.fetchone()
    assert row is not None, "No items found in database"

    result = resolver.resolve_item(row.ID_TI, row.ID_ITEM)
    assert result is not None, f"Expected to resolve item {row.ID_TI}.{row.ID_ITEM}"
    assert result.kind == "item"
    assert result.ti_name == row.ID_TI
    assert result.item_name == row.ID_ITEM


# -- Test: resolve_item con item inexistente --
def test_resolve_item_unknown(resolver):
    result = resolver.resolve_item("ZZZZZ_TI", "ZZZZZ_ITEM")
    assert result is None, "Expected None for nonexistent item"


# -- Test: resolve_rule_source con regla LN4 --
def test_resolve_rule_source(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un item que tenga regla LN4 con source code
    cursor.execute("""
        SELECT TOP 1 r.ID_TI, r.ID_ITEM
        FROM M4RCH_RULES r
        JOIN M4RCH_RULES3 r3
            ON r.ID_TI = r3.ID_TI
            AND r.ID_ITEM = r3.ID_ITEM
            AND r.DT_START = r3.DT_START
            AND r.ID_RULE = r3.ID_RULE
        WHERE r.ID_CODE_TYPE = 1
            AND DATALENGTH(r3.SOURCE_CODE) > 0
    """)
    row = cursor.fetchone()
    assert row is not None, "No LN4 rules with source code found"

    result = resolver.resolve_rule_source(row.ID_TI, row.ID_ITEM)
    assert result is not None, f"Expected to resolve rule for {row.ID_TI}.{row.ID_ITEM}"
    assert result.kind == "rule"
    assert result.source_code is not None
    assert len(result.source_code) > 0


# -- Test: resolve_rule_source sin regla --
def test_resolve_rule_source_none(resolver):
    result = resolver.resolve_rule_source("ZZZZZ_TI", "ZZZZZ_ITEM")
    assert result is None, "Expected None for nonexistent rule"


# -- Test: list_ti_items retorna items --
def test_list_ti_items(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un TI con al menos 1 item
    cursor.execute("""
        SELECT TOP 1 ID_TI, COUNT(*) AS cnt
        FROM M4RCH_ITEMS
        GROUP BY ID_TI
        HAVING COUNT(*) > 0
        ORDER BY cnt DESC
    """)
    row = cursor.fetchone()
    assert row is not None, "No TIs with items found"

    items = resolver.list_ti_items(row.ID_TI)
    assert len(items) > 0, f"Expected items for TI '{row.ID_TI}'"
    assert all(i.kind == "item" for i in items)


# -- Test: list_ti_items para TI inexistente --
def test_list_ti_items_empty(resolver):
    items = resolver.list_ti_items("ZZZZZ_NONEXISTENT_TI")
    assert len(items) == 0


# -- Test: find_tis_for_channel --
def test_find_tis_for_channel(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un canal con al menos 1 nodo/TI
    cursor.execute("""
        SELECT TOP 1 n.ID_T3, COUNT(DISTINCT n.ID_TI) AS ti_cnt
        FROM M4RCH_NODES n
        GROUP BY n.ID_T3
        HAVING COUNT(DISTINCT n.ID_TI) > 0
        ORDER BY ti_cnt DESC
    """)
    row = cursor.fetchone()
    assert row is not None, "No channels with TIs found"

    tis = resolver.find_tis_for_channel(row.ID_T3)
    assert len(tis) > 0, f"Expected TIs for channel '{row.ID_T3}'"
    assert all(t.kind == "ti" for t in tis)


# -- Test: resolve_channel_item cross-channel --
def test_resolve_channel_item(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un canal + TI + item válido
    cursor.execute("""
        SELECT TOP 1 n.ID_T3, n.ID_TI, i.ID_ITEM
        FROM M4RCH_NODES n
        JOIN M4RCH_ITEMS i ON n.ID_TI = i.ID_TI
    """)
    row = cursor.fetchone()
    assert row is not None, "No channel+TI+item combinations found"

    result = resolver.resolve_channel_item(row.ID_T3, row.ID_TI, row.ID_ITEM)
    assert result is not None, f"Expected to resolve {row.ID_T3}!{row.ID_TI}.{row.ID_ITEM}"
    assert result.channel_name == row.ID_T3


# -- Test: resolve_channel_item con TI no del canal --
def test_resolve_channel_item_wrong_channel(resolver):
    result = resolver.resolve_channel_item(
        "ZZZZZ_CHANNEL", "ZZZZZ_TI", "ZZZZZ_ITEM"
    )
    assert result is None


# -- Test: resolve_item_args con item que tiene argumentos --
def test_resolve_item_args_with_args(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un item que tenga al menos 1 argumento
    cursor.execute("""
        SELECT TOP 1 a.ID_TI, a.ID_ITEM, COUNT(*) AS cnt
        FROM M4RCH_ITEM_ARGS a
        GROUP BY a.ID_TI, a.ID_ITEM
        HAVING COUNT(*) > 0
        ORDER BY cnt DESC
    """)
    row = cursor.fetchone()
    assert row is not None, "No items with arguments found in M4RCH_ITEM_ARGS"

    args = resolver.resolve_item_args(row.ID_TI, row.ID_ITEM)
    assert len(args) > 0, f"Expected args for {row.ID_TI}.{row.ID_ITEM}"
    # Verificar estructura de cada argumento
    for arg in args:
        assert "name" in arg, "Arg missing 'name'"
        assert "position" in arg, "Arg missing 'position'"
        assert "m4_type" in arg, "Arg missing 'm4_type'"
    # Verificar que están ordenados por posición
    positions = [a["position"] for a in args]
    assert positions == sorted(positions), f"Args not sorted by position: {positions}"


# -- Test: resolve_item_args sin argumentos --
def test_resolve_item_args_no_args(resolver):
    args = resolver.resolve_item_args("ZZZZZ_TI", "ZZZZZ_ITEM")
    assert len(args) == 0, "Expected empty list for nonexistent item"


# -- Test: resolve_item_args caching --
def test_resolve_item_args_caching(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 a.ID_TI, a.ID_ITEM
        FROM M4RCH_ITEM_ARGS a
    """)
    row = cursor.fetchone()
    assert row is not None, "No item args found"

    # Primera llamada — llena el cache
    args1 = resolver.resolve_item_args(row.ID_TI, row.ID_ITEM)
    # Segunda llamada — debe venir del cache
    args2 = resolver.resolve_item_args(row.ID_TI, row.ID_ITEM)
    assert args1 is args2, "Expected cached result (same object reference)"


# -- Test: resolve_item_with_args con método que tiene args --
def test_resolve_item_with_args(resolver):
    conn = resolver._get_connection()
    cursor = conn.cursor()
    # Buscar un item tipo Method (1) que tenga argumentos
    cursor.execute("""
        SELECT TOP 1 i.ID_TI, i.ID_ITEM
        FROM M4RCH_ITEMS i
        JOIN M4RCH_ITEM_ARGS a ON i.ID_TI = a.ID_TI AND i.ID_ITEM = a.ID_ITEM
        WHERE i.ID_ITEM_TYPE = 1
    """)
    row = cursor.fetchone()
    assert row is not None, "No methods with args found"

    result = resolver.resolve_item_with_args(row.ID_TI, row.ID_ITEM)
    assert result is not None, f"Expected to resolve {row.ID_TI}.{row.ID_ITEM}"
    assert result.arguments is not None, "Expected arguments to be populated"
    assert len(result.arguments) > 0, "Expected at least one argument"


# -- Test: resolve_item_with_args para item inexistente --
def test_resolve_item_with_args_none(resolver):
    result = resolver.resolve_item_with_args("ZZZZZ_TI", "ZZZZZ_ITEM")
    assert result is None, "Expected None for nonexistent item"


# =============================================================================
# Runner
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LN4 DB Resolver Test Suite (Tier 2)")
    print("=" * 70)

    # Intentar conectar a la BD
    resolver = DBResolver()
    if not resolver.is_available:
        print()
        print("  [SKIP] BD no disponible — saltando todos los tests de Tier 2")
        print("         Configure .env con DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD")
        print()
        print("=" * 70)
        print(f" Resultado: 0/0 pasaron, 0/0 fallaron (todos saltados)")
        print("=" * 70)
        sys.exit(0)

    tests = [
        ("Resolver disponible", test_resolver_available),
        ("resolve_ti conocido", test_resolve_ti_known),
        ("resolve_ti desconocido", test_resolve_ti_unknown),
        ("resolve_channel conocido", test_resolve_channel_known),
        ("resolve_channel desconocido", test_resolve_channel_unknown),
        ("resolve_item conocido", test_resolve_item_known),
        ("resolve_item desconocido", test_resolve_item_unknown),
        ("resolve_rule_source con LN4", test_resolve_rule_source),
        ("resolve_rule_source sin regla", test_resolve_rule_source_none),
        ("list_ti_items con items", test_list_ti_items),
        ("list_ti_items vacío", test_list_ti_items_empty),
        ("find_tis_for_channel", test_find_tis_for_channel),
        ("resolve_channel_item cross-channel", test_resolve_channel_item),
        ("resolve_channel_item canal erróneo", test_resolve_channel_item_wrong_channel),
        ("resolve_item_args con argumentos", test_resolve_item_args_with_args),
        ("resolve_item_args sin argumentos", test_resolve_item_args_no_args),
        ("resolve_item_args caching", test_resolve_item_args_caching),
        ("resolve_item_with_args con método", test_resolve_item_with_args),
        ("resolve_item_with_args inexistente", test_resolve_item_with_args_none),
    ]

    try:
        for name, fn in tests:
            run_test(name, fn, resolver)
    finally:
        resolver.close()
        reset_resolver()

    print()
    print("=" * 70)
    print(f" Resultado: {passed}/{passed + failed} pasaron, {failed}/{passed + failed} fallaron")
    print("=" * 70)

    sys.exit(1 if failed > 0 else 0)
