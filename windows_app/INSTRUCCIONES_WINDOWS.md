# Herramienta de OCR para Windows

Dado que el motor "Apple Vision" es exclusivo de Mac, este programa utiliza **Tesseract OCR**, que es el motor de reconocimiento óptico de código abierto más utilizado y estable disponible para Windows.

## Instrucciones de Instalación y Compilación para Windows

Sigue estos pasos **desde tu computadora con Windows** para generar tu archivo `.exe`:

### Paso 1: Instalar Python y Tesseract
1. Instala **Python** (versión 3.10 o superior) desde python.org (Asegúrate de marcar "Add Python to PATH" durante la instalación).
2. Descarga e instala **Tesseract OCR para Windows**:
   - Enlace oficial de descarga: [Tesseract OCR Installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Descarga la versión de 64 bits (`tesseract-ocr-w64-setup-5.3.3.exe`).
   - Durante la instalación, expande "Additional language data (download)" y asegúrate de seleccionar **Spanish** (Español).
   - Instálalo en la ruta por defecto (`C:\Program Files\Tesseract-OCR\`).

### Paso 2: Generar el archivo .exe
1. Copia toda la carpeta `windows_app` a tu computadora Windows.
2. Abre la carpeta `windows_app` y haz doble clic en el archivo **`build.bat`**.
3. Verás que se abre una terminal instalando cosas. Al terminar, aparecerá una nueva carpeta llamada `dist`.
4. ¡Listo! Dentro de la carpeta `dist` encontrarás tu archivo **`OCR_App.exe`**.

> **Nota**: Puedes arrastrar tu `.exe` al Escritorio y ya no necesitarás Python ni la carpeta original (el ejecutable es independiente, aunque siempre requerirá que Tesseract siga instalado en `C:\Program Files\Tesseract-OCR\`).
