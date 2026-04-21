import sys
import os
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.parser import parse_obl
from obl_lsp.symbol_index import SymbolIndex

class TestSymbolIndex(unittest.TestCase):
    def test_path_resolution(self):
        obl_text = """
BEGIN Presentation Pres2
    BEGIN Form FormMain
        BEGIN Splitthorizontal splForm
            BEGIN Splittblock splLeft
                BEGIN Treeview trvTree
                END
            END
        END
    END
END
"""
        root = parse_obl(obl_text)
        index = SymbolIndex(root)
        
        # Test absolute paths
        node = index.resolve_path("*O*/Pres2/FormMain/splForm/splLeft/trvTree")
        self.assertIsNotNone(node)
        self.assertEqual(node.type.upper(), "TREEVIEW")
        self.assertEqual(node.alias, "trvTree")

    def test_method_stripping(self):
        obl_text = """
BEGIN Presentation Pres2
    BEGIN Form FormMain
        BEGIN Button btnSave
        END
    END
END
"""
        root = parse_obl(obl_text)
        index = SymbolIndex(root)
        
        # Test paths with methods
        node = index.resolve_path("*O*/Pres2/FormMain/btnSave.Visible")
        self.assertIsNotNone(node)
        self.assertEqual(node.alias, "btnSave")

if __name__ == "__main__":
    unittest.main()
