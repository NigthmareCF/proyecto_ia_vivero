#!/usr/bin/env python3
"""03_split_dataset.py
Re-split estratificado del contenido de dataset/raw/ hacia dataset/{train,validation,test}/
"""
import argparse
from pathlib import Path
import random
import shutil


def clear_and_create_splits(output_dir: Path, classes):
    for split in ('train', 'validation', 'test'):
        split_dir = output_dir / split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        for c in classes:
            (split_dir / c).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description='Split estratificado del raw dataset')
    parser.add_argument('--raw_dir', default=str(Path(__file__).resolve().parent / 'dataset' / 'raw'), help='Ruta a dataset/raw/')
    parser.add_argument('--output_dir', default=str(Path(__file__).resolve().parent / 'dataset'), help='Ruta a dataset/ (contendrá train/ validation/ test/)')
    parser.add_argument('--train_ratio', type=float, default=0.70)
    parser.add_argument('--val_ratio', type=float, default=0.20)
    parser.add_argument('--test_ratio', type=float, default=0.10)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    raw = Path(args.raw_dir)
    out = Path(args.output_dir)
    classes = [p.name for p in raw.iterdir() if p.is_dir()]
    clear_and_create_splits(out, classes)
    random.seed(args.seed)
    summary = {}
    for c in classes:
        files = [p for p in (raw / c).iterdir() if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png')]
        total = len(files)
        random.shuffle(files)
        n_train = int(total * args.train_ratio)
        n_val = int(total * args.val_ratio)
        n_test = total - n_train - n_val
        # slices
        train_files = files[:n_train]
        val_files = files[n_train:n_train + n_val]
        test_files = files[n_train + n_val:]
        for p in train_files:
            shutil.copy2(p, out / 'train' / c / p.name)
        for p in val_files:
            shutil.copy2(p, out / 'validation' / c / p.name)
        for p in test_files:
            shutil.copy2(p, out / 'test' / c / p.name)
        summary[c] = {'total': total, 'train': len(train_files), 'validation': len(val_files), 'test': len(test_files)}
    # print table
    print('Clase\tTotal\tTrain\tVal\tTest')
    for c, v in summary.items():
        print(f"{c}\t{v['total']}\t{v['train']}\t{v['validation']}\t{v['test']}")


if __name__ == '__main__':
    main()
