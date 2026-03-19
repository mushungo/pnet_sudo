# =============================================================================
# ln4_lsp/tests/test_lsp_integration.py — Test de integración end-to-end
# =============================================================================
# Inicia el servidor LSP real y se comunica con él usando pygls client.
# Verifica:
#   1. Inicialización (initialize / initialized)
#   2. Apertura de documento (textDocument/didOpen)
#   3. Recepción de diagnósticos (textDocument/publishDiagnostics)
#   4. Cambio de documento (textDocument/didChange)
#   5. Limpieza al cerrar (textDocument/didClose)
# =============================================================================

import sys
import os
import asyncio
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lsprotocol import types
from pygls.lsp.client import LanguageClient


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)


async def run_integration_test():
    """Ejecuta un test de integración completo contra el servidor LSP."""

    results = []
    diagnostics_received = {}
    diagnostics_event = asyncio.Event()

    # -- Crear cliente LSP -------------------------------------------------
    client = LanguageClient("ln4-test-client", "v0.1")

    @client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def on_publish_diagnostics(params: types.PublishDiagnosticsParams):
        """Captura diagnósticos publicados por el servidor."""
        diagnostics_received[params.uri] = params.diagnostics
        diagnostics_event.set()

    # -- Iniciar el servidor como subproceso --------------------------------
    python_exe = sys.executable
    await client.start_io(python_exe, "-m", "ln4_lsp")

    try:
        # -- 1. Initialize -------------------------------------------------
        init_result = await client.initialize_async(
            types.InitializeParams(
                capabilities=types.ClientCapabilities(
                    text_document=types.TextDocumentClientCapabilities(
                        synchronization=types.TextDocumentSyncClientCapabilities(
                            did_save=True,
                        ),
                        publish_diagnostics=types.PublishDiagnosticsClientCapabilities(),
                    )
                )
            )
        )
        client.initialized(types.InitializedParams())

        assert init_result is not None, "Initialize returned None"
        server_name = init_result.server_info.name if init_result.server_info else None
        assert server_name == "ln4-language-server", f"Server name: {server_name}"
        results.append(("Initialize", True, "OK"))

        # -- 2. Open document con error de sintaxis -------------------------
        test_uri = "file:///test/example.ln4"
        bad_code = "If Then\n"  # Error de sintaxis: falta expresión
        diagnostics_event.clear()
        diagnostics_received.clear()

        client.text_document_did_open(
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=test_uri,
                    language_id="ln4",
                    version=1,
                    text=bad_code,
                )
            )
        )

        # Esperar diagnósticos (timeout 5s)
        try:
            await asyncio.wait_for(diagnostics_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            results.append(("didOpen + diagnósticos", False, "Timeout esperando diagnósticos"))
        else:
            diags = diagnostics_received.get(test_uri, [])
            if len(diags) >= 1:
                results.append(("didOpen + diagnósticos (error)", True, f"{len(diags)} error(es)"))
            else:
                results.append(("didOpen + diagnósticos (error)", False, "Esperaba >= 1 error"))

        # -- 3. Change document a código válido ----------------------------
        diagnostics_event.clear()
        diagnostics_received.clear()
        good_code = "x = 1\n"

        client.text_document_did_change(
            types.DidChangeTextDocumentParams(
                text_document=types.VersionedTextDocumentIdentifier(
                    uri=test_uri,
                    version=2,
                ),
                content_changes=[
                    types.TextDocumentContentChangeWholeDocument(
                        text=good_code,
                    )
                ],
            )
        )

        try:
            await asyncio.wait_for(diagnostics_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            results.append(("didChange + diagnósticos (limpio)", False, "Timeout"))
        else:
            diags = diagnostics_received.get(test_uri, [])
            if len(diags) == 0:
                results.append(("didChange + diagnósticos (limpio)", True, "0 errores"))
            else:
                msgs = "; ".join(d.message for d in diags)
                results.append(("didChange + diagnósticos (limpio)", False, f"Esperaba 0, obtuvo {len(diags)}: {msgs}"))

        # -- 4. Close document — limpia diagnósticos -----------------------
        diagnostics_event.clear()
        diagnostics_received.clear()

        client.text_document_did_close(
            types.DidCloseTextDocumentParams(
                text_document=types.TextDocumentIdentifier(uri=test_uri)
            )
        )

        try:
            await asyncio.wait_for(diagnostics_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            results.append(("didClose + limpiar diagnósticos", False, "Timeout"))
        else:
            diags = diagnostics_received.get(test_uri, [])
            if len(diags) == 0:
                results.append(("didClose + limpiar diagnósticos", True, "OK"))
            else:
                results.append(("didClose + limpiar diagnósticos", False, f"Debería estar vacío, tiene {len(diags)}"))

    except Exception as e:
        results.append(("ERROR GENERAL", False, str(e)))
    finally:
        # -- Shutdown -------------------------------------------------------
        try:
            await client.shutdown_async(None)
            client.exit(None)
        except Exception:
            pass

        await client.stop()

    return results


def main():
    print("=" * 70)
    print(" LN4 LSP Integration Test (end-to-end)")
    print("=" * 70)

    results = asyncio.run(run_integration_test())

    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    print()
    for name, ok, msg in results:
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")

    print()
    print("=" * 70)
    print(f" Resultado: {passed}/{total} pasaron, {failed}/{total} fallaron")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
