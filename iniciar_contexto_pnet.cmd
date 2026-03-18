@echo off
title Opencode - Contexto PeopleNet
REM Cambia el directorio a la carpeta raíz del proyecto (donde está este script).
cd /d "%~dp0"

echo Directorio cambiado a:
cd
echo --------------------------------------------------
echo.

REM Inicia el servidor HTTP de Engram (memoria persistente) en segundo plano.
REM Requiere que engram.exe esté en el PATH del sistema.
echo Iniciando servidor Engram (memoria persistente)...
where engram >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start /B "" engram serve >nul 2>&1
    echo Engram iniciado en segundo plano.
) else (
    echo [AVISO] engram.exe no encontrado en PATH. La memoria persistente no estará disponible.
    echo         Descarga Engram desde: https://github.com/Gentleman-Programming/engram
)
echo.

echo Ejecutando 'opencode' con los parametros proporcionados...
echo.

REM Ejecuta opencode y le pasa todos los argumentos que se pasaron a este script (%*).
opencode %*
