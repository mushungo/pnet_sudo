# obl_lsp/server.py
"""
Servidor LSP para OBL.
"""
import logging
import os
import sys
from pygls.server import LanguageServer
from lsprotocol import types

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.parser import parse_obl, find_node_at_position
from obl_lsp.symbol_index import SymbolIndex
from obl_lsp.hover import get_hover
from obl_lsp.definition import get_definition
from obl_lsp.diagnostics import get_diagnostics

class OblLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.documents_tree = {}  # uri -> root_node
        self.documents_index = {} # uri -> SymbolIndex

obl_server = OblLanguageServer("obl-lsp", "0.1.0")
logger = logging.getLogger("obl-lsp")

@obl_server.feature(types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params):
    """Acción al abrir un documento."""
    ls.show_message("OBL Document Opened")
    _parse_and_index(ls, params.text_document.uri)

@obl_server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls, params):
    """Acción al cambiar un documento."""
    _parse_and_index(ls, params.text_document.uri)

def _parse_and_index(ls, uri):
    doc = ls.workspace.get_document(uri)
    root = parse_obl(doc.source)
    ls.documents_tree[uri] = root
    index = SymbolIndex(root) if root else None
    ls.documents_index[uri] = index
    
    # Publicar diagnósticos
    if root and index:
        diagnostics = get_diagnostics(doc.source, root, index)
        ls.publish_diagnostics(uri, diagnostics)

@obl_server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls, params):
    uri = params.text_document.uri
    root = ls.documents_tree.get(uri)
    index = ls.documents_index.get(uri)
    if not root or not index: return None

    doc = ls.workspace.get_document(uri)
    line = params.position.line
    col = params.position.character
    
    node = find_node_at_position(root, line, col)
    if not node: return None

    line_text = doc.lines[line]
    # Extraer la palabra bajo el cursor de forma simple
    word = doc.get_word_at_position(params.position)
    
    return get_hover(node, line_text, word, index)

@obl_server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(ls, params):
    uri = params.text_document.uri
    root = ls.documents_tree.get(uri)
    index = ls.documents_index.get(uri)
    if not root or not index: return None

    doc = ls.workspace.get_document(uri)
    line_text = doc.lines[params.position.line]
    word = doc.get_word_at_position(params.position)
    
    locs = get_definition(line_text, word, index)
    if locs:
        for loc in locs:
            loc.uri = uri # El uri es local en esta fase
        return locs
    return None

@obl_server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls, params):
    uri = params.text_document.uri
    root = ls.documents_tree.get(uri)
    if not root: return []

    symbols = []
    def build_symbols(node):
        symbol = types.DocumentSymbol(
            name=f"{node.type} {node.alias}",
            kind=types.SymbolKind.Class if node.type.upper() in ["PRESENTATION", "FORM"] else types.SymbolKind.Field,
            range=types.Range(
                start=types.Position(line=node.line, character=node.col),
                end=types.Position(line=node.end_line if node.end_line else node.line, character=80)
            ),
            selection_range=types.Range(
                start=types.Position(line=node.line, character=node.col),
                end=types.Position(line=node.line, character=node.col + len(node.type) + 1 + len(node.alias))
            ),
            children=[build_symbols(c) for c in node.children]
        )
        return symbol

    return [build_symbols(root)]
