import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import sys
import os
import fitz
import pytesseract
from PIL import Image

TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LANGUAGES = ["spa", "eng", "por", "fra", "deu"]


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_tesseract():
    bundled = os.path.join(_app_dir(), "tesseract", "tesseract.exe")
    if os.path.exists(bundled):
        return bundled
    if os.path.exists(TESSERACT_DEFAULT):
        return TESSERACT_DEFAULT
    return None


def run_ocr(input_path: str, output_path: str, lang: str, on_progress):
    tess_path = find_tesseract()
    if not tess_path:
        raise FileNotFoundError(
            "Tesseract no encontrado.\n"
            "Instálalo desde: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    pytesseract.pytesseract.tesseract_cmd = tess_path
    tessdata_dir = os.path.join(os.path.dirname(tess_path), "tessdata")
    if os.path.isdir(tessdata_dir):
        os.environ["TESSDATA_PREFIX"] = tessdata_dir

    doc = fitz.open(input_path)
    out_doc = fitz.open()
    total = doc.page_count

    for i in range(total):
        on_progress(f"Página {i + 1} de {total}...", i / total * 95)
        page = doc[i]
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
        except pytesseract.pytesseract.TesseractError:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang="eng")
        tmp = fitz.open("pdf", pdf_bytes)
        out_doc.insert_pdf(tmp)
        tmp.close()

    on_progress("Guardando...", 95)
    out_doc.save(output_path)
    out_doc.close()
    doc.close()


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR - PDF Buscable")
        self.root.geometry("520x370")
        self.root.resizable(False, False)
        self.input_pdf = tk.StringVar()
        self.output_pdf = tk.StringVar()
        self.lang_var = tk.StringVar(value="spa")
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Convertidor OCR a PDF Buscable", font=("Segoe UI", 15, "bold")).pack(pady=(0, 18))

        self._file_row(frame, "Archivo PDF original:", self.input_pdf, self._browse_input)
        self._file_row(frame, "Guardar resultado como:", self.output_pdf, self._browse_output, save=True)

        lang_frame = ttk.Frame(frame)
        lang_frame.pack(fill=tk.X, pady=4)
        ttk.Label(lang_frame, text="Idioma:").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Combobox(lang_frame, textvariable=self.lang_var, values=LANGUAGES, width=8, state="readonly").pack(side=tk.LEFT)

        self.status_lbl = ttk.Label(frame, text="Esperando...", foreground="gray")
        self.status_lbl.pack(pady=(14, 4))
        self.progress = ttk.Progressbar(frame, length=420, mode="determinate")
        self.progress.pack(pady=4)

        self.btn_run = ttk.Button(frame, text="▶  Iniciar OCR", command=self._start)
        self.btn_run.pack(pady=16)

    def _file_row(self, parent, label, var, cmd, save=False):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text=label).pack(anchor=tk.W)
        ttk.Entry(row, textvariable=var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(row, text="Guardar en..." if save else "Buscar...", command=cmd).pack(side=tk.RIGHT)

    def _browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        if path:
            self.input_pdf.set(path)
            base, ext = os.path.splitext(path)
            self.output_pdf.set(f"{base}_OCR{ext}")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path:
            self.output_pdf.set(path)

    def _start(self):
        if not self.input_pdf.get() or not self.output_pdf.get():
            messagebox.showwarning("Atención", "Selecciona un archivo de entrada y uno de salida.")
            return
        self.btn_run.config(state=tk.DISABLED)
        self.progress.config(value=0)
        threading.Thread(target=self._process, daemon=True).start()

    def _update(self, msg, val=None):
        self.status_lbl.config(text=msg)
        if val is not None:
            self.progress.config(value=val)
        self.root.update_idletasks()

    def _process(self):
        try:
            run_ocr(self.input_pdf.get(), self.output_pdf.get(), self.lang_var.get(), self._update)
            self._update("¡Listo!", 100)
            self.root.after(0, lambda: messagebox.showinfo("Exito", f"Guardado en:\n{self.output_pdf.get()}"))
        except Exception as exc:
            self._update("Error", 0)
            self.root.after(0, lambda: messagebox.showerror("Error", str(exc)))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    OCRApp(root)
    root.mainloop()
