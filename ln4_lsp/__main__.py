# =============================================================================
# ln4_lsp/__main__.py — Punto de entrada para el servidor LSP de LN4
# =============================================================================
# Permite ejecutar el servidor con:
#   python -m ln4_lsp             # STDIO (modo normal para editores)
#   python -m ln4_lsp --tcp       # TCP (para desarrollo/debug)
#   python -m ln4_lsp --tcp --port 9999
# =============================================================================

import argparse
import logging
import sys

from ln4_lsp.server import server


def main():
    """Punto de entrada principal del servidor LSP de LN4."""

    parser = argparse.ArgumentParser(description="LN4 Language Server")
    parser.add_argument("--tcp", action="store_true", help="Usar transporte TCP en lugar de STDIO")
    parser.add_argument("--host", default="127.0.0.1", help="Host para TCP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2087, help="Puerto para TCP (default: 2087)")
    args = parser.parse_args()

    # Configurar logging — stderr para no interferir con STDIO del LSP
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.tcp:
        server.start_tcp(args.host, args.port)
    else:
        server.start_io()


if __name__ == "__main__":
    main()
