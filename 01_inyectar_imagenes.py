#!/usr/bin/env python3
"""01_inyectar_imagenes.py
Inyecta imágenes nuevas en dataset/raw/{clase}/ renombrando como {clase}_{N}.jpg
"""
import argparse
import re
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import sys

FNAME_RE = re.compile(r"^(?P<class>.+)_(?P<idx>\d+)\.(?P<ext>jpg|jpeg|png)$", re.IGNORECASE)


def get_max_index(raw_dir: Path, clase: str) -> int:
    max_idx = 0
    if not raw_dir.exists():
        return 0
    for p in raw_dir.iterdir():
        if not p.is_file():
            continue
        m = FNAME_RE.match(p.name)
        if m and m.group('class').lower() == clase.lower():
            try:
                idx = int(m.group('idx'))
                if idx > max_idx:
                    max_idx = idx
            except ValueError:
                continue
    return max_idx


def inject_folder(src_folder: Path, raw_dir: Path, clase: str) -> int:
    src = Path(src_folder)
    dest_dir = Path(raw_dir) / clase
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return 0
    files = [p for p in src.iterdir() if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png')]
    idx = get_max_index(dest_dir, clase) + 1
    injected = 0
    for f in files:
        try:
            with Image.open(f) as im:
                im = im.convert('RGB')
                out_name = f"{clase}_{idx}.jpg"
                out_path = dest_dir / out_name
                im.save(out_path, format='JPEG', quality=95)
                injected += 1
                idx += 1
        except UnidentifiedImageError:
            print(f"WARN: could not identify image {f}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: saving {f}: {e}", file=sys.stderr)
    return injected


def main():
    default_base = Path(r"C:\Users\ferch\OneDrive\Escritorio\Reiinyeccion")
    parser = argparse.ArgumentParser(description='Inyectar imágenes nuevas al raw dataset')
    parser.add_argument('--nuevas_sano', default=str(default_base / 'nuevas_sano'), help='Ruta a nuevas_sano/')
    parser.add_argument('--nuevas_atencion', default=str(default_base / 'nuevas_atencion'), help='Ruta a nuevas_atencion/')
    parser.add_argument('--raw_dir', default=str(Path(__file__).resolve().parent / 'dataset' / 'raw'), help='Ruta a dataset/raw/')
    args = parser.parse_args()

    raw = Path(args.raw_dir)
    sano_count = inject_folder(Path(args.nuevas_sano), raw, 'sano')
    atencion_count = inject_folder(Path(args.nuevas_atencion), raw, 'atencion')

    print(f"Inyección completada. sano: {sano_count}, atencion: {atencion_count}")


if __name__ == '__main__':
    main()
