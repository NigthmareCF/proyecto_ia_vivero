"""
limpiar_dataset.py  (MEJORADO v2)
===================================
Filtros activos:
  1. Imagen corrupta
  2. Tamaño mínimo (180x180)
  3. Imagen plana/vacía (std baja)
  4. Fondo blanco dominante >90%  ← NUEVO
  5. Texto detectado por Tesseract ← NUEVO
  6. Duplicados por pHash (distancia <= 10)

Requisitos:
    pip install Pillow imagehash numpy tqdm pytesseract
    Tesseract instalado en: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
"""

from pathlib import Path
import numpy as np
from PIL import Image
import imagehash
import pytesseract
from tqdm import tqdm

# ─── Configuración ───────────────────────────────────────────────────────────

BASE_DIR    = Path("C:/Proyecto_IA_Vivero/dataset/raw")
CLASES      = ["sano", "atencion", "peligro"]

MIN_WIDTH      = 180    # píxeles mínimos de ancho
MIN_HEIGHT     = 180    # píxeles mínimos de alto
STD_MINIMA     = 8.0    # std mínima de color (detecta imágenes planas/vacías)
HASH_SIZE      = 8      # tamaño del hash perceptual
DISTANCIA_HASH = 10     # 0=solo exactos | 10=muy similares | 20=bastante parecidas

UMBRAL_BLANCO  = 0.90   # eliminar si >90% de píxeles son blancos (R,G,B > 240)
MIN_CHARS_TEXTO = 15    # eliminar si Tesseract detecta >= 15 caracteres de texto

# Ruta a Tesseract en Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ─── Funciones ───────────────────────────────────────────────────────────────

def imagen_casi_vacia(img: Image.Image) -> bool:
    """Detecta fondos planos, diapositivas blancas, imágenes sin contenido."""
    arr = np.array(img.convert("RGB"), dtype=np.uint8)
    return float(arr.std()) < STD_MINIMA


def fondo_blanco_dominante(img: Image.Image) -> bool:
    """
    Devuelve True si más del UMBRAL_BLANCO de los píxeles son blancos.
    Blanco = R > 240 AND G > 240 AND B > 240
    """
    arr = np.array(img.convert("RGB"), dtype=np.uint8)
    mascara_blanca = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
    porcentaje = mascara_blanca.sum() / mascara_blanca.size
    return porcentaje > UMBRAL_BLANCO


def tiene_texto(img: Image.Image) -> bool:
    """
    Usa Tesseract OCR para detectar si la imagen contiene texto significativo.
    Si detecta >= MIN_CHARS_TEXTO caracteres no espacios, considera que es
    una infografía, diagrama o imagen con texto y la elimina.
    """
    try:
        texto = pytesseract.image_to_string(img, config="--psm 11 --oem 1")
        chars_utiles = len(texto.replace(" ", "").replace("\n", "").strip())
        return chars_utiles >= MIN_CHARS_TEXTO
    except Exception:
        return False


def limpiar_carpeta(carpeta: Path) -> dict:
    contadores = {
        "correctas":  0,
        "corruptas":  0,
        "pequeñas":   0,
        "vacias":     0,
        "blancas":    0,   # NUEVO
        "con_texto":  0,   # NUEVO
        "duplicadas": 0,
    }

    archivos = [
        f for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    ]

    hashes_vistos: list[tuple] = []   # (imagehash_obj, nombre)

    with tqdm(total=len(archivos), desc=carpeta.name, unit="img", colour="cyan") as barra:
        for archivo in archivos:
            barra.update(1)

            try:
                # ── 1. Verificar integridad ──────────────────────────────
                with Image.open(archivo) as img:
                    img.verify()

                with Image.open(archivo) as img:
                    img = img.convert("RGB")
                    w, h = img.size

                    # ── 2. Tamaño mínimo ─────────────────────────────────
                    if w < MIN_WIDTH or h < MIN_HEIGHT:
                        archivo.unlink()
                        contadores["pequeñas"] += 1
                        barra.set_postfix_str(f"pequeña {w}x{h}")
                        continue

                    # ── 3. Imagen casi vacía / plana ─────────────────────
                    if imagen_casi_vacia(img):
                        archivo.unlink()
                        contadores["vacias"] += 1
                        barra.set_postfix_str("vacía/plana")
                        continue

                    # ── 4. Fondo blanco dominante (>90%) ─────────────────
                    if fondo_blanco_dominante(img):
                        archivo.unlink()
                        contadores["blancas"] += 1
                        barra.set_postfix_str("fondo blanco")
                        continue

                    # ── 5. Texto detectado por Tesseract ─────────────────
                    if tiene_texto(img):
                        archivo.unlink()
                        contadores["con_texto"] += 1
                        barra.set_postfix_str("con texto")
                        continue

                    # ── 6. Duplicados por hash perceptual ────────────────
                    phash_actual = imagehash.phash(img, hash_size=HASH_SIZE)

                    es_duplicada = False
                    for phash_visto, _ in hashes_vistos:
                        if abs(phash_actual - phash_visto) <= DISTANCIA_HASH:
                            es_duplicada = True
                            break

                    if es_duplicada:
                        archivo.unlink()
                        contadores["duplicadas"] += 1
                        barra.set_postfix_str("duplicada")
                        continue

                    hashes_vistos.append((phash_actual, archivo.name))
                    contadores["correctas"] += 1

            except Exception:
                try:
                    archivo.unlink()
                    contadores["corruptas"] += 1
                    barra.set_postfix_str("corrupta")
                except Exception:
                    pass

    return contadores


def main():
    if not BASE_DIR.exists():
        print("ERROR: No existe dataset/raw")
        return

    resumen_global = {}

    for clase in CLASES:
        carpeta = BASE_DIR / clase
        if not carpeta.exists():
            print(f"  Carpeta no encontrada: {carpeta}")
            continue

        print(f"\n{'─'*50}")
        print(f"  Clase: {clase.upper()}")
        print(f"{'─'*50}")

        contadores = limpiar_carpeta(carpeta)
        resumen_global[clase] = contadores

    # ── Reporte final ────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("  RESUMEN FINAL DE LIMPIEZA")
    print(f"{'='*72}")
    print(f"{'Clase':<12} {'Correctas':>10} {'Corruptas':>10} {'Pequeñas':>10} {'Vacías':>8} {'Blancas':>8} {'Texto':>7} {'Duplic.':>8}")
    print(f"{'─'*72}")

    total_correctas = 0
    for clase, c in resumen_global.items():
        print(
            f"{clase:<12} {c['correctas']:>10} {c['corruptas']:>10} "
            f"{c['pequeñas']:>10} {c['vacias']:>8} {c['blancas']:>8} "
            f"{c['con_texto']:>7} {c['duplicadas']:>8}"
        )
        total_correctas += c["correctas"]

    print(f"{'─'*72}")
    print(f"{'TOTAL':<12} {total_correctas:>10} imágenes limpias en dataset/raw")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
