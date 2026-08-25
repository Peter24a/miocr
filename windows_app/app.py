import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import webbrowser
import shutil
import sys
import os
import gc
import pymupdf as fitz
import pytesseract
from PIL import Image

LANGUAGES = [
    ("spa", "Español (spa)"),
    ("eng", "Inglés (eng)"),
    ("por", "Portugués (por)"),
    ("fra", "Francés (fra)"),
    ("deu", "Alemán (deu)"),
    ("ita", "Italiano (ita)"),
]
MAX_PATH = 240
FORMATS = ["PDF Buscable (Texto invisible)", "Texto para IA / Documento (.txt)"]
TESSERACT_DOWNLOAD_URL = "https://github.com/UB-Mannheim/tesseract/wiki"


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_tesseract():
    """Busca el ejecutable de Tesseract en múltiples ubicaciones estándar y portables."""
    # 1. Carpeta portable incluida junto al ejecutable o script
    bundled = os.path.join(_app_dir(), "tesseract", "tesseract.exe")
    if os.path.isfile(bundled):
        return bundled

    # 2. En el PATH del sistema
    in_path = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if in_path and os.path.isfile(in_path):
        return in_path

    # 3. Rutas habituales de instalación en Windows
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramW6432", ""), "Tesseract-OCR", "tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


def get_tessdata_dir(tess_path: str = None) -> str:
    """Encuentra la carpeta tessdata correspondiente."""
    if not tess_path:
        tess_path = find_tesseract()
    if not tess_path:
        return ""

    possible = [
        os.path.join(os.path.dirname(tess_path), "tessdata"),
        os.path.join(_app_dir(), "tesseract", "tessdata"),
        os.path.join(_app_dir(), "tessdata"),
        os.environ.get("TESSDATA_PREFIX", ""),
    ]
    for p in possible:
        if p and os.path.isdir(p):
            return p
    return ""


def get_available_languages() -> list[tuple[str, str]]:
    """Devuelve la lista de idiomas ordenando los disponibles primero."""
    tess_path = find_tesseract()
    tessdata = get_tessdata_dir(tess_path)
    installed_codes = set()
    if tessdata and os.path.isdir(tessdata):
        for f in os.listdir(tessdata):
            if f.endswith(".traineddata") and not f.startswith("osd"):
                installed_codes.add(f[:-12])

    result = []
    for code, label in LANGUAGES:
        if code in installed_codes:
            result.append((code, f"{label} (disponible)"))
        else:
            result.append((code, label))

    for code in sorted(installed_codes):
        if not any(c == code for c, _ in LANGUAGES):
            result.append((code, f"{code.upper()} (disponible)"))

    return result if result else LANGUAGES


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
    if "tesseract" in msg and ("not found" in msg or "no encontrado" in msg or "not installed" in msg):
        return "Tesseract OCR no está instalado o no se encuentra en el sistema."
    if "permission" in msg or "access is denied" in msg or "permiso denegado" in msg:
        return "Permiso denegado al escribir o leer. Cierra el PDF si está abierto en otra app e intenta de nuevo."
    if "no such file" in msg or "cannot open" in msg:
        return "No se encontró el archivo seleccionado. Verifica que la ruta exista."
    if "memory" in msg or "memorydeplete" in msg:
        return "Memoria insuficiente. El PDF contiene imágenes extremadamente pesadas."
    if "failed to initialize" in msg or "error opening" in msg or "cannot open broken" in msg:
        return "El archivo PDF parece estar dañado o no es un PDF válido."
    if "cancelled" in msg or "cancelado" in msg:
        return "Operación cancelada por el usuario."
    return f"Error: {exc}"


def _setup_tesseract(lang: str):
    tess_path = find_tesseract()
    if not tess_path:
        raise FileNotFoundError(
            "Tesseract no encontrado.\n\n"
            "Descarga e instala Tesseract OCR para Windows desde:\n"
            f"{TESSERACT_DOWNLOAD_URL}"
        )
    pytesseract.pytesseract.tesseract_cmd = tess_path

    tessdata_dir = get_tessdata_dir(tess_path)
    if tessdata_dir and os.path.isdir(tessdata_dir):
        os.environ["TESSDATA_PREFIX"] = tessdata_dir
        lang_file = os.path.join(tessdata_dir, f"{lang}.traineddata")
        if not os.path.exists(lang_file):
            if os.path.exists(os.path.join(tessdata_dir, "eng.traineddata")):
                lang = "eng"
            else:
                raise FileNotFoundError(
                    f"No se encontraron modelos de idioma (.traineddata) en:\n{tessdata_dir}"
                )
    return lang


def _page_to_img(page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    del pix
    return img


def run_ocr_pdf(input_path: str, output_path: str, lang: str, on_progress, cancel_event: threading.Event = None):
    if len(output_path) > 255:
        raise ValueError(f"Ruta de salida demasiado larga ({len(output_path)} caracteres). Usa una carpeta más corta.")

    lang = _setup_tesseract(lang)
    doc = fitz.open(input_path)
    total = doc.page_count
    if total == 0:
        doc.close()
        raise ValueError("El documento PDF está vacío (0 páginas).")

    DPI = 300
    SCALE = 72.0 / DPI

    try:
        for i in range(total):
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Operación cancelada por el usuario.")

            pct = (i / total) * 92.0
            on_progress(f"Procesando página {i + 1} de {total}...", pct)

            page = doc[i]
            img = _page_to_img(page, dpi=DPI)

            try:
                data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
            except Exception:
                try:
                    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
                except Exception:
                    del img
                    continue

            del img

            text_items = data.get("text", [])
            for j in range(len(text_items)):
                word = text_items[j]
                if not word or not word.strip():
                    continue

                try:
                    conf = int(data["conf"][j])
                except (ValueError, TypeError, KeyError):
                    conf = -1

                if conf >= 0 and conf < 25:
                    continue

                x0 = data["left"][j] * SCALE
                y0 = data["top"][j] * SCALE
                h = data["height"][j] * SCALE

                page.insert_text(
                    fitz.Point(x0, y0 + h),
                    word,
                    fontsize=max(4.0, h),
                    render_mode=3,  # Texto invisible (buscable y seleccionable)
                )

            if i % 10 == 0:
                gc.collect()

        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Operación cancelada por el usuario.")

        on_progress("Guardando y optimizando PDF resultante...", 95.0)
        doc.save(
            output_path,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            garbage=4,
            clean=True,
        )
    finally:
        doc.close()
        gc.collect()


def run_ocr_txt(input_path: str, output_path: str, lang: str, on_progress, cancel_event: threading.Event = None):
    lang = _setup_tesseract(lang)
    doc = fitz.open(input_path)
    total = doc.page_count
    if total == 0:
        doc.close()
        raise ValueError("El documento PDF está vacío (0 páginas).")

    pages_text = []
    try:
        for i in range(total):
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Operación cancelada por el usuario.")

            pct = (i / total) * 92.0
            on_progress(f"Extrayendo texto de página {i + 1} de {total}...", pct)

            page = doc[i]
            img = _page_to_img(page, dpi=300)

            try:
                text = pytesseract.image_to_string(img, lang=lang)
            except Exception:
                text = pytesseract.image_to_string(img, lang="eng")

            del img
            pages_text.append(f"--- Página {i + 1} ---\n\n" + text.strip())

            if i % 10 == 0:
                gc.collect()

        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Operación cancelada por el usuario.")

        on_progress("Guardando archivo de texto...", 96.0)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n\n".join(pages_text))
    finally:
        doc.close()
        gc.collect()


class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, summary: str, detail: str):
        super().__init__(parent)
        self.title("Aviso de Error")
        self.resizable(True, True)
        self.geometry("580x360")
        self.grab_set()

        header_frame = ttk.Frame(self, padding=12)
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text=summary,
            font=("Segoe UI", 10, "bold"),
            foreground="#c0392b",
            wraplength=540,
        ).pack(anchor="w")

        frame = ttk.Frame(self, padding=(12, 0, 12, 8))
        frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(frame, font=("Consolas", 9), wrap=tk.WORD, bg="#f8f9fa", relief=tk.SOLID, bd=1)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.insert("1.0", detail)
        text.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Copiar detalles", command=lambda: self._copy(detail)).pack(side=tk.LEFT, padx=6)
        if "tesseract" in summary.lower() or "tesseract" in detail.lower():
            ttk.Button(btn_frame, text="🌐 Descargar Tesseract", command=lambda: webbrowser.open(TESSERACT_DOWNLOAD_URL)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=6)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Mágico - PDF Buscable")
        self.root.geometry("580x480")
        self.root.minsize(520, 440)
        self.root.resizable(True, True)

        self.input_pdf = tk.StringVar()
        self.output_path = tk.StringVar()
        self.lang_var = tk.StringVar(value="spa")
        self.format_var = tk.StringVar(value=FORMATS[0])
        self.cancel_event = threading.Event()
        self.is_processing = False

        self._build_ui()
        self._check_tesseract_status()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 9))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))

        main_frame = ttk.Frame(self.root, padding="16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Encabezado
        self._click_count = 0
        header_row = ttk.Frame(main_frame)
        header_row.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ttk.Label(header_row, text="📄 OCR Mágico", style="Header.TLabel", cursor="hand2")
        title_lbl.pack(side=tk.LEFT)
        title_lbl.bind("<Button-1>", self._on_title_click)

        sub_lbl = ttk.Label(header_row, text="v1.0.0", font=("Segoe UI", 8), foreground="#888888")
        sub_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=(4, 0))

        # Barra de estado de Tesseract
        self.tess_banner = ttk.Frame(main_frame, padding=6)
        self.tess_banner.pack(fill=tk.X, pady=(0, 10))
        self.tess_status_lbl = ttk.Label(self.tess_banner, text="Detectando motor OCR...", font=("Segoe UI", 8))
        self.tess_status_lbl.pack(side=tk.LEFT)
        self.tess_btn_dl = ttk.Button(
            self.tess_banner, text="Descargar Tesseract", command=lambda: webbrowser.open(TESSERACT_DOWNLOAD_URL)
        )

        # Selección de archivos
        self._file_row(main_frame, "1. Archivo PDF original:", self.input_pdf, self._browse_input)
        self._file_row(
            main_frame, "2. Guardar resultado como:", self.output_path, self._browse_output, save=True, editable=True
        )

        # Opciones de configuración
        opts_group = ttk.LabelFrame(main_frame, text=" Configuración ", padding=10)
        opts_group.pack(fill=tk.X, pady=8)

        opts_row = ttk.Frame(opts_group)
        opts_row.pack(fill=tk.X)

        ttk.Label(opts_row, text="Idioma:").pack(side=tk.LEFT, padx=(0, 6))
        self.lang_choices = get_available_languages()
        self.lang_cb = ttk.Combobox(
            opts_row,
            textvariable=self.lang_var,
            values=[c[0] for c in self.lang_choices],
            width=8,
            state="readonly",
        )
        self.lang_cb.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(opts_row, text="Formato:").pack(side=tk.LEFT, padx=(0, 6))
        fmt_cb = ttk.Combobox(
            opts_row, textvariable=self.format_var, values=FORMATS, width=28, state="readonly"
        )
        fmt_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        fmt_cb.bind("<<ComboboxSelected>>", self._on_format_change)

        # Progreso
        prog_frame = ttk.Frame(main_frame)
        prog_frame.pack(fill=tk.X, pady=(10, 4))

        self.status_lbl = ttk.Label(prog_frame, text="Listo para procesar.", foreground="#555555")
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        self.progress = ttk.Progressbar(prog_frame, mode="determinate")
        self.progress.pack(fill=tk.X, pady=2)

        # Botones de acción
        btn_box = ttk.Frame(main_frame)
        btn_box.pack(fill=tk.X, pady=(12, 0))

        self.btn_run = ttk.Button(btn_box, text="▶  Iniciar OCR", style="Action.TButton", command=self._start)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)

        self.btn_cancel = ttk.Button(btn_box, text="⏹ Cancelar", command=self._cancel, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT)

    def _check_tesseract_status(self):
        tess_path = find_tesseract()
        if tess_path:
            is_bundled = "tesseract" in tess_path.lower() and _app_dir().lower() in tess_path.lower()
            tipo = "portable" if is_bundled else "sistema"
            self.tess_status_lbl.config(
                text=f"✓ Motor OCR listo ({tipo}): {os.path.basename(tess_path)}", foreground="#27ae60"
            )
            self.tess_btn_dl.pack_forget()
        else:
            self.tess_status_lbl.config(
                text="⚠ Tesseract OCR no detectado. Instálalo para usar la aplicación:", foreground="#c0392b"
            )
            self.tess_btn_dl.pack(side=tk.RIGHT, padx=6)

    def _file_row(self, parent, label, var, cmd, save=False, editable=False):
        group = ttk.Frame(parent)
        group.pack(fill=tk.X, pady=4)
        ttk.Label(group, text=label, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 2))

        row = ttk.Frame(group)
        row.pack(fill=tk.X)
        ttk.Entry(row, textvariable=var, state=tk.NORMAL if editable else "readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
        )
        ttk.Button(row, text="Guardar en..." if save else "Examinar...", command=cmd).pack(side=tk.RIGHT)

    def _is_txt_mode(self) -> bool:
        return self.format_var.get() == FORMATS[1]

    def _on_format_change(self, _=None):
        current = self.output_path.get()
        if not current:
            return
        base = os.path.splitext(current)[0]
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
        w.geometry("340x220")

        tk.Label(w, text="♥", font=("Segoe UI", 48), fg="#e74c3c").pack(pady=(16, 2))
        tk.Label(
            w,
            text="Hecho con amor por tu hermanito,\npara ti, Evelin ❤️",
            font=("Segoe UI", 11, "bold"),
            justify="center",
        ).pack()
        tk.Label(
            w, text="Espero que te sirva mucho para estudiar :)", font=("Segoe UI", 9), fg="#555555"
        ).pack(pady=(6, 14))
        ttk.Button(w, text="Cerrar", command=w.destroy).pack()

    def _browse_input(self):
        path = filedialog.askopenfilename(
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.input_pdf.set(path)
            ext = ".txt" if self._is_txt_mode() else ".pdf"
            self.output_path.set(safe_output_path(path, ext))

    def _browse_output(self):
        if self._is_txt_mode():
            path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Documento de texto", "*.txt")]
            )
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("Documento PDF", "*.pdf")]
            )
        if path:
            self.output_path.set(path)

    def _start(self):
        inp = self.input_pdf.get()
        out = self.output_path.get()
        if not inp or not out:
            messagebox.showwarning("Atención", "Por favor selecciona el archivo PDF original y la ruta de destino.")
            return

        if not os.path.isfile(inp):
            messagebox.showerror("Error", "El archivo de entrada no existe.")
            return

        if not find_tesseract():
            self._check_tesseract_status()
            res = messagebox.askyesno(
                "Tesseract no encontrado",
                "No se encontró Tesseract OCR en tu computadora.\n\n"
                "¿Deseas abrir la página de descarga para instalarlo ahora?",
            )
            if res:
                webbrowser.open(TESSERACT_DOWNLOAD_URL)
            return

        self.is_processing = True
        self.cancel_event.clear()
        self.btn_run.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress.config(value=0)
        threading.Thread(target=self._process, daemon=True).start()

    def _cancel(self):
        if self.is_processing:
            self.cancel_event.set()
            self.status_lbl.config(text="Cancelando operación...")
            self.btn_cancel.config(state=tk.DISABLED)

    def _update(self, msg, val=None):
        self.status_lbl.config(text=msg)
        if val is not None:
            self.progress.config(value=val)
        self.root.update_idletasks()

    def _process(self):
        inp = self.input_pdf.get()
        out = self.output_path.get()
        lang = self.lang_var.get()
        try:
            if self._is_txt_mode():
                run_ocr_txt(inp, out, lang, self._update, self.cancel_event)
            else:
                run_ocr_pdf(inp, out, lang, self._update, self.cancel_event)

            self._update("¡Completado con éxito!", 100)
            self.root.after(0, lambda: self._show_success(out))
        except InterruptedError:
            self._update("Operación cancelada.", 0)
            if os.path.exists(out):
                try:
                    os.remove(out)
                except Exception:
                    pass
        except Exception as exc:
            tb = traceback.format_exc()
            summary = classify_error(exc)
            self._update(f"Error: {summary}", 0)
            self.root.after(0, lambda: ErrorDialog(self.root, summary, tb))
        finally:
            self.is_processing = False
            self.root.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.btn_run.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)

    def _show_success(self, out_path: str):
        dialog = tk.Toplevel(self.root)
        dialog.title("¡OCR Completado!")
        dialog.geometry("460x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(dialog, text="🎉 Documento generado con éxito", font=("Segoe UI", 11, "bold"), foreground="#27ae60").pack(
            pady=(16, 8)
        )
        ttk.Label(dialog, text=f"Guardado en:\n{out_path}", wraplength=420, justify="center").pack(pady=(0, 14))

        btn_row = ttk.Frame(dialog)
        btn_row.pack(pady=(0, 10))

        def open_file():
            try:
                os.startfile(out_path)
            except Exception as e:
                messagebox.showerror("Error al abrir", str(e))

        def open_folder():
            try:
                os.startfile(os.path.dirname(out_path))
            except Exception as e:
                messagebox.showerror("Error al abrir carpeta", str(e))

        ttk.Button(btn_row, text="Abrir archivo", command=open_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Abrir carpeta", command=open_folder).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Cerrar", command=dialog.destroy).pack(side=tk.LEFT, padx=6)
