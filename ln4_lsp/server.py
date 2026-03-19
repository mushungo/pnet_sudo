# =============================================================================
# ln4_lsp/server.py — Servidor LSP para el lenguaje LN4 de PeopleNet
# =============================================================================
# Fase 2 del LSP: servidor básico con pygls.
#   - Sincronización de documentos (open/change/close)
#   - Parsing con gramática ANTLR4 en cada cambio
#   - Publicación de diagnósticos (errores de sintaxis)
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
    """Parsea código LN4 y retorna la lista de errores de sintaxis.

    Args:
        source_code: Texto fuente del documento LN4.

    Returns:
        Lista de tuplas (line, column, message, offendingSymbol).
        line es 1-indexed (ANTLR4 convention).
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
    parser.program()

    return error_listener.errors


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


# =============================================================================
# Servidor LSP
# =============================================================================
class LN4LanguageServer(LanguageServer):
    """Servidor LSP para el lenguaje LN4 de PeopleNet.

    Fase 2: sincronización de documentos y diagnósticos de sintaxis.
    """

    def __init__(self):
        super().__init__("ln4-language-server", "v0.2.0")

    def parse_and_publish(self, uri):
        """Parsea un documento y publica los diagnósticos al cliente.

        Args:
            uri: URI del documento a parsear.
        """
        try:
            doc = self.workspace.get_text_document(uri)
            source = doc.source
        except Exception as e:
            logger.error("Error al obtener documento %s: %s", uri, e)
            return

        try:
            errors = parse_ln4_source(source)
            diagnostics = errors_to_diagnostics(errors)
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
            logger.info(
                "Publicados %d diagnósticos para %s", len(diagnostics), uri
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
