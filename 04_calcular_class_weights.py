#!/usr/bin/env python3
"""04_calcular_class_weights.py
Cuenta imágenes en dataset/train/ y calcula class_weight con sklearn.
"""
import argparse
from pathlib import Path
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

LABEL_MAP = {'atencion': 0, 'sano': 1, 'peligro': 2}


def main():
    parser = argparse.ArgumentParser(description='Calcular class weights desde dataset/train/')
    parser.add_argument('--train_dir', default=str(Path(__file__).resolve().parent / 'dataset' / 'train'), help='Ruta a dataset/train/')
    args = parser.parse_args()
    train = Path(args.train_dir)
    if not train.exists():
        print(f"train_dir no existe: {train}")
        return
    y = []
    counts = {}
    for class_name, label in LABEL_MAP.items():
        class_dir = train / class_name
        if not class_dir.exists():
            counts[class_name] = 0
            continue
        cnt = sum(1 for _ in class_dir.iterdir() if _.is_file() and _.suffix.lower() in ('.jpg', '.jpeg', '.png'))
        counts[class_name] = cnt
        y.extend([label] * cnt)
    if len(y) == 0:
        print('No hay imágenes en train/ para calcular pesos')
        return
    classes = np.unique(list(LABEL_MAP.values()))
    cw = compute_class_weight(class_weight='balanced', classes=classes, y=np.array(y))
    cw_dict = {int(cls): float(w) for cls, w in zip(classes, cw)}
    print('class_weight_dict =', cw_dict)
    print('counts =', counts)


if __name__ == '__main__':
    main()
