# tools/presentations/analyze_obl.py
"""
Analizador semántico de archivos OBL.
Extrae el árbol de componentes, items vinculados, canales, nodos e includes.

Uso:
    python -m tools.presentations.analyze_obl <PATH_TO_OBL>
"""
import sys
import os
import json
import argparse
import re

def analyze_obl(file_path):
    """
    Analiza un archivo OBL y extrae información semántica.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Archivo no encontrado: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    analysis = {
        "presentation_id": None,
        "nodes": set(),
        "items": set(),
        "channels": set(),
        "includes": set(),
        "lookups": [],
        "navigation_tree": [],
        "stats": {
            "total_lines": len(lines),
            "control_count": 0
        }
    }

    # Regex patterns
    re_begin = re.compile(r"^\s*BEGIN\s+(\w+)\s+(\w+)", re.IGNORECASE)
    re_prop_idchannel = re.compile(r"^\s*Idchannel\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
    re_prop_idnode = re.compile(r"^\s*Idnode\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
    re_prop_iditem = re.compile(r"^\s*Iditem\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
    re_prop_idinclude = re.compile(r"^\s*Idinclude\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
    re_token_nd = re.compile(r"##ND\[([^\]]+)\]")
    re_token_chnnl = re.compile(r"##CHNNL\[([^\]]+)\]")
    re_token_tm = re.compile(r"##TM\[([^\]]+)\]")

    for line in lines:
        # BEGIN blocks
        m_begin = re_begin.search(line)
        if m_begin:
            analysis["stats"]["control_count"] += 1
            if m_begin.group(1).upper() == "PRESENTATION" and not analysis["presentation_id"]:
                analysis["presentation_id"] = m_begin.group(2)

        # Properties
        m_chn = re_prop_idchannel.search(line)
        if m_chn: analysis["channels"].add(m_chn.group(1))

        m_nd = re_prop_idnode.search(line)
        if m_nd: analysis["nodes"].add(m_nd.group(1))

        m_itm = re_prop_iditem.search(line)
        if m_itm: analysis["items"].add(m_itm.group(1))

        m_inc = re_prop_idinclude.search(line)
        if m_inc: analysis["includes"].add(m_inc.group(1))

        # Tokens inside values
        for token in re_token_nd.findall(line): analysis["nodes"].add(token)
        for token in re_token_chnnl.findall(line): analysis["channels"].add(token)
        for token in re_token_tm.findall(line): analysis["items"].add(token)

    # Convert sets to sorted lists for JSON
    analysis["nodes"] = sorted(list(analysis["nodes"]))
    analysis["items"] = sorted(list(analysis["items"]))
    analysis["channels"] = sorted(list(analysis["channels"]))
    analysis["includes"] = sorted(list(analysis["includes"]))

    return analysis

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analiza archivos OBL.")
    parser.add_argument("file_path", help="Ruta al archivo .obl")
    args = parser.parse_args()

    result = analyze_obl(args.file_path)
    print(json.dumps(result, indent=2))
