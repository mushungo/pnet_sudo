# =============================================================================
# ln4_lsp/__main__.py — Punto de entrada para el servidor LSP de LN4
# =============================================================================
# Permite ejecutar el servidor con:
#   python -m ln4_lsp             # STDIO (modo normal para editores)
#   python -m ln4_lsp --tcp       # TCP (para desarrollo/debug)
#   python -m ln4_lsp --tcp --port 9999
# =============================================================================

import logging
import sys

from pygls.cli import start_server
from ln4_lsp.server import server


def main():
    """Punto de entrada principal del servidor LSP de LN4."""

    # Configurar logging — stderr para no interferir con STDIO del LSP
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    start_server(server)


if __name__ == "__main__":
    main()
