#!/usr/bin/env python3
"""Fase 7: define el flujo recomendado con Gemini y modelo local."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE6 = ROOT / "training" / "fase6_decision_confianza" / "decision_confianza_fase6.json"
DEFAULT_OUTPUT = ROOT / "training" / "fase7_flujo_gemini"


def build_contract(phase6: dict) -> dict:
    return {
        "current_backend": {
            "endpoint": "POST /api/analisis/planta",
            "mode": "single_image_to_gemini",
            "service": "PlantAnalysisServiceImpl.resolveAnalysis -> callGemini",
            "persistence": "PlantAnalysisRecord + PlantAnalysisRecordImage",
            "websocket_topics": ["/topic/analisis", "/topic/alertas"],
            "limitation": "No agrupa imagenes por planta/maceta/lado antes de llamar a Gemini.",
        },
        "recommended_flow": [
            "Robot captura imagenes y las envia con contexto de QR/planta/maceta/lado.",
            "Backend agrupa por planta + maceta + lado.",
            "Modelo local clasifica cada imagen rapido y produce clase + confianza.",
            "Backend aplica reglas de fase 6 por imagen y por grupo.",
            "Backend selecciona 1 a 3 imagenes representativas si debe escalar.",
            "Gemini analiza solo el grupo seleccionado o casos ambiguos.",
            "Backend persiste resultado final y publica WebSocket.",
        ],
        "gemini_trigger_rules": {
            "always_trigger": [
                "grupo con peligro preliminar",
                "grupo ambiguo con mezcla sano/peligro",
                "grupo cuya clase ganadora sea atencion",
                "confianza promedio < 0.60",
                "menos de 3 imagenes utiles",
                "captura borrosa o evidencia insuficiente",
            ],
            "can_skip_gemini_only_if": [
                "modelo local aprobado en fase 5",
                ">= 3 imagenes utiles del grupo",
                "confianza promedio >= 0.80",
                "voto consistente entre imagenes",
                "sin contradiccion sano/peligro",
            ],
            "current_project_status": {
                "modelo_local_aprobado_fase5": False,
                "gemini_skip_allowed_for_final_diagnosis": False,
                "reason": "Fase 5 no aprobo ningun modelo para diagnostico final.",
            },
        },
        "group_decision_input": {
            "groupKey": "PLA_<planta>_MA_<maceta>_<lado>",
            "plantId": "number|null",
            "potId": "number|null",
            "side": "D|I|O|null",
            "images": [
                {
                    "imageId": "string",
                    "mimeType": "image/jpeg",
                    "imagenBase64": "...",
                    "localPrediction": {
                        "estado": "SANO|ATENCION|PELIGRO",
                        "confianza": 0.0,
                        "bucket": "alta|media|baja",
                    },
                }
            ],
        },
        "group_decision_output": {
            "localEstadoPreliminar": "SANO|ATENCION|PELIGRO|AMBIGUO",
            "localConfianzaPromedio": 0.0,
            "accion": "USAR_GEMINI|CAPTURA_ADICIONAL|REVISION_MANUAL|SOLO_PRELIMINAR",
            "geminiRequired": True,
            "selectedImageIdsForGemini": [],
            "motivosEscalamiento": [],
        },
        "phase6_reference": {
            "thresholds": phase6["thresholds"],
            "final_diagnosis_allowed": phase6["final_diagnosis_allowed"],
            "bucket_stats": phase6["bucket_stats"],
        },
    }


def write_report(path: Path, contract: dict, phase6_path: Path) -> None:
    lines = [
        "# Fase 7: flujo recomendado con Gemini",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Reglas fase 6: `{phase6_path}`",
        "",
        "## Estado actual",
        "",
        "- El backend actual usa `POST /api/analisis/planta`.",
        "- El servicio `PlantAnalysisServiceImpl` manda una imagen a Gemini y persiste un `PlantAnalysisRecord`.",
        "- Publica resultados en `/topic/analisis` y alertas en `/topic/alertas`.",
        "- Todavia no existe un endpoint de analisis por grupo de imagenes.",
        "",
        "## Decision de fase 7",
        "",
        "Gemini no debe llamarse por cada imagen si el robot captura muchas fotos. La llamada correcta es por grupo "
        "`planta + maceta + lado`, despues de que el clasificador local filtre y priorice evidencia.",
        "",
        "Como fase 5 no aprobo ningun modelo local para diagnostico final, el modelo local queda solo como filtro "
        "rapido. Gemini o revision manual siguen siendo obligatorios para el diagnostico final.",
        "",
        "## Flujo recomendado",
        "",
    ]
    for index, step in enumerate(contract["recommended_flow"], start=1):
        lines.append(f"{index}. {step}")

    lines.extend(
        [
            "",
            "## Cuando llamar Gemini",
            "",
        ]
    )
    for rule in contract["gemini_trigger_rules"]["always_trigger"]:
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## Cuando se podria omitir Gemini",
            "",
            "Solo cuando todas estas condiciones sean verdaderas:",
            "",
        ]
    )
    for rule in contract["gemini_trigger_rules"]["can_skip_gemini_only_if"]:
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "En el estado actual del proyecto, esa omision no esta permitida para diagnostico final porque "
            "`modelo_local_aprobado_fase5` es `false`.",
            "",
            "## Contrato sugerido",
            "",
            "```json",
            json.dumps(contract, indent=2),
            "```",
            "",
            "## Cambios sugeridos para una fase posterior de backend",
            "",
            "- Agregar endpoint `POST /api/analisis/grupo`.",
            "- Aceptar multiples imagenes con `groupKey`, `plantId`, `potId`, `side` y predicciones locales.",
            "- Seleccionar 1 a 3 imagenes para Gemini segun peligro, baja confianza o contradiccion.",
            "- Persistir resultado local preliminar y resultado Gemini final por separado.",
            "- Mantener `POST /api/analisis/planta` para analisis manual/individual.",
            "",
            "## Salida operativa",
            "",
            "El reporte final debe distinguir:",
            "",
            "- `localEstadoPreliminar`: resultado rapido del modelo local.",
            "- `geminiEstadoFinal`: resultado final cuando se escale.",
            "- `requiereRevisionManual`: true si hay ambiguedad o evidencia insuficiente.",
            "- `motivosEscalamiento`: lista concreta de razones.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera artefactos de fase 7 para flujo con Gemini.")
    parser.add_argument("--phase6", type=Path, default=DEFAULT_PHASE6)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    phase6 = json.loads(args.phase6.read_text(encoding="utf-8"))
    contract = build_contract(phase6)
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase6_path": str(args.phase6),
        "contract": contract,
    }
    (args.output_dir / "flujo_gemini_fase7.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(args.output_dir / "REPORTE_FLUJO_GEMINI_FASE7.md", contract, args.phase6)
    print((args.output_dir / "REPORTE_FLUJO_GEMINI_FASE7.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
