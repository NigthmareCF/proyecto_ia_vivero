#!/usr/bin/env python3
"""Auditoria no destructiva del dataset para la fase 1 del modelo local.

Genera conteos, validacion de imagenes, duplicados exactos, similitud
perceptual, posible fuga entre splits y una muestra visual de errores de
clasificacion para la clase atencion.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import imagehash
import numpy as np
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


CLASSES = ("atencion", "peligro", "sano")
SPLITS = ("raw", "train", "validation", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
DEFAULT_DATASET = Path(__file__).resolve().parents[1] / "dataset"
DEFAULT_MODEL = Path(__file__).resolve().parents[1] / "modelos" / "modelo_vivero.tflite"
DEFAULT_LABELS = Path(__file__).resolve().parents[1] / "labels.txt"
DEFAULT_OUTPUT_BASE = Path(__file__).resolve().parent


@dataclass
class ImageRecord:
    split: str
    clase: str
    path: str
    name: str
    suffix: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    mode: str | None = None
    sha256: str | None = None
    phash: str | None = None
    readable: bool = False
    error: str | None = None


def iter_image_paths(dataset_dir: Path) -> Iterable[tuple[str, str, Path]]:
    for split in SPLITS:
        split_dir = dataset_dir / split
        if not split_dir.exists():
            continue
        for clase in CLASSES:
            class_dir = split_dir / clase
            if not class_dir.exists():
                continue
            for path in sorted(class_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    yield split, clase, path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_image(split: str, clase: str, path: Path, root: Path) -> ImageRecord:
    record = ImageRecord(
        split=split,
        clase=clase,
        path=str(path.relative_to(root.parent)).replace("\\", "/"),
        name=path.name,
        suffix=path.suffix.lower(),
        size_bytes=path.stat().st_size,
    )

    try:
        record.sha256 = sha256_file(path)
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            record.width, record.height = img.size
            record.mode = img.mode
            record.phash = str(imagehash.phash(img.convert("RGB"), hash_size=8))
            record.readable = True
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        record.error = f"{type(exc).__name__}: {exc}"
    return record


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_by_split_class(records: list[ImageRecord]) -> dict[str, dict[str, int]]:
    counts = {split: {clase: 0 for clase in CLASSES} for split in SPLITS}
    for record in records:
        counts[record.split][record.clase] += 1
    return counts


def find_exact_duplicates(records: list[ImageRecord]) -> list[dict]:
    groups = defaultdict(list)
    for record in records:
        if record.sha256:
            groups[record.sha256].append(record)

    rows = []
    for sha, items in groups.items():
        if len(items) < 2:
            continue
        splits = sorted({item.split for item in items})
        classes = sorted({item.clase for item in items})
        rows.append(
            {
                "sha256": sha,
                "count": len(items),
                "splits": "|".join(splits),
                "classes": "|".join(classes),
                "paths": "|".join(item.path for item in items),
            }
        )
    return sorted(rows, key=lambda row: (-row["count"], row["sha256"]))


def phash_to_int(hash_text: str) -> int:
    return int(hash_text, 16)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def find_perceptual_pairs(records: list[ImageRecord], threshold: int, limit: int) -> list[dict]:
    readable = [record for record in records if record.phash]
    buckets: dict[tuple[int, int], list[tuple[ImageRecord, int]]] = defaultdict(list)
    pairs: dict[tuple[str, str], dict] = {}

    for record in readable:
        value = phash_to_int(record.phash or "0")
        candidate_refs = []
        for band in range(4):
            key = (band, (value >> (band * 16)) & 0xFFFF)
            candidate_refs.extend(buckets.get(key, []))

        seen_candidates = set()
        for candidate, candidate_value in candidate_refs:
            if candidate.path in seen_candidates or candidate.path == record.path:
                continue
            seen_candidates.add(candidate.path)
            distance = hamming(value, candidate_value)
            if distance <= threshold:
                pair_key = tuple(sorted((record.path, candidate.path)))
                if pair_key not in pairs:
                    pairs[pair_key] = {
                        "distance": distance,
                        "split_a": candidate.split,
                        "class_a": candidate.clase,
                        "path_a": candidate.path,
                        "split_b": record.split,
                        "class_b": record.clase,
                        "path_b": record.path,
                        "cross_split": candidate.split != record.split,
                        "cross_class": candidate.clase != record.clase,
                    }

        for band in range(4):
            key = (band, (value >> (band * 16)) & 0xFFFF)
            buckets[key].append((record, value))

    rows = sorted(
        pairs.values(),
        key=lambda row: (row["distance"], not row["cross_split"], row["path_a"], row["path_b"]),
    )
    return rows[:limit]


def load_labels(labels_file: Path) -> list[str]:
    if not labels_file.exists():
        return list(CLASSES)
    labels = [line.strip() for line in labels_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    return labels or list(CLASSES)


def predict_tflite(model_path: Path, labels_file: Path, records: list[ImageRecord], root: Path) -> list[dict]:
    if not model_path.exists():
        return []

    try:
        import tensorflow as tf
    except ModuleNotFoundError:
        return []

    labels = load_labels(labels_file)
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    input_shape = input_details["shape"]
    height, width = int(input_shape[1]), int(input_shape[2])
    floating = input_details["dtype"] == np.float32

    rows = []
    for record in records:
        if record.split not in {"validation", "test"} or not record.readable:
            continue
        image_path = root.parent / record.path
        with Image.open(image_path) as img:
            img = img.convert("RGB").resize((width, height))
            data = np.asarray(img, dtype=np.float32 if floating else input_details["dtype"])
        # El modelo entrenado ya incluye mobilenet_v2.preprocess_input dentro
        # del grafo; dividir aqui por 255 cambia la distribucion esperada.
        data = np.expand_dims(data, axis=0)
        interpreter.set_tensor(input_details["index"], data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details["index"])[0]
        scores = np.asarray(output, dtype=np.float32)
        predicted_idx = int(np.argmax(scores))
        true_idx = labels.index(record.clase) if record.clase in labels else -1
        rows.append(
            {
                "split": record.split,
                "true_class": record.clase,
                "predicted_class": labels[predicted_idx] if predicted_idx < len(labels) else str(predicted_idx),
                "confidence": float(scores[predicted_idx]),
                "correct": predicted_idx == true_idx,
                "path": record.path,
            }
        )
    return rows


def make_attention_error_sheet(predictions: list[dict], output_path: Path, root: Path, max_items: int = 36) -> None:
    errors = [
        row for row in predictions
        if not row["correct"] and (row["true_class"] == "atencion" or row["predicted_class"] == "atencion")
    ]
    errors = sorted(errors, key=lambda row: -row["confidence"])[:max_items]
    if not errors:
        return

    thumb_w, thumb_h = 180, 150
    label_h = 44
    cols = 6
    rows = int(np.ceil(len(errors) / cols))
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, row in enumerate(errors):
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        image_path = root.parent / row["path"]
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((thumb_w, thumb_h))
            px = x + (thumb_w - img.width) // 2
            py = y + (thumb_h - img.height) // 2
            sheet.paste(img, (px, py))
        text = f"{row['split']} | {row['true_class']} -> {row['predicted_class']}\nconf={row['confidence']:.3f}"
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(245, 245, 245))
        draw.text((x + 4, y + thumb_h + 4), text, fill=(0, 0, 0), font=font)

    sheet.save(output_path, quality=92)


def write_markdown_report(
    output_path: Path,
    dataset_dir: Path,
    counts: dict[str, dict[str, int]],
    corrupt: list[ImageRecord],
    exact_duplicates: list[dict],
    perceptual_pairs: list[dict],
    predictions: list[dict],
    elapsed_seconds: float,
) -> None:
    total_images = sum(sum(classes.values()) for classes in counts.values())
    model_splits = {"train", "validation", "test"}
    exact_model_split_duplicates = [
        row for row in exact_duplicates
        if len(set(row["splits"].split("|")) & model_splits) > 1
    ]
    cross_split_similar = [row for row in perceptual_pairs if row["cross_split"]]
    cross_model_split_similar = [
        row for row in perceptual_pairs
        if row["split_a"] in model_splits and row["split_b"] in model_splits and row["split_a"] != row["split_b"]
    ]
    cross_class_similar = [row for row in perceptual_pairs if row["cross_class"]]
    attention_predictions = [row for row in predictions if row["true_class"] == "atencion"]
    attention_errors = [row for row in attention_predictions if not row["correct"]]
    class_metrics = []
    confusion = {true: {pred: 0 for pred in CLASSES} for true in CLASSES}
    for clase in CLASSES:
        rows = [row for row in predictions if row["true_class"] == clase]
        correct = [row for row in rows if row["correct"]]
        if rows:
            class_metrics.append((clase, len(rows), len(correct), len(correct) / len(rows) * 100))
        for row in rows:
            if row["predicted_class"] in confusion[clase]:
                confusion[clase][row["predicted_class"]] += 1

    lines = [
        "# Auditoria fase 1 del dataset IA local",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dataset: `{dataset_dir}`",
        f"Total de imagenes indexadas: `{total_images}`",
        f"Tiempo de auditoria: `{elapsed_seconds:.1f}` segundos",
        "",
        "## Conteo por split y clase",
        "",
        "| Split | atencion | peligro | sano | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in SPLITS:
        total = sum(counts[split].values())
        lines.append(
            f"| {split} | {counts[split]['atencion']} | {counts[split]['peligro']} | "
            f"{counts[split]['sano']} | {total} |"
        )

    lines.extend(
        [
            "",
            "## Hallazgos automaticos",
            "",
            f"- Imagenes corruptas o ilegibles: `{len(corrupt)}`.",
            f"- Grupos de duplicados exactos por SHA-256: `{len(exact_duplicates)}`.",
            f"- Grupos de duplicados exactos que cruzan `train/validation/test`: `{len(exact_model_split_duplicates)}`.",
            f"- Pares perceptualmente similares reportados: `{len(perceptual_pairs)}`.",
            f"- Pares perceptualmente similares entre splits: `{len(cross_split_similar)}`.",
            f"- Pares perceptualmente similares entre `train/validation/test`: `{len(cross_model_split_similar)}`.",
            f"- Pares perceptualmente similares entre clases: `{len(cross_class_similar)}`.",
        ]
    )

    if predictions:
        total_pred = len(predictions)
        ok_pred = sum(1 for row in predictions if row["correct"])
        lines.extend(
            [
                "",
                "## Muestra de errores del modelo actual",
                "",
                f"- Predicciones revisadas en validation/test: `{total_pred}`.",
                f"- Accuracy observado en esta corrida: `{ok_pred / total_pred * 100:.2f}%`.",
                f"- Imagenes reales `atencion` evaluadas: `{len(attention_predictions)}`.",
                f"- Errores donde la clase real era `atencion`: `{len(attention_errors)}`.",
                "- Grilla visual: `muestra_errores_atencion.jpg` si hubo errores aplicables.",
                "",
                "### Accuracy por clase",
                "",
                "| Clase real | Imagenes | Correctas | Accuracy |",
                "|---|---:|---:|---:|",
            ]
        )
        for clase, total, correct, accuracy in class_metrics:
            lines.append(f"| {clase} | {total} | {correct} | {accuracy:.2f}% |")
        lines.extend(
            [
                "",
                "### Matriz de confusion",
                "",
                "| Real \\ Predicha | atencion | peligro | sano |",
                "|---|---:|---:|---:|",
            ]
        )
        for clase in CLASSES:
            lines.append(
                f"| {clase} | {confusion[clase]['atencion']} | {confusion[clase]['peligro']} | {confusion[clase]['sano']} |"
            )
    else:
        lines.extend(
            [
                "",
                "## Muestra de errores del modelo actual",
                "",
                "- No se genero muestra de errores porque no se pudo cargar el modelo TFLite o TensorFlow.",
            ]
        )

    lines.extend(
        [
            "",
            "## Archivos generados",
            "",
            "- `records.csv`: inventario completo de imagenes auditadas.",
            "- `counts.json`: conteos por split y clase.",
            "- `corrupt_images.csv`: imagenes ilegibles o corruptas.",
            "- `exact_duplicates.csv`: grupos con bytes identicos.",
            "- `perceptual_similar_pairs.csv`: pares casi iguales detectados por pHash.",
            "- `predictions_validation_test.csv`: predicciones del modelo actual sobre validation/test.",
            "",
            "## Lectura inicial",
            "",
            "Esta auditoria inicia la fase 1 sin modificar el dataset. Los pasos manuales siguientes son revisar "
            "`perceptual_similar_pairs.csv` para decidir si hay fuga real entre train/validation/test y revisar "
            "visualmente `muestra_errores_atencion.jpg` para separar `atencion` leve, severo y casi sano antes "
            "de construir `dataset_curado`.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoria fase 1 del dataset del modelo IA local.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--phash-threshold", type=int, default=8)
    parser.add_argument("--phash-limit", type=int, default=5000)
    args = parser.parse_args()

    start = datetime.now()
    output_dir = args.output or DEFAULT_OUTPUT_BASE / f"auditoria_fase1_{start.strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset: {args.dataset}")
    print(f"Salida: {output_dir}")

    records = []
    for split, clase, path in iter_image_paths(args.dataset):
        records.append(audit_image(split, clase, path, args.dataset))
    print(f"Imagenes auditadas: {len(records)}")

    counts = count_by_split_class(records)
    corrupt = [record for record in records if not record.readable]
    exact_duplicates = find_exact_duplicates(records)
    perceptual_pairs = find_perceptual_pairs(records, args.phash_threshold, args.phash_limit)
    predictions = predict_tflite(args.model, args.labels, records, args.dataset)
    make_attention_error_sheet(predictions, output_dir / "muestra_errores_atencion.jpg", args.dataset)

    write_csv(output_dir / "records.csv", [asdict(record) for record in records], list(asdict(records[0]).keys()) if records else [])
    write_csv(output_dir / "corrupt_images.csv", [asdict(record) for record in corrupt], list(asdict(records[0]).keys()) if records else [])
    write_csv(
        output_dir / "exact_duplicates.csv",
        exact_duplicates,
        ["sha256", "count", "splits", "classes", "paths"],
    )
    write_csv(
        output_dir / "perceptual_similar_pairs.csv",
        perceptual_pairs,
        ["distance", "split_a", "class_a", "path_a", "split_b", "class_b", "path_b", "cross_split", "cross_class"],
    )
    write_csv(
        output_dir / "predictions_validation_test.csv",
        predictions,
        ["split", "true_class", "predicted_class", "confidence", "correct", "path"],
    )
    (output_dir / "counts.json").write_text(json.dumps(counts, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = (datetime.now() - start).total_seconds()
    write_markdown_report(
        output_dir / "REPORTE_AUDITORIA_FASE1.md",
        args.dataset,
        counts,
        corrupt,
        exact_duplicates,
        perceptual_pairs,
        predictions,
        elapsed,
    )

    print(f"Corruptas/ilegibles: {len(corrupt)}")
    print(f"Duplicados exactos: {len(exact_duplicates)}")
    print(f"Pares similares pHash: {len(perceptual_pairs)}")
    if predictions:
        correct = sum(1 for row in predictions if row["correct"])
        print(f"Predicciones validation/test: {len(predictions)} | accuracy={correct / len(predictions) * 100:.2f}%")
    print(f"Reporte: {output_dir / 'REPORTE_AUDITORIA_FASE1.md'}")


if __name__ == "__main__":
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
