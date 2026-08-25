# 📄 Herramienta de OCR para Windows

Esta versión para Windows utiliza **Tesseract OCR** optimizado y una interfaz gráfica en Python (`tkinter` / `ttk`) para procesar documentos PDF y convertirlos en archivos PDF con texto seleccionable/buscable o en archivos de texto plano (`.txt`).

---

## Opción 1: Descargar el Ejecutable Listo para Usar (Recomendado)

Si solo quieres usar la aplicación sin instalar Python ni compilar nada:

1. Ve a la sección de **[Releases / Lanzamientos](https://github.com/Peter24a/miocr/releases)** del repositorio.
2. Descarga el archivo **`OCR_App_Windows_x64.zip`**.
3. Descomprime la carpeta en tu computadora (por ejemplo, en el Escritorio).
4. Haz doble clic en **`OCR_App.exe`** y ¡listo! Ya incluye el motor OCR en español e inglés sin requerir configuración adicional.

---

## Opción 2: Compilar desde el Código Fuente

Si eres desarrollador y deseas modificar el código o generar tu propio ejecutable:

### Requisitos Previos
1. **Python 3.10 o superior** instalado con la opción "Add Python to PATH" marcada.
2. *(Opcional)* **Tesseract OCR**: Puedes instalarlo en el sistema desde el [instalador oficial de UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) marcando el idioma Español, o colocar los binarios en `windows_app/tesseract`.

### Pasos para Compilar

1. Clona o descarga este repositorio:
   ```bash
   git clone https://github.com/Peter24a/miocr.git
   cd miocr
   ```

2. Ejecuta el compilador automático:
   - Haz doble clic en **`windows_app/build.bat`** o ejecuta en PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install -r windows_app/requirements.txt
   python windows_app/package.py
   ```

3. El resultado compilado y el archivo portable comprimido se generarán en la carpeta:
   - `windows_app/dist/OCR_App/` (Carpeta con el `.exe` y dependencias)
   - `windows_app/dist/OCR_App_Windows_x64.zip` (Paquete portable listo para distribuir)

