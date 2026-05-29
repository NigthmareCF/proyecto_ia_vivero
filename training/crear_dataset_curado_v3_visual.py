#!/usr/bin/env python3
"""Crea dataset_curado_v3 con recuperacion visual de atencion."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "dataset_curado"
OUTPUT = ROOT / "dataset_curado_v3"
SELECTION = ROOT / "training" / "revision_visual_atencion" / "seleccion_atencion_visual.csv"
VISUAL_DIR = ROOT / "training" / "revision_visual_atencion"
MANIFEST_REVISION = BASE / "revision_dudosa" / "manifest_revision_dudosa.csv"
CLASSES = ("atencion", "peligro", "sano")
SPLITS = ("train", "validation", "test")
RATIOS = {"train": 0.70, "validation": 0.20, "test": 0.10}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def code_to_source() -> dict[str, dict[str, str]]:
    mapping = {}
    for csv_path in sorted(VISUAL_DIR.glob("atencion_conflicto_lote_*.csv")):
        for row in read_csv(csv_path):
            mapping[row["code"]] = row
    return mapping


def split_plan(total: int) -> dict[str, int]:
    train = int(total * RATIOS["train"])
    validation = int(total * RATIOS["validation"])
    return {"train": train, "validation": validation, "test": total - train - validation}


def copy_selected_atencion(output_dir: Path) -> list[dict]:
    source_by_code = code_to_source()
    selected = [row for row in read_csv(SELECTION) if row["decision"] == "keep_atencion"]
    plan = split_plan(len(selected))
    recovered = []
    offset = 0
    for split in SPLITS:
        batch = selected[offset:offset + plan[split]]
        offset += plan[split]
        for row in batch:
            src_info = source_by_code[row["code"]]
            src = ROOT / src_info["path"]
            dst = output_dir / split / "atencion" / f"visual_{src.name}"
            shutil.copy2(src, dst)
            recovered.append(
                {
                    "split": split,
                    "target_class": "atencion",
                    "source_path": src_info["path"],
                    "dest_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                    "decision": row["decision"],
                    "notes": row["notes"],
                    "review_code": row["code"],
                }
            )
    return recovered


def list_images(output_dir: Path, split: str, clase: str) -> list[Path]:
    return sorted((output_dir / split / clase).iterdir())


def count_dataset(output_dir: Path) -> dict[str, dict[str, int]]:
    return {split: {clase: len(list_images(output_dir, split, clase)) for clase in CLASSES} for split in SPLITS}


def balance_peligro_sano(output_dir: Path, recovered: list[dict]) -> None:
    counts = count_dataset(output_dir)
    target_total = sum(counts[split]["atencion"] for split in SPLITS)
    current_total = {clase: sum(counts[split][clase] for split in SPLITS) for clase in CLASSES}
    revision_rows = read_csv(MANIFEST_REVISION)
    extras = defaultdict(list)
    for row in revision_rows:
        if row["reason"] == "excedente por balance de clases" and row["original_class"] in {"peligro", "sano"}:
            extras[row["original_class"]].append(row["path"])

    for clase in ("peligro", "sano"):
        need = max(0, target_total - current_total[clase])
        plan = split_plan(need)
        offset = 0
        for split in SPLITS:
            for source in extras[clase][offset:offset + plan[split]]:
                src = ROOT / source
                dst = output_dir / split / clase / f"visual_balance_{src.name}"
                shutil.copy2(src, dst)
                recovered.append(
                    {
                        "split": split,
                        "target_class": clase,
                        "source_path": source,
                        "dest_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                        "decision": "balance_extra",
                        "notes": "excedente usado para mantener balance con atencion recuperada",
                        "review_code": "",
                    }
                )
            offset += plan[split]


def write_report(output_dir: Path, recovered: list[dict]) -> None:
    counts = count_dataset(output_dir)
    lines = [
        "# Dataset curado v3 con revision visual",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Base: `{BASE}`",
        f"Salida: `{output_dir}`",
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
            f"- Imagenes agregadas totales: `{len(recovered)}`.",
            f"- Imagenes `atencion` recuperadas visualmente: `{sum(1 for row in recovered if row['target_class'] == 'atencion')}`.",
            "",
            "## Advertencia",
            "",
            "Este dataset usa revision visual asistida. Debe validarse con auditoria y entrenamiento antes de cualquier integracion.",
            "",
        ]
    )
    (output_dir / "REPORTE_DATASET_CURADO_V3_VISUAL.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_dataset": str(BASE),
        "output_dataset": str(output_dir),
        "counts": counts,
        "recovered_total": len(recovered),
        "recovered_atencion": sum(1 for row in recovered if row["target_class"] == "atencion"),
    }
    (output_dir / "MANIFEST_DATASET_CURADO_V3.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea dataset_curado_v3 con seleccion visual de atencion.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists() and not args.force:
        raise SystemExit(f"Ya existe {args.output_dir}; usa --force.")
    copy_tree(BASE, args.output_dir)
    recovered = copy_selected_atencion(args.output_dir)
    balance_peligro_sano(args.output_dir, recovered)
    write_csv(
        args.output_dir / "manifest_recuperacion_visual.csv",
        recovered,
        ["split", "target_class", "source_path", "dest_path", "decision", "notes", "review_code"],
    )
    write_report(args.output_dir, recovered)
    print((args.output_dir / "REPORTE_DATASET_CURADO_V3_VISUAL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
