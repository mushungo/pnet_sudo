@echo off
cd /d "%~dp0"

echo Directorio cambiado a:
cd
echo --------------------------------------------------
echo.

Path=%~dp0.engram;%PATH%

REM Inicia el servidor HTTP de Engram (memoria persistente) en segundo plano.
REM Requiere que engram.exe esté en el PATH del sistema.
echo Iniciando servidor Engram (memoria persistente)...
where engram >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start /B "" engram serve >nul 2>&1
    echo Engram iniciado en segundo plano.
) else (
    echo [AVISO] engram.exe no encontrado en PATH. La memoria persistente no estara disponible.
    echo         Descarga Engram desde: https://github.com/Gentleman-Programming/engram
)
echo.

REM ── Selector de proyecto ────────────────────────────────────────────────────
echo Selecciona el proyecto a investigar:
echo   [1] CAF    ^(SQL Server^)
echo   [2] AAPP   ^(Oracle - GOTHAM:1944/ORA6^)
echo   [intro] sin proyecto ^(usa .env raiz^)
echo.
set /p PROYECTO_OPCION="Opcion: "

if "%PROYECTO_OPCION%"=="1" (
    set PNET_PROJECT=caf
    echo Proyecto: CAF ^(SQL Server^)
) else if "%PROYECTO_OPCION%"=="2" (
    set PNET_PROJECT=aapp
    echo Proyecto: AAPP ^(Oracle - GOTHAM^)
) else (
    set PNET_PROJECT=
    echo Sin proyecto seleccionado, usando .env raiz.
)
echo --------------------------------------------------
echo.

title Opencode - PeopleNet [%PNET_PROJECT%]

echo Ejecutando 'opencode' con los parametros proporcionados...
echo recuerda. Comando para la carga del contexto:
echo    engram_mem_context [project=pnet_sudo]
echo.
echo pulsa intro para entrar en opencode
pause >nul
echo accediendo.....

call code .
REM Ejecuta opencode y le pasa todos los argumentos que se pasaron a este script (%*).
opencode %*

echo hemos salido de opencode
