import os

rutas = [
    "dataset/raw/sano",
    "dataset/raw/atencion",
    "dataset/raw/peligro",

    "dataset/train/sano",
    "dataset/train/atencion",
    "dataset/train/peligro",

    "dataset/validation/sano",
    "dataset/validation/atencion",
    "dataset/validation/peligro",

    "dataset/test/sano",
    "dataset/test/atencion",
    "dataset/test/peligro"
]

for ruta in rutas:
    os.makedirs(ruta, exist_ok=True)
    print(f"Carpeta creada: {ruta}")

print("\nEstructura lista.")