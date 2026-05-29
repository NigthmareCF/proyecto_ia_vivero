#!/usr/bin/env python3
"""Evalua el checkpoint Keras generado para dataset_curado_v3."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow import keras


ROOT = Path(__file__).resolve().parents[1]
IMG_SIZE = (224, 224)
BATCH_SIZE = 16


def load_test_dataset(dataset_dir: Path):
    test_dir = dataset_dir / "test"
    test_ds = keras.utils.image_dataset_from_directory(
        test_dir,
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
        color_mode="rgb",
    )
    return test_ds.prefetch(tf.data.AUTOTUNE), test_ds.class_names


def collect_predictions(model: keras.Model, test_ds):
    y_true, y_pred, y_conf = [], [], []
    for images, labels in test_ds:
        probs = model.predict(images, verbose=0)
        pred = np.argmax(probs, axis=1)
        conf = np.max(probs, axis=1)
        y_true.extend(labels.numpy().tolist())
        y_pred.extend(pred.tolist())
        y_conf.extend(conf.tolist())
    return np.array(y_true), np.array(y_pred), np.array(y_conf)


def write_confusion_matrix(path: Path, matrix, class_names: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["real/predicha", *class_names])
        for idx, class_name in enumerate(class_names):
            writer.writerow([class_name, *matrix[idx].tolist()])


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua checkpoint Keras v3 visual.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset_curado_v3")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=ROOT
        / "training"
        / "fase4_entrenamiento_v3_visual"
        / "mobilenetv3small"
        / "mobilenetv3small.best.keras",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "training" / "fase4_entrenamiento_v3_visual" / "evaluacion_checkpoint",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    test_ds, class_names = load_test_dataset(args.dataset)
    model = keras.models.load_model(args.checkpoint)
    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    y_true, y_pred, y_conf = collect_predictions(model, test_ds)
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))

    metrics = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(args.dataset),
        "checkpoint": str(args.checkpoint),
        "test_loss": float(test_loss),
        "test_accuracy": float(test_acc),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "class_metrics": report,
        "confidence_mean": float(np.mean(y_conf)),
        "confidence_p25": float(np.percentile(y_conf, 25)),
        "confidence_p50": float(np.percentile(y_conf, 50)),
        "confidence_p75": float(np.percentile(y_conf, 75)),
    }
    (args.output_dir / "metrics_checkpoint_v3_visual.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    write_confusion_matrix(args.output_dir / "confusion_matrix_checkpoint_v3_visual.csv", matrix, class_names)

    lines = [
        "# Evaluacion checkpoint v3 visual",
        "",
        f"Fecha: {metrics['generated_at']}",
        f"Dataset: `{args.dataset}`",
        f"Checkpoint: `{args.checkpoint}`",
        "",
        "## Resultado",
        "",
        f"Accuracy test: `{test_acc * 100:.2f}%`",
        f"Macro F1: `{metrics['macro_f1']:.4f}`",
        "",
        "| Clase real | Recall | Precision | F1 |",
        "|---|---:|---:|---:|",
    ]
    for class_name in class_names:
        class_metrics = report[class_name]
        lines.append(
            f"| {class_name} | {class_metrics['recall'] * 100:.2f}% | "
            f"{class_metrics['precision'] * 100:.2f}% | {class_metrics['f1-score']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Este checkpoint no se exporto a TFLite por el fallo del entrenamiento original. "
            "No debe sustituir el modelo productivo sin una exportacion TFLite exitosa y sin pasar fase 5.",
            "",
        ]
    )
    report_path = args.output_dir / "REPORTE_CHECKPOINT_V3_VISUAL.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
