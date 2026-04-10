# =============================================================================
# ln4_lsp/signature_help.py — Signature help para LN4
# =============================================================================
# Proporciona información de firma (signature help) cuando el usuario escribe
# '(' o ',' dentro de una llamada a función/método.
#
# Soporta dos fuentes de datos:
#   1. Funciones built-in: del catálogo JSON (301 funciones)
#   2. Métodos de TI: de M4RCH_ITEM_ARGS via DBResolver (77K+ argumentos)
#
# Estrategia de parsing del contexto:
#   - Analizar el texto desde el inicio de la línea hasta la posición del cursor
#   - Identificar la última llamada a función/método abierta (paréntesis sin cerrar)
#   - Contar comas respetando anidamiento para determinar el parámetro activo
# =============================================================================

import logging
import re

from lsprotocol import types

from ln4_lsp.ln4_builtins import get_catalog
from ln4_lsp.completion import M4_TYPE_NAMES, _build_signature, _format_arg

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Parsing de contexto — encontrar la función activa y el parámetro
# =============================================================================

def _find_active_call(text_before_cursor):
    """Analiza el texto antes del cursor para encontrar la llamada activa.

    Busca hacia atrás desde la posición del cursor para encontrar el
    paréntesis de apertura sin cerrar más cercano, luego extrae el
    nombre de la función/método.

    Args:
        text_before_cursor: Texto desde el inicio de la línea (o varias líneas)
                           hasta la posición del cursor.

    Returns:
        Tupla (func_name, ti_name, active_param_index) o None si no hay
        llamada activa. ti_name es None para funciones simples.
        func_name puede ser None si se encontró '(' pero no se pudo
        identificar el nombre.
    """
    if not text_before_cursor:
        return None

    # Rastrear paréntesis para encontrar el '(' sin cerrar más cercano
    # Recorrer de derecha a izquierda
    depth = 0
    paren_pos = -1
    active_param = 0

    i = len(text_before_cursor) - 1
    while i >= 0:
        ch = text_before_cursor[i]

        # Ignorar strings entre comillas
        if ch == '"':
            i -= 1
            while i >= 0 and text_before_cursor[i] != '"':
                i -= 1
            i -= 1
            continue

        if ch == ')':
            depth += 1
        elif ch == '(':
            if depth == 0:
                paren_pos = i
                break
            depth -= 1
        elif ch == ',' and depth == 0:
            active_param += 1

        i -= 1

    if paren_pos < 0:
        return None

    # Extraer el nombre de la función/método antes del '('
    before_paren = text_before_cursor[:paren_pos].rstrip()
    if not before_paren:
        return None

    # Patrones posibles:
    #   FuncName(         → built-in function
    #   TI.Method(        → TI method access
    #   TI..SysMethod(    → system method
    #   CHANNEL!TI.Method( → cross-channel
    #   expr.Method(      → member access (podría ser variable)

    # Intentar match con TI.Method pattern
    # Match: IDENTIFIER.IDENTIFIER justo antes del paréntesis
    member_match = re.search(r'(\w+)\.(\w+)\s*$', before_paren)
    if member_match:
        ti_name = member_match.group(1)
        method_name = member_match.group(2)
        return (method_name, ti_name, active_param)

    # Match: TI..SysMethod
    sys_match = re.search(r'(\w+)\.\.(\w+)\s*$', before_paren)
    if sys_match:
        # System methods — no tienen args en DB, pero podríamos informar
        return (sys_match.group(2), None, active_param)

    # Match: simple function name
    func_match = re.search(r'(\w+)\s*$', before_paren)
    if func_match:
        return (func_match.group(1), None, active_param)

    return None


# =============================================================================
# Construcción de SignatureHelp para built-in functions
# =============================================================================

def _build_builtin_signature_help(func, active_param):
    """Construye SignatureHelp para una función built-in del catálogo.

    Args:
        func: Dict de la función del catálogo (ln4_builtins.json).
        active_param: Índice del parámetro activo (0-based).

    Returns:
        types.SignatureHelp
    """
    sig_label = _build_signature(func)
    args = func.get("arguments", [])
    comment = func.get("comment", "")

    # Construir ParameterInformation para cada argumento
    parameters = []
    for arg in args:
        arg_label = _format_arg(arg)
        arg_doc = ""
        arg_type_id = arg.get("arg_type")
        if arg_type_id == 2:
            arg_doc = "(output / by-ref)"
        parameters.append(
            types.ParameterInformation(
                label=arg.get("name", "?"),
                documentation=arg_doc if arg_doc else None,
            )
        )

    # Si tiene argumentos variables, agregar un parámetro "..."
    if func.get("variable_arguments"):
        parameters.append(
            types.ParameterInformation(
                label="...",
                documentation="Argumentos variables",
            )
        )

    # Clamp active_param al rango válido
    if parameters:
        if func.get("variable_arguments") and active_param >= len(parameters) - 1:
            active_param = len(parameters) - 1
        else:
            active_param = min(active_param, len(parameters) - 1)

    # Limpiar comment
    doc = ""
    if comment:
        doc = comment.replace("\r\n", "\n").strip()
    group_name = func.get("group_name", "")
    if group_name:
        doc = f"**{group_name}**\n\n{doc}" if doc else f"**{group_name}**"

    sig_info = types.SignatureInformation(
        label=sig_label,
        documentation=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value=doc,
        ) if doc else None,
        parameters=parameters,
    )

    return types.SignatureHelp(
        signatures=[sig_info],
        active_signature=0,
        active_parameter=active_param,
    )


# =============================================================================
# Construcción de SignatureHelp para métodos de TI (DB-backed)
# =============================================================================

def _build_item_signature_help(ti_name, item_name, item_args, active_param,
                                item_desc=None, variable_arguments=False):
    """Construye SignatureHelp para un método de TI desde ITEM_ARGS.

    Args:
        ti_name: Nombre del TI.
        item_name: Nombre del item/método.
        item_args: Lista de dicts de argumentos (de resolve_item_args).
        active_param: Índice del parámetro activo (0-based).
        item_desc: Descripción del item (opcional).
        variable_arguments: Si el item acepta argumentos variables adicionales
                            más allá de los declarados en ITEM_ARGS.

    Returns:
        types.SignatureHelp
    """
    if not item_args and not variable_arguments:
        # Sin argumentos → firma vacía
        sig_label = f"{ti_name}.{item_name}()"
        return types.SignatureHelp(
            signatures=[types.SignatureInformation(
                label=sig_label,
                parameters=[],
            )],
            active_signature=0,
            active_parameter=0,
        )

    # Construir la firma: TI.Method(arg1: Type, arg2: Type, ...)
    arg_strs = []
    parameters = []
    for arg in (item_args or []):
        name = arg.get("name", "?")
        m4_type = arg.get("m4_type")
        type_name = M4_TYPE_NAMES.get(m4_type, str(m4_type)) if m4_type is not None else "?"
        arg_strs.append(f"{name}: {type_name}")

        arg_doc = ""
        arg_type_id = arg.get("arg_type")
        if arg_type_id == 2:
            arg_doc = "(output / by-ref)"

        parameters.append(
            types.ParameterInformation(
                label=name,
                documentation=arg_doc if arg_doc else None,
            )
        )

    # Si tiene argumentos variables, agregar un parámetro "..."
    if variable_arguments:
        arg_strs.append("...")
        parameters.append(
            types.ParameterInformation(
                label="...",
                documentation="Argumentos variables",
            )
        )

    sig_label = f"{ti_name}.{item_name}({', '.join(arg_strs)})"

    # Clamp active_param al rango válido
    if parameters:
        if variable_arguments and active_param >= len(parameters) - 1:
            active_param = len(parameters) - 1
        else:
            active_param = min(active_param, len(parameters) - 1)

    doc = ""
    if item_desc:
        doc = item_desc

    sig_info = types.SignatureInformation(
        label=sig_label,
        documentation=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value=doc,
        ) if doc else None,
        parameters=parameters,
    )

    return types.SignatureHelp(
        signatures=[sig_info],
        active_signature=0,
        active_parameter=active_param,
    )


# =============================================================================
# Función principal — resolver signature help para una posición
# =============================================================================

def get_signature_help(source, line, character):
    """Genera SignatureHelp para la posición dada en el documento.

    Analiza el contexto de la posición para determinar qué función/método
    se está invocando, luego consulta el catálogo built-in o la BD.

    Args:
        source: Texto completo del documento.
        line: Línea del cursor (0-indexed, LSP convention).
        character: Columna del cursor (0-indexed).

    Returns:
        types.SignatureHelp o None si no hay contexto de llamada.
    """
    lines = source.split("\n")
    if line < 0 or line >= len(lines):
        return None

    # Tomar texto desde el inicio de la línea hasta el cursor
    # Para manejar multi-línea, tomamos hasta 5 líneas previas como contexto
    start_line = max(0, line - 5)
    context_lines = lines[start_line:line + 1]
    if context_lines:
        # La última línea se corta en la posición del cursor
        context_lines[-1] = context_lines[-1][:character]
    text_before = "\n".join(context_lines)

    call_info = _find_active_call(text_before)
    if call_info is None:
        return None

    func_name, ti_name, active_param = call_info

    if func_name is None:
        return None

    # Intentar como built-in function primero
    catalog = get_catalog()
    if catalog.is_loaded and catalog.has_function(func_name):
        func = catalog.get_function(func_name)
        if func:
            return _build_builtin_signature_help(func, active_param)

    # Intentar como método de TI via DB
    if ti_name:
        try:
            from ln4_lsp.db_resolver import get_resolver
            resolver = get_resolver()
            if resolver.is_available:
                item_result = resolver.resolve_item_with_args(ti_name, func_name)
                if item_result and (item_result.arguments or item_result.variable_arguments):
                    desc = item_result.description_esp or item_result.description_eng or ""
                    return _build_item_signature_help(
                        ti_name, func_name, item_result.arguments,
                        active_param, item_desc=desc,
                        variable_arguments=item_result.variable_arguments,
                    )
        except Exception as e:
            logger.debug("Error en signature help para %s.%s: %s", ti_name, func_name, e)

    return None
