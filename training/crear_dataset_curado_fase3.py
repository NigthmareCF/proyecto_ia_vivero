#!/usr/bin/env python3
"""Crea dataset_curado para la fase 3 sin modificar dataset original."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "training" / "auditoria_fase1_20260528_043608"
DEFAULT_OUTPUT = ROOT / "dataset_curado"
CLASSES = ("atencion", "peligro", "sano")
SPLITS = ("train", "validation", "test")
RATIOS = {"train": 0.70, "validation": 0.20, "test": 0.10}


@dataclass(frozen=True)
class Record:
    split: str
    clase: str
    path: str
    name: str
    sha256: str
    phash: str
    readable: bool


def load_all_record_rows(audit_dir: Path) -> list[dict[str, str]]:
    return read_csv(audit_dir / "records.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_raw_records(audit_dir: Path) -> list[Record]:
    rows = read_csv(audit_dir / "records.csv")
    records: list[Record] = []
    for row in rows:
        if row["split"] != "raw":
            continue
        records.append(
            Record(
                split=row["split"],
                clase=row["clase"],
                path=row["path"],
                name=row["name"],
                sha256=row["sha256"],
                phash=row["phash"],
                readable=row["readable"] == "True",
            )
        )
    return records


def build_exact_conflict_sets(records: list[Record]) -> tuple[set[str], dict[str, set[str]]]:
    by_sha: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        if record.sha256:
            by_sha[record.sha256].append(record)

    conflict_paths: set[str] = set()
    conflict_classes: dict[str, set[str]] = {}
    for sha, items in by_sha.items():
        classes = {item.clase for item in items}
        if len(classes) > 1:
            conflict_classes[sha] = classes
            for item in items:
                conflict_paths.add(item.path)
    return conflict_paths, conflict_classes


def build_perceptual_conflict_shas(audit_dir: Path) -> set[str]:
    all_rows = load_all_record_rows(audit_dir)
    path_to_sha = {row["path"]: row["sha256"] for row in all_rows if row.get("sha256")}
    conflict_shas: set[str] = set()
    for row in read_csv(audit_dir / "perceptual_similar_pairs.csv"):
        if row["cross_class"] != "True":
            continue
        for key in ("path_a", "path_b"):
            sha = path_to_sha.get(row[key])
            if sha:
                conflict_shas.add(sha)
    return conflict_shas


def select_unique_records(
    records: list[Record],
    conflict_paths: set[str],
    perceptual_conflict_shas: set[str],
) -> tuple[dict[str, list[Record]], list[dict]]:
    selected_by_class: dict[str, list[Record]] = {clase: [] for clase in CLASSES}
    review_rows: list[dict] = []
    seen_sha_by_class: dict[str, set[str]] = {clase: set() for clase in CLASSES}

    for record in sorted(records, key=lambda item: (item.clase, item.sha256, item.path)):
        if not record.readable:
            review_rows.append(review_row(record, "excluir_baja_calidad", "imagen no legible segun auditoria"))
            continue
        if record.path in conflict_paths:
            review_rows.append(review_row(record, "revision_dudosa", "duplicado exacto con etiqueta conflictiva"))
            continue
        if record.sha256 in perceptual_conflict_shas:
            review_rows.append(review_row(record, "revision_dudosa", "similaridad perceptual con etiqueta conflictiva"))
            continue
        if record.sha256 in seen_sha_by_class[record.clase]:
            review_rows.append(review_row(record, "excluir_duplicado", "duplicado exacto dentro de la misma clase"))
            continue
        seen_sha_by_class[record.clase].add(record.sha256)
        selected_by_class[record.clase].append(record)

    return selected_by_class, review_rows


def review_row(record: Record, decision: str, reason: str) -> dict:
    return {
        "decision": decision,
        "reason": reason,
        "original_class": record.clase,
        "path": record.path,
        "sha256": record.sha256,
        "phash": record.phash,
    }


def balanced_split(selected_by_class: dict[str, list[Record]]) -> tuple[dict[str, dict[str, list[Record]]], list[dict]]:
    min_count = min(len(selected_by_class[clase]) for clase in CLASSES)
    splits: dict[str, dict[str, list[Record]]] = {split: {clase: [] for clase in CLASSES} for split in SPLITS}
    review_rows: list[dict] = []

    n_train = int(min_count * RATIOS["train"])
    n_val = int(min_count * RATIOS["validation"])
    n_test = min_count - n_train - n_val

    for clase in CLASSES:
        usable = sorted(selected_by_class[clase], key=lambda item: (item.sha256, item.path))
        chosen = usable[:min_count]
        extra = usable[min_count:]

        splits["train"][clase] = chosen[:n_train]
        splits["validation"][clase] = chosen[n_train:n_train + n_val]
        splits["test"][clase] = chosen[n_train + n_val:n_train + n_val + n_test]

        for record in extra:
            review_rows.append(review_row(record, "revision_dudosa", "excedente por balance de clases"))

    return splits, review_rows


def ensure_layout(output_dir: Path) -> None:
    for split in SPLITS:
        for clase in CLASSES:
            (output_dir / split / clase).mkdir(parents=True, exist_ok=True)
    for reason in ("conflicto_etiqueta", "duplicado", "baja_calidad", "excedente_balance"):
        for clase in CLASSES:
            (output_dir / "revision_dudosa" / reason / clase).mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dataset(root: Path, output_dir: Path, splits: dict[str, dict[str, list[Record]]], review_rows: list[dict]) -> None:
    for split, classes in splits.items():
        for clase, records in classes.items():
            for record in records:
                src = root / record.path
                dst = output_dir / split / clase / Path(record.path).name
                copy_file(src, dst)

    reason_dirs = {
        "duplicado exacto con etiqueta conflictiva": "conflicto_etiqueta",
        "similaridad perceptual con etiqueta conflictiva": "conflicto_etiqueta",
        "duplicado exacto dentro de la misma clase": "duplicado",
        "imagen no legible segun auditoria": "baja_calidad",
        "excedente por balance de clases": "excedente_balance",
    }
    for row in review_rows:
        src = root / row["path"]
        if not src.exists():
            continue
        reason_dir = reason_dirs.get(row["reason"], "conflicto_etiqueta")
        dst = output_dir / "revision_dudosa" / reason_dir / row["original_class"] / Path(row["path"]).name
        copy_file(src, dst)


def write_report(
    output_dir: Path,
    selected_by_class: dict[str, list[Record]],
    splits: dict[str, dict[str, list[Record]]],
    review_rows: list[dict],
    audit_dir: Path,
) -> None:
    split_counts = {
        split: {clase: len(splits[split][clase]) for clase in CLASSES}
        for split in SPLITS
    }
    review_counts = Counter(row["reason"] for row in review_rows)
    selected_counts = {clase: len(selected_by_class[clase]) for clase in CLASSES}
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_dir": str(audit_dir),
        "output_dir": str(output_dir),
        "selected_before_balance": selected_counts,
        "split_counts": split_counts,
        "review_counts": dict(review_counts),
        "total_curated": sum(sum(classes.values()) for classes in split_counts.values()),
        "total_review": len(review_rows),
    }
    (output_dir / "MANIFEST_FASE3.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Fase 3: dataset curado",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Auditoria base: `{audit_dir}`",
        f"Salida: `{output_dir}`",
        "",
        "## Resultado",
        "",
        f"- Total en `train/validation/test`: `{summary['total_curated']}` imagenes.",
        f"- Total enviado a `revision_dudosa`: `{summary['total_review']}` imagenes.",
        "- El dataset original no fue modificado.",
        "",
        "## Conteo curado",
        "",
        "| Split | atencion | peligro | sano | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in SPLITS:
        total = sum(split_counts[split].values())
        lines.append(
            f"| {split} | {split_counts[split]['atencion']} | {split_counts[split]['peligro']} | "
            f"{split_counts[split]['sano']} | {total} |"
        )

    lines.extend(
        [
            "",
            "## Revision dudosa",
            "",
            "| Motivo | Imagenes |",
            "|---|---:|",
        ]
    )
    for reason, count in sorted(review_counts.items()):
        lines.append(f"| {reason} | {count} |")

    lines.extend(
        [
            "",
            "## Criterio aplicado",
            "",
            "- Se copio desde `dataset/raw`, no desde los splits anteriores.",
            "- Se excluyeron de entrenamiento imagenes con duplicado exacto entre etiquetas distintas.",
            "- Se excluyeron de entrenamiento imagenes con similitud perceptual contra otra clase.",
            "- Se elimino duplicado exacto dentro de una misma clase conservando una copia canonica.",
            "- Se balancearon las tres clases al tamano de la clase usable mas pequena.",
            "- Los excedentes por balance quedaron en `revision_dudosa/excedente_balance` para no perder trazabilidad.",
            "",
            "## Siguiente paso",
            "",
            "La fase 4 debe entrenar contra `dataset_curado` y comparar el resultado con el modelo actual.",
            "",
        ]
    )
    (output_dir / "REPORTE_FASE3_DATASET_CURADO.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea dataset_curado balanceado y no destructivo.")
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="Recrear output-dir si ya existe.")
    args = parser.parse_args()

    if args.output_dir.exists():
        if not args.force:
            raise SystemExit(f"Ya existe {args.output_dir}. Usa --force para recrearlo.")
        shutil.rmtree(args.output_dir)

    ensure_layout(args.output_dir)
    records = load_raw_records(args.audit_dir)
    conflict_paths, _ = build_exact_conflict_sets(records)
    perceptual_conflict_shas = build_perceptual_conflict_shas(args.audit_dir)
    selected_by_class, review_rows = select_unique_records(records, conflict_paths, perceptual_conflict_shas)
    splits, balance_review_rows = balanced_split(selected_by_class)
    review_rows.extend(balance_review_rows)

    copy_dataset(ROOT, args.output_dir, splits, review_rows)
    write_csv(
        args.output_dir / "revision_dudosa" / "manifest_revision_dudosa.csv",
        review_rows,
        ["decision", "reason", "original_class", "path", "sha256", "phash"],
    )
    write_report(args.output_dir, selected_by_class, splits, review_rows, args.audit_dir)

    print(f"Dataset curado: {args.output_dir}")
    print((args.output_dir / "MANIFEST_FASE3.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
