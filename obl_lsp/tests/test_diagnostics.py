import sys
import os
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.parser import parse_obl
from obl_lsp.symbol_index import SymbolIndex
from obl_lsp.diagnostics import get_diagnostics

class TestDiagnostics(unittest.TestCase):
    def test_broken_paths(self):
        obl_text = """
BEGIN Presentation Pres2
    BEGIN Action_call act1
        Sentence = "*O*/Pres2/NonExistent/Control"
    END
END
"""
        root = parse_obl(obl_text)
        index = SymbolIndex(root)
        
        diagnostics = get_diagnostics(obl_text, root, index)
        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Ruta OBL no resuelta", diagnostics[0].message)

    def test_valid_path(self):
        obl_text = """
BEGIN Presentation Pres2
    BEGIN Form Form1
    END
    BEGIN Action_call act1
        Sentence = "*O*/Pres2/Form1"
    END
END
"""
        root = parse_obl(obl_text)
        index = SymbolIndex(root)
        
        diagnostics = get_diagnostics(obl_text, root, index)
        self.assertEqual(len(diagnostics), 0)

if __name__ == "__main__":
    unittest.main()
