#!/usr/bin/env python3
"""02_preprocesar_raw.py
Deduplicación por phash, resize a IMG_SIZE y validación de imágenes en dataset/raw/
"""
import argparse
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import imagehash
import sys


def iter_image_files(folder: Path):
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png'):
            yield p


def process_class(class_dir: Path, img_size=(224, 224), hash_thresh=8):
    seen_hashes = []
    removed_dup = 0
    removed_corrupt = 0
    # Deduplication
    for p in list(iter_image_files(class_dir)):
        try:
            with Image.open(p) as im:
                ph = imagehash.phash(im)
        except UnidentifiedImageError:
            print(f"Removing corrupt image (cannot open): {p}")
            p.unlink(missing_ok=True)
            removed_corrupt += 1
            continue
        except Exception as e:
            print(f"WARN: error hashing {p}: {e}", file=sys.stderr)
            continue
        dup = False
        for h in seen_hashes:
            if ph - h <= hash_thresh:
                dup = True
                break
        if dup:
            p.unlink(missing_ok=True)
            removed_dup += 1
        else:
            seen_hashes.append(ph)
    # Resize and validate
    for p in list(iter_image_files(class_dir)):
        try:
            with Image.open(p) as im:
                im = im.convert('RGB')
                im = im.resize(img_size, Image.LANCZOS)
                im.save(p, format='JPEG', quality=95)
        except Exception as e:
            print(f"Removing corrupt/failed image during resize: {p} ({e})")
            p.unlink(missing_ok=True)
            removed_corrupt += 1
    total_after = sum(1 for _ in iter_image_files(class_dir))
    return removed_dup, removed_corrupt, total_after


def main():
    parser = argparse.ArgumentParser(description='Preprocesar dataset raw')
    parser.add_argument('--raw_dir', default=str(Path(__file__).resolve().parent / 'dataset' / 'raw'), help='Ruta a dataset/raw/')
    parser.add_argument('--img_size', type=int, nargs=2, default=(224, 224), help='Tamaño objetivo, ej: --img_size 224 224')
    parser.add_argument('--hash_thresh', type=int, default=8, help='Distancia hamming para considerar duplicado (default 8)')
    args = parser.parse_args()

    raw = Path(args.raw_dir)
    if not raw.exists():
        print(f"raw_dir no existe: {raw}")
        return
    classes = [p.name for p in raw.iterdir() if p.is_dir()]
    for clase in classes:
        class_dir = raw / clase
        print(f"Procesando clase: {clase} (dir: {class_dir})")
        removed_dup, removed_corrupt, total_after = process_class(class_dir, tuple(args.img_size), args.hash_thresh)
        print(f"Clase {clase}: duplicados eliminados={removed_dup}, corruptos eliminados={removed_corrupt}, total_final={total_after}")


if __name__ == '__main__':
    main()
