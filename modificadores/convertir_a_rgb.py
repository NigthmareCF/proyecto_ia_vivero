"""
convertir_a_rgb.py
===================
Convierte TODAS las imágenes de train/validation/test a JPEG RGB puro.
Elimina cualquier imagen que no se pueda abrir o convertir.
Corre este script UNA VEZ antes de entrenar_modelo.py.

Requisitos:
    pip install Pillow tqdm
"""

from pathlib import Path
from PIL import Image
from tqdm import tqdm

SPLITS  = ["train", "validation", "test"]
CLASES  = ["sano", "atencion", "peligro"]
BASE    = Path("dataset")
EXTS    = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

convertidas = 0
eliminadas  = 0
omitidas    = 0

for split in SPLITS:
    for clase in CLASES:
        carpeta = BASE / split / clase
        if not carpeta.exists():
            continue

        archivos = [f for f in carpeta.iterdir()
                    if f.is_file() and f.suffix.lower() in EXTS]

        for archivo in tqdm(archivos, desc=f"{split}/{clase}", unit="img"):
            try:
                with Image.open(archivo) as img:
                    # Convertir a RGB sin importar el modo original
                    # (RGBA, L, P, LA, etc.)
                    rgb = img.convert("RGB")

                # Guardar como JPG en el mismo lugar
                nuevo_nombre = archivo.with_suffix(".jpg")
                rgb.save(nuevo_nombre, "JPEG", quality=95)

                # Si era PNG u otro formato, eliminar el original
                if archivo.suffix.lower() != ".jpg":
                    archivo.unlink()
                    convertidas += 1
                else:
                    omitidas += 1

            except Exception as e:
                try:
                    archivo.unlink()
                    eliminadas += 1
                except Exception:
                    pass

print(f"\n{'='*40}")
print(f"  Convertidas a JPG RGB : {convertidas}")
print(f"  Ya eran JPG (ok)      : {omitidas}")
print(f"  Eliminadas (corruptas): {eliminadas}")
print(f"{'='*40}")
print("Listo. Ahora corre entrenar_modelo.py\n")
