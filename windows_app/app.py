import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import sys
import os
import fitz
import pytesseract
from PIL import Image

TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LANGUAGES = ["spa", "eng", "por", "fra", "deu"]
MAX_PATH = 200
FORMATS = ["PDF buscable", "Texto para IA (.txt)"]


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


def safe_output_path(input_path: str, ext: str) -> str:
    directory = os.path.dirname(input_path)
    base = os.path.splitext(os.path.basename(input_path))[0]
    suffix = "_OCR"
    candidate = os.path.join(directory, base + suffix + ext)
    if len(candidate) <= MAX_PATH:
        return candidate
    max_base = MAX_PATH - len(directory) - len(os.sep) - len(suffix) - len(ext)
    return os.path.join(directory, base[:max(max_base, 8)] + suffix + ext)


def classify_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "tesseract" in msg and ("not found" in msg or "not installed" in msg):
        return "Tesseract no encontrado. Verifica que la carpeta 'tesseract' este junto al .exe."
    if "permission" in msg or "access is denied" in msg:
        return "Permiso denegado. Cierra el PDF en otros programas e intenta de nuevo."
    if "no such file" in msg or "cannot open" in msg:
        return "No se encontro el archivo. Verifica que el PDF de entrada existe."
    if "memory" in msg or "memorydeplete" in msg:
        return "Sin memoria suficiente. El PDF puede ser demasiado grande."
    if "failed to initialize" in msg or "error opening" in msg:
        return "El archivo PDF parece estar dañado o no es un PDF valido."
    return "Error inesperado. Ver detalles abajo."


def _setup_tesseract(lang: str):
    tess_path = find_tesseract()
    if not tess_path:
        raise FileNotFoundError("Tesseract no encontrado.")
    pytesseract.pytesseract.tesseract_cmd = tess_path

    tessdata_dir = os.path.join(os.path.dirname(tess_path), "tessdata")
    if os.path.isdir(tessdata_dir):
        os.environ["TESSDATA_PREFIX"] = tessdata_dir
        if not os.path.exists(os.path.join(tessdata_dir, f"{lang}.traineddata")):
            lang = "eng"
        if not os.path.exists(os.path.join(tessdata_dir, "eng.traineddata")):
            raise FileNotFoundError(f"No se encontraron datos de idioma en:\n{tessdata_dir}")
    return lang


def _page_to_img(page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def run_ocr_pdf(input_path: str, output_path: str, lang: str, on_progress):
    if len(output_path) > 255:
        raise ValueError(f"Ruta de salida demasiado larga ({len(output_path)} chars). Usa un nombre mas corto.")

    lang = _setup_tesseract(lang)
    doc = fitz.open(input_path)
    total = doc.page_count
    DPI = 300
    SCALE = 72.0 / DPI  # pixeles → puntos PDF

    for i in range(total):
        on_progress(f"Página {i + 1} de {total}...", i / total * 95)
        page = doc[i]
        img = _page_to_img(page, dpi=DPI)

        try:
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        except (pytesseract.pytesseract.TesseractError, FileNotFoundError):
            data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)

        for j in range(len(data["text"])):
            word = data["text"][j]
            try:
                conf = int(data["conf"][j])
            except (ValueError, TypeError):
                conf = -1
            if not word.strip() or conf < 30:
                continue

            x0 = data["left"][j] * SCALE
            y0 = data["top"][j] * SCALE
            h = data["height"][j] * SCALE

            page.insert_text(
                fitz.Point(x0, y0 + h),
                word,
                fontsize=max(4, h),
                render_mode=3,  # texto invisible (solo buscable)
            )

    on_progress("Guardando y comprimiendo...", 95)
    doc.save(
        output_path,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        garbage=4,
        clean=True,
    )
    doc.close()


def run_ocr_txt(input_path: str, output_path: str, lang: str, on_progress):
    lang = _setup_tesseract(lang)
    doc = fitz.open(input_path)
    total = doc.page_count
    pages_text = []

    for i in range(total):
        on_progress(f"Página {i + 1} de {total}...", i / total * 95)
        img = _page_to_img(doc[i], dpi=300)
        try:
            text = pytesseract.image_to_string(img, lang=lang)
        except (pytesseract.pytesseract.TesseractError, FileNotFoundError):
            text = pytesseract.image_to_string(img, lang="eng")
        pages_text.append(text.strip())

    on_progress("Guardando...", 95)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(pages_text))
    doc.close()


class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, summary: str, detail: str):
        super().__init__(parent)
        self.title("Error Detallado")
        self.resizable(True, True)
        self.geometry("600x380")
        self.grab_set()

        ttk.Label(self, text=summary, font=("Segoe UI", 10, "bold"),
                  foreground="#c0392b", wraplength=560).pack(padx=16, pady=(14, 6), anchor="w")

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        text = tk.Text(frame, font=("Consolas", 9), wrap=tk.WORD, bg="#f8f8f8", relief=tk.FLAT)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.insert("1.0", detail)
        text.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 12))
        ttk.Button(btn_frame, text="Copiar error", command=lambda: self._copy(detail)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR - PDF Buscable")
        self.root.geometry("540x420")
        self.root.resizable(False, False)
        self.input_pdf = tk.StringVar()
        self.output_path = tk.StringVar()
        self.lang_var = tk.StringVar(value="spa")
        self.format_var = tk.StringVar(value=FORMATS[0])
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        self._click_count = 0
        title_lbl = ttk.Label(frame, text="Convertidor OCR", font=("Segoe UI", 15, "bold"), cursor="arrow")
        title_lbl.pack(pady=(0, 16))
        title_lbl.bind("<Button-1>", self._on_title_click)

        self._file_row(frame, "Archivo PDF original:", self.input_pdf, self._browse_input)
        self._file_row(frame, "Guardar resultado como:", self.output_path, self._browse_output,
                       save=True, editable=True)

        opts = ttk.Frame(frame)
        opts.pack(fill=tk.X, pady=6)

        ttk.Label(opts, text="Idioma:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Combobox(opts, textvariable=self.lang_var, values=LANGUAGES,
                     width=7, state="readonly").pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(opts, text="Formato:").pack(side=tk.LEFT, padx=(0, 6))
        fmt_cb = ttk.Combobox(opts, textvariable=self.format_var, values=FORMATS,
                               width=22, state="readonly")
        fmt_cb.pack(side=tk.LEFT)
        fmt_cb.bind("<<ComboboxSelected>>", self._on_format_change)

        self.status_lbl = ttk.Label(frame, text="Esperando...", foreground="gray")
        self.status_lbl.pack(pady=(16, 4))
        self.progress = ttk.Progressbar(frame, length=440, mode="determinate")
        self.progress.pack(pady=4)

        self.btn_run = ttk.Button(frame, text="▶  Iniciar OCR", command=self._start)
        self.btn_run.pack(pady=14)

    def _file_row(self, parent, label, var, cmd, save=False, editable=False):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text=label).pack(anchor=tk.W)
        ttk.Entry(row, textvariable=var, state=tk.NORMAL if editable else "readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(row, text="Guardar en..." if save else "Buscar...", command=cmd).pack(side=tk.RIGHT)

    def _is_txt_mode(self) -> bool:
        return self.format_var.get() == FORMATS[1]

    def _on_format_change(self, _=None):
        current = self.output_path.get()
        if not current:
            return
        base = os.path.splitext(current)[0]
        # Quitar sufijo _OCR si ya existe para recalcular
        if base.endswith("_OCR"):
            base = base[:-4]
        ext = ".txt" if self._is_txt_mode() else ".pdf"
        self.output_path.set(safe_output_path(base + ".pdf", ext))

    def _on_title_click(self, _=None):
        self._click_count += 1
        if self._click_count >= 5:
            self._click_count = 0
            self._show_easter_egg()

    def _show_easter_egg(self):
        w = tk.Toplevel(self.root)
        w.title("Hecho con amor")
        w.resizable(False, False)
        w.grab_set()
        w.geometry("320x200")

        tk.Label(w, text="♥", font=("Segoe UI", 48), fg="#e74c3c").pack(pady=(20, 4))
        tk.Label(w, text="Hecho con amor por tu hermanito,\npara ti, Evelin.",
                 font=("Segoe UI", 11), justify="center").pack()
        tk.Label(w, text="Espero que te sirva mucho  :)",
                 font=("Segoe UI", 9), fg="gray").pack(pady=(6, 16))
        ttk.Button(w, text="Cerrar", command=w.destroy).pack()

    def _browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        if path:
            self.input_pdf.set(path)
            ext = ".txt" if self._is_txt_mode() else ".pdf"
            self.output_path.set(safe_output_path(path, ext))

    def _browse_output(self):
        if self._is_txt_mode():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Texto", "*.txt")])
        else:
            path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                filetypes=[("PDF", "*.pdf")])
        if path:
            self.output_path.set(path)

    def _start(self):
        if not self.input_pdf.get() or not self.output_path.get():
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
            inp = self.input_pdf.get()
            out = self.output_path.get()
            lang = self.lang_var.get()
            if self._is_txt_mode():
                run_ocr_txt(inp, out, lang, self._update)
            else:
                run_ocr_pdf(inp, out, lang, self._update)
            self._update("¡Listo!", 100)
            self.root.after(0, lambda: messagebox.showinfo("Exito", f"Guardado en:\n{out}"))
        except Exception as exc:
            tb = traceback.format_exc()
            summary = classify_error(exc)
            self._update(f"Error: {summary}", 0)
            self.root.after(0, lambda: ErrorDialog(self.root, summary, tb))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    OCRApp(root)
    root.mainloop()
