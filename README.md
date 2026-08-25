# 📄 OCR Mágico - Convertidor a PDF Buscable y Texto

> *Dedicado con todo cariño a mi hermanita Evelin ❤️*

[![GitHub Release](https://img.shields.io/github/v/release/Peter24a/miocr?color=brightgreen&label=Versi%C3%B3n)](https://github.com/Peter24a/miocr/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://github.com/Peter24a/miocr)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**OCR Mágico** es una herramienta de escritorio ligera, rápida y fácil de usar para transformar cualquier documento o libro PDF escaneado en un **PDF completamente interactivo (buscable, seleccionable y copiable)** o extraer todo su contenido en texto limpio (`.txt`) listo para usar con IA o editores de texto.

---

## 📥 Descarga para Windows (Listo para Usar)

No necesitas saber programar ni tener instalado Python en tu computadora:

1. Ve a la sección de **[Últimos Lanzamientos (Releases)](https://github.com/Peter24a/miocr/releases/latest)**.
2. Descarga el archivo comprimido **`OCR_App_Windows_x64.zip`**.
3. Haz clic derecho y selecciona **"Extraer todo..."** en tu computadora (por ejemplo, en el Escritorio).
4. Abre la carpeta y haz doble clic en **`OCR_App.exe`**.

> 💡 **Nota:** La versión portable incluye el motor Tesseract OCR y los modelos de idioma en Español e Inglés integrados. Funciona completamente **offline** (sin internet) y no requiere instalaciones adicionales.

---

## ✨ Características Principales

* 🔍 **PDFs Idénticos y Buscables:** Mantiene exactamente el diseño visual, tipografía y formato visual original del PDF, añadiendo una capa invisible de texto que te permite buscar con `Ctrl + F`, resaltar, copiar y pegar.
* 🤖 **Modo Texto para IA (.txt):** Extrae todo el contenido página por página delimitado, ideal para alimentar modelos de IA (ChatGPT, Claude, Gemini, DeepSeek) o procesar información.
* 🇪🇸 **Soporte Multilingüe:** Optimizado para textos en Español e Inglés (y ampliable a Portugués, Francés, Alemán, etc.).
* ⏹️ **Control de Procesamiento y Memoria:** Incluye botón para cancelar en cualquier momento y liberación continua de memoria RAM, ideal para libros y documentos extensos.
* 🚀 **Doble Modo de Detección:** Funciona con el motor portable incluido o se conecta automáticamente con instalaciones existentes de Tesseract en el sistema.

---

## 🖥️ Cómo Usar la Aplicación

1. **Seleccionar PDF:** Haz clic en **"Examinar..."** y elige el archivo PDF que deseas procesar.
2. **Elegir Formato:**
   - `PDF Buscable`: Genera un nuevo archivo con el sufijo `_OCR.pdf`.
   - `Texto para IA (.txt)`: Genera un archivo `.txt` con todo el texto extraído.
3. **Seleccionar Idioma:** Por defecto en `Español (spa)`.
4. **Iniciar:** Presiona **▶ Iniciar OCR** y sigue el avance en la barra de progreso.
5. **Listo:** Al finalizar, usa los botones directos para **"Abrir archivo"** o **"Abrir carpeta"**.

---

## 🛠️ Para Desarrolladores: Compilación y Ejecución

Si deseas contribuir, modificar la interfaz o compilar tu propio ejecutable:

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Peter24a/miocr.git
cd miocr
```

### 2. Crear Entorno Virtual e Instalar Dependencias
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r windows_app/requirements.txt
```

### 3. Ejecutar en Modo Desarrollo
```powershell
python windows_app/app.py
```

### 4. Compilar el Ejecutable Portable (.exe + .zip)
Simplemente haz doble clic en **`windows_app/build.bat`** o ejecuta:
```powershell
python windows_app/package.py
```
El archivo distribuible `OCR_App_Windows_x64.zip` se generará automáticamente en `windows_app/dist/`.

---

## ⚙️ Integración Continua (CI/CD)

El repositorio cuenta con un pipeline automatizado de **GitHub Actions** (`.github/workflows/release.yml`) que compila la aplicación en un entorno limpio de Windows y publica las nuevas versiones automáticamente cada vez que se crea una etiqueta (tag) de versión (por ejemplo `v1.0.0`).

---

## 📜 Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE). Puedes usarlo, modificarlo y compartirlo libremente.
