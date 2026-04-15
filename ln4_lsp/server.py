# =============================================================================
# ln4_lsp/server.py — Servidor LSP para el lenguaje LN4 de PeopleNet
# =============================================================================
# Fase 5+ del LSP: servidor con diagnósticos, autocompletado, hover,
# go-to-definition y signature help.
#   - Sincronización de documentos (open/change/close)
#   - Parsing con gramática ANTLR4 en cada cambio
#   - Publicación de diagnósticos:
#       * Errores de sintaxis (ANTLR4 error listener)
#       * Funciones desconocidas (warning) — validadas contra catálogo de 301 built-ins
#       * Aridad incorrecta (error) — min/max args + argumentos variables
#   - Autocompletado: 301 funciones built-in + keywords + constantes
#   - Autocompletado contextual: items de TI desde BD tras "TI." (con args)
#   - Hover: documentación de funciones, constantes, keywords y TI items (BD)
#   - Go-to-definition: variables locales (Tier 1) + TI/items/canales via BD (Tier 2)
#   - Signature help: firmas de funciones built-in y métodos de TI (BD)
#
# Uso:
#   python -m ln4_lsp             # STDIO (para editores)
#   python -m ln4_lsp --tcp       # TCP (para desarrollo/debug)
# =============================================================================

import logging
import sys
import os

from lsprotocol import types
from pygls.server import LanguageServer

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

# -- Ajustar sys.path para importar los módulos generados ---------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.generated.LN4Lexer import LN4Lexer
from ln4_lsp.generated.LN4Parser import LN4Parser
from ln4_lsp.semantic import analyze_semantics, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO
from ln4_lsp.completion import get_completion_items, get_hover_for_word, get_hover_for_item, get_hover_for_sentence, get_contextual_completion
from ln4_lsp.definition import resolve_definition
from ln4_lsp.signature_help import get_signature_help

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Custom ANTLR4 Error Listener — captura errores de sintaxis
# =============================================================================
class LN4ErrorListener(ErrorListener):
    """Recolecta errores de sintaxis del parser ANTLR4 como una lista de
    tuplas (line, column, message) para luego convertirlos en LSP Diagnostics."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append((line, column, msg, offendingSymbol))


# =============================================================================
# Funciones auxiliares de parsing
# =============================================================================
def parse_ln4_source(source_code):
    """Parsea código LN4 y retorna errores de sintaxis y el parse tree.

    Args:
        source_code: Texto fuente del documento LN4.

    Returns:
        Tupla (errors, tree) donde:
          - errors: Lista de tuplas (line, column, message, offendingSymbol).
            line es 1-indexed (ANTLR4 convention).
          - tree: Parse tree de ANTLR4 (retornado por parser.program()).
    """
    error_listener = LN4ErrorListener()

    input_stream = InputStream(source_code)
    lexer = LN4Lexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)

    token_stream = CommonTokenStream(lexer)
    parser = LN4Parser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    # Ejecutar el parsing completo
    tree = parser.program()

    return error_listener.errors, tree


def errors_to_diagnostics(errors):
    """Convierte errores de ANTLR4 en LSP Diagnostics.

    Args:
        errors: Lista de (line, column, message, offendingSymbol) del parser.

    Returns:
        Lista de types.Diagnostic.
    """
    diagnostics = []

    for line, column, msg, symbol in errors:
        # ANTLR4 line es 1-indexed, LSP es 0-indexed
        lsp_line = max(0, line - 1)
        lsp_col = max(0, column)

        # Calcular el rango del token problemático
        if symbol is not None and hasattr(symbol, "text") and symbol.text:
            end_col = lsp_col + len(symbol.text)
        else:
            end_col = lsp_col + 1

        diagnostics.append(
            types.Diagnostic(
                message=msg,
                severity=types.DiagnosticSeverity.Error,
                source="ln4",
                range=types.Range(
                    start=types.Position(line=lsp_line, character=lsp_col),
                    end=types.Position(line=lsp_line, character=end_col),
                ),
            )
        )

    return diagnostics


def semantic_to_diagnostics(semantic_diags):
    """Convierte diagnósticos semánticos en LSP Diagnostics.

    Args:
        semantic_diags: Lista de (line, column, end_column, message, severity)
                       del analizador semántico.

    Returns:
        Lista de types.Diagnostic.
    """
    SEVERITY_MAP = {
        SEVERITY_ERROR: types.DiagnosticSeverity.Error,
        SEVERITY_WARNING: types.DiagnosticSeverity.Warning,
        SEVERITY_INFO: types.DiagnosticSeverity.Information,
    }

    diagnostics = []

    for line, column, end_column, msg, severity in semantic_diags:
        # ANTLR4 line es 1-indexed, LSP es 0-indexed
        lsp_line = max(0, line - 1)
        lsp_col = max(0, column)
        lsp_end_col = max(lsp_col + 1, end_column)

        diagnostics.append(
            types.Diagnostic(
                message=msg,
                severity=SEVERITY_MAP.get(severity, types.DiagnosticSeverity.Warning),
                source="ln4-semantic",
                range=types.Range(
                    start=types.Position(line=lsp_line, character=lsp_col),
                    end=types.Position(line=lsp_line, character=lsp_end_col),
                ),
            )
        )

    return diagnostics


# =============================================================================
# Servidor LSP
# =============================================================================
class LN4LanguageServer(LanguageServer):
    """Servidor LSP para el lenguaje LN4 de PeopleNet.

    Fase 5+: diagnósticos de sintaxis y semánticos, autocompletado, hover,
    go-to-definition y signature help.
    """

    def __init__(self):
        super().__init__("ln4-language-server", "v0.6.0")
        # Cache de parse trees por URI (para go-to-definition sin re-parsear)
        self._parse_trees = {}

    def parse_and_publish(self, uri):
        """Parsea un documento y publica los diagnósticos al cliente.

        Ejecuta dos fases de análisis:
          1. Parsing ANTLR4 → errores de sintaxis
          2. Análisis semántico → funciones desconocidas, aridad incorrecta

        Los diagnósticos semánticos solo se ejecutan si el parsing fue exitoso
        (sin errores de sintaxis), porque un árbol con errores puede generar
        falsos positivos en el análisis semántico.

        Args:
            uri: URI del documento a parsear.
        """
        try:
            doc = self.workspace.get_text_document(uri)
            source = doc.source
        except Exception as e:
            logger.error("Error al obtener documento %s: %s", uri, e)
            return

        diagnostics = []

        try:
            errors, tree = parse_ln4_source(source)
            syntax_diags = errors_to_diagnostics(errors)
            diagnostics.extend(syntax_diags)

            # Cachear el parse tree para go-to-definition
            if not errors and tree is not None:
                self._parse_trees[uri] = tree
            elif uri in self._parse_trees:
                # Mantener el último tree válido si hay errores
                pass

            # Fase 2: análisis semántico — solo si no hay errores de sintaxis
            if not errors and tree is not None:
                try:
                    semantic_diags = analyze_semantics(tree)
                    diagnostics.extend(semantic_to_diagnostics(semantic_diags))
                except Exception as e:
                    logger.error("Error en análisis semántico de %s: %s", uri, e)

        except Exception as e:
            logger.error("Error al parsear %s: %s", uri, e)
            # En caso de error interno del parser, reportar un diagnóstico genérico
            diagnostics = [
                types.Diagnostic(
                    message=f"Error interno del parser LN4: {e}",
                    severity=types.DiagnosticSeverity.Error,
                    source="ln4",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                )
            ]

        self.publish_diagnostics(
            uri,
            diagnostics=diagnostics,
            version=doc.version if doc else None,
        )

        if diagnostics:
            syntax_count = len([d for d in diagnostics if d.source == "ln4"])
            semantic_count = len([d for d in diagnostics if d.source == "ln4-semantic"])
            logger.info(
                "Publicados %d diagnósticos (%d syntax, %d semantic) para %s",
                len(diagnostics), syntax_count, semantic_count, uri,
            )
        else:
            logger.debug("Sin errores en %s", uri)


# -- Instancia global del servidor -------------------------------------------
server = LN4LanguageServer()


# =============================================================================
# Handlers LSP — Sincronización de documentos
# =============================================================================

@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LN4LanguageServer, params: types.DidOpenTextDocumentParams):
    """Parsea el documento cuando se abre."""
    logger.info("Documento abierto: %s", params.text_document.uri)
    ls.parse_and_publish(params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LN4LanguageServer, params: types.DidChangeTextDocumentParams):
    """Re-parsea el documento cuando cambia."""
    logger.debug("Documento modificado: %s", params.text_document.uri)
    ls.parse_and_publish(params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: LN4LanguageServer, params: types.DidCloseTextDocumentParams):
    """Limpia diagnósticos y cache cuando se cierra el documento."""
    logger.info("Documento cerrado: %s", params.text_document.uri)
    # Limpiar cache de parse tree
    ls._parse_trees.pop(params.text_document.uri, None)
    ls.publish_diagnostics(
        params.text_document.uri,
        diagnostics=[],
    )


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: LN4LanguageServer, params: types.DidSaveTextDocumentParams):
    """Re-parsea en cada guardado (por si el cliente no envía didChange)."""
    logger.info("Documento guardado: %s", params.text_document.uri)
    ls.parse_and_publish(params.text_document.uri)


# =============================================================================
# Handlers LSP — Autocompletado
# =============================================================================

@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=[".", "!", "#", "@"]),
)
def completion(
    ls: LN4LanguageServer, params: types.CompletionParams
) -> types.CompletionList:
    """Proporciona autocompletado para funciones built-in, keywords, constantes
    y items de TI (contextual).

    Cuando el trigger es '.', intenta detectar el TI name antes del punto
    y consulta la BD para listar sus items con argumentos enriquecidos.
    En cualquier otro caso, retorna la lista estática de built-ins.
    """
    # Detectar si es completion contextual tras "TI."
    trigger = None
    if params.context:
        trigger = params.context.trigger_character

    if trigger == ".":
        try:
            doc = ls.workspace.get_text_document(params.text_document.uri)
            line_text = doc.source.split("\n")[params.position.line]
            col = params.position.character

            # Extraer el identificador antes del "."
            # El cursor está después del ".", así que buscamos antes de col-1
            import re
            before_dot = line_text[:max(0, col - 1)].rstrip()
            ti_match = re.search(r'(\w+)\s*$', before_dot)
            if ti_match:
                ti_name = ti_match.group(1)
                contextual_items = get_contextual_completion(ti_name)
                if contextual_items:
                    logger.debug(
                        "Completion contextual: %d items para TI '%s'",
                        len(contextual_items), ti_name,
                    )
                    return types.CompletionList(
                        is_incomplete=False, items=contextual_items
                    )
        except Exception as e:
            logger.debug("Error en completion contextual: %s", e)

    # Fallback: lista estática de built-ins + keywords + constantes
    items = get_completion_items()
    return types.CompletionList(is_incomplete=False, items=items)


# =============================================================================
# Handlers LSP — Hover
# =============================================================================

@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(
    ls: LN4LanguageServer, params: types.HoverParams
) -> types.Hover | None:
    """Muestra documentación al pasar el cursor sobre un identificador.

    Prioridad:
      1. Funciones built-in, constantes, keywords (catálogo local)
      2. Sentences (Load_Blk, Load_Prg, SYS_SENTENCE) — desde BD
      3. TI items con argumentos (BD, M4RCH_ITEMS + M4RCH_ITEM_ARGS + BDL)
    """
    try:
        doc = ls.workspace.get_text_document(params.text_document.uri)
        word = doc.word_at_position(params.position)
    except Exception as e:
        logger.error("Error obteniendo palabra en hover: %s", e)
        return None

    if not word:
        return None

    # 1. Built-in functions, constants, keywords
    result = get_hover_for_word(word)
    if result:
        logger.debug("Hover para '%s': built-in encontrado", word)
        return result

    # 2. Sentence hover — detectar si la palabra es un argumento de
    #    Load_Blk(), Load_Prg() o SYS_SENTENCE()
    try:
        line_text = doc.source.split("\n")[params.position.line]
        import re
        # Patrón: Load_Blk("SENTENCE_ID") / Load_Prg("SENTENCE_ID") /
        #         SYS_SENTENCE("SENTENCE_ID") — la palabra bajo el cursor
        #         puede estar entre comillas o no (identificador sin comillas)
        sentence_pattern = re.compile(
            r'(?:Load_Blk|Load_Prg|SYS_SENTENCE)\s*\(\s*["\']?(\w+)["\']?',
            re.IGNORECASE,
        )
        for m in sentence_pattern.finditer(line_text):
            col = params.position.character
            # Verificar que el cursor está dentro del argumento capturado
            if m.start(1) <= col <= m.end(1):
                sentence_id = m.group(1)
                sentence_result = get_hover_for_sentence(sentence_id)
                if sentence_result:
                    logger.debug("Hover para '%s': sentence encontrada", sentence_id)
                    return sentence_result
    except Exception as e:
        logger.debug("Error en hover sentence para '%s': %s", word, e)

    # 3. TI item hover (buscar patrón TI.ITEM en la línea)
    try:
        line_text = doc.source.split("\n")[params.position.line]
        col = params.position.character
        # Buscar hacia atrás si hay un '.' antes de la palabra actual
        import re
        # Patrón: IDENTIFIER.word donde word está en la posición del cursor
        # Buscamos: "TI_NAME." justo antes de la posición donde empieza 'word'
        word_start = line_text.rfind(word, 0, col + len(word))
        if word_start > 0:
            before = line_text[:word_start]
            ti_match = re.search(r'(\w+)\.\s*$', before)
            if ti_match:
                ti_name = ti_match.group(1)
                item_result = get_hover_for_item(ti_name, word)
                if item_result:
                    logger.debug("Hover para '%s.%s': DB item encontrado", ti_name, word)
                    return item_result
    except Exception as e:
        logger.debug("Error en hover DB para '%s': %s", word, e)

    return result


# =============================================================================
# Handlers LSP — Go-to-definition
# =============================================================================

@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(
    ls: LN4LanguageServer, params: types.DefinitionParams
) -> types.Location | None:
    """Resuelve go-to-definition para el símbolo bajo el cursor.

    Tier 1: definiciones locales (variables, for vars) dentro del documento.
    Tier 2: resolución contra la BD (TI items, canales, métodos).
    """
    uri = params.text_document.uri

    try:
        doc = ls.workspace.get_text_document(uri)
        source = doc.source
    except Exception as e:
        logger.error("Error obteniendo documento para definition: %s", e)
        return None

    # Obtener el parse tree (del cache o re-parsear)
    tree = ls._parse_trees.get(uri)
    if tree is None:
        try:
            errors, tree = parse_ln4_source(source)
            if not errors and tree is not None:
                ls._parse_trees[uri] = tree
        except Exception as e:
            logger.error("Error al parsear para definition: %s", e)
            return None

    if tree is None:
        return None

    # Convertir posición LSP (0-indexed) a ANTLR4 (1-indexed line, 0-indexed col)
    antlr_line = params.position.line + 1
    antlr_col = params.position.character

    result = resolve_definition(tree, source, antlr_line, antlr_col, uri)

    if result is None:
        logger.debug("Definition: no se pudo resolver en %d:%d", antlr_line, antlr_col)
        return None

    logger.debug(
        "Definition: %s → %s (%d:%d)",
        result.kind, result.tooltip or "?", result.line, result.column,
    )

    # Construir Location para el cliente
    target_uri = result.uri or uri
    return types.Location(
        uri=target_uri,
        range=types.Range(
            start=types.Position(line=result.line, character=result.column),
            end=types.Position(line=result.end_line, character=result.end_column),
        ),
    )


# =============================================================================
# Handlers LSP — Signature Help
# =============================================================================

@server.feature(
    types.TEXT_DOCUMENT_SIGNATURE_HELP,
    types.SignatureHelpOptions(
        trigger_characters=["(", ","],
        retrigger_characters=[","],
    ),
)
def signature_help(
    ls: LN4LanguageServer, params: types.SignatureHelpParams
) -> types.SignatureHelp | None:
    """Muestra firma de función/método al escribir '(' o ','."""
    try:
        doc = ls.workspace.get_text_document(params.text_document.uri)
        source = doc.source
    except Exception as e:
        logger.error("Error obteniendo documento para signature help: %s", e)
        return None

    result = get_signature_help(
        source,
        params.position.line,
        params.position.character,
    )

    if result:
        sig_label = result.signatures[0].label if result.signatures else "?"
        logger.debug("Signature help: %s (param %d)", sig_label, result.active_parameter)

    return result
