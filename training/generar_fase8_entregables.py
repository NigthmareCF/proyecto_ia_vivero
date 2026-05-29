#!/usr/bin/env python3
"""Fase 8: inventario final de entregables del plan de IA local."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "training" / "fase8_entregables"


EXPECTED = [
    "modelos/modelo_vivero_v2.keras",
    "modelos/modelo_vivero_v2.tflite",
    "modelos/labels.txt",
    "training/reporte_modelo_v2.md",
    "training/metrics_modelo_v2.json",
    "training/confusion_matrix_modelo_v2.csv",
    "dataset_curado",
]

PHASE_ARTIFACTS = [
    "training/auditoria_fase1_20260528_043608/REPORTE_AUDITORIA_FASE1.md",
    "training/fase2_reglas_etiquetado/REGLAS_ETIQUETADO_FASE2.md",
    "dataset_curado/REPORTE_FASE3_DATASET_CURADO.md",
    "training/reporte_modelo_v2.md",
    "training/fase5_criterio_aceptacion/REPORTE_CRITERIO_ACEPTACION_FASE5.md",
    "training/fase6_decision_confianza/REPORTE_DECISION_CONFIANZA_FASE6.md",
    "training/fase7_flujo_gemini/REPORTE_FLUJO_GEMINI_FASE7.md",
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_path(relative: str) -> dict:
    path = ROOT / relative
    exists = path.exists()
    if path.is_dir():
        file_count = sum(1 for item in path.rglob("*") if item.is_file())
        size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        kind = "directory"
    elif path.is_file():
        file_count = 1
        size = path.stat().st_size
        kind = "file"
    else:
        file_count = 0
        size = 0
        kind = "missing"
    return {
        "path": relative,
        "exists": exists,
        "kind": kind,
        "size_bytes": size,
        "file_count": file_count,
        "sha256": sha256(path),
    }


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_report(path: Path, manifest: dict) -> None:
    metrics = manifest["model_decision"]
    phase5 = manifest["phase5_decision"]
    dataset = manifest["dataset_curado"]
    lines = [
        "# Fase 8: entregables finales del plan IA local",
        "",
        f"Fecha: {manifest['generated_at']}",
        "",
        "## Estado final",
        "",
        f"- Dataset curado: `{dataset['total_curated']}` imagenes en train/validation/test.",
        f"- Imagenes en revision/dudosas: `{dataset['total_review']}`.",
        f"- Mejor modelo medido: `{metrics['best_overall_model']['model']}` con `{metrics['best_overall_model']['test_accuracy'] * 100:.2f}%`.",
        f"- Mejor candidato entrenado: `{metrics['best_trained_model']['model']}` con `{metrics['best_trained_model']['test_accuracy'] * 100:.2f}%`.",
        f"- `modelo_vivero_v2` aceptado como reemplazo: `{'si' if metrics['accepted_as_replacement'] else 'no'}`.",
        f"- Aprobado para diagnostico final: `{'si' if phase5['decision']['approved_for_final_diagnosis'] else 'no'}`.",
        "",
        "## Entregables esperados",
        "",
        "| Ruta | Existe | Tipo | Archivos | Tamano bytes |",
        "|---|---|---|---:|---:|",
    ]
    for item in manifest["expected_deliverables"]:
        lines.append(
            f"| `{item['path']}` | {'si' if item['exists'] else 'no'} | {item['kind']} | "
            f"{item['file_count']} | {item['size_bytes']} |"
        )

    lines.extend(
        [
            "",
            "## Reportes por fase",
            "",
        ]
    )
    for item in manifest["phase_reports"]:
        lines.append(f"- `{item['path']}`")

    lines.extend(
        [
            "",
            "## Decision de integracion",
            "",
            "No integrar `modelos/modelo_vivero_v2.tflite` al backend como reemplazo del modelo actual. "
            "El archivo existe como candidato entrenado y evidencia de fase 4, pero no supero el baseline ni el "
            "criterio minimo de fase 5.",
            "",
            "El uso correcto del modelo local por ahora es filtro rapido por grupo, con escalamiento a Gemini o "
            "revision manual segun fase 6 y fase 7.",
            "",
            "## Pendientes tecnicos",
            "",
            "- Revisar manualmente `dataset_curado/revision_dudosa` para recuperar ejemplos utiles.",
            "- Conseguir mas datos reales de `atencion` con sintomas claros y balanceados.",
            "- Reentrenar con mas datos o estrategia especifica para `atencion` antes de intentar reemplazo.",
            "- Implementar en backend solo despues un flujo por grupo `POST /api/analisis/grupo` si se decide avanzar.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera manifiesto fase 8.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expected_deliverables": [describe_path(path) for path in EXPECTED],
        "phase_reports": [describe_path(path) for path in PHASE_ARTIFACTS],
        "model_decision": read_json("training/metrics_modelo_v2.json"),
        "phase5_decision": read_json("training/fase5_criterio_aceptacion/criterio_aceptacion_fase5.json"),
        "dataset_curado": read_json("dataset_curado/MANIFEST_FASE3.json"),
    }
    (args.output_dir / "MANIFEST_ENTREGABLES_FASE8.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_report(args.output_dir / "REPORTE_ENTREGABLES_FASE8.md", manifest)
    print((args.output_dir / "REPORTE_ENTREGABLES_FASE8.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
