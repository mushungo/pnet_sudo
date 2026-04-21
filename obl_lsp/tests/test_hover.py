import sys
import os
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.parser import parse_obl
from obl_lsp.symbol_index import SymbolIndex
from obl_lsp.hover import get_hover

class TestHover(unittest.TestCase):
    def setUp(self):
        self.obl_text = """
BEGIN Presentation Pres2
    BEGIN Form FormMain
        Idchannel = "CHANNEL_1"
        BEGIN Itemlabel txtItem
            Iditem = "ITEM_1"
            Grants = 27
        END
    END
END
"""
        self.root = parse_obl(self.obl_text)
        self.index = SymbolIndex(self.root)

    @patch('obl_lsp.hover.get_resolver')
    def test_item_hover(self, mock_get_resolver):
        # Mock resolver
        mock_resolver = MagicMock()
        mock_resolver.get_item_info.return_value = {
            "id": "ITEM_1",
            "name": "Test Item Name",
            "type": 1
        }
        mock_get_resolver.return_value = mock_resolver
        
        node = self.root.children[0].children[0] # Itemlabel
        line_text = '            Iditem = "ITEM_1"'
        word = "ITEM_1"
        
        hover_result = get_hover(node, line_text, word, self.index)
        self.assertIsNotNone(hover_result)
        self.assertIn("Test Item Name", hover_result.contents.value)

    def test_grants_hover(self):
        node = self.root.children[0].children[0] # Itemlabel
        line_text = '            Grants = 27'
        word = "27"
        
        hover_result = get_hover(node, line_text, word, self.index)
        self.assertIsNotNone(hover_result)
        self.assertIn("Lectura y Escritura", hover_result.contents.value)

if __name__ == "__main__":
    unittest.main()
