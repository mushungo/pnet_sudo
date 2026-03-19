# =============================================================================
# ln4_lsp/server.py — Servidor LSP para el lenguaje LN4 de PeopleNet
# =============================================================================
# Fase 4 del LSP: servidor con diagnósticos, autocompletado y hover.
#   - Sincronización de documentos (open/change/close)
#   - Parsing con gramática ANTLR4 en cada cambio
#   - Publicación de diagnósticos:
#       * Errores de sintaxis (ANTLR4 error listener)
#       * Funciones desconocidas (warning) — validadas contra catálogo de 301 built-ins
#       * Aridad incorrecta (error) — min/max args + argumentos variables
#   - Autocompletado: 301 funciones built-in + keywords + constantes
#   - Hover: documentación de funciones, constantes y keywords
#
# Uso:
#   python -m ln4_lsp             # STDIO (para editores)
#   python -m ln4_lsp --tcp       # TCP (para desarrollo/debug)
# =============================================================================

import logging
import sys
import os

from lsprotocol import types
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

# -- Ajustar sys.path para importar los módulos generados ---------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.generated.LN4Lexer import LN4Lexer
from ln4_lsp.generated.LN4Parser import LN4Parser
from ln4_lsp.semantic import analyze_semantics, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO
from ln4_lsp.completion import get_completion_items, get_hover_for_word

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

    Fase 4: diagnósticos de sintaxis y semánticos, autocompletado y hover.
    """

    def __init__(self):
        super().__init__("ln4-language-server", "v0.4.0")

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

        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                version=doc.version if doc else None,
                diagnostics=diagnostics,
            )
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
    """Limpia diagnósticos cuando se cierra el documento."""
    logger.info("Documento cerrado: %s", params.text_document.uri)
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=params.text_document.uri,
            diagnostics=[],
        )
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
    """Proporciona autocompletado para funciones built-in, keywords y constantes."""
    items = get_completion_items()
    return types.CompletionList(is_incomplete=False, items=items)


# =============================================================================
# Handlers LSP — Hover
# =============================================================================

@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(
    ls: LN4LanguageServer, params: types.HoverParams
) -> types.Hover | None:
    """Muestra documentación al pasar el cursor sobre un identificador."""
    try:
        doc = ls.workspace.get_text_document(params.text_document.uri)
        word = doc.word_at_position(params.position)
    except Exception as e:
        logger.error("Error obteniendo palabra en hover: %s", e)
        return None

    if not word:
        return None

    result = get_hover_for_word(word)
    if result:
        logger.debug("Hover para '%s': encontrado", word)
    return result
