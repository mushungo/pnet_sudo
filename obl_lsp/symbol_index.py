# obl_lsp/symbol_index.py
"""
Índice de símbolos para el lenguaje OBL.
Mapea alias y rutas *O* a nodos físicos en el archivo.
"""

class SymbolIndex:
    def __init__(self, root_node):
        self.root = root_node
        self.alias_map = {}  # alias -> OblNode
        self.path_map = {}   # path -> OblNode
        self._build_index(root_node, "")

    def _build_index(self, node, current_path):
        if not node: return
        
        # El root suele ser BEGIN Presentation Pres2
        # La ruta OBL empieza por /Pres2/...
        # Pero a veces el root no tiene path base si no es Presentation
        new_path = f"{current_path}/{node.alias}"
        
        # Guardar en mapas (case-insensitive para alias si es necesario, 
        # pero PeopleNet suele ser estricto con rutas *O*)
        self.alias_map[node.alias] = node
        self.path_map[new_path] = node
        
        # Caso especial: Presentation dentro de Exeblocks
        if node.type.upper() == "PRESENTATION":
            # Permitir acceso directo por Alias para .Call()
            self.alias_map[node.alias] = node

        for child in node.children:
            self._build_index(child, new_path)

    def resolve_path(self, path):
        """
        Resuelve una ruta *O*.
        Ej: *O*/Pres2/FormMain/splForm -> retorna el nodo splForm
        """
        clean_path = path
        if path.startswith("*O*"):
            clean_path = path[3:]
        
        # Eliminar métodos al final si existen (ej: .Call o .Visible)
        if "." in clean_path:
            clean_path = clean_path.split(".")[0]
            
        return self.path_map.get(clean_path)

    def get_all_symbols(self):
        """Retorna todos los símbolos para el Outline de VS Code."""
        symbols = []
        def collect(node):
            symbols.append(node)
            for child in node.children:
                collect(child)
        collect(self.root)
        return symbols
