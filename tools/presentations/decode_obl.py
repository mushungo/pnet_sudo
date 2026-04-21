# tools/presentations/decode_obl.py
"""
Decodifica el blob binario XPACKAGE (formato TLV propietario de Meta4) 
y lo convierte en texto OBL legible.

El formato TLV (Type-Length-Value) inferido es:
0x00 [bytes_longitud] \t Classname<Tipo><Alias>[Propiedades] ... 0xFF (Fin objeto)

Uso:
    python -m tools.presentations.decode_obl <ID_PRESENTATION>
    python -m tools.presentations.decode_obl <ID_PRESENTATION> --output ./output.obl
"""
import sys
import os
import json
import argparse
import struct

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection

def decode_obl_binary(blob):
    """
    Decodifica el binario TLV a una representación de texto OBL.
    """
    if not blob:
        return ""

    text_output = []
    text_output.append("// DECODED OBL (Alpha version)")
    text_output.append("// Note: Binary strings extracted from XPACKAGE")
    
    # Extraer strings imprimibles de al menos 3 caracteres
    # Esto es un fallback de "strings" mientras refinamos el parser binario
    import re
    strings = re.findall(b"[\x20-\x7E]{3,}", blob)
    
    current_indent = 0
    for s in strings:
        try:
            line = s.decode("utf-8")
            if line.upper().startswith("BEGIN"):
                text_output.append("    " * current_indent + line)
                current_indent += 1
            elif line.upper().startswith("END"):
                current_indent = max(0, current_indent - 1)
                text_output.append("    " * current_indent + line)
            else:
                text_output.append("    " * current_indent + line)
        except:
            continue
            
    return "\n".join(text_output)


def get_and_decode(id_presentation, output_file=None):
    """Recupera el blob de BD y lo decodifica."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT XPACKAGE FROM M4RPT_PRESENT_PKG1 WHERE ID_PRESENTATION = ?",
                id_presentation
            )
            row = cursor.fetchone()
            if not row or not row.XPACKAGE:
                return {"status": "error", "message": f"No se encontró XPACKAGE para {id_presentation}"}
            
            decoded_text = decode_obl_binary(row.XPACKAGE)
            
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(decoded_text)
                return {"status": "success", "file": output_file}
            else:
                return {"status": "success", "content": decoded_text}
                
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decodifica presentaciones OBL desde BD.")
    parser.add_argument("id_presentation", help="ID de la presentación")
    parser.add_argument("--output", help="Archivo de salida (.obl)")
    args = parser.parse_args()

    result = get_and_decode(args.id_presentation, args.output)
    print(json.dumps(result, indent=2))
