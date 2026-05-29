#!/usr/bin/env python3
"""Recupera ejemplos de revision_dudosa para crear un dataset curado v2.

La recuperacion es conservadora: usa el modelo baseline solo para proponer
ejemplos adicionales de atencion cuando la confianza es alta. El objetivo es
subir la cantidad de ejemplos de atencion sin contaminar con conflictos obvios.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATASET_CURADO = ROOT / "dataset_curado"
OUTPUT = ROOT / "dataset_curado_v2"
MODEL = ROOT / "modelos" / "modelo_vivero.tflite"
LABELS = ROOT / "labels.txt"
MANIFEST = DATASET_CURADO / "revision_dudosa" / "manifest_revision_dudosa.csv"
CLASSES = ("atencion", "peligro", "sano")
SPLITS = ("train", "validation", "test")
RATIOS = {"train": 0.70, "validation": 0.20, "test": 0.10}


@dataclass(frozen=True)
class Candidate:
    original_class: str
    path: str
    reason: str
    predicted_class: str
    confidence: float


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def labels() -> list[str]:
    return [line.strip() for line in LABELS.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_interpreter():
    interpreter = tf.lite.Interpreter(model_path=str(MODEL))
    interpreter.allocate_tensors()
    return interpreter, interpreter.get_input_details()[0], interpreter.get_output_details()[0], labels()


def predict(path: Path, interpreter, input_details, output_details, label_names: list[str]) -> tuple[str, float]:
    shape = input_details["shape"]
    height, width = int(shape[1]), int(shape[2])
    dtype = input_details["dtype"]
    with Image.open(path) as img:
        img = img.convert("RGB").resize((width, height))
        arr = np.asarray(img, dtype=dtype)
    arr = np.expand_dims(arr, axis=0)
    interpreter.set_tensor(input_details["index"], arr)
    interpreter.invoke()
    scores = np.asarray(interpreter.get_tensor(output_details["index"])[0], dtype=np.float32)
    idx = int(np.argmax(scores))
    return label_names[idx], float(scores[idx])


def collect_recovery_candidates(confidence: float) -> list[Candidate]:
    interpreter, input_details, output_details, label_names = load_interpreter()
    rows = read_csv(MANIFEST)
    candidates: list[Candidate] = []
    for row in rows:
        if row["original_class"] != "atencion":
            continue
        if row["reason"] not in {
            "similaridad perceptual con etiqueta conflictiva",
            "duplicado exacto con etiqueta conflictiva",
        }:
            continue
        image_path = ROOT / row["path"]
        if not image_path.exists():
            continue
        predicted, conf = predict(image_path, interpreter, input_details, output_details, label_names)
        if predicted == "atencion" and conf >= confidence:
            candidates.append(Candidate(row["original_class"], row["path"], row["reason"], predicted, conf))
    return sorted(candidates, key=lambda item: (-item.confidence, item.path))


def list_images(split: str, clase: str, dataset_dir: Path = DATASET_CURADO) -> list[Path]:
    return sorted((dataset_dir / split / clase).iterdir())


def copy_base_dataset(output_dir: Path) -> None:
    for split in SPLITS:
        for clase in CLASSES:
            dst = output_dir / split / clase
            dst.mkdir(parents=True, exist_ok=True)
            for src in list_images(split, clase):
                shutil.copy2(src, dst / src.name)


def copy_recovered_atencion(candidates: list[Candidate], output_dir: Path, max_add: int) -> list[dict]:
    added = []
    split_counts = {
        "train": int(max_add * RATIOS["train"]),
        "validation": int(max_add * RATIOS["validation"]),
    }
    split_counts["test"] = max_add - split_counts["train"] - split_counts["validation"]
    offset = 0
    for split in SPLITS:
        for candidate in candidates[offset:offset + split_counts[split]]:
            src = ROOT / candidate.path
            name = f"recuperada_{src.name}"
            dst = output_dir / split / "atencion" / name
            shutil.copy2(src, dst)
            added.append(
                {
                    "split": split,
                    "target_class": "atencion",
                    "source_path": candidate.path,
                    "dest_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                    "reason": candidate.reason,
                    "predicted_class": candidate.predicted_class,
                    "confidence": f"{candidate.confidence:.6f}",
                }
            )
        offset += split_counts[split]
    return added


def rebalance_extra_classes(output_dir: Path) -> list[dict]:
    counts = {clase: len(list_images("train", clase, output_dir)) + len(list_images("validation", clase, output_dir)) + len(list_images("test", clase, output_dir)) for clase in CLASSES}
    target = counts["atencion"]
    added = []
    manifest_rows = read_csv(MANIFEST)
    by_class = defaultdict(list)
    for row in manifest_rows:
        if row["reason"] != "excedente por balance de clases":
            continue
        if row["original_class"] in {"peligro", "sano"}:
            by_class[row["original_class"]].append(row["path"])

    for clase in ("peligro", "sano"):
        need = max(0, target - counts[clase])
        split_counts = {"train": int(need * RATIOS["train"]), "validation": int(need * RATIOS["validation"])}
        split_counts["test"] = need - split_counts["train"] - split_counts["validation"]
        offset = 0
        for split in SPLITS:
            for source in by_class[clase][offset:offset + split_counts[split]]:
                src = ROOT / source
                if not src.exists():
                    continue
                dst = output_dir / split / clase / f"recuperada_{src.name}"
                shutil.copy2(src, dst)
                added.append(
                    {
                        "split": split,
                        "target_class": clase,
                        "source_path": source,
                        "dest_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                        "reason": "excedente por balance recuperado para mantener balance",
                        "predicted_class": "",
                        "confidence": "",
                    }
                )
            offset += split_counts[split]
    return added


def count_dataset(output_dir: Path) -> dict[str, dict[str, int]]:
    return {
        split: {clase: len(list_images(split, clase, output_dir)) for clase in CLASSES}
        for split in SPLITS
    }


def write_report(output_dir: Path, candidates: list[Candidate], recovered: list[dict], counts: dict) -> None:
    reason_counts = Counter(row["reason"] for row in recovered)
    lines = [
        "# Recuperacion conservadora de revision_dudosa",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Salida: `{output_dir}`",
        "",
        "## Criterio",
        "",
        "- Se uso el baseline `modelos/modelo_vivero.tflite` como filtro.",
        "- Solo se recuperaron candidatos `atencion` si el baseline predijo `atencion` con confianza alta.",
        "- Se recuperaron excedentes de `peligro` y `sano` solo para mantener balance.",
        "- No se modifico `dataset_curado` original.",
        "",
        "## Conteo",
        "",
        "| Split | atencion | peligro | sano | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in SPLITS:
        total = sum(counts[split].values())
        lines.append(f"| {split} | {counts[split]['atencion']} | {counts[split]['peligro']} | {counts[split]['sano']} | {total} |")
    lines.extend(
        [
            "",
            "## Recuperacion",
            "",
            f"- Candidatos `atencion` de alta confianza encontrados: `{len(candidates)}`.",
            f"- Imagenes recuperadas totales: `{len(recovered)}`.",
            "",
            "| Motivo | Imagenes |",
            "|---|---:|",
        ]
    )
    for reason, count in sorted(reason_counts.items()):
        lines.append(f"| {reason} | {count} |")
    lines.extend(
        [
            "",
            "## Advertencia",
            "",
            "Este dataset v2 sigue necesitando validacion con entrenamiento. Recuperar ejemplos por confianza "
            "mejora cobertura de `atencion`, pero no demuestra por si solo que el modelo vaya a superar el minimo.",
            "",
        ]
    )
    (output_dir / "REPORTE_RECUPERACION_REVISION_DUDOSA.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea dataset_curado_v2 recuperando atencion dudosa de alta confianza.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--confidence", type=float, default=0.80)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output_dir.exists():
        if not args.force:
            raise SystemExit(f"Ya existe {args.output_dir}; usa --force.")
        shutil.rmtree(args.output_dir)

    candidates = collect_recovery_candidates(args.confidence)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    copy_base_dataset(args.output_dir)
    recovered = copy_recovered_atencion(candidates, args.output_dir, len(candidates))
    recovered.extend(rebalance_extra_classes(args.output_dir))

    counts = count_dataset(args.output_dir)
    write_csv(
        args.output_dir / "manifest_recuperacion_revision_dudosa.csv",
        recovered,
        ["split", "target_class", "source_path", "dest_path", "reason", "predicted_class", "confidence"],
    )
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_dataset": str(DATASET_CURADO),
        "output_dataset": str(args.output_dir),
        "confidence_threshold": args.confidence,
        "attention_candidates": len(candidates),
        "recovered_total": len(recovered),
        "counts": counts,
    }
    (args.output_dir / "MANIFEST_DATASET_CURADO_V2.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_report(args.output_dir, candidates, recovered, counts)
    print((args.output_dir / "REPORTE_RECUPERACION_REVISION_DUDOSA.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
