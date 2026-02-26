import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import sys

# Configurar ruta de Tesseract por defecto en Windows
# (El usuario debió instalarlo según las INSTRUCCIONES)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Herramienta OCR (Generador de PDF Buscable)")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Variables
        self.input_pdf = tk.StringVar()
        self.output_pdf = tk.StringVar()

        # Configurar Estilos
        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TLabel', font=('Segoe UI', 10))

        # Interfaz Gráfica (Widgets)
        self.create_widgets()

    def create_widgets(self):
        # Marco principal
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Título
        lbl_title = ttk.Label(frame, text="Convertidor OCR a PDF Identico", font=("Segoe UI", 16, "bold"))
        lbl_title.pack(pady=(0, 20))

        # Selección de entrada
        frame_input = ttk.Frame(frame)
        frame_input.pack(fill=tk.X, pady=5)
        ttk.Label(frame_input, text="Archivo Original (PDF):").pack(anchor=tk.W)
        self.entry_input = ttk.Entry(frame_input, textvariable=self.input_pdf, state='readonly')
        self.entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(frame_input, text="Buscar...", command=self.browse_input).pack(side=tk.RIGHT)

        # Selección de salida
        frame_output = ttk.Frame(frame)
        frame_output.pack(fill=tk.X, pady=15)
        ttk.Label(frame_output, text="Guardar Resultado como (PDF):").pack(anchor=tk.W)
        self.entry_output = ttk.Entry(frame_output, textvariable=self.output_pdf, state='readonly')
        self.entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(frame_output, text="Guardar en...", command=self.browse_output).pack(side=tk.RIGHT)

        # Barra de progreso
        self.progress_lbl = ttk.Label(frame, text="Esperando instrucciones...", foreground="gray")
        self.progress_lbl.pack(pady=(10, 5))
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=5)

        # Botón de Procesar
        self.btn_process = ttk.Button(frame, text="▶ Iniciar OCR", command=self.start_ocr_thread)
        self.btn_process.pack(pady=20)

    def browse_input(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            self.input_pdf.set(filepath)
            # Autocompletar la salida
            base, ext = os.path.splitext(filepath)
            self.output_pdf.set(f"{base}_OCR{ext}")

    def browse_output(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if filepath:
            self.output_pdf.set(filepath)

    def start_ocr_thread(self):
        if not self.input_pdf.get() or not self.output_pdf.get():
            messagebox.showwarning("Atención", "Por favor selecciona un archivo de entrada y uno de salida.")
            return
            
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            messagebox.showerror("Error Crítico", "Tesseract OCR no fue encontrado.\nDebes instalarlo primero en 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' según las instrucciones.")
            return

        # Bloquear botón y UI
        self.btn_process.config(state=tk.DISABLED)
        self.progress.config(value=0)
        
        # Ejecutar en un hilo separado para no congelar la GUI
        thread = threading.Thread(target=self.run_ocr_process)
        thread.daemon = True
        thread.start()

    def update_ui(self, message, progress_value=None):
        self.progress_lbl.config(text=message)
        if progress_value is not None:
            self.progress.config(value=progress_value)
        self.root.update_idletasks()

    def run_ocr_process(self):
        input_path = self.input_pdf.get()
        output_path = self.output_pdf.get()

        try:
            self.update_ui("Abriendo PDF original...")
            doc = fitz.open(input_path)
            out_doc = fitz.open()

            total_pages = doc.page_count
            
            for page_num in range(total_pages):
                self.update_ui(f"Procesando página {page_num + 1} de {total_pages}...", (page_num / total_pages) * 100)
                
                page = doc[page_num]
                
                # Renderizar página a imagen de alta resolución
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Usar Tesseract para generar un PDF directamente (Searchable PDF bypass)
                # lang='spa' es para español (debe estar instalado)
                try:
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='spa')
                except pytesseract.pytesseract.TesseractError:
                    # Intento de fallback a inglés si no se instaló español
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='eng')

                # Abrir los bytes generados por tesseract como una página de PyMuPDF e insertarlo
                temp_doc = fitz.open("pdf", pdf_bytes)
                out_doc.insert_pdf(temp_doc)
                temp_doc.close()

            self.update_ui("Guardando archivo PDF final (Esto puede tardar)...", 95)
            out_doc.save(output_path)
            out_doc.close()
            doc.close()

            self.update_ui("¡Proceso Finalizado!", 100)
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"El archivo fue procesado correctamente.\nSe guardó en:\n{output_path}"))

        except Exception as e:
            self.update_ui("Ocurrió un error", 0)
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ha ocurrido un problema:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.btn_process.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
