# obl_lsp/hover.py
"""
Proporciona información de Hover para el OBL LSP.
"""
import re
from lsprotocol import types
from obl_lsp.db_resolver import get_resolver

# Catálogos estáticos
GRANTS_MAP = {
    "1": "Solo Lectura (Read Only)",
    "27": "Lectura y Escritura (Read/Write)",
}

CONSTRUCTIF_MAP = {
    "32": "Flag de Entorno (Environment Dependent)",
}

def get_hover(node, line_text, word, symbol_index):
    """
    Calcula el contenido del hover basado en la palabra y el contexto del nodo.
    """
    resolver = get_resolver()
    contents = []

    # 1. Tokens especiales ##CHNNL, ##ND, ##TM
    m_chn = re.search(r"##CHNNL\[([^\]]+)\]", line_text)
    if m_chn and m_chn.group(1) in word:
        info = resolver.get_channel_info(m_chn.group(1))
        if info:
            contents.append(f"**Canal:** {info['id']}\n\n{info['name']}")
        else:
            contents.append(f"**Canal:** {m_chn.group(1)} (No encontrado)")

    m_nd = re.search(r"##ND\[([^\]]+)\]", line_text)
    if m_nd and m_nd.group(1) in word:
        info = resolver.get_node_info(m_nd.group(1))
        if info:
            contents.append(f"**Nodo:** {info['id']}\n\n{info['name']}\n\n*Canal padre:* {info['channel']}")
        else:
            contents.append(f"**Nodo:** {m_nd.group(1)} (No encontrado)")

    m_tm = re.search(r"##TM\[([^\]]+)\]", line_text)
    if m_tm and m_tm.group(1) in word:
        info = resolver.get_item_info(m_tm.group(1))
        if info:
            contents.append(f"**Item (Traducción):** {info['id']}\n\n{info['name']}\n\n*Tipo interno:* {info['type']}")
        else:
            contents.append(f"**Item:** {m_tm.group(1)} (No encontrado)")

    # 2. Propiedades específicas
    if "Iditem" in line_text and word in line_text:
        item_id = word.strip('"')
        info = resolver.get_item_info(item_id)
        if info:
            contents.append(f"**Item Vinculado:** {info['id']}\n\n{info['name']}")

    if "Grants" in line_text and word in GRANTS_MAP:
        contents.append(f"**Permisos (Grants):** {word}\n\n{GRANTS_MAP[word]}")

    # 3. Rutas *O*
    if "*O*" in line_text and word in line_text:
        # Extraer la ruta completa de la palabra o su vecindad
        path_match = re.search(r"\*O\*[/[\.\w\-]+", line_text)
        if path_match:
            path = path_match.group(0)
            target_node = symbol_index.resolve_path(path)
            if target_node:
                contents.append(f"**Ruta OBL:** {path}\n\nDestino: `{target_node.type} {target_node.alias}` (Línea {target_node.line + 1})")
            else:
                # Intentar resolver rutas relativas
                if ".." in path:
                    contents.append(f"**Ruta OBL (Relativa):** {path}\n\n*Nota: El motor de resolución de rutas relativas está en desarrollo.*")
                else:
                    contents.append(f"**Ruta OBL:** {path}\n\n⚠️ Destino no encontrado en este archivo.")

    if not contents:
        return None

    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value="\n\n---\n\n".join(contents)
        )
    )
