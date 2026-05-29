#!/usr/bin/env python3
"""Fase 4: entrenamiento comparativo sobre dataset_curado."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow import keras
from tensorflow.keras import layers


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_curado"
OUTPUT = ROOT / "training" / "fase4_entrenamiento_comparativo"
MODELS_DIR = ROOT / "modelos"
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
SEED = 42


def configure_runtime() -> None:
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    tf.keras.utils.set_random_seed(SEED)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass
    tf.config.threading.set_intra_op_parallelism_threads(0)
    tf.config.threading.set_inter_op_parallelism_threads(0)


def load_datasets(dataset_dir: Path):
    train_dir = dataset_dir / "train"
    val_dir = dataset_dir / "validation"
    test_dir = dataset_dir / "test"

    train_ds = keras.utils.image_dataset_from_directory(
        train_dir,
        seed=SEED,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        color_mode="rgb",
    )
    class_names = train_ds.class_names
    val_ds = keras.utils.image_dataset_from_directory(
        val_dir,
        seed=SEED,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
        color_mode="rgb",
    )
    test_ds = keras.utils.image_dataset_from_directory(
        test_dir,
        seed=SEED,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
        color_mode="rgb",
    )

    autotune = tf.data.AUTOTUNE
    return (
        train_ds.prefetch(autotune),
        val_ds.prefetch(autotune),
        test_ds.prefetch(autotune),
        class_names,
    )


def class_weights(dataset_dir: Path, class_names: list[str]) -> dict[int, float]:
    counts = {}
    for name in class_names:
        counts[name] = len([p for p in (dataset_dir / "train" / name).iterdir() if p.is_file()])
    total = sum(counts.values())
    return {idx: round(total / (len(class_names) * counts[name]), 4) for idx, name in enumerate(class_names)}


def base_model_for(name: str) -> keras.Model:
    if name == "mobilenetv2":
        return keras.applications.MobileNetV2(
            input_shape=IMG_SIZE + (3,),
            include_top=False,
            weights="imagenet",
        )
    if name == "mobilenetv3small":
        return keras.applications.MobileNetV3Small(
            input_shape=IMG_SIZE + (3,),
            include_top=False,
            weights="imagenet",
            include_preprocessing=False,
        )
    if name == "efficientnetv2b0":
        return keras.applications.EfficientNetV2B0(
            input_shape=IMG_SIZE + (3,),
            include_top=False,
            weights="imagenet",
            include_preprocessing=False,
        )
    raise ValueError(f"Modelo no soportado: {name}")


def preprocessing_layer(name: str):
    if name in {"mobilenetv2", "mobilenetv3small"}:
        return layers.Rescaling(1.0 / 127.5, offset=-1.0, name="rescale_mobilenet")
    if name == "efficientnetv2b0":
        return layers.Rescaling(1.0 / 255.0, name="rescale_efficientnet")
    raise ValueError(name)


def build_model(name: str, class_names: list[str]) -> tuple[keras.Model, keras.Model]:
    base = base_model_for(name)
    base.trainable = False

    augmentation = keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomZoom(0.10),
            layers.RandomContrast(0.12),
            layers.RandomBrightness(0.10),
            layers.RandomTranslation(0.04, 0.04),
        ],
        name="data_augmentation",
    )

    inputs = keras.Input(shape=IMG_SIZE + (3,), name="image")
    x = augmentation(inputs)
    x = preprocessing_layer(name)(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.35)(x)
    outputs = layers.Dense(len(class_names), activation="softmax", name="estado")(x)
    model = keras.Model(inputs, outputs, name=f"vivero_{name}")
    return model, base


def compile_model(model: keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )


def save_history_csv(path: Path, history_rows: list[dict]) -> None:
    if not history_rows:
        return
    fields = sorted({key for row in history_rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(history_rows)


def collect_predictions(model: keras.Model, test_ds) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y_true, y_pred, y_conf = [], [], []
    for images, labels in test_ds:
        probs = model.predict(images, verbose=0)
        pred = np.argmax(probs, axis=1)
        conf = np.max(probs, axis=1)
        y_true.extend(labels.numpy().tolist())
        y_pred.extend(pred.tolist())
        y_conf.extend(conf.tolist())
    return np.array(y_true), np.array(y_pred), np.array(y_conf)


def convert_to_tflite(model: keras.Model, output_path: Path) -> int:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()
    output_path.write_bytes(tflite_model)
    return output_path.stat().st_size


def evaluate_tflite_baseline(model_path: Path, dataset_dir: Path, test_ds, class_names: list[str]) -> dict | None:
    if not model_path.exists():
        return None
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    input_shape = input_details["shape"]
    height, width = int(input_shape[1]), int(input_shape[2])
    dtype = input_details["dtype"]

    y_true, y_pred, y_conf = [], [], []
    for class_idx, class_name in enumerate(class_names):
        for path in sorted((dataset_dir / "test" / class_name).iterdir()):
            if not path.is_file():
                continue
            img = keras.utils.load_img(path, target_size=(height, width))
            arr = keras.utils.img_to_array(img).astype(dtype)
            arr = np.expand_dims(arr, axis=0)
            interpreter.set_tensor(input_details["index"], arr)
            interpreter.invoke()
            scores = interpreter.get_tensor(output_details["index"])[0]
            scores = np.asarray(scores, dtype=np.float32)
            pred = int(np.argmax(scores))
            y_true.append(class_idx)
            y_pred.append(pred)
            y_conf.append(float(np.max(scores)))

    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    accuracy = float(np.mean(np.array(y_true) == np.array(y_pred)))
    return {
        "model": "baseline_modelo_vivero_tflite",
        "test_accuracy": accuracy,
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "class_metrics": report,
        "confidence_mean": float(np.mean(y_conf)) if y_conf else 0.0,
        "source_path": str(model_path),
        "promotable": False,
    }


def train_candidate(name: str, args, train_ds, val_ds, test_ds, class_names: list[str]) -> dict:
    candidate_dir = args.output_dir / name
    candidate_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    model, base = build_model(name, class_names)
    weights = class_weights(args.dataset, class_names)

    histories = []
    compile_model(model, args.lr_head)
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=args.patience, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.25, patience=max(1, args.patience // 2)),
        keras.callbacks.ModelCheckpoint(candidate_dir / f"{name}.best.keras", monitor="val_accuracy", save_best_only=True),
    ]
    h1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs_head,
        class_weight=weights,
        callbacks=callbacks,
        verbose=2,
    )
    for idx, row in enumerate(history_to_rows(h1, "head"), start=1):
        row["epoch"] = idx
        histories.append(row)

    if args.epochs_finetune > 0:
        base.trainable = True
        for layer in base.layers[: args.freeze_until]:
            layer.trainable = False
        compile_model(model, args.lr_finetune)
        h2 = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=args.epochs_finetune,
            class_weight=weights,
            callbacks=callbacks,
            verbose=2,
        )
        offset = len(histories)
        for idx, row in enumerate(history_to_rows(h2, "finetune"), start=1):
            row["epoch"] = offset + idx
            histories.append(row)

    save_history_csv(candidate_dir / "history.csv", histories)
    best_checkpoint = candidate_dir / f"{name}.best.keras"
    if best_checkpoint.exists():
        model = keras.models.load_model(best_checkpoint)
    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    y_true, y_pred, y_conf = collect_predictions(model, test_ds)

    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    matrix_path = candidate_dir / "confusion_matrix.csv"
    with matrix_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["real/predicha", *class_names])
        for idx, class_name in enumerate(class_names):
            writer.writerow([class_name, *matrix[idx].tolist()])

    keras_path = candidate_dir / f"{name}.keras"
    tflite_path = candidate_dir / f"{name}.tflite"
    model.save(keras_path)
    tflite_size = convert_to_tflite(model, tflite_path)

    metrics = {
        "model": name,
        "test_loss": float(test_loss),
        "test_accuracy": float(test_acc),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "class_metrics": report,
        "confidence_mean": float(np.mean(y_conf)),
        "confidence_p25": float(np.percentile(y_conf, 25)),
        "confidence_p50": float(np.percentile(y_conf, 50)),
        "confidence_p75": float(np.percentile(y_conf, 75)),
        "keras_path": str(keras_path),
        "tflite_path": str(tflite_path),
        "tflite_size_bytes": int(tflite_size),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "promotable": True,
    }
    (candidate_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def history_to_rows(history: keras.callbacks.History, stage: str) -> list[dict]:
    rows = []
    keys = list(history.history.keys())
    for idx in range(len(history.history[keys[0]])):
        row = {"stage": stage}
        for key in keys:
            row[key] = history.history[key][idx]
        rows.append(row)
    return rows


def write_summary(output_dir: Path, metrics_list: list[dict], class_names: list[str]) -> None:
    trained = [item for item in metrics_list if item.get("promotable")]
    best_trained = max(trained, key=lambda item: (item["test_accuracy"], item["macro_f1"]))
    best_overall = max(metrics_list, key=lambda item: (item["test_accuracy"], item["macro_f1"]))
    accepted = best_overall.get("promotable", False)
    (output_dir / "metrics_modelo_v2.json").write_text(
        json.dumps(
            {
                "best_trained_model": best_trained,
                "best_overall_model": best_overall,
                "accepted_as_replacement": accepted,
                "candidates": metrics_list,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    best_dir = Path(best_trained["keras_path"]).parent
    shutil.copy2(best_trained["keras_path"], MODELS_DIR / "modelo_vivero_v2.keras")
    shutil.copy2(best_trained["tflite_path"], MODELS_DIR / "modelo_vivero_v2.tflite")
    (MODELS_DIR / "labels.txt").write_text("\n".join(class_names) + "\n", encoding="utf-8")
    shutil.copy2(best_dir / "confusion_matrix.csv", output_dir / "confusion_matrix_modelo_v2.csv")

    lines = [
        "# Fase 4: entrenamiento comparativo modelo IA local",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dataset: `{DATASET}`",
        "",
        "## Resultado",
        "",
        f"Mejor candidato entrenado: `{best_trained['model']}`",
        f"Accuracy test candidato: `{best_trained['test_accuracy'] * 100:.2f}%`",
        f"Macro F1 candidato: `{best_trained['macro_f1']:.4f}`",
        f"Mejor resultado general medido: `{best_overall['model']}` con `{best_overall['test_accuracy'] * 100:.2f}%`.",
        f"Aceptado como reemplazo del modelo actual: `{'si' if accepted else 'no'}`.",
        f"TFLite candidato: `{best_trained['tflite_path']}`",
        "",
        "## Comparacion",
        "",
        "| Modelo | Accuracy test | Macro F1 | atencion | peligro | sano |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metrics in sorted(metrics_list, key=lambda item: item["test_accuracy"], reverse=True):
        class_metrics = metrics["class_metrics"]
        lines.append(
            f"| {metrics['model']} | {metrics['test_accuracy'] * 100:.2f}% | {metrics['macro_f1']:.4f} | "
            f"{class_metrics['atencion']['recall'] * 100:.2f}% | "
            f"{class_metrics['peligro']['recall'] * 100:.2f}% | "
            f"{class_metrics['sano']['recall'] * 100:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Archivos generados",
            "",
            "- `modelos/modelo_vivero_v2.keras`",
            "- `modelos/modelo_vivero_v2.tflite`",
            "- `modelos/labels.txt`",
            "- `training/fase4_entrenamiento_comparativo/metrics_modelo_v2.json`",
            "- `training/fase4_entrenamiento_comparativo/confusion_matrix_modelo_v2.csv`",
            "",
            "## Decision",
            "",
            "El candidato se exporta como `modelo_vivero_v2`, pero no debe integrarse al backend si "
            "`accepted_as_replacement` es `false` en `metrics_modelo_v2.json`.",
            "",
        ]
    )
    (output_dir / "reporte_modelo_v2.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena candidatos fase 4 sobre dataset_curado.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--models", default="mobilenetv2", help="Lista separada por coma: mobilenetv2,mobilenetv3small,efficientnetv2b0")
    parser.add_argument("--epochs-head", type=int, default=10)
    parser.add_argument("--epochs-finetune", type=int, default=8)
    parser.add_argument("--freeze-until", type=int, default=80)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--lr-finetune", type=float, default=1e-5)
    args = parser.parse_args()

    configure_runtime()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    train_ds, val_ds, test_ds, class_names = load_datasets(args.dataset)
    (args.output_dir / "labels.txt").write_text("\n".join(class_names) + "\n", encoding="utf-8")

    metrics_list = []
    errors = []
    baseline = evaluate_tflite_baseline(MODELS_DIR / "modelo_vivero.tflite", args.dataset, test_ds, class_names)
    if baseline:
        metrics_list.append(baseline)
    for name in [item.strip().lower() for item in args.models.split(",") if item.strip()]:
        try:
            print(f"\n=== Entrenando {name} ===")
            metrics_list.append(train_candidate(name, args, train_ds, val_ds, test_ds, class_names))
        except Exception as exc:
            errors.append({"model": name, "error": f"{type(exc).__name__}: {exc}"})
            print(f"ERROR en {name}: {errors[-1]['error']}")

    if errors:
        (args.output_dir / "errores_modelos.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
    if not metrics_list:
        raise SystemExit("No se entreno ningun modelo correctamente.")

    write_summary(args.output_dir, metrics_list, class_names)
    print((args.output_dir / "reporte_modelo_v2.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
