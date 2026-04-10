# =============================================================================
# ln4_lsp/completion.py — Autocompletado y hover para LN4
# =============================================================================
# Fase 4+ del LSP: autocompletado, hover information e item hover mejorado.
#
# Proporciona:
#   1. Completion: funciones built-in (301), constantes, keywords
#   2. Completion contextual: items de TI desde BD (tras "TI.")
#   3. Hover: documentación de funciones (firma, argumentos, comentarios)
#   4. Hover de TI items: documentación enriquecida con ITEM_ARGS de BD
#   5. Signature help data (reusable por signature_help.py)
#
# Los items de completion estáticos se pre-generan una sola vez al cargar.
# Los items de TI se generan dinámicamente por consulta a BD.
# =============================================================================

import logging

from lsprotocol import types

from ln4_lsp.ln4_builtins import get_catalog, LN4_CONSTANTS

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# M4 Type names — para documentación de argumentos
# =============================================================================
M4_TYPE_NAMES = {
    0: "Null",
    1: "FixedString",
    2: "VarChar",
    3: "Long",
    4: "Date",
    5: "Timestamp",
    6: "Number",
    7: "Variant",
    8: "Currency",
    9: "MiniVariant",
    10: "Blob",
    11: "BinaryString",
    12: "Time",
    13: "VarCharUnicode",
    14: "LongUnicode",
    15: "VariantUnicode",
    16: "FixedStringUnicode",
    17: "TimeInterval",
}

# =============================================================================
# Keywords de LN4 (para completion)
# =============================================================================
LN4_KEYWORDS = [
    "If", "Then", "ElseIf", "Else", "EndIf",
    "For", "To", "Step", "Next",
    "While", "Wend",
    "Do", "Until", "Loop",
    "Return",
    "And", "Or", "Not",
]

# Descripciones breves de keywords para hover
LN4_KEYWORD_DOCS = {
    "IF": "Condicional: If expr Then ... [ElseIf ...] [Else ...] EndIf",
    "THEN": "Parte del bloque If: If expr Then ...",
    "ELSEIF": "Rama alternativa: ElseIf expr Then ...",
    "ELSE": "Rama por defecto del bloque If",
    "ENDIF": "Cierra un bloque If multi-línea",
    "FOR": "Bucle: For var = start To end [Step n] ... Next",
    "TO": "Rango del bucle For: For var = start To end",
    "STEP": "Incremento del bucle For: For var = start To end Step n",
    "NEXT": "Cierra un bucle For",
    "WHILE": "Bucle: While expr ... Wend",
    "WEND": "Cierra un bucle While",
    "DO": "Bucle: Do ... Until expr  o  Do ... While expr Loop",
    "UNTIL": "Condición de salida: Do ... Until expr",
    "LOOP": "Cierra un bucle Do...While: Do ... While expr Loop",
    "RETURN": "Retorna un valor: Return, Return(expr), Return expr",
    "AND": "Operador lógico AND",
    "OR": "Operador lógico OR",
    "NOT": "Operador lógico NOT (negación)",
}

# Descripciones breves de constantes para hover
LN4_CONSTANT_DOCS = {
    "M4_TRUE": "Valor booleano verdadero",
    "M4_FALSE": "Valor booleano falso",
    "M4_SUCCESS": "Resultado exitoso",
    "M4_ERROR": "Resultado de error",
    "M4_EQUAL": "Operador de comparación: igual",
    "EQUAL": "Operador de comparación: igual",
    "GREATER": "Operador de comparación: mayor",
    "GREATER_OR_EQUAL": "Operador de comparación: mayor o igual",
    "LESS": "Operador de comparación: menor",
    "LESS_OR_EQUAL": "Operador de comparación: menor o igual",
    "NOT_EQUAL": "Operador de comparación: distinto",
    "NULL": "Valor nulo",
    "NOTHING": "Valor nulo (alias)",
    "EMPTY": "Cadena vacía",
    "M4_MINUS_INF": "Fecha mínima del sistema (menos infinito)",
    "M4_PLUS_INF": "Fecha máxima del sistema (más infinito)",
    "M4_ERRORLOG": "Nivel de log: error",
    "M4_DEBUGINFOLOG": "Nivel de log: debug info",
    "M4_WARNINGLOG": "Nivel de log: warning",
    "M4_AUTOLOAD_OFF": "Desactiva la carga automática de nodos",
    "M4_AUTOLOAD_NODESAYS": "Carga automática según configuración del nodo",
    "M4_INSTANCE_GLOBAL_SHARED": "Instancia compartida globalmente",
    "M4_INSTANCE_NOT_SHARED": "Instancia no compartida",
    "M4_ROLLBACK": "Operación de rollback",
    "M4_ROLLBACK_RESUME": "Reanudar tras rollback",
    "M4_TRIM_ALL": "Modo trim: eliminar espacios de ambos lados",
    "M4_TYPE_FIELD": "Tipo: campo",
    "M4_SCOPE_REGISTER": "Ámbito: registro actual",
    "M4_SCOPE_ALL": "Ámbito: todos los registros",
    "M4_CR": "Carácter de retorno de carro (CR)",
    "M4_TAB": "Carácter de tabulación",
    "M4_NEW_LINE": "Carácter de nueva línea",
    "M4_DOUBLE_QUOTE": "Carácter de comilla doble",
    "M4_DAY": "Unidad de tiempo: día",
    "M4_MONTH": "Unidad de tiempo: mes",
    "M4_YEAR": "Unidad de tiempo: año",
    "M4_TIMESTAMP": "Tipo timestamp",
    "M4_RETURN": "Valor de retorno",
    "M4_ORGANIZATION_L2_TYPE_FATHER": "Tipo de organización L2: padre",
}


# =============================================================================
# Helpers — generar firma y documentación de funciones
# =============================================================================
def _format_arg(arg, m4_types=M4_TYPE_NAMES):
    """Formatea un argumento para mostrar en firma/documentación."""
    name = arg.get("name", "?")
    m4_type = arg.get("m4_type")
    optional = arg.get("optional", False)
    type_name = m4_types.get(m4_type, str(m4_type)) if m4_type is not None else "?"

    if optional:
        return f"[{name}: {type_name}]"
    return f"{name}: {type_name}"


def _build_signature(func):
    """Construye la firma de una función: Name(arg1: Type, arg2: Type, ...)"""
    name = func.get("name", "?")
    args = func.get("arguments", [])
    var_args = func.get("variable_arguments", False)

    if not args and not var_args:
        return f"{name}()"

    arg_strs = [_format_arg(a) for a in args]
    if var_args:
        arg_strs.append("...")

    return f"{name}({', '.join(arg_strs)})"


def _build_hover_markdown(func):
    """Construye el contenido markdown para hover de una función."""
    sig = _build_signature(func)
    group_name = func.get("group_name", "")
    comment = func.get("comment", "")

    lines = []
    lines.append(f"```ln4\n{sig}\n```")

    if group_name:
        lines.append(f"**Grupo**: {group_name}")

    if comment:
        # Limpiar \r\n y formatear
        clean_comment = comment.replace("\r\n", "\n").strip()
        lines.append("")
        lines.append(clean_comment)

    # Detalles de argumentos
    args = func.get("arguments", [])
    if args:
        lines.append("")
        lines.append("**Argumentos:**")
        for arg in args:
            arg_str = _format_arg(arg)
            lines.append(f"- `{arg_str}`")

    if func.get("variable_arguments"):
        lines.append("- `...` (argumentos variables)")

    return "\n".join(lines)


def _build_snippet(func):
    """Construye un snippet de inserción: Name(${1:arg1}, ${2:arg2})"""
    name = func.get("name", "?")
    args = func.get("arguments", [])
    required_args = [a for a in args if not a.get("optional", False)]

    if not required_args:
        return f"{name}($0)"

    placeholders = []
    for i, arg in enumerate(required_args, 1):
        arg_name = arg.get("name", f"arg{i}")
        placeholders.append(f"${{{i}:{arg_name}}}")

    return f"{name}({', '.join(placeholders)})"


# =============================================================================
# Pre-built completion items — generados una vez
# =============================================================================
_completion_items_cache = None


def get_completion_items():
    """Retorna la lista completa de CompletionItems pre-generados.

    Se genera una sola vez (cache) para evitar reconstruir en cada request.
    Incluye: 301 funciones + keywords + constantes.
    """
    global _completion_items_cache
    if _completion_items_cache is not None:
        return _completion_items_cache

    items = []

    # -- 1. Funciones built-in (301) ------------------------------------------
    catalog = get_catalog()
    if catalog.is_loaded:
        for name in sorted(catalog.get_all_names()):
            func = catalog.get_function(name)
            if func is None:
                continue

            sig = _build_signature(func)
            hover_md = _build_hover_markdown(func)
            snippet = _build_snippet(func)
            group_name = func.get("group_name", "")

            items.append(
                types.CompletionItem(
                    label=func.get("name", name),
                    kind=types.CompletionItemKind.Function,
                    detail=sig,
                    documentation=types.MarkupContent(
                        kind=types.MarkupKind.Markdown,
                        value=hover_md,
                    ),
                    insert_text=snippet,
                    insert_text_format=types.InsertTextFormat.Snippet,
                    sort_text=f"0_{name}",  # Funciones primero
                )
            )

    # -- 2. Keywords ----------------------------------------------------------
    for kw in LN4_KEYWORDS:
        doc = LN4_KEYWORD_DOCS.get(kw.upper(), f"Keyword LN4: {kw}")
        items.append(
            types.CompletionItem(
                label=kw,
                kind=types.CompletionItemKind.Keyword,
                detail=f"Keyword: {kw}",
                documentation=doc,
                sort_text=f"2_{kw.upper()}",  # Keywords después de funciones
            )
        )

    # -- 3. Constantes --------------------------------------------------------
    for const in sorted(LN4_CONSTANTS):
        doc = LN4_CONSTANT_DOCS.get(const, f"Constante LN4: {const}")
        items.append(
            types.CompletionItem(
                label=const,
                kind=types.CompletionItemKind.Constant,
                detail=f"Constante: {const}",
                documentation=doc,
                sort_text=f"1_{const}",  # Constantes entre funciones y keywords
            )
        )

    logger.info(
        "Generados %d items de completion (%d funciones, %d keywords, %d constantes)",
        len(items),
        len([i for i in items if i.kind == types.CompletionItemKind.Function]),
        len([i for i in items if i.kind == types.CompletionItemKind.Keyword]),
        len([i for i in items if i.kind == types.CompletionItemKind.Constant]),
    )

    _completion_items_cache = items
    return items


# =============================================================================
# Hover — resolver identificador bajo cursor
# =============================================================================
def get_hover_for_word(word):
    """Genera información de hover para una palabra.

    Args:
        word: Palabra bajo el cursor (case-insensitive).

    Returns:
        types.Hover o None si no se reconoce la palabra.
    """
    if not word:
        return None

    upper = word.upper()

    # -- 1. Función built-in --------------------------------------------------
    catalog = get_catalog()
    if catalog.is_loaded and catalog.has_function(upper):
        func = catalog.get_function(upper)
        if func:
            md = _build_hover_markdown(func)
            return types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value=md,
                )
            )

    # -- 2. Constante ---------------------------------------------------------
    if upper in LN4_CONSTANTS:
        doc = LN4_CONSTANT_DOCS.get(upper, f"Constante LN4: {upper}")
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**{upper}** — Constante\n\n{doc}",
            )
        )

    # -- 3. Keyword -----------------------------------------------------------
    if upper in LN4_KEYWORD_DOCS:
        doc = LN4_KEYWORD_DOCS[upper]
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**{word}** — Keyword\n\n{doc}",
            )
        )

    return None


# =============================================================================
# Hover para TI items — enriquecido con ITEM_ARGS de BD
# =============================================================================

def build_item_hover_markdown(resolved_symbol, item_type_names=None):
    """Construye documentación markdown para un item de TI.

    Incluye información del item (tipo, descripción) y sus argumentos
    si están disponibles (de M4RCH_ITEM_ARGS).

    Args:
        resolved_symbol: ResolvedSymbol con arguments opcionales.
        item_type_names: Dict de tipo → nombre (ej. {1: "Method"}).

    Returns:
        String markdown con la documentación del item.
    """
    if item_type_names is None:
        from ln4_lsp.db_resolver import ITEM_TYPE_NAMES
        item_type_names = ITEM_TYPE_NAMES

    ti = resolved_symbol.ti_name or "?"
    item = resolved_symbol.item_name or resolved_symbol.name or "?"
    item_type = item_type_names.get(resolved_symbol.item_type, "Item")
    desc_esp = resolved_symbol.description_esp or ""
    desc_eng = resolved_symbol.description_eng or ""
    args = resolved_symbol.arguments

    lines = []

    # Firma con argumentos si están disponibles
    var_args_flag = getattr(resolved_symbol, "variable_arguments", False)
    if args or var_args_flag:
        arg_strs = []
        for arg in (args or []):
            name = arg.get("name", "?")
            m4_type = arg.get("m4_type")
            type_name = M4_TYPE_NAMES.get(m4_type, str(m4_type)) if m4_type is not None else "?"
            arg_strs.append(f"{name}: {type_name}")
        if var_args_flag:
            arg_strs.append("...")
        sig = f"{ti}.{item}({', '.join(arg_strs)})"
    else:
        sig = f"{ti}.{item}"
        if resolved_symbol.item_type == 1:  # Method
            sig += "()"

    lines.append(f"```ln4\n{sig}\n```")
    lines.append(f"**Tipo**: {item_type}")

    if desc_esp:
        lines.append(f"**Descripción**: {desc_esp}")
    if desc_eng and desc_eng != desc_esp:
        lines.append(f"**Description**: {desc_eng}")

    # Detalles de argumentos
    var_args = getattr(resolved_symbol, "variable_arguments", False)
    if args or var_args:
        lines.append("")
        lines.append("**Argumentos:**")
        for arg in (args or []):
            name = arg.get("name", "?")
            m4_type = arg.get("m4_type")
            type_name = M4_TYPE_NAMES.get(m4_type, str(m4_type)) if m4_type is not None else "?"
            arg_type = arg.get("arg_type")
            suffix = ""
            if arg_type == 2:
                suffix = " *(output)*"
            lines.append(f"- `{name}: {type_name}`{suffix}")
        if var_args:
            lines.append("- `...` (argumentos variables)")

    # Tipo M4 del item
    m4_type = resolved_symbol.m4_type
    if m4_type is not None:
        m4_name = M4_TYPE_NAMES.get(m4_type, str(m4_type))
        lines.append(f"\n**Tipo M4**: {m4_name}")

    return "\n".join(lines)


def get_hover_for_item(ti_name, item_name):
    """Genera hover para un item de TI, consultando la BD para args.

    Combina resolve_item_with_args para obtener el item y sus argumentos
    en una sola operación.

    Args:
        ti_name: Nombre del TI.
        item_name: Nombre del item.

    Returns:
        types.Hover o None si no se puede resolver.
    """
    try:
        from ln4_lsp.db_resolver import get_resolver
        resolver = get_resolver()
        if not resolver.is_available:
            return None

        result = resolver.resolve_item_with_args(ti_name, item_name)
        if result is None:
            return None

        md = build_item_hover_markdown(result)
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=md,
            )
        )
    except Exception as e:
        logger.debug("Error en hover para %s.%s: %s", ti_name, item_name, e)
        return None


# =============================================================================
# Completion contextual — items de TI desde BD (tras "TI.")
# =============================================================================

# Mapeo de ITEM_TYPE → CompletionItemKind
_ITEM_TYPE_TO_COMPLETION_KIND = {
    1: types.CompletionItemKind.Method,     # Method
    2: types.CompletionItemKind.Property,   # Property
    3: types.CompletionItemKind.Field,      # Field
    4: types.CompletionItemKind.Interface,  # Concept
}


def _build_item_signature_str(item_name, args, variable_arguments=False):
    """Construye la firma de un item con sus argumentos.

    Args:
        item_name: Nombre del item.
        args: Lista de dicts de argumentos (de ITEM_ARGS), o None.

    Returns:
        String con la firma, ej. "MyMethod(arg1: VarChar, arg2: Number, ...)".
    """
    if not args and not variable_arguments:
        return f"{item_name}()"

    arg_strs = []
    for arg in (args or []):
        name = arg.get("name", "?")
        m4_type = arg.get("m4_type")
        type_name = M4_TYPE_NAMES.get(m4_type, str(m4_type)) if m4_type is not None else "?"
        arg_type = arg.get("arg_type")
        suffix = " [out]" if arg_type == 2 else ""
        arg_strs.append(f"{name}: {type_name}{suffix}")

    if variable_arguments:
        arg_strs.append("...")

    return f"{item_name}({', '.join(arg_strs)})"


def _build_item_snippet(item_name, item_type, args):
    """Construye un snippet de inserción para un item de TI.

    Para métodos (type=1) con argumentos, genera placeholders:
        MyMethod(${1:arg1}, ${2:arg2})
    Para métodos sin argumentos:
        MyMethod()$0
    Para properties/fields/concepts:
        ItemName (sin paréntesis)

    Args:
        item_name: Nombre del item.
        item_type: Tipo de item (1=Method, 2=Property, 3=Field, 4=Concept).
        args: Lista de dicts de argumentos, o None.

    Returns:
        Tupla (snippet_text, insert_text_format).
    """
    if item_type == 1:  # Method
        if args:
            # Solo args de input (arg_type != 2) como placeholders
            input_args = [a for a in args if a.get("arg_type") != 2]
            if input_args:
                placeholders = []
                for i, arg in enumerate(input_args, 1):
                    arg_name = arg.get("name", f"arg{i}")
                    placeholders.append(f"${{{i}:{arg_name}}}")
                return (
                    f"{item_name}({', '.join(placeholders)})",
                    types.InsertTextFormat.Snippet,
                )
            # Todos los args son output — paréntesis vacíos
            return (f"{item_name}()$0", types.InsertTextFormat.Snippet)
        # Sin args
        return (f"{item_name}()$0", types.InsertTextFormat.Snippet)

    # Property, Field, Concept — sin paréntesis
    return (item_name, types.InsertTextFormat.PlainText)


def _build_item_documentation(resolved_symbol):
    """Construye la documentación markdown para un item de TI en completion.

    Versión simplificada de build_item_hover_markdown() para el popup
    de autocompletado (más compacto).

    Args:
        resolved_symbol: ResolvedSymbol con arguments opcionales.

    Returns:
        String markdown.
    """
    from ln4_lsp.db_resolver import ITEM_TYPE_NAMES

    item_type = ITEM_TYPE_NAMES.get(resolved_symbol.item_type, "Item")
    desc_esp = resolved_symbol.description_esp or ""
    desc_eng = resolved_symbol.description_eng or ""
    args = resolved_symbol.arguments

    lines = []
    lines.append(f"**{item_type}**")

    if desc_esp:
        lines.append(desc_esp)
    elif desc_eng:
        lines.append(desc_eng)

    var_args = getattr(resolved_symbol, "variable_arguments", False)
    if args or var_args:
        lines.append("")
        lines.append("**Args:**")
        for arg in (args or []):
            name = arg.get("name", "?")
            m4_type = arg.get("m4_type")
            type_name = M4_TYPE_NAMES.get(m4_type, str(m4_type)) if m4_type is not None else "?"
            suffix = ""
            if arg.get("arg_type") == 2:
                suffix = " *(out)*"
            lines.append(f"- `{name}: {type_name}`{suffix}")
        if var_args:
            lines.append("- `...` (argumentos variables)")

    m4_type = resolved_symbol.m4_type
    if m4_type is not None:
        m4_name = M4_TYPE_NAMES.get(m4_type, str(m4_type))
        lines.append(f"\n**Tipo M4**: {m4_name}")

    return "\n".join(lines)


def get_contextual_completion(ti_name):
    """Genera CompletionItems para los items de un TI específico.

    Consulta la BD en batch (2 queries: items + args) y construye
    CompletionItems con firmas, snippets y documentación enriquecida.

    Args:
        ti_name: Nombre del TI (se busca case-insensitive).

    Returns:
        Lista de CompletionItem, o lista vacía si no hay BD o TI no existe.
    """
    try:
        from ln4_lsp.db_resolver import get_resolver
        resolver = get_resolver()
        if not resolver.is_available:
            return []

        # Batch: items + args en 2 queries
        items = resolver.list_ti_items_with_args(ti_name)
        if not items:
            return []

        completion_items = []
        for resolved in items:
            kind = _ITEM_TYPE_TO_COMPLETION_KIND.get(
                resolved.item_type, types.CompletionItemKind.Variable
            )

            # Firma para detail
            if resolved.item_type == 1:  # Method
                detail = _build_item_signature_str(
                    resolved.item_name, resolved.arguments,
                    variable_arguments=getattr(resolved, "variable_arguments", False),
                )
            else:
                type_label = {
                    2: "Property", 3: "Field", 4: "Concept"
                }.get(resolved.item_type, "Item")
                m4_type = resolved.m4_type
                if m4_type is not None:
                    m4_name = M4_TYPE_NAMES.get(m4_type, str(m4_type))
                    detail = f"{type_label}: {m4_name}"
                else:
                    detail = type_label

            # Snippet
            snippet_text, insert_format = _build_item_snippet(
                resolved.item_name, resolved.item_type, resolved.arguments
            )

            # Documentación
            doc_md = _build_item_documentation(resolved)

            completion_items.append(
                types.CompletionItem(
                    label=resolved.item_name,
                    kind=kind,
                    detail=detail,
                    documentation=types.MarkupContent(
                        kind=types.MarkupKind.Markdown,
                        value=doc_md,
                    ),
                    insert_text=snippet_text,
                    insert_text_format=insert_format,
                    sort_text=f"0_{resolved.item_name}",
                )
            )

        logger.info(
            "Generados %d items contextuales para TI '%s'",
            len(completion_items), ti_name,
        )
        return completion_items

    except Exception as e:
        logger.debug("Error en completion contextual para TI %s: %s", ti_name, e)
        return []
