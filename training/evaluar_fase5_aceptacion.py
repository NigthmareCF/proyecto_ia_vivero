#!/usr/bin/env python3
"""Fase 5: evalua criterios de aceptacion del modelo local."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS = ROOT / "training" / "metrics_modelo_v2.json"
DEFAULT_OUTPUT = ROOT / "training" / "fase5_criterio_aceptacion"

MINIMUM = {
    "accuracy": 0.80,
    "atencion": 0.70,
    "peligro": 0.80,
}

IDEAL = {
    "accuracy": 0.85,
    "atencion": 0.80,
    "peligro": 0.85,
}


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def evaluate_model(metrics: dict) -> dict:
    class_metrics = metrics["class_metrics"]
    result = {
        "model": metrics["model"],
        "accuracy": metrics["test_accuracy"],
        "atencion": class_metrics["atencion"]["recall"],
        "peligro": class_metrics["peligro"]["recall"],
        "sano": class_metrics["sano"]["recall"],
        "macro_f1": metrics["macro_f1"],
    }
    result["passes_minimum"] = (
        result["accuracy"] >= MINIMUM["accuracy"]
        and result["atencion"] >= MINIMUM["atencion"]
        and result["peligro"] >= MINIMUM["peligro"]
    )
    result["passes_ideal"] = (
        result["accuracy"] >= IDEAL["accuracy"]
        and result["atencion"] >= IDEAL["atencion"]
        and result["peligro"] >= IDEAL["peligro"]
    )
    return result


def decision(results: list[dict]) -> dict:
    accepted = [item for item in results if item["passes_minimum"]]
    best = max(results, key=lambda item: (item["accuracy"], item["macro_f1"]))
    best_trained = max(
        [item for item in results if item["model"] != "baseline_modelo_vivero_tflite"],
        key=lambda item: (item["accuracy"], item["macro_f1"]),
    )
    return {
        "accepted_models": [item["model"] for item in accepted],
        "best_model": best["model"],
        "best_trained_model": best_trained["model"],
        "approved_for_final_diagnosis": bool(accepted),
        "approved_for_backend_replacement": bool(accepted and best["model"] != "baseline_modelo_vivero_tflite"),
        "recommended_use": (
            "diagnostico_final"
            if accepted
            else "filtro_rapido_por_grupo_no_diagnostico_final"
        ),
        "reason": (
            "Hay al menos un modelo que cumple el minimo de fase 5."
            if accepted
            else "Ningun modelo alcanza accuracy>=80%, atencion>=70% y peligro>=80%."
        ),
    }


def write_report(path: Path, payload: dict) -> None:
    rows = payload["results"]
    dec = payload["decision"]
    lines = [
        "# Fase 5: criterio de aceptacion modelo IA local",
        "",
        f"Fecha: {payload['generated_at']}",
        f"Metricas base: `{payload['metrics_path']}`",
        "",
        "## Criterio",
        "",
        "| Nivel | Accuracy test | atencion | peligro |",
        "|---|---:|---:|---:|",
        f"| Minimo | {pct(MINIMUM['accuracy'])} | {pct(MINIMUM['atencion'])} | {pct(MINIMUM['peligro'])} |",
        f"| Ideal | {pct(IDEAL['accuracy'])} | {pct(IDEAL['atencion'])} | {pct(IDEAL['peligro'])} |",
        "",
        "## Resultado por modelo",
        "",
        "| Modelo | Accuracy | atencion | peligro | sano | Macro F1 | Minimo | Ideal |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in sorted(rows, key=lambda item: item["accuracy"], reverse=True):
        lines.append(
            f"| {row['model']} | {pct(row['accuracy'])} | {pct(row['atencion'])} | "
            f"{pct(row['peligro'])} | {pct(row['sano'])} | {row['macro_f1']:.4f} | "
            f"{'PASS' if row['passes_minimum'] else 'FAIL'} | "
            f"{'PASS' if row['passes_ideal'] else 'FAIL'} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Mejor modelo medido: `{dec['best_model']}`.",
            f"- Mejor modelo entrenado en fase 4: `{dec['best_trained_model']}`.",
            f"- Aprobado para diagnostico final: `{'si' if dec['approved_for_final_diagnosis'] else 'no'}`.",
            f"- Aprobado para reemplazar backend: `{'si' if dec['approved_for_backend_replacement'] else 'no'}`.",
            f"- Uso recomendado: `{dec['recommended_use']}`.",
            f"- Razon: {dec['reason']}",
            "",
            "## Implicacion",
            "",
            "El modelo local puede seguir siendo util como filtro rapido y para agregacion por grupo, "
            "pero no debe presentarse como diagnostico final autonomo. La siguiente fase debe aplicar "
            "reglas de confianza y escalamiento a captura adicional, revision manual o Gemini.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua criterio de aceptacion fase 5.")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    results = [evaluate_model(item) for item in metrics["candidates"]]
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics_path": str(args.metrics),
        "minimum": MINIMUM,
        "ideal": IDEAL,
        "results": results,
        "decision": decision(results),
    }
    (args.output_dir / "criterio_aceptacion_fase5.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    write_report(args.output_dir / "REPORTE_CRITERIO_ACEPTACION_FASE5.md", payload)
    print((args.output_dir / "REPORTE_CRITERIO_ACEPTACION_FASE5.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
