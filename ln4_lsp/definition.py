# =============================================================================
# ln4_lsp/definition.py — Orquestador de go-to-definition para LN4
# =============================================================================
# Combina Tier 1 (in-document symbol index) y Tier 2 (DB resolution)
# para proporcionar go-to-definition.
#
# Estrategia de resolución:
#   1. Parsear el documento y construir el SymbolIndex (Tier 1)
#   2. Encontrar el símbolo bajo el cursor
#   3. Si es una variable local → ir a su primera definición en el documento
#   4. Si es un acceso a miembro (TI.ITEM) → consultar la BD (Tier 2)
#   5. Si es una referencia cross-channel → consultar la BD (Tier 2)
#   6. Si es un built-in function → informar (no hay "fuente" para saltar)
#
# El resultado es un DefinitionResult que contiene:
#   - location: (uri, line, column) para saltar en el editor
#   - info: metadatos del símbolo resuelto (para mostrar en hover extendido)
# =============================================================================

import sys
import os
import logging

logger = logging.getLogger("ln4-lsp")

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.symbol_index import (
    build_symbol_index, find_definition_at_position,
    SYM_VARIABLE, SYM_FOR_VAR, SYM_FUNCTION_CALL,
    SYM_MEMBER_ACCESS, SYM_SYSTEM_METHOD, SYM_CHANNEL_REF,
    SYM_HASH_REF, SYM_AT_REF, SYM_IDENTIFIER,
    SymbolOccurrence,
)
from ln4_lsp.db_resolver import get_resolver, ResolvedSymbol
from ln4_lsp.ln4_builtins import get_catalog, is_known_constant


# =============================================================================
# DefinitionResult — resultado del go-to-definition
# =============================================================================
class DefinitionResult:
    """Resultado de una resolución de go-to-definition.

    Attributes:
        uri: URI del documento destino (None si es el documento actual).
        line: Línea destino (0-indexed para LSP).
        column: Columna destino (0-indexed).
        end_line: Línea final del rango.
        end_column: Columna final del rango.
        tooltip: Texto informativo adicional (para hover enriquecido).
        kind: Tipo de resolución ("local", "db_item", "db_rule", "db_ti",
              "db_channel", "builtin_function", "constant").
        resolved: ResolvedSymbol de la BD (si aplica).
    """

    __slots__ = [
        "uri", "line", "column", "end_line", "end_column",
        "tooltip", "kind", "resolved",
    ]

    def __init__(self, line, column, end_line=None, end_column=None,
                 uri=None, tooltip=None, kind="local", resolved=None):
        self.uri = uri
        self.line = line
        self.column = column
        self.end_line = end_line if end_line is not None else line
        self.end_column = end_column if end_column is not None else column + 1
        self.tooltip = tooltip
        self.kind = kind
        self.resolved = resolved

    def __repr__(self):
        loc = f"{self.line}:{self.column}"
        if self.uri:
            loc = f"{self.uri}:{loc}"
        return f"DefinitionResult({self.kind}, {loc})"


# =============================================================================
# resolve_definition — función principal
# =============================================================================
def resolve_definition(tree, source_code, line, column, document_uri=None):
    """Resuelve go-to-definition para la posición dada en el documento.

    Args:
        tree: Parse tree de ANTLR4 (de parse_ln4_source).
        source_code: Texto fuente del documento.
        line: Línea de la posición del cursor (1-indexed, ANTLR4).
        column: Columna de la posición del cursor (0-indexed).
        document_uri: URI del documento actual (para definiciones locales).

    Returns:
        DefinitionResult o None si no se puede resolver.
    """
    if tree is None:
        return None

    # Tier 1: Construir índice de símbolos del documento
    index = build_symbol_index(tree)

    # Buscar el símbolo bajo el cursor
    occurrence = find_definition_at_position(index, source_code, line, column)

    if occurrence is None:
        return None

    # Intentar resolución según el tipo de símbolo
    return _resolve_occurrence(occurrence, index, document_uri)


def _resolve_occurrence(occurrence, index, document_uri=None):
    """Resuelve una ocurrencia de símbolo según su tipo.

    Args:
        occurrence: SymbolOccurrence encontrada bajo el cursor.
        index: SymbolIndex del documento.
        document_uri: URI del documento actual.

    Returns:
        DefinitionResult o None.
    """
    sym_type = occurrence.symbol_type

    # -- Variables locales (asignación, for var) --------------------------
    if sym_type in (SYM_VARIABLE, SYM_FOR_VAR):
        if occurrence.is_definition:
            # Ya estamos en la definición — retornar la misma posición
            return DefinitionResult(
                line=occurrence.line - 1,  # Convertir a 0-indexed
                column=occurrence.column,
                end_column=occurrence.end_column,
                uri=document_uri,
                tooltip=f"Variable local: {occurrence.name}",
                kind="local",
            )
        # Buscar la primera definición
        first_def = index.get_first_definition(occurrence.name)
        if first_def:
            return DefinitionResult(
                line=first_def.line - 1,
                column=first_def.column,
                end_column=first_def.end_column,
                uri=document_uri,
                tooltip=f"Variable local: {first_def.name}",
                kind="local",
            )

    # -- Identificador simple (podría ser variable, constante, TI, etc.) --
    if sym_type == SYM_IDENTIFIER:
        return _resolve_identifier(occurrence, index, document_uri)

    # -- Llamada a función built-in ---------------------------------------
    if sym_type == SYM_FUNCTION_CALL:
        return _resolve_function_call(occurrence, document_uri)

    # -- Acceso a miembro: TI.ITEM ----------------------------------------
    if sym_type == SYM_MEMBER_ACCESS:
        return _resolve_member_access(occurrence, document_uri)

    # -- Método de sistema: TI..SysMethod ---------------------------------
    if sym_type == SYM_SYSTEM_METHOD:
        return _resolve_system_method(occurrence, document_uri)

    # -- Referencia cross-channel: CHANNEL!TI.ITEM ------------------------
    if sym_type == SYM_CHANNEL_REF:
        return _resolve_channel_ref(occurrence, document_uri)

    # -- Hash ref: #ITEM o TI.#ITEM ---------------------------------------
    if sym_type == SYM_HASH_REF:
        return _resolve_hash_ref(occurrence, document_uri)

    # -- At ref: @ITEM_NAME -----------------------------------------------
    if sym_type == SYM_AT_REF:
        return _resolve_at_ref(occurrence, document_uri)

    return None


# =============================================================================
# Resolución por tipo de símbolo
# =============================================================================

def _resolve_identifier(occurrence, index, document_uri):
    """Resuelve un identificador simple.

    Prioridad:
      1. Variable local definida en el documento
      2. Constante conocida (info only)
      3. Función built-in usada como referencia
      4. TI en la BD (Tier 2)
    """
    name = occurrence.name

    # 1. Variable local
    first_def = index.get_first_definition(name)
    if first_def:
        return DefinitionResult(
            line=first_def.line - 1,
            column=first_def.column,
            end_column=first_def.end_column,
            uri=document_uri,
            tooltip=f"Variable local: {first_def.name}",
            kind="local",
        )

    # 2. Constante
    if is_known_constant(name):
        return DefinitionResult(
            line=occurrence.line - 1,
            column=occurrence.column,
            end_column=occurrence.end_column,
            tooltip=f"Constante LN4: {name.upper()}",
            kind="constant",
        )

    # 3. Función built-in
    catalog = get_catalog()
    if catalog.is_loaded and catalog.has_function(name):
        func = catalog.get_function(name)
        return DefinitionResult(
            line=occurrence.line - 1,
            column=occurrence.column,
            end_column=occurrence.end_column,
            tooltip=f"Función built-in: {func['name']}",
            kind="builtin_function",
        )

    # 4. TI en la BD (Tier 2)
    try:
        resolver = get_resolver()
        if resolver.is_available:
            ti_result = resolver.resolve_ti(name)
            if ti_result:
                desc = ti_result.description_esp or ti_result.description_eng or ""
                return DefinitionResult(
                    line=occurrence.line - 1,
                    column=occurrence.column,
                    end_column=occurrence.end_column,
                    tooltip=f"TI: {ti_result.name} — {desc}".strip(" —"),
                    kind="db_ti",
                    resolved=ti_result,
                )
    except Exception as e:
        logger.debug("Error en Tier 2 para identificador '%s': %s", name, e)

    return None


def _resolve_function_call(occurrence, document_uri):
    """Resuelve una llamada a función built-in."""
    catalog = get_catalog()
    if catalog.is_loaded and catalog.has_function(occurrence.name):
        func = catalog.get_function(occurrence.name)
        return DefinitionResult(
            line=occurrence.line - 1,
            column=occurrence.column,
            end_column=occurrence.end_column,
            tooltip=f"Función built-in: {func['name']}",
            kind="builtin_function",
        )
    return None


def _resolve_member_access(occurrence, document_uri):
    """Resuelve acceso a miembro: TI.ITEM o TI.METHOD(args).

    Tier 2: consulta M4RCH_ITEMS para el par (TI, ITEM).
    Si el item tiene una regla LN4, también obtiene el source code.
    """
    ti_name = occurrence.context_ti
    item_name = occurrence.name

    if not ti_name:
        return None

    try:
        resolver = get_resolver()
        if not resolver.is_available:
            return None

        # Primero intentar resolver el item
        item_result = resolver.resolve_item(ti_name, item_name)
        if item_result:
            # Si es un método (tipo 1), intentar obtener el source code
            if item_result.item_type == 1:
                rule_result = resolver.resolve_rule_source(ti_name, item_name)
                if rule_result and rule_result.source_code:
                    desc = item_result.description_esp or item_result.description_eng or ""
                    return DefinitionResult(
                        line=occurrence.line - 1,
                        column=occurrence.column,
                        end_column=occurrence.end_column,
                        tooltip=f"Método: {ti_name}.{item_name} — {desc}".strip(" —"),
                        kind="db_rule",
                        resolved=rule_result,
                    )

            desc = item_result.description_esp or item_result.description_eng or ""
            from ln4_lsp.db_resolver import ITEM_TYPE_NAMES
            type_label = ITEM_TYPE_NAMES.get(item_result.item_type, "Item")
            return DefinitionResult(
                line=occurrence.line - 1,
                column=occurrence.column,
                end_column=occurrence.end_column,
                tooltip=f"{type_label}: {ti_name}.{item_name} — {desc}".strip(" —"),
                kind="db_item",
                resolved=item_result,
            )
    except Exception as e:
        logger.debug("Error en Tier 2 para %s.%s: %s", ti_name, item_name, e)

    return None


def _resolve_system_method(occurrence, document_uri):
    """Resuelve método de sistema: TI..SysMethod(args).

    Los métodos de sistema son built-in del runtime, no residen en la BD.
    Retornamos info descriptiva.
    """
    ti_name = occurrence.context_ti or "?"
    return DefinitionResult(
        line=occurrence.line - 1,
        column=occurrence.column,
        end_column=occurrence.end_column,
        tooltip=f"Método de sistema: {ti_name}..{occurrence.name}()",
        kind="builtin_function",
    )


def _resolve_channel_ref(occurrence, document_uri):
    """Resuelve referencia cross-channel: CHANNEL!TI.ITEM o CHANNEL!Method().

    Tier 2: verifica canal + TI + item en la BD.
    """
    channel_name = occurrence.context_channel
    ti_name = occurrence.context_ti
    item_name = occurrence.name

    if not channel_name:
        return None

    try:
        resolver = get_resolver()
        if not resolver.is_available:
            return None

        if ti_name and item_name:
            # CHANNEL!TI.ITEM — resolución completa
            result = resolver.resolve_channel_item(channel_name, ti_name, item_name)
            if result:
                desc = result.description_esp or result.description_eng or ""
                return DefinitionResult(
                    line=occurrence.line - 1,
                    column=occurrence.column,
                    end_column=occurrence.end_column,
                    tooltip=f"Cross-channel: {channel_name}!{ti_name}.{item_name} — {desc}".strip(" —"),
                    kind="db_item",
                    resolved=result,
                )
        elif item_name:
            # CHANNEL!Method() — solo canal + método
            channel_result = resolver.resolve_channel(channel_name)
            if channel_result:
                desc = channel_result.description_esp or channel_result.description_eng or ""
                return DefinitionResult(
                    line=occurrence.line - 1,
                    column=occurrence.column,
                    end_column=occurrence.end_column,
                    tooltip=f"Canal: {channel_name} — {desc}".strip(" —"),
                    kind="db_channel",
                    resolved=channel_result,
                )
    except Exception as e:
        logger.debug(
            "Error en Tier 2 para %s!%s.%s: %s",
            channel_name, ti_name, item_name, e,
        )

    return None


def _resolve_hash_ref(occurrence, document_uri):
    """Resuelve hash ref: #ITEM o TI.#ITEM.

    Tier 2: busca el item en la BD.
    """
    ti_name = occurrence.context_ti
    item_name = occurrence.name

    if ti_name:
        # TI.#ITEM → resolver como member access
        return _resolve_member_access(occurrence, document_uri)

    # #ITEM sin contexto de TI — no podemos resolver sin saber el TI
    return DefinitionResult(
        line=occurrence.line - 1,
        column=occurrence.column,
        end_column=occurrence.end_column,
        tooltip=f"Hash reference: #{item_name}",
        kind="constant",
    )


def _resolve_at_ref(occurrence, document_uri):
    """Resuelve at ref: @ITEM_NAME.

    @ITEM es una auto-referencia al item actual del TI.
    Sin contexto de TI (que depende de la regla que se está editando),
    solo podemos informar que es una referencia @.

    Tier 2: si supiéramos el TI del documento actual, podríamos resolver.
    """
    item_name = occurrence.name

    return DefinitionResult(
        line=occurrence.line - 1,
        column=occurrence.column,
        end_column=occurrence.end_column,
        tooltip=f"Item self-reference: @{item_name}",
        kind="constant",
    )
