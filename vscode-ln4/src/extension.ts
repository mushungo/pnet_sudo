// =============================================================================
// src/extension.ts — LN4 Language Client for VS Code
// =============================================================================
// Spawns the LN4 LSP server (python -m ln4_lsp) via STDIO and connects
// the VS Code language client to it.
// =============================================================================

import * as path from "path";
import { workspace, ExtensionContext, window } from "vscode";
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

export function activate(context: ExtensionContext): void {
    const config = workspace.getConfiguration("ln4");
    const pythonPath: string = config.get<string>("pythonPath", "python");
    const serverArgs: string[] = config.get<string[]>("serverArgs", ["-m", "ln4_lsp"]);

    // The server is a Python process: python -m ln4_lsp (STDIO mode)
    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: serverArgs,
        options: {
            // Use the workspace folder as cwd so imports resolve correctly
            cwd: workspace.workspaceFolders?.[0]?.uri.fsPath,
        },
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: "file", language: "ln4" }],
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher("**/*.ln4"),
        },
        outputChannelName: "LN4 Language Server",
    };

    client = new LanguageClient(
        "ln4LanguageServer",
        "LN4 Language Server",
        serverOptions,
        clientOptions
    );

    // Start the client (which also starts the server process)
    client.start().catch((err) => {
        window.showErrorMessage(
            `Failed to start LN4 Language Server: ${err.message}. ` +
            `Ensure Python is installed and ln4_lsp is available.`
        );
    });

    context.subscriptions.push({
        dispose: () => {
            if (client) {
                client.stop();
            }
        },
    });
}

export function deactivate(): Thenable<void> | undefined {
    if (client) {
        return client.stop();
    }
    return undefined;
}
