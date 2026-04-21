# obl_lsp/__main__.py
"""
Punto de entrada para el servidor OBL LSP.
"""
import sys
import argparse
import logging
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from obl_lsp.server import obl_server

def main():
    parser = argparse.ArgumentParser(description="OBL Language Server")
    parser.add_argument("--tcp", action="store_true", help="Usa TCP en lugar de STDIO")
    parser.add_argument("--host", default="127.0.0.1", help="Host para TCP")
    parser.add_argument("--port", type=int, default=2088, help="Puerto para TCP")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    if args.tcp:
        print(f"Iniciando OBL LSP en {args.host}:{args.port}...")
        obl_server.start_tcp(args.host, args.port)
    else:
        obl_server.start_io()

if __name__ == "__main__":
    main()
