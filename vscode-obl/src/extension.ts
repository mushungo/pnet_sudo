import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
    const pythonPath = workspace.getConfiguration('obl').get<string>('pythonPath') || 'python';
    const serverArgs = workspace.getConfiguration('obl').get<string[]>('serverArgs') || ['-m', 'obl_lsp'];

    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: serverArgs,
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'obl' }],
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher('**/*.obl')
        }
    };

    client = new LanguageClient(
        'oblLsp',
        'OBL Language Server',
        serverOptions,
        clientOptions
    );

    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
