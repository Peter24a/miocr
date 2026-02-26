@echo off
setlocal

set VENV=..\env\Scripts
set APP_NAME=OCR_App
set DIST=dist\%APP_NAME%

echo [1/3] Instalando dependencias...
%VENV%\pip install -r requirements.txt --quiet

echo [2/3] Compilando con PyInstaller...
%VENV%\pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "%APP_NAME%" ^
    app.py

if errorlevel 1 (
    echo ERROR: Fallo la compilacion.
    pause
    exit /b 1
)

echo [3/3] Copiando Tesseract al distribuible...
xcopy /E /I /Q tesseract "%DIST%\tesseract"

echo.
echo Listo. El ejecutable esta en: %DIST%\
echo Comparte toda la carpeta "%APP_NAME%" para que funcione en cualquier PC.
echo.
pause
