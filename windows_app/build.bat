@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Compilador y Empaquetador - OCR Magico
echo ===================================================
echo.

:: Detectar ejecutable de Python
set "PYTHON_EXE="

if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\.venv\Scripts\python.exe"
) else if exist "..\venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\venv\Scripts\python.exe"
) else if exist "..\env\Scripts\python.exe" (
    set "PYTHON_EXE=..\env\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] No se encontro Python ni un entorno virtual (.venv/venv).
    echo Por favor instala Python 3.10+ o crea un entorno virtual.
    pause
    exit /b 1
)

echo Usando Python: %PYTHON_EXE%
echo.
echo [1/2] Verificando dependencias...
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet

echo.
echo [2/2] Ejecutando empaquetador...
"%PYTHON_EXE%" package.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un error durante la compilacion.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo Proceso finalizado.
echo El ZIP listo para compartir esta en: dist\OCR_App_Windows_x64.zip
echo ===================================================
echo.
pause
