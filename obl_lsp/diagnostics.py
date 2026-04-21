# obl_lsp/diagnostics.py
"""
Analizador de diagnósticos para el OBL LSP.
"""
import re
from lsprotocol import types

def get_diagnostics(text, root_node, symbol_index):
    """
    Analiza el texto y el árbol para generar diagnósticos.
    """
    diagnostics = []
    lines = text.splitlines()

    # 1. Validar rutas *O* rotas
    re_path = re.compile(r"\*O\*[/[\.\w]+")
    for i, line in enumerate(lines):
        for match in re_path.finditer(line):
            path = match.group(0)
            target = symbol_index.resolve_path(path)
            if not target:
                diagnostics.append(types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=i, character=match.start()),
                        end=types.Position(line=i, character=match.end())
                    ),
                    message=f"Ruta OBL no resuelta: {path}",
                    severity=types.DiagnosticSeverity.Warning,
                    source="obl-lsp"
                ))

    # 2. Validar BEGIN/END balanceados
    # (El parser recursivo ya hace esto implícitamente, pero aquí podemos
    # reportar líneas específicas si el stack no está vacío al final)
    # Por ahora, mantenemos diagnósticos simples de rutas que es el valor principal.

    return diagnostics
