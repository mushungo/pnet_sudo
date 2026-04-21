# obl_lsp/parser.py
"""
Parser recursivo para el lenguaje OBL.
Convierte texto OBL en un árbol de nodos (OblNode).
"""
import re

class OblNode:
    def __init__(self, node_type, alias, line, col):
        self.type = node_type
        self.alias = alias
        self.line = line  # 0-indexed
        self.col = col    # 0-indexed
        self.properties = {}
        self.children = []
        self.parent = None
        self.end_line = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def __repr__(self):
        return f"OblNode({self.type}, {self.alias}, children={len(self.children)})"

def parse_obl(text):
    """
    Parsea el texto OBL y retorna la raíz del árbol (generalmente BEGIN Presentation).
    """
    lines = text.splitlines()
    root = None
    stack = []
    
    re_begin = re.compile(r"^\s*BEGIN\s+([\w\.]+)\s+([\w\.\-]+)", re.IGNORECASE)
    re_end = re.compile(r"^\s*END\b", re.IGNORECASE)
    re_prop = re.compile(r"^\s*([\w\.]+)\s*=\s*(.+)$", re.IGNORECASE)

    for i, line in enumerate(lines):
        # BEGIN
        m_begin = re_begin.search(line)
        if m_begin:
            node_type = m_begin.group(1)
            alias = m_begin.group(2)
            col = line.find(m_begin.group(0))
            new_node = OblNode(node_type, alias, i, col)
            
            if stack:
                stack[-1].add_child(new_node)
            else:
                if not root: root = new_node
            
            stack.append(new_node)
            continue

        # END
        m_end = re_end.search(line)
        if m_end:
            if stack:
                closed_node = stack.pop()
                closed_node.end_line = i
            continue

        # Properties
        m_prop = re_prop.search(line)
        if m_prop and stack:
            prop_name = m_prop.group(1)
            prop_value = m_prop.group(2).strip()
            # Quitar comillas si las hay
            if prop_value.startswith('"') and prop_value.endswith('"'):
                prop_value = prop_value[1:-1]
            stack[-1].properties[prop_name] = prop_value

    return root

def find_node_at_position(root, line, col):
    """Encuentra el nodo más profundo que contiene la posición dada."""
    if not root: return None
    
    # Si la línea está fuera del rango del nodo, no es este
    if root.line > line or (root.end_line is not None and root.end_line < line):
        return None
    
    # Buscar en los hijos primero (de abajo hacia arriba en profundidad)
    for child in root.children:
        found = find_node_at_position(child, line, col)
        if found: return found
        
    return root
