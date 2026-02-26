# OCR Mágico - Herramienta de Reconocimiento de Texto
> *Dedicado con todo cariño a mi hermanita Evelin ❤️*

Este es un pequeño proyecto para crear documentos PDF idénticos al original pero con texto completamente buscable, seleccionable y copiable.

## Características

1. **OCR Nativo en Mac:** Utiliza todo el poder de `Apple Vision Framework` a través de Python para extraer e incrustar texto invisible de manera veloz con los procesadores del Mac.
2. **Exportación de Word:** Exporta cualquier PDF a documento de texto de Word si se requiere reescribir contenido.
3. **App Windows Autónoma:** Una versión sencilla en interfaz gráfica con `tkinter` y `Tesseract` para usar en cualquier PC con Windows (compilada en `.exe`).

## Estructura del Proyecto

* `mac_ocr.py`: Script de ejecución principal en macOS.
* `export_to_word.py`: Herramienta para extraer texto de PDFs OCR a documentos `.docx`.
* `windows_app/`: Código y scripts para generar el ejecutable de Windows con interfaz gráfica.
* `requirements.txt`: Dependencias en Python para correrlo en Mac.
