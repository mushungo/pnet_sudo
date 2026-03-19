# =============================================================================
# ln4_lsp/symbol_index.py — Índice de símbolos in-document para LN4
# =============================================================================
# Tier 1 del go-to-definition: camina el parse tree y recolecta todas las
# definiciones de símbolos dentro de un documento LN4.
#
# Símbolos detectados:
#   1. Asignaciones: x = expr  → define variable 'x'
#   2. Variables de For: For i = ... → define variable 'i'
#   3. Llamadas a función standalone: NullValue() → referencia a built-in
#   4. Acceso a miembros: TI.ITEM, TI.METHOD(), TI..SysMethod()
#   5. Acceso cross-channel: CHANNEL!TI.ITEM, CHANNEL!Method()
#   6. Hash refs: #FUNC_NAME, TI.#ITEM
#   7. At refs: @ITEM_NAME
#
# El índice mapea nombres (uppercase) a listas de SymbolOccurrence, cada una
# con su tipo, posición (line, column) y contexto (TI, channel, etc.).
# =============================================================================

import sys
import os
import logging

from antlr4 import CommonTokenStream, InputStream

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.generated.LN4Parser import LN4Parser
from ln4_lsp.generated.LN4Visitor import LN4Visitor

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Tipos de símbolo
# =============================================================================
SYM_VARIABLE = "variable"           # Asignación local: x = expr
SYM_FOR_VAR = "for_variable"        # Variable de For loop: For i = ...
SYM_FUNCTION_CALL = "function_call"  # Llamada a función: Func(args)
SYM_MEMBER_ACCESS = "member_access"  # TI.ITEM o TI.METHOD(args)
SYM_SYSTEM_METHOD = "system_method"  # TI..SysMethod(args)
SYM_CHANNEL_REF = "channel_ref"      # CHANNEL!TI.ITEM
SYM_HASH_REF = "hash_ref"           # #FUNC_NAME o TI.#ITEM
SYM_AT_REF = "at_ref"               # @ITEM_NAME
SYM_IDENTIFIER = "identifier"       # Uso simple de identificador (lectura)


# =============================================================================
# SymbolOccurrence — una ocurrencia de un símbolo en el documento
# =============================================================================
class SymbolOccurrence:
    """Representa una ocurrencia de un símbolo en el documento.

    Attributes:
        name: Nombre original del símbolo (preserva casing).
        symbol_type: Tipo de símbolo (SYM_VARIABLE, SYM_FUNCTION_CALL, etc.)
        line: Línea (1-indexed, ANTLR4 convention).
        column: Columna (0-indexed).
        end_column: Columna final (0-indexed).
        is_definition: True si es una definición (asignación, for var).
        context_ti: Nombre del TI si es acceso a miembro (e.g., "TI_NAME").
        context_channel: Nombre del canal si es cross-channel (e.g., "CHANNEL_NAME").
    """

    __slots__ = [
        "name", "symbol_type", "line", "column", "end_column",
        "is_definition", "context_ti", "context_channel",
    ]

    def __init__(self, name, symbol_type, line, column, end_column,
                 is_definition=False, context_ti=None, context_channel=None):
        self.name = name
        self.symbol_type = symbol_type
        self.line = line
        self.column = column
        self.end_column = end_column
        self.is_definition = is_definition
        self.context_ti = context_ti
        self.context_channel = context_channel

    def __repr__(self):
        parts = [f"{self.symbol_type}:{self.name}@{self.line}:{self.column}"]
        if self.is_definition:
            parts.append("DEF")
        if self.context_ti:
            parts.append(f"TI={self.context_ti}")
        if self.context_channel:
            parts.append(f"CH={self.context_channel}")
        return f"SymbolOccurrence({', '.join(parts)})"


# =============================================================================
# SymbolIndex — índice de símbolos de un documento
# =============================================================================
class SymbolIndex:
    """Índice de símbolos para un documento LN4.

    Almacena todas las ocurrencias de símbolos, indexadas por nombre (uppercase).
    Permite buscar definiciones y usos de un símbolo.
    """

    def __init__(self):
        # {uppercase_name: [SymbolOccurrence, ...]}
        self._symbols = {}

    def add(self, occurrence):
        """Agrega una ocurrencia al índice."""
        key = occurrence.name.upper()
        if key not in self._symbols:
            self._symbols[key] = []
        self._symbols[key].append(occurrence)

    def get_definitions(self, name):
        """Retorna todas las definiciones de un símbolo (case-insensitive).

        Args:
            name: Nombre del símbolo.

        Returns:
            Lista de SymbolOccurrence donde is_definition=True.
        """
        key = name.upper()
        occurrences = self._symbols.get(key, [])
        return [o for o in occurrences if o.is_definition]

    def get_first_definition(self, name):
        """Retorna la primera definición de un símbolo.

        En LN4, la primera asignación es lo más cercano a una "declaración".
        """
        defs = self.get_definitions(name)
        return defs[0] if defs else None

    def get_all_occurrences(self, name):
        """Retorna todas las ocurrencias de un símbolo (case-insensitive)."""
        return self._symbols.get(name.upper(), [])

    def get_member_occurrences(self, ti_name, item_name):
        """Retorna ocurrencias de TI.ITEM (acceso a miembro).

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            Lista de SymbolOccurrence con context_ti matching.
        """
        key = item_name.upper()
        ti_upper = ti_name.upper()
        return [
            o for o in self._symbols.get(key, [])
            if o.context_ti and o.context_ti.upper() == ti_upper
        ]

    def get_channel_occurrences(self, channel_name, ti_name=None, item_name=None):
        """Retorna ocurrencias cross-channel."""
        results = []
        for key, occurrences in self._symbols.items():
            for o in occurrences:
                if o.context_channel and o.context_channel.upper() == channel_name.upper():
                    if ti_name and o.context_ti and o.context_ti.upper() != ti_name.upper():
                        continue
                    if item_name and o.name.upper() != item_name.upper():
                        continue
                    results.append(o)
        return results

    def all_symbols(self):
        """Retorna un dict con todos los símbolos indexados."""
        return dict(self._symbols)

    def definition_names(self):
        """Retorna los nombres de todos los símbolos que tienen definiciones."""
        return {
            name for name, occs in self._symbols.items()
            if any(o.is_definition for o in occs)
        }


# =============================================================================
# SymbolCollector — visitor que construye el SymbolIndex
# =============================================================================
class SymbolCollector(LN4Visitor):
    """Visitor que camina el parse tree y recolecta ocurrencias de símbolos."""

    def __init__(self):
        super().__init__()
        self.index = SymbolIndex()

    def _token_info(self, token):
        """Extrae (line, column, end_column, text) de un token."""
        text = token.getText() if hasattr(token, "getText") else str(token)
        if hasattr(token, "symbol"):
            sym = token.symbol
            return sym.line, sym.column, sym.column + len(sym.text), sym.text
        elif hasattr(token, "line"):
            return token.line, token.column, token.column + len(text), text
        return 1, 0, len(text), text

    # -----------------------------------------------------------------
    # For loop variable
    # -----------------------------------------------------------------
    def visitForBlock(self, ctx):
        """For i = start To end — registra 'i' como definición."""
        id_token = ctx.IDENTIFIER()
        if id_token:
            line, col, end_col, text = self._token_info(id_token)
            self.index.add(SymbolOccurrence(
                name=text,
                symbol_type=SYM_FOR_VAR,
                line=line, column=col, end_column=end_col,
                is_definition=True,
            ))
        return self.visitChildren(ctx)

    # -----------------------------------------------------------------
    # Assignment
    # -----------------------------------------------------------------
    def visitAssignmentOrCall(self, ctx):
        """Detecta asignaciones para registrar definiciones de variables."""
        if ctx.EQ():
            member_expr = ctx.memberExpression()
            if member_expr:
                primary = member_expr.primaryExpression()
                member_tails = member_expr.memberTail()
                if primary and (not member_tails or len(member_tails) == 0):
                    id_node = primary.IDENTIFIER()
                    if id_node and not primary.LPAREN():
                        line, col, end_col, text = self._token_info(id_node)
                        self.index.add(SymbolOccurrence(
                            name=text,
                            symbol_type=SYM_VARIABLE,
                            line=line, column=col, end_column=end_col,
                            is_definition=True,
                        ))
        return self.visitChildren(ctx)

    # -----------------------------------------------------------------
    # Primary expressions — identifiers, function calls, refs
    # -----------------------------------------------------------------
    def visitPrimaryExpression(self, ctx):
        """Registra identificadores, llamadas a función, hash refs y at refs."""
        id_node = ctx.IDENTIFIER()

        if id_node and ctx.LPAREN():
            # Llamada a función: IDENTIFIER(args)
            line, col, end_col, text = self._token_info(id_node)
            self.index.add(SymbolOccurrence(
                name=text,
                symbol_type=SYM_FUNCTION_CALL,
                line=line, column=col, end_column=end_col,
            ))
        elif id_node and not ctx.LPAREN():
            # Identificador simple (variable, constante, TI)
            line, col, end_col, text = self._token_info(id_node)
            self.index.add(SymbolOccurrence(
                name=text,
                symbol_type=SYM_IDENTIFIER,
                line=line, column=col, end_column=end_col,
            ))

        # Hash ref: #FUNC_NAME
        hash_ref = ctx.HASH_REF()
        if hash_ref:
            line, col, end_col, text = self._token_info(hash_ref)
            # Quitar el # para el nombre
            clean_name = text[1:] if text.startswith("#") else text
            self.index.add(SymbolOccurrence(
                name=clean_name,
                symbol_type=SYM_HASH_REF,
                line=line, column=col, end_column=end_col,
            ))

        # At ref: @ITEM_NAME
        at_ref = ctx.AT_REF()
        if at_ref:
            line, col, end_col, text = self._token_info(at_ref)
            clean_name = text[1:] if text.startswith("@") else text
            self.index.add(SymbolOccurrence(
                name=clean_name,
                symbol_type=SYM_AT_REF,
                line=line, column=col, end_column=end_col,
            ))

        return self.visitChildren(ctx)

    # -----------------------------------------------------------------
    # Member tail — dot access, system methods, channel refs
    # -----------------------------------------------------------------
    def visitMemberExpression(self, ctx):
        """Procesa cadenas de acceso a miembros para extraer contexto TI/channel."""
        primary = ctx.primaryExpression()
        member_tails = ctx.memberTail()

        if not member_tails or len(member_tails) == 0:
            return self.visitChildren(ctx)

        # Determinar el identificador base (posible TI)
        base_id = None
        id_node = primary.IDENTIFIER() if primary else None
        if id_node and not primary.LPAREN():
            base_id = id_node.getText()

        # Procesar cada memberTail
        for tail in member_tails:
            self._process_member_tail(tail, base_id)

        return self.visitChildren(ctx)

    def _process_member_tail(self, ctx, base_id):
        """Procesa un memberTail y registra la ocurrencia apropiada.

        memberTail alternativas:
          1. DOT DOT IDENTIFIER (LPAREN argList? RPAREN)?   → ..SysMethod
          2. DOT HASH_REF                                    → .#ITEM
          3. DOT IDENTIFIER (LPAREN argList? RPAREN)?        → .ITEM / .METHOD()
          4. LBRACKET expression RBRACKET                    → [index]
          5. BANG IDENTIFIER DOT IDENTIFIER (LPAREN ...)?    → !TI.ITEM / !TI.METHOD()
          6. BANG IDENTIFIER (LPAREN argList? RPAREN)?       → !Method() / !TI
        """
        dots = ctx.DOT()
        bangs = ctx.BANG()
        ids = ctx.IDENTIFIER()
        hash_ref = ctx.HASH_REF()

        # Count dots and bangs to distinguish alternatives
        dot_count = len(dots) if dots else 0
        has_bang = bool(bangs)

        # Check bang alternatives FIRST (Alt 5, 6) since they can also
        # have dots (e.g., !TI.ITEM has 1 bang + 1 dot + 2 identifiers)
        if has_bang and ids:
            id_list = ids if isinstance(ids, list) else [ids]
            if len(id_list) >= 2 and dot_count >= 1:
                # Alt 5: !TI.ITEM o !TI.METHOD(args?)
                ti_token = id_list[0]
                item_token = id_list[1]
                ti_line, ti_col, ti_end, ti_text = self._token_info(ti_token)
                item_line, item_col, item_end, item_text = self._token_info(item_token)
                # El base_id es el channel en este caso
                self.index.add(SymbolOccurrence(
                    name=item_text,
                    symbol_type=SYM_CHANNEL_REF,
                    line=item_line, column=item_col, end_column=item_end,
                    context_ti=ti_text,
                    context_channel=base_id,
                ))
            elif len(id_list) == 1:
                # Alt 6: !Method(args?) o !TI
                id_token = id_list[0]
                line, col, end_col, text = self._token_info(id_token)
                has_parens = ctx.LPAREN() is not None
                self.index.add(SymbolOccurrence(
                    name=text,
                    symbol_type=SYM_CHANNEL_REF,
                    line=line, column=col, end_column=end_col,
                    context_channel=base_id,
                ))

        elif dot_count == 2 and ids:
            # Alt 1: ..SysMethod(args?)
            id_token = ids[0] if isinstance(ids, list) else ids
            line, col, end_col, text = self._token_info(id_token)
            self.index.add(SymbolOccurrence(
                name=text,
                symbol_type=SYM_SYSTEM_METHOD,
                line=line, column=col, end_column=end_col,
                context_ti=base_id,
            ))

        elif dot_count == 1 and hash_ref:
            # Alt 2: .#ITEM
            line, col, end_col, text = self._token_info(hash_ref)
            clean_name = text[1:] if text.startswith("#") else text
            self.index.add(SymbolOccurrence(
                name=clean_name,
                symbol_type=SYM_HASH_REF,
                line=line, column=col, end_column=end_col,
                context_ti=base_id,
            ))

        elif dot_count == 1 and ids:
            # Alt 3: .ITEM o .METHOD(args?)
            id_token = ids[0] if isinstance(ids, list) else ids
            line, col, end_col, text = self._token_info(id_token)
            self.index.add(SymbolOccurrence(
                name=text,
                symbol_type=SYM_MEMBER_ACCESS,
                line=line, column=col, end_column=end_col,
                context_ti=base_id,
            ))

        # [index] — Alt 4: no registrar (no hay identifier)


# =============================================================================
# Función pública — construir índice de símbolos
# =============================================================================
def build_symbol_index(tree):
    """Construye un SymbolIndex a partir de un parse tree de ANTLR4.

    Args:
        tree: Parse tree de ANTLR4 (retornado por parser.program()).

    Returns:
        SymbolIndex con todas las ocurrencias detectadas.
    """
    collector = SymbolCollector()
    collector.visit(tree)
    return collector.index


def find_definition_at_position(index, source_code, line, column):
    """Encuentra la definición del símbolo en la posición dada.

    Busca el símbolo que abarca la posición (line, column) y retorna
    su primera definición (si existe en el índice).

    Args:
        index: SymbolIndex del documento.
        source_code: Texto fuente del documento.
        line: Línea (1-indexed, ANTLR4 convention).
        column: Columna (0-indexed).

    Returns:
        SymbolOccurrence de la definición, o None si no se encuentra.
    """
    # Buscar el símbolo que contiene esta posición
    for name, occurrences in index.all_symbols().items():
        for occ in occurrences:
            if occ.line == line and occ.column <= column < occ.end_column:
                # Encontramos el símbolo — buscar su definición
                if occ.is_definition:
                    return occ  # Ya está en la definición
                first_def = index.get_first_definition(name)
                if first_def:
                    return first_def
                # Retornar la ocurrencia misma con info de contexto
                # (para que el llamador pueda intentar Tier 2)
                return occ
    return None
