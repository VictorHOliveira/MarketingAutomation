@echo off
REM ============================================================
REM MARKETING AUTOMATION - Launcher
REM ============================================================
REM Uso: run.bat [comando]
REM Comandos: run, run-single, start, status, topics, seo
REM ============================================================

setlocal enabledelayedexpansion

set BASE_DIR=%~dp0
set PYTHON=python

if "%1"=="" goto :help

if "%1"=="run" (
    echo Executando pipeline completo...
    %PYTHON% "%BASE_DIR%social_scheduler.py" run
    goto :end
)

if "%1"=="run-single" (
    if "%2"=="" (
        echo Erro: Especifique o projeto (qa_overflow, scandoc, supertarefas, qa_picker)
        exit /b 1
    )
    echo Executando pipeline para %2...
    %PYTHON% "%BASE_DIR%social_scheduler.py" run-single %2
    goto :end
)

if "%1"=="start" (
    echo Iniciando scheduler...
    echo Pressione Ctrl+C para parar.
    %PYTHON% "%BASE_DIR%social_scheduler.py" start
    goto :end
)

if "%1"=="status" (
    %PYTHON% "%BASE_DIR%social_scheduler.py" status
    goto :end
)

if "%1"=="topics" (
    echo Buscando trending topics...
    %PYTHON% "%BASE_DIR%topic_generator.py"
    goto :end
)

if "%1"=="seo" (
    echo Gerando relatorio SEO...
    %PYTHON% "%BASE_DIR%seo_monitor.py"
    goto :end
)

if "%1"=="help" goto :help
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

echo Comando desconhecido: %1
goto :help

:help
echo.
echo MARKETING AUTOMATION
echo ====================
echo.
echo Uso: run.bat [comando]
echo.
echo Comandos:
echo   run              Executa pipeline para todos os projetos
echo   run-single PROJ  Executa para um projeto especifico
echo                    Projetos: qa_overflow, scandoc, supertarefas, qa_picker
echo   start            Inicia scheduler automatico
echo   status           Mostra status do sistema
echo   topics           Busca trending topics
echo   seo              Gera relatorio SEO
echo   help             Mostra esta ajuda
echo.
echo Exemplos:
echo   run.bat run
echo   run.bat run-single qa_overflow
echo   run.bat start
echo   run.bat status
echo.

:end
endlocal
