import sys
import os
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.parser import parse_obl

class TestOblParser(unittest.TestCase):
    def test_basic_parse(self):
        obl_text = """
BEGIN Presentation Pres1
    Idchannel = "CHANNEL_ID"
    BEGIN Form Form1
        Width = 100
    END
END
"""
        root = parse_obl(obl_text)
        self.assertIsNotNone(root)
        self.assertEqual(root.type.upper(), "PRESENTATION")
        self.assertEqual(root.alias, "Pres1")
        self.assertEqual(root.properties.get("Idchannel"), "CHANNEL_ID")
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].type.upper(), "FORM")

if __name__ == "__main__":
    unittest.main()
