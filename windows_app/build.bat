@echo off
echo ==============================================
echo Instalando dependencias de Python...
echo ==============================================
pip install -r requirements.txt

echo.
echo ==============================================
echo Generando el archivo Ejecutable (.exe)...
echo ==============================================
pyinstaller --noconfirm --onedir --windowed --name "OCR_App" "app.py"

echo.
echo ==============================================
echo Compilado completado.
echo Puedes encontrar tu OCR_App.exe dentro de la carpeta "dist\OCR_App"
echo ==============================================
pause
