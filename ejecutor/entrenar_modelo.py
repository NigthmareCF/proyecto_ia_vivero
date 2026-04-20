"""
entrenar_modelo.py  (v3 — optimizado para subir accuracy)
===========================================================
Cambios respecto a v2:
  - Class weights: penaliza más los errores en 'atencion' (clase difícil)
  - Fine-tuning desde capa 80 en lugar de 100 (aprende más de plantas)
  - Dropout 0.30 (reduce sobreajuste)
  - EarlyStopping patience=6 (más oportunidad de converger)
  - Eliminado guardado .h5 (incompatible con Keras 3+)
  - Se mantiene optimización CPU con todos los núcleos

Dependencias:
    pip install -r requirements-ml.txt
"""

import os
import sys
from pathlib import Path

try:
    import numpy as np
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Falta la dependencia 'numpy'. Instala el entorno de ML con: "
        "python -m pip install -r requirements-ml.txt"
    ) from exc

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Falta la dependencia 'tensorflow'. Ejecuta este script dentro de un "
        "entorno de ML dedicado e instala: "
        "python -m pip install -r requirements-ml.txt"
    ) from exc

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
print(f"Usando Python: {sys.executable}")
print(f"Directorio de trabajo: {ROOT_DIR}")

# ─── Optimización CPU ────────────────────────────────────────────────────────

tf.config.threading.set_intra_op_parallelism_threads(0)
tf.config.threading.set_inter_op_parallelism_threads(0)
print(f"Entrenando en CPU — núcleos disponibles: {os.cpu_count()}")

# ─── Configuración ───────────────────────────────────────────────────────────

IMG_SIZE     = (224, 224)
BATCH_SIZE   = 16
EPOCHS       = 25        # más épocas, EarlyStopping corta cuando corresponde
SEED         = 42

BASE_DATASET = Path("dataset")
TRAIN_DIR    = BASE_DATASET / "train"
TEST_DIR     = BASE_DATASET / "test"

if (BASE_DATASET / "validation").exists():
    VAL_DIR = BASE_DATASET / "validation"
elif (BASE_DATASET / "val").exists():
    VAL_DIR = BASE_DATASET / "val"
else:
    raise FileNotFoundError("No existe dataset/validation ni dataset/val")

MODEL_KERAS  = "modelo_vivero.keras"
MODEL_TFLITE = "modelo_vivero.tflite"
LABELS_FILE  = "labels.txt"

# ─── Carga del dataset ───────────────────────────────────────────────────────

print("\nCargando datasets...")

train_ds = tf.keras.utils.image_dataset_from_directory(
    TRAIN_DIR,
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    color_mode="rgb"
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    VAL_DIR,
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    color_mode="rgb"
)

test_ds = tf.keras.utils.image_dataset_from_directory(
    TEST_DIR,
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    color_mode="rgb"
)

class_names = train_ds.class_names
num_classes = len(class_names)

print(f"\nClases detectadas ({num_classes}):")
for i, c in enumerate(class_names):
    print(f"  {i}: {c}")

with open(LABELS_FILE, "w", encoding="utf-8") as f:
    for c in class_names:
        f.write(c + "\n")

# ─── Class weights — penaliza más los errores en clases difíciles ────────────
# Cuenta imágenes por clase para calcular el peso automáticamente

print("\nCalculando class weights...")
conteos = {}
for clase in class_names:
    carpeta = TRAIN_DIR / clase
    n = sum(1 for f in carpeta.iterdir()
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    conteos[clase] = n
    print(f"  {clase}: {n} imágenes")

total_imgs  = sum(conteos.values())
class_weight = {}
for i, clase in enumerate(class_names):
    # Fórmula estándar: total / (num_clases * conteo_clase)
    peso = total_imgs / (num_classes * conteos[clase])
    class_weight[i] = round(peso, 4)
    print(f"  peso [{clase}]: {class_weight[i]}")

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds   = val_ds.prefetch(buffer_size=AUTOTUNE)
test_ds  = test_ds.prefetch(buffer_size=AUTOTUNE)

# ─── Data Augmentation ───────────────────────────────────────────────────────

data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.10),
    layers.RandomZoom(0.10),
    layers.RandomContrast(0.15),
    layers.RandomBrightness(0.15),
    layers.RandomTranslation(0.05, 0.05),
], name="data_augmentation")

# ─── Modelo ──────────────────────────────────────────────────────────────────

base_model = keras.applications.MobileNetV2(
    input_shape=IMG_SIZE + (3,),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

inputs  = keras.Input(shape=IMG_SIZE + (3,))
x       = data_augmentation(inputs)
x       = keras.applications.mobilenet_v2.preprocess_input(x)
x       = base_model(x, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.Dropout(0.30)(x)          # subido de 0.25 a 0.30
outputs = layers.Dense(num_classes, activation="softmax")(x)

model = keras.Model(inputs, outputs)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ─── Callbacks ───────────────────────────────────────────────────────────────

def get_callbacks(sufijo):
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=6,                    # subido de 4 a 6
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.2,
            patience=3,                    # subido de 2 a 3
            verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_KERAS,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        keras.callbacks.CSVLogger(
            f"training_log_{sufijo}.csv",
            append=False
        ),
    ]

# ─── Fase 1: Transfer Learning ───────────────────────────────────────────────

print("\n" + "="*50)
print("  FASE 1 — Transfer Learning")
print("="*50)

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weight,             # ← nuevo
    callbacks=get_callbacks("fase1")
)

# ─── Fase 2: Fine-tuning ─────────────────────────────────────────────────────

print("\n" + "="*50)
print("  FASE 2 — Fine-tuning")
print("="*50)

base_model.trainable = True

# Descongelado desde capa 80 (antes era 100) — aprende más de plantas
for layer in base_model.layers[:80]:
    layer.trainable = False

total_trainable = sum(1 for l in base_model.layers if l.trainable)
print(f"  Capas entrenables en base_model: {total_trainable}")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

history_fine = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=15,                             # subido de 10 a 15
    class_weight=class_weight,             # ← nuevo
    callbacks=get_callbacks("fase2")
)

# ─── Evaluación final ────────────────────────────────────────────────────────

print("\n" + "="*50)
print("  EVALUACIÓN EN TEST")
print("="*50)

test_loss, test_acc = model.evaluate(test_ds, verbose=1)
print(f"\n  Accuracy en test : {test_acc*100:.2f}%")
print(f"  Loss en test     : {test_loss:.4f}")

# Matriz de confusión
print("\n  Matriz de confusión:")
y_true, y_pred = [], []
for images, labels in test_ds:
    preds = model.predict(images, verbose=0)
    y_true.extend(labels.numpy())
    y_pred.extend(np.argmax(preds, axis=1))

y_true = np.array(y_true)
y_pred = np.array(y_pred)

print(f"\n  {'':12}", end="")
for c in class_names:
    print(f"  {c:>10}", end="")
print()
for i, c in enumerate(class_names):
    print(f"  {c:<12}", end="")
    for j in range(num_classes):
        count = int(np.sum((y_true == i) & (y_pred == j)))
        print(f"  {count:>10}", end="")
    total_clase = int(np.sum(y_true == i))
    acc_clase = int(np.sum((y_true == i) & (y_pred == i))) / total_clase * 100
    print(f"   ({acc_clase:.0f}%)")

# ─── Guardar modelos ─────────────────────────────────────────────────────────

print("\n" + "="*50)
print("  GUARDANDO MODELOS")
print("="*50)

model.save(MODEL_KERAS)
print(f"  Guardado: {MODEL_KERAS}")

# TFLite con cuantización float16 para Raspberry Pi
print("\n  Convirtiendo a TFLite (float16)...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_model = converter.convert()

with open(MODEL_TFLITE, "wb") as f:
    f.write(tflite_model)

size_mb = os.path.getsize(MODEL_TFLITE) / (1024 * 1024)

# ─── Resumen final ───────────────────────────────────────────────────────────

print("\n" + "="*50)
print("  RESUMEN FINAL")
print("="*50)
print(f"  Accuracy test        : {test_acc*100:.2f}%")
print(f"  Loss test            : {test_loss:.4f}")
print(f"  modelo_vivero.keras  : guardado")
print(f"  modelo_vivero.tflite : guardado ({size_mb:.1f} MB)")
print(f"  labels.txt           : guardado")
print(f"  training_log_fase1.csv : guardado")
print(f"  training_log_fase2.csv : guardado")
print("="*50 + "\n")
