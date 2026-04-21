# obl_lsp/definition.py
"""
Proporciona Go-to-Definition para el OBL LSP.
"""
import re
from lsprotocol import types

def get_definition(line_text, word, symbol_index):
    """
    Resuelve la definición para una palabra dada.
    Soporta rutas *O* y llamadas a presentaciones (.Call).
    """
    # 1. Rutas *O*
    if "*O*" in line_text:
        # Extraer la ruta completa que contiene la palabra
        path_match = re.search(r"\*O\*[/[\.\w]+", line_text)
        if path_match:
            path = path_match.group(0)
            target_node = symbol_index.resolve_path(path)
            if target_node:
                return [types.Location(
                    uri="", # Se rellenará en el server
                    range=types.Range(
                        start=types.Position(line=target_node.line, character=target_node.col),
                        end=types.Position(line=target_node.line, character=target_node.col + len(target_node.alias))
                    )
                )]

    # 2. Llamadas a sub-presentaciones en Exeblocks .Call(Alias)
    m_call = re.search(r"\.Call\((\w+)\)", line_text)
    if m_call and word == m_call.group(1):
        alias = m_call.group(1)
        # Buscar BEGIN Presentation alias
        target_node = symbol_index.alias_map.get(alias)
        if target_node:
            return [types.Location(
                uri="",
                range=types.Range(
                    start=types.Position(line=target_node.line, character=target_node.col),
                    end=types.Position(line=target_node.line, character=target_node.col + len(target_node.alias))
                )
            )]

    return None
