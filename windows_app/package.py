import os
import shutil
import zipfile
import subprocess
import sys

def build_and_package():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    windows_app_dir = os.path.join(base_dir, "windows_app")
    dist_dir = os.path.join(windows_app_dir, "dist")
    app_dist = os.path.join(dist_dir, "OCR_App")

    print("[1/4] Compilando ejecutable con PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "OCR_App",
        "--distpath", dist_dir,
        "--workpath", os.path.join(windows_app_dir, "build"),
        os.path.join(windows_app_dir, "app.py")
    ]
    subprocess.run(cmd, check=True)

    print("[2/4] Copiando Tesseract portable...")
    tess_src = os.path.join(windows_app_dir, "tesseract")
    tess_dest = os.path.join(app_dist, "tesseract")
    os.makedirs(tess_dest, exist_ok=True)

    if os.path.isdir(tess_src):
        for item in os.listdir(tess_src):
            s = os.path.join(tess_src, item)
            d = os.path.join(tess_dest, item)
            if os.path.isfile(s) and (item.endswith(".dll") or item == "tesseract.exe"):
                shutil.copy2(s, d)

        tessdata_src = os.path.join(tess_src, "tessdata")
        tessdata_dest = os.path.join(tess_dest, "tessdata")
        os.makedirs(tessdata_dest, exist_ok=True)
        if os.path.isdir(tessdata_src):
            for item in os.listdir(tessdata_src):
                if item.endswith(".traineddata") or item.endswith(".ttf") or item.endswith(".user-patterns") or item.endswith(".user-words"):
                    shutil.copy2(os.path.join(tessdata_src, item), os.path.join(tessdata_dest, item))

    print("[3/4] Generando instrucciones...")
    with open(os.path.join(app_dist, "LEEME.txt"), "w", encoding="utf-8") as f:
        f.write("==============================================\n")
        f.write("  OCR Magico - PDF Buscable (Windows)\n")
        f.write("==============================================\n\n")
        f.write("INSTRUCCIONES DE USO:\n")
        f.write("1. Haz doble clic en OCR_App.exe para abrir la aplicacion.\n")
        f.write("2. Selecciona tu archivo PDF en 'Examinar...'.\n")
        f.write("3. Selecciona la carpeta y nombre de salida.\n")
        f.write("4. Elige el idioma (Espanol o Ingles) y el formato.\n")
        f.write("5. Haz clic en 'Iniciar OCR'.\n\n")
        f.write("Esta aplicacion es 100% portable y no requiere instalar Python ni Tesseract.\n")

    print("[4/4] Comprimiendo en OCR_App_Windows_x64.zip...")
    zip_path = os.path.join(dist_dir, "OCR_App_Windows_x64.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, _, files in os.walk(app_dist):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                zipf.write(full_path, rel_path)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\nEmpaquetado exitoso!")
    print(f"Archivo de distribucion: {zip_path}")
    print(f"Tamano: {size_mb:.2f} MB")

if __name__ == "__main__":
    build_and_package()
