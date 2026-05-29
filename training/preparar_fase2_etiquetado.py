#!/usr/bin/env python3
"""Prepara los entregables de fase 2: reglas y cola de revision de etiquetas."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "training" / "auditoria_fase1_20260528_043608"
DEFAULT_OUTPUT = ROOT / "training" / "fase2_reglas_etiquetado"
MODEL_SPLITS = {"train", "validation", "test"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_set(value: str) -> set[str]:
    return {part for part in value.split("|") if part}


def build_review_queue(audit_dir: Path) -> list[dict]:
    predictions = read_csv(audit_dir / "predictions_validation_test.csv")
    exact_duplicates = read_csv(audit_dir / "exact_duplicates.csv")
    perceptual_pairs = read_csv(audit_dir / "perceptual_similar_pairs.csv")

    rows: list[dict] = []

    for row in predictions:
        if row["true_class"] == "atencion" and row["correct"] == "False":
            predicted = row["predicted_class"]
            priority = "alta" if predicted in {"sano", "peligro"} and float(row["confidence"]) >= 0.70 else "media"
            rows.append(
                {
                    "priority": priority,
                    "source": "modelo_error_atencion",
                    "current_label": "atencion",
                    "suggested_review": f"revisar si es atencion real o deberia ser {predicted}",
                    "confidence_or_distance": row["confidence"],
                    "path_a": row["path"],
                    "path_b": "",
                    "notes": "Error del modelo actual; revisar sintomas visibles y borde sano/peligro.",
                }
            )

    for row in exact_duplicates:
        splits = split_set(row["splits"])
        classes = split_set(row["classes"])
        if len(classes) > 1 or len(splits & MODEL_SPLITS) > 1:
            priority = "critica" if len(classes) > 1 else "alta"
            rows.append(
                {
                    "priority": priority,
                    "source": "duplicado_exacto",
                    "current_label": row["classes"],
                    "suggested_review": "definir una sola etiqueta canonica y evitar fuga entre splits",
                    "confidence_or_distance": "sha256",
                    "path_a": row["paths"],
                    "path_b": "",
                    "notes": f"Grupo con {row['count']} copias en splits {row['splits']}.",
                }
            )

    for row in perceptual_pairs:
        if row["cross_class"] != "True":
            continue
        priority = "alta" if int(row["distance"]) <= 4 else "media"
        rows.append(
            {
                "priority": priority,
                "source": "similaridad_perceptual_entre_clases",
                "current_label": f"{row['class_a']}|{row['class_b']}",
                "suggested_review": "decidir etiqueta canonica o enviar a revision_dudosa",
                "confidence_or_distance": row["distance"],
                "path_a": row["path_a"],
                "path_b": row["path_b"],
                "notes": f"Par pHash similar; cross_split={row['cross_split']}.",
            }
        )

    priority_order = {"critica": 0, "alta": 1, "media": 2, "baja": 3}
    rows.sort(key=lambda item: (priority_order[item["priority"]], item["source"], item["confidence_or_distance"]))
    return rows


def write_rules(path: Path, audit_dir: Path, queue: list[dict]) -> None:
    source_counts = Counter(row["source"] for row in queue)
    priority_counts = Counter(row["priority"] for row in queue)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""# Fase 2: reglas de etiquetado para dataset IA local

Fecha: {now}
Auditoria base: `{audit_dir}`
Salida de revision: `training/fase2_reglas_etiquetado/revision_etiquetado_fase2.csv`

## Objetivo

Hacer consistentes las clases `sano`, `atencion` y `peligro` antes de crear `dataset_curado`.
Esta fase no mueve ni borra imagenes. Solo define reglas y deja una cola de revision.

## Regla principal

Etiqueta por lo que se ve en la planta, no por lo que el nombre del archivo o el split dicen.
Si la imagen no permite decidir con claridad, no debe forzarse a una clase fuerte: va a
`revision_dudosa` en la fase 3.

## Clases

### sano

Usar `sano` cuando la planta se vea funcionalmente normal:

- hojas verdes o con variacion leve natural;
- sin manchas relevantes, necrosis, plaga visible ni marchitez marcada;
- bordes secos minimos o ruido visual que no compromete el estado general;
- fondo, iluminacion o encuadre no deben crear una falsa alarma.

No usar `sano` si hay amarillamiento extendido, manchas multiples, hojas caidas, tejido muerto,
plaga visible o deterioro que un operador deberia revisar.

### atencion

Usar `atencion` para sintomas leves o moderados:

- manchas pequenas o localizadas;
- amarillamiento parcial;
- hojas secas leves o bordes deteriorados;
- estres visible, pero sin dano dominante;
- planta recuperable o caso que requiere seguimiento, no alarma inmediata.

`atencion` es la clase de frontera. Debe excluir dos extremos:

- si casi no hay sintoma visible, mover a `sano`;
- si el dano es extenso, negro, necrotico, con plaga marcada o marchitez fuerte, mover a `peligro`.

### peligro

Usar `peligro` cuando el dano sea fuerte o de riesgo alto:

- necrosis evidente o tejido muerto dominante;
- plaga severa visible;
- marchitez marcada;
- pudricion o manchas oscuras extensas;
- dano que afecta gran parte de la planta;
- caso donde el sistema deberia priorizar alerta o intervencion.

No usar `peligro` para una hoja aislada con borde seco si el resto de la planta luce estable.

## Casos que van a revision_dudosa

Enviar a revision si:

- la imagen esta borrosa, demasiado oscura o demasiado recortada;
- se ve mas maceta/fondo que planta;
- el sintoma podria ser luz/sombra;
- hay mezcla fuerte entre planta sana y una hoja muy danada;
- dos etiquetas parecen igualmente defensibles;
- es duplicado o casi duplicado de otra imagen con etiqueta distinta.

## Reglas para duplicados

1. Si dos archivos son la misma imagen exacta y tienen etiquetas distintas, elegir una sola etiqueta canonica.
2. Si una imagen exacta aparece en `train` y tambien en `validation` o `test`, dejarla solo en un split en fase 3.
3. Si dos imagenes son casi iguales, tratarlas como un mismo grupo visual para evitar fuga entre splits.
4. El `test` curado debe conservar imagenes no vistas por entrenamiento ni validacion.

## Prioridad de revision

La cola de revision contiene `{len(queue)}` entradas:

- Criticas: `{priority_counts.get('critica', 0)}`.
- Altas: `{priority_counts.get('alta', 0)}`.
- Medias: `{priority_counts.get('media', 0)}`.

Origenes principales:

- Errores del modelo en `atencion`: `{source_counts.get('modelo_error_atencion', 0)}`.
- Duplicados exactos conflictivos o con fuga: `{source_counts.get('duplicado_exacto', 0)}`.
- Pares similares entre clases: `{source_counts.get('similaridad_perceptual_entre_clases', 0)}`.

## Decision para fase 3

Al construir `dataset_curado`, cada imagen revisada debe caer en una de estas decisiones:

- `keep_sano`
- `keep_atencion`
- `keep_peligro`
- `move_sano`
- `move_atencion`
- `move_peligro`
- `revision_dudosa`
- `excluir_duplicado`
- `excluir_baja_calidad`

La fase 3 debe crear una copia curada. No debe editar `dataset/raw`, `dataset/train`,
`dataset/validation` ni `dataset/test` directamente.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera reglas y cola de revision para fase 2.")
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    queue = build_review_queue(args.audit_dir)

    fieldnames = [
        "priority",
        "source",
        "current_label",
        "suggested_review",
        "confidence_or_distance",
        "path_a",
        "path_b",
        "notes",
    ]
    write_csv(args.output_dir / "revision_etiquetado_fase2.csv", queue, fieldnames)
    write_rules(args.output_dir / "REGLAS_ETIQUETADO_FASE2.md", args.audit_dir, queue)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_dir": str(args.audit_dir),
        "review_rows": len(queue),
        "by_priority": dict(Counter(row["priority"] for row in queue)),
        "by_source": dict(Counter(row["source"] for row in queue)),
    }
    (args.output_dir / "resumen_fase2.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Reglas: {args.output_dir / 'REGLAS_ETIQUETADO_FASE2.md'}")
    print(f"Revision: {args.output_dir / 'revision_etiquetado_fase2.csv'}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
