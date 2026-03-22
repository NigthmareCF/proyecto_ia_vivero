from pathlib import Path

CLASES = ["sano", "atencion", "peligro"]
EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def contar(carpeta: Path) -> int:
    if not carpeta.exists():
        return -1   # -1 = no existe
    return sum(1 for f in carpeta.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONES)


def mostrar_seccion(titulo: str):
    print(f"\n{'='*58}")
    print(f"  {titulo}")
    print(f"{'='*58}")


def main():

    # ── RAW ──────────────────────────────────────────────────────────────────
    mostrar_seccion("dataset/raw  (imágenes sin dividir)")
    print(f"{'Clase':<14} {'Archivos':>10}")
    print(f"{'─'*26}")

    total_raw = 0
    for clase in CLASES:
        n = contar(Path("dataset/raw") / clase)
        if n == -1:
            print(f"  {clase:<12}   [NO EXISTE]")
        else:
            print(f"  {clase:<12} {n:>10}")
            total_raw += n

    print(f"{'─'*26}")
    print(f"  {'TOTAL':<12} {total_raw:>10}")

    # ── TRAIN / VALIDATION / TEST ─────────────────────────────────────────────
    mostrar_seccion("Splits  (train / validation / test)")
    print(f"{'Clase':<14} {'Train':>8} {'Val':>8} {'Test':>8} {'Total':>8}  {'Train%':>7} {'Val%':>6} {'Test%':>6}")
    print(f"{'─'*70}")

    totales = {"train": 0, "validation": 0, "test": 0}

    for clase in CLASES:
        counts = {}
        for split in ["train", "validation", "test"]:
            n = contar(Path("dataset") / split / clase)
            counts[split] = n
            if n > 0:
                totales[split] += n

        total_clase = sum(v for v in counts.values() if v >= 0)

        def pct(v):
            if total_clase == 0 or v < 0:
                return "  -  "
            return f"{v/total_clase*100:>5.1f}%"

        def fmt(v):
            return f"{v:>8}" if v >= 0 else "  [?] "

        print(
            f"  {clase:<12} {fmt(counts['train'])} {fmt(counts['validation'])} "
            f"{fmt(counts['test'])} {total_clase:>8}  "
            f"{pct(counts['train'])} {pct(counts['validation'])} {pct(counts['test'])}"
        )

    print(f"{'─'*70}")
    total_split = sum(totales.values())
    print(
        f"  {'TOTAL':<12} {totales['train']:>8} {totales['validation']:>8} "
        f"{totales['test']:>8} {total_split:>8}"
    )

    # ── Alertas ───────────────────────────────────────────────────────────────
    alertas = []

    for clase in CLASES:
        n_raw = contar(Path("dataset/raw") / clase)
        if n_raw == -1:
            alertas.append(f"  dataset/raw/{clase} no existe")
        elif n_raw == 0:
            alertas.append(f"  dataset/raw/{clase} está vacía")

        for split in ["train", "validation", "test"]:
            n = contar(Path("dataset") / split / clase)
            if n == -1:
                alertas.append(f"  dataset/{split}/{clase} no existe — ¿corriste dividir_dataset.py?")
            elif n == 0:
                alertas.append(f"  dataset/{split}/{clase} está vacía")

    if alertas:
        print(f"\n{'='*58}")
        print("  ALERTAS")
        print(f"{'='*58}")
        for a in alertas:
            print(a)
    else:
        print(f"\n  Todo en orden. Dataset listo.\n")


if __name__ == "__main__":
    main()
