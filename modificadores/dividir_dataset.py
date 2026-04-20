"""
dividir_dataset.py  (MEJORADO)
================================
Mejoras respecto al original:
  - Solo copia archivos de imagen (ignora .db, .ini, thumbs, etc.)
  - Verifica que las carpetas destino estén vacías antes de dividir
    (evita duplicar si se corre dos veces)
  - Seed configurable para reproducibilidad (mismo split siempre)
  - Reporte final con conteos exactos por split y clase
  - División estratificada: 70% train / 20% validation / 10% test

IMPORTANTE — leer antes de ejecutar:
  Corre limpiar_dataset.py ANTES de este script.
  La división se hace sobre dataset/raw (ya limpio).
"""

import os
import random
import shutil
from pathlib import Path

# ─── Configuración ───────────────────────────────────────────────────────────

ORIGEN  = Path("C:/Proyecto_IA_Vivero/dataset/raw")
DESTINO = Path("dataset")
CLASES  = ["sano", "atencion", "peligro"]

SPLIT_TRAIN      = 0.70
SPLIT_VALIDATION = 0.20
# SPLIT_TEST = lo que sobra (~0.10)

SEED = 42   # Fija el seed para reproducibilidad: mismo resultado cada vez que corras el script

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


# ─── Utilidades ──────────────────────────────────────────────────────────────

def carpetas_destino_vacias() -> bool:
    """
    Verifica que train/validation/test estén vacíos.
    Si ya tienen archivos, detiene la ejecución para evitar duplicados.
    """
    for split in ["train", "validation", "test"]:
        for clase in CLASES:
            carpeta = DESTINO / split / clase
            if carpeta.exists():
                archivos = [f for f in carpeta.iterdir() if f.is_file()]
                if archivos:
                    return False
    return True


def limpiar_destinos():
    """Elimina el contenido de train/validation/test si el usuario lo confirma."""
    for split in ["train", "validation", "test"]:
        ruta = DESTINO / split
        if ruta.exists():
            shutil.rmtree(ruta)
            print(f"  Eliminado: {ruta}")


def obtener_imagenes(carpeta: Path) -> list:
    return sorted([
        f for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES_VALIDAS
    ])


# ─── División ────────────────────────────────────────────────────────────────

def dividir_clase(clase: str) -> dict:
    carpeta_origen = ORIGEN / clase
    if not carpeta_origen.exists():
        print(f"  ADVERTENCIA: No existe {carpeta_origen}")
        return {}

    archivos = obtener_imagenes(carpeta_origen)
    random.shuffle(archivos)

    total = len(archivos)
    if total == 0:
        print(f"  ADVERTENCIA: {carpeta_origen} está vacía")
        return {}

    n_train = int(total * SPLIT_TRAIN)
    n_val   = int(total * SPLIT_VALIDATION)
    # El resto va a test para no perder ningún archivo por redondeo

    splits = {
        "train":      archivos[:n_train],
        "validation": archivos[n_train : n_train + n_val],
        "test":       archivos[n_train + n_val :],
    }

    conteos = {}
    for split_name, lista in splits.items():
        carpeta_destino = DESTINO / split_name / clase
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        for archivo in lista:
            shutil.copy2(str(archivo), str(carpeta_destino / archivo.name))

        conteos[split_name] = len(lista)

    return conteos


def main():
    if not ORIGEN.exists():
        print("ERROR: No existe dataset/raw — corre limpiar_dataset.py primero.")
        return

    # ── Verificar si ya hay archivos en destino ──────────────────────────────
    if not carpetas_destino_vacias():
        print("\nADVERTENCIA: Las carpetas train/validation/test ya contienen archivos.")
        print("Si continúas, se eliminarán y se volverán a crear desde cero.")
        respuesta = input("¿Deseas continuar? (s/n): ").strip().lower()
        if respuesta != "s":
            print("Operación cancelada.")
            return
        print("\nEliminando carpetas anteriores...")
        limpiar_destinos()

    # ── División ─────────────────────────────────────────────────────────────
    random.seed(SEED)

    print(f"\nDividiendo dataset con seed={SEED}")
    print(f"Split: {int(SPLIT_TRAIN*100)}% train / {int(SPLIT_VALIDATION*100)}% validation / {int((1-SPLIT_TRAIN-SPLIT_VALIDATION)*100)}% test\n")

    resumen = {}
    for clase in CLASES:
        conteos = dividir_clase(clase)
        resumen[clase] = conteos
        total = sum(conteos.values())
        print(f"  {clase:<12} → train: {conteos.get('train',0):>5} | val: {conteos.get('validation',0):>5} | test: {conteos.get('test',0):>5} | total: {total:>6}")

    # ── Reporte final ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RESUMEN FINAL DE DIVISIÓN")
    print(f"{'='*60}")
    print(f"{'Split':<14} {'sano':>8} {'atencion':>10} {'peligro':>10} {'total':>8}")
    print(f"{'─'*60}")

    for split in ["train", "validation", "test"]:
        fila = {clase: resumen.get(clase, {}).get(split, 0) for clase in CLASES}
        total_fila = sum(fila.values())
        print(
            f"{split:<14} {fila['sano']:>8} {fila['atencion']:>10} "
            f"{fila['peligro']:>10} {total_fila:>8}"
        )

    print(f"{'─'*60}")
    total_global = sum(
        resumen.get(clase, {}).get(split, 0)
        for clase in CLASES
        for split in ["train", "validation", "test"]
    )
    print(f"{'TOTAL':<14} {total_global:>38}")
    print(f"{'='*60}\n")
    print("División completada correctamente.")


if __name__ == "__main__":
    main()
