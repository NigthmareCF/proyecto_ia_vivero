#!/usr/bin/env python3
"""Genera contact sheets para revisar visualmente imagenes dudosas."""

from __future__ import annotations

import argparse
import csv
from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "dataset_curado" / "revision_dudosa" / "manifest_revision_dudosa.csv"
OUTPUT = ROOT / "training" / "revision_visual_atencion"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_sheet(rows: list[dict[str, str]], output_path: Path, page: int) -> None:
    cols = 5
    thumb_w, thumb_h = 180, 150
    label_h = 48
    rows_count = ceil(len(rows) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows_count * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, row in enumerate(rows):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        src = ROOT / row["path"]
        try:
            with Image.open(src) as img:
                img = img.convert("RGB")
                img.thumbnail((thumb_w, thumb_h))
                sheet.paste(img, (x + (thumb_w - img.width) // 2, y + (thumb_h - img.height) // 2))
        except Exception:
            draw.rectangle((x, y, x + thumb_w, y + thumb_h), fill=(230, 230, 230))
            draw.text((x + 6, y + 6), "ERROR", fill=(180, 0, 0), font=font)

        code = Path(row["path"]).name
        label = f"{page:02d}-{idx+1:02d} {code}\n{row['reason'][:28]}"
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(245, 245, 245))
        draw.text((x + 4, y + thumb_h + 4), label, fill=(0, 0, 0), font=font)

    sheet.save(output_path, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera lotes visuales de atencion conflictiva.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--page-size", type=int, default=25)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_rows = [
        row for row in read_csv(MANIFEST)
        if row["original_class"] == "atencion"
        and row["reason"] in {
            "similaridad perceptual con etiqueta conflictiva",
            "duplicado exacto con etiqueta conflictiva",
        }
    ]

    for page_start in range(0, len(source_rows), args.page_size):
        page = page_start // args.page_size + 1
        batch = source_rows[page_start:page_start + args.page_size]
        make_sheet(batch, args.output_dir / f"atencion_conflicto_lote_{page:02d}.jpg", page)
        with (args.output_dir / f"atencion_conflicto_lote_{page:02d}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["code", "path", "reason", "decision", "notes"])
            writer.writeheader()
            for idx, row in enumerate(batch):
                writer.writerow(
                    {
                        "code": f"{page:02d}-{idx+1:02d}",
                        "path": row["path"],
                        "reason": row["reason"],
                        "decision": "",
                        "notes": "",
                    }
                )

    print(f"Generados {ceil(len(source_rows) / args.page_size)} lotes en {args.output_dir}")


if __name__ == "__main__":
    main()
