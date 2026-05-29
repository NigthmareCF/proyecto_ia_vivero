#!/usr/bin/env python3
"""Fase 6: reglas de decision por confianza para el modelo local."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDICTIONS = ROOT / "training" / "auditoria_fase3_dataset_curado" / "predictions_validation_test.csv"
DEFAULT_ACCEPTANCE = ROOT / "training" / "fase5_criterio_aceptacion" / "criterio_aceptacion_fase5.json"
DEFAULT_OUTPUT = ROOT / "training" / "fase6_decision_confianza"

HIGH_THRESHOLD = 0.80
MID_THRESHOLD = 0.60


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def bucket(confidence: float) -> str:
    if confidence >= HIGH_THRESHOLD:
        return "alta"
    if confidence >= MID_THRESHOLD:
        return "media"
    return "baja"


def action_for(row: dict, final_diagnosis_allowed: bool) -> str:
    confidence = float(row["confidence"])
    predicted = row["predicted_class"]
    if confidence >= HIGH_THRESHOLD:
        if final_diagnosis_allowed:
            return "aceptar_clasificacion_local"
        if predicted == "peligro":
            return "alerta_preliminar_y_confirmar_con_gemini"
        return "clasificacion_preliminar_no_final"
    if confidence >= MID_THRESHOLD:
        return "agregar_con_otras_imagenes_del_grupo"
    return "captura_adicional_revision_o_gemini"


def summarize(rows: list[dict], final_diagnosis_allowed: bool) -> tuple[list[dict], list[dict], dict]:
    enriched = []
    bucket_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    action_stats = Counter()
    class_bucket_stats = defaultdict(lambda: {"total": 0, "correct": 0})

    for row in rows:
        confidence = float(row["confidence"])
        is_correct = row["correct"] == "True"
        row_bucket = bucket(confidence)
        action = action_for(row, final_diagnosis_allowed)
        enriched_row = {
            "split": row["split"],
            "true_class": row["true_class"],
            "predicted_class": row["predicted_class"],
            "confidence": f"{confidence:.6f}",
            "bucket": row_bucket,
            "action": action,
            "correct": row["correct"],
            "path": row["path"],
        }
        enriched.append(enriched_row)

        bucket_stats[row_bucket]["total"] += 1
        class_bucket_stats[(row["predicted_class"], row_bucket)]["total"] += 1
        if is_correct:
            bucket_stats[row_bucket]["correct"] += 1
            class_bucket_stats[(row["predicted_class"], row_bucket)]["correct"] += 1
        action_stats[action] += 1

    bucket_rows = []
    for name in ("alta", "media", "baja"):
        stats = bucket_stats[name]
        total = stats["total"]
        bucket_rows.append(
            {
                "bucket": name,
                "threshold": threshold_text(name),
                "total": total,
                "correct": stats["correct"],
                "accuracy": (stats["correct"] / total if total else 0.0),
            }
        )

    class_rows = []
    for (predicted, name), stats in sorted(class_bucket_stats.items()):
        total = stats["total"]
        class_rows.append(
            {
                "predicted_class": predicted,
                "bucket": name,
                "total": total,
                "correct": stats["correct"],
                "accuracy": (stats["correct"] / total if total else 0.0),
            }
        )

    summary = {
        "actions": dict(action_stats),
        "bucket_stats": bucket_rows,
        "class_bucket_stats": class_rows,
    }
    return enriched, bucket_rows, summary


def threshold_text(name: str) -> str:
    if name == "alta":
        return "confianza >= 0.80"
    if name == "media":
        return "0.60 <= confianza < 0.80"
    return "confianza < 0.60"


def group_policy() -> dict:
    return {
        "group_key": "planta + maceta + lado",
        "minimum_images": 3,
        "recommended_images": 5,
        "local_acceptance": {
            "all_required": [
                "modelo_aprobado_en_fase5 == true",
                ">= 3 imagenes del grupo",
                "clase ganadora por promedio/voto",
                "confianza_promedio >= 0.80",
                "sin contradiccion fuerte entre sano y peligro",
            ]
        },
        "current_project_decision": {
            "modelo_aprobado_en_fase5": False,
            "local_final_diagnosis_allowed": False,
            "local_role": "filtro_rapido_para_priorizar_y_decidir_escalamiento",
        },
        "escalation_rules": [
            "Si aparece peligro con confianza alta, generar alerta preliminar y confirmar con Gemini o revision.",
            "Si las imagenes del grupo mezclan sano y peligro, no decidir localmente.",
            "Si la mayoria cae en atencion, pedir confirmacion porque es la clase debil.",
            "Si confianza promedio < 0.60, solicitar captura adicional o revision manual.",
        ],
    }


def write_report(path: Path, payload: dict) -> None:
    lines = [
        "# Fase 6: decision por confianza",
        "",
        f"Fecha: {payload['generated_at']}",
        f"Predicciones base: `{payload['predictions_path']}`",
        f"Dictamen fase 5: `{payload['acceptance_path']}`",
        "",
        "## Decision base",
        "",
        f"- Modelo aprobado para diagnostico final: `{'si' if payload['final_diagnosis_allowed'] else 'no'}`.",
        "- Por lo tanto, una confianza alta no significa diagnostico final; significa senal local preliminar.",
        "",
        "## Umbrales por imagen",
        "",
        "| Bucket | Regla | Imagenes | Correctas | Accuracy observado | Accion |",
        "|---|---|---:|---:|---:|---|",
    ]
    action_by_bucket = {
        "alta": "preliminar alta; confirmar si afecta decision final",
        "media": "agregar con otras imagenes del grupo",
        "baja": "captura adicional, revision o Gemini",
    }
    for row in payload["bucket_stats"]:
        total = row["total"]
        accuracy = row["accuracy"] * 100 if total else 0.0
        lines.append(
            f"| {row['bucket']} | {row['threshold']} | {total} | {row['correct']} | "
            f"{accuracy:.2f}% | {action_by_bucket[row['bucket']]} |"
        )

    lines.extend(
        [
            "",
            "## Reglas operativas",
            "",
            "1. No usar `argmax` solo como diagnostico final.",
            "2. Si `confianza >= 0.80`, aceptar solo como clasificacion preliminar local.",
            "3. Si predice `peligro` con confianza alta, levantar alerta preliminar y confirmar con Gemini/revision.",
            "4. Si `0.60 <= confianza < 0.80`, esperar mas imagenes del mismo grupo.",
            "5. Si `confianza < 0.60`, pedir captura adicional, revision manual o Gemini.",
            "6. Si el grupo mezcla `sano` y `peligro`, escalar aunque haya confianza alta en una imagen.",
            "7. Si la clase ganadora es `atencion`, escalar o pedir mas evidencia porque fue la clase debil en fases 4 y 5.",
            "",
            "## Regla por grupo",
            "",
            "Grupo operativo: `planta + maceta + lado`.",
            "",
            "- Minimo: 3 imagenes.",
            "- Recomendado: 5 imagenes.",
            "- Agregacion: promedio de probabilidades y voto por clase.",
            "- Salida local: `sano_preliminar`, `atencion_preliminar`, `peligro_preliminar`, `ambiguo`, `requiere_gemini`.",
            "",
            "## Contrato recomendado para backend",
            "",
            "```json",
            json.dumps(payload["group_policy"], indent=2),
            "```",
            "",
            "## Implicacion para fase 7",
            "",
            "La fase 7 debe usar Gemini solo cuando el grupo sea ambiguo, haya peligro preliminar, "
            "la clase sea atencion o la confianza agregada no sea suficiente.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera reglas fase 6 por confianza.")
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions = read_csv(args.predictions)
    acceptance = json.loads(args.acceptance.read_text(encoding="utf-8"))
    final_allowed = bool(acceptance["decision"]["approved_for_final_diagnosis"])

    enriched, bucket_rows, summary = summarize(predictions, final_allowed)
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "predictions_path": str(args.predictions),
        "acceptance_path": str(args.acceptance),
        "thresholds": {
            "high": HIGH_THRESHOLD,
            "mid": MID_THRESHOLD,
        },
        "final_diagnosis_allowed": final_allowed,
        "bucket_stats": bucket_rows,
        "actions": summary["actions"],
        "class_bucket_stats": summary["class_bucket_stats"],
        "group_policy": group_policy(),
    }

    write_csv(
        args.output_dir / "decisiones_por_imagen_fase6.csv",
        enriched,
        ["split", "true_class", "predicted_class", "confidence", "bucket", "action", "correct", "path"],
    )
    (args.output_dir / "decision_confianza_fase6.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(args.output_dir / "REPORTE_DECISION_CONFIANZA_FASE6.md", payload)
    print((args.output_dir / "REPORTE_DECISION_CONFIANZA_FASE6.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
